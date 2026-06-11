# Metrics Golang SDK 接入指南

Metrics SDK 是整个 Metrics 写入链路的第一环，是公司内业务接入 Metrics 系统的标准方式。Metrics Go SDK 是公司内部使用最多的基础库之一，接入了超过 50000 个 PSM，目前线上主要使用 V2、V3 和 V4 三个版本。

## 前置条件

Metrics 在每台物理机/云主机都有部署名为 `metricserver2` 的 agent，该 agent 负责收集 SDK 打过来的指标，并且每 30s 进行一次**序列内**、**时间纬度**上的聚合，然后发送给 Metrics 后端。SDK 依赖 metricserver2 向后传递数据，因此用户需要确保 Metrics Agent 在本机上部署。

**物理机环境检查**：检查 metricserver2 进程是否运行：

```bash
ps aux | grep metricserver2
```

**容器环境检查**：检查以下目录 `/opt/tmp/sock`，确认 socket 文件是否存在。

## 工程接入

仓库：https://code.byted.org/gopkg/metrics

```bash
# 接入 V4（推荐）
go get code.byted.org/gopkg/metrics/v4

# 接入 V3
go get code.byted.org/gopkg/metrics/v3

# 接入 V2
go get code.byted.org/gopkg/metrics
```

## 各版本特性对比

### V4 版本（推荐）
- **状态**：最新一代 SDK，推荐使用
- **发布时间**：2022年11月10日
- **特点**：在 V3 基础上进行大更新，绝大多数 API 保持兼容，核心编码模块升级到 codec-2.0 私有编码，原生支持后端的 Metrics-2.0
- **功能**：提供更丰富的功能，包括对 V2 的兼容性 API（v4.0.19 之后）
- **性能**：打点性能提升 10%-100%
- **最佳实践**：[[metrics/v4] Metrics-2.0 Go SDK用户使用指南](https://bytedance.feishu.cn/wiki/wikcndhGxB3yS3eEAXoQvB5G8jg)

### V3 版本
- **状态**：当前主要使用版本
- **特点**：解决了 V2 中的丢点问题，并发性能较 V2 有明显的提升
- **兼容性**：与 V2、V1 的 API 不兼容，但可以与 V1、V2 一同使用
- **性能提升**：在绝大多数场景下都有 50% 以上的性能提升
- **GoDoc**: https://code.byted.org/godoc/code.byted.org/gopkg/metrics/v3/

### V2 版本
- **状态**：不推荐新项目使用
- **特点**：早期版本，存在丢点问题
- **性能**：相对较低，并发性能不如后续版本
- **Go Doc**: https://code.byted.org/godoc/code.byted.org/gopkg/metrics

## 使用 V4 Client

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
   client, err = m.NewClient("metrics.sdk.demo.v4")
   if err != nil {
      panic(fmt.Sprintf("failed to create the client: %v\n", err))
   }

   metric, err = client.NewMetricWithOps("my.metric", []string{"tag0", "tag1", "tag2"},
      m.SetHistogramBucket(m.LinearBuckets(1, 2, 3)),
      m.SetMultiFieldTimer(),
   )
   if err != nil {
      fmt.Printf("failed to create the metric: %v\n, the metric is a noop instance", err)
   }
}

func main() {
   ticker := time.NewTicker(3 * time.Second)
   for _ = range ticker.C {
      err := metric.WithTags(
         m.T{"tag0", "value0"},
         m.T{"tag1", "value1"},
         m.T{"tag2", "value2"},
      ).Emit(
         m.Add(rand.Intn(10)),          // DeltaCounter类型，多值指标，默认后缀：delta_counter
         m.IncrCounter(rand.Intn(10)), // 不推荐，Counter类型, 默认后缀:counter
         m.Incr(rand.Intn(10)),        // RateCounter类型，默认后缀：rate
         m.Store(rand.Intn(10)),       // Store类型, 默认后缀：store
         m.Observe(rand.Intn(500)),    // Timer类型，默认后缀:timer
         m.Stat(rand.Intn(500)),       // Histogram类型,默认后缀histogram
      )

      if err != nil {
         fmt.Printf("failed to emit metric: %v\n", err)
      }
   }
}
```

上述示例会创建 6 个指标，分别是 DeltaCounter 类型、Counter 类型、RateCounter 类型、Store 类型、多值 Timer 类型，以及多值 Histogram 类型。指标名由 client 前缀、metric 中缀、用户使用打点 API 的后缀三段拼接组合而成，如果是多值指标，还会有额外的 Field 信息：

```
metrics.sdk.demo.v4.my.metric.delta_counter
    [delta,rate,counter]
metrics.sdk.demo.v4.my.metric.counter
metrics.sdk.demo.v4.my.metric.rate
metrics.sdk.demo.v4.my.metric.store
metrics.sdk.demo.v4.my.metric.timer
    [min, max, avg, sum, counter, pct50, pct90, pct95, pct99, pct995]
metrics.sdk.demo.v4.my.metric.histogram
    [hist:b-1, hist:b-3, hist:b-5, hist:sum, hist:count]
```

## 使用 V3 Client

```go
package main

import (
   "fmt"
   "time"

   "code.byted.org/gopkg/metrics/v3"
)

var client metrics.Client
var metric metrics.Metric

func init() {
   // 需要注意：client、metric 创建后应保持全局引用，请勿每次打点都去NewClient、NewMetric
   client = metrics.NewClient("metrics.sdk.demo.v3", metrics.SetTceTags())
   metric = client.NewMetric("my.metric", "tag0", "tag1", "tag2")
}

func main() {
   ticker := time.NewTicker(3 * time.Second)
   for _ = range ticker.C {
      err := metric.WithTags(
         metrics.T{"tag0", "value0"},
         metrics.T{"tag1", "value1"},
         metrics.T{"tag2", "value2"},
      ).Emit(
         metrics.Store(1), // 默认后缀"store"
         metrics.Incr(2),  // 默认后缀"rate"
         metrics.WithSuffix("float.rate").Incrf(3.0),    //指定后缀"float.rate"
         metrics.WithSuffix("myCounter").IncrCounter(1), //用户指定后缀"myCounter"
         metrics.WithSuffix("latency").Observe(10),      //用户指定后缀"latency"
      )

      if err != nil {
         fmt.Println("err is", err)
      }
   }
}
```

这会创建 14 个指标，分别是 Store 类型、两个 RateCounter 类型、Counter 类型和 Timer 类型展开的 10 个指标。指标名由 client、metric、用户使用的打点 API 三段拼接组合而成，如果是 Timer 类型指标还会额外展开成 10 个统计信息：

```
metrics.sdk.demo.v3.my.metric.store         // a Store metric with default suffix
metrics.sdk.demo.v3.my.metric.rate          // a RateCounter metric with default suffix
metrics.sdk.demo.v3.my.metric.float.rate    // a RateCounter metrics with a customized suffix
metrics.sdk.demo.v3.my.metric.myCounter     // a Counter metric with a customized suffix
// A Timer metric will be extended to 10 metrics:
metrics.sdk.demo.v3.my.metric.latency.min
metrics.sdk.demo.v3.my.metric.latency.max
metrics.sdk.demo.v3.my.metric.latency.avg
metrics.sdk.demo.v3.my.metric.latency.sum
metrics.sdk.demo.v3.my.metric.latency.counter
metrics.sdk.demo.v3.my.metric.latency.pct50
metrics.sdk.demo.v3.my.metric.latency.pct90
metrics.sdk.demo.v3.my.metric.latency.pct95
metrics.sdk.demo.v3.my.metric.latency.pct99
metrics.sdk.demo.v3.my.metric.latency.pct999
```

## 使用 V2 Client

```go
package main

import (
   "time"

   "code.byted.org/gopkg/metrics"
)

func main() {
   //Step 1: 初始化metrics client & 声明metrics 前缀"metrics.sdk.demo.v2"
   // set nocheck=true to disable metric definitions
   cli := metrics.NewDefaultMetricsClientV2("metrics.sdk.demo.v2", true)

   //Step 3: 打点，带上额外tagkV： "product" & "app"
   _ = cli.EmitStore("my.metric.store", 1,
      metrics.T{"product", "toutiao"},
      metrics.T{"app", "news_article"})

   _ = cli.EmitRateCounter("my.metric.rate", 1,
      metrics.T{"product", "toutiao"},
      metrics.T{"app", "news_article"})

   _ = cli.EmitRateCounter("my.metric.float.rate", 2.0,
      metrics.T{"product", "toutiao"},
      metrics.T{"app", "news_article"})

   _ = cli.EmitCounter("my.metric.myCounter", 1,
      metrics.T{"product", "toutiao"},
      metrics.T{"app", "news_article"},
   )

   _ = cli.EmitTimer("my.metric.latency", 1,
      metrics.T{"product", "toutiao"},
      metrics.T{"app", "news_article"})

   // 出于性能考虑数据异步，maxPendingSize=1000 or emitInterval=200ms 两个条件满足之一才发送
   time.Sleep(1 * time.Second)
}
```

这同样会创建 14 个指标：

```
metrics.sdk.demo.v2.my.metric.store
metrics.sdk.demo.v2.my.metric.rate
metrics.sdk.demo.v2.my.metric.float.rate
metrics.sdk.demo.v2.my.metric.myCounter
// A Timer metric will be extended to 10 metrics:
metrics.sdk.demo.v2.my.metric.latency.min
metrics.sdk.demo.v2.my.metric.latency.max
metrics.sdk.demo.v2.my.metric.latency.avg
metrics.sdk.demo.v2.my.metric.latency.sum
metrics.sdk.demo.v2.my.metric.latency.counter
metrics.sdk.demo.v2.my.metric.latency.pct50
metrics.sdk.demo.v2.my.metric.latency.pct90
metrics.sdk.demo.v2.my.metric.latency.pct95
metrics.sdk.demo.v2.my.metric.latency.pct99
metrics.sdk.demo.v2.my.metric.latency.pct999
```

## 接入验证

用户可以使用 strace 命令来跟踪进程执行时的系统调用和所接收的信号。SDK 是通过 write 系统调用来发送数据的，因此我们可以用 strace 命令判断 SDK 是否正确地写出了数据：

```bash
$ pid=`pgrep -f {your program}`
$ strace -f -s 65535 -p $pid 2>&1 | grep "{your metric name}"
```

若能看到 SDK 正确地发送了数据，则说明业务侧正确地使用了 SDK，接入成功。

## 升级建议

1. **新项目**：推荐直接使用 V4 版本
2. **现有 V2 项目**：可升级到 V4 的兼容性 API，改造成本低
3. **现有 V3 项目**：可平滑升级到 V4，API 基本保持兼容

## V4 与 V3 不兼容性说明

V4 与 V3 存在一些不兼容的部分：

1. **API 返回值**：V4 的 NewClient 和 NewMetric 新增 error 返回值
2. **重名 metric**：V4 同一个 Client 下默认不支持定义多个重名 Metric
3. **Metric name**：V4 不支持定义空名 Metric
4. **重名 tag key**：V4 不允许重名 tag key
5. **合法 string 规则**：V4 对字符串格式有更严格的限制