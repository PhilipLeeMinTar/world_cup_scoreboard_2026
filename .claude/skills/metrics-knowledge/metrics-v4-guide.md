# Metrics 2.0 Go SDK 使用指南

## 概述

metrics/v4 是字节跳动推出的最新一代 metrics Go SDK，在 metrics/v3 基础上进行了大量更新，核心的编码模块升级到 codec-2.0 私有编码，原生支持后端的 Metrics-2.0，为用户提供了更丰富的功能。目前 V2（V1）、V3、V4 可以一起使用，不会互相影响。

## 面向业务价值

### 新功能支持
- **多租户支持**：SDK 侧做到配置隔离、资源隔离，后端支持独立的存储集群
- **新增打点类型**：包括多值 Timer、Histogram，以及自定义多值
- **打点精度定制化**：最高可支持秒级打点

### 成本与性能优化
- **降低存储成本**：使用多值 Metric 类型，可降低 50-90% 的存储空间
- **SDK 侧数据聚合**：完全在 SDK 侧完成数据聚合，降低 80% 以上数据发送频率，减少 50% 以上数据发送量，降低 metrics agent 90% CPU 负载，95% 内存负载，彻底解决写入链路丢点
- **查询性能提升**：多值模型下支持多个 Field 之间查询加速，提高查询效率

### 数据标准化
- SDK 根据环境自动注入标准 Tag，方便用户和平台进行数据治理

## 工程接入

### 安装
```bash
go get code.byted.org/gopkg/metrics/v4
```

仓库地址：https://code.byted.org/gopkg/metrics

## V4 原生 API 接入示例

### 创建 Client
```go
package main

import (
    "fmt"
    "math/rand"
    "time"

    m "code.byted.org/gopkg/metrics/v4"
)

var client m.Client
var metric m.Metric

func init() {
    var err error
    client, err = m.NewClient("metrics.sdk.demo", m.SetTenant("xxxxxxx")) // Must be a valid tenant
    if err != nil {
        panic(fmt.Sprintf("failed to create the client: %v\n", err))
    }

    metric, err = client.NewMetricWithOps("my.metric", []string{"tag0", "tag1", "tag2"},
        m.SetHistogramBucket(m.LinearBuckets(1.0, 2.5, 3)), // Start is 1.0, Width is 2.5, Count is 3
        m.SetMultiFieldTimer(),
    )
    if err != nil {
        fmt.Printf("failed to create the metric: %v\n, the metric is a noop instance", err)
    }
}
```

### 打点操作
```go
func main() {
    ticker := time.NewTicker(3 * time.Second)
    for _ = range ticker.C {
        err := metric.WithTags(
            m.T{"tag0", "value0"},
            m.T{"tag1", "value1"},
            m.T{"tag2", "value2"},
        ).Emit(
            m.Add(1),                     // DeltaCounter类型，多值指标，默认后缀：delta_counter
            m.IncrCounter(rand.Intn(10)), // Counter类型，默认后缀：counter
            m.Incr(rand.Intn(10)),        // RateCounter类型，默认后缀：rate
            m.Store(rand.Intn(10)),       // Store类型，默认后缀：store
            m.Observe(rand.Intn(500)),    // Timer类型，默认后缀：timer
            m.Stat(rand.Intn(500)),       // Histogram类型，多值指标，默认后缀：histogram
        )

        if err != nil {
            fmt.Printf("failed to emit metric: %v\n", err)
        }
    }
}
```

上述示例会创建 6 个指标，分别是多值 DeltaCounter 类型、Counter 类型、RateCounter 类型、Store 类型、多值 Timer 类型，以及多值 Histogram 类型。指标名包含三部分：由 client 前缀、metric 中缀、用户使用打点 API 的后缀。如果是多值指标，还会有额外的 Field 信息。

## 创建 Metric 的注意事项

- **Metric 一般为全局变量**：不可频繁创建新的 Metric。一个 Client 下最多支持 1024 个 Metric（中缀）
- **指标名区分**：具体的指标名应该用 `WithSuffix(suffix string)` 来区分
- **错误处理**：请捕捉 `NewMetric` 返回的 error，确保 metric 创建成功
- **迁移注意事项**：如果是 1.0 SDK 迁移到 2.0 SDK 的场景且使用多值功能，需避免指标名一致，否则会导致多值指标查不到数据

## 自定义输出方式

metrics SDK 会把指标上报给 metrics agent（metricserve2），但也支持用户自己实现 `io.WriteCloser` 接口。这个功能一般用于 debug 或者转发数据，大部分用户无需修改。

示例：
```go
type redirectWriter struct {} 

func (w *redirectWriter) Write(b []byte) (int, error) {
    fmt.Println("[redirected writer]", len(b), b)
    return len(b), nil
}

func (w *redirectWriter) Close() error {
    return nil
}

var client m.Client

func init() {
    var err error
    client, err = m.NewClient("metrics.sdk.demo",
        m.SetWriter(&redirectWriter{}),
    )
}
```

## 性能测试报告

详细的性能测试报告可参考：[metrics/v4] 性能测试报告

## 可视化入口

Metrics-FE 入口：https://metrics-fe.byted.org/web/plot/metrics#

