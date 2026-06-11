# GDP metrics 组件

## 概述

GDP metrics 组件提供了统一接口、开箱即用的打点功能，不需要任何二次封装。通过简洁的 API，开发者可以方便地记录各种业务指标，包括计数器、计量器、计时器等，同时支持标签管理和自定义前缀。

**代码包**：code.byted.org/gdp/metrics

## 主要特性

- **统一接口**：提供简洁一致的打点 API
- **多种指标类型**：支持 Counter、Meter、Timer、Store 等多种指标
- **自动标签**：默认使用服务 PSM 作为指标前缀
- **标签管理**：支持为指标添加自定义标签
- **上下文集成**：支持为单次请求统一添加标签
- **版本兼容**：支持 V3 版本客户端

## 快速上手

### 基础打点

`gdp/metrics` 默认使用当前服务 PSM 作为前缀：

```go
import "code.byted.org/gdp/metrics"

// 假设 psm: tiktok.demo.api
func RecordMetrics(ctx context.Context) {
    // 计数器，带标签
    metrics.EmitCounter(ctx, "request.count", 1,
        metrics.Tag("cluster", "mock"),
    )

    // 简单计数器
    metrics.EmitCounter(ctx, "request.total", 1)
    metrics.EmitIncrBy(ctx, "request.incr")

    // 速率计数器
    metrics.EmitRateCounter(ctx, "request.rate", 1)

    // 计量器（自动计算速率和总数）
    metrics.EmitMeter(ctx, "request.meter", 1)

    // 计时器（自动生成多个统计指标）
    metrics.EmitTimer(ctx, "request.duration", 150)

    // 存储器（记录当前值）
    metrics.EmitStore(ctx, "queue.size", 100)
}
```

### 自定义前缀

可以变更默认的 PSM 前缀：

```go
import "code.byted.org/gdp/metrics"

func RecordWithCustomPrefix(ctx context.Context) {
    // 使用自定义前缀
    metrics.WithPrefix("custom.service").EmitCounter(ctx, "count", 1)
    // 指标名：custom.service.count
}
```

### 标签管理

为单次请求所有的打点添加统一标签：

```go
import "code.byted.org/gdp/metrics"

func RecordWithTags(ctx context.Context) {
    // 设置全局标签（每个请求只能调用一次）
    metrics.WithTags(ctx,
        metrics.Tag("region", "us"),
        metrics.Tag("env", "prod"),
    )

    // 后续所有指标都会带上 region 和 env 标签
    metrics.EmitCounter(ctx, "biz.count", 1)

    // 排除全局标签，使用自定义标签
    metrics.With(metrics.WithoutCtxTag()).
        EmitCounter(ctx, "special.count", 1,
            metrics.Tag("type", "special"),
        )
}
```

### V3 版本客户端

```go
import "code.byted.org/gdp/metrics"

func UseV3Client(ctx context.Context) {
    metrics.With(metrics.V3()).EmitCounter(ctx, "v3.count", 1)
}
```

## 指标类型详解

### Counter（计数器）
- **EmitCounter**: 基础计数器，可添加标签
- **EmitIncrBy**: 简单的递增计数器（步长为1）
- **EmitRateCounter**: 带速率的计数器

**适用场景**：请求计数、事件计数、错误计数等

### Meter（计量器）
- 自动计算速率和总数
- 输出两个指标：基础计数器和速率计数器
- 指标名：`.meter` 和 `.meter.rate`

**适用场景**：QPS 计算、吞吐量统计等

### Timer（计时器）
- 记录操作耗时
- 自动生成多个统计指标：min/max/avg/sum/counter/百分位数
- 指标名：`.timer.min`、`.timer.max`、`.timer.avg`、`.timer.pct95` 等

**适用场景**：接口延迟、处理时间、响应时间等

### Store（存储器）
- 用于记录当前值类型的指标
- 适合记录队列长度、连接数、内存使用等瞬时状态

**适用场景**：队列长度、并发数、资源使用量等

## 最佳实践

### 命名规范
- 使用有意义的指标名称，反映业务含义
- 采用小写字母和下划线分隔（snake_case）
- 保持命名一致性，避免混用风格
- 指标名应该简洁明了，避免过长

### 标签使用
- 合理使用标签进行维度划分
- 避免标签值过多导致指标爆炸（cardinality）
- 使用 `WithTags` 为单次请求添加通用标签
- 标签键名应该稳定，避免动态生成

### 性能考虑
- 指标收集是轻量级操作，可放心使用
- 避免在热点代码中创建过多不同的指标名
- 合理使用采样率控制指标数量
- 注意标签组合可能带来的指标数量增长

### 指标设计
- 选择合适类型的指标：Counter 用于计数，Timer 用于耗时，Store 用于当前值
- 为关键业务指标设置合理的标签维度
- 考虑指标的聚合和查询需求
- 避免记录敏感信息到指标中

## 相关文档
- [RAL概述](../ral/overview.md) - RAL组件总体介绍
- [RPC资源](../ral/rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](../ral/abase_redis.md) - 缓存资源配置和使用
- [Database资源](../ral/database.md) - 数据库资源配置和使用
- [Eventbus资源](../ral/eventbus.md) - 消息队列资源配置和使用