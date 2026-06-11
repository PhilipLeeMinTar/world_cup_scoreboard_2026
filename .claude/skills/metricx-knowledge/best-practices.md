# 最佳实践与示例

本文档提供metricx在实际业务场景中的最佳实践和使用示例，帮助开发者高效、规范地使用metricx进行监控打点。

## DB+缓存打点场景

以数据库操作和缓存命中的监控为例，展示如何设计合理的Metric Model结构。

### 需求分析
假设需要以下3个打点：
- `{P.S.M}.db.throughput`：代表数据库吞吐量，每次打点默认携带 `dbname`、`table`、`method`、`error` 4个tag，其中`method`和`error`需要在运行时获取
- `{P.S.M}.db.latency`：代表数据库操作耗时，每次打点默认携带 `dbname`、`table`、`method` 3个tag，其中`method`需要在运行时获取
- `{P.S.M}.cache.hit`：代表缓存命中量，每次打点默认携带 `redis_cluster`、`method` 2个tag，其中`method`需要在运行时获取

### 实现代码
```go
package main

import "code.byted.org/gopkg/metricx"

var ModelCacheMetrics = &struct {
    DB struct {
        Throughput     metricx.Counter   `metric:"throughput" tnames:"error" `
        Latency        metricx.Timer     `metric:"latency"`
    } `prefix:"db" tags:"dbname=demo,table=test" tnames:"method"`
    CacheHitStats      metricx.Gauge     `metric:"cache.hit" tags:"redis_cluster=demo" tnames:"method"`
}{}

func main() {
    // default prefix is `env.PSM()`, specific prefix by `metricx.WithNamespace` Option.
    metricx.MustInit(ModelCacheMetrics)

    ModelCacheMetrics.DB.Throughput.Inc(1, metricx.T{"method", "select"}, {"error", "false"})
    ModelCacheMetrics.DB.Latency.Record(time.Second, metricx.Tags{{"method", "select"}}...)
    ModelCacheMetrics.CacheHitStats.Update(2, metricx.T{"method", "Get"})
}
```

### 设计要点
1. **结构体嵌套**：使用嵌套结构体组织相关metrics，通过`prefix`标签为DB相关metrics统一添加前缀
2. **静态标签**：`dbname`、`table`、`redis_cluster`等固定值使用`tags`标签定义
3. **动态标签**：`method`、`error`等运行时变量使用`tnames`标签定义
4. **类型匹配**：根据统计需求选择合适的打点类型（Counter、Timer、Gauge）

## 同时上报metrics和influxdb

metricx支持配置多个输出源，实现同时向不同存储系统上报metrics。

### 多存储配置示例
```go
package main

import (
    "time"

    "code.byted.org/gopkg/env"
    "code.byted.org/gopkg/metricx"
    "code.byted.org/gopkg/metricx/contrib/influxdb"
)

var m = &struct {
    PingThroughput metricx.Counter        `metric:"ping_throughput"`
    PingLatency    metricx.Timer          `metric:"ping_latency"`
    // influxdb独有的StoreWithTime也支持，需要引入相应的包
    GcPauseAvg     influxdb.StoreWithTime `metric:"gc_pause_avg"`        
}{}

func main() {
    metricx.MustInit(
        m,
        metricx.WithTimeUnit(time.Nanosecond),
        metricx.WithFactories(
            influxdb.Factory("http://boe-influxdb.byted.org:80", "metricx_test", "", ""),
            metricx.BytedMetrics,
        ),
        metricx.WithGlobalTags(map[string]string {
            "pod_name": env.PodName(),
            "host": env.HostIP(), 
            "dc": env.IDC(),
        }),
    )

    m.PingThroughput.Inc(1)
    m.PingLatency.Record(time.Second)
    m.GcPauseAvg.Update(float64(time.Millisecond), time.Now())
}
```

### 配置说明
1. **Factory配置**：使用`WithFactories`选项配置多个输出源
   - `metricx.BytedMetrics`：公司默认的metrics存储
   - `influxdb.Factory`：InfluxDB存储，需要提供连接信息
2. **全局标签**：使用`WithGlobalTags`添加环境信息标签，如`pod_name`、`host`、`dc`等
3. **时间单位**：使用`WithTimeUnit`自定义Timer的耗时单位
4. **特殊类型**：InfluxDB独有的`StoreWithTime`类型也支持，需要引入相应包

## 全局标签配置

为所有打点添加统一的环境信息标签，便于监控数据的聚合和分析。

### 环境标签示例
```go
metricx.MustInit(
    metricsModel,
    metricx.WithGlobalTags(map[string]string {
        "pod_name": env.PodName(),
        "host": env.HostIP(), 
        "dc": env.IDC(),
        "env": env.Env(),
        "region": env.Region(),
    }),
)
```

### 标签选择建议
1. **基础设施标签**：`pod_name`、`host`、`dc`、`region`等
2. **环境标签**：`env`（prod/staging/test等）
3. **业务标签**：根据业务特点添加相关标签
4. **版本标签**：服务版本号，便于追踪版本变更影响

## 耗时单位调整

根据监控需求调整Timer的耗时单位，确保数据精度和可读性。

### 单位配置示例
```go
metricx.MustInit(
    metricsModel,
    metricx.WithTimeUnit(time.Nanosecond),  // 纳秒单位
    // 或
    metricx.WithTimeUnit(time.Microsecond), // 微秒单位（默认）
    // 或  
    metricx.WithTimeUnit(time.Millisecond), // 毫秒单位
    // 或
    metricx.WithTimeUnit(time.Second),      // 秒单位
)
```

### 单位选择指南
1. **高精度需求**：使用`time.Nanosecond`，适用于性能敏感场景
2. **通用场景**：使用`time.Microsecond`（默认），平衡精度和可读性
3. **业务监控**：使用`time.Millisecond`或`time.Second`，便于业务理解

## 命名空间配置

自定义metric name的前缀，覆盖默认的`env.PSM()`。

### 命名空间示例
```go
metricx.MustInit(
    metricsModel,
    metricx.WithNamespace("custom_prefix"),
)
```

### 使用场景
1. **跨服务统一前缀**：多个相关服务使用相同的前缀
2. **特殊命名需求**：需要自定义命名规则的场景
3. **迁移兼容**：从其他监控系统迁移时保持命名一致性

## 代码规范检查

为确保打点代码质量，建议配置相关工具进行代码检查。

### 推荐配置
1. **Golintx**：在MR阶段进行CI检查，避免tag误用
2. **Bytecheck插件**：在IDE编码阶段进行前置检查
3. **打点规范**：遵守公司统一的打点规范和注意点

### 检查要点
1. **tag定义一致性**：确保打点时传入的tag name已在tnames中定义
2. **tag value非空**：避免传入空值的tag
3. **类型匹配**：确保打点方法与metric类型匹配
4. **命名规范**：遵循metric命名规范

## 总结

metricx的最佳实践核心在于：
1. **合理设计Metric Model**：根据业务场景组织metrics结构
2. **灵活配置输出源**：支持多存储同时上报
3. **规范标签管理**：区分静态和动态标签的使用
4. **统一环境信息**：通过全局标签添加基础设施信息
5. **代码质量保障**：利用工具确保打点代码规范性

通过遵循这些最佳实践，可以构建高质量、易维护的监控打点系统，为服务可观测性提供坚实基础。
