# RTC 服务端 OpenAPI 使用指南

## 前置条件

在调用 RTC 服务端 OpenAPI 之前，需要完成以下准备工作：

1. **开通 RTC 服务**：在控制台开通 RTC 服务
2. **获取 AK/SK**：注册账号，获取对应的 AK/SK 凭证，相关信息在对应环境的控制台-秘钥管理页面可以看到

## 控制台访问路径

根据不同的业务环境，访问对应的控制台：

- **国内环境**（cn-north-1）：[https://vconsole.bytedance.net/overview/](https://vconsole.bytedance.net/overview/) - 字节内部 TikTok 以外业务使用
- **美东环境**（us-east-1）：[https://vconsole-us.bytedance.net/overview](https://vconsole-us.bytedance.net/overview) - TikTok 专用
- **新加坡环境**（ap-singapore-1）：[https://vconsole-sg.bytedance.net/overview/](https://vconsole-sg.bytedance.net/overview/) - TikTok 专用

> **注意**：字节企业服务，和火山引擎环境中的服务和账号等均不互通

## 账号管理最佳实践

强烈推荐在对应环境下，以主账号权限创建用户（子账号），并使用用户的 AK/SK 发起 OpenAPI 调用。要创建用户，访问控制台-访问控制-用户管理路径。

## BOE 环境接入

如果业务处于调试阶段，部署在 BOE 环境中，推荐接入正式 RTC 环境进行调试。如果由于特殊原因无法使用正式环境，需要联系技术同学协助。

### BOE 环境配置

**客户端接入**：
- 接入和正式环境中相同的 SDK
- 调用私有接口 `SetParameters` 指定接入 BOE 环境下的 RTC 服务
- 通过传入指定的 `rtc.env` 参数指定 RTC 环境，参考[RTC 私有接口汇总](https://bytedance.feishu.cn/sheets/shtcnRwZzqRVQrSZ4VkSK2XAKjH)

**服务端调用**：
- 调用 RTC 提供的 OpenAPI 时，使用 BOE 环境的域名：`staging-openapi-boe.byted.org`

**控制台访问**：
- 访问 BOE 环境下的 [RTC 控制台](https://v-vconsole.bytedance.net/rtc/workplaceRTC)

## 消息通知回调

RTC 服务端支持向业务服务端发送状态消息回调，需要部署 HTTP(s) 服务接收回调。

### 回调处理要求

1. **响应状态码**：接收回调响应的 HTTP 状态码为 `200` 时，RTC 服务端即认为回调成功
2. **失败重试**：状态码不为 `200`，或响应时间超过5秒，都视为回调失败，RTC 服务端会重试，重试最多2次（总计回调不超过3次）
3. **签名验证**：RTC 服务端发起回调时会使用回调密钥对回调签名，业务服务端需要验证签名

### 签名验证示例

以下是使用 GoLang 实现的签名验证算法示例：

```go
type Event struct {
    EventType string `json:"EventType"`
    EventData string `json:"EventData"`
    EventTime string `json:"EventTime"`
    EventID   string `json:"EventId"`
    AppID     string `json:"AppId"`
    Version   string `json:"Version"`
    Noce      string `json:"Noce"`
    Signature string `json:"Signature"`
}

var event Event

data := []string{
    event.EventType,
    event.EventData,
    event.EventTime,
    event.EventID,
    event.AppID,
    event.Version,
    event.Noce,
    // 回调密钥 SecretKey
}
```

## 应用管理

可以通过 OpenAPI 实现应用管理，包括创建应用等操作。

### 创建应用接口

使用 `CreateApp` 接口创建 AppID，效果和在控制台上手动创建一致。

**前提条件**：
- 已在控制台上开通了 RTC 服务
- 完成实名认证
- 确定计费类型

## 转推直播功能

RTC 支持将音视频通话中的多路音视频流合为一路，并将合并得到的音视频流推送到指定的推流地址（通常是 CDN 地址）。

### 调用方式

可以在音视频应用客户端和服务端开始转推直播/更改转推配置：

- **客户端调用**：当音视频房间内的主播希望向更多观众开始/关闭直播时，可以使用 RTC SDK 中的 API 实现转推直播
- **服务端调用**：当应用管理员判定音视频房间中的内容不适合直播时，可以在应用服务端调用 OpenAPI 关闭转推直播

无论在哪里调用，转推直播的过程都在 RTC 服务端实现。

## 音频切片功能

RTC 提供音频切片服务，用于对通话音频进行切片处理。

### 基本流程

1. **配置音频切片规则**
2. **进入房间**，进行通话，通过 API 开启切片服务
3. **退出房间**，通过 API 结束切片服务
4. **接收回调**

### 接入方式

- **前端接入**：使用 ByteRTC SDK 接入，配置切片服务参数，使用 HTTP 接口开启、结束任务
- **服务端配置**：通过[服务端接口](https://doc.bytedance.net/docs/1/6/108333/)设置对应配置，所有配置在 HTTP 接口中也可以指定，优先级高于通用配置

## 认证与 Token 机制

RTC 使用 Token 进行身份认证，确保音视频通话的安全性。

### 认证流程

1. **客户端申请**：客户端向应用服务器申请 Token
2. **生成 Token**：应用服务器基于 streamID 为每个会话生成 Token
3. **下发 Token**：应用服务器将 Token 下发到客户端
4. **发布/订阅**：客户端使用 Token 发布/订阅媒体流
5. **验证 Token**：RTC 服务器验证 Token
6. **接收响应**：应用客户端接收响应

![认证流程](https://p-vcloud.byteimg.com/tos-cn-i-em5hxbkur4/698c738d873447299aa2930549bc49aa~tplv-em5hxbkur4-noop.image?width=686&height=358)

## 注意事项

1. **环境隔离**：不同环境的服务和账号不互通，需要分别配置
2. **回调处理**：确保回调服务稳定可靠，避免因回调失败导致业务异常
3. **权限管理**：使用子账号进行 API 调用，提高安全性
4. **测试环境**：BOE 环境主要用于调试，正式上线应使用正式环境

## 参考文档

- [RTC 控制台](https://vconsole.bytedance.net/overview/)
- [RTC 私有接口汇总](https://bytedance.feishu.cn/sheets/shtcnRwZzqRVQrSZ4VkSK2XAKjH)
- [服务端接口文档](https://doc.bytedance.net/docs/1/6/108333/)
- [客户端转推直播文档](https://bytedance.feishu.cn/docs/doccnLNSkqSH0nDYV3PvKfTLINb#)