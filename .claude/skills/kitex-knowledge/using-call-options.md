# Kitex 调用时指定参数

## 概述

Kitex 支持在调用时动态指定参数，覆盖 Client 初始化时的配置。

## CallOption 机制

### 基本用法

```go
import (
    "github.com/cloudwego/kitex/client/callopt"
)

// Client 初始化时的默认配置
cli, err := myservice.NewClient(
    "my.service",
    client.WithRPCTimeout(100 * time.Millisecond),
)

// 调用时覆盖超时配置
resp, err := cli.MyMethod(
    ctx,
    req,
    callopt.WithRPCTimeout(200 * time.Millisecond),  // 临时超时 200ms
)
```

## 常用 CallOption

### 1. 超时配置

#### RPC 超时

```go
// 设置本次调用的 RPC 超时
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRPCTimeout(500 * time.Millisecond),
)
```

#### 连接超时

```go
// 设置连接超时
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithConnectTimeout(50 * time.Millisecond),
)
```

### 2. 重试配置

#### 覆盖重试策略

```go
import (
    "github.com/cloudwego/kitex/pkg/retry"
)

// 本次调用不重试
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRetryPolicy(retry.BuildFailurePolicy(retry.NewFailurePolicy WithMaxRetryTimes(0))),
)
```

#### 禁用 Backup Request

```go
// 禁用备份请求
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRetryPolicy(retry.BuildFailurePolicy(retry.NewFailurePolicy WithEnableBackupRequest(false))),
)
```

### 3. 指定目标地址

#### 直接指定 IP:Port

```go
// 绕过服务发现，直接调用指定地址
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithHostPort("192.168.1.100:8888"),
)
```

#### 指定 URL

```go
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithURL("http://192.168.1.100:8888/api"),
)
```

### 4. 标签(Tag)传递

#### 设置请求标签

```go
// 用于灰度发布、A/B 测试等场景
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithTag("env", "gray"),
    callopt.WithTag("version", "v2"),
)
```

### 5. HTTP 配置 (泛化调用)

#### HTTP Header

```go
resp, err := cli.GenericCall(
    ctx,
    method,
    request,
    callopt.WithHTTPHost("example.com"),
    callopt.WithHTTPHeader("Authorization", "Bearer token"),
    callopt.WithHTTPHeader("User-Agent", "MyClient/1.0"),
)
```

## 组合使用

### 多个 CallOption

```go
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRPCTimeout(500 * time.Millisecond),
    callopt.WithConnectTimeout(50 * time.Millisecond),
    callopt.WithHostPort("192.168.1.100:8888"),
    callopt.WithTag("env", "gray"),
)
```

### 封装常用配置

```go
// 封装灰度环境调用配置
func GrayCallOptions() []callopt.Option {
    return []callopt.Option{
        callopt.WithRPCTimeout(1000 * time.Millisecond),
        callopt.WithTag("env", "gray"),
        callopt.WithTag("cluster", "gray-cluster"),
    }
}

// 使用
resp, err := cli.GetUser(ctx, req, GrayCallOptions()...)
```

## 使用场景

### 1. 灰度发布

```go
func CallWithGray(ctx context.Context, cli myservice.Client, req *myservice.Request, isGray bool) (*myservice.Response, error) {
    opts := []callopt.Option{}

    if isGray {
        opts = append(opts,
            callopt.WithTag("env", "gray"),
            callopt.WithRPCTimeout(2000 * time.Millisecond),  // 灰度环境更长超时
        )
    }

    return cli.GetUser(ctx, req, opts...)
}
```

### 2. 重要请求特殊处理

```go
func CallVIPUser(ctx context.Context, cli myservice.Client, req *myservice.Request) (*myservice.Response, error) {
    // VIP 用户请求：更长超时 + 更多重试
    return cli.GetUser(
        ctx,
        req,
        callopt.WithRPCTimeout(2000 * time.Millisecond),
        callopt.WithRetryPolicy(retry.BuildFailurePolicy(
            retry.NewFailurePolicy().
                WithMaxRetryTimes(3).
                WithEnableBackupRequest(true),
        )),
    )
}
```

### 3. 故障降级

```go
func CallWithFallback(ctx context.Context, cli myservice.Client, req *myservice.Request) (*myservice.Response, error) {
    // 主集群调用
    resp, err := cli.GetUser(ctx, req)
    if err != nil {
        // 降级到备用集群
        resp, err = cli.GetUser(
            ctx,
            req,
            callopt.WithHostPort("backup-cluster:8888"),
            callopt.WithRPCTimeout(500 * time.Millisecond),
        )
    }

    return resp, err
}
```

### 4. A/B 测试

```go
func CallWithABTest(ctx context.Context, cli myservice.Client, req *myservice.Request, userID int64) (*myservice.Response, error) {
    // 根据用户 ID 分流
    bucket := userID % 100

    opts := []callopt.Option{}
    if bucket < 10 {
        // 10% 用户使用新版本
        opts = append(opts, callopt.WithTag("version", "v2"))
    } else {
        opts = append(opts, callopt.WithTag("version", "v1"))
    }

    return cli.GetUser(ctx, req, opts...)
}
```

### 5. 跨机房调用

```go
func CallCrossIDC(ctx context.Context, cli myservice.Client, req *myservice.Request, targetIDC string) (*myservice.Response, error) {
    // 跨机房调用需要更长超时
    timeout := 100 * time.Millisecond
    if targetIDC != "local" {
        timeout = 500 * time.Millisecond
    }

    return cli.GetUser(
        ctx,
        req,
        callopt.WithRPCTimeout(timeout),
        callopt.WithTag("target_idc", targetIDC),
    )
}
```

## CallOption 优先级

CallOption 的优先级高于 Client 初始化时的配置：

```go
// Client 默认超时 100ms
cli, err := myservice.NewClient(
    "my.service",
    client.WithRPCTimeout(100 * time.Millisecond),
)

// 本次调用超时 200ms (CallOption 覆盖)
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRPCTimeout(200 * time.Millisecond),
)
```

## 从 Context 读取配置

### 通过 Context 传递配置

```go
import (
    "github.com/cloudwego/kitex/pkg/rpcinfo"
)

// 设置到 Context
ctx = context.WithValue(ctx, "target_addr", "192.168.1.100:8888")

// 在 Middleware 中读取
middleware := func(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        addr := ctx.Value("target_addr").(string)

        // 动态设置地址
        ri := rpcinfo.GetRPCInfo(ctx)
        rpcinfo.AsMutableEndpointInfo(ri.To()).SetAddress(utils.NewNetAddr("tcp", addr))

        return next(ctx, req, resp)
    }
}
```

## 性能考虑

### CallOption 开销

CallOption 会有额外的分配和处理开销：

```go
// 高性能场景：尽量使用 Client 默认配置
cli, err := myservice.NewClient(
    "my.service",
    client.WithRPCTimeout(100 * time.Millisecond),
)

// 避免每次调用都创建 CallOption
resp, err := cli.GetUser(ctx, req)  // ✅ 推荐
```

```go
// 低频场景：可以使用 CallOption 灵活调整
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRPCTimeout(200 * time.Millisecond),  // ✅ 可接受
)
```

### 缓存常用 CallOption

```go
var (
    grayOptions = []callopt.Option{
        callopt.WithTag("env", "gray"),
        callopt.WithRPCTimeout(2000 * time.Millisecond),
    }

    vipOptions = []callopt.Option{
        callopt.WithRPCTimeout(5000 * time.Millisecond),
        callopt.WithRetryPolicy(retry.BuildFailurePolicy(
            retry.NewFailurePolicy().WithMaxRetryTimes(3),
        )),
    }
)

// 重用预定义的 Options
resp, err := cli.GetUser(ctx, req, grayOptions...)
```

## 最佳实践

### 1. 明确覆盖意图

```go
// ✅ 明确注释为什么要覆盖配置
// 灰度环境网络延迟较高，增加超时时间
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRPCTimeout(500 * time.Millisecond),
)
```

### 2. 避免滥用

```go
// ❌ 不推荐：每次调用都指定相同配置
resp, err := cli.GetUser(
    ctx,
    req,
    callopt.WithRPCTimeout(100 * time.Millisecond),  // 应该设为默认值
)

// ✅ 推荐：在 Client 初始化时设置
cli, err := myservice.NewClient(
    "my.service",
    client.WithRPCTimeout(100 * time.Millisecond),
)
```

### 3. 封装业务逻辑

```go
type ServiceCaller struct {
    cli myservice.Client
}

func (s *ServiceCaller) GetUser(ctx context.Context, uid int64, opts ...callopt.Option) (*myservice.User, error) {
    req := &myservice.GetUserRequest{UID: uid}

    // 业务层统一处理 CallOption
    defaultOpts := []callopt.Option{
        callopt.WithRPCTimeout(1000 * time.Millisecond),
    }

    allOpts := append(defaultOpts, opts...)
    return s.cli.GetUser(ctx, req, allOpts...)
}
```

## 相关文档

- [超时配置](./configure-timeout.md)
- [重试配置](./configure-retry.md)
- [服务配置](./configure-service.md)
- [使用中间件](./using-middleware.md)
