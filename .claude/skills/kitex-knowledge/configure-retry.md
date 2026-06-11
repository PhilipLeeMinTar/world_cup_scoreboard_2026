# Kitex 重试策略

## 概述

重试机制用于提高服务调用的可靠性。当请求因临时性错误失败时,通过自动重试可以提升成功率。

## 重试类型

### Failure Retry (失败重试)

请求失败后进行重试:

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/retry"
)

fp := retry.NewFailurePolicy()
fp.WithMaxRetryTimes(2)  // 最多重试2次

cli, err := myservice.NewClient(
    "my.service",
    client.WithFailureRetry(fp),
)
```

### Backup Request (备份请求)

在指定时间内没有响应时,发送备份请求:

```go
bp := retry.NewBackupPolicy(20)  // 20ms后发送备份请求

cli, err := myservice.NewClient(
    "my.service",
    client.WithBackupRequest(bp),
)
```

## 配置参数

### 最大重试次数

```go
fp.WithMaxRetryTimes(2)  // 加上首次,共3次请求
```

### 总超时时间

```go
fp.WithMaxDurationMS(500)  // 总耗时不超过500ms
```

### 退避策略

#### 固定延迟

```go
fp.WithFixedBackOff(50 * time.Millisecond)
```

#### 随机延迟

```go
fp.WithRandomBackOff(10*time.Millisecond, 100*time.Millisecond)
```

### 重试同节点

```go
fp.WithRetrySameNode()  // 允许重试同一个节点
```

### 熔断阈值

```go
fp.WithRetryBreaker(0.1)  // 错误率超过10%停止重试
```

## 最佳实践

### 1. 确保接口幂等性

```go
type Request struct {
    RequestID string  // 幂等键
    // ...
}
```

### 2. 合理设置重试次数

```go
// ✅ 推荐
fp.WithMaxRetryTimes(1)

// ❌ 避免
fp.WithMaxRetryTimes(5)  // 产生6倍流量
```

### 3. 设置总超时

```go
fp.WithMaxDurationMS(500)
```

### 4. 启用熔断

```go
fp.WithRetryBreaker(0.1)
```

## 使用场景

### 适合重试

- 网络临时抖动
- 服务短暂不可用
- 连接失效

### 不适合重试

- 非幂等接口(扣款、下单)
- 参数错误
- 权限拒绝

## 相关文档

- [超时配置](timeout.md)
- [熔断机制](circuit-breaker.md)
