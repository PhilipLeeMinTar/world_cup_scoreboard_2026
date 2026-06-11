# 高级功能与选项

metricx 提供了一系列选项来满足高级使用需求，这些选项可以在初始化时通过 `metricx.MustInit` 函数传入，用于定制化 metricx 的行为和配置。

## WithFactories

**函数签名**：`func WithFactories(factory factory.Factory, factories ...factory.Factory) Option`

**默认情况**：不使用 `WithFactories` 的情况下，metricx 默认使用 `gopkg/metrics` 上报。

**使用方法**：至少填写一个参数，每次打点会同时向所有的入参 Factory 进行打点。`metricx.BytedMetrics` 对应公司默认的 metrics，如需 influxdb，用法参见最佳实践部分。

**示例代码**：
```go
metricx.MustInit(
    m,
    metricx.WithFactories(
        influxdb.Factory("http://boe-influxdb.byted.org:80", "metricx_test", "", ""),
        metricx.BytedMetrics,
    ),
)
```

## WithNamespace

**函数签名**：`func WithNamespace(namespace string) Option`

**默认情况**：不使用 `WithNamespace` 的情况下，metrics 上报默认使用 `env.PSM()` 作为前缀。

**使用方法**：填入公共前缀，用于覆盖默认的 metric name 前缀。

**示例代码**：
```go
metricx.MustInit(m, metricx.WithNamespace("custom_namespace"))
```

## WithTimeUnit

**函数签名**：`func WithTimeUnit(timeUnit time.Duration) Option`

**默认情况**：不使用 `WithTimeUnit` 的情况下，metricx.Timer 默认以微秒为单位上报耗时。

**使用方法**：填入期待的耗时单位，比如 `time.Nanosecond` 代表单位是纳秒。

**示例代码**：
```go
metricx.MustInit(m, metricx.WithTimeUnit(time.Nanosecond))
```

## WithGlobalTags

**函数签名**：`func WithGlobalTags(tags map[string]string) Option`

**默认情况**：不使用 `WithGlobalTags` 的情况下，influxdb 无默认携带 tags。

**使用方法**：用于添加全局的环境标签，如 pod_name、host、dc 等信息。

**示例代码**：
```go
metricx.MustInit(
    m,
    metricx.WithGlobalTags(map[string]string {
        "pod_name": env.PodName(),
        "host": env.HostIP(), 
        "dc": env.IDC(),
    }),
)
```

## WithDisableTCETags

**函数签名**：`func WithDisableTCETags() Option`

**默认情况**：不使用 `WithDisableTCETags` 的情况下，metrics 默认携带 TCE Tags，比如 host、pod_name、psm 等。

**使用方法**：用于禁用默认的 TCE Tags。

**示例代码**：
```go
metricx.MustInit(m, metricx.WithDisableTCETags())
```

## 默认行为差异

metricx 针对不同的输出源有不同的默认行为：

### metrics 输出源
- **metric name 前缀**：默认从 `env.PSM()` 获得 PSM 作为 metric name 前缀
- **tags**：默认携带 TCE tags，对应 metrics v3 的 `metrics.SetTceTags()`
- **耗时单位**：默认以微秒为单位

### influxdb 输出源
- **metric name 前缀**：无默认前缀。如需前缀请使用 `metricx.WithNamespace`
- **tags**：无默认携带 tags。如需携带本地环境 tag，请使用 `metricx.WithGlobalTags`
- **耗时单位**：默认以微秒为单位

## 使用建议

1. **多存储上报**：使用 `WithFactories` 可以同时向多个存储上报，如同时上报到 metrics 和 influxdb
2. **环境标签**：对于 influxdb 输出，建议使用 `WithGlobalTags` 添加必要的环境信息标签
3. **单位统一**：根据业务需求使用 `WithTimeUnit` 统一耗时单位，确保监控数据的可读性和一致性
4. **命名空间**：使用 `WithNamespace` 可以为特定服务或模块设置统一的 metric 前缀

