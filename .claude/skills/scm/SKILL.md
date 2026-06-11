---
name: scm
description: Manage SCM (Source Code Management) repository versions. Query repo info, list versions, create new releases, check version status/build logs, and diagnose build failures with AI-powered analysis.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# SCM 代码管理

> **何时使用**: 当需要管理 SCM 仓库和版本时调用此 SKILL，如查看仓库信息、获取版本列表、创建新版本、获取构建日志、查看构建问题分析与 AI 诊断等。

## 使用方法

```bash
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "<action>", ...}'
```

## 支持的 Action

| Action | 描述 | 必填参数 | 可选参数 |
|--------|------|----------|----------|
| `create_version` | 创建新的 SCM 版本 | - | branch_name, build_image, commit_hash, pub_base, repo_id, repo_name, type；默认 type=test，CN 环境下默认开启同步 VA 区域 (sync_aws) 和同步 SG 区域 (sync_oss)，TTP 默认关闭 |
| `get_repo` | 获取 SCM 仓库详情 | - | repo_id, repo_name |
| `get_version_detail` | 获取版本详情 | version | repo_id, repo_name (二选一) |
| `get_version_list` | 获取 SCM 版本列表，支持按分支、提交、创建人、类型、版本号等筛选，支持分页 | repo_id 或 repo_name | branch, commit_hash, create_user, limit, offset, page_num, page_size, scmbranch, type, version |
| `get_version_status` | 获取 SCM 版本状态 | - | repo_id, repo_name, version_id, version_number |
| `get_build_log` | 获取指定版本的构建日志 | version_number | repo_id, repo_name, step_name, limit |
| `get_build_troubleshoot` | 获取版本构建的 AI 问题诊断（错误日志分析 → 错误根因 → 解决方案，与 SCM 页面一致） | - | record_id, repo_id, repo_name, version_number |


## 输入参数

| 参数 | 类型 | 描述 |
|------|------|------|
| action | string | 必填，要执行的操作 |
| region | string | 调用区域：CN（默认）或 TTP |
| repo_id | number | 仓库唯一 ID，与 repo_name 二选一 |
| repo_name | string | **SCM 三段式仓库名**（如 `ies/gdp/openapi`、`tiktok/gdp/gemini_proxy`），注意不是 code 仓库路径，与 repo_id 二选一 |
| version_id | number | 版本唯一 ID |
| version | string | 语义版本号或版本名称（用于 get_version_detail） |
| version_number | string | 语义版本号（用于 get_build_log、get_version_status、get_build_troubleshoot） |
| record_id | string | 构建记录 ID（用于 get_build_troubleshoot；如未提供会自动从 version_number + repo 解析） |
| branch_name | string | Git 分支名称（如 main, feature/xyz） |
| commit_hash | string | Git 完整 commit hash |
| pub_base | string | 发布基准策略：branch_base（默认）或 commit_base |
| type | string | 环境类型：online、offline、test；**create_version 未填时默认为 test**，其他无默认 |
| build_image | string | 自定义构建镜像 |
| step_name | string | 构建步骤名称，默认自动根据 failed_step 或者 building 进行推测 |
| limit | number | 返回的最大条目数，默认 10 |
| page_num | number | 页码，默认 1（仅 get_version_list） |
| page_size | number | 每页条数，默认 10（仅 get_version_list） |
| offset | number | 偏移量，默认 0（仅 get_version_list） |
| create_user | string | 创建人（仅 get_version_list 筛选） |
| scmbranch | string | 分支名，与 branch 同义（仅 get_version_list 筛选） |

## 参数约束说明

### 仓库标识
大多数 action 需要标识仓库，提供以下之一即可：
- `repo_id`: 仓库唯一 ID
- `repo_name`: **SCM 三段式仓库名**（如 `ies/gdp/openapi`），注意不是 code 代码仓库路径

### 版本标识
部分 action 需要标识版本，可以通过以下方式之一：
- 仅提供 `version_id`
- 提供 `version_number` + (`repo_id` 或 `repo_name`)

### 创建版本约束
- 如果 `pub_base` 是 `branch_base`（默认），必须提供 `branch_name`
- 如果 `pub_base` 是 `commit_base`，必须提供 `commit_hash`

## 注意事项
- 需要有相应仓库的访问权限

## 示例

```bash
# 获取仓库详情
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_repo", "repo_name": "tiktok/gdp/gemini_proxy"}'

# 获取版本列表（仅 repo + limit）
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_version_list", "repo_name": "tiktok/gdp/gemini_proxy", "limit": 5}'

# 获取版本列表（按分支、提交、创建人、类型、版本号筛选 + 分页）
gdpa-cli run scm --session-id list_filter --input '{"action": "get_version_list", "repo_name": "desrpc/test/client", "commit_hash": "7d1fe28ca950d28943f565558307312576791f80", "create_user": "laihongquan", "branch": "feat/ai2d-gdpa-skill", "scmbranch": "feat/ai2d-gdpa-skill", "type": "test", "version": "1.0.1.426", "page_num": 1, "page_size": 10, "limit": 10, "offset": 0}'

# 获取版本详情
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_version_detail", "repo_name": "tiktok/gdp/gemini_proxy", "version": "1.0.0.9"}'

# 获取版本状态
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_version_status", "repo_name": "tiktok/gdp/gemini_proxy", "version_number": "1.0.0.9"}'

# 获取构建日志（默认自动推测 step，如 building 或失败的步骤）
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_build_log", "repo_name": "tiktok/gdp/gemini_proxy", "version_number": "1.0.0.9"}'

# 获取指定步骤的构建日志
# 说明：可用的 step_name（如 building、unit_test、lint_check）可通过 get_version_detail 返回数据中的 build_steps 的 keys 获知
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_build_log", "repo_name": "tiktok/gdp/gemini_proxy", "version_number": "1.0.0.9", "step_name": "unit_test"}'

# 创建新版本（从分支创建在线版本）
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "create_version", "repo_name": "tiktok/gdp/gemini_proxy", "branch_name": "feat/bits_test", "type": "test"}'

# 获取构建 AI 诊断（与 SCM 页面"问题分析"一致）
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_build_troubleshoot", "repo_name": "ies/gdp/openapi", "version_number": "1.0.0.3694"}'

# 直接通过 record_id 获取 AI 诊断
gdpa-cli run scm --session-id "$SESSION_ID" --input '{"action": "get_build_troubleshoot", "record_id": "125226641"}'
```

## 输出格式

```json
{
  "success": true,
  "action": "<action>",
  "data": { ... }
}
```
