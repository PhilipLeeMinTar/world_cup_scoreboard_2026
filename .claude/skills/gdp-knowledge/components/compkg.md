# compkg 组件使用指南

## 概述

`compkg` 是 TikTok 基于 GDP 开发的通用基础库,封装了 API 与 RPC 服务所需的大量通用逻辑和工具。

**代码库地址**: `code.byted.org/tiktok/compkg`

## 核心组件

### 路由选项 (options)

路由选项用于配置接口的校验规则和响应打包方式。

#### 基础使用

```go
import "code.byted.org/tiktok/compkg/options"

func YourApiOpts() []af.RouterOption {
    // 获取默认参数
    dp := options.DefaultAPIOptionalParam()

    // 自定义配置
    dp.CheckUser = false  // 关闭强制登录校验

    return []af.RouterOption{
        options.WithAPIOption(dp, YourApiHandler),
    }
}
```

#### 接口校验设置

| 字段 | 类型 | 默认值 | 用途 |
|------|------|--------|------|
| `CheckUser` | `bool` | `true` | 是否进行强制登录校验 |
| `WeakCheckUser` | `bool` | `false` | 是否进行弱登录校验(CheckUser 为 false 时生效) |
| `BlockFTC` | `bool` | `false` | 是否拦截 FTC 用户 |
| `CheckWhale` | `bool` | `false` | 是否进行 Whale 验签 |

**示例**:
```go
// 公开接口(无需登录)
func GetPublicInfoOpts() []af.RouterOption {
    dp := options.DefaultAPIOptionalParam()
    dp.CheckUser = false  // 不检查登录状态
    return []af.RouterOption{
        options.WithAPIOption(dp, GetPublicInfo),
    }
}

// 需要登录的接口
func GetUserProfileOpts() []af.RouterOption {
    dp := options.DefaultAPIOptionalParam()
    dp.CheckUser = true   // 强制登录(默认)
    dp.BlockFTC = true    // 拦截 FTC 用户
    return []af.RouterOption{
        options.WithAPIOption(dp, GetUserProfile),
    }
}
```

#### 响应打包设置

**JSON 格式(默认)**:
```go
options.WithAPIOption(dp, handler)
```

**Protobuf 格式**:
```go
options.WithAPIOption(dp, handler,
    options.WithRespProtoBuf(),
)
```

**图片格式**:
```go
options.WithAPIOption(dp, handler,
    options.WithRespImage(),  // JPEG 格式
)
```

### 错误处理 (errors)

`compkg/errors` 提供了统一的错误返回机制。

#### 基础使用

```go
import (
    "code.byted.org/gdp/af"
    errcode "code.byted.org/ies/errcode_i18n"
    "code.byted.org/tiktok/compkg/errors"
)

func YourApiHandler(ctx context.Context) (interface{}, af.RespError) {
    // 业务逻辑
    if someErrorOccurs {
        // 返回标准错误
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    return response, nil
}
```

#### 常用错误码

```go
errcode.ERR_INVALID_PARAM        // 参数错误
errcode.ERR_PERMISSION_DENIED    // 权限不足
errcode.ERR_NOT_FOUND            // 资源不存在
errcode.ERR_INTERNAL             // 内部错误
errcode.ERR_SERVICE_UNAVAILABLE  // 服务不可用
```

### 日志与监控

#### 通用日志

框架为每个请求自动输出 `Notice` 日志,包含:
- 请求路径和参数
- 处理耗时
- 错误码
- 响应大小

无需手动实现通用日志逻辑。

**自定义日志**:
```go
import "code.byted.org/gopkg/logs"

logs.Info(ctx, "User created successfully", logs.String("user_id", userID))
logs.Warn(ctx, "High latency detected", logs.Int64("latency_ms", latency))
logs.Error(ctx, "Database error", logs.String("error", err.Error()))
```

#### 通用打点

框架通过 `gdp/metrics` 自动上报:
- **吞吐量**: QPS
- **延迟**: P50, P95, P99
- **错误率**: 4xx, 5xx 错误率

**自定义打点**:
```go
import "code.byted.org/gdp/metrics"

// Counter
metrics.EmitCounter(ctx, "user.create.success", 1)

// Timer
start := time.Now()
// ... do something
metrics.EmitTimer(ctx, "user.create.latency", time.Since(start))

// Store
metrics.EmitStore(ctx, "user.cache.hit_rate", hitRate)
```

## 高级功能

### 参数获取

```go
import "code.byted.org/gdp/af"

func Handler(ctx context.Context) (interface{}, af.RespError) {
    // 获取查询参数
    userID := af.Query(ctx, "user_id")

    // 获取路径参数
    id := af.Param(ctx, "id")

    // 获取 Header
    token := af.Header(ctx, "Authorization")

    // 获取 Form 数据
    name := af.FormValue(ctx, "name")

    // 上传文件
    file, err := af.FormFile(ctx, "file")
}
```

### 请求上下文

```go
// 获取用户 ID
userID := af.GetUserID(ctx)

// 获取设备 ID
deviceID := af.GetDeviceID(ctx)

// 获取请求 ID
requestID := af.GetRequestID(ctx)

// 获取客户端 IP
clientIP := af.GetClientIP(ctx)
```

### 响应设置

```go
func Handler(ctx context.Context) (interface{}, af.RespError) {
    // 设置响应 Header
    af.SetHeader(ctx, "X-Custom-Header", "value")

    // 设置响应状态码
    af.SetStatus(ctx, 201)

    return response, nil
}
```

## 最佳实践

1. **合理配置路由选项**: 根据接口特点选择登录校验策略
2. **统一错误处理**: 使用 compkg/errors 包装所有错误
3. **充分利用日志**: 关键操作记录日志,便于问题排查
4. **自定义打点**: 为核心业务指标添加自定义打点
5. **参数校验**: 在 Action 层使用 af.Bind 绑定和校验参数

## 常见问题

**Q: 如何关闭某个接口的登录校验?**
A: 在路由选项中设置 `dp.CheckUser = false`

**Q: 如何返回自定义错误码?**
A: 使用 `errors.WithError(ctx, yourErrCode)`

**Q: 如何获取当前登录用户信息?**
A: 使用 `af.GetUserID(ctx)` 获取用户 ID

**Q: 如何实现接口限流?**
A: 使用 GDP 框架的限流中间件或 compkg 的限流组件

## 相关文档

- [arch-action-layer-examples.md](../architecture/arch-action-layer-examples.md) - Action 层代码示例
- [arch-code-layers-guide.md](../architecture/arch-code-layers-guide.md) - 代码分层架构指南
