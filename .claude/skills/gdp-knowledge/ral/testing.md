# RAL单元测试指南

## 概述

RAL 基于 GDP 已有的单测能力，提供了一套能实现完整模拟资源访问请求的能力，为了方便研发能更好的构造单测数据，RAL 提供了一套链式方法创建对应的模拟数据。

同时配合`gdp/mocks`提供的`Run`方法，能更简单的完成单测的开发，详细介绍可参考：[GDP 单测开发指南](https://bytedance.larkoffice.com/wiki/KwQdwYXSWiNQo5ksTXtczYianjh)

## 主要特性

- **完整Mock能力**：支持RPC、Abase/Redis、Database、Eventbus等所有资源类型的Mock
- **链式API**：提供简洁的链式方法创建模拟数据，代码更易读
- **自动资源管理**：测试完成后自动释放Mock资源，避免资源泄漏
- **集成测试框架**：与`gdp/mocks`深度集成，支持`Run`方法简化测试开发
- **真实数据模拟**：支持构造接近真实场景的测试数据
- **零依赖测试**：不依赖真实外部服务，测试执行更快更稳定

## RPC测试

GDP 已在`rpcmodels`与`overpass`客户端中生成了对应 RPC 请求的方法，直接使用对应客户端的`Mock`方法即可。

### 基本示例

```go
import (
    "context"
    "testing"

    "code.byted.org/gdp/mocks"
    tiktok_ugc_center "code.byted.org/tiktok/rpcmodels/tiktok_ugc_center/cli"
    dto "code.byted.org/tiktok/rpcmodels/tiktok_ugc_center/dto"
    "github.com/stretchr/testify/assert"
)

func TestRPCCall(t *testing.T) {
    as := assert.New(t)

    req := &dto.PostRequest{}

    mocks.Run("post rpc call with biz error", t, func(ctx context.Context) {
        tiktok_ugc_center.Mock().Post().WithResponse(&dto.PostResponse{
            ItemID: "mock_item_id",
        }).WithBizCallError(123, "mock error").Build()

        resp, err := tiktok_ugc_center.Post(ctx, req)
        as.Equal("mock_item_id", resp.ItemID)
        as.Equal(int32(123), resp.BaseResp.StatusCode) // 框架会自动赋值BaseResp
        as.Equal("mock error", resp.BaseResp.StatusMessage)
        as.Nil(err)
    })

    t.Run("mock and unpatch with self", func(t *testing.T) {
        // 非mocks.Run下，需要自行释放
        defer tiktok_ugc_center.Mock().Post().WithRPCCallError().Build().Unpatch()

        resp, err := tiktok_ugc_center.Post(ctx, req)
        as.Nil(resp)
        as.NotNil(err)
    })
}
```

### Mock方法说明

想要了解更多的使用方式，请参考[此链接](https://code.byted.org/gdp/ral/blob/master/c/rpc/rpc_test.go#L177)，以下是 Mock 支持的链式方法：

| **方法名** | **说明** |
| --- | --- |
| `WithResponse` | • 设置 RPC 请求结果`Response` |
| `WithBizCallError` | • 设置业务请求错误结果<br />• 会自动赋值结果`BaseResp`的`StatusCode`与`StatusMessage`字段，无需再手动赋值 |
| `WithRPCCallError` | • 设置并模拟 RPC 请求失败场景，并同时将请求结果赋值为`nil` |

## Abase/Redis测试

`redis`与`abase`的使用方式类似：

### 基本示例

```go
import (
    "context"
    "testing"

    "code.byted.org/gdp/mocks"
    "code.byted.org/gdp/ral/c/redis"
    "github.com/stretchr/testify/assert"
)

func TestRedisCall(t *testing.T) {
    as := assert.New(t)

    mocks.Run("redis get key success", t, func(ctx context.Context) {
        redis.Mock().Get().WithKey("redis_key").WithResponse("redis ok").Build()

        res := redis.GetClient().Get(ctx, "redis_key")
        as.Equal("redis ok", res.Val())
        as.Nil(res.Err())
    })

    t.Run("mock any methods", func(t *testing.T)) {
        defer redis.Mock().MockMethod("Scan").WithResponse(...).Build().Unpatch()

        res := redis.GetClient().Scan(ctx, ...)
    }
}
```

### Mock方法说明

想要了解更多的使用方式，请参考[ redis](https://code.byted.org/gdp/ral/blob/master/c/redis/redis_test.go#L151)/[abase](https://code.byted.org/gdp/ral/blob/master/c/abase/abase_test.go#L138)，以下是 Mock 支持的链式方法：

| **方法名** | **说明** |
| --- | --- |
| `WithCluster` | • 设置 mock 指定的集群 |
| `WithKey` | • 设置 key 规则，只有完整匹配的 key 生效 |
| `WithKeyPrefix` | • 设置 key 前缀匹配规则，匹配成的 key 前缀生效 |
| `WithKeyPattern` | • 设置 key 正则匹配规则，匹配成的 key 前缀生效 |
| `WithResponse` | • 模拟对应返回的结果，需要注意数据的类型需要和返回的命令匹配，否则会出现 panic |
| `WithAbaseNil`<br />`WithRedisNil` | • 模拟 Redis/Abase 返回结果为`Nil` |
| `WithCallError` | • 模拟 Redis/Abase 请求失败错误 |

## Database测试

```go
import (
    "context"
    "testing"

    "code.byted.org/gdp/mocks"
    "code.byted.org/gdp/ral/c/db"
    "github.com/stretchr/testify/assert"
)

func TestDB(t *testing.T) {
    as := assert.New(t)

    mocks.Run("db success", t, func(ctx context.Context) {
        db.Mock().WithMockData(&Data{ID: uint64(123)}).Build()

        d := &Data{}
        err := db.Conn(ctx).Where("id=?", 123).First(d).Error
        as.Equal(uint64(123), d.ID)
        as.Nil(err)
    })
}
```

### Mock方法说明

想要了解更多的使用方式，请参考[此链接](https://code.byted.org/gdp/ral/blob/master/c/db/db_test.go#L177)，以下是 Mock 支持的链式方法：

| **方法名** | **说明** |
| --- | --- |
| `WithCluster` | • 设置 mock 指定的集群 |
| `WithModel` | • 设置需要创建的表对应的 model（只创建表） |
| `WithMockData` | • 设置需要创建的表对应的 model 和数据（会同时创建表和数据） |

## Eventbus测试

```go
import (
    "context"
    "testing"

    "code.byted.org/gdp/mocks"
    "code.byted.org/gdp/ral/c/eventbus"
    "github.com/stretchr/testify/assert"
)

func TestEventbus(t *testing.T) {
    as := assert.New(t)

    mocks.Run("eventbus failed", t, func(ctx context.Context) {
        eventbus.Mock().WithSendFailed(errors.New("failed")).Build()

        err := eventbus.Send(ctx, event)
        as.Equal(errors.New("failed"), err)
    })
}
```

### Mock方法说明

想要了解更多的使用方式，请参考[此链接](https://code.byted.org/gdp/ral/blob/master/c/eventbus/eventbus_test.go#L112)，以下是 Mock 支持的链式方法：

| **方法名** | **说明** |
| --- | --- |
| `WithCluster` | • 设置 mock 指定的集群 |
| `WithProducer` | • 设置 eventbus 的所有请求使用指定 producer |
| `WithSendSuccess` | • 设置 eventbus 的`Send`、`SendBatch`请求为成功 |
| `WithSendFailed` | • 设置 eventbus 的`Send`、`SendBatch`请求为失败 |

## Mock日志标识

在单测场景下，RAL的日志也会正常输出记录，如果命中mock数据，会在日志中显著的通过`resp_mocked`字段标注并记录下来，如下所示：

```
Notice 2024-07-12 10:44:07,655 v1(7) invokehandler.go:99 10.78.202.16 p.s.m - default - 0 span=[0.9] req_start_time=[1720752247.6650171] req_name=[redis_gdp] psm=[toutiao.redis.gdp] req_type=[redis] conn_timeout=[250ms] write_timeout=[250ms] read_timeout=[250ms] cmd=[GET] req_key=[redis_run_string_key1] key_num=[1] resp_mocked=[true] key_pattern=[^redis_run_string_key1$] conn=[0.000ms] req=[0.000ms] total=[0.007ms] errno=[0] errmsg=[ok]
```

## 相关文档

- [RAL概述](overview.md) - RAL组件总体介绍
- [RPC资源](rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](abase_redis.md) - 缓存资源配置和使用
- [Database资源](database.md) - 数据库资源配置和使用
- [Eventbus资源](eventbus.md) - 消息队列资源配置和使用