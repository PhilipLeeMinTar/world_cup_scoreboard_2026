# Kitex 负载均衡

## 概述

Kitex 提供多种负载均衡策略，支持自定义实现。

## 内置负载均衡策略

### 1. WeightedRandom (加权随机)

默认策略，根据实例权重随机选择。

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/loadbalance"
)

cli, err := myservice.NewClient(
    "my.service",
    client.WithLoadBalancer(loadbalance.NewWeightedRandomBalancer()),
)
```

### 2. WeightedRoundRobin (加权轮询)

按权重依次轮询实例。

```go
cli, err := myservice.NewClient(
    "my.service",
    client.WithLoadBalancer(loadbalance.NewWeightedRoundRobinBalancer()),
)
```

### 3. ConsistentHash (一致性哈希)

根据请求特征（如用户 ID）将请求固定路由到特定实例。

#### 基本用法

```go
cli, err := myservice.NewClient(
    "my.service",
    client.WithLoadBalancer(loadbalance.NewConsistHashBalancer(
        loadbalance.NewConsistentHashOption(func(ctx context.Context, request interface{}) string {
            // 返回用于哈希的 key
            req := request.(*myservice.MyRequest)
            return fmt.Sprintf("%d", req.UserID)
        }),
    )),
)
```

#### Mesh 模式下使用一致性哈希

```go
import (
    "github.com/cloudwego/kitex/pkg/rpcinfo"
    "github.com/cloudwego/kitex/client"
)

cli, err := myservice.NewClient(
    "my.service",
    client.WithMiddleware(func(next endpoint.Endpoint) endpoint.Endpoint {
        return func(ctx context.Context, req, resp interface{}) error {
            // 设置哈希 key 到 RPC Info
            ri := rpcinfo.GetRPCInfo(ctx)
            myReq := req.(*myservice.MyRequest)
            hashKey := fmt.Sprintf("%d", myReq.UserID)

            // Mesh 会读取这个 key 进行一致性哈希
            rpcinfo.AsMutableRPCConfig(ri.Config()).SetTag("hash_key", hashKey)

            return next(ctx, req, resp)
        }
    }),
)
```

## 一致性哈希使用场景

### 1. 本地缓存

将相同用户的请求路由到同一实例，提高缓存命中率。

```go
hashFunc := func(ctx context.Context, request interface{}) string {
    req := request.(*api.UserRequest)
    return fmt.Sprintf("user_%d", req.UID)
}

cli, err := api.NewClient(
    "user.service",
    client.WithLoadBalancer(
        loadbalance.NewConsistHashBalancer(
            loadbalance.NewConsistentHashOption(hashFunc),
        ),
    ),
)
```

### 2. 会话保持

确保同一用户的多个请求到达相同实例。

```go
hashFunc := func(ctx context.Context, request interface{}) string {
    req := request.(*api.SessionRequest)
    return req.SessionID
}
```

### 3. 分片处理

将数据按范围分配到不同实例。

```go
hashFunc := func(ctx context.Context, request interface{}) string {
    req := request.(*api.DataRequest)
    return fmt.Sprintf("shard_%d", req.ShardID)
}
```

## 自定义负载均衡器

### 实现 Loadbalancer 接口

```go
type MyLoadBalancer struct{}

func (m *MyLoadBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    instances := result.Instances
    return &MyPicker{instances: instances}
}

type MyPicker struct {
    instances []discovery.Instance
}

func (m *MyPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    // 自定义选择逻辑
    // 例如：根据请求类型选择不同实例
    req := request.(*myservice.MyRequest)

    if req.Priority == "high" {
        // 选择高性能实例
        return m.instances[0]
    }

    // 默认随机选择
    idx := rand.Intn(len(m.instances))
    return m.instances[idx]
}
```

### 使用自定义负载均衡器

```go
cli, err := myservice.NewClient(
    "my.service",
    client.WithLoadBalancer(&MyLoadBalancer{}),
)
```

## 负载均衡器选择建议

| 策略 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| WeightedRandom | 通用场景 | 简单高效 | 流量可能不均 |
| WeightedRoundRobin | 需要严格轮询 | 流量更均匀 | 略慢 |
| ConsistentHash | 本地缓存/会话 | 缓存命中率高 | 实例变化影响大 |

## 性能考虑

### 1. 虚拟节点数

一致性哈希使用虚拟节点提高均匀性：

```go
// 默认虚拟节点数为 10
// 可通过环境变量调整
// KITEX_CONSITHASH_REPLICA=20
```

### 2. 哈希函数选择

建议使用快速哈希函数：

```go
import "github.com/cespare/xxhash/v2"

hashFunc := func(ctx context.Context, request interface{}) string {
    req := request.(*myservice.MyRequest)
    key := fmt.Sprintf("%d", req.UserID)
    hash := xxhash.Sum64String(key)
    return fmt.Sprintf("%d", hash)
}
```

## 实例权重

### 设置实例权重

通过服务发现设置：

```go
// 在服务注册时设置权重
registry.Register(&registry.Info{
    ServiceName: "my.service",
    Addr:        net.ParseAddr("127.0.0.1:8888"),
    Weight:      10,  // 权重值
    Tags: map[string]string{
        "idc": "bj",
    },
})
```

### 动态调整权重

```go
// 通过配置中心动态调整
// Kitex 会自动读取最新的权重值
```

## 健康检查集成

Kitex 会自动过滤不健康的实例：

```go
cli, err := myservice.NewClient(
    "my.service",
    client.WithLoadBalancer(loadbalance.NewWeightedRandomBalancer()),
    // 自动过滤失败实例
    client.WithFailureRetry(retry.NewFailurePolicy()),
)
```

## 最佳实践

### 1. 选择合适的策略

```go
// 无状态服务：WeightedRandom
client.WithLoadBalancer(loadbalance.NewWeightedRandomBalancer())

// 有本地缓存：ConsistentHash
client.WithLoadBalancer(loadbalance.NewConsistHashBalancer(...))

// 需要严格流量控制：WeightedRoundRobin
client.WithLoadBalancer(loadbalance.NewWeightedRoundRobinBalancer())
```

### 2. 监控负载分布

```go
// 记录每个实例的请求数
middleware := func(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        ri := rpcinfo.GetRPCInfo(ctx)
        addr := ri.To().Address().String()

        // 上报监控指标
        metrics.Counter("lb_requests", "addr", addr).Inc()

        return next(ctx, req, resp)
    }
}
```

### 3. 处理实例变化

```go
// 一致性哈希下，实例变化会影响路由
// 建议：
// 1. 预热新实例
// 2. 使用足够的虚拟节点
// 3. 监控缓存命中率
```

## 故障处理

### 实例摘除

Kitex 会自动摘除连续失败的实例：

```go
cli, err := myservice.NewClient(
    "my.service",
    // 失败后自动重试其他实例
    client.WithFailureRetry(retry.NewFailurePolicy()),
)
```

### 降级策略

```go
middleware := func(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        err := next(ctx, req, resp)

        if errors.Is(err, kerrors.ErrNoMoreInstance) {
            // 所有实例都不可用，执行降级
            return fallbackResponse(resp)
        }

        return err
    }
}
```

## 相关文档

- [重试配置](./configure-retry.md)
- [超时配置](./configure-timeout.md)
- [自定义 LoadBalancer](./implement-custom-loadbalancer.md)
- [服务配置](./configure-service.md)
