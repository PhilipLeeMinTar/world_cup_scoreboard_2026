# Kitex 错误处理最佳实践

## 错误分类

### 1. 框架错误 (RPC Error)

连接、超时、序列化等框架层面的错误。

```go
import (
    "github.com/cloudwego/kitex/pkg/kerrors"
)

resp, err := cli.GetUser(ctx, req)
if err != nil {
    // 判断框架错误类型
    if errors.Is(err, kerrors.ErrRPCTimeout) {
        log.Println("RPC timeout")
    } else if errors.Is(err, kerrors.ErrRPCFinish) {
        log.Println("Connection failed")
    }
}
```

### 2. 业务错误 (Business Error)

通过 BaseResp 返回的业务逻辑错误。

```go
resp, err := cli.GetUser(ctx, req)
if err != nil {
    return err  // 先处理 RPC 错误
}

// 检查业务错误
if resp.BaseResp != nil && resp.BaseResp.StatusCode != 0 {
    return fmt.Errorf("business error: %d - %s",
        resp.BaseResp.StatusCode,
        resp.BaseResp.StatusMessage)
}
```

## 错误码设计

### 分层错误码

```go
const (
    // 成功
    StatusOK = 0

    // 客户端错误 (4xxxx)
    StatusBadRequest     = 40000  // 请求参数错误
    StatusUnauthorized   = 40100  // 未授权
    StatusForbidden      = 40300  // 禁止访问
    StatusNotFound       = 40400  // 资源不存在

    // 服务端错误 (5xxxx)
    StatusInternalError  = 50000  // 内部错误
    StatusDependencyError = 50100  // 依赖服务错误
    StatusDatabaseError  = 50200  // 数据库错误
)
```

### 错误码映射

```go
type ErrorCode int32

func (e ErrorCode) Message() string {
    messages := map[ErrorCode]string{
        StatusBadRequest:     "Invalid request parameters",
        StatusUnauthorized:   "Unauthorized access",
        StatusNotFound:       "Resource not found",
        StatusInternalError:  "Internal server error",
    }
    return messages[e]
}

func (e ErrorCode) ToBaseResp() *base.BaseResp {
    return &base.BaseResp{
        StatusCode:    int32(e),
        StatusMessage: e.Message(),
    }
}
```

## Client 端错误处理

### 统一错误处理

```go
func CallWithErrorHandling(ctx context.Context, cli myservice.Client, req *myservice.Request) (*myservice.Response, error) {
    resp, err := cli.GetUser(ctx, req)

    // 1. 处理 RPC 错误
    if err != nil {
        if errors.Is(err, kerrors.ErrRPCTimeout) {
            return nil, fmt.Errorf("service timeout: %w", err)
        }
        return nil, fmt.Errorf("rpc call failed: %w", err)
    }

    // 2. 处理业务错误
    if resp.BaseResp != nil && resp.BaseResp.StatusCode != 0 {
        return nil, &BusinessError{
            Code:    resp.BaseResp.StatusCode,
            Message: resp.BaseResp.StatusMessage,
        }
    }

    return resp, nil
}

type BusinessError struct {
    Code    int32
    Message string
}

func (e *BusinessError) Error() string {
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}
```

### 错误重试策略

```go
func CallWithRetry(ctx context.Context, cli myservice.Client, req *myservice.Request) (*myservice.Response, error) {
    var lastErr error

    for i := 0; i < 3; i++ {
        resp, err := cli.GetUser(ctx, req)

        if err == nil {
            // 检查业务错误
            if resp.BaseResp != nil && resp.BaseResp.StatusCode != 0 {
                // 业务错误不重试
                return nil, &BusinessError{
                    Code:    resp.BaseResp.StatusCode,
                    Message: resp.BaseResp.StatusMessage,
                }
            }
            return resp, nil
        }

        // RPC 错误，判断是否可重试
        if errors.Is(err, kerrors.ErrRPCTimeout) {
            lastErr = err
            time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
            continue
        }

        // 不可重试的错误，直接返回
        return nil, err
    }

    return nil, fmt.Errorf("max retry exceeded: %w", lastErr)
}
```

## Server 端错误处理

### 统一错误返回

```go
type MyServiceImpl struct{}

func (s *MyServiceImpl) GetUser(ctx context.Context, req *myservice.GetUserRequest) (*myservice.GetUserResponse, error) {
    resp := &myservice.GetUserResponse{
        BaseResp: &base.BaseResp{},
    }

    // 参数校验
    if req.UID <= 0 {
        resp.BaseResp.StatusCode = StatusBadRequest
        resp.BaseResp.StatusMessage = "Invalid UID"
        return resp, nil  // 业务错误通过 BaseResp 返回
    }

    // 查询用户
    user, err := s.userRepo.GetUser(ctx, req.UID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            // 用户不存在
            resp.BaseResp.StatusCode = StatusNotFound
            resp.BaseResp.StatusMessage = "User not found"
            return resp, nil
        }

        // 数据库错误
        log.Errorf("Failed to get user: %v", err)
        resp.BaseResp.StatusCode = StatusInternalError
        resp.BaseResp.StatusMessage = "Internal server error"
        return resp, nil
    }

    // 成功
    resp.BaseResp.StatusCode = StatusOK
    resp.BaseResp.StatusMessage = "success"
    resp.User = user

    return resp, nil
}
```

### 错误中间件

```go
func ErrorMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 捕获 panic
            defer func() {
                if r := recover(); r != nil {
                    log.Errorf("Panic recovered: %v\n%s", r, debug.Stack())

                    if r, ok := resp.(BaseResponse); ok {
                        baseResp := r.GetBaseResp()
                        if baseResp == nil {
                            baseResp = &base.BaseResp{}
                        }
                        baseResp.StatusCode = StatusInternalError
                        baseResp.StatusMessage = "Internal server error"
                    }
                }
            }()

            // 框架错误转业务错误
            if err != nil {
                log.Errorf("Handler error: %v", err)

                if r, ok := resp.(BaseResponse); ok {
                    baseResp := r.GetBaseResp()
                    if baseResp == nil {
                        baseResp = &base.BaseResp{}
                    }

                    // 未设置业务错误码，填充默认错误
                    if baseResp.StatusCode == 0 {
                        baseResp.StatusCode = StatusInternalError
                        baseResp.StatusMessage = "Internal server error"
                    }
                }

                // 不向上传递错误，通过 BaseResp 返回
                return nil
            }

            return nil
        }
    }
}
```

## 错误日志

### 结构化日志

```go
func LogError(ctx context.Context, err error, fields map[string]interface{}) {
    ri := rpcinfo.GetRPCInfo(ctx)

    logFields := map[string]interface{}{
        "method": ri.To().Method(),
        "error":  err.Error(),
    }

    for k, v := range fields {
        logFields[k] = v
    }

    if errors.Is(err, kerrors.ErrRPCTimeout) {
        log.WithFields(logFields).Warn("RPC timeout")
    } else {
        log.WithFields(logFields).Error("RPC error")
    }
}

// 使用
resp, err := cli.GetUser(ctx, req)
if err != nil {
    LogError(ctx, err, map[string]interface{}{
        "uid": req.UID,
    })
}
```

## 错误监控

### 上报错误指标

```go
func ReportError(ctx context.Context, err error) {
    ri := rpcinfo.GetRPCInfo(ctx)
    method := ri.To().Method()

    // 分类统计
    errorType := "unknown"
    if errors.Is(err, kerrors.ErrRPCTimeout) {
        errorType = "timeout"
    } else if errors.Is(err, kerrors.ErrRPCFinish) {
        errorType = "connection"
    }

    metrics.Counter("rpc_errors",
        "method", method,
        "type", errorType).Inc()
}
```

## 降级处理

### 错误降级

```go
func GetUserWithFallback(ctx context.Context, cli myservice.Client, uid int64) (*myservice.User, error) {
    req := &myservice.GetUserRequest{UID: uid}
    resp, err := cli.GetUser(ctx, req)

    if err != nil || (resp.BaseResp != nil && resp.BaseResp.StatusCode != 0) {
        // 降级：返回默认用户
        return &myservice.User{
            UID:  uid,
            Name: "Unknown User",
        }, nil
    }

    return resp.User, nil
}
```

## 最佳实践总结

### 1. 错误分层

```go
// ✅ 推荐：明确区分 RPC 错误和业务错误
resp, err := cli.GetUser(ctx, req)
if err != nil {
    // RPC 错误
    return handleRPCError(err)
}

if resp.BaseResp.StatusCode != 0 {
    // 业务错误
    return handleBusinessError(resp.BaseResp)
}
```

### 2. 不要忽略错误

```go
// ❌ 错误：忽略错误
resp, _ := cli.GetUser(ctx, req)

// ✅ 正确：处理错误
resp, err := cli.GetUser(ctx, req)
if err != nil {
    return err
}
```

### 3. 提供错误上下文

```go
// ✅ 推荐：使用 fmt.Errorf 添加上下文
if err != nil {
    return fmt.Errorf("failed to get user %d: %w", uid, err)
}
```

### 4. 避免在 BaseResp 中返回敏感信息

```go
// ❌ 错误：暴露内部错误
resp.BaseResp.StatusMessage = err.Error()  // 可能包含数据库连接字符串等

// ✅ 正确：返回通用错误信息
resp.BaseResp.StatusMessage = "Internal server error"
log.Errorf("Database error: %v", err)  // 详细错误记录到日志
```

## 相关文档

- [错误处理](./handle-errors.md)
- [重试配置](./configure-retry.md)
- [使用中间件](./using-middleware.md)
