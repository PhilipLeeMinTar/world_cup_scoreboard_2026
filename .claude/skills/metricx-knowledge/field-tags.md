# 字段标签配置详解

metricx通过结构体字段标签来定义metric的元信息，这是代码生成的重要依据。以下是各种字段标签的详细说明和使用方法。

## metric标签

**作用**：定义metric name后缀

**格式**：`metric:"metric_name_suffix"`

**示例**：`metric:"dbread.throughput"`

**说明**：
- 打点时作为metric name后缀，与metric name前缀组合成完整的metric name
- 有关前缀的默认行为，请参考[默认行为](https://bytedance.feishu.cn/wiki/wikcn47Tm9E3ybFg65w7cO8By7d#JG2UO7)部分

## prefix标签

**作用**：为嵌套结构体中的字段统一添加metric name前缀

**格式**：`prefix:"prefix_name"`

**示例**：`prefix:"dbread"`

**说明**：
- 用于嵌套结构体，在任意一层的结构体上加这个tag都可以给结构体内字段统一加`{prefix}.`前缀
- 支持多层嵌套，内层字段会继承外层结构体上的prefix标签

## tags标签

**作用**：定义静态键值对标签

**格式**：`tags:"k1=v1,k2=v2"`

**示例**：`tags:"dbname=demo,table=test"`

**说明**：
- 在打点上报时会携带这组键值对作为tags
- 适用于tag键值均已知的情况
- 多个键值对用逗号分隔

## tnames标签

**作用**：定义预定义tag name，允许打点时动态传入对应的value

**格式**：`tnames:"k1,k2,k3"`

**示例**：`tnames:"method,error"`

**说明**：
- 在打点上报时允许临时传预定义tag name及对应的value
- 例如：`m.Throughput.Inc(1, metricx.Tags{{"k1", "v1"}}...)`

**使用规范**：
1. 打点时仍需遵守[打点规范/注意点](https://bytedance.feishu.cn/wiki/wikcng7lMJAAeysmDtuyhnH5WMe)
2. 如果tnames里已定义，但打点时未传相应tag或者tag value == ""的话，会填默认tag value为 `-`
3. 如果打点时传了未定义过的tag name，则会打点失败（与metrics v3一致）
4. 为避免人为的误用出现，强烈建议：
   - 代码仓库[安装golintx](https://bytedance.feishu.cn/wiki/wikcnBkIkxzO8CjZi7e5X5BzdJe#nwptVq)，在mr阶段会有CI检查做卡点
   - IDE[安装bytecheck插件](https://bytedance.feishu.cn/wiki/wikcnzVd8P6wPCZe4cBufoLLdye)，在编码阶段可以前置检查

## 嵌套结构体的标签继承

Model支持结构体嵌套，嵌套的情况下，内层字段会继承外层结构体上的struct tag，包括tnames、tags、prefix。这适用于批量为一些metric配置公共元信息。

**示例**：
```go
var ModelCacheMetrics = &struct {
    DB struct {
        Throughput     metricx.Counter   `metric:"throughput" tnames:"error" `
        Latency        metricx.Timer     `metric:"latency"`
    } `prefix:"db" tags:"dbname=demo,table=test" tnames:"method"`
    CacheHitStats      metricx.Gauge     `metric:"cache.hit" tags:"redis_cluster=demo" tnames:"method"`
}{}
```

在这个示例中：
- `DB.Throughput`的完整metric name为：`{prefix}.db.throughput`
- `DB`结构体上的`tags:"dbname=demo,table=test"`会被`DB.Throughput`和`DB.Latency`继承
- `DB`结构体上的`tnames:"method"`会被`DB.Throughput`和`DB.Latency`继承

## 标签组合使用最佳实践

在实际使用中，可以根据业务需求灵活组合各种标签：

1. **静态配置**：使用`tags`标签定义不变的标签
2. **动态参数**：使用`tnames`标签定义运行时传入的标签
3. **命名空间**：使用`prefix`标签组织相关metrics
4. **metric命名**：使用`metric`标签定义具体的metric名称

通过合理的标签组合，可以构建出清晰、可维护的监控指标体系。
