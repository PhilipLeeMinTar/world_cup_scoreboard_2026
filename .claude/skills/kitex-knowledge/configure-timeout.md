# Kitex 超时配置

## 超时类型

### RPC Timeout

单次 RPC 调用的总超时时间:

```go
client.WithRPCTimeout(100 * time.Millisecond)
```

### Connection Timeout

建立连接的超时时间:

```go
client.WithConnectTimeout(50 * time.Millisecond)
```

## 动态超时

### 使用 CallOption

```go
import "github.com/cloudwego/kitex/client/callopt"

resp, err := cli.MyMethod(
    ctx,
    req,
    callopt.WithRPCTimeout(200*time.Millisecond),
)
```

### 使用 Context

```go
ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
defer cancel()

resp, err := cli.MyMethod(ctx, req)
```

## 超时传递

Kitex 自动在调用链中传递剩余超时时间:

```
A (500ms) -> B (剩余400ms) -> C (剩余300ms)
```

## 配置优先级

1. CallOption 动态配置
2. Context Deadline
3. Client 初始化配置
4. 配置中心配置
5. 默认值

## 推荐配置

```go
// 基于 P99 设置
// P99 延迟: 80ms
// 超时配置: 80ms * 1.2 = 100ms
client.WithRPCTimeout(100 * time.Millisecond)
```

## 超时错误处理

```go
import (
    "errors"
    "github.com/cloudwego/kitex/pkg/kerrors"
)

resp, err := cli.MyMethod(ctx, req)
if err != nil {
    if errors.Is(err, kerrors.ErrRPCTimeout) {
        // 超时处理
        log.Warn("request timeout")
    }
}
```

## 相关文档

- [重试策略](retry.md)
- [熔断机制](circuit-breaker.md)
