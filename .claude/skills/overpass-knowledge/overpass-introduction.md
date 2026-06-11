# Overpass 平台简介

## 什么是 Overpass

**Overpass** 是 ByteDance 内部的一站式 RPC 调用解决方案,可以全自动生成 RPC 调用代码的服务。

**核心价值**:
- 自动生成 kitex_gen 代码
- 自动创建和管理 Client
- 提供统一的 RPC 调用封装
- IDL 变更时自动更新代码
- 集成 DevFlow 平台,与 IDL 管理无缝对接

**官方网站**: [overpass.bytedance.net](https://overpass.bytedance.net/)

---

## 免责声明

**重要**: Overpass 是代码生成和封装工具,以下情况不提供技术支持:

1. **对于 Overpass 类似产品**,Overpass 不会提供任何需求/技术支持
2. **对于人工或平台二次修改 Overpass 的成源代码**导致后续的请求失败或 Overpass 平台成失败,Overpass 不提供任何技术支持并免责
3. **Overpass 对于非 RGO 场景在编译期修改 Overpass 的代码**,所导致的编译报错、请求失败,Overpass 不提供任何技术支持并免责

**注**: 对于 Overpass 平台本身的代码生成报错仍提供支持

**详细免责声明**: [Overpass 免责文档](https://bytedance.larkoffice.com/docx/GLOfdjwaGo4uD7x5YjQcfF2fnib)

---

## 解决的问题

### 传统 RPC 调用的痛点

在没有 Overpass 的情况下,调用 RPC 的典型流程:

```
找到 PSM 的 IDL 文件路径 → kitex tool 生成代码 → 编写/copy 业务 RPC 封装代码 → RPC 调用
```

**存在的问题**:

1. **每次调用都要生成 kitex_gen**
   - 需要找 IDL 文件路径
   - 需要编写 NewClient 的代码
   - kitex tool 命令记不住,令人抓狂

2. **业务 RPC 封装散落各处**
   - 命名、标准不统一
   - 重复性工作太多
   - copy 来 copy 去,容易留坑

3. **通用功能缺乏统一实现**
   - 错误封装
   - Mock 支持
   - 日志打印
   - 每次都要写一大堆代码

---

## Overpass 的解决方案

### 核心机制

Overpass 为每个服务**全自动创建一个代码仓库**,路径为:

```
https://code.byted.org/overpass/P_S_M
```

**仓库自动包含**:
- ✅ 所有自动生成的 `kitex_gen`
- ✅ Client 的创建和管理
- ✅ 常用通用能力的封装实现
- ✅ 通用的错误处理
- ✅ 日志打印
- ✅ Mock 支持

**自动更新**: 当服务的 IDL 发生变化时,Overpass 能够感知并自动更新仓库中的代码

### 使用方式

**只需三步**:

1. 在 Overpass 网站添加 PSM 到白名单
2. 在项目中添加 Overpass 仓库依赖
3. 使用生成的函数进行 RPC 调用

**示例代码**:

```go
import "code.byted.org/overpass/tiktok_user_service/rpc/tiktok_user_service"

// 一行代码完成 RPC 调用
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
```

---

## Overpass 与 DevFlow 集成

### IDL 管理流程

```
DevFlow 修改 IDL
    ↓
DevFlow 触发 Overpass 更新
    ↓
Overpass 自动生成/更新代码仓库
    ↓
开发者执行 go get 更新依赖
    ↓
使用最新的 Overpass 代码进行 RPC 调用
```

### 与 DTO 的关系

**Overpass 主要负责**:
- RPC Client 代码生成
- RPC 调用封装
- kitex_gen 生成

**DTO (apimodels/rpcmodels) 负责**:
- 接口定义
- 数据传输对象
- 版本化管理

**两者配合使用**:
```go
// 使用 Overpass 生成的 RPC 调用
import "code.byted.org/overpass/tiktok_user_service/rpc/tiktok_user_service"

// 使用 DTO 定义的数据结构
import "code.byted.org/tiktok/rpcmodels/user_service"

resp, err := tiktok_user_service.GetUserInfo(ctx, &rpcmodels.GetUserInfoRequest{
    UserID: 12345,
})
```

---

## 核心特性

### 1. 白名单机制

**原因**: 公司内 RPC 服务众多,无法为所有服务预生成仓库

**解决方案**: 采用白名单机制,仅对用户需要调用的 PSM 创建仓库

**操作方式**:
1. 访问 [overpass.bytedance.net](https://overpass.bytedance.net/)
2. 在"IDL 信息查询"页面搜索 PSM
3. 点击"生成 Overpass 仓库"按钮
4. 等待数秒后仓库自动创建

### 2. 自动代码生成

**生成内容**:
- `kitex_gen/` - Kitex 自动生成的代码
- `rpc/` - RPC 调用封装
- `option/` - Kitex Option 配置
- `mock/` - Mock 实现

**生成时机**:
- 首次添加白名单时
- IDL 文件变更时
- 手动触发更新时

### 3. 统一的调用规范

**默认封装格式**:

```go
resp, err := P_S_M.Method(ctx, YourParams)
```

**特点**:
- 包名采用下划线形式的 P_S_M
- 方法名与 IDL 中定义一致
- 自动创建 Client (指定 PSM,无 Kitex Option)
- Request 结构体简化,仅接受非 optional 字段

---

## Overpass V2 模板升级

### 版本说明

**Overpass V2**: 2023 年 3 月升级的新模板,当前线上使用版本

**主要改进**:
- 更简洁的 API 设计
- 更好的类型安全
- 更强大的自定义扩展能力
- 更完善的错误处理

**迁移指南**: 参考 [新模板 QuickLook](https://doc.bytedance.net/docs/3861/5551/v2_quicklook/)

---

## 与 GDP 开发的关系

在 GDP 开发流程中,Overpass 用于:

1. **调用下游 RPC 服务** - 在 DAL 层调用其他服务的 RPC 接口
2. **获取 DTO 定义** - 通过 Overpass 生成的代码访问 DTO 结构
3. **统一 RPC 调用规范** - 所有 GDP 服务使用统一的 Overpass 调用方式

**典型使用场景**:

```
GDP Service A (DAL 层)
    ↓ (使用 Overpass)
调用 Service B 的 RPC 接口
    ↓
Service B (RPC 服务)
```

---

## 常见问题

### Q1: IDL 文件是从哪里获取的?

**A**: Overpass 从 DevFlow 平台自动获取 IDL 文件。服务的 IDL 必须在 DevFlow 中注册和管理。

### Q2: 生成代码需要多久?

**A**: 通常数秒内完成。复杂的 IDL 可能需要 10-30 秒。

### Q3: Overpass 采用哪个 RPC 框架?

**A**: Overpass 基于 **Kitex** 框架生成代码。

### Q4: 如何更新 Overpass 生成的代码?

**A**: 执行 `go get -u code.byted.org/overpass/your_psm@latest` 更新到最新版本。

### Q5: Overpass 支持哪些语言?

**A**:
- Go (主要支持)
- Python/Euler
- Java/Jet
- Rust/Lust
- JavaScript
- Hertz (HTTP)

---

## 文档指引

**快速开始**:
- [Quick Start](overpass-quickstart.md) - 通过实例快速上手 Overpass

**核心功能**:
- [overpass Go 代码基本使用](overpass-go-usage.md) - Go 语言使用详解
- [overpass 平台基础操作](overpass-platform-operations.md) - 平台操作指南

**与 GDP 集成**:
- [DevFlow Overpass 集成](devflow-overpass-integration.md) - GDP 开发中使用 Overpass

**进阶主题**:
- RPC Mock 支持
- 自定义扩展能力
- 错误和日志处理

---

## 用户支持

**反馈渠道**:
- 加入 Overpass 用户群
- 提交 Issue 到 SCM
- 发起 Overpass Oncall

**相关链接**:
- Overpass 网站: [overpass.bytedance.net](https://overpass.bytedance.net/)
- 免责声明: [Overpass 免责文档](https://bytedance.larkoffice.com/docx/GLOfdjwaGo4uD7x5YjQcfF2fnib)
- 新模板文档: [Overpass V2 QuickLook](https://doc.bytedance.net/docs/3861/5551/v2_quicklook/)

---

## 相关文档

- [overpass-quickstart.md](overpass-quickstart.md) - Overpass 快速开始
- [devflow-overpass-integration.md](devflow-overpass-integration.md) - GDP 开发中使用 Overpass
- [devflow-workflow-overview.md](devflow-workflow-overview.md) - DevFlow 工作流概览
