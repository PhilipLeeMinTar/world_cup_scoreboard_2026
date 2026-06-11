# BytedTrace Metrics Schema Reference

> **重要**：BytedTrace metrics 无论 span 是否被采样，都会**全量上报**。

## 快速查找指标（Argos UI）

1. 进入 [Argos -> APM -> Trace 搜索](https://cloud.bytedance.net/argos/trace/retrieve/conditionRetrieve)，选中目标 PSM
2. 左上角选择"索引对象"：Server[接口调用] / Client[调用下游] / Event/Log / 自定义
3. 查看右侧"指标展示"，展开"查看更多指标"
4. 点击指标右上角超链接图标，跳转 Metrics 页面查看指标查询明细

## Global Tags

All BytedTrace 2.0 metrics include these tags:

- `_psm`, `_dc`, `_cluster`, `_env`
- `_ipv4`, `_ipv6`, `_pod_name`, `_deploy_stage`

## 1. Span Metrics (`family: span`)

### Metric Suffixes

| Suffix                   | Type        | Meaning                           |
|:-------------------------|:------------|:----------------------------------|
| `$type.latency.us.pct99` | timer       | Duration P99 (microseconds)       |
| `$type.rate`             | rateCounter | Frequency (QPS)                   |
| `$type.send.bytes`       | rateCounter | Send size (Client/Server only)    |
| `$type.receive.bytes`    | rateCounter | Receive size (Client/Server only) |
| `$type.mq_lag.us`        | timer       | MQ consumer lag (Consumer span only) |

### Server Spans (`span_type=server`)

**Tags:**

- `_method`: Interface name
- `_status_code`: Status code
- `_is_error`: 0=Success, 1=Fail
- `_biz_status_code`: Business status code
- `_service_type`: e.g., http, thrift
- `_from_service`: Remote client PSM
- `_from_cluster`, `_from_dc`: Remote client location
- `_from_addr`: Remote IP (Error requests only)
- Custom fields via `AppendSpanMetricTags`

### Client Spans (`span_type=client`)

**Tags:**

- `_method`: Local interface where the call originated
- `_status_code`: Status code
- `_is_error`: 0=Success, 1=Fail
- `_biz_status_code`: Business status code
- `_to_service`: Remote server PSM
- `_to_method`: Remote interface name
- `_to_service_type`: e.g., http, thrift, mysql, redis
- `_to_cluster`, `_to_dc`: Remote server location
- `_to_addr`: Remote IP (Error requests only)
- Custom fields via `AppendSpanMetricTags`

### Custom Spans (`span_type=<custom>`)

Custom spans do **not** emit metrics by default. Enable via `EnableEmitSpanMetrics` option.

**Tags:**

- `_name`: Span name (defined in `StartCustomSpan`)
- `_status_code`: Status code
- Custom fields via `AppendSpanMetricTags`

## 2. Event Metrics (`family: event`)

### Log Events

**Metric**: `bytedtrace.sdk.event.log.rate`
**Tags**:

- `_name`: EventName (set in `NewXXLogEvent(eventName)`)
- `_method`: Context interface name where the event occurred
- `_log_level`: 0:Trace, 1:Debug, 2:Info, 3:Notice, 4:Warn, 5:Error, 6:Fatal
- *Note*: Default only outputs Warn (4) and above.
- Custom fields via `AppendEventMetricTags`

### Custom Events

Custom events do **not** emit metrics by default. Enable via `event.SetEmitMetrics(true)`.

**Tags:**

- `_name`: EventName (set in `NewEvent(eventType, eventName)`)
- `_method`: Context interface name where the event occurred
- Custom fields via `AppendEventMetricTags`

## 3. Internal & Custom Metrics

### Custom (`family: custom`)

- **Metric**: `bytedtrace.sdk.custom.<name>`
- **Tags**: Fully custom, registered via `RegisterCustomMetric(metricsName, tagNames...)`.

### Internal (`family: internal`)

- **Error Rate**: `bytedtrace.sdk.internal.error.rate` (Tag: `type` — see [error type definitions](https://code.byted.org/bytedtrace/bytedtrace-client-go/blob/develop/stat/errors.go))
- **Op Rate**: `bytedtrace.sdk.internal.op.rate` (Tag: `name`, values: `txn.report.qps`, `txn.report.Bps`)

## Aggregation & Rewrite Rules

### Tag Rewrites

The system automatically rewrites specific metric prefixes to optimize tag cardinality:

- `bytedtrace.sdk.span.server` -> `_psm`
- `bytedtrace.sdk.span.client` -> `_psm`, `_to_service`
- `bytedtrace.sdk.event.log` -> `_psm`

### Pre-Aggregation Keys

High-cardinality metrics (Client Rate, Client Latency, Server Rate, Server Latency) are pre-aggregated on the following
dimensions. Queries outside these dimensions may be slow or unavailable:

`dc`, `_psm`, `_dc`, `_cluster`, `_env`, `_deploy_stage`, `_status_code`, `_is_error`, `_biz_status_code`, `_method` (or
`_to_method`), `_service` (or `_to_service`/`_from_service`), `_cluster` (to/from), `_dc` (to/from).
