# GDP 插件与中间件开发指南

> 适用框架：GDP、gdp/af、gdp/raf、gdp/ral

## 概述

GDP 为 HTTP（af）、RPC（raf）框架提供了**中间件机制**，并为 HTTP（af）框架提供了**插件机制**，用于将服务中通用逻辑统一注入到指定业务逻辑中。

- **插件**：af 框架独有，基于 AOP 编程思想，分阶段执行，功能强大但实现较复杂
- **中间件**：af 与 raf 均支持，基于责任链设计模式，开发简单

## 开发插件

> 插件机制为 `af` 框架独有，`raf` 框架不具备此能力

### 插件接口

```go
import "code.byted.org/gdp/af"

type Plugin interface {
    Type() af.PluginType
    Init()
    OnStartup(ctx context.Context) (context.Context, af.RespError)
    OnShutdown(ctx context.Context) context.Context
    OnSuccess(ctx context.Context, resp interface{})
    OnError(ctx context.Context, err af.RespError)
}
```

### 插件类型

```go
func (p *plugin) Type() af.PluginType {
    return af.PluginTypeNormal // 普通插件
}
```

| 类型 | 说明 | 是否必须注册 |
|------|------|------------|
| `PluginTypeNormal` | 普通插件，绝大部分插件归属此类。按注册顺序执行，某个插件 panic 后续不再执行 | 否 |
| `PluginTypeResp` | 返回值插件，对业务逻辑返回数据结构进行统一打包。优先于普通插件执行，异常独立处理 | **是**（否则启动报错） |
| `PluginTypeFinish` | 终结插件，最先/最后执行的兜底插件（如日志打点）。异常独立处理 | 否 |

### 插件执行阶段

| 执行阶段 | 对应接口 | 说明 |
|----------|----------|------|
| 逻辑执行 | `OnStartup(ctx) (ctx, RespError)` | 业务逻辑开始前执行；返回错误会中断后续流程 |
| 逻辑执行 | `OnShutdown(ctx) ctx` | 业务逻辑执行结束后执行；只能做收尾操作 |
| 结果处理 | `OnSuccess(ctx, resp)` | 只在业务逻辑成功后执行（`resp != nil && err == nil`） |
| 结果处理 | `OnError(ctx, err)` | 只在业务逻辑失败后执行（`resp == nil && err != nil`） |

**不需要某阶段时，方法留空即可。**

### 插件流程控制

只能在 `OnStartup` 阶段进行流程控制：

```go
// 方式1：中断并放弃后续所有业务逻辑（包括插件、中间件和业务逻辑）
func (p *Plugin) OnStartup(ctx context.Context) (context.Context, af.RespError) {
    if criticalErr != nil {
        af.Exit(ctx) // 中断后续所有逻辑
        return ctx, nil
    }
}

// 方式2：返回错误，当前插件后续逻辑不执行，已执行插件继续执行其剩余逻辑
func (a *plugin) OnStartup(ctx context.Context) (context.Context, af.RespError) {
    if err := doValid(ctx); err != nil {
        return ctx, af.NewRespError(err.code, a.opts.respErrorNo)
    }
    return ctx, nil
}
```

### 插件注册

推荐使用**插件包管理模式**：

```go
import (
    "code.byted.org/gdp/af"
    "code.byted.org/gdp/gdp"
)

// 1. 定义插件包
func ProductA() *af.PluginSuite {
    s := af.NewPluginSuite(
        plugin1.New(),
        plugin2.New(),
    )
    s.Register(xxxx) // 注册单个插件到插件包
    return s
}

// 2. 注册插件包到框架
func main() {
    gdp.Init(
        // ...
        gdp.WithAfPluginSuite(ProductA),
    ).Run()
}
```

## 开发中间件

> af 与 raf 均支持中间件，但实现上有些差异

### 中间件接口

```go
// API 框架（af）
func Middleware(ctx context.Context) (resp interface{}, err af.RespError)

// RPC 框架（raf）
func Middleware(ctx context.Context, req interface{}) (resp interface{}, err raf.RespError)
```

### 流程控制

#### Next：继续执行下一个中间件

> 注意：`Next` 不能在同一中间件内部被调用多次（会覆盖执行结果）

```go
func APIMdw(ctx context.Context) (interface{}, RespError) {
    // 前置逻辑...
    resp, err := af.Next(ctx)
    // 后置逻辑...
    return resp, err
}

func RPCMdw(ctx context.Context, req interface{}) (interface{}, RespError) {
    resp, err := raf.Next(ctx, req)
    return resp, err
}
```

#### Abort：放弃后续逻辑执行

> 只标记后续逻辑放弃执行，当前中间件剩余逻辑还会继续执行

```go
func APIMdw(ctx context.Context) (resp interface{}, err RespError) {
    if err != nil {
        af.Abort(ctx)
        return resp, err
    }
    // ...
}

func RPCMdw(ctx context.Context, req interface{}) (resp interface{}, err RespError) {
    if err != nil {
        raf.Abort(ctx)
        return resp, err
    }
    // ...
}
```

### 中间件注册

#### 全局注册（推荐使用中间件包形式）

```go
// API 框架（af）
import (
    "code.byted.org/gdp/af"
    "code.byted.org/gdp/gdp"
)

func ProductA() *af.MiddlewareSuite {
    s := af.NewMiddlewareSuite(mdw1)
    s.Use(mdw2)
    return s
}

func main() {
    gdp.Init(
        gdp.WithAfMiddlewareSuite(ProductA),
    ).Run()
}

// RPC 框架（raf）
import (
    "code.byted.org/gdp/gdp"
    "code.byted.org/gdp/raf"
)

func ProductA() *raf.MiddlewareSuite {
    s := raf.NewMiddlewareSuite(mdw1)
    s.Use(mdw2)
    return s
}

func main() {
    gdp.Init(
        gdp.WithRafMiddlewareSuite(ProductA),
    ).Run()
}
```

也可独立注册：`af.Use(mdw1, mdw2)`

#### 路由组注册（仅 af 支持）

```go
r := af.NewRouter("/path/to/test")
r.Use(mdw1, mdw2) // 只在路由组内所有接口生效
```

#### 接口注册（仅 af 支持）

```go
r := af.NewRouter("/path/to/test")
r.GET("/path/to/mdw", af.RouteWithMiddlewares(mdw3, mdw4)) // 只在该接口生效
```

## 自定义参数传递

框架提供基于 URI 的静态参数注册传递机制，可将接口级别的参数传递给插件/中间件/业务逻辑。

### 注册自定义参数

```go
type RouteOpt interface {
    Name() interface{} // 唯一标识，建议使用结构体确保唯一性
    Data() interface{} // 需要传递的数据，可以是任意类型
}

// 注册到路由接口
r.POST("path/to/uri", hdlr, af.RouteWithOpt(xxx))
```

示例（JWT 插件参数控制）：

```go
type jwtOpt struct {
    enable bool
}

func (j *jwtOpt) Name() interface{} { return jwtJudgeKey }
func (j *jwtOpt) Data() interface{} { return j.enable }

func Enable() af.RouterOption  { return af.RouteWithOpt(&jwtOpt{true}) }
func Disable() af.RouterOption { return af.RouteWithExtra(&jwtOpt{false}) }

r.POST("path/to/enable", hdlr, jwt.Enable())
r.GET("path/to/disable", hdlr, jwt.Disable())
```

### 使用自定义参数

```go
// 在插件、中间件、业务逻辑的任意阶段获取
data, ok := af.RouterExtra(ctx, jwtJudgeKey)
if ok && !data.(bool) {
    return ctx, nil
}
```

## 插件 vs 中间件选择指南

| 维度 | 插件 | 中间件 |
|------|------|--------|
| 实现复杂度 | 复杂（多阶段接口） | 简单（单函数） |
| 执行顺序 | 优先于中间件执行 | 在所有插件 OnStartup 后执行 |
| 阶段控制 | 明确的切面接口（OnStartup/OnShutdown/OnSuccess/OnError） | 需自行判断执行时机 |
| 适用场景 | 复杂通用逻辑、需要模块化组织 | 简单通用逻辑 |
| 框架支持 | 仅 af | af 和 raf |

## 已实现插件参考

参考仓库：https://code.byted.org/gdp/plugin/

| 插件名 | 插件包 | 备注 |
|--------|--------|------|
| `cdf` | `code.byted.org/gdp/plugin/cdf` | |
| `jwt` | `code.byted.org/gdp/plugin/jwt` | JWT 插件 |
| `session` | `code.byted.org/gdp/plugin/session` | **国内业务使用**，passport 与 odin 中台服务封装 |
| `tiktok_session` | `code.byted.org/gdp/plugin/tiktok_session` | **海外 TikTok 业务使用** |
| `swagger` | `code.byted.org/gdp/plugin/swagger` | Swagger 插件 |
