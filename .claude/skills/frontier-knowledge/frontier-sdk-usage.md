# Frontier SDK 使用指南

## 安装与配置

### 前提条件
- Go 版本要求 ≥ 1.17
- 需要实现 `FrontierCallback` 接口来处理上行消息

### 安装步骤
1. **下载SDK包到代码仓库**
   ```bash
   go get code.byted.org/frontier/server-sdk-go
   go mod tidy
   ```

2. **代码文件引入SDK**
   ```go
   package main
   
   import (
       "code.byted.org/frontier/server-sdk-go"
   )
   ```

## 接口实现

### FrontierCallback 接口
服务端接收上行消息需要实现以下接口：
```thrift
type FrontierCallback interface {
    SendMessageResponse  SendMessage(1: SendMessageRequest req)
    PullMessagesResponse PullMessages(1: PullMessagesRequest req)
    SendEventResponse    SendEvent(1: SendEventRequest req)
    AuthResponse         Auth(1: AuthRequest req)
    ACKMessageResponse   ACKMessage(1: ACKMessageRequest req)
    oneway void Upstream(1: SendMessageRequest req)
}
```

### 接口说明

#### 上行消息接收接口
- **SendMessage**：接收Frontier发送的上行消息
- **Auth**：实现鉴权逻辑（只在 App 开启自定义鉴权时需要）
- **SendEvent**：发送事件消息（建连/断连/心跳）。消息聚合周期20ms或100事件
- **ACKMessage**：通知下行消息下发结果（需在路由配置中开启了"消息回执"）
- **PullMessages** ⚠️ 即将废弃：保持空实现
- **Upstream** ⚠️ 即将废弃：保持空实现

#### 下行消息推送接口
- **Push** / **PushAsync**：向单个App的多设备推送单条消息。跨App推送请用PushV2

## 异步接口说明
异步接口（"Async"后缀）统一说明如下：
- **处理模式**：推送请求加入推送队列后即返回，等推送完成后，通过callback函数通知调用方继续后续处理
- **超时处理**：SDK内部未设置超时处理机制，需要调用方自行处理

## 组管理接口

### GroupControlAsync
GroupControl的异步接口在推送请求被加入推送队列后即刻返回，待推送完成，将通过回调函数通知调用方进行后续处理。

**请求参数**：
- `ctx`：context.Context，用于传递一些公用信息，如logid
- `req`：*GroupControlRequest，组管理请求
- `callback`：func(*GroupControlResponse, error)，回调函数
- `callopt`：...Option，kitex接口调用可选参数

**数据结构**：
```go
type GroupControlRequest struct {
    ProductID        int32
    AppID            int32
    Group            string
    // 单次请求最多加100个设备
    Devices          []*Device
    // 0: 创建组 1: 加组 2: 退组 3: 解散组 4: 查询组信息 5: 替换组
    Code             GroupCtlCode
    WithDeviceList   bool
    Method           int32
    Service          int32
    // 1: ServiceID必须不等于0， 2: Method必须不等于0
    Scope            GroupScope
    Groups           []string
    Base             *base.Base
}
```

## 条件推送支持

### SDK 使用建议
强烈推荐使用 Frontier 提供的 [Go SDK](https://code.byted.org/frontier/server-sdk-go/blob/master/pkg/filter/builder.go?ref_type=heads) 来构建匹配条件的表达式。

**SDK优势**：
- 内部封装了 `device_platform` 的枚举值、`client_version` 的转换规则等细节
- 限制了传参的类型和约束，有效避免拼装出不合法的条件
- 关于 SDK 的集成方式，请参考文档：[Frontier Server GO SDK集成](https://bytedance.larkoffice.com/wiki/JuGqwTXEpiNFNRk4VzCckzE2nrd)

### 错误码示意
条件推送相关的错误码主要有两个：
- `INVALID_CONN_FILTER (8000)`：表示您提供的过滤表达式存在语法错误，导致解析失败
- `CONN_FILTERED (8001)`：表示连接因为不满足匹配条件而被成功过滤，未进行推送

```go
INVALID_CONN_FILTER      = 8000 // 过滤表达式有问题
CONN_FILTERED            = 8001 // 条件过滤
```

## 平台配置要求

### 创建长连接实例
在开始使用SDK前，需要先在Frontier平台创建长连接实例。

**动态加速配置**：
- 公司安全要求外网域名默认接入动态加速
- 请求流量通过动态加速智能回源到当前解析生效的 Frontier 集群

**配置项说明**：
- **中心直连**：外网域名是否直接连接到该 Frontier 集群。如果使用 QUIC 协议接入，请开启中心直连
- **边缘 IP 白名单**：是否启用边缘 IP 白名单。边缘 IP 白名单有专门的 CDN 资源池，能满足对出网安全要求较高的业务需求
- **客户端 IPv4/IPv6/双栈**：是否开启 IPv6。由于合规要求，建议开启 IPv6 开关
- **Websocket**：默认打开，使用 QUIC 协议接入时需要关闭

## 接入流程概述

### 平台配置步骤
1. **创建 Frontier 实例**：[创建长连接实例](https://bytedance.larkoffice.com/wiki/H5Ycwj3bRiB3yskkZuUciMn0nmd?from=from_lark_index_search&ccm_open_type=from_lark_index_search)
2. **配置路由规则**：[创建长连接实例](https://bytedance.larkoffice.com/wiki/H5Ycwj3bRiB3yskkZuUciMn0nmd?from=from_lark_index_search&ccm_open_type=from_lark_index_search)、[配置消息代理路由](https://bytedance.larkoffice.com/wiki/QmOSw5nlbiP0hSkZVUvcY8eEnQf?from=from_parent_docx)

### 客户端接入架构
通过 TTNet SDK（移动端）/Frontier Web SDK/Client GO SDK（PC 端）接入

![Frontier接入架构](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/ff13828daf0e4d559a65f1350036a80d~tplv-goo7wpa0wc-image.image)

## 最佳实践建议

1. **版本兼容性**：确保Go版本符合要求（≥1.17）
2. **错误处理**：合理处理异步接口的回调错误
3. **条件推送**：使用SDK提供的builder构建过滤条件，避免手动拼装
4. **性能优化**：根据业务场景选择合适的推送接口（单推、批量推、组播等）
5. **监控告警**：监控消息推送成功率、延迟等关键指标

## 相关文档链接
- [Frontier Server GO SDK集成](https://bytedance.larkoffice.com/wiki/JuGqwTXEpiNFNRk4VzCckzE2nrd)
- [创建长连接实例](https://bytedance.larkoffice.com/wiki/H5Ycwj3bRiB3yskkZuUciMn0nmd?from=from_lark_index_search&ccm_open_type=from_lark_index_search)
- [配置消息代理路由](https://bytedance.larkoffice.com/wiki/QmOSw5nlbiP0hSkZVUvcY8eEnQf?from=from_parent_docx)
- [配置消息网关路由](https://bytedance.larkoffice.com/wiki/QVJQwJ2asiJt5Ske30ncJtkenrg)
- [条件推送文档](https://bytedance.larkoffice.com/wiki/WWfKwOYyuiQbZRkwKPTcuqB2nrc)
