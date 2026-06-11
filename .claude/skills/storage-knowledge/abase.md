# Abase SDK 使用指南 - goredis

## 概述

**Abase** 是字节跳动内部的分布式 KV 存储服务，专为大规模、高吞吐量的键值数据存储场景设计。Abase 兼容 Redis 协议，因此与 Redis 共用同一个 Go SDK —— **goredis**。该 SDK 基于 `redis-v6` 封装，集成了服务发现、监控、熔断等内部特性。

**特性**：
- 兼容 Redis 协议，使用 goredis SDK
- 分布式、高可用架构
- 支持海量 KV 数据存储
- 高吞吐量读写
- 集成字节内部中间件生态

**代码包**：
- `code.byted.org/kv/goredis` (版本 >= 5.3.13)
- `code.byted.org/kv/redis-v6`

## 适用场景

- **大规模 KV 数据存储**：适合存储海量的键值对数据，如用户画像、配置信息等。
- **高吞吐量读写**：支持高并发的读写操作，适合实时性要求高的业务。
- **持久化存储**：相比 Redis 缓存，Abase 提供更可靠的数据持久化能力。

## 定位对比

- 与 **Redis** 相比，Abase 和 Redis 使用同一个 goredis SDK，但 Abase 更侧重于持久化的大规模 KV 存储，而 Redis 更适合作为高性能缓存。
- 与 **RDS (MySQL)** 相比，Abase 是 NoSQL 存储，不支持复杂的关系查询和事务，但在简单 KV 操作上性能更优。

## 连接与初始化

### 安装依赖

需要同时安装两个包：

```bash
go get code.byted.org/kv/goredis
go get code.byted.org/kv/redis-v6
```

### 初始化方式

Abase 有两种初始化方式，区别在于访问 Key 时是否需要拼接表名：

1. **`NewAbaseClientWithOption`（推荐）**：访问 Key 时**不需要**拼接表名，SDK 会自动处理。
2. **`NewClientWithOption`**：访问 Key 时**需要**手动拼接表名，格式为 `[table]key`。

### 配置项

通过 `goredis.NewOption()` 创建配置对象。**注意：Abase 的平均延迟高于 Redis，不能使用 Redis SDK 的默认超时值。**

- `DialTimeout`：建议 `250ms` 以上。
- `ReadTimeout`：建议 `250ms` 以上。
- `WriteTimeout`：建议 `250ms` 以上。
- `PoolTimeout`：建议 `250ms` 以上。
- `IdleTimeout`：**必须小于 30 分钟**（Abase Proxy 会关闭连续闲置 30 分钟的连接，建议设为 25m）。
- `PoolSize`：建议不超过 100，根据 QPS 和后端 Proxy 数量调整。
- `SetPoolInitSize`：连接池初始大小，默认 10。
- `autoLoadConf`: 必须为 `true`（默认值），否则会导致 Consul 列表不更新。

### 典型初始化代码

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "code.byted.org/kv/goredis"
    redis "code.byted.org/kv/redis-v6"
)

func NewAbaseClient(cluster, table string) (*goredis.Client, error) {
    options := goredis.NewOption()

    // 1. 连接池配置
    options.SetPoolInitSize(10)
    options.PoolSize = 100
    
    // 2. 超时配置 (Abase 建议值)
    options.DialTimeout = 250 * time.Millisecond
    options.ReadTimeout = 250 * time.Millisecond
    options.WriteTimeout = 250 * time.Millisecond
    options.PoolTimeout = 250 * time.Millisecond
    
    // 3. 空闲超时 (必须小于 30m)
    options.IdleTimeout = 25 * time.Minute

    // 4. 使用 NewAbaseClientWithOption 初始化 (推荐)
    // 这样后续操作 Key 时不需要手动拼接表名
    client, err := goredis.NewAbaseClientWithOption(cluster, table, options)
    if err != nil {
        return nil, fmt.Errorf("failed to create abase client: %w", err)
    }

    return client, nil
}

func main() {
    // 替换为实际的集群 PSM 和表名
    cluster := "bytedance.abase2.your_cluster.service.lf"
    table := "your_table_name"

    client, err := NewAbaseClient(cluster, table)
    if err != nil {
        log.Fatalf("init failed: %v", err)
    }

    // 验证连接
    if _, err := client.Ping().Result(); err != nil {
        log.Fatalf("ping failed: %v", err)
    }
    
    fmt.Println("Abase client initialized successfully")
}
```

## 常用命令与操作

下述示例假设使用了 `NewAbaseClientWithOption` 初始化，因此 Key 无需拼接表名。

### 读写操作 (Read/Write)

```go
// Set: 设置 Key (第三个参数为过期时间，0 表示不过期)
err := client.Set("key", "value", 0).Err()

// Get: 获取 Key
val, err := client.Get("key").Result()
if err == redis.Nil {
    // Key 不存在
} else if err != nil {
    // 其他错误
}

// MGet: 批量获取
vals, err := client.MGet("key1", "key2").Result()

// Del: 删除 Key (注意：Abase 只能删除 String 类型的 Key)
n, err := client.Del("key1").Result()

// Incr: 自增
newVal, err := client.Incr("counter").Result()
```

### CAS 操作 (XGet/XSet)

Abase 支持通过 `XGet` 和 `XSet` 实现 CAS (Compare-And-Swap) 乐观锁。

```go
// XGet: 获取值和版本号 (generation)
// return (value, generation) on success
// return (nullptr, -1) on not-found
val, gen, err := client.XGet("key").Result()

// XSet: 带版本号写入
// 第3个参数为 old generation，第4个参数为过期时间
// generation 为 -1 表示"仅当 key 不存在时 set"
// generation 为 0 表示"忽略版本号强制 set"
numOps, _, err := client.XSet("key", "newValue", gen, 0).Result()

if numOps == 1 {
    // CAS 成功
} else {
    // CAS 失败 (数据已被修改)
}
```

### 过期时间操作

- `TTL` / `PTTL`: 查看剩余时间
- `Expire` / `PExpire`: 设置过期时间
- `ExpireAt` / `PExpireAt`: 设置过期时间戳
- `Persist`: 移除过期时间

注意：`Del`, `TTL` 等命令仅对 String 类型生效。复杂数据结构需使用特定命令（如 `Hashexists`, `Httl`）。

## 常见坑与注意事项

1.  **Lua 脚本**: Abase **不支持** Lua 脚本。
2.  **Del 命令**: Abase 的 `Del` 命令只能删除 String 类型的 Key，无法删除 Hash/List/Set/ZSet 等结构。
3.  **Pipeline 限制**:
    *   建议一次打包 20-30 个命令，不宜过多 (>200)。
    *   Batch 写命令（如 MSet）不能包含重复的 Key。
4.  **Context 并发安全**:
    *   `client.WithContext(ctx)` 返回的新 Client 对象**不是并发安全的**。
    *   在并发场景（如多个 Goroutine）中，必须为每个 Goroutine 单独调用 `WithContext`。
5.  **IdleTimeout**: 必须小于 30 分钟，否则会因 Proxy 端关闭连接而导致客户端 `Broken Pipe`。
6.  **重试机制**: `MaxRetries` 默认为 0，不建议开启 SDK 层面的自动重试，以免在集群故障时造成流量风暴。

## 相关文档

- [Abase SDK 官方文档](https://cloud.bytedance.net/docs/abase/docs/63d768447df7d2021dfbf062/63d8de53215b040230c410b9)
- [Goredis SDK 文档](https://code.byted.org/kv/goredis)
- [Abase 数据结构及支持命令](https://cloud.bytedance.net/docs/abase/docs/63d768447df7d2021dfbf062/63d8bec0bd6ec602247bb6d4)
