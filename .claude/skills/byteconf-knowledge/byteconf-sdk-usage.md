# ByteConf SDK 使用指南

## 概述

ByteConf SDK 是字节跳动内部配置管理平台的服务端 SDK，提供配置的动态下发、实时更新和条件规则管理能力。SDK 基于 CDS 做配置分发，采用 gRPC 长链接 push 机制，实现秒级生效的配置更新。

## 核心概念

### 关键术语
- **配置**：指单个配置项，命名规则为 `^[0-9a-z_.]+$`，例如：`test`
- **目录/Path**：配置的路径，支持两级路径，平台显示为 `biz_tree_path`，例如：`/A/B/`
- **bcKey**：目录+配置名，唯一定义一个 namespace 下的配置，例如：`/A/B/test`
- **监听**：SDK 内部建立长连接实时获取配置变更，相关接口不对外暴露
- **回调**：业务方定义的 callback 逻辑，用于实时获取配置/目录更新，触发事件

### 新旧 SDK 对比
新版 SDK 主要解决了老版 SDK 的几个问题：
1. 协程数过大（从 7800+ 减少到 ~70）
2. 内存消耗大（从 500M+ 减少到 230M）
3. 配置下线和删除难
4. 监听目录时初始化耗时大（从 >60s 减少到 ~1.5s）
5. 配置发布慢、回滚慢
6. 稳定性有所提升

## SDK 初始化

### Client 对象
Client 作为配置/目录的操作对象，初始化包括参数 + clientOption。不支持重复监听，否则会报错。

**三个对外开放的 client 接口：**
- `NewClient`：单个配置 Key 的操作对象
- `NewClientByKeys`：多个配置 Key 的操作配置
- `NewClientByPath`：监听某个目录/path 的操作对象，前缀匹配

### 初始化参数
- `serviceName`：标识当前服务对象，业务自定义，例如："byteconf_service"
- `namespace`：ByteConf 的命名空间，例如："toutiao.stream.stream.V2"
- `bcKey`：目录+配置名构成的唯一 Key，例如："/A/B/test"
- `bizPath`：ByteConf 的 path

### ClientOption 可选项
- `WithClientKeyCallback`：非必须，配置对象的回调，当配置变更时调用该 callback
- `WithClientPathCallback`：非必须，目录对象的回调，当目录下有配置变更时调用该 callback
- `WithClientInitTimeout`：非必须，初始化拉取配置的超时时间，默认阻塞直到拉取成功
- `WithClientDisableListen`：非必须，初次拉取完最新配置后，是否关闭后端的监听长连接
- `WithClientWatchEmpty`：非必须，是否支持监听不存在的配置，默认关闭
- `WithClientModelMap`：非必须，反序列化配置的 model。schemaName -> model

## 监听模式

### 单配置监听
```go
client, err := byteconf.NewClientByKeys(meta.ServiceName, meta.Namespace, meta.Keys,
   byteconf.WithClientKeyCallback(confCallback))
```

### 目录监听
目录监听会获取目录下所有的 key，默认是前缀匹配，并且程序运行中增加的 key 也能获取到：
```go
// 默认生成 client 的时候，后端已经挂了一条监听长连接
client, err := byteconf.NewClientByPath(meta.ServiceName, meta.Namespace, meta.BizPath,
   byteconf.WithClientPathCallback(pathCallback))
```

## 监听机制
ByteConf SDK 底层利用 CDS-SDK 实现配置监听：
- gRPC 长链接，多路复用
- 配置变更 push 机制，线上和 BOE 环境秒级下发
- CDS 容灾

## 重要注意事项

### 新手必看
1. **多个可枚举的 bcKey 请业务 const 全局定义**，避免每次调用时拼接出错
2. **不能对同一个 key 重复监听**。最好一个程序只 New 一个 byteconf Client。如果确实需要多次 new，确保没有重复监听 key
3. **NewClient 的调用最好放到程序初始化时**，并且当 NewClient 返回错误时，panic 程序
4. **Mac Book 使用 SDK**，需要设置环境变量 `RUNTIME_IDC_NAME=boe`
5. **目录监听默认不允许重复监听**，并且是递归监听
6. **不允许在回调函数里面 NewClient**。该操作会造成死锁

## 配置获取接口

### GetBytes
获取配置未序列化的原始内容，业务方拿到后根据需要自行反序列化。

### GetModel
获取配置反序列化后的数据内容，业务方拿到后用 model 断言。

**示例代码：**
```go
import (
    "fmt"
    byteconf "code.byted.org/ttarch/byteconf_sdk"
)

func fooKey() {
    service_name := "service_name"
    namespace := "toutiao.byteconf.lwq"
    bcKey := "/dmt/douyin/score"

    client, err := byteconf.NewClient(service_name, namespace, bcKey)
    if err != nil {
        fmt.Printf("fail to new Client. err: %v\n", err)
        return
    }

    // 获取字节流形式的配置内容
    if data, err := client.GetBytes(bcKey); err == nil {
        fmt.Printf("data: %s\n", string(data))
    } else {
        fmt.Printf("fail to GetBytes. err: %v\n", err)
    }

    type BizConfModel struct {
        Name  string `json:"name"`
        Score int    `json:"score"`
    }

    // 如果是 json 动态配置，需要 WithConfScope 这个 option
    scope := map[string]interface{}{"did": 120}
    options := []byteconf.ConfOption{byteconf.WithConfModel(BizConfModel{}), byteconf.WithConfScope(scope)}
    if val, err := client.GetModel(bcKey, options...); err == nil {
        fmt.Printf("data: %+v\n", val.(*BizConfModel))
    } else {
        fmt.Printf("fail to GetModel. err: %v\n", err)
    }
}
```

## 回调机制

### KeyCallback
定义：`func(client *Client, bcKey string) error`

```go
cb := func(client *byteconf.Client, bcKey string) error {
    if val, err := client.GetBytes(bcKey); err == nil {
        fmt.Printf("data: %s\n", string(val))
    } else {
        fmt.Printf("fail to GetModel. err: %v\n", err)
    }
    return nil
}
```

### PathCallback
定义：`func(client *Client, bcKey string, action PathAction) error`

PathAction 目前有两个动作含义：
- `PathAddOrUpdate`：新增配置或者更新配置时回调
- `PathDelete`：删除配置

```go
cb := func(client *byteconf.Client, bcKey string, action byteconf.PathAction) error {
    if action == byteconf.PathAddOrUpdate {
        if data, err := client.GetBytes(bcKey); err != nil {
            fmt.Printf("fail to get bcKey[%s] data. err: %+v\n", bcKey, err)
        } else {
            fmt.Printf("data: %s\n", string(data))
        }
    } else if action == byteconf.PathDelete {
        // 删除配置处理逻辑
    }
    return nil
}
```

## 单次接口（FAAS 场景）

### GetConfByOnce
单次获取单个配置的原始内容(bytes)：

```go
func GetKeyOnce() {
    namespace := "toutiao.byteconf.lwq"
    bcKey := "/dmt/douyin/score"
    
    if data, err := byteconf.GetConfByOnce(namespace, bcKey); err != nil { 
        fmt.Printf("fail to new Client. err: %v\n", err)
    } else { 
        fmt.Printf("data: %s\n", string(data))
    }
    
    // 获取 model 形式
    type BizConfModel struct {
        Name  string `json:"name"`
        Score int    `json:"score"`
    }

    if ret, err := byteconf.GetConfModelByOnce(namespace, bcKey, BizConfModel{}); err != nil {
        fmt.Printf("fail to GetConfModelByOnce. Err: %s\n", err.Error())
    } else {
        fmt.Printf("getModelByOnce : %+v\n", ret.(*BizConfModel))
    }
}
```

### GetPathByOnce
单次获取某个目录下所有配置的原始内容(bytes)：

```go
func GetPathOnce() {
    namespace := "toutiao.byteconf.lwq"
    bizPath := "/dmt/douyin/"

    if confs, err := byteconf.GetPathByOnce(namespace, bizPath); err != nil {
        fmt.Printf("fail to new Client. err: %v\n", err)
    } else {
        for bcKey, data := range confs {
            fmt.Printf("%s => data: %s\n", bcKey, string(data))
        }
    }
}
```

## 取消监听

### 取消监听 keys
```go
// 取消对 bcKey2 的监听，也可以传一个之前没有监听的 bcKey
client.CancelWatchKeys([]string{bcKey2, "/other/path"})
```

### 取消监听目录
```go
client.CancelWatchPath(bizPath)
```

## 错误处理

### NewClientError 类型
如果想知道 NewClient/NewClientByPath 返回的具体错误原因，可以尝试转换成 NewClientError 类型：

```go
func fooNewErr() {
    service_name := "service_name"
    namespace := "toutiao.byteconf.lwq"
    bcKey := "/dmt/douyin/score22" // 一个不存在的 key

    if _, err := byteconf.NewClient(service_name, namespace, bcKey); err != nil {
        if newErr, ok := err.(byteconf.NewClientError); ok {
            if newErr.IsNotExist() {
                fmt.Printf("conf: %s not exist\n", bcKey)
            } else {
                panic(fmt.Sprintf("other error: %v", newErr))
            }
        } else {
            panic(fmt.Sprintf("other error: %v", err))
        }
    }
}
```

## 最佳实践

### 场景一：FAAS 场景（只需要启动时拉取一次配置）
适用于只需要获取一次当前配置或者目录下所有配置，例如 FAAS 场景。

### 场景二：实时监听场景
服务启动需要拉取配置，并且后续也需要实时监听配置变更。

**关键代码示例：**
```go
// 单个配置监听
func fetchSingleConf() {
    meta := &MetaInfo{
        ServiceName: "test",
        Namespace:   "wh_test",
        ByteConfKey: "/copy/test3",
    }

    client, err := byteconf.NewClientByKeys(meta.ServiceName, meta.Namespace, []string{meta.ByteConfKey}, byteconf.WithClientKeyCallback(keyCallback))
    if err != nil {
        return
    }

    // 获取 model 数据
    data2, err2 := client.GetModel(myByteconfStaticKey, byteconf.WithConfModel(BizConfModel{}))
    if err2 != nil {
        logs.Errorf("Get conf fail: err[%v]", err2)
        return
    }
    modelData := data2.(*BizConfModel)
    logs.Infof("Get model conf: field_0[%v] field_1[%v]", modelData.Field0, modelData.Field1)
}
```

## 配置下发原理
当 new byteconf SDK 时，SDK 默认会阻塞直到拉取所有配置内容到本地，然后会把下发的配置内容缓存到本地中，然后回调用户传入的回调函数。每次配置变更的下发都是以上的流程。每次调用 SDK 的 get 请求，SDK 都是从内存中获取缓存的配置内容返回给调用方。

## 性能优势
新版 SDK 相比旧版 SDK 在性能上有显著提升：
- **初始化时间**：从 >60s 减少到 ~1.5s
- **内存消耗**：从 500M+ 减少到 230M
- **协程数**：从 7800+ 减少到 ~70

