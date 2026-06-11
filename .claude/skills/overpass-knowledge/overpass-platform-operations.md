# Overpass 平台操作指南

## 概述

本文介绍 Overpass 网站 ([overpass.bytedance.net](https://overpass.bytedance.net/)) 的各项功能和操作方法。

---

## 平台功能总览

Overpass 网站提供两大核心功能模块:

```
┌─────────────────────────────────────┐
│     Overpass 网站功能架构           │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐ │
│  │   IDL 信息查询               │ │
│  ├───────────────────────────────┤ │
│  │ • PSM 搜索                    │ │
│  │ • IDL 文件查看                │ │
│  │ • 生成 Overpass 仓库          │ │
│  │ • 查看生成进度                │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │   仓库信息管理               │ │
│  ├───────────────────────────────┤ │
│  │ • 查看已生成仓库              │ │
│  │ • 快捷命令                    │ │
│  │ • 手动触发更新                │ │
│  │ • 删除仓库                    │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

---

## IDL 信息查询

### 功能 1: PSM 搜索

**位置**: 首页 → IDL 信息查询

**操作步骤**:

1. 在搜索框输入 PSM (支持模糊搜索)
   - 完整 PSM: `tiktok.user.service`
   - 部分关键词: `user.service`
   - 下划线格式: `tiktok_user_service`

2. 点击 "搜索" 或按 Enter

3. 查看搜索结果

**搜索结果包含**:
- PSM 名称
- IDL 文件路径
- 服务类型 (RPC/API)
- 所属业务线
- 仓库状态 (已生成/未生成)

### 功能 2: 生成 Overpass 仓库

**前提条件**:
- ✅ PSM 在 DevFlow 中已注册
- ✅ IDL 文件已提交到主干或任务分支
- ✅ 你有该服务的访问权限

**操作步骤**:

1. 搜索目标 PSM
2. 点击 **"生成 Overpass 仓库"** 按钮
3. 等待生成 (通常 5-30 秒)
4. 页面自动刷新,按钮变为 **"仓库已存在"**

**生成内容**:
```
https://code.byted.org/overpass/P_S_M
├── kitex_gen/     # 自动生成
├── rpc/           # RPC 调用封装
├── option/        # Kitex Option
├── mock/          # Mock 实现
└── go.mod         # Go 模块
```

### 功能 3: 查看 IDL 文件

**操作步骤**:

1. 搜索 PSM
2. 点击 **"查看 IDL"** 链接
3. 在线查看 IDL 文件内容

**功能特点**:
- 语法高亮
- 可以查看历史版本
- 可以查看依赖的其他 IDL 文件

### 功能 4: 查看代码生成进度

**适用场景**: 首次生成仓库或 IDL 变更后查看更新进度

**操作步骤**:

1. 搜索 PSM
2. 点击 **"生成进度"** 按钮
3. 查看生成状态

**生成状态**:
- ⏳ **队列中** - 等待生成
- 🔄 **生成中** - 正在生成代码
- ✅ **成功** - 生成完成
- ❌ **失败** - 生成失败 (查看错误日志)

---

## 仓库信息管理

### 功能 1: 查看已生成仓库

**位置**: 首页 → 仓库信息管理

**查看方式**:

**方式 1: 查看所有仓库**
- 显示你有权限的所有 Overpass 仓库
- 支持按业务线、服务类型筛选
- 支持按更新时间排序

**方式 2: 搜索特定仓库**
- 输入 PSM 或关键词
- 快速定位目标仓库

**仓库信息包含**:
- 仓库 URL
- PSM 名称
- 生成时间
- 最后更新时间
- IDL 版本
- 自动更新状态

### 功能 2: 快捷命令

Overpass 提供多个实用的快捷命令,一键复制到剪贴板。

#### 2.1 添加依赖

**命令**:
```bash
go get code.byted.org/overpass/P_S_M
```

**使用场景**: 在项目中添加 Overpass 依赖

**操作**:
1. 点击 "添加依赖" 按钮
2. 命令自动复制到剪贴板
3. 在终端粘贴并执行

#### 2.2 Import 路径

**内容**:
```go
"code.byted.org/overpass/P_S_M/rpc/p_s_m"
```

**使用场景**: 在代码中 import Overpass 包

**操作**:
1. 点击 "import 路径" 按钮
2. 路径自动复制到剪贴板
3. 在代码中粘贴

#### 2.3 仓库 URL

**内容**:
```
https://code.byted.org/overpass/P_S_M
```

**使用场景**: 在浏览器中查看 Overpass 仓库

**操作**:
1. 点击 "仓库 URL" 按钮
2. 在浏览器中打开

#### 2.4 更新依赖

**命令**:
```bash
go get -u code.byted.org/overpass/P_S_M@latest
```

**使用场景**: 更新 Overpass 依赖到最新版本

### 功能 3: 手动触发更新

**适用场景**:
- IDL 文件已变更,但 Overpass 仓库未自动更新
- 需要立即获取最新的代码生成结果

**操作步骤**:

1. 在仓库信息管理页面找到目标仓库
2. 点击 **"手动触发更新"** 按钮
3. 确认操作
4. 等待更新完成

**更新流程**:
```
手动触发更新
    ↓
从 DevFlow 拉取最新 IDL
    ↓
Kitex Tool 生成代码
    ↓
更新 Overpass 仓库
    ↓
触发 CI 构建
    ↓
更新完成
```

### 功能 4: 基于分支生成仓库

**适用场景**: 基于 IDL 的特定分支生成临时仓库,用于测试

**操作步骤**:

1. 在仓库信息管理页面
2. 点击 **"基于分支生成"**
3. 输入分支名称 (例如: `feature-new-api`)
4. 点击 "生成"

**生成的仓库**:
```
https://code.byted.org/overpass/P_S_M_branch_feature_new_api
```

**注意事项**:
- ⚠️ 基于分支的仓库不会自动更新
- ⚠️ 分支合并后建议删除临时仓库
- ⚠️ 仅用于测试,不要在生产环境使用

### 功能 5: 删除仓库

**适用场景**: 不再使用的 Overpass 仓库

**操作步骤**:

1. 在仓库信息管理页面
2. 找到目标仓库
3. 点击 **"删除"** 按钮
4. 确认删除 (输入 PSM 确认)

**注意事项**:
- ⚠️ 删除操作不可恢复
- ⚠️ 删除前确保没有代码依赖该仓库
- ⚠️ 删除后可以重新生成

---

## 添加白名单详解

### 白名单机制

Overpass 采用白名单机制的原因:

1. **服务数量庞大**: 公司内有数万个 RPC 服务
2. **按需生成**: 仅为用户需要调用的 PSM 创建仓库
3. **节约资源**: 避免预生成大量无用仓库
4. **自动更新**: 白名单内的仓库会自动跟随 IDL 变更更新

### 添加白名单的完整流程

```
步骤 1: 搜索 PSM
    ↓
步骤 2: 点击"生成 Overpass 仓库"
    ↓
步骤 3: 系统验证 (PSM 是否存在、权限等)
    ↓
步骤 4: 从 DevFlow 拉取 IDL
    ↓
步骤 5: Kitex Tool 生成代码
    ↓
步骤 6: 创建 SCM 仓库
    ↓
步骤 7: 提交代码到仓库
    ↓
步骤 8: 配置自动更新 Webhook
    ↓
步骤 9: 完成 (显示"仓库已存在")
```

### 常见错误和解决方案

#### 错误 1: "PSM 不存在"

**原因**: DevFlow 中没有该 PSM 的注册信息

**解决方案**:
1. 确认 PSM 拼写正确
2. 在 [DevFlow 平台](https://janus.byted.org/devflow/) 搜索该 PSM
3. 如果确实不存在,联系服务 Owner 在 DevFlow 注册

#### 错误 2: "IDL 文件不存在"

**原因**: DevFlow 中该 PSM 没有 IDL 文件

**解决方案**:
1. 在 DevFlow 检查 IDL 文件是否已提交
2. 确认 IDL 文件路径配置正确
3. 联系服务 Owner 上传 IDL 文件

#### 错误 3: "权限不足"

**原因**: 你没有该服务的访问权限

**解决方案**:
1. 联系服务 Owner 添加权限
2. 在 DevFlow 平台申请权限
3. 加入服务的用户组

#### 错误 4: "生成超时"

**原因**: IDL 过于复杂或系统繁忙

**解决方案**:
1. 等待 1-2 分钟后刷新页面
2. 查看生成进度页面了解详情
3. 如果持续失败,发起 Overpass Oncall

#### 错误 5: "自动更新失败"

**原因**: Webhook 配置错误或 DevFlow 异常

**解决方案**:
1. 点击 "手动触发更新" 按钮
2. 如果手动更新也失败,查看错误日志
3. 发起 Overpass Oncall 寻求支持

---

## 前端实用功能

### 1. 快速跳转

**仓库相关链接**:
- 📦 Overpass 仓库 (SCM)
- 📄 IDL 文件 (DevFlow)
- 📊 CI 构建状态
- 📖 生成的文档

**操作**: 点击对应的图标或链接即可快速跳转

### 2. 批量操作

**支持的批量操作**:
- 批量添加白名单
- 批量更新依赖
- 批量删除仓库

**操作步骤**:
1. 勾选目标仓库
2. 点击批量操作按钮
3. 确认操作

### 3. 收藏夹

**功能**: 收藏常用的 Overpass 仓库

**操作**:
1. 点击仓库旁的 ⭐ 图标收藏
2. 在 "我的收藏" 页面查看所有收藏的仓库

### 4. 最近使用

**功能**: 自动记录最近访问的仓库

**查看**: 首页 → "最近使用" 模块

### 5. 搜索历史

**功能**: 保存最近的搜索记录

**查看**: 搜索框下拉列表显示历史搜索

---

## IDL 信息服务

Overpass 提供 IDL 信息查询 API,可以通过编程方式获取 IDL 信息。

### API Endpoint

```
GET https://overpass.bytedance.net/api/v1/idl/info
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| psm | string | 是 | 服务 PSM |
| version | string | 否 | IDL 版本 (默认 latest) |

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "psm": "tiktok.user.service",
    "idl_path": "idl/user/user_service.thrift",
    "idl_content": "...",
    "methods": [
      {
        "name": "GetUserInfo",
        "request": "GetUserInfoRequest",
        "response": "GetUserInfoResponse"
      }
    ],
    "repo_url": "https://code.byted.org/overpass/tiktok_user_service",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

### 使用示例

```go
import (
    "encoding/json"
    "net/http"
)

func getIDLInfo(psm string) (*IDLInfo, error) {
    url := fmt.Sprintf("https://overpass.bytedance.net/api/v1/idl/info?psm=%s", psm)

    resp, err := http.Get(url)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result struct {
        Code    int      `json:"code"`
        Message string   `json:"message"`
        Data    *IDLInfo `json:"data"`
    }

    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return result.Data, nil
}
```

---

## 监控和告警

### 自动更新监控

Overpass 会监控所有仓库的自动更新状态。

**监控指标**:
- 更新成功率
- 更新延迟
- 错误率

**告警机制**:
- 更新失败 → 邮件通知服务 Owner
- 连续失败 3 次 → 升级告警
- 关键服务更新失败 → 立即告警

### 查看监控数据

**位置**: 仓库信息管理 → 点击仓库 → "监控数据"

**数据内容**:
- 最近 7 天更新记录
- 成功/失败次数
- 平均更新耗时
- 错误日志

---

## 权限管理

### 权限级别

| 权限级别 | 说明 | 能做什么 |
|---------|------|---------|
| **查看** | 查看仓库信息 | 搜索、查看 IDL、查看仓库 |
| **使用** | 使用仓库 | 生成仓库、添加依赖 |
| **管理** | 管理仓库 | 手动更新、删除仓库 |
| **所有者** | 服务 Owner | 所有操作、权限管理 |

### 申请权限

**步骤**:
1. 在 Overpass 网站搜索 PSM
2. 点击 "申请权限"
3. 填写申请理由
4. 等待 Owner 审批

---

## 最佳实践

### 1. 及时更新依赖

IDL 变更后,及时更新 Overpass 依赖:

```bash
go get -u code.byted.org/overpass/<P_S_M>@latest
```

### 2. 使用快捷命令

利用网站提供的快捷命令,提高操作效率。

### 3. 收藏常用仓库

将常用的 Overpass 仓库加入收藏,方便快速访问。

### 4. 定期检查更新状态

定期查看仓库的自动更新状态,确保使用的是最新代码。

### 5. 遇到问题及时反馈

如果遇到生成失败、更新异常等问题,及时通过 Oncall 反馈。

---

## 常见问题

### Q1: 如何批量生成多个服务的 Overpass 仓库?

**A**: 目前不支持批量生成,需要逐个添加白名单。可以使用 IDL 信息服务 API 实现自动化。

### Q2: Overpass 仓库可以手动修改吗?

**A**: 不建议手动修改。Overpass 仓库会自动更新,手动修改的内容会被覆盖。如需自定义,建议在业务代码中封装。

### Q3: 如何查看 Overpass 仓库的更新历史?

**A**: 在仓库信息管理页面点击仓库,然后查看 "更新历史" 标签。

### Q4: Overpass 支持哪些 IDL 格式?

**A**: 主要支持 Thrift IDL,也支持 Protobuf (需要特殊配置)。

### Q5: 如何知道 Overpass 仓库何时更新?

**A**: 可以在仓库信息管理页面查看最后更新时间,或者订阅更新通知。

---

## 相关文档

- [Overpass 平台简介](./overpass-introduction.md)
- [Overpass 快速开始](./overpass-quickstart.md)
- [Overpass Go 代码使用](./overpass-go-usage.md)
- [问题排查](./overpass-troubleshooting.md)
