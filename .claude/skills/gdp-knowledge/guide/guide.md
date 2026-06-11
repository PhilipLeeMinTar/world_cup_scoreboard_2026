# GDP项目开发规范

## 概述

本规范定义了在GDP项目中的开发标准和最佳实践，确保项目开发的一致性、可维护性和高质量。

## 核心原则

### 原则一：遵循 IDL 驱动开发流程

GDP 采用 **IDL 驱动开发模式**：先定义接口（IDL），再生成代码骨架，最后实现业务逻辑。

**核心要求**：
- **识别开发模式**：开发前先检测本地开发模式（`.gdp/rpcmodels.local.yaml` 存在）。`.gdp/rpcmodels.local.yaml` 用于存放本地 IDL 文件路径配置，如果该文件不存在，则代表 IDL 存放于远端。
- **IDL 编辑**：本地模式通过 `.gdp/rpcmodels.local.yaml` 获取 IDL 位置进行编辑。DevFlow 模式在平台编辑 IDL。
- **代码生成**：完成 IDL 变更后，**必须先执行 `gdp update` 同步代码**，再进行业务逻辑开发
- 禁止手动创建 router/handler/action/domain 目录下的文件

**详细参考**：[workflow-guide.md](./workflow-guide.md)

---

### 原则二：遵循 GDP 代码分层规范

代码组织**必须**遵循 GDP 分层架构，按 `handler → action → domain → dal → dao` 调用链组织代码。

**各层职责**：

| 层级 | 目录 | 职责 | 生成方式 | 可否修改 |
|------|------|------|----------|----------|
| Handler | `handler/` | RPC 入口层，路由分发（RPC 服务专用） | `gdp update` 自动生成 | **禁止修改** |
| Action | `action/` | 接入层，参数绑定和校验，调用 Domain | `gdp update` 自动生成 | 可添加逻辑 |
| Domain | `service/domain/` | 业务逻辑层，核心业务实现，调用 DAL | `gdp update` 自动生成 | 可编写业务 |
| DAL | `service/dal/` | 数据服务层，聚合 DAO、调用 RPC、缓存处理 | 手动创建 | 可编写 |
| DAO | `service/dao/` | 数据模型层，数据库 CRUD 操作 | 手动创建 | 可编写 |
| Pkg | `pkg/` | 工具层，通用工具、配置、类型定义 | 手动创建 | 可编写 |

**核心要求**：
- 禁止跨层调用，各层职责清晰
- `gdp update` 自动生成目录（router/handler/action/domain）：禁止手动创建文件，只能编辑已生成文件
- 手动创建目录（dal/dao/pkg）：按需创建和编写

**详细参考**：[code-layers-guide.md](./code-layers-guide.md)

---

### 原则三：使用 GDP 组件

禁止引入未经审核的第三方组件替代 GDP 官方实现。

**核心要求**：

| 要求 | 组件 | 使用场景 | 包名 | 参考文档 |
|------|------|----------|------|----------|
| 必须 | 日志 | 业务日志记录、错误追踪 | `code.byted.org/gdp/log` | [log.md](../components/log.md) |
| 必须 | 监控 | 业务指标采集、性能监控 | `code.byted.org/gdp/metrics` | [metrics.md](../components/metrics.md) |
| 建议 | 配置 | 配置管理、动态配置更新 | `code.byted.org/gdp/config` | [config.md](../components/config.md) |
| 建议 | 测试 | 单元测试、Mock 依赖隔离 | `code.byted.org/gdp/mocks` | [testing.md](../components/testing.md) |
| 建议 | Mockey | 函数/方法打桩、测试Mock | `github.com/bytedance/mockey` | [mockey-usage.md](../../golang/mockey-usage.md) |
| 建议 | compkg | 业务公共库、通用工具 | `code.byted.org/tiktok/compkg` | [compkg.md](../components/compkg.md) |

**详细参考**：[components/](../components/)

## 文档导航

### 必读文档

| 文档 | 说明 |
|------|------|
| [guide.md](./guide.md) | **整体规范**：核心原则、组件使用、最佳实践 |
| [workflow-guide.md](./workflow-guide.md) | **开发流程**：从IDL编辑、gdp update到业务实现的完整步骤 |
| [code-layers-guide.md](./code-layers-guide.md) | **代码规范**：action/domain/dal/dao/pkg 五层职责和调用规则 |

### 代码示例 (code-layers/)

- [action-examples.md](../code-layers/action-examples.md) - 接入层实现示例
- [domain-examples.md](../code-layers/domain-examples.md) - 业务逻辑层实现示例
- [dal-examples.md](../code-layers/dal-examples.md) - 数据服务层实现示例
- [dao-examples.md](../code-layers/dao-examples.md) - 数据模型层实现示例

### 组件文档 (components/)

- [log.md](../components/log.md) - 日志组件（必须）
- [metrics.md](../components/metrics.md) - 监控组件（必须）
- [config.md](../components/config.md) - 配置组件（建议）
- [testing.md](../components/testing.md) - 测试组件（建议）
- [compkg.md](../components/compkg.md) - 业务公共库
