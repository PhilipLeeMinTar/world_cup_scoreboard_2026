# EventBus SDK 使用指南 - client-go

## 概述

**EventBus** 是一个通用的、大规模、分布式的消息中间件平台。它为业务方提供了可靠、高可用、高性能的消息生产与消费服务，旨在解耦上下游业务系统。

**特性**：
- 可靠的消息生产与消费
- 支持同步、异步、批量发送
- 支持有序消费
- 支持延迟消息
- 支持消息重试与死信队列
- 集成字节内部中间件生态

**代码包**：
- `code.byted.org/eventbus/client-go`
- `code.byted.org/eventbus/client-go/legacy`

## 适用场景

- **异步任务解耦**：例如，用户注册后，通过发送消息来触发积分、优惠券发放等多个下游系统。
- **最终一致性事件**：通过可靠的消息投递与重试，确保状态变更事件最终能被所有相关方处理。
- **削峰填谷**：应对突发流量，将请求放入消息队列，消费者按自身处理能力平稳消费。
- **延迟任务**：如订单创建 30 分钟后未支付则自动取消。
- **有序事件流**：如同一订单的状态变更（创建、支付、发货、完成）需要按顺序处理。

## 消息生命周期

一个事件的完整生命周期包括：
1. **生产（Produce）**：业务方通过 SDK 将消息发送到 EventBus。
2. **存储（Store）**：EventBus 将消息持久化到后端存储（如 RocketMQ、BMQ）。
3. **分发（Dispatch）**：EventBus 根据订阅关系将消息推送给对应的消费组。
4. **消费（Consume）**：消费者 SDK 拉取消息并交由业务逻辑处理。
5. **确认（Acknowledge）**：业务处理完成后，SDK 向 EventBus 确认消息，EventBus 更新消费位点。
6. **重试（Retry）**：若消费失败，EventBus 会根据配置的策略（本地或远端）进行重试，直至成功或达到最大次数后进入死信队列。

## 边界与限制

- 主要提供**至少一次（At-Least-Once）**的投递语义，业务侧需自行处理消费幂等。SDK v1.16.0+ 提供了基于 Redis 的幂等消费辅助功能。
- 异步远端重试最大次数为 **16 次**。
- 延迟消息精度为秒级，存在约 ±1s 的误差，最大支持 **15 天**的延迟。

## 生产者 (Producer)

### 初始化方式

**1. 极简 API（推荐）**

适用于配置全部通过控制台管理的场景。SDK 会懒加载并缓存 Producer 实例，24 小时未使用后自动清理。

```go
// 无需手动创建 Producer，直接发布
import eventbus "code.byted.org/eventbus/client-go"
eventbus.Publish(ctx, event)
```

**2. 通用 SDK**

需要更精细的本地配置时使用。推荐在服务启动时创建**单例** Producer，并管理其生命周期。

```go
import eventbus "code.byted.org/eventbus/client-go"

// 1. 创建配置
conf, err := eventbus.NewProducerConfig(eventName, psm)
if err != nil {
    // handle error
}
// 2. 自定义配置
conf.Producer.SendTimeout = 3 * time.Second
// ... 其他配置

// 3. 创建 Producer 实例
producer, err := eventbus.NewProducer(conf)
if err != nil {
    // handle error
}
```

### 关键配置

这些配置既可以在 `NewProducerConfig` 后通过代码设置，也可以在 **EventBus 控制台**进行动态修改（**控制台优先级更高**）。

- `SendTimeout`: **单次发送超时**。同步发送或批量发送单次请求的超时时间。SDK 在此时间内会自动重试。
- `Retry`: **重试次数**。发送失败时的最大自动重试次数。
- `RetryInterval`: **重试间隔**。两次重试之间的等待时间。
- `AsyncQueueCount`: **异步队列数量**。异步发送时内部处理队列的数量，默认为 `max(2 * CPU核心数, 8)`。
- `AsyncBufferSize`: **异步 Buffer 大小**。异步发送时本地 channel 缓存的消息数量。
- `AsyncChanTimeout`: **异步入 chan 超时**。当本地 buffer 满时，消息进入 channel 的等待超时时间。

### 消息对象字段

通过 `eventbus.NewProducerEventBuilder()` 链式构建：

- `WithKey(key []byte)` / `WithKeyString(key string)`: **消息 Key**。用于分区路由，相同 Key 的消息会被发送到同一个分区，是实现**有序消费**的前提。也用于在控制台查询消息。
- `WithTag(tag string)` / `WithTags(tags []string)`: **消息 Tag**。用于消费端进行消息过滤。
- `WithId(id string)`: **消息 ID**。消息的唯一标识。不设置时 SDK 会自动生成。消费端可用于幂等判断。
- `WithDelay(duration time.Duration)`: **延迟时间**。用于发送延迟消息。
- `WithHeader(key, value string)` / `WithHeaders(headers map[string]string)`: **消息头**。用于传递自定义的元数据，例如链路追踪的 `logid`、泳道标识等。
- `WithSearchKey(key []byte)`: **搜索 Key**。专门用于在 EventBus 控制台进行消息搜索的 Key，与路由无关。
- `WithValue(value []byte)`: **消息体**。实际的业务数据，通常是序列化后的 JSON、Protobuf 等。

### 生命周期管理

- 对于**通用 SDK**，Producer 应该是**单例**的，在服务启动时创建，在服务关闭时销毁。
- 如果使用了**异步发送 (`SendAsync`)**，必须在服务正常退出前调用 `producer.Close()` 方法。此方法会阻塞，直到内部缓存的消息全部发送完成或超时，以防止消息丢失。

```go
// 在服务关闭的钩子中调用
if producer != nil {
    if err := producer.Close(); err != nil {
        logs.Error("failed to close eventbus producer: %v", err)
    }
}
```

## 消费者 (Consumer)

### 初始化方式

**1. 极简 API（推荐）**

```go
import eventbus "code.byted.org/eventbus/client-go"

// 启动一个阻塞的消费者
err := eventbus.Subscribe(eventName, group, eventbus.WithHandler(func(ctx context.Context, event *legacy.ConsumerEvent) error {
    // ... 业务逻辑 ...
    return nil // 返回 nil 代表成功，返回 error 将触发重试
}))
```

**2. 通用 SDK**

```go
import eventbus "code.byted.org/eventbus/client-go"

// 1. 创建配置
conf, err := eventbus.NewConsumerConfig(eventName, psm, group)
// ... handle error ...

// 2. 自定义配置 (e.g., 开启批量消费)
conf.Consumer.Batch.Size = 100
conf.Consumer.Batch.Interval = time.Second

// 3. 定义处理器
func myHandler(ctx context.Context, event *eventbus.ConsumerEvent) error {
    // ... 业务逻辑 ...
    return nil
}

// 4. 创建 Consumer 实例
consumer, err := eventbus.NewConsumer(conf, myHandler)
// ... handle error ...

// 5. 启动消费 (阻塞)
if err := consumer.Run(); err != nil {
    // ... handle error ...
}
```

### 关键配置

**控制台动态配置优先级高于代码配置**。

- `WorkerNum`: **消费并发数**。单个消费者实例内并发处理消息的 goroutine 数量。
- `WorkerBufferSize`: 每个 Worker 的**内部缓冲大小**。
- `SwndSize`: **滑动窗口大小**。SDK 内部从 Broker 拉取到本地的最大缓存消息数。配置过小会导致 Worker 饥饿，过大会增加重启时重复消费的概率。
- `RateLimit` & `RateLimitBurst`: **单实例限流**，控制消费速率。
- `Retry`: **是否开启重试**。消费失败（handler 返回 error）时是否进行重试。
- `LocalRetry`: **是否开启本地重试**。开启后，失败的消息会在当前消费者实例内部进行重试，而不是返回给 Broker 进行远端（异步）重试。这是**实现严格有序消费重试**的关键。
- `RetryStrategy`: **重试策略**，如 `normal` (固定间隔), `customized` (自定义间隔), `exponential` (指数退避)。
- `MaxRetry`: **最大重试次数**。
- `AutoAck`: **ACK 模式**。默认为 `true`，即 handler 执行完自动确认。设为 `false` 可开启**手动 Ack**。
- `Tags`: **过滤标签**。一个字符串数组，只消费带有这些 Tag 的消息。
- `Batch`: **批量消费**配置，包含 `Size` (最大批量) 和 `Interval` (最长等待时间)。

### 有序消费

有序消费的核心是**将需要保证顺序的一组消息，始终分发到同一个消费 Worker 处理**。

1. **生产者**：必须为这组消息设置**相同的 `Key`**。
2. **消费者**：配置客户端分发策略：
   - **按 Key 有序 (`NewEventKeyWorkerDispatcher`)**：将具有相同 `Key` 的消息分发到同一个 Worker。
   - **按分区有序 (`PartitionWorkerDispatcherBuilder`)**：将来自同一个分区的所有消息分发到同一个 Worker。

```go
// 代码配置示例
conf.Consumer.WorkerDispatcherBuilder = eventbus.NewEventKeyWorkerDispatcher
```

为了保证**严格有序**（即一条消息失败后，后续消息必须等待其重试成功），还需要开启**本地重试**：

```go
// 开启本地重试，通常与有序分发策略配合使用
conf, err := eventbus.NewConsumerConfig(eventName, psm, group, eventbus.WithLocalRetry())
```

**推荐在控制台配置"严格有序"模式**，平台会自动将分发策略设为按分区有序，并将重试类型设为本地重试。

### 优雅退出

- `consumer.Run()` 是一个**阻塞**方法，通常需要在一个独立的 goroutine 中运行。
- 为了实现优雅退出，可以调用 `eventbus.UnSubscribe(eventName, group)` 或 `consumer.Close()`。这会停止接收新消息，并等待正在处理的消息执行完成。

```go
// 示例：监听系统信号实现优雅退出
go func() {
    if err := consumer.Run(); err != nil {
        logs.Errorf("consumer run failed: %v", err)
    }
}()

quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

logs.Info("shutting down server...")
if err := eventbus.UnSubscribe(eventName, group); err != nil {
    logs.Errorf("failed to unsubscribe: %v", err)
}
logs.Info("consumer unsubscribed.")
```

## 上下文使用 (Context)

- `context.Context` 在生产和消费的整个链路中都至关重要，用于**传递超时、取消信号和链路追踪信息**。
- **生产端**：`Send`, `SendAsync`, `SendBatch` 等方法都需要传入 `ctx`。
- **消费端**：`handler` 函数的第一个参数就是 `ctx`。
- **传递 logid**：SDK 会自动处理 `logid` 的透传。

```go
import "code.byted.org/gopkg/ctxvalues"

// 生产端手动设置 logid
ctx = ctxvalues.SetLogID(ctx, "your-log-id")
producer.Send(ctx, event)

// 消费端获取 logid
func handler(ctx context.Context, event *eventbus.ConsumerEvent) error {
    logid := ctxvalues.GetLogID(ctx)
    // ...
    return nil
}
```

## 典型代码片段

### 生产者 - 极简 API

```go
package main

import (
    "context"
    "time"

    eventbus "code.byted.org/eventbus/client-go"
    "code.byted.org/eventbus/client-go/legacy"
    "code.byted.org/gopkg/logs"
)

const eventName = "your_event_name"

func main() {
    ctx := context.Background()

    // 1. 极简同步发送
    err := eventbus.Publish(ctx,
        eventbus.NewProducerEventBuilder().
            WithEventName(eventName).
            WithValue([]byte("hello world")).
            WithKeyString("user-123").
            Build(),
    )
    if err != nil {
        logs.Errorf("Publish failed: %v", err)
    }

    // 2. 极简批量发送
    batchResp, err := eventbus.PublishBatch(ctx,
        eventbus.NewProducerEventBuilder().WithEventName(eventName).WithValue([]byte("batch-1")).Build(),
        eventbus.NewProducerEventBuilder().WithEventName(eventName).WithValue([]byte("batch-2")).Build(),
    )
    if err != nil {
        logs.Errorf("PublishBatch failed: %v", err)
    }
    if batchResp != nil && len(batchResp.Failed) > 0 {
        logs.Warnf("%d messages failed in batch", len(batchResp.Failed))
    }

    // 3. 极简异步发送
    eventbus.PublishAsync(ctx,
        eventbus.NewProducerEventBuilder().
            WithEventName(eventName).
            WithValue([]byte("async hello")).
            Build(),
        func(ctx context.Context, event *legacy.ProducerEvent, err error) {
            if err != nil {
                logs.Errorf("Async send failed for event %s: %v", event.ID(), err)
            } else {
                logs.Infof("Async send succeeded for event %s", event.ID())
            }
        },
    )

    // 异步发送需要等待回调，这里仅为演示
    time.Sleep(2 * time.Second)
}
```

### 生产者 - 通用 SDK

```go
package main

import (
    "context"
    "os"
    "os/signal"
    "syscall"
    "time"

    eventbus "code.byted.org/eventbus/client-go"
    "code.byted.org/gopkg/logs"
)

var (
    producer  eventbus.Producer
    eventName = "your_event_name"
    psm       = "your.service.psm"
)

func setupProducer() {
    conf, err := eventbus.NewProducerConfig(eventName, psm)
    if err != nil {
        panic(err)
    }
    conf.Producer.SendTimeout = 3 * time.Second
    conf.Producer.Retry = 3
    conf.Producer.RetryInterval = 100 * time.Millisecond
    conf.Producer.AsyncBufferSize = 1024 // 如果使用异步发送，建议配置

    producer, err = eventbus.NewProducer(conf)
    if err != nil {
        panic(err)
    }
}

func main() {
    setupProducer()
    defer func() {
        logs.Info("Closing producer...")
        // 如果使用了 SendAsync，必须调用 Close
        if err := producer.Close(); err != nil {
            logs.Errorf("Failed to close producer: %v", err)
        }
    }()

    ctx := context.Background()

    // 1. 同步发送 + Builder
    event := eventbus.NewProducerEventBuilder().
        WithKeyString("order-456").
        WithValue([]byte(`{"amount": 100}`)).
        WithTag("vip_user").
        WithDelay(10 * time.Second).
        WithHeader("X-Request-Id", "logid-from-upstream").
        Build()
    if err := producer.Send(ctx, event); err != nil {
        logs.Errorf("Send failed: %v", err)
    }

    // 2. 异步发送
    asyncEvent := eventbus.NewProducerEventBuilder().
        WithValue([]byte("async data")).
        Build()
    producer.SendAsync(ctx, asyncEvent, func(ctx context.Context, pev *eventbus.ProducerEvent, err error) {
        if err != nil {
            logs.Warnf("Async send finally failed after retries: %v", err)
        }
    })

    // 阻塞主 goroutine 以等待程序退出信号
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
}
```

### 消费者 - 极简 API

```go
package main

import (
    "context"
    "errors"
    "os"
    "os/signal"
    "syscall"
    "time"

    eventbus "code.byted.org/eventbus/client-go"
    "code.byted.org/eventbus/client-go/legacy"
    "code.byted.org/gopkg/logs"
)

const (
    eventName = "your_event_name"
    group     = "your_consumer_group"
)

func main() {
    // 1. 极简单条消费
    go func() {
        logs.Info("Starting single handler consumer...")
        err := eventbus.Subscribe(eventName, group, eventbus.WithHandler(func(ctx context.Context, event *legacy.ConsumerEvent) error {
            logs.Infof("Received message: ID=%s, Key=%s, Value=%s", event.ID(), string(event.Key), string(event.Value))
            // 模拟消费失败
            if string(event.Key) == "fail" {
                return errors.New("this message should be retried")
            }
            return nil
        }))
        if err != nil {
            panic(err)
        }
    }()

    // 2. 极简批量消费
    go func() {
        logs.Info("Starting batch handler consumer...")
        err := eventbus.Subscribe(eventName, group+"-batch", eventbus.WithBatchHandler(func(events eventbus.Events) {
            logs.Infof("Received a batch of %d messages", len(events))
            for _, e := range events {
                logs.Infof("  - Processing message ID: %s", e.ID())
                // 标记单条消息消费失败，只有被标记的会重试
                if string(e.Key()) == "batch_fail" {
                    e.MarkError(errors.New("failed to process this specific message"))
                }
            }
        }))
        if err != nil {
            panic(err)
        }
    }()

    // 优雅退出
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    logs.Info("Shutting down...")

    // Unsubscribe all
    eventbus.UnSubscribe(eventName, group)
    eventbus.UnSubscribe(eventName, group+"-batch")

    time.Sleep(2 * time.Second) // 等待退出完成
    logs.Info("Server exited.")
}
```

### 消费者 - 有序消费与重试策略

```go
package main

import (
    "context"
    "errors"
    "os"
    "os/signal"
    "syscall"
    "time"

    eventbus "code.byted.org/eventbus/client-go"
    "code.byted.org/eventbus/client-go/legacy"
    "code.byted.org/gopkg/logs"
)

func main() {
    psm := "your.service.psm"
    eventName := "your_event_name"
    group := "your_consumer_group"

    // 1. 配置：严格有序 + 指数退避重试
    // 推荐在控制台配置 "严格有序"，这里仅为代码示例
    conf, err := eventbus.NewConsumerConfig(eventName, psm, group,
        // 使用指数退避重试策略，初始间隔1s，最大次数5
        eventbus.WithRetryStrategy(eventbus.RetryStrategyExponential, time.Second, 5),
        // 开启本地重试以保证重试时仍然有序
        eventbus.WithLocalRetry(),
    )
    if err != nil {
        panic(err)
    }
    // 配置按 Key 分发到 Worker，保证普通消息有序
    conf.Consumer.WorkerDispatcherBuilder = eventbus.NewEventKeyWorkerDispatcher
    // 配置 Tag 过滤
    conf.Consumer.Tags = []string{"tagA", "tagB"}

    // 2. 创建 Consumer
    consumer, err := eventbus.NewConsumer(conf, func(ctx context.Context, event *legacy.ConsumerEvent) error {
        logs.Infof("Orderly consumer received message: Key=%s, RetryTimes=%d", string(event.Key), event.GetRetryTimes())
        if event.GetRetryTimes() < 2 { // 模拟前两次消费失败
            return errors.New("deliberate failure for retry test")
        }
        logs.Infof("Message with Key=%s processed successfully.", string(event.Key))
        return nil
    })
    if err != nil {
        panic(err)
    }

    // 3. 启动并管理生命周期
    go func() {
        if err := consumer.Run(); err != nil {
            logs.Errorf("Consumer exited with error: %v", err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    logs.Info("Shutting down consumer...")
    if err := consumer.Close(); err != nil {
        logs.Errorf("Failed to close consumer: %v", err)
    }
    logs.Info("Consumer closed.")
}
```

## 常见坑与推荐写法

### 生产侧

#### 不要频繁创建 Producer

`Producer` 是一个重量级对象，包含连接池和后台 goroutine。应在服务启动时创建单例，并在整个生命周期中复用。极简 API `eventbus.Publish` 内部已实现缓存和复用机制。

#### 合理设置异步 Buffer

`AsyncBufferSize` 不是越大越好。过大会导致进程退出时大量消息需要 `Close` 等待，且占用较多内存。过小则可能导致 `SendAsync` 因 channel 满而阻塞或超时。需根据生产 QPS、消息大小和机器资源进行压测和调整。

#### Callback 逻辑需轻量

`SendAsync` 的回调函数应非常轻量，例如只记录日志或更新计数器。避免在 Callback 中执行 RPC、数据库查询等耗时操作，否则会阻塞内部的 goroutine pool，进而影响整个异步发送流程。

#### 理解 Key 与分区热点

使用 `Key` 是为了实现有序，但如果 `Key` 的基数很小，或某些 `Key` 的流量远高于其他，可能导致少数分区成为**热点**，造成消息积压。设计 `Key` 时应考虑其散列的均匀性。

#### 延迟消息的精度与排队

延迟消息并非精确触发，存在秒级误差。大量相同延迟时间的任务可能会在同一时刻到期，形成消费洪峰。如果业务对精度和执行时间有严格要求，应考虑使用专业的延迟任务调度系统。

#### 优先使用控制台动态配置

生产者的超时、重试等参数，优先在控制台进行调整。这无需修改代码和重新部署，响应更快，是处理线上问题的首选方式。

### 消费侧

#### Run 方法是阻塞的

`consumer.Run()` 会阻塞当前 goroutine，直到消费者被关闭。必须将它放在一个独立的 goroutine 中执行，否则会阻塞服务启动流程。

#### 动态配置调整需谨慎

频繁调整消费者的动态配置（如 `WorkerNum`, `SwndSize` 等）会频繁触发消费者 Rebalance，导致消费中断、消息重复，甚至可能加剧消息积压。调整应低频且谨慎。

#### 严格有序的代价

开启严格有序（按 Key/分区有序 + 本地重试）意味着单个 Worker 内的消息处理是**串行**的。如果某条消息处理耗时很长或持续重试失败，会阻塞该 Worker 上后续所有消息的处理。

#### 批量消费的错误标记

在批量消费的 handler (`WithBatchHandler`) 中，如果只有部分消息处理失败，应使用 `e.MarkError(err)` 来标记失败的单条消息，而不是让整个 handler 返回 error。只有被标记的消息会进入重试流程。

#### 理解 RateLimit 与 Burst

`RateLimit` 是平均速率，而 `RateLimitBurst` 允许在一段时间无消费后积累令牌，以应对短时间的流量突刺。

#### SwndSize 与重启行为

`SwndSize` 定义了 SDK 本地缓存的消息量。这个值越大，吞吐量可能越高，但如果消费者进程异常退出，这部分已拉到本地但未处理（或未 Ack）的消息，在消费者重启后会**全部重新消费**。

#### UnSubscribe 的优雅退出

调用 `UnSubscribe` 或 `Close` 后，SDK 会停止拉取新消息，但会等待已拉到本地且正在处理的消息完成。这是实现优雅停机的关键。

## 配置清单

### 典型参数列表

| 参数 (代码)                 | 范围/推荐                      | 场景     | 描述                                                           |
| --------------------------- | ------------------------------ | -------- | -------------------------------------------------------------- |
| **Producer**                |                                |          |                                                                |
| `SendTimeout`               | `1s` ~ `5s`                    | 生产     | 同步/批量发送的单次超时，包含内部重试。                        |
| `Retry`                     | `2` ~ `3`                      | 生产     | 失败重试次数。`SendTimeout` 内的重试。                         |
| `RetryInterval`             | `50ms` ~ `200ms`               | 生产     | 重试间隔。                                                     |
| `AsyncBufferSize`           | `1024` ~ `4096`                | 生产异步 | 异步发送本地缓存大小，根据 QPS 和消息大小调整。                |
| **Consumer**                |                                |          |                                                                |
| `WorkerNum`                 | `16` ~ `512` (不超过 512)      | 消费     | 消费并发 goroutine 数。有序消费时通常需配合调整。              |
| `RateLimit`                 | 根据业务处理能力设定           | 消费     | 单实例消费速率限制 (QPS)。                                     |
| `SwndSize`                  | `256` ~ `4096` (不超过 4096)   | 消费     | 客户端最大缓存消息数。影响吞吐和重启重复量。                   |
| `MaxRetry`                  | `3` ~ `16` (远端重试上限 16)   | 消费     | 最大重试次数。                                                 |
| `RetryInterval`             | `1s` ~ 数分钟 (根据重试策略)   | 消费     | 重试间隔。指数退避策略下为初始间隔。                           |
| `Batch.Size`                | `10` ~ `200`                   | 消费批量 | 批量消费最大消息数。                                           |
| `Batch.Interval`            | `100ms` ~ `2s`                 | 消费批量 | 批量消费最长等待时间。                                         |

### 命名与使用规范

- **Event 命名**：应具有业务含义，采用 `.` 分隔，如 `trade.order.paid`。
- **Group 命名**：消费组名，同样应有业务含义，如 `risk_control.order_auditor`。
- **Key 规范**：
  - 用于**保证顺序**时，使用业务上唯一的 ID，如订单 ID、用户 ID。
  - 设计时需考虑散列均匀性，避免热点。例如，不要用业务类型作 Key。
  - 内容建议为可见的字符串，便于排查问题。
- **Tag 规范**：
  - 用于**消息过滤**，定义业务的子类型或属性，如 `user_grade.A`, `action.create`。
  - Tag 逻辑是 "或"，即消费者订阅 `[tagA, tagB]`，会收到带 `tagA` 或 `tagB` 的消息。
- **延迟消息**：仅用于对时间不精确的场景。精确的定时任务请使用专业调度系统。
- **泳道消息**：生产端需在 Context 中传递 `K_ENV` Header，消费端部署在对应泳道环境即可自动订阅。

## 示例 Prompt

- "请帮我为一个 Golang 服务集成 EventBus。服务启动时需要初始化一个生产者，用于发送名为 `user.profile.updated` 的事件。同时，还需要启动一个消费者，订阅该事件，消费组为 `data_sync.service`。请提供完整的、包含优雅退出的代码框架。"
- "我需要实现一个严格有序的 EventBus 消费者，用于处理订单状态变更事件。事件名为 `trade.order.status.changed`，使用订单 ID (`order_id`) 作为 `Key` 来保证顺序。请为我展示如何配置消费者，使其能够按 `Key` 有序消费，并且在消费失败时进行本地重试，以防止后续消息被阻塞。"
- "我的服务需要消费 `log.raw.collected` 事件并批量写入数据库。请帮我编写一个 EventBus 批量消费者，配置为每批最多 100 条消息，或最长等待 1 秒。在 handler 中，需要展示如何遍历批量消息，并演示如何标记其中某几条消息处理失败，以便让它们能被单独重试。"
- "请为我演示如何配置一个 EventBus 消费者，使其在消费失败时采用**指数退避**的重试策略。初始重试间隔为 2 秒，最多重试 5 次。"
- "我的一个 EventBus 生产者发送的消息在下游没有被消费，我怀疑消息没发送成功。请提供一个使用**通用 SDK** 的生产者示例，包含完整的配置（超时、重试），并演示如何在 `Send` 方法返回错误时打印详细的错误日志。"

## 相关文档

- [EventBus SDK 生产者使用指南](https://bytedance.larkoffice.com/wiki/wikcn7d5ubBkkeXNSTIw0VWuosf)
- [EventBus SDK 消费者使用指南](https://bytedance.larkoffice.com/wiki/wikcnpTCN4iO6Vye74Zvw6I1Wyg)
