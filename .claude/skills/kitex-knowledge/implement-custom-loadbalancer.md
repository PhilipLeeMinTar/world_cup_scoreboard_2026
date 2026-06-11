# 自定义 LoadBalancer

## 概述

LoadBalancer 负责从实例列表中选择一个实例进行调用。Kitex 支持自定义负载均衡策略。

## LoadBalancer 接口

```go
type Loadbalancer interface {
    // GetPicker 根据服务发现结果创建 Picker
    GetPicker(discovery.Result) Picker
}

type Picker interface {
    // Next 选择下一个实例
    Next(ctx context.Context, request interface{}) discovery.Instance
}
```

## 实现自定义 LoadBalancer

### 轮询负载均衡

```go
type RoundRobinBalancer struct{}

func NewRoundRobinBalancer() *RoundRobinBalancer {
    return &RoundRobinBalancer{}
}

func (b *RoundRobinBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    instances := result.Instances
    return &RoundRobinPicker{
        instances: instances,
        index:     0,
    }
}

type RoundRobinPicker struct {
    instances []discovery.Instance
    index     uint32
}

func (p *RoundRobinPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    idx := atomic.AddUint32(&p.index, 1) - 1
    return p.instances[int(idx)%len(p.instances)]
}
```

### 使用自定义 LoadBalancer

```go
cli, err := myservice.NewClient(
    "my.service",
    client.WithLoadBalancer(NewRoundRobinBalancer()),
)
```

## 高级示例

### 最少连接数负载均衡

```go
type LeastConnectionBalancer struct{}

func (b *LeastConnectionBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    instances := result.Instances

    // 为每个实例初始化连接计数
    connCounts := make(map[string]*int32)
    for _, inst := range instances {
        count := int32(0)
        connCounts[inst.Address().String()] = &count
    }

    return &LeastConnectionPicker{
        instances:  instances,
        connCounts: connCounts,
    }
}

type LeastConnectionPicker struct {
    instances  []discovery.Instance
    connCounts map[string]*int32
}

func (p *LeastConnectionPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    // 找到连接数最少的实例
    var minInst discovery.Instance
    minCount := int32(math.MaxInt32)

    for _, inst := range p.instances {
        addr := inst.Address().String()
        count := atomic.LoadInt32(p.connCounts[addr])

        if count < minCount {
            minCount = count
            minInst = inst
        }
    }

    // 增加连接计数
    if minInst != nil {
        addr := minInst.Address().String()
        atomic.AddInt32(p.connCounts[addr], 1)

        // 请求完成后减少计数
        go func() {
            <-ctx.Done()
            atomic.AddInt32(p.connCounts[addr], -1)
        }()
    }

    return minInst
}
```

### 基于延迟的负载均衡

```go
type LatencyBasedBalancer struct {
    mu        sync.RWMutex
    latencies map[string]*LatencyTracker
}

type LatencyTracker struct {
    totalLatency time.Duration
    requestCount int64
}

func NewLatencyBasedBalancer() *LatencyBasedBalancer {
    return &LatencyBasedBalancer{
        latencies: make(map[string]*LatencyTracker),
    }
}

func (b *LatencyBasedBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    instances := result.Instances

    // 初始化延迟追踪
    b.mu.Lock()
    for _, inst := range instances {
        addr := inst.Address().String()
        if _, exists := b.latencies[addr]; !exists {
            b.latencies[addr] = &LatencyTracker{}
        }
    }
    b.mu.Unlock()

    return &LatencyBasedPicker{
        balancer:  b,
        instances: instances,
    }
}

type LatencyBasedPicker struct {
    balancer  *LatencyBasedBalancer
    instances []discovery.Instance
}

func (p *LatencyBasedPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    // 选择平均延迟最低的实例
    var bestInst discovery.Instance
    minAvgLatency := time.Duration(math.MaxInt64)

    p.balancer.mu.RLock()
    for _, inst := range p.instances {
        addr := inst.Address().String()
        tracker := p.balancer.latencies[addr]

        if tracker.requestCount == 0 {
            // 新实例，给予机会
            bestInst = inst
            break
        }

        avgLatency := tracker.totalLatency / time.Duration(tracker.requestCount)
        if avgLatency < minAvgLatency {
            minAvgLatency = avgLatency
            bestInst = inst
        }
    }
    p.balancer.mu.RUnlock()

    // 记录请求延迟
    start := time.Now()
    go p.recordLatency(ctx, bestInst.Address().String(), start)

    return bestInst
}

func (p *LatencyBasedPicker) recordLatency(ctx context.Context, addr string, start time.Time) {
    <-ctx.Done()
    latency := time.Since(start)

    p.balancer.mu.Lock()
    tracker := p.balancer.latencies[addr]
    tracker.totalLatency += latency
    tracker.requestCount++
    p.balancer.mu.Unlock()
}
```

### 基于请求特征的负载均衡

```go
type FeatureBasedBalancer struct{}

func (b *FeatureBasedBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    // 按标签分组实例
    groups := make(map[string][]discovery.Instance)
    for _, inst := range result.Instances {
        tags := inst.Tag()
        group := tags["group"]
        if group == "" {
            group = "default"
        }
        groups[group] = append(groups[group], inst)
    }

    return &FeatureBasedPicker{groups: groups}
}

type FeatureBasedPicker struct {
    groups map[string][]discovery.Instance
    index  uint32
}

func (p *FeatureBasedPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    // 根据请求特征选择实例组
    req := request.(*myservice.Request)

    var group string
    if req.Priority == "high" {
        group = "high-performance"
    } else if req.Size > 1024*1024 {
        group = "large-file"
    } else {
        group = "default"
    }

    // 在组内轮询
    instances, ok := p.groups[group]
    if !ok || len(instances) == 0 {
        instances = p.groups["default"]
    }

    if len(instances) == 0 {
        return nil
    }

    idx := atomic.AddUint32(&p.index, 1) - 1
    return instances[int(idx)%len(instances)]
}
```

## 结合权重

### 加权随机负载均衡

```go
type WeightedRandomBalancer struct{}

func (b *WeightedRandomBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    instances := result.Instances

    // 计算总权重
    totalWeight := 0
    weights := make([]int, len(instances))
    for i, inst := range instances {
        weight := inst.Weight()
        if weight <= 0 {
            weight = 10  // 默认权重
        }
        weights[i] = weight
        totalWeight += weight
    }

    return &WeightedRandomPicker{
        instances:   instances,
        weights:     weights,
        totalWeight: totalWeight,
    }
}

type WeightedRandomPicker struct {
    instances   []discovery.Instance
    weights     []int
    totalWeight int
}

func (p *WeightedRandomPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    // 随机选择一个权重值
    r := rand.Intn(p.totalWeight)

    // 找到对应的实例
    sum := 0
    for i, weight := range p.weights {
        sum += weight
        if r < sum {
            return p.instances[i]
        }
    }

    return p.instances[len(p.instances)-1]
}
```

## 健康检查集成

### 自动过滤不健康实例

```go
type HealthAwareBalancer struct {
    delegate    loadbalance.Loadbalancer
    healthCheck func(discovery.Instance) bool
}

func (b *HealthAwareBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    // 过滤健康实例
    var healthyInstances []discovery.Instance
    for _, inst := range result.Instances {
        if b.healthCheck(inst) {
            healthyInstances = append(healthyInstances, inst)
        }
    }

    // 如果所有实例都不健康，仍然尝试使用全部实例
    if len(healthyInstances) == 0 {
        healthyInstances = result.Instances
    }

    // 委托给其他负载均衡器
    filteredResult := discovery.Result{
        Instances: healthyInstances,
    }

    return b.delegate.GetPicker(filteredResult)
}
```

## 性能优化

### 无锁实现

```go
type LockFreeRoundRobinBalancer struct{}

func (b *LockFreeRoundRobinBalancer) GetPicker(result discovery.Result) loadbalance.Picker {
    return &LockFreeRoundRobinPicker{
        instances: result.Instances,
    }
}

type LockFreeRoundRobinPicker struct {
    instances []discovery.Instance
    counter   uint64
}

func (p *LockFreeRoundRobinPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    // 使用 atomic 操作避免锁
    n := atomic.AddUint64(&p.counter, 1)
    idx := int(n % uint64(len(p.instances)))
    return p.instances[idx]
}
```

## 最佳实践

### 1. 处理空实例列表

```go
func (p *MyPicker) Next(ctx context.Context, request interface{}) discovery.Instance {
    if len(p.instances) == 0 {
        return nil
    }

    // 正常选择逻辑
    // ...
}
```

### 2. 避免热点

```go
// ✅ 推荐：添加随机偏移避免所有 client 同时访问同一实例
type SmartRoundRobinPicker struct {
    instances []discovery.Instance
    offset    uint32
}

func NewSmartRoundRobinPicker(instances []discovery.Instance) *SmartRobinPicker {
    return &SmartRoundRobinPicker{
        instances: instances,
        offset:    rand.Uint32(),  // 随机起始位置
    }
}
```

### 3. 支持实例更新

```go
// 当服务发现结果变化时，LoadBalancer 会重新调用 GetPicker
// 确保 Picker 是无状态的或正确处理状态迁移
```

## 相关文档

- [负载均衡配置](./configure-loadbalance.md)
- [自定义 Resolver](./implement-custom-resolver.md)
- [服务配置](./configure-service.md)
