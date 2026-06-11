# ByteTIM HTTP 框架集成指南

ByteTIM 支持多种 HTTP 框架的中间件接入，包括 Ginex、Hertz v1.x、Hertz v0.x 等。这些中间件会根据业务方注册时所填的用户类型以及设备类型，生成相应的流量身份标识。

## Ginex 框架集成

若业务方服务是基于 Ginex 框架开发的，ByteTIM 提供了易用的中间件，可参考以下示例代码接入：

```go
import (
    "code.byted.org/gin/ginex"
    // Tiktok 业务请使用 session_lib code.byted.org/tiktok/tiktok_session_lib
    "code.byted.org/passport/session_lib"
    "code.byted.org/bytetim/client-go/generator/timginex"
)

func main() {
    ginex.Init()
    conf := session_lib.SessionClientConfig{Caller: ginex.PSM()}
    session_lib.Init(conf) // 初始化session SDK（C端用户才需要，否则不需要引入）
    timginex.MustInit() // 初始化ByteTIM SDK（需要放置在session_lib.Init后）

    engine := ginex.Default()
    ...
    engine.Use(session_lib.SessionProcessor.ProcessRequest) // 引入session中间件（C端用户才需要，在 ByteTIM 中间件之前）
    engine.Use(timginex.ByteTIMGinexMW()) // 引入 ByteTIM 提供的中间件
    ...
}
```

**关键点**：
- 上述中间件会根据业务方注册时所填的用户类型以及设备类型，生成相应的流量身份标识
- 业务方再通过`ginex.CacheRPCContext`或`ginex.RPCContext`生成 rpcCtx 发起 RPC 调用，即可实现流量身份标识的透传
- 当业务方注册时的用户类型为 C 端用户，需先初始化 Session Lib/TikTok Session Lib，再初始化 ByteTIM SDK，且 ByteTIM 中间件需要放置在 Session 中间件后面

## Hertz v1.x 框架集成

若业务方服务是基于 Hertz v1 版本框架开发的，ByteTIM 提供了易用的中间件，参考以下示例代码接入：

```go
import (
     "code.byted.org/bytetim/client-go/generator/timhertz"
     "code.byted.org/middleware/hertz/byted"
     "code.byted.org/middleware/hertz/byted/config/local"
     // Tiktok 业务请使用 session_lib code.byted.org/tiktok/tiktok_session_lib
     "code.byted.org/passport/session_lib"
)

func main() {
    byted.Init()
    conf := session_lib.SessionClientConfig{Caller: local.PSM()}
    session_lib.Init(conf) // 初始化session SDK（C端用户才需要，否则不需要引入）
    timhertz.MustInit() // 初始化ByteTIM SDK（需要放置在session_lib.Init后）

    r := byted.Default()
    ...
    r.Use(session_lib.HertzSessionProcessor.ProcessRequest) // 引入 session 中间件（C端用户才需要引入，在 ByteTIM 中间件之前）
    r.Use(timhertz.ByteTIMHertzMW()) // 引入ByteTIM 提供的中间件
    ...
}
```

**关键点**：
- 上述中间件会根据业务方注册时所填的用户类型以及设备类型，解析请求获取信息并生成相应的流量身份标识
- 业务方使用 handler func 中的 ctx 发起 RPC 调用，即可实现流量身份标识的透传
- 当业务方注册时的用户类型为 C 端用户，需先初始化 Session Lib/TikTok Session Lib，再初始化 ByteTIM SDK，且 ByteTIM 中间件需要放置在 Session 中间件后面

## Hertz v0.x 框架集成

若业务方服务是基于 Hertz v0 版本框架开发的，ByteTIM 提供易用的中间件，参考以下示例代码接入：

```go
import (
     "code.byted.org/bytetim/client-go/generator/timhertzv0"
     "code.byted.org/middleware/hertz"
     "code.byted.org/middleware/hertz/app"
     // Tiktok 业务请使用 session_lib code.byted.org/tiktok/tiktok_session_lib
     "code.byted.org/passport/session_lib"
     "code.byted.org/middleware/hertz/config/local"
)

func main() {
    hertz.Init()
    conf := session_lib.SessionClientConfig{Caller: local.PSM()}
    session_lib.Init(conf) // 初始化session SDK（C端用户才需要，否则不需要引入）
    timhertzv0.MustInit() // 初始化ByteTIM SDK（需要放置在session_lib.Init后）

    r := app.Default()
    ...
}
```

## 开启 Auth Level 和 Session App ID 字段

从 ByteTIM v1.2.28 Go SDK 开始支持在 C 端场景注入 Auth Level 和 Session App ID 字段，需要通过初始化 SDK 时指定初始化配置来开启。

### Ginex 框架开启示例

```go
import (
    "code.byted.org/gin/ginex"
    "code.byted.org/passport/session_lib"
    "code.byted.org/bytetim/client-go/generator/timginex"
)

func main() {
    ginex.Init()
    // 1. 初始化 Session lib
    conf := session_lib.SessionClientConfig{Caller: ginex.PSM()}
    session_lib.Init(conf)
    
    // 2. 初始化 ByteTIM SDK，传入启用字段 Option
    opts := []timginex.InitOption{
        timginex.WithEnableAuthLevel(),
        timginex.WithEnableSessionAppID()
    }
    timginex.MustInit(opts...)

    engine := ginex.Default()
    // 3. 引入中间件，注意需要 Session lib 中间件需要在 ByteTIM 中间件之前
    engine.Use(session_lib.SessionProcessor.ProcessRequest)
    engine.Use(timginex.ByteTIMGinexMW())
    ...
}
```

### Hertz v1.x 框架开启示例

```go
import (
     "code.byted.org/bytetim/client-go/generator/timhertz"
     "code.byted.org/middleware/hertz/byted"
     "code.byted.org/middleware/hertz/byted/config/local"
     "code.byted.org/passport/session_lib"
)

func main() {
    byted.Init()
    // 1. 初始化 Session lib
    conf := session_lib.SessionClientConfig{Caller: local.PSM()}
    session_lib.Init(conf)
    
    // 2. 初始化 ByteTIM SDK，传入启用字段 Option
    opts := []timhertz.InitOption{
        timhertz.WithEnableAuthLevel(),
        timhertz.WithEnableSessionAppID()
    }
    timhertz.MustInit(opts...)

    r := byted.Default()
    // 3. 引入中间件，注意需要 Session lib 中间件需要在 ByteTIM 中间件之前
    r.Use(session_lib.SessionProcessor.ProcessRequest)
    r.Use(timhertz.ByteTIMHertzMW())
    ...
}
```

## 注意事项

1. **版本要求**：开启 Auth Level 和 Session App ID 字段需要 ByteTIM SDK 版本 >= v1.2.28
2. **中间件顺序**：Session lib 中间件需要在 ByteTIM 中间件之前引入
3. **适用场景**：Auth Level 和 Session App ID 字段仅适用于 C 端场景（基于 Passport Session 进行登录态管理），非 C 端场景不需要（例如内部管理系统等）
4. **依赖管理**：需要正确导入对应的 SDK 包，如 `code.byted.org/bytetim/client-go/generator/timginex`、`code.byted.org/bytetim/client-go/generator/timhertz` 等

## 相关文档

- [ByteTIM 开启注入 Auth Level 和 Session App ID 字段指引](https://bytedance.larkoffice.com/wiki/QPl2wz08SiOklMkxDHScYEgOnQh)
- [票据生成方接入（Golang SDK 方式）](https://bytedance.larkoffice.com/wiki/wikcn9MXpdCz2YNJjqJtDD5rTKb)