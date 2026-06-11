# BMQ SDK 使用指南 - inf/sarama & tmq/kafka-client

## 概述

**BMQ SDK** 是字节跳动内部使用的消息队列客户端，基于开源 Kafka 协议兼容，提供高性能、高可用的消息生产与消费能力。Go 语言版本主要包含两个代码库：`inf/sarama` 提供基础的生产者和低级消费者 API，`tmq/kafka-client` 依赖 sarama 提供高级消费者 API。

**特性**：
- 与 Kafka 协议完全兼容
- 支持双机房高可用
- 内置泳道功能支持
- 提供生产消费监控
- 支持消息压缩（Zstd）

**代码包**：
- `code.byted.org/inf/sarama` - 基础 SDK，提供 producer 和 low level consumer API
- `code.byted.org/tmq/kafka-client` - 高级消费者 SDK，依赖 sarama

## 适用场景

- **高吞吐业务**：适用于离线及近线业务的高吞吐量消息处理[^BMQ]
- **服务解耦**：微服务架构中的异步通信和解耦
- **数据流处理**：实时数据流处理和日志收集
- **事件驱动**：构建事件驱动架构，实现最终一致性

## 定位对比

- **BMQ vs Kafka**：BMQ 是字节自主研发的消息队列，与 Kafka 协议兼容，具备高可用、高性能、可扩展等优点[^BMQ]
- **sarama vs kafka-client**：sarama 提供基础 API，kafka-client 在 sarama 基础上封装了高级消费者功能
- **消息大小限制**：BMQ 集群服务端限制单条消息大小为 20MB（压缩前），最佳实践是控制在 <1MB

## 连接与初始化

### 配置项

**生产者关键配置**：
- `Producer.MaxMessageBytes`：客户端消息大小限制，默认 1000000 字节，必须小于服务端的 `message.max.bytes`（BMQ 集群为 20MB）
- `Producer.Timeout`：生产消息超时时间，默认 10 * time.Second
- `EnableMultiEnv`：是否开启泳道功能，默认 false

**消费者关键配置**：
- `EnableMultiEnv`：泳道环境消费泳道消息需设置为 true
- `PreferService`：消费模式，可选 dclocal 或 dcleader，默认 dclocal
- `Consumer.Return.Errors`：打印 error log，默认 true

### 版本要求

- `inf/sarama`：建议使用 1.4.11 及以上版本
- `tmq/kafka-client`：建议使用 1.0.7 及以上版本
- 对于 kafka_game_galinc2 集群，不要使用 v1.0.6 版本

## 典型代码片段

### 初始化 SDK

```go
package main

import (
    "code.byted.org/inf/sarama"
    kafka "code.byted.org/tmq/kafka-client/bsm/sarama-cluster"
)

// 下载 SDK
// go get code.byted.org/inf/sarama@latest

// NewProducerClient 创建生产者客户端
func NewProducerClient(brokers []string) (sarama.SyncProducer, error) {
    config := sarama.NewConfig()
    config.Producer.MaxMessageBytes = 1000000  // 1MB限制
    config.Producer.Timeout = 10 * time.Second
    config.EnableMultiEnv = false  // 默认不开启泳道
    
    return sarama.NewSyncProducer(brokers, config)
}

// NewConsumerClient 创建消费者客户端
func NewConsumerClient(cluster, topic, group string) (*kafka.Consumer, error) {
    config := kafka.NewConfig()
    config.EnableMultiEnv = true  // 开启泳道功能
    config.PreferService = "dclocal"
    
    return kafka.NewConsumerWithClusterName(cluster, topic, group, config)
}
```

### 生产者示例

```go
package producer

import (
    "context"
    "code.byted.org/inf/sarama"
)

type MessageProducer struct {
    producer sarama.SyncProducer
}

func NewMessageProducer(producer sarama.SyncProducer) *MessageProducer {
    return &MessageProducer{producer: producer}
}

// SendMessage 发送单条消息
func (mp *MessageProducer) SendMessage(ctx context.Context, topic, key, value string) error {
    msg := &sarama.ProducerMessage{
        Topic: topic,
        Key:   sarama.StringEncoder(key),
        Value: sarama.StringEncoder(value),
    }
    
    _, _, err := mp.producer.SendMessage(msg)
    return err
}

// SendMessageWithHeader 发送带header的消息
func (mp *MessageProducer) SendMessageWithHeader(ctx context.Context, topic, key, value string, headers []sarama.RecordHeader) error {
    msg := &sarama.ProducerMessage{
        Topic:   topic,
        Key:     sarama.StringEncoder(key),
        Value:   sarama.StringEncoder(value),
        Headers: headers,
    }
    
    _, _, err := mp.producer.SendMessage(msg)
    return err
}
```

### 消费者示例

```go
package consumer

import (
    "context"
    "code.byted.org/tmq/kafka-client/bsm/sarama-cluster"
)

type MessageConsumer struct {
    consumer *kafka.Consumer
}

func NewMessageConsumer(consumer *kafka.Consumer) *MessageConsumer {
    return &MessageConsumer{consumer: consumer}
}

// ConsumeMessages 消费消息
func (mc *MessageConsumer) ConsumeMessages(ctx context.Context, handler func(*sarama.ConsumerMessage) error) error {
    for {
        select {
        case msg, ok := <-mc.consumer.Messages():
            if !ok {
                return nil
            }
            if err := handler(msg); err != nil {
                // 处理错误，可以选择重试或记录日志
                continue
            }
            mc.consumer.MarkOffset(msg, "") // 提交offset
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}

// BatchConsume 批量消费
func (mc *MessageConsumer) BatchConsume(ctx context.Context, batchSize int, handler func([]*sarama.ConsumerMessage) error) error {
    var batch []*sarama.ConsumerMessage
    
    for {
        select {
        case msg, ok := <-mc.consumer.Messages():
            if !ok {
                if len(batch) > 0 {
                    return handler(batch)
                }
                return nil
            }
            
            batch = append(batch, msg)
            if len(batch) >= batchSize {
                if err := handler(batch); err != nil {
                    return err
                }
                // 批量提交offset
                for _, m := range batch {
                    mc.consumer.MarkOffset(m, "")
                }
                batch = nil
            }
        case <-ctx.Done():
            if len(batch) > 0 {
                return handler(batch)
            }
            return ctx.Err()
        }
    }
}
```

## 常见坑与推荐写法

### 消息大小限制

**问题**：生产单条消息太大时，会报错 "kafka server: Message was too large, server rejected it to avoid allocation error"

**解决方案**：
1. 控制单条消息大小在 1MB 以内（最佳实践）
2. 如果业务需要大消息，优先考虑将内容放到 HDFS/TOS，在 BMQ 中存放元信息和 link
3. 适当调大 `Producer.MaxMessageBytes` 参数，但必须小于服务端限制（BMQ 20MB）

```go
// 推荐配置
config.Producer.MaxMessageBytes = 1000000  // 1MB
```

### 批量生产限制

**问题**：BMQ 服务端限制一个 Request 不能超过 100MB，batch 生产时要注意总大小

**解决方案**：
```go
func (mp *MessageProducer) SafeBatchSend(messages []*sarama.ProducerMessage) error {
    var totalSize int64
    for _, msg := range messages {
        // 估算消息大小
        size := estimateMessageSize(msg)
        totalSize += size
        
        if totalSize > 95*1024*1024 { // 留5MB余量
            // 分批发送
            if err := mp.sendBatch(messages[:len(messages)-1]); err != nil {
                return err
            }
            messages = messages[len(messages)-1:]
            totalSize = size
        }
    }
    return mp.sendBatch(messages)
}
```

### 泳道功能配置

**问题**：泳道环境需要正确配置才能消费泳道消息

**解决方案**：
```go
// 生产者开启泳道
config.EnableMultiEnv = true
config.MultiEnv.Version = sarama.MULTI_ENV_V2  // 推荐使用泳道二期

// 消费者开启泳道
config.EnableMultiEnv = true  // 泳道环境消费泳道消息必须设置为true
```

### Offset 管理

**推荐配置**：
```go
config.Consumer.Offsets.AutoResetHandler = sarama.AutoResetToOldestOrNewestIfOutOfRange
config.Consumer.Offsets.InitialHandler = sarama.InitOffsetToZeroOrNewest
```

**要求**：`inf/sarama` 版本为 v1.4.5+、`tmq/kafka-client` 版本为 v1.0.13+

### Goroutine 泄漏

**问题**：sarama 在刷新 metadata 时可能会创建过多 goroutine

**解决方案**：
1. 使用 `inf/sarama v1.4.21+` 版本，该版本会优先选择已连接的 Proxy
2. 同一个 cluster 的 topic 共用一个 producer 减少 client 创建
3. 定期检查 goroutine 数量，特别是 `backgroundMetadataUpdater` 调用栈

## 性能优化建议

1. **消息压缩**：对于大消息，开启 Zstd 压缩减少网络传输
2. **批量操作**：合理使用 batch 生产提高吞吐量
3. **连接复用**：相同集群的 topic 共享 producer 实例
4. **监控告警**：配置消息堆积、消费延迟等监控指标

## 相关文档

- [BMQ 用户手册](https://bytedance.feishu.cn/wiki/4to274ze) - 官方使用文档
- [sarama DeepWiki](https://deepwiki.bytedance.net/inf/sarama/) - SDK 详细文档
- [kafka-client DeepWiki](https://deepwiki.bytedance.net/tmq/kafka-client/) - 高级消费者文档
- [使用限制文档](/4to274ze/32aih7s3) - BMQ 使用限制说明
- [泳道支持文档](/4to274ze/368r4p41) - 泳道功能使用指南

## 故障排查

### 常见错误及解决

1. **"Request was for a topic or partition that does not exist"**
   - 检查 topic 是否存在
   - 确认 SDK 版本符合要求

2. **消息大小超限错误**
   - 检查单条消息是否超过 20MB（BMQ）或 4MB（Kafka）
   - 检查 batch 总大小是否超过 100MB

3. **连接问题**
   - 检查网络连通性
   - 确认权限配置正确

### 监控与告警

- 使用离线看板监控 SDK 使用情况
- 配置消息堆积告警
- 监控生产消费延迟

