# RocketMQ SDK 使用指南 - rocketmq-go-proxy

## 概述

**rocketmq-go-proxy** 是字节跳动内部使用的 RocketMQ Go SDK，为 Go 项目提供高性能、高可靠的消息队列服务接入能力。该 SDK 集成了服务发现、监控、熔断等内部特性，支持同步/异步消息发送、顺序消费、广播消费等多种消息模式。

**特性**：
- 支持同步和异步消息发送
- 支持顺序消费和广播消费
- 内置消息重试和熔断机制
- 支持消息体 CRC 校验
- 集成服务发现和监控打点

**代码包**：
- `code.byted.org/rocketmq/rocketmq-go-proxy`

## 适用场景

- **高可用/低延迟的线上业务场景**：适用于对消息延迟和可用性要求较高的业务
- **交易/支付系统**：对消息可靠性以及消息事务要求较高的业务场景
- **异步任务处理**：需要异步消息处理的业务场景
- **削峰填谷**：处理流量峰值，平滑系统负载

## 定位对比

- **与 EventBus 对比**：RocketMQ 更侧重于高可用、低延迟的线上业务场景，而 EventBus 更侧重于最终一致性事件传递和有序事件流处理
- **与 Kafka 对比**：RocketMQ 在事务消息、顺序消息、延迟消息等方面有更好的支持

## 连接与初始化

### 前提条件
在使用本 SDK 之前，需要确保你已经完成以下步骤：
- 已创建相应 topic 并拥有生产和消费权限
- SDK 已开启生产和消费鉴权，需要先申请权限

### 下载 SDK
在你的项目中使用 `go get` 命令获取 SDK：
```go
go get code.byted.org/rocketmq/rocketmq-go-proxy@latest
```

### 配置项

#### 生产者配置参数详解：
- **ProduceTimeout**：生产消息的超时时间，单位是 ms，可根据业务需要调整超时时间
- **MaxTries**：生产消息时失败的重试次数，默认重试 3 次，可以根据业务需求调整
- **IsSmallInf**：是否是云上 sinf 业务访问，如果是 sinf 需要设置为 true
- **MaxMessageSize**：消息的大小上限，单位是字节（bytes），默认值是 128*1024*1024，即 128MB
- **EnableBodyCRC**：是否启用消息体 CRC 校验
- **EnableUserMiddleWares**：是否启用用户中间件

#### 消费者配置参数详解：
- **FanoutMode**：表示是通用的消息消费，还是广播消息消费，CLUSTERING 表示通用的，BROADCAST 表示广播消息消费
- **ConsumerMode**：消费类型，可选类型为 HIGH_LEVEL 或 LOW_LEVEL，推荐使用 HIGH_LEVEL

## 典型代码片段

### 生产者初始化

```go
package main

import (
    "context"
    "fmt"
    "log"
    "strconv"
    "time"

    "code.byted.org/rocketmq/rocketmq-go-proxy/pkg/config"
    "code.byted.org/rocketmq/rocketmq-go-proxy/pkg/producer"
    "code.byted.org/rocketmq/rocketmq-go-proxy/pkg/types"
)

var p producer.Producer

func InitProducer() {
    psm := "p.s.m"
    clusterName := "rmq_dev_test"
    cfg := config.NewProducerConfig(psm, clusterName)
    cfg.ProduceTimeout = 1000 * time.Millisecond
    producer, err := producer.NewProducer(cfg)
    if err != nil {
        log.Fatal(err)
    }

    p = producer
}

func SendNormalMessage(topic string) {
    ctx := context.Background()
    for i := 0; i < 10; i++ {
        msg := types.NewMessage(topic, []byte("normal message "+strconv.Itoa(i)))
        msg.WithTag("tagA")
        resp, err := p.Send(msg)
        if err != nil {
            log.Printf("Send message failed: %v", err)
            continue
        }
        fmt.Printf("Send message success, msgid: %s\n", resp.MsgID)
    }
}
```

### 高吞吐量配置示例

```go
func highThroughputConfig() *config.ProducerConfig {
    cfg := config.NewProducerConfig("high-throughput-producer", "production-cluster")
    
    // 消息大小和压缩
    cfg.MaxMessageSize = 64 * 1024 * 1024  // 64MB，需参考集群的设置
    cfg.Compression = types.CompressionZSTD  // 平衡压缩率和速度
    
    // 异步生产者通道配置 - 增大缓冲区
    cfg.ProducerChannelSize = 2048
    cfg.TopicChannelSize = 2048
    cfg.BrokerChannelSize = 2048
    cfg.CallbackChannelSize = 2048
    cfg.RetryChannelSize = 2048
    cfg.BrokerThreadNum = 16  // 增加线程数
    
    // 批量刷新配置
    cfg.FlushFrequency = 100 * time.Millisecond  // 更频繁的刷新
    cfg.FlushMessages = 100  // 更大的批次
    cfg.FlushBytes = 1024 * 1024  // 1MB批次大小
    
    return cfg
}
```

### 高可靠性配置示例

```go
func highReliabilityConfig() *config.ProducerConfig {
    cfg := config.NewProducerConfig("reliable-producer", "production-cluster")
    
    // 等待存储确认
    cfg.WaitStore = true  // 等待broker确认存储
    
    // 增加重试次数
    cfg.MaxTries = 5
    cfg.ProduceTimeout = 2 * time.Second
    
    // 启用熔断保护
    cfg.EnableCircuitBreaker = true
    cfg.CircuitBreakerOptions = circuitbreaker.Options{
        CoolingTimeout:    10 * time.Second,  // 熔断冷却时间
        DetectTimeout:     5 * time.Second,   // 检测超时
        ShouldTrip:        circuitbreaker.RateTripFunc(0.8, 10), // 80%失败率触发熔断
        HalfOpenSuccesses: 5,  // 半开状态需要5次成功
    }
    
    // 启用消息体CRC校验
    cfg.EnableBodyCRC = true
    
    return cfg
}
```

### 消费者初始化与消费

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "code.byted.org/rocketmq/rocketmq-go-proxy/pkg/config"
    "code.byted.org/rocketmq/rocketmq-go-proxy/pkg/consumer"
)

func InitConsumer() {
    psm := "consumer.psm"
    clusterName := "rmq_dev_test"
    topic := "test_topic"
    consumerGroup := "test_consumer_group"
    
    cfg := config.NewConsumerConfig(psm, clusterName, topic, consumerGroup)
    cfg.SubExpr = "tagA||tagB" // 订阅携带 tagA 或 tagB 消息
    // cfg.SubExpr = "tagC" // 订阅携带 tagC 消息
    
    // 配置消费模式
    cfg.FanoutMode = config.CLUSTERING  // 集群消费模式
    cfg.ConsumerMode = config.HIGH_LEVEL  // 高级消费模式
    
    r, err := consumer.NewConsumer(cfg)
    if err != nil {
        log.Fatal(err)
    }
    
    // 注册消息处理函数
    r.RegisterMessageListener(func(ctx context.Context, msgs []*types.MessageExt) error {
        for _, msg := range msgs {
            fmt.Printf("Received message: %s, tag: %s\n", 
                string(msg.Body), msg.GetTag())
        }
        return nil
    })
    
    // 启动消费者
    r.Start()
}
```

### Tag和多Tag使用

```go
// 生产带Tag的消息
msg := types.NewMessage(topic, []byte("normal message "+strconv.Itoa(i)))
msg.WithTag("tagA")
resp, err := p.Send(msg)

// 消费时订阅多个Tag
cfg.SubExpr = "tagA||tagB" // 订阅携带 tagA 或 tagB 消息

// 对于多Tag消息，需要在消费配置中设置 useSQLExpr=True
// 如果不加这个参数，消费的时候这条消息的 tag 就会是主 tag
```

## 常见坑与推荐写法

### 1. Tag消费问题
**问题**：生产的消息带了多个tag，消费者监听了其中一个tag，但是没有消费到消息

**解决方案**：对于多Tag消息，需要在消费配置中设置 `useSQLExpr=True`。如果不加这个参数，消费的时候这条消息的 tag 就会是主 tag（多个tag中的第一个）

### 2. 消息堆积监控
**注意**：计算每个queue堆积的公式是：broker上最大的offset - 消费组消费到的offset。如果消费组都没有消费实例连接，压根就没有消费消息，提交offset，自然不会有堆积，堆积是有消费后才有可能出现的

### 3. 日志配置
**建议**：SDK V1.4.16 版本后，Rocketmq Go SDK 支持配置 LogConfig 和自定义 logger 传入。通过调用 `InitRocketMQLog` 可以将 SDK 的日志打印到单独日志文件

**注意**：如果不初始化 RocketMQLog，日志会使用默认的 logs 输出。如果你的业务也使用了 logs 库，RocketMQLog 也会输出到业务日志中

### 4. 动态配置
**功能**：支持通过动态配置暂停consumer，需要go sdk v1.4.24及以上版本支持
- 配置项：`consumer.disable.podname`，按podname暂停consumer，多个用','分隔
- 想要取消的话，需要再修改这个参数的配置，去掉之前配置的podname的值，保持为空就行

### 5. 消费限速
**配置**：支持单consumer的消费qps限速
- 配置项：`consumer.rate.limit.enable` 和 `consumer.rate.limit.qps`
- 两个参数需要一起配置，如果只配置其中一个会导致go sdk panic
- 请使用v1.6.12及以上版本，这些版本已修复此bug

## 性能优化建议

### 消费性能优化
当遇到以下场景时，可以考虑优化消费者性能：
- 无序消费出现消费超时问题
- 顺序/无序消费堆积问题，且消费者实例的CPU和内存资源使用率较低

### 消息大小限制
**最佳实践**：消息大小最佳实践是<1MB。RMQ对于消息大小的限制参考使用限制中的单条消息大小限制，不要超过此上限

## 监控与排查

### 生产者监控
生产者相关的监控打点依赖客户端主动上报，如果客户端打点上报有问题则无法作为参考依据。只有鉴权成功，即正常使用的生产者才会在监控上看到以下打点：
```
rocketmq.client.producer.success.throughput
cluster字段为必填字段，_psm字段为生产者服务的PSM
```

![生产者监控](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/985fd3e753604f6f8c34684a5d811c1f~tplv-goo7wpa0wc-image.image)

### 消费者监控
消费者相关的监控打点同样依赖客户端主动上报：
```
rocketmq.client.consumer.success.throughput
cluster字段为必填字段，_psm字段为消费者服务的PSM
```

![消费者监控](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/054916e3d7f3459dac69fd669ae87394~tplv-goo7wpa0wc-image.image)

## 相关文档

- [RocketMQ Go SDK 接入指南](https://deepwiki.bytedance.net/rocketmq/rocketmq-go-proxy/)
- [RocketMQ 用户手册](https://rocketmq.arcosite.bytedance.net/)
- [代码仓库](https://code.byted.org/rocketmq/rocketmq-go-proxy)
- [同步发送示例](https://code.byted.org/rocketmq/rocketmq-go-proxy/blob/master/example/producer_demo.go)
- [异步发送示例](https://code.byted.org/rocketmq/rocketmq-go-proxy/blob/master/example/async_producer.go)

## 版本注意事项

- 如果升级 `google.golang.org/grpc >= 1.42.0` 出现错误 `"rocketmq_producer_proxy_consul://producer/test_common, result in : context deadline exceeded"`，请升级到 v1.4.10 以上版本
- 如果项目中使用了 google 的 protobuf-java 包，请使用 3.10.0 及以后版本。如果 protobuf-java 包小于 3.10.0 版，可能出现连接失败、连接上不消费等问题
