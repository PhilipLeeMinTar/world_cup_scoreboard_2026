# BytedTrace Go SDK 使用指引

> 本文假设你已了解 BytedTrace 基础知识。如需接入 BytedTrace，优先使用框架组件直接接入（见 framework-integration.md），如需业务自定义埋点或裸用 SDK，则阅读本文。

## 代码仓库

| 名称 | 仓库 |
|------|------|
| 接口定义 | `code.byted.org/bytedtrace/interface-go` |
| SDK 实现 | `code.byted.org/bytedtrace/bytedtrace-client-go` |
| 使用 Demo | `code.byted.org/bytedtrace/bytedtrace-go-demo` |

## 引入依赖

```go
go get code.byted.org/bytedtrace/interface-go
go get code.byted.org/bytedtrace/bytedtrace-client-go
```

## 初始化 Tracer

若已使用支持 BytedTrace 的框架（如 kitex、hertz），不需要手动初始化。

```go
import (
    bytedTrace "code.byted.org/bytedtrace/interface-go"
    client "code.byted.org/bytedtrace/bytedtrace-client-go"
)

func initBytedTrace() {
    err := client.InitBytedTracer("your.psm",
        // 没有使用框架时，需手动初始化 logger
        client.SetSpanLogger(loghelper.GetLogger(loghelper.BytedTrace)),
        // 没有框架时 ctx 中没有 logId，需自定义采样种子
        client.SamplingSeed(func(ctx context.Context) uint64 {
            return rand.Uint64()
        }),
    )
    if err != nil {
        panic(err)
    }

    // 注册自定义 metrics tag（在 Init 时调用，不要重复调用）
    bytedTrace.AppendSpanMetricTags(bytedTrace.ServerSpanType, "extra_tag")
    // 注册裸打 metrics
    bytedTrace.RegisterCustomMetric("my_metrics_counter", "custom_tag")
}
```

### TracerOption 配置项

| 配置 | 说明 |
|------|------|
| `SetLogger(lg)` | 自定义 tracer 内部 logger |
| `SetSpanLogger(l)` | 自定义 custom span 日志 |
| `SetServerSpanLogger(l)` | 自定义 server span 日志 |
| `SetClientSpanLogger(l)` | 自定义 client span 日志 |
| `DisableDynamicConfig` | 禁用动态配置 |
| `DisableMetrics` | 禁用 metrics |
| `SamplingSeed(fn)` | 自定义采样种子（ctx 中无 logId 时使用） |
| `AddGlobalTag(key, value, asMetricsGlobalTag)` | 添加全局 tag |

## Tracer API

### 创建 Span

```go
// Server Span（被调方）
span, ctx := bytedTrace.StartServerSpan(ctx, "method_name")

// Client Span（主调方）
span, ctx := bytedTrace.StartClientSpan(ctx, "downstream.psm")

// Custom Span（自定义类型，默认不建索引、不打 metrics）
span, ctx := bytedTrace.StartCustomSpan(ctx, "span_type", "span_name")
// 需要 metrics 时加 EnableEmitSpanMetrics：
span, ctx := bytedTrace.StartCustomSpan(ctx, "span_type", "span_name", bytedTrace.EnableEmitSpanMetrics)
```

### 从 Context 获取 Span

```go
span := bytedTrace.GetSpanFromContext(ctx)
if span != nil {
    span.SetTag("key", "value")
}
```

### 添加 Event 到 Context 中的 Span

```go
bytedTrace.AddEvents(ctx, events...)
bytedTrace.AddInfoLogEvent(ctx, "event_name", "content", tagKvs...)
bytedTrace.AddWarnLogEvent(ctx, "event_name", "content", tagKvs...)
bytedTrace.AddErrorLogEvent(ctx, "event_name", "content", tagKvs...)
bytedTrace.AddFatalLogEvent(ctx, "event_name", "content", tagKvs...)
bytedTrace.AddPanicEvent(ctx, "panicMsg", tagKvs...)
```

### 裸打 Metrics（通过 Context）

```go
bytedTrace.EmitMetricsTimer(ctx, metricsName, value, tagKvs...)
bytedTrace.EmitMetricsRateCounter(ctx, metricsName, value, tagKvs...)
bytedTrace.EmitMetricsStore(ctx, metricsName, value, tagKvs...)
bytedTrace.EmitMetricsCounter(ctx, metricsName, value, tagKvs...)
bytedTrace.EmitMetricsMeter(ctx, metricsName, value, tagKvs...)
```

## Span API

```go
// 结束 Span（所有 Span 都必须调用）
span.Finish()

// 设置 Tag
span.SetTag("key", value)

// 添加 Event
span.AddEvents(events...)

// 裸打 Metrics（需要预注册）
span.EmitMetricsTimer(metricsName, value, tagKvs...)
span.EmitMetricsRateCounter(metricsName, value, tagKvs...)
span.EmitMetricsCounter(metricsName, value, tagKvs...)

// 获取 SpanContext（用于跨进程传递）
ctx := span.GetContext()
```

### 系统内置 Tag 设置方法

| Tag 名称 | 设置方法 | 适用 Span |
|----------|----------|-----------|
| `_is_error` | `bytedTrace.SetIsError(sp, bool)` | server/client |
| `_biz_status_code` | `bytedTrace.SetBusinessStatusCode(sp, int32)` | server/client |
| `_status_code` | `bytedTrace.SetStatusCode(sp, int32)` | server/client |
| `_from_service` | `bytedTrace.SetFromService(sp, string)` | server |
| `_from_cluster` | `bytedTrace.SetFromCluster(sp, string)` | server |
| `_from_dc` | `bytedTrace.SetFromDc(sp, string)` | server |
| `_from_addr` | `bytedTrace.SetFromAddr(sp, interface{})` | server |
| `_to_method` | `bytedTrace.SetToMethod(sp, string)` | client |
| `_to_cluster` | `bytedTrace.SetToCluster(sp, string)` | client |
| `_to_dc` | `bytedTrace.SetToDc(sp, string)` | client |
| `_to_addr` | `bytedTrace.SetToAddr(sp, interface{})` | client |

### StartSpanOption 配置项

```go
bytedTrace.SetStartTime(t time.Time)         // 设置起始时间
bytedTrace.ChildOf(spanCtx)                  // 作为子 span（跨进程串联）
bytedTrace.FollowsFrom(spanCtx)              // 异步子 span
bytedTrace.EnableEmitSpanMetrics             // 开启 span 结束时打 metrics
bytedTrace.DisableEmitSpanMetrics            // 关闭 span 结束时打 metrics
bytedTrace.EnableEmitSpanLog                 // 开启 span 结束时打 trace log
bytedTrace.AsAsyncChildSpan                  // 作为 context 中 span 的异步子 span
```

## Event API

```go
// 生成 Event（不能直接 new）
event := bytedTrace.NewEvent(eventType, eventName)
event := bytedTrace.NewInfoLogEvent(eventName)
event := bytedTrace.NewWarnLogEvent(eventName)
event := bytedTrace.NewErrorLogEvent(eventName)
event := bytedTrace.NewFatalLogEvent(eventName)
event := bytedTrace.NewPanicEvent(panicMsg)

// Event 配置（链式调用）
event.SetTimestamp(t).SetTag("key", value).SetContent("msg").SetEmitMetrics(true)
```

## Metrics 预注册

**使用 SDK 打点前必须在 Init 时完成预注册，且 tags 顺序需和注册时一致，不能缺省或传空字符串。**

> 新版 SDK 支持 Span Tag 白名单功能，可参考 FAQ 文档使用，无需预注册也能把 tag 添加进指标。

```go
// 在 server/client span 默认 metrics 中加自定义 tag
bytedTrace.AppendSpanMetricTags(bytedTrace.ServerSpanType, "my_tag")
bytedTrace.AppendSpanMetricTags(bytedTrace.ClientSpanType, "my_tag")

// 注意：AppendSpanMetricTags 会影响接口 P99 统计，请谨慎使用

// 为 Event metrics 注册 tag（Log 类型的 eventType 为 "log"）
bytedTrace.AppendEventMetricTags("log", "my_tag")

// 注册裸打指标
bytedTrace.RegisterCustomMetric("my_metrics_counter", "tag1", "tag2")
```

## Span 继承传递

### 进程内（推荐用 context 传递）

```go
// 方式 1：通过 context 传递（parent 和 child 在同一 transaction）
parent, ctx := bytedTrace.StartServerSpan(ctx, "parent")
child, ctx := bytedTrace.StartClientSpan(ctx, "child")

// 方式 2：通过 SpanContext 传递（两者不在同一 transaction）
child, ctx := bytedTrace.StartClientSpan(ctx, "child", bytedTrace.ChildOf(parent.GetContext()))
```

> 异步 goroutine 场景参考 FAQ 文档。

### 跨进程（Inject / Extract）

```go
// 服务 A（上游）：注入 span context 到 carrier
clientSpan, _ := bytedTrace.StartClientSpan(ctx, "client")
carrier := make(map[string]string)
bytedTrace.Inject(clientSpan.GetContext(), bytedTrace.TextMap, bytedTrace.TextMapCarrier(carrier))
// 由框架或 http header 将 carrier 传递给下游

// 服务 B（下游）：从 carrier 解析 span context
spanCtx, err := bytedTrace.Extract(bytedTrace.TextMap, bytedTrace.TextMapCarrier(carrier))
if err == nil {
    serverSpan, _ := bytedTrace.StartServerSpan(ctx, "server", bytedTrace.ChildOf(spanCtx))
    serverSpan.Finish()
}
clientSpan.Finish()
```

## 后置采样

```go
// LocalTrace 采样
bytedTrace.SamplingTrace(span, bytedTrace.LocalTrace)
// PostTrace 采样
bytedTrace.SamplingTrace(span, bytedTrace.PostTrace, bytedTrace.SetSamplingTraceRootSpanContext(cspan.GetContext()))
// DebugTrace 采样
bytedTrace.SamplingTrace(span, bytedTrace.DebugTrace)
// BothSideTrace 采样
bytedTrace.SamplingTrace(span, bytedTrace.BothSideTrace, bytedTrace.SetSamplingTraceRootSpanContext(cspan.GetContext()))
```

## 接入验证

进入 [Argos -> APM -> Trace 搜索](https://cloud.bytedance.net/argos/trace/retrieve/conditionRetrieve)，选择你的 PSM，若有数据则接入成功。

> 如何查找具体指标名和 Tag，参考 **[metrics-schema.md](references/metrics-schema.md)** 的"快速查找指标"章节。
