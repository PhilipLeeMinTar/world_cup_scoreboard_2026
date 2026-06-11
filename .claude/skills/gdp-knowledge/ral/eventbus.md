# Eventbus资源配置和使用

## 概述

Eventbus基于`code.byted.org/eventbus/client-go`封装，使用方式与原生`Eventbus`客户端完全一致。RAL提供了统一的事件生产和消费接口，支持单条发送、批量发送等多种模式。

## 主要特性

- **原生兼容**：完全兼容原生Eventbus客户端API，零学习成本
- **多种发送模式**：支持单条发送、批量发送、异步发送等多种模式
- **自动重试**：内置失败重试机制，提高消息发送可靠性
- **性能优化**：支持批量处理和连接池管理，提升吞吐量
- **监控集成**：内置消息发送监控和性能指标收集
- **配置灵活**：支持Topic权限配置、超时设置等多种参数
- **容错处理**：提供完善的错误处理和异常捕获机制

## 资源配置

Eventbus 配置需要注意以下几点：

- `PSM`为对 topic 有权限的`PSM`，可以不配置（不配置默认为当前服务 PSM）
- `EventTopic`为必填字段
- 超时选项只支持设置`ReqTimeout`，其余设置无效

### 配置示例

```yaml
tar_cluster_event:
  PSM: tiktok.ugc.task_center
  Protocol: eventbus
  Retry: 1
  ReqTimeout: 500ms
  ExtensionCfg:
    IsDefault: true
    EventTopic: tiktok.creation.task_center.job_queue
```

### 扩展配置字段

`ExtensionCfg`支持的配置字段如下：

| **字段名** | **`ENV_tag`** | **字段含义** |
| --- | --- | --- |
| `IsDefault` | `不支持` | 是否设置为默认集群，如果指定集群为默认集群，可省略`WithCluster` |
| `EventTopic` | `不支持` | 访问的 topic 名字，必填项 |

## 使用客户端

使用的方式与接口与原生 eventbus 客户端完全一致。

### 基本使用

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/eventbus"
)

func Invoke(ctx context.Context) {
    event := eventbus.NewProducerEventBuilder() // create event
        .WithKey([]byte(key))
        .WithValue([]byte("value")).Build()

    // send event directly to default cluster
    {
        err := eventbus.Send(ctx, event)
    }

    // send event to another topic
    {
        err := eventbus.Send(ctx, event,
            eventbus.WithCluster("another_cluster_event"))
    }

    // send batch events
    {
        batch := []*eventbus.ProducerEvent{msg}
        err := eventbus.SendBatch(ctx, batch)
    }
}
```

### 高级使用

获取producer实例进行更灵活的操作：

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/eventbus"
)

func AdvancedUsage(ctx context.Context) {
    // get producer instance and send event
    pdr := eventbus.GetProducer(eventbus.WithCluster("tar_cluster_eventbus"))

    {
        err := pdr.Send(ctx, msg)
        if err != nil {
            // error handle
        }
    }

    {
        ret, err := pdr.SendBatch(ctx, msg)
    }
}
```

## 请求日志

```
Notice invokehandler.go:92 10.78.204.49 p.s.m - default - 0 span=[0.1] req_start_time=[1716445956.897047] req_name=[eventbus_gdp] psm=[ies.gdp.open_api] req_type=[eventbus] req_timeout=[3s] is_async=[false] event_num=[1] event_id=[80896131-f0cc-4b48-83e3-d29cac29acd5] event_key=[key] event_delay=[3s] event_tag=[filter_tag] req=[66.163ms] total=[66.164ms] errno=[0] errmsg=[ok]
```

请求日志字段说明：

|   | **字段名** | **字段详情** |
| --- | --- | --- |
| 事件信息 | `is_async`<br />`event_id`<br />`event_key`<br />`event_delay`<br />`event_tag` | • 消息是否异步<br />• 此次请求发送的消息数量<br />• 事件 ID，可根据 ID 查询事件发送详情<br />• 事件 key 信息<br />• 事件延迟发送时间<br />• 事件 tag 信息 |

## 相关文档

- [RAL概述](overview.md) - RAL组件总体介绍
- [RPC资源](rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](abase_redis.md) - 缓存资源配置和使用
- [Database资源](database.md) - 数据库资源配置和使用
- [单元测试](testing.md) - RAL组件单元测试指南