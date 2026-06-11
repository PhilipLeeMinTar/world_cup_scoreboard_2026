---
name: env
description: Query and manage Env Platform BOE/PPE environments — view details, services, clusters, permissions, fallback config, deploy/upgrade/delete TCE/TCC services via DSL, create or delete environments, check deployment status, and get SCM dependencies. Use whenever the user asks about BOE or PPE environments, wants to deploy a service, check deployment status, view services/clusters, verify permissions, check fallback configuration, delete an environment, or get SCM code dependencies. Also trigger when the user mentions env platform, BOE/PPE deployment, DSL deploy, TCE/TCC deployment to BOE/PPE, or environment management.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# Env Platform 查询与部署

> **何时使用**: 查询或管理 BOE/PPE 环境信息，包括环境详情、服务列表、集群信息、权限检查、Fallback 配置、服务部署（创建/升级/删除）、环境创建、部署状态查询、SCM 依赖等。

## 使用方法

```bash
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "<action>", ...}'
```

## 支持的 Action

### 查询类

| Action | 描述 | 必填参数 | 可选参数 |
|--------|------|----------|----------|
| `detail` | 获取环境详情 | name | type |
| `service_info` | 获取环境中部署的服务列表 | name | type, detail_limit |
| `cluster_info` | 获取 PSM 在 BOE/PPE 中的集群信息 | psm | scope, env |
| `check_permission` | 检查用户对服务的操作权限 | psm, scope | env |
| `fallback_conf` | 获取环境 Fallback 配置 | env_name | env_type |
| `instance_meta` | 获取环境实例元信息（按 VRegion 聚合，含集群、SCM、调试等详情） | name | env_type, search, service_types, services |
| `create_suggest` | 获取服务部署建议（集群、配额、IDC、可用 zones 树） | psm | service_type, env, env_type, vregion, idc, zone, cluster |
| `scm_dependencies` | 获取服务的 SCM 代码依赖 | psm | env, env_type |

### 部署类（DSL）

| Action | 描述 | 必填参数 | 可选参数 |
|--------|------|----------|----------|
| `dsl_deploy` | 在已有环境中部署/升级/删除服务（DSLUpdate） | name, psm | version, branch, deploy_action, region, ... |
| `faas_deploy` | 在已有环境中部署 ByteFaaS（create=建集群+发版；upgrade=仅发版，需已有集群名） | name, psm | `deploy_action`（create 默认 / upgrade）, cluster（upgrade 必填）, env_type, region, ... |
| `faas_create` | 创建全新 PPE 环境并部署 ByteFaaS 服务（DSLCreate） | name, psm | env_type, region, cluster, code_version, pre_check, ... |
| `dsl_create` | 创建新环境并部署 TCE/TCC 服务（DSLCreate） | name, psm | version, branch, zone, cpu, mem, ... |
| `delete_env` | 删除整个环境（包含其中所有服务） | name | — |
| `dsl_status` | 查询 DSL 部署状态 | deployment_id | name |
| `dsl_retry` | 重试失败的 DSL 部署 | deployment_id | name |

## 输入参数说明

### 通用参数

| 参数 | 类型 | 描述 |
|------|------|------|
| action | string | 必填，要执行的操作 |
| name | string | 环境名称（如 `boe_xxx` 或 `ppe_xxx`） |
| psm | string | 服务 PSM |
| vregion | string | **必填。** VRegion（`code.byted.org/gopkg/env` 标准常量），用于认证和区域路由。如果用户未指定，**必须先询问用户目标区域**，不要自行填写默认值 |

### 查询类参数

| 参数 | 类型 | 描述 |
|------|------|------|
| scope | string | 环境范围：`boe` 或 `ppe` |
| env | string | 具体的环境名称（用于 cluster_info、check_permission、create_suggest、scm_dependencies） |
| env_name | string | 环境名称（用于 fallback_conf） |
| type | string | 环境类型，可从 name 前缀自动推断 |
| env_type | string | 环境类型：`boe_feature`、`boe_base`、`ppe` |
| search | string | 搜索关键字（用于 instance_meta 过滤） |
| service_types | string | 服务类型过滤（用于 instance_meta），如 `tce` |
| services | string | 服务 PSM 过滤（用于 instance_meta），如 `my.service.psm` |
| detail_limit | int | 服务详情返回数量上限（用于 service_info），默认 100 |
| service_type | string | 服务类型（用于 create_suggest），默认 `tce` |

### 查询类参数（create_suggest）

`create_suggest` 用于获取服务在某个环境下的部署建议（推荐 cpu/mem/count/zone/idc/cluster 等）。
默认 `env_type=ppe`（未传时自动补默认值，否则 BITS API 返回基本为空）。
默认 `SpecifyDcs` 来自 `vregion → DefaultVDC`，但只要用户显式传 `idc/zone/cluster`，就会原样透传给 BITS API，不再受 vregion 默认 VDC 限制。

| 参数 | 类型 | 描述 |
|------|------|------|
| psm | string | 必填，服务 PSM |
| service_type | string | 服务类型，默认 `tce`（可选 `tcc`） |
| env | string | 环境名（可选；用于查同名环境下的建议） |
| env_type | string | `ppe` / `boe_feature` / `boe_base`，未传默认 `ppe` |
| vregion | string | 目标 VRegion，例如 `Singapore-Central`、`MYCOMPLIANCE`；未显式给 idc 时用作默认 VDC |
| idc | string | 想看哪些 IDC 的建议，逗号分隔（如 `my,my2`），等价于 `idcs`/`vdc`/`vdcs` |
| zone | string | 想看哪些 zone 的建议，逗号分隔（如 `tiktok-row-default`） |
| cluster | string | 想看哪些虚拟集群的建议，逗号分隔 |

返回字段除了原有的 `quota.cpu_suggest / mem_suggest / count_suggest / idc_suggest` 外，
还包含 `quota.zones`：完整的 `zone → virtual_clusters → idc_list` 树（每个 IDC 标注 vregion / cpu / mem / resource_pool / resource_group_id），便于人工或后续 `dsl_deploy` 选择放置。

### 部署类参数（dsl_deploy）

`dsl_deploy` 操作已有环境中的服务，使用 `DSLUpdate` API。支持三种模式：

- **升级（upgrade）**：已有集群 + 提供 version/branch → 自动检测为 upgrade
- **新建服务（create）**：无集群 → 自动检测为 create，从 `create_suggest` 补全参数
- **删除服务（delete）**：设置 `deploy_action=delete`

| 参数 | 类型 | 描述 | 自动补全 |
|------|------|------|----------|
| version | string | SCM 版本号（如 `1.0.0.213`），与 `branch` 二选一 | — |
| branch | string | Git 分支名，与 `version` 二选一 | — |
| deploy_action | string | 部署动作：`create`、`upgrade`、`delete`。不传时自动推断 | — |
| service_type | string | 服务类型，默认 `tce`（可选：`tcc`） | — |
| scm_name | string | SCM 仓库名称 | ✅ 从 `scm_dependencies` 主仓库获取 |
| region | string | 部署区域（TCC 服务必填，如 `EU-TTP,US-EastRed`） | — |
| service_id | string | TCC 服务 ID | ✅ 自动通过 `SearchTccService` 获取 |
| cluster_name | string | 集群名称，默认 `default`（仅新建时使用） | — |
| zone | string | TCE zone（仅新建时使用） | ✅ 从 `create_suggest` 获取 |
| idc | string | IDC 名称（仅新建时使用，支持逗号分隔多个 IDC，如 `my,my2`） | ✅ 从 `create_suggest` 获取 |
| virtual_cluster | string | 虚拟集群名称（仅新建时使用） | ✅ 从 `create_suggest` 获取 |
| cpu | float | CPU 配额（仅新建时使用） | ✅ 从 `create_suggest` 获取 |
| mem | float | 内存配额（仅新建时使用） | ✅ 从 `create_suggest` 获取 |
| count | int | 实例数量（仅新建时使用；多 IDC 时会对每个 IDC 生效） | ✅ 从 `create_suggest` 获取 |
| sync | bool | 是否同步等待部署完成，默认 `false` | — |
| failed_strategy | string | 失败策略，默认 `WaitBrothers` | — |

> **自动补全说明**：
> - 所有自动补全的参数均可被用户显式传入的值覆盖
> - `scm_dependencies` → 自动获取主仓库 `name` 和 `remote_id`
> - `cluster_info` → 获取已有集群 ID 列表（用于判断 create/upgrade）
> - `create_suggest` → 新建时自动获取 zone、cpu、mem、ports、sidecar 等参数
> - `SearchTccService` → TCC 服务自动获取 service_id
>
> **SCM 类型自动设置**：
> - 传 `version` → `ScmRepo.Type="scm"`（SCM 版本号部署）
> - 传 `branch` → `ScmRepo.Type="git"`（Git 分支部署）
>
> **TCC 注意事项**：
> - TCC 部署必须提供 `region` 参数（如 `EU-TTP`、`US-EastRed`、`CN`），否则会报错
> - `service_id` 可自动获取，也可手动指定

### 部署类参数（faas_deploy）

`faas_deploy` 用于在**已有 PPE 环境**中部署 ByteFaaS 服务。它和 `dsl_deploy` 一样属于“已有环境内的部署”，但面向 ByteFaaS 场景，agent 会自动完成 region 选择、可用版本选择、基础集群查询以及部署前校验。

支持两种模式：

- **`create`**（默认）：为目标服务创建/选择 ByteFaaS 集群并发版
- **`upgrade`**：仅对已有 ByteFaaS 集群发版，**必须显式传 `cluster`**

执行前会做必要的一致性校验；如果代码版本与 SCM 依赖信息不匹配，或预检查发现阻断项，agent 会直接失败并把原因返回给用户，而不会继续提交部署。

| 参数 | 类型 | 描述 |
|------|------|------|
| name | string | 环境名称（必填） |
| psm | string | 服务 PSM（必填） |
| deploy_action | string | `create`（默认）：建集群并发版；`upgrade`：仅发版（须传 `cluster`） |
| env_type | string | 环境类型，默认 `ppe` |
| region | string | FaaS region 的 `name`（如 `cn-north`）；不传则按 `vregion`、`lane_zone` 推断 |
| lane_zone | string | 指定 lane_zone（如 `CN`），用于在没有显式 `region` 时挑选 region |
| cluster | string | base cluster 名；与 `base_cluster` 等价 |
| base_cluster | string | 同 `cluster`，二选一 |
| base_cluster_name | string | DSL `meta.clusters[].base_cluster_name`，默认与 cluster 相同 |
| code_version | string | 选用 `get_code_version` 中 `number` 或 `source` 匹配的一项；不传则取列表第一个 |
| code_revision_id | string | `faas_release[].code_revision_id` |
| use_latest_code_revision | bool | 默认 `true` |
| scm_source | string | 覆盖 `scm_version.source`（可选） |
| scm_source_type | string | 覆盖 `source_type`（可选） |
| scm_deploy_method | string | 覆盖 `deploy_method`（可选） |
| pre_check | bool | 是否 DSL 预检查，默认 `false` |
| expire_time | int | `run_option.expire_time`，默认 `10` |
| recycle_type | string | 默认 `short` |
| recycle_due_time | string | PPE `short` 回收截止时间（RFC3339）；不传时 agent 对 `ppe` 默认约为 14 天后 |
| debug | bool | `meta.debug`，默认 `false` |
| sync / failed_strategy | bool / string | 与 `dsl_deploy` 相同 |

> 注意：
> - `faas_deploy` 面向 **PPE ByteFaaS**
> - 如果只是给已有集群发版，优先使用 `deploy_action=upgrade`
> - `upgrade` 场景下必须提供 `cluster`
> - `pre_check=true` 时，若存在阻断项会直接中止，不会继续部署

### 部署类参数（faas_create）

`faas_create` 用于创建**全新 PPE 环境**并部署 ByteFaaS 服务，使用 `DSLCreate` API。仅当环境不存在时使用。与 `faas_deploy` 的区别在于：`faas_deploy` 操作已有环境（DSLUpdate），`faas_create` 创建新环境（DSLCreate）。

| 参数 | 类型 | 描述 |
|------|------|------|
| name | string | 新环境名称（必填） |
| psm | string | 服务 PSM（必填） |
| env_type | string | 环境类型，默认 `ppe` |
| region | string | FaaS region 的 `name`（如 `cn-north`）；不传则按 `vregion`、`lane_zone` 推断 |
| lane_zone | string | 指定 lane_zone（如 `CN`），用于在没有显式 `region` 时挑选 region |
| cluster | string | base cluster 名；与 `base_cluster` 等价 |
| base_cluster | string | 同 `cluster`，二选一 |
| base_cluster_name | string | DSL `meta.clusters[].base_cluster_name`，默认与 cluster 相同 |
| code_version | string | 选用 `get_code_version` 中 `number` 或 `source` 匹配的一项；不传则取列表第一个 |
| code_revision_id | string | `faas_release[].code_revision_id` |
| use_latest_code_revision | bool | 默认 `true` |
| scm_source | string | 覆盖 `scm_version.source`（可选） |
| scm_source_type | string | 覆盖 `source_type`（可选） |
| scm_deploy_method | string | 覆盖 `deploy_method`（可选） |
| pre_check | bool | 是否 DSL 预检查，默认 `false` |
| expire_time | int | `run_option.expire_time`，默认 `10` |
| recycle_type | string | 默认 `short` |
| recycle_due_time | string | PPE `short` 回收截止时间（RFC3339）；不传时 agent 对 `ppe` 默认约为 14 天后 |
| debug | bool | `meta.debug`，默认 `false` |
| sync / failed_strategy | bool / string | 与 `dsl_deploy` 相同 |

### 部署类参数（dsl_create）

`dsl_create` 用于创建**全新环境**并部署服务，使用 `DSLCreate` API。仅当环境不存在时使用。

| 参数 | 类型 | 描述 | 自动补全 |
|------|------|------|----------|
| name | string | 新环境名称（必填） | — |
| psm | string | 服务 PSM（必填） | — |
| version | string | SCM 版本号，与 `branch` 二选一 | — |
| branch | string | Git 分支名，与 `version` 二选一 | — |
| service_type | string | 服务类型，默认 `tce` | — |
| zone | string | TCE zone | ✅ 从 `create_suggest` 获取 |
| idc | string | IDC 名称（支持逗号分隔多个 IDC，如 `my,my2`） | ✅ 从 `create_suggest` 获取 |
| virtual_cluster | string | 虚拟集群名称 | ✅ 从 `create_suggest` 获取 |
| cpu | float | CPU 配额 | ✅ 从 `create_suggest` 获取 |
| mem | float | 内存配额 | ✅ 从 `create_suggest` 获取 |
| count | int | 实例数量 | ✅ 从 `create_suggest` 获取 |
| cluster_name | string | 集群名称，默认 `default` | — |
| sync | bool | 是否同步等待，默认 `false` | — |
| failed_strategy | string | 失败策略，默认 `WaitBrothers` | — |

### vregion 可选值

使用 `code.byted.org/gopkg/env` 中定义的标准 VRegion 常量：

| VRegion | 说明 | StandardEnv 映射 |
|---------|------|------------------|
| `Singapore-Central` | 新加坡（默认值） | online_i18n |
| `US-East` | 美东 | online_i18n |
| `US-West` | 美西 | online_i18n |
| `China-North` | 中国北方 | online_cn |
| `China-East` | 中国华东 | online_cn |
| `EU-TTP` | 欧洲 TTP | online_euttp |
| `EU-TTP2` | 欧洲 TTP2 | online_euttp |
| `US-TTP` | 美国 TTP | online_usttp |
| `US-TTP2` | 美国 TTP2 | online_usttp |
| `US-EastRed` | 美东 Red | online_euttp |
| `China-BOE` | 中国 BOE 测试环境 | boe |
| `US-BOE` | 国际 BOE 测试环境 | boe |

> **重要**：VRegion 决定了 API 路由（通过 StandardEnv）和 JWT 鉴权类型。查询不同区域的环境时必须指定正确的 vregion。

## 输出格式

所有输出遵循统一结构：

```json
{
  "success": true,
  "action": "<action>",
  "data": { ... }
}
```

### dsl_deploy / dsl_create 输出

```json
{
  "success": true,
  "action": "dsl_deploy",
  "data": {
    "env": "ppe_my_env",
    "psm": "example.service.psm",
    "deployment_id": "1234567890",
    "status": "Pending",
    "message": ""
  }
}
```

### dsl_status 输出

```json
{
  "success": true,
  "action": "dsl_status",
  "data": {
    "deployment_id": "1234567890",
    "env": "ppe_my_env",
    "env_type": "ppe",
    "status": "success",
    "create_user": "user1",
    "create_at": "2026-01-01T00:00:00Z",
    "tickets": [
      {
        "action": "create_service",
        "type": "tce",
        "resource": "example.service.psm",
        "scope": "ppe",
        "status": "success",
        "steps": [
          {"name": "SCM compile", "status": "Jumped"},
          {"name": "Create tce service", "status": "Succeed"},
          {"name": "Create tce cluster", "status": "Succeed"}
        ]
      }
    ]
  }
}
```

## 示例

### 查询类

```bash
# 查询 PPE 环境详情（EUTTP）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "detail", "name": "ppe_my_env", "vregion": "EU-TTP"}'

# 查询 BOE 环境详情（国内）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "detail", "name": "boe_my_feature", "vregion": "China-BOE"}'

# 查询环境的服务列表
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "service_info", "name": "ppe_my_env", "vregion": "EU-TTP"}'

# 查询 PSM 在 PPE 中的集群信息
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "cluster_info", "psm": "tiktok.example.service", "scope": "ppe", "vregion": "EU-TTP"}'

# 检查用户对服务的操作权限
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "check_permission", "psm": "tiktok.example.service", "scope": "ppe", "vregion": "EU-TTP"}'

# 查询环境的 Fallback 配置
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "fallback_conf", "env_name": "ppe_my_env", "env_type": "ppe", "vregion": "EU-TTP"}'

# 查询环境实例元信息
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "instance_meta", "name": "ppe_my_env", "service_types": "tce", "vregion": "EU-TTP"}'

# 查询环境中指定服务的实例详情（含集群、SCM、调试信息）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "instance_meta", "name": "ppe_my_env", "service_types": "tce", "services": "my.service.psm", "vregion": "Singapore-Central"}'

# 获取服务部署建议（默认按 vregion 推断 IDC）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "create_suggest", "psm": "tiktok.example.service", "env": "ppe_my_env", "env_type": "ppe", "vregion": "EU-TTP"}'

# 显式指定多个 IDC，查看它们的资源建议（vregion 默认值会被覆盖）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "create_suggest", "psm": "tiktok.example.service", "vregion": "MYCOMPLIANCE", "idc": "my,my2"}'

# 获取 SCM 代码依赖
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "scm_dependencies", "psm": "tiktok.example.service", "env": "ppe_my_env", "env_type": "ppe", "vregion": "EU-TTP"}'
```

### 部署类

```bash
# 升级 TCE 服务版本（自动检测已有集群，使用 upgrade 模式）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_deploy", "name": "ppe_my_env", "psm": "tiktok.example.service", "version": "1.0.0.213", "vregion": "EU-TTP"}'

# 使用 Git 分支部署
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_deploy", "name": "ppe_my_env", "psm": "tiktok.example.service", "branch": "feature/my-branch", "vregion": "EU-TTP"}'

# 在已有环境中新建 TCE 服务（PSM 无集群时自动补全参数）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_deploy", "name": "ppe_my_env", "psm": "tiktok.new.service", "version": "1.0.0.1", "vregion": "EU-TTP"}'

# 删除环境中的服务
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_deploy", "name": "ppe_my_env", "psm": "tiktok.example.service", "deploy_action": "delete", "vregion": "EU-TTP"}'

# 部署 TCC 服务（region 必填，service_id 自动获取）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_deploy", "name": "ppe_my_env", "psm": "tiktok.example.tcc", "service_type": "tcc", "version": "1.0.0.1", "region": "EU-TTP,US-EastRed", "vregion": "EU-TTP"}'

# 部署 ByteFaaS 服务（PPE）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "faas_deploy", "name": "ppe_my_env", "psm": "tiktok.example.faas", "vregion": "EU-TTP"}'

# 指定 region/base_cluster/code revision 并开启 pre-check
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "faas_deploy", "name": "ppe_my_env", "psm": "tiktok.example.faas", "region": "eu-ttp", "base_cluster": "default", "code_revision_id": "123456", "pre_check": true, "vregion": "EU-TTP"}'

# 集群已就绪后，仅发版（对齐 faas_ppe_publish.har）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "faas_deploy", "deploy_action": "upgrade", "name": "ppe_my_env", "psm": "tiktok.example.faas", "cluster": "faas-cn-north", "vregion": "China-North"}'

# 创建全新 PPE 环境并部署 ByteFaaS 服务
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "faas_create", "name": "ppe_new_env", "psm": "tiktok.example.faas", "vregion": "EU-TTP"}'

# 创建全新 PPE 环境并部署 ByteFaaS 服务（指定 region 和 base_cluster）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "faas_create", "name": "ppe_new_env", "psm": "tiktok.example.faas", "region": "eu-ttp", "base_cluster": "faas-eu-ttp", "vregion": "EU-TTP"}'

# 创建全新环境并部署服务
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_create", "name": "ppe_new_env", "psm": "tiktok.example.service", "version": "1.0.0.1", "vregion": "EU-TTP"}'

# 删除整个环境（包含其中所有服务）
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "delete_env", "name": "ppe_my_env", "vregion": "EU-TTP"}'

# 查询部署状态
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_status", "deployment_id": "1234567890", "name": "ppe_my_env", "vregion": "EU-TTP"}'

# 重试失败的部署
gdpa-cli run env --session-id "$SESSION_ID" --input '{"action": "dsl_retry", "deployment_id": "1234567890", "name": "ppe_my_env", "vregion": "EU-TTP"}'
```

### 典型部署流程

```
1. 查询环境服务：service_info → 了解当前环境中有哪些服务
2. 部署/升级服务：dsl_deploy → 获取 deployment_id
   - 升级版本：只需 name + psm + version
   - 新建服务：只需 name + psm + version（自动补全集群参数）
   - 删除服务：name + psm + deploy_action=delete
3. 查询状态：dsl_status → 轮询直到 status 为 success 或 failure
4.（失败时）重试：dsl_retry
```

### dsl_deploy vs dsl_create vs faas_deploy vs faas_create

| | dsl_deploy | dsl_create | faas_deploy | faas_create |
|---|---|---|---|---|
| API | DSLUpdate (PUT) | DSLCreate (POST) | DSLUpdate (PUT) | DSLCreate (POST) |
| 用途 | 操作**已有环境**中的 TCE/TCC 服务 | 创建**全新环境** + TCE/TCC 服务 | 操作**已有环境**中的 ByteFaaS 服务 | 创建**全新环境** + ByteFaaS 服务 |
| 支持操作 | create/upgrade/delete 服务 | 创建环境 + 创建服务 | create/upgrade ByteFaaS | 创建环境 + 创建 ByteFaaS |
| 环境必须存在 | 是 | 否（会创建新环境） | 是 | 否（会创建新环境） |

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `action parameter is required` | 缺少 action 参数 | 添加 `action` 参数 |
| `name parameter is required` | 缺少环境名称 | 添加 `name` 参数 |
| `psm and scope parameters are required` | check_permission 缺少必填参数 | 添加 `psm` 和 `scope` 参数 |
| `deployment_id parameter is required` | dsl_status/dsl_retry 缺少部署 ID | 添加 `deployment_id` 参数 |
| `TCC deployment requires 'region' parameter` | TCC 部署未指定 region | 添加 `region` 参数 |
| `authentication failed` | JWT 获取失败 | 运行 `gdpa-cli login` 先登录 |
| `NOT_EXIST env not exists` | 环境不存在 | 检查名称拼写，或使用 `dsl_create` 创建新环境 |
| `Quota checking failed` | TCE 配额不足 | 申请更多配额，或用更小的 cpu/mem 参数 |
| `unfinished tickets` | 有未完成的部署任务 | 等待前一个部署完成后再操作 |

## 注意事项

- **vregion 为必填参数**，如果用户未指定，必须先询问用户目标区域后再执行命令，不要自行猜测或使用默认值。常见选择：I18N 用 `Singapore-Central`、国内用 `China-North`、BOE 测试用 `China-BOE` 或 `US-BOE`
- `cluster_info` 的 `scope` 默认为 `ppe`，查询 BOE 集群需要显式指定 `scope: boe`
- 环境名称通常以 `boe_` 或 `ppe_` 为前缀，`type` 参数可从前缀自动推断
- `instance_meta` 建议指定 `service_types`（如 `tce`）以获取有效数据，可通过 `services` 参数过滤指定 PSM 的实例详情（含集群部署、SCM 版本、调试状态等）
- TCC 部署时 `region` 为必填参数，格式如 `EU-TTP`、`US-EastRed`、`CN`，多个用逗号分隔
- `dsl_status` / `dsl_retry` 建议带上 `name` 参数以确保正确的 API 路由
- 部署后通过 `dsl_status` 轮询状态，status 通常为 `Pending` → `running` → `success` / `failure`
- 需要先通过 `gdpa-cli login` 登录获取认证凭据
