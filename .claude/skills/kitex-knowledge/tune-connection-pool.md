# Kitex 连接池配置

## 概述

Kitex 支持长连接池来提高性能和资源利用率。

⚠️ **注意**: 仅适用于未开启 Mesh 的场景。开启 Mesh 后，长连接由 Mesh 接管，Kitex Client 侧的配置不生效。

## 基本配置

### 启用长连接池

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/connpool"
)

cli, err := myservice.NewClient(
    "my.service",
    client.WithLongConnection(connpool.IdleConfig{
        MaxIdlePerAddress: 10,
        MaxIdleGlobal:     1000,
        MaxIdleTimeout:    60 * time.Second,
        MinIdlePerAddress: 2,  // Kitex >= v1.10.2
    }),
)
```

## 配置参数详解

### MaxIdlePerAddress

**含义**: 每个后端实例允许的最大闲置连接数

**计算公式**:
```
MaxIdlePerAddress = qps_per_dest_host * avg_response_time_sec
```

**示例**:
- 每个请求响应时间: 100ms
- 平摊到每个下游地址的 QPS: 100
- 推荐值: `100 * 0.1 = 10`

**注意事项**:
- 最小值为 1，否则长连接会退化为短连接
- 过大或过小都会导致连接复用率低
- 需考虑流量波动和 `MaxIdleTimeout` 的影响

### MinIdlePerAddress

**含义**: 每个后端实例维持的最小空闲连接数

**适用场景**: 周期性请求，且周期大于 `MaxIdleTimeout`

**配置要点**:
- 最大可设置为 5
- 这部分连接不会因空闲时间过长而被清理
- 可减少建连次数，降低 TP99/TP999

**示例**:
```go
// 5 个连接，每个请求 100ms
// 可支持 50 QPS 而无需新建连接
MinIdlePerAddress: 5
```

### MaxIdleGlobal

**含义**: Client 的全局最大闲置连接数

**推荐设置**:
```
MaxIdleGlobal > 下游目标总数 * MaxIdlePerAddress
```

超出部分用于限制主动新建连接的总数量。

⚠️ 该参数价值不大，建议设置为较大值（如 10000）。

### MaxIdleTimeout

**含义**: 连接的闲置时长，超过后连接会被关闭

**重要提示**:
- Kite Server 在 3s 内会清理不活跃的连接
- Kitex Server 不会主动清理不活跃的连接
- 下游为 Kite 时，该值不可超过 2.5s

**推荐值**:
```go
// 下游为 Kitex
MaxIdleTimeout: 60 * time.Second

// 下游为 Kite
MaxIdleTimeout: 2 * time.Second
```

## 连接池实现原理

### 获取连接流程

1. 从目标地址的连接池 (ring) 中获取连接
2. 如果获取失败（无空闲连接），新建连接
3. 如果获取成功，检查空闲时间是否超过 `MaxIdleTimeout`
4. 超时则关闭并新建，否则返回使用

### 归还连接流程

1. 检查连接是否正常，异常则关闭
2. 检查全局空闲连接数是否超过 `MaxIdleGlobal`，超过则关闭
3. 检查目标连接池是否有空间，有则放入，否则关闭

## 最佳实践

### 1. 根据 QPS 和响应时间调整

```go
// 高 QPS 场景 (1000 QPS/实例, 50ms 响应时间)
MaxIdlePerAddress: 50

// 低 QPS 场景 (10 QPS/实例, 100ms 响应时间)
MaxIdlePerAddress: 1
```

### 2. 周期性请求优化

```go
// 避免每次周期性请求都新建连接
MinIdlePerAddress: 2
MaxIdleTimeout:    120 * time.Second
```

### 3. 监控连接池状态

建议监控指标:
- 连接建立速率
- 连接复用率
- 空闲连接数
- 连接超时数

## 常见问题

### Q: 长连接池不生效？

**A**: 检查以下几点:
- 是否开启了 Mesh (Mesh 会接管连接)
- `MaxIdlePerAddress` 是否大于 0
- 下游服务是否主动关闭连接

### Q: 连接频繁新建？

**A**: 可能原因:
- `MaxIdlePerAddress` 设置过小
- `MaxIdleTimeout` 设置过短
- `MaxIdleGlobal` 设置过小

### Q: 下游为 Kite，连接经常失效？

**A**: Kite Server 3s 清理连接，需设置:
```go
MaxIdleTimeout: 2 * time.Second  // 必须小于 2.5s
```

## 性能影响

### 短连接 vs 长连接

| 场景 | 短连接 | 长连接池 |
|------|--------|----------|
| 连接建立开销 | 每次请求 | 首次/超时 |
| 内存占用 | 低 | 中 |
| CPU 占用 | 高（握手） | 低 |
| 适用场景 | 低 QPS | 高 QPS |

### 性能建议

- QPS > 10: 使用长连接池
- QPS < 10: 短连接即可
- 高 TP99 要求: 设置 `MinIdlePerAddress`

## 相关文档

- [超时配置](./configure-timeout.md)
- [流式传输](./using-streaming.md)
- [重试配置](./configure-retry.md)
