# ByteTIM SDK 使用指南

本文档提供 ByteTIM SDK 在 Golang 服务中的详细使用指导，涵盖票据生成方和票据校验方的接入方式、框架集成、自定义参数配置等核心功能。

## 接入前准备

在接入 ByteTIM SDK 前，需要明确以下关键信息：

### 1. 服务角色判断
- **票据生成方**：负责生成票据，一般为微服务架构请求链路中的起始节点，如面向 C 端用户或字节员工流量的 HTTP 服务、脚本服务、定时服务等
- **票据校验方**：仅负责校验票据，一般为请求链路的底层服务
- **混合角色**：若节点同时存在票据生成以及票据校验的诉求，按票据生成方角色进行注册

### 2. 版本兼容性配置
- **只支持新版本**：对于票据生成方表示仅生成新版本票据，对于票据校验方表示仅校验新版本票据
- **同时支持新旧版本**：对于票据生成方表示同时生成新旧版本票据，对于票据校验方表示同时支持校验新旧版

### 3. 用户类型配置（仅票据生成方需要）
- **C 端用户**：基于 Passport Session 管理用户登录态的服务
- **SSO 登录用户**：基于 ByteDance SSO 管理用户登录态的内部系统
- **混合登录态**：存在多种用户登录态管理方式的服务
- **普通内部服务**：一般的脚本服务或者 MQ 消费者等

### 4. 设备类型配置（仅票据生成方需要）
- **常规终端设备**：一般情况下的场景，如安卓和 IOS 客户端等
- **ToB 设备**：用于提供给不同 B 端分组标识一台设备的类型
- **Web 设备**：用于实现 PC 站推荐/统计、Web 回流页统计等场景

## 管理平台注册

在接入 SDK 前，必须登录 ByteTIM 管理平台完成服务注册：

### 平台访问地址
- **BOE 区域**：https://cloud-boe.bytedance.net/bytetim/service/list
- **China-North/China-East 区域**：https://cloud.bytedance.net/bytetim/service/list
- **US-East 区域**：https://cloud-i18n.bytedance.net/bytetim/service/list?region=US
- **Singapore-Central 区域**：https://cloud-i18n.bytedance.net/bytetim/service/list?region=SG

### 注册流程
1. 搜索对应 PSM 是否已注册
2. 若未注册，通过「接入服务」入口完成服务注册
3. 若已注册，核对注册信息，有误可通过「编辑」入口修正

![管理平台服务列表](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/425d65539c9044a0b5ede7edd49527e0~tplv-tika-image.image)

## 票据生成方接入

### Ginex 框架接入

**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/generator/timginex
```

**基础接入代码**：
```go
import (
    "code.byted.org/gin/ginex"
    "code.byted.org/passport/session_lib"
    "code.byted.org/bytetim/client-go/generator/timginex"
)

func main() {
    ginex.Init()
    conf := session_lib.SessionClientConfig{Caller: ginex.PSM()}
    session_lib.Init(conf) // C端用户需要，否则不需要
    timginex.MustInit() // 必须初始化ByteTIM SDK
    
    engine := ginex.Default()
    engine.Use(session_lib.SessionProcessor.ProcessRequest) // C端用户需要
    engine.Use(timginex.ByteTIMGinexMW()) // 引入ByteTIM中间件
}
```

**自定义参数配置**：
```go
import (
    "code.byted.org/bytetim/client-go/generator/timginex"
    "code.byted.org/bytetim/client-go/timpkg"
)

func handlerFunc(c *gin.Context) {
    t, err := timginex.GetOrCreateTicketWithGinCtx(c)
    if err != nil {
        return
    }
    
    opts := []timpkg.AlterTicketOption{
        timpkg.WithExtra(map[string]string{"BYTETIM_BUSINESS_XX": "XXXX"}),
    }
    
    if err = t.SetWithOption(ginex.CacheRPCContext(c), opts...); err != nil {
        return
    }
    
    t.InjectTicketWithGinCtx(c)
}
```

### Hertz 框架接入

#### Hertz V0 版本
**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/generator/timhertzv0 (>= v1.2.9)
```

**基础接入代码**：
```go
import (
    "code.byted.org/bytetim/client-go/generator/timhertzv0"
    "code.byted.org/middleware/hertz"
    "code.byted.org/middleware/hertz/app"
    "code.byted.org/passport/session_lib"
)

func main() {
    hertz.Init()
    conf := session_lib.SessionClientConfig{Caller: local.PSM()}
    session_lib.Init(conf)
    timhertzv0.MustInit()
    
    r := app.Default()
    r.Use(session_lib.HertzSessionProcessor.ProcessRequest)
    r.Use(timhertzv0.ByteTIMHertzMW())
}
```

#### Hertz V1 版本
**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/generator/timhertz
```

**基础接入代码**：
```go
import (
    "code.byted.org/bytetim/client-go/generator/timhertz"
    "code.byted.org/middleware/hertz/byted"
    "code.byted.org/passport/session_lib"
)

func main() {
    byted.Init()
    conf := session_lib.SessionClientConfig{Caller: local.PSM()}
    session_lib.Init(conf)
    timhertz.MustInit()
    
    r := byted.Default()
    r.Use(session_lib.HertzSessionProcessor.ProcessRequest)
    r.Use(timhertz.ByteTIMHertzMW())
}
```

### Kite 框架接入

**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/generator/timkite
```

**客户端中间件**：
```go
import "code.byted.org/bytetim/client-go/generator/timkite"

func main() {
    timkite.MustInit()
    timkite.InitByteTIMKiteMW()
}
```

**服务端中间件**：
```go
import (
    "code.byted.org/bytetim/client-go/generator/timkite"
    "code.byted.org/kite/kite"
)

func main() {
    kite.Init()
    timkite.MustInit()
    kite.Use(timkite.NewByteTIMKiteMW())
}
```

### KiteX 框架接入

**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/generator/timkitex
```

**客户端中间件**：
```go
import (
    "code.byted.org/kite/kitex/client"
    "code.byted.org/bytetim/client-go/generator/timkitex"
)

func main() {
    timkitex.MustInit()
    
    // 方式1：client.WithMiddleware
    clientx, err = demoservice.NewClient("ies.demo.kiteX", 
        client.WithMiddleware(timkitex.ByteTIMKiteXMW))
    
    // 方式2：client.WithInstanceMW
    clientx, err = demoservice.NewClient("ies.demo.kiteX", 
        client.WithInstanceMW(timkitex.ByteTIMKiteXMW))
}
```

**服务端中间件**：
```go
import (
    "code.byted.org/kite/kitex/server"
    "code.byted.org/bytetim/client-go/generator/timkitex"
)

func main() {
    timkitex.MustInit()
    svr := demoservice.NewServer(new(DemoServiceImpl), 
        server.WithMiddleware(timkitex.ByteTIMKiteXMW))
}
```

### GDP 框架接入

**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/generator/timgdp
```

**基础接入代码**：
```go
import (
    "code.byted.org/bytetim/client-go/generator/timgdp"
    "code.byted.org/gdp/plugin/session"
    "code.byted.org/gdp/compkg/af/plugin"
)

func main() {
    app.Init()
    
    psuite := plugin.APISuite()
    // C端场景需要引入session中间件
    err := psuite.Register(newSessionPlugin())
    if err != nil {
        panic(err)
    }
    // 引入ByteTIM中间件
    err = psuite.Register(timgdp.NewByteTIMAfPlugin())
    if err != nil {
        panic(err)
    }
}
```

## 票据校验方接入

### 基础接入

**依赖引入**：
```bash
go get code.byted.org/bytetim/client-go/verifier/timticket
```

**初始化代码**：
```go
import (
    "code.byted.org/bytetim/client-go/verifier/timticket"
    "code.byted.org/bytetim/client-go/timpkg"
)

func main() {
    timticket.MustInit() // 初始化失败会panic
}

func handler(ctx context.Context) {
    ticket, err := timticket.GetTicket(ctx)
    if err == timpkg.ErrTicketNotExist {
        // 票据不存在处理
    }
}
```

## SDK 升级指引

### 包名路径变动
从依赖拆分之前的 SDK（< v1.2.1）升级到依赖拆分后的 SDK（>= v1.2.1）时，包名路径发生以下变动：

| 框架类型 | 旧包路径 | 新包路径 |
|---------|---------|---------|
| Ginex | `code.byted.org/bytetim/client-go/generator` | `code.byted.org/bytetim/client-go/generator/timginex` |
| Hertz v0 | `code.byted.org/bytetim/client-go/generator` | `code.byted.org/bytetim/client-go/generator/timhertzv0` |
| Hertz v1 | `code.byted.org/bytetim/client-go/generator` | `code.byted.org/bytetim/client-go/generator/timhertz` |
| Kite | `code.byted.org/bytetim/client-go/generator` | `code.byted.org/bytetim/client-go/generator/timkite` |
| KiteX | `code.byted.org/bytetim/client-go/generator` | `code.byted.org/bytetim/client-go/generator/timkitex` |
| GDP | `code.byted.org/bytetim/client-go/generator` | `code.byted.org/bytetim/client-go/generator/timgdp` |
| 票据校验 | `code.byted.org/bytetim/client-go/verifier` | `code.byted.org/bytetim/client-go/verifier/timticket` |
| 通用包 | `code.byted.org/bytetim/client-go/tim` | `code.byted.org/bytetim/client-go/timpkg` |

### 代码迁移示例
```go
// 升级前
import "code.byted.org/bytetim/client-go/generator"
generator.MustInit()
r.Use(generator.ByteTIMGinexMW())

// 升级后
import "code.byted.org/bytetim/client-go/generator/timginex"
timginex.MustInit()
r.Use(timginex.ByteTIMGinexMW())
```

## 验证接入是否成功

### 监控指标
- **SDK 版本 >= 1.2.18**：查询指标 `iesarch.bytetim.client.generate_ticket.v2`
- **SDK 版本 < 1.2.18**：查询指标 `iesarch.bytetim.client.generate_ticket`

### 关键标签
- `result: success`
- `ticket_type: bytetim`
- `parse_uid_succ: *`（true表示能解析到用户标识）
- `end_psm: ${YOUR_SERVICE_NAME}`

## 注意事项

1. **C端用户接入**：需先初始化 Session Lib/TikTok Session Lib，再初始化 ByteTIM SDK，且 ByteTIM 中间件需要放置在 Session 中间件后面
2. **SSO登录用户**：接入 SDK 前需要去管理平台完成 SSO 相关配置
3. **自定义参数**：需要在管理平台申请后才能使用
4. **非中国区 MQ Consumer**：需通过 PnS 隐私安全团队封装的 SDK 接入
5. **脚本服务**：如果基于 RPC 调用请求下游，可基于 Kite/KiteX 框架（客户端）接入

## 参考文档
- [ByteTIM 快速接入](https://bytedance.larkoffice.com/wiki/VkuYwZdr6ihDj2kf3AycAsDRn5b)
- [票据生成方接入（Golang SDK 方式）](https://bytedance.larkoffice.com/wiki/wikcnr3QfaFOGLkX3PniSceoDBg)
- [ByteTIM SDK 升级指引](https://bytedance.larkoffice.com/wiki/wikcnEpALQ2vwvYPxtE3KD0xRNc)

