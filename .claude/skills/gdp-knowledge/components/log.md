# GDP 日志组件

## 概述

GDP 日志组件提供了简单、开箱即用的日志功能，专为字节跳动内部服务设计。通过统一的日志接口，开发者可以方便地记录调试信息、业务日志和错误信息，同时支持结构化日志输出和上下文信息传递。

**代码包**：code.byted.org/gdp/log

## 主要特性

- **简单易用**：提供统一的日志接口，引用即可使用
- **分级日志**：支持 Debug、Info、Warn、Error 四个业务日志级别
- **分离输出**：正常日志和错误日志分文件输出，便于问题定位
- **框架集成**：自动与 GDP 框架集成，支持上下文信息传递
- **结构化输出**：支持 KV 格式的结构化日志输出
- **合规支持**：适配不同机房环境的日志格式要求

## 快速上手

### 基本日志输出

使用标准库`fmt`一致的格式输出日志：

```go
import "code.byted.org/gdp/log"

func Invoker(ctx context.Context) (interface{}, af.RespError) {
    log.Debugf(ctx, "debug log, %d", 2333)
    log.Infof(ctx, "info log, %s", "value")
    log.Warnf(ctx, "warn log, %v", []string{"str1", "str2"})
    log.Errorf(ctx, "error log, %+v", map[string]interface{}{"key1": "val1", "key2": 1})
}
```

### 结构化日志输出

GDP 提供键值对方式输出日志，在普通机房格式`key=[value]`、合规机房（TTP、EU）`{{key=value}}`：

```go
import "code.byted.org/gdp/log"

func Invoker(ctx context.Context) (interface{}, af.RespError) {
    // 普通文本日志
    log.Debug(ctx, "debug log")

    // 结构化日志 with log.Fields
    log.Info(ctx, "info log", log.Fields{
        "req_size": 52,
        "req":      map[string]string{"uid": "2"},
    })

    // 结构化日志 with log.KV
    log.Warn(ctx, "warn log",
        log.KV{"req_size", 52},
        log.KV{"req", map[string]interface{}{"uid": 2}},
    )
}
```

### 上下文信息增强

`WithKV`与`WithKVs`用于给日志添加额外的 KV 信息，**且只在 Notice 日志输出**：

```go
import "code.byted.org/gdp/log"

func Invoker(ctx context.Context) (interface{}, af.RespError) {
    // 添加单个 KV
    ctx = log.WithKV(ctx, "key1", "val1")

    // 添加多个 KVs
    ctx = log.WithKVs(ctx,
        log.KV{"key2", "val2"},
        log.KV{"key3", "val3"},
    )

    // 输出日志时会包含之前添加的 KV 信息
    log.Info(ctx, "info log")
}
```

## 日志级别说明

GDP 基于业务使用场景，提供了与通用日志组件差别较大的封装形式：

| **等级** | **说明** | **使用场景** | **输出文件** |
| --- | --- | --- | --- |
| `Debug` | 调试级别 | 开发、测试、PPE 等场合 | `log/app/gdp-{p.s.m}.log` |
| `Info` | 普通级别 | 可能需要关注的场合 | `log/app/gdp-{p.s.m}.log` |
| `Warn` | 警告级别 | 服务执行非预期逻辑、需要关注 | `log/app/gdp-{p.s.m}.log.wf` |
| `Error` | 错误级别 | 服务执行非预期逻辑、严重错误 | `log/app/gdp-{p.s.m}.log.wf` |
| `Notice` | 框架级别 | 每次请求逻辑执行完后统一输出 | `log/app/gdp-{p.s.m}.log` |
| `Fatal` | 严重级别 | 服务出现严重错误、Panic 时 | `log/app/gdp-{p.s.m}.log.wf` |

**关键特性：**
- 提供简单、开箱即用的接口，引用即可使用
- 只提供四个业务日志级别，简化使用
- **正常与错误日志分文件输出**，便于问题定位
- 结合框架能力，保证每次请求输出 Notice 日志
- 只有在异常场合才输出 Fatal 日志

## 最佳实践

### 日志级别选择
- **Debug**: 仅在开发和测试环境使用，生产环境应关闭
- **Info**: 记录重要的业务状态变化
- **Warn**: 记录可恢复的错误或异常情况
- **Error**: 记录需要立即关注的严重错误

### 结构化日志
- 优先使用结构化日志（KV 格式）便于后续分析
- 合理使用 `WithKV`/`WithKVs` 添加上下文信息
- 避免在日志中输出敏感信息

### 性能考虑
- 日志输出是同步操作，避免在高频路径中输出过多日志
- 使用合适的日志级别控制日志量
- 合理使用采样和聚合策略

## 相关文档
- [RAL概述](../ral/overview.md) - RAL组件总体介绍
- [RPC资源](../ral/rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](../ral/abase_redis.md) - 缓存资源配置和使用
- [Database资源](../ral/database.md) - 数据库资源配置和使用
- [Eventbus资源](../ral/eventbus.md) - 消息队列资源配置和使用