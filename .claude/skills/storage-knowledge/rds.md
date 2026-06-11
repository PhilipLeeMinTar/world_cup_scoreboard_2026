# RDS (MySQL) SDK 使用指南 - BytedGORM

## 概述

**BytedGORM** 是基于开源 [GORM](https://gorm.io/) 的字节跳动内部封装版本，专为访问 **RDS (MySQL)** 这类关系型数据库设计。它继承了 GORM 的所有功能，并集成了字节内部的中间件生态，如服务发现、监控、全链路压测、安全认证等。

**特性**：
- 完整继承 GORM ORM 功能
- 集成字节内部服务发现、监控、压测等中间件
- 支持读写分离
- 支持事务管理
- 支持连接池管理

**代码包**：
- `gorm.io/gorm`
- `gorm.io/driver/mysql`
- `code.byted.org/gorm/bytedgorm`

## 适用场景

- **业务数据存储**: 适合需要事务保证、结构化数据存储的核心业务场景，如用户信息、订单、商品等。
- **复杂查询**: 支持 Join、Group By、子查询等复杂 SQL 查询。
- **快速原型开发**: ORM 特性可以帮助开发者快速构建应用的增删改查 (CRUD) 逻辑。

## 定位对比

- 与 **Redis** 相比，RDS (MySQL) 提供持久化、强一致性的事务型数据存储，适合作为核心业务的权威数据源；而 Redis 则侧重于高性能的内存缓存和键值存储。
- 与 **ABase/Bytedoc** 相比，RDS 是关系型数据库，强制要求结构化（Schema-on-Write），提供强大的事务和关联查询能力；而 ABase (NoSQL 表存储) 和 Bytedoc (文档数据库) 则提供更灵活的数据模型（Schema-on-Read），适合半结构化或非结构化数据。

## 连接与初始化

初始化 BytedGORM 客户端是服务启动阶段的关键步骤，需要正确配置连接池、超时、重试等参数。

### 配置项

主要通过 DSN (Data Source Name) 字符串进行配置，也可以通过 `bytedgorm.NewDB` 结合 `mysql.Config` 进行更精细的控制。

### 连接池

底层使用 `database/sql` 的连接池。关键参数包括：
- `SetMaxOpenConns`: 最大打开连接数。建议根据服务 QPS 和数据库承载能力设置，例如 `100`。
- `SetMaxIdleConns`: 最大空闲连接数。建议设置为 `MaxOpenConns` 的 10%-20%，例如 `10`。
- `SetConnMaxLifetime`: 连接最大存活时间。建议设置为 `1h`，避免因网络设备策略导致连接失效。
- `SetConnMaxIdleTime`: 连接最大空闲时间。建议设置为 `30m`，回收长时间不用的连接。

### TLS/认证

BytedGORM 内部封装了字节的安全认证体系，通常无需手动配置 TLS 证书。

### 超时与重试

- **连接超时**: 在 DSN 中通过 `timeout` 参数设置，如 `timeout=10s`。
- **读写超时**: 在 DSN 中通过 `readTimeout` 和 `writeTimeout` 设置，如 `readTimeout=5s`。
- **重试**: GORM 层面默认不提供自动重试。业务层应针对网络抖动等临时性错误封装重试逻辑。

### 读写分离

BytedGORM 支持通过 GORM 的 [DB Resolver](https://gorm.io/docs/dbresolver.html) 插件实现读写分离，将写操作路由到主库，读操作路由到从库。

## 生命周期管理

- **启动**: 在服务启动时，创建全局唯一的 `*gorm.DB` 实例，并将其注入到依赖容器中（如 Wire、Fx 或自定义容器）。
- **健康检查**: 实现一个健康检查接口，定期调用 `db.DB().Ping()` 来验证数据库连接的可用性。
- **关闭**: 在服务优雅关闭时，调用 `db.DB().Close()` 来关闭所有数据库连接。

## 依赖注入

- **Wire/Fx**: 使用依赖注入框架管理 `*gorm.DB` 实例的生命周期，可以简化代码结构。
- **手写容器**: 对于简单应用，可以在 `main` 函数中初始化 `*gorm.DB`，并将其作为参数传递给业务逻辑层。

## 典型代码片段

### 初始化

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "gorm.io/driver/mysql"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
    "code.byted.org/gorm/bytedgorm"
)

// User 模型定义
type User struct {
    ID        uint   `gorm:"primaryKey"`
    Name      string `gorm:"size:255;not null"`
    Email     string `gorm:"unique;not null"`
    CreatedAt time.Time
    UpdatedAt time.Time
}

// NewDB 创建并返回一个 GORM DB 实例
func NewDB(dsn string) (*gorm.DB, error) {
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
        // 字节内部封装，集成监控、压测等
        NowFunc: bytedgorm.NowFunc,
    })
    if err != nil {
        return nil, fmt.Errorf("failed to connect to database: %w", err)
    }

    // 使用 bytedgorm 的插件
    if err := db.Use(bytedgorm.NewPlugin()); err != nil {
        return nil, fmt.Errorf("failed to use bytedgorm plugin: %w", err)
    }

    sqlDB, err := db.DB()
    if err != nil {
        return nil, fmt.Errorf("failed to get sql.DB: %w", err)
    }

    // 设置连接池参数
    sqlDB.SetMaxIdleConns(10)
    sqlDB.SetMaxOpenConns(100)
    sqlDB.SetConnMaxLifetime(time.Hour)
    sqlDB.SetConnMaxIdleTime(30 * time.Minute)

    return db, nil
}

func main() {
    // DSN (Data Source Name)
    // 格式: user:password@tcp(host:port)/dbname?charset=utf8mb4&parseTime=True&loc=Local
    dsn := "user:password@tcp(127.0.0.1:3306)/my_db?charset=utf8mb4&parseTime=True&loc=Local&timeout=10s"

    db, err := NewDB(dsn)
    if err != nil {
        log.Fatalf("database connection failed: %v", err)
    }

    // 自动迁移 schema
    if err := db.AutoMigrate(&User{}); err != nil {
        log.Fatalf("failed to migrate schema: %v", err)
    }

    fmt.Println("Database connected and schema migrated successfully.")

    // 在这里执行业务逻辑...
}
```

### 基本 CRUD

```go
package repository

import (
    "context"
    "gorm.io/gorm"
)

type UserRepository struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) *UserRepository {
    return &UserRepository{db: db}
}

// CreateUser 创建用户
func (r *UserRepository) CreateUser(ctx context.Context, user *User) error {
    return r.db.WithContext(ctx).Create(user).Error
}

// GetUserByID 根据 ID 查询用户
func (r *UserRepository) GetUserByID(ctx context.Context, id uint) (*User, error) {
    var user User
    err := r.db.WithContext(ctx).First(&user, id).Error
    if err != nil {
        // gorm.ErrRecordNotFound 是一个常见的错误，表示未找到记录
        return nil, err
    }
    return &user, nil
}

// UpdateUser 更新用户信息
func (r *UserRepository) UpdateUser(ctx context.Context, user *User) error {
    // Save 会更新所有字段，即使是零值
    // Updates 只更新非零值字段，或使用 map/struct 指定字段
    return r.db.WithContext(ctx).Model(user).Updates(User{Name: user.Name, Email: user.Email}).Error
}

// DeleteUser 删除用户
func (r *UserRepository) DeleteUser(ctx context.Context, id uint) error {
    return r.db.WithContext(ctx).Delete(&User{}, id).Error
}
```

### 事务

GORM 推荐使用 `Transaction` 方法，它可以自动处理提交和回滚。

```go
func (s *UserService) CreateUserWithProfile(ctx context.Context, userName, profileInfo string) error {
    return s.db.Transaction(func(tx *gorm.DB) error {
        // 1. 创建用户
        user := User{Name: userName}
        if err := tx.WithContext(ctx).Create(&user).Error; err != nil {
            // 返回错误，事务将自动回滚
            return err
        }

        // 2. 创建用户资料
        profile := Profile{UserID: user.ID, Info: profileInfo}
        if err := tx.WithContext(ctx).Create(&profile).Error; err != nil {
            return err
        }

        // 返回 nil，事务将自动提交
        return nil
    })
}
```

### 错误处理与超时

```go
import (
    "context"
    "errors"
    "time"
    "gorm.io/gorm"
)

func (r *UserRepository) GetUserWithTimeout(id uint) (*User, error) {
    // 设置请求级别的超时
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()

    var user User
    err := r.db.WithContext(ctx).First(&user, id).Error

    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            // 业务上可区分处理"未找到"
            return nil, fmt.Errorf("user with id %d not found", id)
        }
        if errors.Is(ctx.Err(), context.DeadlineExceeded) {
            // 超时错误
            return nil, fmt.Errorf("database query timed out: %w", err)
        }
        // 其他数据库错误
        return nil, fmt.Errorf("database error: %w", err)
    }

    return &user, nil
}
```

## 常见坑与推荐写法

### 避免 N+1 查询

在查询列表及关联数据时，使用 `Preload` 提前加载关联数据，而不是在循环中单独查询。

- **错误**: 遍历用户列表，在循环中查询每个用户的资料。
- **正确**: `db.Preload("Profile").Find(&users)`

### 索引与分页注意事项

- **索引**: 确保所有 `WHERE`、`ORDER BY`、`JOIN` 的字段都已建立合适的索引。使用 `EXPLAIN` 分析查询计划。
- **分页**: 避免使用 `OFFSET` 进行深分页，因为它在数据量大时性能会急剧下降。推荐使用基于游标（Cursor-based）的分页，即每次查询都带上上一页最后一条记录的 ID 或排序字段值。
  - **错误**: `db.Limit(10).Offset(100000).Find(&users)`
  - **正确**: `db.Where("id > ?", lastID).Limit(10).Order("id asc").Find(&users)`

### 键名与序列化规范

- 模型字段使用 `gorm` 标签明确指定列名、类型、约束等，保持代码与数据库结构一致。
- GORM 自动处理 Go 结构体与数据库记录的序列化，无需手动干预。

### 事务边界与幂等

- **事务边界**: 事务应尽可能小，只包裹必要的原子操作。避免在事务中执行 RPC 调用或其他耗时操作。
- **幂等**: 对于创建或更新操作，如果需要保证幂等性，可以在业务逻辑中先查询记录是否存在，或利用数据库的唯一索引约束来防止重复插入。

### 热点限流与降级

BytedGORM 会集成字节内部的限流、熔断组件。业务层应关注核心接口的性能，并准备降级预案（如从缓存读取、返回默认值等）。

### 连接泄漏

- **务必确保手动事务 (`db.Begin()`) 都有对应的 `Commit()` 或 `Rollback()`**。推荐使用 `db.Transaction()` 自动管理事务生命周期。
- 监控连接池的 `WaitCount`、`WaitDuration` 等指标，如果持续升高，很可能存在连接泄漏或连接池配置不合理。

## 配置清单

### 连接参数 (DSN)

`user:password@tcp(host:port)/dbname?charset=utf8mb4&parseTime=True&loc=Local&timeout=10s&readTimeout=5s&writeTimeout=5s`

| 参数            | 推荐区间/示例值                      | 说明                                                         |
| --------------- | ------------------------------------ | ------------------------------------------------------------ |
| `endpoint`      | `host:port`                          | 数据库地址和端口。内部环境通常通过服务发现获取。             |
| `数据库/集合`   | `dbname`                             | 数据库名称。                                                 |
| `认证`          | `user:password`                      | 用户名和密码。内部环境通常通过安全组件自动注入。             |
| `timeout`       | `10s`                                | 建立 TCP 连接的超时时间。                                    |
| `readTimeout`   | `5s`                                 | 读取数据库响应的超时时间。                                   |
| `writeTimeout`  | `5s`                                 | 向数据库写入数据的超时时间。                                 |
| `parseTime`     | `True`                               | 必须为 `True`，以便 GORM 能正确处理 `time.Time` 类型。       |
| `loc`           | `Local`                              | 时区设置，确保时间数据正确。                                 |
| `charset`       | `utf8mb4`                            | 字符集，推荐使用 `utf8mb4` 以支持 Emoji 等字符。             |

### 连接池配置

| 参数                | 推荐区间/示例值 | 说明                                                         |
| ------------------- | --------------- | ------------------------------------------------------------ |
| `MaxOpenConns`      | `50` - `200`    | 最大打开连接数，根据 QPS 和数据库规格调整。                  |
| `MaxIdleConns`      | `10` - `20`     | 最大空闲连接数，通常为 `MaxOpenConns` 的 10%-20%。           |
| `ConnMaxLifetime`   | `1h`            | 连接最大存活时间，防止因网络策略导致的长连接失效。           |
| `ConnMaxIdleTime`   | `30m`           | 连接最大空闲时间，回收不活跃连接，节约资源。                 |

### 命名规范

- **库/表名**:
  - 使用小写字母、数字和下划线 `_`。
  - 表名应为复数形式，如 `users`, `orders`。
  - 推荐使用环境前缀，如 `dev_users`, `prod_users`，但这通常由 DBA 规范或发布系统保证。
- **模型名**:
  - Go 结构体使用驼峰式命名，如 `User`, `OrderDetail`。

## 示例 Prompt

- "请帮我在现有 Go 服务中集成 BytedGORM，并增加一个 `products` 表的 CRUD 接口，表结构包含 ID、名称、价格和创建时间。"
- "如何使用 BytedGORM 实现一个用户注册功能？该功能需要在一个事务中同时向 `users` 表和 `user_profiles` 表写入数据。"
- "给我一个使用 BytedGORM 进行分页查询的示例代码，要求使用基于游标的分页方式以优化性能。"
- "如何配置 BytedGORM 的读写分离，将所有查询请求路由到只读从库？"
- "我的服务在使用 BytedGORM 时出现了大量的 'too many connections' 错误，请帮我分析可能的原因并提供连接池的推荐配置。"

## 相关文档

- [GORM 官方文档](https://gorm.io/docs/)
- [GORM DB Resolver (读写分离)](https://gorm.io/docs/dbresolver.html)
