# Abase/Redis资源配置和使用

## 概述

Abase和Redis都是基于`code.byted.org/gopkg/redis-v6`封装的缓存资源，服务接入 GDP 即可使用。虽然两者使用了相同的协议，但使用形式、支持的命令、某些命令的结果都有差异，所以请在使用时务必分清。

## 主要特性

- **双缓存支持**：同时支持Abase和Redis两种缓存系统
- **协议兼容**：基于统一的Redis协议封装，提供一致的API接口
- **丰富命令支持**：支持String、Hash、List、Set、SortedSet等数据结构操作
- **高级功能**：支持Pipeline批量操作、Lua脚本执行、事务处理
- **连接池管理**：自动连接池管理，支持连接复用和负载均衡
- **集群支持**：支持Redis集群模式和Abase分布式架构
- **监控集成**：内置性能监控和慢查询日志功能

## 协议标识

Abase 与 Redis 的协议使用方式类似，但是协议标识不同：

| **Redis** | **Abase** |
| --- | --- |
| `redis` | `abase` |

## 资源配置

Abase/Redis 的配置需要注意以下细节：

### 扩展配置字段

`ExtensionCfg`支持配置的字段如下：

| **字段名** | **`ENV_tag`** | **字段含义** |
| --- | --- | --- |
| `IsDefault` | `不支持` | • 是否设置为默认集群 |
| `IdleTimeout` | `不支持` | • 单个连接的最大空闲时长，超过该时长后连接还没有被使用，连接会被关闭 |
| `PoolTimeout` | `不支持` | • 连接池已满且所有连接都已被占用下，业务代码获取连接的最大等待时长，超过返回错误 |
| `PoolInitSize` | `不支持` | • 客户端初始化时主动与 Proxy 建立的连接数 |

### 配置示例

```yaml
# Redis配置示例
redis_cluster:
  PSM: toutiao.redis.user_cache
  Protocol: redis
  ConnTimeout: 50ms
  ReadTimeout: 50ms
  WriteTimeout: 50ms
  ExtensionCfg:
    IsDefault: true
    IdleTimeout: 300s
    PoolTimeout: 5s
    PoolInitSize: 10

# Abase配置示例
abase_cluster:
  PSM: toutiao.abase.session_data
  Protocol: abase
  ConnTimeout: 50ms
  ReadTimeout: 50ms
  WriteTimeout: 50ms
  ExtensionCfg:
    IsDefault: false
    IdleTimeout: 300s
    PoolTimeout: 5s
    PoolInitSize: 5
```

## 使用客户端

Abase 与 Redis 客户端都支持`Cmd`、`Pipeline`，`Script`则只有 Redis 客户端支持。

### 基本命令使用

**Redis使用示例：**
```go
import (
    "context"

    "code.byted.org/gdp/ral/c/redis"
)

func RedisExample(ctx context.Context) {
    // 基本命令
    result := redis.GetClient().Get(ctx, "key")

    // 设置值
    err := redis.GetClient().Set(ctx, "key", "value", 0).Err()

    // 批量操作
    pipe := redis.GetClient().Pipeline()
    pipe.Set(ctx, "key1", "value1", 0)
    pipe.Get(ctx, "key1")
    _, err := pipe.Exec(ctx)
}
```

**Abase使用示例：**
```go
import (
    "context"

    "code.byted.org/gdp/ral/c/abase"
)

func AbaseExample(ctx context.Context) {
    // 基本命令
    result := abase.GetClient().Get(ctx, "key")

    // 设置值
    err := abase.GetClient().Set(ctx, "key", "value", 0).Err()
}
```

### Pipeline使用

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/redis"
)

func PipelineExample(ctx context.Context) {
    pipe := redis.GetClient().Pipeline()

    // 添加多个命令到pipeline
    pipe.Set(ctx, "key1", "value1", 0)
    pipe.Get(ctx, "key1")
    pipe.Set(ctx, "key2", "value2", 0)

    // 执行pipeline
    cmds, err := pipe.Exec(ctx)
    if err != nil {
        // 处理错误
    }

    // 获取结果
    for _, cmd := range cmds {
        // 处理每个命令的结果
    }
}
```

### Script使用（仅Redis支持）

只有 Redis 支持 Script，**Abase 并不支持**。

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/redis"
)

func Script(ctx context.Context) {
    s := redis.NewScript("script_name")

    _ = s.Eval(ctx, keys)
}
```

## 重要说明

**需要注意的是**，字节云 Redis 不支持或者禁用了某些原生 Redis 的命令，并且 Abase 和 Redis 对数据结构和命令的支持**有些许差异**，即使是相同的命令可能结果也并不对等。

## 请求日志

```
Notice invokehandler.go:92 10.78.204.49 p.s.m - default - 0 span=[0.1] req_start_time=[1716379646.909676] req_name=[tar_redis_cluster] psm=[toutiao.redis.tar_cluster] req_type=[redis] conn_timeout=[250ms] write_timeout=[250ms] read_timeout=[250ms] mesh_mode=[false] read_only=[false] remote_addr=[[fdbd:dc02:ff:1:1:174:227:161]:9644] send_size=[51] cmd=[SET] req_key=[redis_run_string_key1] key_num=[1] resp_len=[2] conn=[23.318ms] req=[35.632ms] total=[35.675ms] errno=[0] errmsg=[ok]
```

请求日志字段说明：

|   | **字段名** | **字段详情** |
| --- | --- | --- |
| `通用字段` | `abase_table`<br />`resp_len` | • 请求 Abase 表名<br />• 基于特定逻辑计算出的返回值，**只能作为返回值大小的参考** |
| `Cmd` | `read_only`<br />`cmd`<br />`req_key`<br />`key_num` | • 集群是否只读<br />• 执行的命令<br />• 执行命令 key，如有多个以`,`分隔<br />• 执行命令 key 数量 |
| `Pipeline` | `total_cmd`、`succ_cmd`、`fail_cmd` | • 通过 Pipeline 执行命令时，总命令数、成功数、失败数 |

## 相关文档

- [RAL概述](overview.md) - RAL组件总体介绍
- [RPC资源](rpc.md) - 远程过程调用配置和使用
- [Database资源](database.md) - 数据库资源配置和使用
- [Eventbus资源](eventbus.md) - 消息队列资源配置和使用
- [单元测试](testing.md) - RAL组件单元测试指南