# metricx 打点类型详解

metricx 支持5种打点类型，每种类型对应不同的监控场景和统计需求。了解这些打点类型的特点和使用方法，对于设计合理的监控指标体系至关重要。

## 打点类型对应关系

| 打点类型        | metricx 方法     | metrics v3 对应方法  | metrics v2 对应方法             | 主要用途                                   |
| --------------- | ---------------- | -------------------- | ------------------------------- | ------------------------------------------ |
| **Counter**     | Counter.Inc      | Measurer.IncrCounter | MetricsClientV2.EmitCounter     | 累积值统计                                 |
| **RateCounter** | RateCounter.Inc  | Measurer.Inc         | MetricsClientV2.EmitRateCounter | 单位时间累积值统计                         |
| **Gauge**       | Gauge.Update     | Measurer.Store       | MetricsClientV2.EmitStore       | 记录瞬时值                                 |
| **Timer**       | Timer.Record     | Measurer.Observe     | MetricsClientV2.EmitTimer       | 记录耗时，计算min/max/avg/sum/count/分位值 |
| **Histogram**   | Histogram.Record | Measurer.Observe     | MetricsClientV2.EmitTimer       | 记录值，计算min/max/avg/sum/count/分位值   |

## 各类型详细说明

### 1. Counter（累积值统计）

**使用场景**：
- 统计事件发生的总次数
- 记录累积的业务指标
- 如：API调用次数、数据库操作次数、错误发生次数

**示例代码**：
```go
var ModelCacheMetrics = &struct {
    DB struct {
        Throughput metricx.Counter `metric:"throughput" tnames:"error"`
    } `prefix:"db" tags:"dbname=demo,table=test" tnames:"method"`
}{}

// 使用方式
ModelCacheMetrics.DB.Throughput.Inc(1, metricx.T{"method", "select"}, {"error", "false"})
```

### 2. RateCounter（单位时间累积值）

**使用场景**：
- 统计单位时间内的累积值
- 如：QPS（每秒查询数）、TPS（每秒事务数）
- 适用于需要时间维度归一化的场景

### 3. Gauge（瞬时值记录）

**使用场景**：
- 记录当前时刻的瞬时值
- 如：内存使用量、连接池大小、缓存命中数
- 适用于需要监控当前状态的指标

**示例代码**：
```go
var ModelCacheMetrics = &struct {
    CacheHitStats metricx.Gauge `metric:"cache.hit" tags:"redis_cluster=demo" tnames:"method"`
}{}

// 使用方式
ModelCacheMetrics.CacheHitStats.Update(2, metricx.T{"method", "Get"})
```

### 4. Timer（耗时记录）

**使用场景**：
- 记录操作的耗时分布
- 如：API响应时间、数据库查询耗时、缓存访问延迟
- 提供丰富的统计信息：min/max/avg/sum/count/分位值

**示例代码**：
```go
var ModelCacheMetrics = &struct {
    DB struct {
        Latency metricx.Timer `metric:"latency"`
    } `prefix:"db" tags:"dbname=demo,table=test" tnames:"method"`
}{}

// 使用方式
ModelCacheMetrics.DB.Latency.Record(time.Second, metricx.Tags{{"method", "select"}}...)
```

**默认行为**：
- 默认的耗时单位是微秒
- 如需调整单位，请使用 `metricx.WithTimeUnit` 选项

### 5. Histogram（直方图记录）

**使用场景**：
- 记录数值的分布情况
- 如：请求体大小分布、处理数据量分布
- 与Timer类似，但适用于非耗时类型的数值分布统计

## 选择打点类型的指导原则

1. **统计次数用Counter**：当需要统计事件发生的总次数时
2. **统计速率用RateCounter**：当需要统计单位时间内的累积值时
3. **记录状态用Gauge**：当需要记录当前时刻的瞬时状态时
4. **测量耗时用Timer**：当需要记录操作耗时并分析分布时
5. **分析分布用Histogram**：当需要分析数值的分布情况时

## 注意事项

1. **标签使用规范**：打点时仍需遵守[打点规范/注意点](https://bytedance.feishu.cn/wiki/wikcng7lMJAAeysmDtuyhnH5WMe)
2. **标签值处理**：如果tnames里已定义，但打点时未传相应tag或者tag value为空，会填默认tag value为 `-`
3. **未定义标签**：如果打点时传了未定义过的tag name，则会打点失败（与metrics v3一致）
4. **代码检查**：为避免人为误用，建议安装golintx和bytecheck插件进行前置检查

通过合理选择和使用这些打点类型，可以构建出全面、有效的监控指标体系，帮助及时发现和定位系统问题。
