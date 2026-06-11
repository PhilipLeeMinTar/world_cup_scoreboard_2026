# Redis SDK 使用指南 - goredis

## 概述

**goredis** 是字节跳动内部广泛使用的 Go Redis 客户端，它在官方 `go-redis` 库的基础上进行了封装，集成了服务发现 (Consul)、监控、熔断、安全认证等内部特性，为业务提供了开箱即用的高性能缓存访问能力。

**特性**：
- 基于官方 go-redis 封装
- 集成 Consul 服务发现
- 内置监控、熔断机制
- 自动安全认证
- 连接池管理

**代码包**：
- `code.byted.org/kv/goredis`

## 适用场景

- **数据缓存**: 作为 MySQL 等关系型数据库的前置缓存，降低数据库压力，提升访问速度。
- **分布式锁**: 利用 Redis 的原子操作（如 `SETNX`）实现分布式锁。
- **计数器/排行榜**: 使用 `INCR`、`ZADD` 等命令实现实时计数器和排行榜功能。
- **会话存储**: 存储用户登录会话信息。
- **消息队列/发布订阅**: 利用 `LPUSH`/`BRPOP` 或 `PUBLISH`/`SUBSCRIBE` 实现简单的消息传递。

## 定位对比

- 与 **RDS (MySQL)** 相比，Redis 是基于内存的键值存储，性能极高但默认不保证数据持久性（可通过 RDB/AOF 配置），适合存储临时性、非核心或可再生数据。
- 与 **ABase/Bytedoc** 相比，Redis 数据结构更简单（KV、Hash、Set 等），操作原子，通常用于缓存或简单数据结构存储。ABase 和 Bytedoc 则提供更复杂的表或文档模型，支持二级索引和更复杂的查询。

## 连接与初始化

`goredis` 的初始化通常在服务启动时完成，并保持一个全局单例的客户端实例。

### 配置项

通过 `goredis.NewOption()` 创建配置对象，链式调用设置各项参数。

### 服务发现

内部 `goredis` 默认通过 PSM (服务标识) 从 Consul 动态发现 Redis 服务地址，业务代码通常无需关心具体 IP 和端口。

### 连接池

`goredis` 内部为每个 Redis 节点维护一个连接池：
- `PoolSize`: 每个节点的连接池大小，建议根据 QPS 设置，例如 `100`-`200`。
- `IdleTimeout`: 连接最大空闲时间，例如 `10s`。超过此时间的空闲连接会被回收。
- `LiveTimeout`: 连接最大存活时间，例如 `30s`。

### 超时与重试

- `DialTimeout`: 建立连接的超时时间，例如 `100ms`。
- `ReadTimeout`: 读超时，例如 `50ms`。
- `WriteTimeout`: 写超时，例如 `50ms`。
- **重试**: `goredis` 默认不进行重试 (`MaxRetries: 0`)。对于偶发的网络错误，客户端在执行命令时会进行内部重试。业务层通常无需额外处理。

### 熔断

`goredis` 内置了熔断机制。当某个 Redis 节点连接失败率超过阈值时，客户端会自动将其熔断，在一段时间内不再向其发送请求，避免雪崩。

## 生命周期管理

- **启动**: 在服务启动时，调用 `goredis.NewClientWithOption(psm, options)` 创建全局唯一的 `*goredis.Client` 实例，并注入依赖。
- **健康检查**: `goredis` 客户端内部管理节点的健康状态，通常无需业务主动进行 `PING` 检查。监控 `goredis` 的成功率、延迟等指标即可。
- **关闭**: `goredis` 客户端无需显式关闭。连接的生命周期由内部连接池管理。

## 依赖注入

与 BytedGORM 类似，推荐使用 Wire 或 Fx 等依赖注入框架管理 `*goredis.Client` 的单例生命周期。

## 典型代码片段

### 初始化

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "code.byted.org/kv/goredis"
)

// NewRedisClient 创建并返回一个 goredis Client 实例
func NewRedisClient(psm string) (*goredis.Client, error) {
    options := goredis.NewOption()

    // ---- 核心配置 ----
    // PSM 用于服务发现
    // options.SetServiceDiscoveryWithConsul() // 默认已开启

    // 超时配置
    options.DialTimeout = 100 * time.Millisecond
    options.ReadTimeout = 200 * time.Millisecond
    options.WriteTimeout = 200 * time.Millisecond

    // 连接池配置
    options.PoolSize = 100               // 每个节点的连接池大小
    options.IdleTimeout = 10 * time.Second // 空闲连接超时
    options.LiveTimeout = 30 * time.Second // 连接最大存活时间

    // 熔断器配置 (通常使用默认值)
    // options.MaxFailureRate = 0.2
    // options.MinSample = 10
    // options.WindowTime = 10 * time.Second

    client, err := goredis.NewClientWithOption(psm, options)
    if err != nil {
        return nil, fmt.Errorf("failed to create goredis client: %w", err)
    }

    // 通常不需要 Ping，NewClientWithOption 已包含连接可用性检查
    return client, nil
}

func main() {
    // Redis 服务的 PSM
    redisPSM := "toutiao.redis.your_service_name"

    redisClient, err := NewRedisClient(redisPSM)
    if err != nil {
        log.Fatalf("redis client initialization failed: %v", err)
    }

    fmt.Println("Redis client initialized successfully.")

    // 在这里执行业务逻辑...
    // 示例：执行一个 PING 命令
    ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
    defer cancel()

    status, err := redisClient.Ping(ctx).Result()
    if err != nil {
        log.Fatalf("ping redis failed: %v", err)
    }
    fmt.Printf("Ping response: %s\n", status)
}
```

### 基本 CRUD (KV, Hash, Set)

```go
package cache

import (
    "context"
    "time"
    "code.byted.org/kv/goredis"
)

type UserCache struct {
    client *goredis.Client
    prefix string
}

func NewUserCache(client *goredis.Client) *UserCache {
    return &UserCache{
        client: client,
        prefix: "user:",
    }
}

// SetUserCache 缓存用户信息 (使用 String)
func (c *UserCache) SetUserCache(ctx context.Context, userID string, userData string, expiration time.Duration) error {
    key := c.prefix + userID
    return c.client.Set(ctx, key, userData, expiration).Err()
}

// GetUserCache 获取用户信息 (使用 String)
func (c *UserCache) GetUserCache(ctx context.Context, userID string) (string, error) {
    key := c.prefix + userID
    val, err := c.client.Get(ctx, key).Result()
    if err == goredis.Nil {
        // 缓存未命中
        return "", nil
    }
    return val, err
}

// HSetUserProfile 缓存用户配置 (使用 Hash)
func (c *UserCache) HSetUserProfile(ctx context.Context, userID string, field string, value string) error {
    key := c.prefix + "profile:" + userID
    return c.client.HSet(ctx, key, field, value).Err()
}

// HGetUserProfile 获取用户配置 (使用 Hash)
func (c *UserCache) HGetUserProfile(ctx context.Context, userID string, field string) (string, error) {
    key := c.prefix + "profile:" + userID
    return c.client.HGet(ctx, key, field).Result()
}

// SAddUserTag 为用户添加标签 (使用 Set)
func (c *UserCache) SAddUserTag(ctx context.Context, userID string, tags ...string) error {
    key := c.prefix + "tags:" + userID
    // Go-redis v8 Set/Hash 操作需要将 interface{} slice 转换为 []interface{}
    iTags := make([]interface{}, len(tags))
    for i, t := range tags {
        iTags[i] = t
    }
    return c.client.SAdd(ctx, key, iTags...).Err()
}
```

### 事务/Pipeline

Pipeline 用于将多个命令一次性发送到 Redis，减少网络往返，从而提高性能。Redis 的事务 (MULTI/EXEC) 也可以通过 Pipeline 实现。

```go
func (c *UserCache) BatchGetUsers(ctx context.Context, userIDs []string) (map[string]string, error) {
    pipe := c.client.Pipeline()
    results := make(map[string]*goredis.StringCmd)

    for _, id := range userIDs {
        key := c.prefix + id
        results[id] = pipe.Get(ctx, key)
    }

    // 执行 Pipeline
    _, err := pipe.Exec(ctx)
    if err != nil && err != goredis.Nil {
        return nil, err
    }

    userMap := make(map[string]string)
    for id, cmd := range results {
        // 即使 pipeline 的 Exec 返回错误，单个命令也可能成功
        // 需要逐个检查命令的错误状态
        val, err := cmd.Result()
        if err == nil {
            userMap[id] = val
        }
        // 可以选择忽略 goredis.Nil 错误
    }

    return userMap, nil
}

// Redis 事务示例：INCR 和 EXPIRE 原子化
func (c *UserCache) IncrWithTransaction(ctx context.Context, key string) error {
    pipe := c.client.TxPipeline()
    pipe.Incr(ctx, key)
    pipe.Expire(ctx, key, 1*time.Hour)
    _, err := pipe.Exec(ctx)
    return err
}
```

## 常见坑与推荐写法

### 大 Key/热 Key

- **大 Key**: 避免存储过大的 Value (如超过 1MB 的 JSON 字符串) 或包含数万个成员的 Hash/Set/List。大 Key 会导致网络阻塞、内存分配不均和删除缓慢。可将大对象拆分为多个小 Key。
- **热 Key**: 单个 Key 的 QPS 过高（如超过 5万）会导致 Redis 单核 CPU 瓶颈。可以通过在 Key 中加入随机前缀/后缀，将访问分散到多个 Key。

### 键名与序列化规范

- **键名**: 制定统一的命名规范，如 `业务:子业务:版本:唯一ID`，例如 `video:profile:v1:12345`。清晰的键名有助于问题排查和数据管理。
- **序列化**: 对于结构体数据，推荐使用 **Protobuf** 或 **MsgPack** 进行序列化，它们比 JSON 更紧凑、解析更快。避免使用 Go 的 `gob`，因为它有兼容性问题。

### TTL (过期时间) 与防雪崩策略

- **必须设置 TTL**: 缓存数据一定要设置过期时间，防止内存被无用数据占满。
- **防雪崩**: 给同一批写入的缓存设置一个随机的过期时间（例如，在基础过期时间上增加一个 0-10% 的随机值），避免大量缓存在同一时刻集体失效，导致所有请求穿透到数据库。

### 连接泄漏

`goredis` 客户端是并发安全的，应作为全局单例使用。**不要在每次请求处理时都创建一个新的客户端实例**，这会导致连接数暴增和性能问题。

### 缓存穿透与击穿

- **缓存穿透**: 对于查询一个不存在的数据，缓存中没有，数据库中也没有。这会导致每次请求都打到数据库。可以在缓存中为一个空结果设置一个短时间的占位符（如空字符串）。
- **缓存击穿**: 一个热点 Key 过期，大量并发请求同时访问这个 Key，导致所有请求都打到数据库。可以使用分布式锁，只让一个请求去查询数据库并写回缓存。

## 配置清单

### 连接参数

通过 `goredis.NewOption()` 设置：

| 参数           | 推荐区间/示例值          | 说明                                                       |
| -------------- | ------------------------ | ---------------------------------------------------------- |
| `PSM`          | `toutiao.redis.xxx`      | Redis 服务的 PSM (服务发现标识)。                          |
| `DialTimeout`  | `100ms`                  | 建立连接的超时时间。                                       |
| `ReadTimeout`  | `50ms` - `200ms`         | 读取 Redis 响应的超时时间。                                |
| `WriteTimeout` | `50ms` - `200ms`         | 向 Redis 写入数据的超时时间。                              |
| `PoolSize`     | `100` - `500`            | 每个 Redis 节点的连接池大小，根据 QPS 调整。               |
| `IdleTimeout`  | `10s` - `30s`            | 空闲连接的超时时间。                                       |
| `LiveTimeout`  | `30s` - `1m`             | 连接最大存活时间，比 `IdleTimeout` 略长。                  |
| `MaxRetries`   | `0` (默认)               | 内部已有重试机制，通常不需要业务层配置。                   |
| `breaker`      | 默认配置                 | 内部熔断器配置，通常使用默认值。                           |

### Key 命名规范

- **模板**: `<product>:<business>:<sub_business>:<version>:{id}`
- **示例**: `tiktok:user_profile:v2:{uid:12345}`
- **租户/版本维度**: 在 Key 中包含版本号或租户信息，便于数据隔离和未来迁移。
- **TTL 策略**:
  - **基础 TTL**: `Set(key, value, 24*time.Hour)`
  - **防雪崩 TTL (随机化)**: `Set(key, value, 24*time.Hour + time.Duration(rand.Intn(3600))*time.Second)`

### 序列化方式选择

| 方式        | 优点                         | 缺点                               | 适用场景                       |
| ----------- | ---------------------------- | ---------------------------------- | ------------------------------ |
| **JSON**    | 可读性好，调试方便，通用     | 性能较差，体积较大                 | 对性能要求不高的场景，或需要调试 |
| **Protobuf**| 高性能，体积小，跨语言支持好 | 需要预定义 `.proto` 文件，可读性差 | 对性能和空间敏感的核心业务     |
| **MsgPack** | 性能和体积优于 JSON，无需 IDL | 不如 Protobuf 普及，可读性差       | 在 Go 服务间作为 JSON 的替代品 |

**提示**: 对于非常大的对象 (如 > 1MB)，应考虑在业务层将其拆分为多个小的 Redis Key，或者使用压缩算法（如 Gzip, Snappy）在序列化后进行压缩，再存入 Redis。

## 示例 Prompt

- "请帮我使用 goredis 实现一个分布式锁，锁的过期时间为 30 秒，并提供加锁和解锁的代码示例。"
- "如何使用 goredis 的 Pipeline 功能批量获取 100 个 Key 的值？请给出示例代码。"
- "我需要缓存一个 `User` 结构体到 Redis，请展示如何使用 Protobuf 序列化该结构体，并用 goredis 的 `SET` 和 `GET` 命令进行存取。"
- "请解释 Redis 的缓存雪崩、穿透和击穿问题，并提供使用 goredis 的解决方案代码。"
- "给我一个使用 goredis 实现排行榜功能的例子，要求能添加用户分数并获取排名前 10 的用户列表。"

## 相关文档

- [go-redis 官方文档](https://redis.uptrace.dev/)
- [Redis 官方命令参考](https://redis.io/commands/)
