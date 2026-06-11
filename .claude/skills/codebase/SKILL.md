---
name: codebase
description: Query and operate Codebase (code.byted.org) — repos, branches, files, commits, MRs, diffs, comments, reviewers, review status, check runs, permissions, and user statistics. Use whenever a code.byted.org URL appears (e.g. `.../merge_requests/<n>`, `.../commit/<sha>`, repo home, branch/tree path), or the user references a repo by `org/repo`, MR number, or commit SHA; also trigger on cues like MR, merge request, diff, branch, review. Prefer this over WebFetch for any code.byted.org link — the domain is internal.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# Codebase

> **何时使用**: 查询或操作 Codebase (`code.byted.org`) — 仓库、分支、文件、提交、MR、diff、评论、评审、检查结果、权限、用户统计。用户给出 `code.byted.org` URL、`org/repo` 路径、MR 编号或 commit SHA 时，优先用本 skill，不要用 WebFetch（`code.byted.org` 是内网域名）。

## 使用方法

```bash
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"<action>", ...}'
```

## 认证

认证按以下优先级自动选择（命中即停）：

| 优先级 | 方式 | 环境变量 | 说明 |
|--------|------|----------|------|
| 1 | User JWT（显式） | `CODEBASE_JWT_TOKEN` | 直接指定 Codebase UserJWT |
| 2 | User JWT（自动换取） | _无需设置_ | 自动获取 CN JWT 并换取 Codebase UserJWT |
| 3 | App 身份 | `CODEBASE_APP_ID` + `CODEBASE_APP_SECRET` | 使用 Codebase App 凭证，适合服务集成 |
| 4 | PAT | `CODEBASE_PAT_TOKEN` | 个人访问令牌，格式 `code_pat_xxx` |

默认走用户 JWT（优先级 2），无需额外设置：

```bash
# 无需额外设置，codebase 会自动获取 CN JWT 并换取 Codebase UserJWT
```

显式指定 Codebase JWT：

```bash
export CODEBASE_JWT_TOKEN=xxx
```

使用 App 身份（服务集成场景）：

```bash
export CODEBASE_APP_ID=12345
export CODEBASE_APP_SECRET=xxx
```

> App 需要在目标仓库中安装后才能访问对应资源。ZTI Token 由 SDK 自动注入，无需手动设置。
> App 创建与管理见 [Codebase App 文档](https://bytedance.larkoffice.com/wiki/EYfEwivTbiNmBhkF4Mpcfjqvnhb)。

PAT 仅作为备选方案，申请与配置方式见文末”补充说明：PAT 备选认证”。

## 支持的 Action

| Action | 描述 | 必填参数 | 可选参数 |
|--------|------|----------|----------|
| `get_self` | 获取当前登录用户信息 | - | - |
| `get_repository` | 获取仓库详情 | `id` 或 `path` | - |
| `list_repositories` | 列出**当前用户参与的**仓库（创建 / 贡献 / star 过）。要找全量公开仓库（如别的部门的项目），改用 `search_repositories` | - | query, namespace_id, contributed_by_id, starred_by_id, starred, has_wiki, statuses, sort_by, sort_order, page_number, page_size |
| `search_repositories` | **跨命名空间全局搜索**仓库，覆盖当前用户从未访问过的公开仓库（对应 code.byted.org 顶部搜索栏的能力） | - | query (= path 别名，按仓库路径子串匹配), path, namespace_name, namespace_id, contributed_by_username, contributed_by_id, starred_by_username, starred_by_id, status (`created`/`archived`), sort_by (`CreatedAt`/`UpdatedAt`), sort_order, page_number, page_size |
| `list_branches` | 查询分支列表 | `repo_id` | type, query, query_mode, commit_id, sort_by, sort_order, page_number, page_size |
| `create_branch` | 创建分支 | `repo_id`, `branch` 或 `name`, `revision` | - |
| `get_file` | 获取文件内容 | `repo_id`, `path` | revision，默认 `main` |
| `get_commit` | 获取单个提交 | `repo_id`, `revision` | - |
| `list_commits` | 获取提交列表 | `repo_id`, `revision` | path, paths, author, committed_after, committed_before, query, first_parent, page_number, page_size |
| `list_diff_files` | 获取 MR 或提交间 diff 文件 | `repo_id`，以及 `number` 或 `from_commit+to_commit` | id, merge_request_id, change_id, is_straight, raw_stat_only |
| `create_commit` | 创建提交 | `repo_id`, `branch`, `message` 或 `commit_message`, `actions` 或 `commit_files_actions` | start_branch, commit_author_name, commit_author_email |
| `create_merge_request` | 创建 MR | `repo_id` 或 `source_repo_id+target_repo_id`, `source_branch`, `target_branch`, `title` | description, merge_method, remove_source_branch_after_merge, squash_commits, merge_commit_message, squash_commit_message, reviewer_ids, work_item_ids, auto_invite_reviewers, auto_link_work_items, draft, label_ids, milestone_id |
| `get_merge_request` | 获取 MR 详情 | `repo_id`，以及 `id` / `number` / `change_id` 之一 | with_versions, with_reviewers, with_review_status, with_check_run_summary_status, with_url, with_labels |
| `update_merge_request` | 更新 MR | `repo_id`，以及 `id` 或 `number` | title, description, auto_merge, merge_method, remove_source_branch_after_merge, merge_commit_message, squash_commit_message, wip, work_item_ids, target_branch, auto_invite_reviewers, squash_commits, draft, milestone_id |
| `merge_merge_request` | 合并 MR | `repo_id`，以及 `id` 或 `number` | merge_method, remove_source_branch_after_merge, merge_commit_message, squash_commit_message, squash_commits |
| `create_merge_request_bypasses` | 创建 MR bypass | `repo_id`，以及 `merge_request_id/id` 或 `merge_request_number/number`，`inputs` | commit_id |
| `list_merge_request_bypasses` | 查询 MR bypass 列表 | `repo_id`，以及 `merge_request_id/id` 或 `merge_request_number/number` | commit_id |
| `get_merge_request_mergeability` | 查询 MR 是否可合并 | `repo_id`，以及 `id` 或 `number` | - |
| `list_repo_merge_requests` | 查询仓库 MR 列表 | `repo_id` 或 `target_repo_id` | source_branch, target_branch, since, status, author_id, author, title, commit_id, reviewer_id, reviewer, sort_by, sort_order, wip, review_status, draft, attention_user_id, attention_username, labels, milestone_ids, page_number, page_size |
| `create_comment` | 创建评论 | `content`，以及 `repo_id+number` 或 `commentable_type+commentable_id` | commit_id, thread_id, position |
| `create_draft_comment` | 创建草稿评论 | `content`，以及 `repo_id+number` 或 `commentable_type+commentable_id` | commit_id, thread_id, position |
| `create_comments` | 批量创建评论 | `comments` | draft |
| `publish_draft_comments` | 发布草稿评论 | `repo_id+number` 或 `commentable_type+commentable_id` | review_content |
| `list_threads` | 查询评论线程 | `repo_id+number` 或 `commentable_type` | commentable_id, commit_id |
| `count_user_activities_by_date` | 统计用户按日期活动量 | username, tenant_id, begin_date, end_date | - |
| `get_user_statistics` | 获取用户统计 | `relative_days` 或 `natural_year` | user_id, username |
| `get_review_status` | 获取 MR 评审状态 | `repo_id`，以及 `merge_request_id` 或 `number` | - |
| `list_review_network_statistics` | 获取评审网络统计 | - | author_id, author_username, reviewer_id, reviewer_username, top_n |
| `list_reviewers` | 获取 MR 评审人列表 | `repo_id`，以及 `merge_request_id` 或 `number` | with_meet_review_rules, with_pending_effective_approver |
| `update_reviewers` | 更新 MR 评审人 | `repo_id`，以及 `merge_request_id` 或 `number` | add_reviewers, remove_reviewers, set_reviewers |
| `search_users` | 查询用户（用户名↔ID 互查） | `usernames` 或 `user_ids` 或 `query` | page_number, page_size |
| `list_check_runs` | 获取检查结果 | `repo_id`，以及 `number` 或 `commit_id` | merge_request_id, branch, app_id, get_unfinalized_apps, page_number, page_size |
| `list_work_item_links` | 获取 MR 关联工单 | `repo_id`，以及 `merge_request_id` 或 `number` | page_number, page_size |
| `apply_repo_permission` | 申请仓库权限 | `repo_name` 或 `repo_id/path`，`reason` | permission, permission_action, role, apply_action, revision |

## 输入参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `action` | string | 必填，要执行的操作 |
| `repo_id` | string | 仓库 ID，也支持传仓库路径，如 `tiktok/gdp_gemini_proxy` |
| `path` | string | 仓库路径或文件路径，具体含义取决于 action |
| `revision` | string | 分支名、tag 或 commit SHA |
| `id` | string | 通用资源 ID，常用于仓库或 MR |
| `number` | number | MR 编号 |
| `change_id` | string | MR 关联 change id |
| `branch` | string | 分支名 |
| `source_branch` | string | MR 源分支 |
| `target_branch` | string | MR 目标分支 |
| `title` | string | 标题 |
| `description` | string | 描述 |
| `content` | string | 评论内容 |
| `commentable_type` | string | 评论对象类型，如 `merge_request` |
| `commentable_id` | string | 评论对象 ID |
| `merge_request_id` | string | MR ID |
| `merge_request_number` | number | MR 编号，`number` 的等价别名 |
| `commit_id` | string | commit SHA |
| `permission` | string | 申请权限级别，支持 `reporter` / `developer` / `master`，默认 `developer` |
| `page_number` | number | 页码，默认 1 |
| `page_size` | number | 每页大小，默认 20 |
| `with_versions` | bool | `get_merge_request` 专用，开启后响应的 `merge_request.versions` 会包含 MR 的全部 version（含 `id` / `number` / `source_commit_id` / `target_commit_id` / `base_commit_id` / `type` / `created_at`）；默认关闭以保持轻量 |
| `with_reviewers` | bool | `get_merge_request` 专用，开启后返回评审人详情 |
| `with_review_status` | bool | `get_merge_request` 专用，开启后返回评审状态摘要 |
| `with_check_run_summary_status` | bool | `get_merge_request` 专用，开启后返回 CI 检查总状态（passed / pending / failed） |
| `with_url` | bool | `get_merge_request` 专用，开启后返回 MR 的访问 URL |
| `with_labels` | bool | `get_merge_request` 专用，开启后返回 MR 关联的 labels |

## 参数约束说明

### 仓库标识

大多数 action 需要标识仓库，支持以下两种方式：

- `repo_id`: 纯数字仓库 ID
- `repo_id`: 直接传仓库路径，如 `tiktok/gdp_gemini_proxy`

### MR 标识

多数 MR 相关 action 支持以下方式之一：

- `id`
- `merge_request_id`
- `number` + `repo_id`
- `change_id` + `repo_id`

### MR bypass 动作

`create_merge_request_bypasses` 需要传 `inputs` 数组。每个元素至少包含：

- `target_type`: `review` / `app_check` / `merge_queue`
- `reason`: 可选，支持 `no_need_for_review` / `no_available_reviewer` / `emergency` / `inaccurate_conclusion` / `no_response` / `other`

其中：

- `target_type=review` 时，不需要额外 target 字段
- `target_type=merge_queue` 时，不需要额外 target 字段
- `target_type=app_check` 时，可选传 `app_id`、`app_name`、`check_run_name`

### 更新评审人动作

`update_reviewers` 支持以下操作模式（可组合使用）：

- `add_reviewers`: 添加评审人，传用户名或 ID 数组（自动识别），如 `["laihongquan", "1291316"]`
- `remove_reviewers`: 移除评审人，传用户名或 ID 数组（自动识别）
- `set_reviewers`: 覆盖设置评审人列表（对象数组），每个元素含 `reviewer_id`（可传用户名或 ID），可选 `required_approver`（bool）

### 评论动作

MR 评论场景推荐直接传：

- `repo_id`
- `number`
- `content`

不需要再显式传 `commentable_type=merge_request`。

### 创建提交动作

`create_commit` 支持以下别名：

- `message` 或 `commit_message`
- `actions` 或 `commit_files_actions`
- `file_path` 或 `path`

### 仓库权限申请动作

`apply_repo_permission` 的参数约束：

- `reason` 必填
- `permission` 默认值为 `developer`
- `permission` 支持：`reporter` / `developer` / `master`
- 当前仅支持一次申请一个仓库；agent 会自动把 `repos` 固定为单元素数组
- 由于顶层 `action` 已用于选择 agent 动作，权限级别请使用 `permission`（或其别名 `permission_action` / `role` / `apply_action`），不要复用顶层 `action`

## 示例

### 用户与仓库

```bash
# 获取当前用户
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_self"}'

# 获取仓库详情
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_repository","path":"tiktok/gdp_gemini_proxy"}'

# 查询「我的」仓库（创建 / 贡献 / star 过的；不会包含别人 namespace 下你没动过的仓库）
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_repositories","query":"gdp","page_size":10}'

# 全局搜索仓库（对应 code.byted.org 顶部搜索栏，能找到任意公开仓库）
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"search_repositories","query":"hiseek_knowledge","page_size":10}'

# 限定 namespace 下搜索
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"search_repositories","namespace_name":"ies-cs","query":"hiseek","page_size":20}'

# 翻第二页
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"search_repositories","query":"knowledge","page_size":20,"page_number":2}'
```

> **list_repositories vs search_repositories**：`list_repositories` 受 Codebase API 限制，只返回当前用户参与过的仓库；找别人 namespace 下的公开仓库（如 `ies-cs/hiseek_knowledge`）必须用 `search_repositories`。两者翻页都用 `page_number` + `page_size`，建议 `page_number` 不超过 10。

### 分支与文件

```bash
# 查询分支
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_branches","repo_id":"tiktok/gdp_gemini_proxy"}'

# 创建分支
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_branch","repo_id":"tiktok/gdp_gemini_proxy","branch":"feat/demo","revision":"master"}'

# 获取文件
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_file","repo_id":"tiktok/gdp_gemini_proxy","path":"go.mod","revision":"master"}'
```

### 提交

```bash
# 获取单个提交
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_commit","repo_id":"tiktok/gdp_gemini_proxy","revision":"98b4578f6c34e67156b27b5f163675eaeae6c865"}'

# 查询提交列表
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_commits","repo_id":"tiktok/gdp_gemini_proxy","revision":"master"}'

# 创建提交
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_commit","repo_id":"tiktok/gdp_gemini_proxy","branch":"feat/demo","message":"add smoke file","actions":[{"action":"create","file_path":"tmp/demo.md","content":"demo"}]}'
```

### MR

```bash
# 创建 MR
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_merge_request","repo_id":"tiktok/gdp_gemini_proxy","source_branch":"feat/demo","target_branch":"master","title":"demo mr","description":"demo"}'

# 获取 MR
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_merge_request","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 获取 MR 详情 + 全部 version（每次 push 形成一个 version，含 SourceCommitId / TargetCommitId / Number / Type 等）
# 配合 list_check_runs 按 commit_id 维度循环就能算「每个 version 的 CI 通过率」
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_merge_request","repo_id":"tiktok/gdp_gemini_proxy","number":7,"with_versions":true}'

# 更新 MR
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"update_merge_request","repo_id":"tiktok/gdp_gemini_proxy","number":7,"description":"updated description"}'

# 合并 MR
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"merge_merge_request","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 创建 review bypass
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_merge_request_bypasses","repo_id":"tiktok/gdp_gemini_proxy","number":7,"inputs":[{"target_type":"review","reason":"other"}]}'

# 创建 app check bypass
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_merge_request_bypasses","repo_id":"tiktok/gdp_gemini_proxy","number":7,"commit_id":"<commit_sha>","inputs":[{"target_type":"app_check","reason":"other","check_run_name":"Bits Analysis"}]}'

# 查询 bypass 列表
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_merge_request_bypasses","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 查询 MR 是否可合并
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_merge_request_mergeability","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 查询仓库 MR 列表
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_repo_merge_requests","repo_id":"tiktok/gdp_gemini_proxy","page_size":10}'

# 查询 MR diff 文件
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_diff_files","repo_id":"tiktok/gdp_gemini_proxy","number":7}'
```

### 评论与线程

```bash
# 创建评论
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_comment","repo_id":"tiktok/gdp_gemini_proxy","number":7,"content":"looks good"}'

# 创建草稿评论
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_draft_comment","repo_id":"tiktok/gdp_gemini_proxy","number":7,"content":"draft comment"}'

# 批量创建评论
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"create_comments","comments":[{"repo_id":"tiktok/gdp_gemini_proxy","number":7,"content":"comment 1"},{"repo_id":"tiktok/gdp_gemini_proxy","number":7,"content":"comment 2"}]}'

# 发布草稿评论
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"publish_draft_comments","repo_id":"tiktok/gdp_gemini_proxy","number":7,"review_content":"publish all drafts"}'

# 查询线程
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_threads","repo_id":"tiktok/gdp_gemini_proxy","number":7}'
```

### 评审与检查

```bash
# 获取评审状态
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_review_status","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 获取检查结果
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_check_runs","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 获取工单关联
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_work_item_links","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 获取评审人列表
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_reviewers","repo_id":"tiktok/gdp_gemini_proxy","number":7}'

# 添加评审人（用户名和 ID 可混用）
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"update_reviewers","repo_id":"tiktok/gdp_gemini_proxy","number":7,"add_reviewers":["zhangsan","1291316"]}'

# 移除评审人
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"update_reviewers","repo_id":"tiktok/gdp_gemini_proxy","number":7,"remove_reviewers":["zhangsan"]}'

# 设置评审人（含必选审批人标记，reviewer_id 支持传用户名或 ID）
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"update_reviewers","repo_id":"tiktok/gdp_gemini_proxy","number":7,"set_reviewers":[{"reviewer_id":"zhangsan","required_approver":true},{"reviewer_id":"1291316"}]}'

# 获取评审网络统计
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"list_review_network_statistics","author_username":"yuehongwei.harvey","top_n":10}'
```

### 权限申请

```bash
# 默认申请 developer 权限
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"apply_repo_permission","repo_name":"fuyujie.daisy/test-apply","reason":"need write access for development"}'

# 显式申请 reporter 权限
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"apply_repo_permission","repo_name":"fuyujie.daisy/test-apply","permission":"reporter","reason":"need read access for investigation"}'

# 也支持沿用 repo_id/path 形式传仓库路径
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"apply_repo_permission","repo_id":"fuyujie.daisy/test-apply","permission":"master","reason":"need release branch maintenance access"}'
```

### 用户统计

```bash
# 统计用户按日期活动量
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"count_user_activities_by_date","username":"yuehongwei.harvey","tenant_id":"0","begin_date":"2026-03-01","end_date":"2026-03-19"}'

# 获取用户统计
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"get_user_statistics","username":"yuehongwei.harvey","relative_days":30}'

# 按用户名查 ID（支持批量）
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"search_users","usernames":["laihongquan","yuehongwei.harvey"]}'

# 按 ID 反查用户名
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"search_users","user_ids":["2199877"]}'

# 简写：单个用户名查询
gdpa-cli run codebase --session-id "$SESSION_ID" --input '{"action":"search_users","query":"laihongquan"}'
```

## 输出格式

```json
{
  "success": true,
  "action": "get_repository",
  "data": { ... }
}
```

## 补充说明：PAT 备选认证

当自动用户 JWT 链路不可用时，可以使用 PAT 作为备选方案。

### 申请步骤

1. 访问 [Personal Access Token](https://code.byted.org/profile/personal_access_tokens) 页面
2. 点击创建新的 PAT，填写名称和描述
3. 设置权限范围，建议至少包含：
   - `Repo metadata`
   - `Repo contents`
   - `Merge requests`
   - `Comment`
   - `Checks`
4. 点击创建，立即保存生成的 PAT，格式为 `code_pat_xxxxxx`

### 配置方式

```bash
export CODEBASE_PAT_TOKEN=code_pat_xxxxxx
```

建议写入 `~/.bashrc` 或 `~/.zshrc`，并在不再需要时及时移除。
