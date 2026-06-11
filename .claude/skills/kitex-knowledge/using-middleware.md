# Kitex 中间件基础

## 什么是中间件?

中间件是在 RPC 调用前后插入自定义逻辑的机制,用于:
- 日志记录
- 监控埋点
- 链路追踪
- 权限校验
- 参数校验

## 中间件定义

```go
import (
    "context"
    "github.com/cloudwego/kitex/pkg/endpoint"
)

func MyMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        // 请求前处理
        log.Println("before")

        // 调用下一个中间件
        err := next(ctx, req, resp)

        // 响应后处理
        log.Println("after")

        return err
    }
}
```

## 注册中间件

### Client 端

```go
cli, err := myservice.NewClient(
    "my.service",
    client.WithMiddleware(MyMiddleware),
)
```

### Server 端

```go
svr := myservice.NewServer(
    new(MyServiceImpl),
    server.WithMiddleware(MyMiddleware),
)
```

## 中间件顺序

按注册顺序执行:

```go
client.WithMiddleware(MW1)  // 最外层
client.WithMiddleware(MW2)  // 中间层
client.WithMiddleware(MW3)  // 最内层
```

执行流程:
```
请求: MW1 -> MW2 -> MW3 -> RPC
响应: MW1 <- MW2 <- MW3 <- RPC
```

## 获取 RPC 信息

```go
import "github.com/cloudwego/kitex/pkg/rpcinfo"

func InfoMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        ri := rpcinfo.GetRPCInfo(ctx)

        method := ri.To().Method()
        service := ri.To().ServiceName()

        log.Printf("Call: %s.%s", service, method)

        return next(ctx, req, resp)
    }
}
```

## 相关文档

- [自定义中间件](custom-middleware.md)
- [中间件示例](middleware-examples.md)
