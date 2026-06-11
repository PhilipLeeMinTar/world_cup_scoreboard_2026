# ByteTIM KiteX 框架集成指南

ByteTIM 为 KiteX 框架提供了专门的中间件支持，帮助业务方在 RPC 服务中实现流量身份标识的生成和透传。

## 角色判断

在接入前需要明确服务的角色：
1. **KiteX 服务端**：若业务方服务是一个 RPC 服务端，承接 RPC 请求流量，则接入 KiteX 服务端中间件
2. **KiteX 客户端**：若业务方服务不承接 RPC 请求流量（例如脚本服务或者消息队列消费者服务等），则接入 KiteX 客户端中间件

## KiteX 客户端接入

### 基础接入方式

```go
import (
    "code.byted.org/kite/kitex/client"
    "code.byted.org/bytetim/client-go/generator/timkitex"
)

func main() {
    timkitex.MustInit() // 必须初始化 SDK
    ...
}

func InitRpcDemo(){
    // 1. client.WithMiddleware 方式
    clientx, err = demoservice.NewClient("ies.demo.kiteX", client.WithMiddleware(timkitex.ByteTIMKiteXMW))
    
    // 2. client.WithInstanceMW 方式
    clientx, err = demoservice.NewClient("ies.demo.kiteX", client.WithInstanceMW(timkitex.ByteTIMKiteXMW))
    ...
}
```

`client.WithMiddleware` 和 `client.WithInstanceMW` 的区别参见[扩展 KiteX](https://bytedance.feishu.cn/wiki/wikcnxc1YMnrLXi3p99NU5q3TLh#eE0BlN)。

### Overpass 通用业务线客户端接入

```go
import (
    "code.byted.org/bytetim/client-go/generator/timkitex"
    "code.byted.org/overpass/ies_demo_kitex/rpc/ies_demo_kitex"
    "code.byted.org/overpass/common/option/clientoption"
)

func InitRpcDemo(){
    timkitex.MustInit() // 必须初始化ByteTIM SDK
    ...
    // 设置RPC客户端的Option
    ies_demo_kitex.InitDefaultClientOptions(clientoption.WithMiddleware(timkitex.ByteTIMKiteXMW))
}
```

### Overpass TikCast 业务线客户端接入

```go
import (
    "code.byted.org/bytetim/client-go/generator/timkitex"
    "code.byted.org/overpass/common/option/clientoption"  
    "code.byted.org/kite/kitex/client"
    "code.byted.org/tikcast/rpc_tikcast_user_base/tikcast_user_base"
)

var ByteTim_tikcast_user_base *tikcast_user_base.CustomCallStruct 

func InitRpcDemo(){
    timkitex.MustInit() // 必须初始化ByteTIM SDK
    ...
    // 引入 ByteTIM 中间件
    ByteTim_tikcast_user_base = tikcast_user_base.MustInitCustomClient(
        "tikcast.user.base", 
        clientoption.WithRawOptions(client.WithMiddleware(timkitex.ByteTIMKiteXMW))
    )
}
```

## KiteX 服务端接入

```go
import (
    "code.byted.org/kite/kitex/server"
    "code.byted.org/bytetim/client-go/generator/timkitex"
)

func main() {
    timkitex.MustInit() // 必须初始化 SDK
    svr := demoservice.NewServer(new(DemoServiceImpl), server.WithMiddleware(timkitex.ByteTIMKiteXMW))
    if err := svr.Run(); err != nil {
        ...
        return
    }
}
```

## 自定义参数处理

当需要透传自定义参数时，可以通过以下方式修改票据：

```go
import (
    "code.byted.org/bytetim/client-go/generator/timkitex"
    "code.byted.org/bytetim/client-go/timpkg"
)

func handler(ctx context.Context, req interface{}) (resp interface{}, err error) {
    t, err := timkitex.GetOrCreateTicket(ctx) // 获取或创建票据
    if err != nil {
        ...
        return
    }

    opts := []timpkg.AlterTicketOption{
        // 自定义参数需要在管理平台申请
        timpkg.WithExtra(map[string]string{"BYTETIM_BUSINESS_XX": "XXXX"}),
    }

    if err = t.SetWithOption(ctx, opts...); err != nil {
        ...
        return
    }

    ctx = t.InjectTicket(ctx) // 重新注入票据到上下文
    // 使用新的 ctx 进行 RPC 调用
    ...
}
```

## 验证接入是否成功

### SDK 版本 >= 1.2.18
- **指标名称**：`iesarch.bytetim.client.generate_ticket.v2`
- **指标类型**：Rate Counter
- **关键标签**：
  - `result: success`
  - `ticket_type: bytetim`
  - `parse_uid_succ: *`（true 表示能解析到用户标识）
  - `end_psm: ${YOUR_SERVICE_NAME}`

### SDK 版本 < 1.2.18
- **指标名称**：`iesarch.bytetim.client.generate_ticket`
- **指标类型**：Counter
- **关键标签**：同上

## 注意事项

1. **自定义参数申请**：所有自定义参数需要在 ByteTIM 管理平台申请后才能使用
2. **中间件顺序**：如果同时使用 Session 中间件，ByteTIM 中间件需要放置在 Session 中间件之后
3. **非中国区 MQ Consumer**：需要通过 PnS 隐私安全团队封装的 SDK 接入，会额外注入敏感数据治理信息
4. **脚本服务**：对于 consumer 或 Cronjob 等脚本服务，如果基于 RPC 调用请求下游，参照 KiteX 客户端接入方式即可

