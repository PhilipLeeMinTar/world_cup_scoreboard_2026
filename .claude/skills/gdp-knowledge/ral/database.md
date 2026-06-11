# Database资源配置和使用

## 概述

Database资源基于`gorm.io/gorm`封装，并完全兼容`gorm`的链式调用。但是不支持基于`gorm/gen`代码生成的数据库管理形式。RAL提供了完整的数据库连接池管理和事务支持。

## 主要特性

- **GORM兼容**：完全兼容GORM的链式调用语法，支持所有GORM特性
- **连接池管理**：自动数据库连接池管理，支持连接复用和负载均衡
- **事务支持**：完整的事务支持，包括手动事务和自动事务管理
- **读写分离**：支持主从数据库配置，自动读写分离
- **多数据库支持**：支持MySQL、PostgreSQL等多种关系型数据库
- **性能监控**：内置SQL执行监控和慢查询日志功能
- **配置灵活**：支持多种数据库配置选项和扩展参数

## 资源配置

RDS 的配置需要注意的细节：

- `Protocol`配置为：`rds`
- `ExtensionCfg`中的`DBName`为必填字段
- 默认事务选项`SkipDefaultTransaction`**在 RAL 中为****`true`**，`bytedgorm`默认为`false`

### 配置示例

```yaml
tar_cluster_rds:
  PSM: toutiao.mysql.target_cluster
  Protocol: rds
  ConnTimeout: 0s
  ReadTimeout: 5s
  WriteTimeout: 5s
  ExtensionCfg:
    IsDefault: true
    Cluster:
      ENV_maliva: ie
    DBName: gdp_data
    DBCharset: utf8mb4
    TablePrefix: ral_ut_
    SkipDefaultTransaction: true
    MaxIdleConns: 200
    MaxOpenConns: 300
```

### 扩展配置字段

`ExtensionCfg`支持的配置字段如下：

| **字段名** | **`Env_tag`** | **字段含义** |
| --- | --- | --- |
| `IsDefault` | `不支持` | 是否设置为默认集群 |
| `Cluster` | `支持` | 需要跨机房访问时需要指定的目标集群<br />• 关于此参数更详细的解释，请参考： |
| `ReadReplicas` | `不支持` | 是否开启读写分离，**此选项默认关闭** |
| `DBName` | 支持 | 数据库名称，**必填项** |
| `DBCharset` | `不支持` | 访问数据库时所用的字符集，默认`utf8mb4` |
| `TablePrefix` | `不支持` | 数据库表前缀，如果配置会在访问数据库时拼接上表前缀 |
| `SkipDefaultTransaction` | `不支持` | 是否关闭默认事务，**此选项默认关闭**（与 gorm 默认选项相反） |
| `MaxIdleConns` | `不支持` | 数据库连接池最大空闲连接数 |
| `MaxOpenConns` | `不支持` | 数据库连接池最大开启连接数 |

## 使用客户端

`DB`客户端的使用方式与`gorm`完全一致，并提供了跨连接事务的支持。

### 链式调用

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/db"
)

func ChainableCall(ctx context.Context) {
    tx := db.Conn(ctx) // get db connection

    var ret User

    // gorm style chainable call
    if err := tx.Where("id > ?", 1).Where("id < ?", 10).Find(&ret).Error; err != nil {
        // ...
    }
}
```

### 事务支持

支持**单连接事务**与**跨连接事务**，同时跨连接事务也可调用需要`context`场景的函数，使用场景更广。

#### 单连接事务

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/db"
)

func NormalTransaction(ctx context.Context) {
    tx := db.Conn(ctx) // get connection with context

    if err := tx.Transaction(func(tx *db.DB) error {
        tx.Limit(1).Find()
        // ...

        return nil
    }); err != nil {
        // ...
    }
}
```

#### 跨连接事务

```go
import (
    "context"

    "code.byted.org/gdp/ral/c/db"
)

func ContextTransaction(ctx context.Context) {
    err := db.Transaction(ctx, func (ctx context.Context) error {
        // transaction in another db cluster
        if err := db.Transaction(ctx, func(ctx context.Context) error{
            tx := db.Conn(ctx)
            // ...
        }, db.WithCluster("tar_another_cluster")); err != nil {
            return err
        }

        // tx in current db cluster
        tx := db.Conn(ctx)
        // ...

        if err := methodNeedsCtx(ctx); err != nil {
            return err
        }

        return nil
    })
}
```

## 请求日志

```
Notice invokehandler.go:92 10.78.204.49 p.s.m - default - 0 span=[0.5] req_start_time=[1716434954.2671769] req_name=[rds_data] psm=[toutiao.mysql.gdp_data] req_type=[rds] write_timeout=[5s] read_timeout=[5s] dry_run=[false] target_cluster=[boe] db_name=[gdp_data] mesh_mode=[false] remote_addr=[toutiao.mysql.gdp_data_read] table=[ral_ut_resp_detail] sql=[SELECT * FROM `ral_ut_resp_detail` WHERE resp_id=? ORDER BY `ral_ut_resp_detail`.`resp_id` LIMIT ?] rows_affected=[1] req=[20.989ms] total=[20.995ms] errno=[0] errmsg=[ok]
```

请求日志字段说明：

|   | **字段名** | **字段详情** |
| --- | --- | --- |
| 请求信息 | `dry_run`<br />`target_cluster`<br />`db_name`<br />`table`<br />`sql` | • 是否是 dryRun 状态，可用于调试，**dryRun 下所有请求都不会提交**<br />• 设置跨机房集群后，当前请求访问的集群（设置后才会输出）<br />• 请求数据库名称<br />• 请求数据库表名<br />• 请求 SQL，默认为 prepare 语句，Debug 会打印全语句 |
| 结果信息 | `rows_affected`<br />`record_not_found` | • 此次 SQL 执行涉及的行数<br />• 如果是查询语句并未查询到任何信息，会出现此字段 |

## 相关文档

- [RAL概述](overview.md) - RAL组件总体介绍
- [RPC资源](rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](abase_redis.md) - 缓存资源配置和使用
- [Eventbus资源](eventbus.md) - 消息队列资源配置和使用
- [单元测试](testing.md) - RAL组件单元测试指南