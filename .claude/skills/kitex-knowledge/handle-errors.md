# Kitex 错误类型

## 错误分类

### 业务错误

在 IDL 中定义的业务异常:

```thrift
exception BizException {
    1: required i32 code
    2: required string message
}

service MyService {
    Response MyMethod(1: Request req) throws (1: BizException err)
}
```

### 框架错误

RPC 框架层面的错误:
- 网络连接失败
- 超时
- 序列化失败
- 服务不可用

## 抛出业务错误

### Server 端

```go
func (s *MyServiceImpl) MyMethod(ctx context.Context, req *Request) (*Response, error) {
    if req.ID <= 0 {
        return nil, &api.BizException{
            Code:    400,
            Message: "invalid id",
        }
    }

    // 正常处理
    return resp, nil
}
```

## 处理错误

### Client 端

```go
import (
    "errors"
    "github.com/cloudwego/kitex/pkg/kerrors"
)

resp, err := cli.MyMethod(ctx, req)
if err != nil {
    // 判断业务异常
    var bizErr *api.BizException
    if errors.As(err, &bizErr) {
        log.Printf("biz error: code=%d, msg=%s", bizErr.Code, bizErr.Message)
        return
    }

    // 判断框架错误
    if errors.Is(err, kerrors.ErrRPCTimeout) {
        log.Println("timeout")
        return
    }

    // 其他错误
    log.Printf("unknown error: %v", err)
}
```

## 常见框架错误

### 超时

```go
if errors.Is(err, kerrors.ErrRPCTimeout) {
    // RPC 超时
}
```

### 连接错误

```go
if errors.Is(err, kerrors.ErrRPCFinish) {
    // 连接失败
}
```

### 无可用实例

```go
if errors.Is(err, kerrors.ErrNoMoreInstance) {
    // 服务不可用
}
```

## 错误码设计

```go
const (
    // 2xx: 成功
    CodeSuccess = 200

    // 4xx: 客户端错误
    CodeBadRequest   = 400
    CodeUnauthorized = 401
    CodeForbidden    = 403
    CodeNotFound     = 404

    // 5xx: 服务端错误
    CodeInternalError = 500
    CodeServiceUnavailable = 503
)
```

## 相关文档

- [业务错误处理](business-errors.md)
- [错误处理最佳实践](error-best-practices.md)
