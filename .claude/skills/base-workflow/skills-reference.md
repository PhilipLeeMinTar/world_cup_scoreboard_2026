# 可用 Skill 速查与选择指南

> **重要**：在调用任何 Skill 前，**必须先阅读对应的 Skill** 获取完整的参数说明、输入输出格式和使用示例。
> **Workflow Session 约束**：本文件中的所有 `gdpa-cli run` 示例在实际执行时都应显式追加同一个 `--session-id <sid>`。CLI 不再全局强制，但 base-workflow 需要依赖它串联 `.gdpa/{session-id}/status.json`、恢复进度和排障信息。

## Skill 速查表

| 分类 | Skill 名称 | 一句话说明 | 典型场景 |
|------|-----------|-----------|---------|
| **任务管理** | `devflow` | DevFlow 任务生命周期管理 | 创建/查询/启动/关闭开发任务、触发部署流水线 |
| | `meego-manage` | Meego 任务搜索与关联 | 搜索用户任务、按关键字查找 Story/Issue |
| **接口 & IDL** | `edit-idl` | IDL 编辑编排指南（不可直接运行），需依次调用 `idl-pull` → `idl-commit` → `idl-codegen` | 新增/修改/删除接口字段、新增 Endpoint |
| | `idl-pull` | 拉取 PSM 相关 IDL 文件到本地临时目录 | edit-idl 流程第 1 步 |
| | `idl-commit` | 提交 IDL 变更到远程仓库并创建 BAM 版本 | edit-idl 流程第 2 步（本地编辑后） |
| | `idl-codegen` | 触发代码生成并检查状态 | edit-idl 流程第 3 步 |
| | `bam-api` | 查询 BAM 上的 API 接口定义 | 查看下游接口 Schema、获取接口列表 |
| | `bam-query` | BAM 接口测试（发送 RPC/HTTP 请求） | 测试接口、调试 RPC/HTTP 端点 |
| **服务 & 调用** | `overpass` | 获取服务 IDL 信息和生成 Kitex 调用代码 | 获取方法列表、生成 overpass 代码 |
| **代码 & 仓库** | `repotalk` | 代码仓库智能查询 | 语义搜索代码、查看结构体定义、分析调用链 |
| **动态配置 & 数据** | `tcc-query` | 查询 TCC 远程配置 | 查询开关状态、AB 实验配置、分支控制逻辑 |
| | `rds_query` | 查询 RDS 数据库元数据（BOE） | 搜索数据库、查看表结构、获取库信息 |
| **日志 & 排查** | `argos-query` | 查询 Argos 服务日志 | 按 PSM/关键字/时间范围搜索日志 |
| **权限** | `iam` | IAM 权限申请 | 为服务账号申请 MCP 调用权限 |

## Skill 选择决策指南

```
需要创建/管理研发任务？
  ├─ 创建/查询/启动/关闭任务 → devflow
  └─ 搜索关联 Meego 任务 → meego-manage

需要变更 IDL 接口？
  └─ 是 → 阅读 edit-idl 编排指南，依次执行：
       ├─ idl-pull（拉取 IDL 到本地）
       ├─ 本地编辑 .thrift/.proto 文件
       ├─ idl-commit（提交 + 创建 BAM 版本）
       └─ idl-codegen（触发代码生成）

需要了解下游服务的接口定义/Schema？
  ├─ 知道 PSM → bam-api (get_api_service_list → get_api_definition_info)
  └─ 不知道 PSM，只知道关键字 → bam-api (get_api_definition_info_without_psm)

需要测试接口（发送 RPC/HTTP 请求）？
  └─ 是 → bam-query（vregion 用标准值如 Singapore-Central，env 用完整泳道名如 ppe_xxx）

需要调用 Kitex 下游服务？
  ├─ 获取方法列表 → overpass (get_psm_method_list)
  ├─ 获取调用代码 → repotalk (get_rpcinfo)
  └─ 获取/生成 overpass 仓库 → overpass (get_psm_repo_info / generate_psm_repo)

需要理解代码仓库结构/搜索代码？
  ├─ 语义搜索（用自然语言找代码） → repotalk (search_nodes)
  ├─ 查看结构体/函数定义 → repotalk (get_nodes_detail)
  ├─ 查看仓库概览 → repotalk (get_repos_detail)
  └─ 查询内部组件用法 → repotalk (infra_search)

需要管理代码版本（CI/CD）？
  └─ 是 → scm（查询仓库/版本、创建版本、查看构建日志）

需要查看 TCC 远程配置来判断代码逻辑？
  └─ 是 → tcc-query（查询开关、AB 实验、分支控制配置）

需要查询数据库表结构？
  └─ 是 → rds_query（BOE 环境元数据查询）

需要查看 TCE 服务/集群/Pod 信息？
  └─ 是 → tce（服务列表、集群详情、Pod 状态）

需要查询/分析服务日志？
  └─ 是 → argos-query（按 PSM/关键字/时间范围搜索 Argos 日志）

需要申请 MCP 服务调用权限？
  └─ 是 → iam（为服务账号申请权限）
```

## coding 阶段常用 Skill 用法

| 场景 | Skill | 示例命令 |
|------|-------|---------|
| 查询 TCC 配置 | `tcc-query` | `gdpa-cli run tcc-query --input '{"action": "get_config", "key": "..."}'` |
| 查询下游接口定义 | `bam-api` | `gdpa-cli run bam-api --input '{"action": "get_api_definition_info", "psm": "...", "method": "..."}'` |
| 获取 Kitex 调用方式 | `overpass` | `gdpa-cli run overpass --input '{"action": "get_psm_method_list", "psm": "..."}'` |
| 语义搜索代码 | `repotalk` | `gdpa-cli run repotalk --input '{"action": "search_nodes", "question": "...", "repo_names": "..."}'` |
| 查询数据库表结构 | `rds_query` | `gdpa-cli run rds_query --input '{"action": "list_tables", "db_name": "..."}'` |
| 查询内部组件用法 | `repotalk` | `gdpa-cli run repotalk --input '{"action": "infra_search", "component": "Kitex", "question": "..."}'` |
| 申请 MCP 调用权限 | `iam` | `gdpa-cli run iam --input '...'` |

## testing 阶段 bam-query 用法

> **重要**：`vregion` 必须使用标准值，`env` 使用完整泳道名。所有参数从 `status.json` 的 `context` 读取。

| 参数 | 来源 | 示例值 |
|------|------|--------|
| `vregion` | `context.vregion[i]` | `Singapore-Central`（不是 `sg`） |
| `vdc` | `context.vdc[i]` | `sg1`（不是 `sg`） |
| `env` | `context.env` | `ppe_20260211`（不是 `ppe`） |

```bash
# 正确示例：使用标准 VRegion + 完整 env
gdpa-cli run bam-query --input '{"action":"rpc","psm":"tiktok.xxx.service","func_name":"GetUserInfo","request":"{}","vregion":"Singapore-Central","env":"ppe_20260211","vdc":"sg1"}'

```
