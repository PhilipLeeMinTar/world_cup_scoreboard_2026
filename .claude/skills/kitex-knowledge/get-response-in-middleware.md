# 在中间件中获取 Request/Response

## 概述

Kitex 中间件可以访问真实的 Request 和 Response 对象，用于日志、监控、业务逻辑处理等。

## 获取 BaseResp

### Client 中间件

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/endpoint"
)

func ClientMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            // 调用下游
            err := next(ctx, req, resp)

            // 获取 Response
            if r, ok := resp.(*myservice.Response); ok {
                // 访问 BaseResp
                if r.BaseResp != nil {
                    log.Printf("StatusCode: %d, StatusMessage: %s",
                        r.BaseResp.StatusCode,
                        r.BaseResp.StatusMessage)

                    // 根据 BaseResp 做业务逻辑
                    if r.BaseResp.StatusCode != 0 {
                        // 记录业务错误
                        metrics.Counter("business_error").Inc()
                    }
                }
            }

            return err
        }
    }
}

// 使用
cli, err := myservice.NewClient(
    "my.service",
    client.WithMiddleware(ClientMiddleware()),
)
```

### Server 中间件

```go
func ServerMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            // 记录请求
            if r, ok := req.(*myservice.Request); ok {
                log.Printf("Received request: %+v", r)
            }

            // 处理请求
            err := next(ctx, req, resp)

            // 修改响应
            if r, ok := resp.(*myservice.Response); ok {
                // 确保 BaseResp 存在
                if r.BaseResp == nil {
                    r.BaseResp = &base.BaseResp{}
                }

                // 填充 BaseResp
                if err != nil {
                    r.BaseResp.StatusCode = 500
                    r.BaseResp.StatusMessage = err.Error()
                } else {
                    r.BaseResp.StatusCode = 0
                    r.BaseResp.StatusMessage = "success"
                }
            }

            return err
        }
    }
}
```

## 类型断言处理

### 安全的类型断言

```go
func SafeMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 使用 switch 处理多种类型
            switch r := resp.(type) {
            case *myservice.GetUserResponse:
                if r.BaseResp != nil {
                    log.Printf("GetUser StatusCode: %d", r.BaseResp.StatusCode)
                }

            case *myservice.CreateUserResponse:
                if r.BaseResp != nil {
                    log.Printf("CreateUser StatusCode: %d", r.BaseResp.StatusCode)
                }

            default:
                log.Printf("Unknown response type: %T", resp)
            }

            return err
        }
    }
}
```

### 使用泛型 (Go 1.18+)

```go
type BaseResponse interface {
    GetBaseResp() *base.BaseResp
}

func GenericMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 检查是否实现了 BaseResponse 接口
            if r, ok := resp.(BaseResponse); ok {
                baseResp := r.GetBaseResp()
                if baseResp != nil {
                    log.Printf("StatusCode: %d", baseResp.StatusCode)
                }
            }

            return err
        }
    }
}
```

## 获取 Request 信息

### 记录请求参数

```go
func LogRequestMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            // 记录请求开始
            start := time.Now()

            // 提取请求信息
            var reqInfo string
            switch r := req.(type) {
            case *myservice.GetUserRequest:
                reqInfo = fmt.Sprintf("GetUser(uid=%d)", r.UID)
            case *myservice.CreateUserRequest:
                reqInfo = fmt.Sprintf("CreateUser(name=%s)", r.Name)
            default:
                reqInfo = fmt.Sprintf("Unknown request: %T", req)
            }

            log.Printf("Request: %s", reqInfo)

            // 执行请求
            err := next(ctx, req, resp)

            // 记录请求结束
            duration := time.Since(start)
            log.Printf("Request: %s, Duration: %v, Error: %v", reqInfo, duration, err)

            return err
        }
    }
}
```

## 修改 Request/Response

### Client 端修改请求

```go
func ModifyRequestMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            // 修改请求
            if r, ok := req.(*myservice.GetUserRequest); ok {
                // 添加默认值
                if r.Extra == nil {
                    r.Extra = make(map[string]string)
                }
                r.Extra["client_version"] = "1.0"
                r.Extra["timestamp"] = fmt.Sprintf("%d", time.Now().Unix())
            }

            return next(ctx, req, resp)
        }
    }
}
```

### Server 端修改响应

```go
func ModifyResponseMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 修改响应
            if r, ok := resp.(*myservice.GetUserResponse); ok {
                // 添加额外信息
                if r.Extra == nil {
                    r.Extra = make(map[string]string)
                }
                r.Extra["server_version"] = "2.0"
                r.Extra["process_time"] = fmt.Sprintf("%v", time.Now())
            }

            return err
        }
    }
}
```

## 使用 RPC Info

### 获取调用元信息

```go
import (
    "github.com/cloudwego/kitex/pkg/rpcinfo"
)

func RPCInfoMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            ri := rpcinfo.GetRPCInfo(ctx)

            // 获取调用者信息
            from := ri.From()
            log.Printf("Caller: %s, Address: %s",
                from.ServiceName(),
                from.Address())

            // 获取被调用者信息
            to := ri.To()
            log.Printf("Callee: %s, Method: %s",
                to.ServiceName(),
                to.Method())

            // 获取配置信息
            config := ri.Config()
            log.Printf("RPCTimeout: %v", config.RPCTimeout())

            // 执行调用
            err := next(ctx, req, resp)

            // 获取调用统计
            stats := rpcinfo.GetRPCStats(ri)
            log.Printf("SendSize: %d, RecvSize: %d",
                stats.SendSize(),
                stats.RecvSize())

            return err
        }
    }
}
```

## 获取下游 IP

### Client 获取下游地址

```go
func GetDownstreamIPMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 获取实际调用的下游地址
            ri := rpcinfo.GetRPCInfo(ctx)
            addr := ri.To().Address()

            if addr != nil {
                log.Printf("Downstream IP: %s", addr.String())

                // 存储到 Context 用于后续处理
                ctx = context.WithValue(ctx, "downstream_addr", addr.String())
            }

            return err
        }
    }
}
```

### Server 获取上游 IP

```go
func GetUpstreamIPMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            ri := rpcinfo.GetRPCInfo(ctx)

            // 获取调用方地址
            from := ri.From()
            if from.Address() != nil {
                log.Printf("Upstream IP: %s", from.Address().String())
            }

            return next(ctx, req, resp)
        }
    }
}
```

## 业务场景示例

### 1. 统一错误处理

```go
func ErrorHandlingMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 处理 RPC 错误
            if err != nil {
                log.Printf("RPC Error: %v", err)

                // 填充业务错误响应
                if r, ok := resp.(BaseResponse); ok {
                    baseResp := r.GetBaseResp()
                    if baseResp == nil {
                        baseResp = &base.BaseResp{}
                    }
                    baseResp.StatusCode = 500
                    baseResp.StatusMessage = "Internal Server Error"
                }

                return err
            }

            // 检查业务错误
            if r, ok := resp.(BaseResponse); ok {
                baseResp := r.GetBaseResp()
                if baseResp != nil && baseResp.StatusCode != 0 {
                    log.Printf("Business Error: %d - %s",
                        baseResp.StatusCode,
                        baseResp.StatusMessage)

                    // 上报业务错误指标
                    metrics.Counter("business_error",
                        "code", fmt.Sprintf("%d", baseResp.StatusCode)).Inc()
                }
            }

            return nil
        }
    }
}
```

### 2. 请求响应日志

```go
func AccessLogMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            start := time.Now()
            ri := rpcinfo.GetRPCInfo(ctx)

            // 记录请求信息
            log.Printf("[Request] Method: %s, From: %s",
                ri.To().Method(),
                ri.From().ServiceName())

            // 执行请求
            err := next(ctx, req, resp)

            // 记录响应信息
            duration := time.Since(start)
            statusCode := 0

            if r, ok := resp.(BaseResponse); ok {
                if baseResp := r.GetBaseResp(); baseResp != nil {
                    statusCode = int(baseResp.StatusCode)
                }
            }

            log.Printf("[Response] Method: %s, Duration: %v, StatusCode: %d, Error: %v",
                ri.To().Method(),
                duration,
                statusCode,
                err)

            return err
        }
    }
}
```

### 3. 性能监控

```go
func MetricsMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            start := time.Now()
            ri := rpcinfo.GetRPCInfo(ctx)
            method := ri.To().Method()

            // 执行请求
            err := next(ctx, req, resp)

            // 记录耗时
            duration := time.Since(start)
            metrics.Histogram("rpc_duration", "method", method).Observe(duration.Seconds())

            // 记录请求数
            status := "success"
            if err != nil {
                status = "error"
            }
            metrics.Counter("rpc_requests", "method", method, "status", status).Inc()

            // 记录大小
            stats := rpcinfo.GetRPCStats(ri)
            metrics.Histogram("rpc_send_size", "method", method).Observe(float64(stats.SendSize()))
            metrics.Histogram("rpc_recv_size", "method", method).Observe(float64(stats.RecvSize()))

            return err
        }
    }
}
```

## 最佳实践

### 1. 避免修改不应该修改的字段

```go
// ❌ 不推荐：在 Client 中间件中修改 Response
func BadClientMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // 不应该在 Client 修改 Server 返回的 Response
            if r, ok := resp.(*myservice.Response); ok {
                r.Data = "modified"  // ❌ 错误
            }

            return err
        }
    }
}
```

### 2. 注意并发安全

```go
// ✅ 推荐：不要在中间件中修改共享状态
func ConcurrentSafeMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            // 每个请求独立处理，不共享状态
            localData := make(map[string]interface{})
            ctx = context.WithValue(ctx, "local_data", localData)

            return next(ctx, req, resp)
        }
    }
}
```

### 3. 处理类型断言失败

```go
func SafeTypeAssertionMiddleware() endpoint.Middleware {
    return func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            err := next(ctx, req, resp)

            // ✅ 总是检查类型断言结果
            if r, ok := resp.(*myservice.Response); ok && r != nil {
                if r.BaseResp != nil {
                    // 安全访问
                    log.Printf("StatusCode: %d", r.BaseResp.StatusCode)
                }
            }

            return err
        }
    }
}
```

## 相关文档

- [使用中间件](./using-middleware.md)
- [错误处理](./handle-errors.md)
- [错误处理指南](./error-handling-guide.md)
