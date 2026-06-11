# Hertz 框架概览

## 什么是 Hertz?

Hertz 是字节跳动内部自研的一款高性能 Golang HTTP 框架,具备以下特点:

- **高性能**: 基于高性能网络库 Netpoll,提供卓越的吞吐量和低延迟
- **易用性**: API 层面与 Ginex 保持高度一致,降低学习成本
- **可扩展**: 提供丰富的扩展接口和中间件生态
- **内外统一**: 在 GitHub 开源,内外部版本统一维护
- **完善的工具链**: 提供 Hertztool 代码生成工具,支持 IDL 驱动开发

## 核心概念

### HTTP 框架

Hertz 是一个专门用于 HTTP 服务开发的框架,提供:
- RESTful API 开发能力
- 路由管理和参数绑定
- 中间件机制
- 文件上传下载
- 流式处理

### 代码生成

Hertz 通过 Hertztool 工具从 IDL (Thrift/Protobuf) 自动生成:
- 数据结构的 Go 代码
- HTTP Handler 框架代码
- 路由注册代码
- 参数绑定代码

### 上下文模型

Hertz 1.0 引入全新的双上下文模型:
- **context.Context**: 标准 Go Context,用于跨中间件传递,协程安全
- **app.RequestContext**: 请求上下文,包含请求/响应信息,高性能但非协程安全

## 架构组件

### Server 端

- **路由系统**: 支持静态路由、参数路由、通配符路由
- **Handler 处理**: 请求处理和响应构建
- **中间件**: 可插拔的请求处理链
- **Binding**: 自动参数绑定和验证
- **优雅退出**: 平滑停止服务

### Client 端

- **HTTP Client**: 高性能 HTTP 客户端
- **服务发现**: 支持 Consul 等服务发现
- **负载均衡**: 内置负载均衡算法
- **中间件**: Client 端中间件支持
- **正向代理**: 支持配置正向代理

## 支持的协议和特性

### 网络协议

- **HTTP/1.1**: 完整支持
- **HTTP/2**: Server 端支持,Client 端开发中
- **TLS**: 支持单/双向 TLS 认证
- **WebSocket**: 通过扩展支持

### 网络库

- **Netpoll**: 默认使用,高性能事件驱动网络库
- **Go net**: 支持切换到标准库网络实现
- **灵活切换**: 可按需切换网络库实现

## 使用场景

### 微服务 API

在微服务架构中,作为 HTTP 服务提供 RESTful API。

### API 网关

作为 API 网关,统一对外提供服务入口。

### 高性能服务

需要低延迟、高吞吐的 HTTP 服务场景。

### 中台服务

为前端或其他服务提供业务中台能力。

## 与其他框架对比

| 特性 | Hertz | Gin | Fasthttp |
|------|-------|-----|----------|
| 性能 | 极高 | 高 | 极高 |
| 易用性 | 高 | 高 | 中 |
| 生态 | 丰富 | 丰富 | 一般 |
| 网络库 | Netpoll | Go net | 自研 |
| 内部集成 | 完善 | 需定制 | 需定制 |
| 代码生成 | Hertztool | 无 | 无 |

## Hertz 版本说明

- **Hertz 1.x**: 推荐使用,最新特性和最佳性能
- **Hertz 0.x**: 已废弃,不推荐使用

当前文档基于 Hertz 1.0+ 版本编写。

## 下一步

- 阅读《Hertz 环境安装》
- 阅读《创建第一个 Hertz 服务》
- 了解《Server API 示例》
- 学习《Hertz 1.0 Release Notes》

## 参考资料

- [Hertz GitHub](https://github.com/cloudwego/hertz)
- [CloudWeGo 官网](https://www.cloudwego.io/)
- [字节跳动内部文档](https://bytedance.larkoffice.com/wiki/wikcnmQDePOkwy6EQIALtLnP0gd)
