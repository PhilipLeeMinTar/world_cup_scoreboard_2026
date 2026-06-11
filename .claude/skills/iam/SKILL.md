---
name: iam
description: Manage ByteCloud IAM custom user groups, search users, inspect "my permissions" (the /iam/mine/role/list page), request missing RBAC permissions (the /iam/workorder/apply page), and operate cloud ticket workflow (query ticket detail, list my / to-audit / all tickets, cancel pending ticket) across CN, I18N, US-TTP, and EU-TTP control planes. Use whenever the user wants to create a user group, add or remove members or admins, inspect a custom group, list group members, search usernames, list their own IAM roles / resources / role bindings, apply for a missing RBAC permission (person / service_account / custom_group / org_group), check for an existing pending apply ticket, look up resource owners or metadata, list the org + custom groups the current user can apply on behalf of, fetch the detail of a cloud ticket, list my cloud tickets (我发起的 / 待我审批 / 全部 tabs), cancel a pending cloud ticket, or operate IAM in cloud.bytedance.net, cloud.tiktok-row.net, cloud.tiktok-us.net, or EU-TTP control planes.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# IAM 用户组管理 & 权限申请 & 工单操作

管理 ByteCloud IAM 自定义用户组，支持建组 / 成员 / 管理员、用户搜索、**一键申请 RBAC 权限**，以及工单详情 / 列表 / 撤销等工单流全链路操作。

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{"action":"create_group","vregion":"cn","name":"gdpa_skill_dev"}'
```

## Action 索引（按场景分类）

| 场景 | Action | 详细文档 |
|---|---|---|
| 用户组管理 | `list_groups` / `list_all_groups` / `create_group` / `get_group_summary` / `list_group_members` | `references/groups.md` |
| 用户组成员增删 | `add_members` / `add_admins` / `remove_members` / `remove_admins` | `references/groups.md` |
| 用户查询 | `search_users` / `get_users_by_usernames` | `references/groups.md` |
| 查看我的授权 | `list_my_roles` | `references/my-roles.md` |
| 权限申请（三种模式，提交前自动去重） | `apply_permission` | `references/permission-apply.md` |
| 申请前置 / 查询 | `check_apply_exists` / `get_resource_owner` / `get_resource_info` / `list_apply_groups` | `references/permission-apply.md` |
| 工单查询 | `get_ticket` / `list_tickets` | `references/tickets.md` |
| 工单撤销 | `cancel_ticket` | `references/tickets.md` |

## 路由：按 action 决定加载哪个 reference

模型应根据用户意图先选定 `action`，再加载对应文档：

| 想做的事 | 必读文件 |
|---|---|
| 建 / 查 / 改用户组，增删成员，搜用户 | `references/groups.md` |
| 看我自己在某站点有哪些 IAM 授权 | `references/my-roles.md` |
| 申请权限（个人 / 服务账号 / 用户组 / 组织节点），查是否有同类待审申请，查资源 owner / 元信息，查我可代表的 org + 用户组 | `references/permission-apply.md` |
| 查工单详情 / 列表（我发起的 / 待我审批 / 全部），撤销工单 | `references/tickets.md` |

> reference 文件在 skill 安装时已一并复制到本目录。请直接 `read ./references/<name>.md`，不要再尝试重新拉取。

## 共享约定（所有 action 通用）

### 区域 / 站点

1. 区域参数同时接受 `vregion` 和 `region`。
2. `vregion` 仅支持以下取值：
   - `cn`（`cloud.bytedance.net`）
   - `i18n`（`cloud.tiktok-row.net` 入口；cloud_ticket 子区域 = US-East，host `bc-maliva-gw.tiktok-row.net`）
   - `i18n-sg` / `sg` / `singapore`（i18n Singapore-Central 子区域，host `cloud-sg.tiktok-row.net`）
   - `us-ttp`（`cloud-ttp-us.bytedance.net` / `cloud.tiktok-us.net`）
   - `eu-ttp`（EU TTP 控制面）
3. 粘贴 URL 的 action（`apply_permission` / `check_apply_exists` / `get_resource_owner` / `get_ticket` / `cancel_ticket`）可省略 `vregion`，由 host 自动推断；推断不准时显式传入覆盖。
4. **i18n 子区域工单必须用正确的 alias**：`apply_permission` 返回 `home_vregion_alias`（`i18n` 或 `i18n-sg`），后续 `get_ticket` / `cancel_ticket` 请复用该 alias；跨子区域查询会命中 `1000030003: ticket not found`。

### 鉴权

所有 action 都用当前 session JWT 调用。默认从 `gdpa-cli login <site>` 登记的身份中取 `username`，需要代表他人 / 账号时在 input 显式传 `username`。

### 输入兼容性

1. `usernames`：支持字符串数组，也支持逗号分隔字符串。
2. `ticket_id` / `bpm_id`：接受纯数字、URL、整型、字符串四种形式，详见 `references/tickets.md`。
3. `duration`：支持枚举别名（`1h` / `24h` / `permanent` 等）或直接传秒数，详见 `references/permission-apply.md`。

## 返回结果

所有 action 统一结构：

```json
{
  "success": true,
  "action": "apply_permission",
  "vregion": "US-TTP",
  "data": { "...action 特有的结构..." }
}
```

失败时：

```json
{
  "success": false,
  "action": "apply_permission",
  "vregion": "US-TTP",
  "error": "[INPUT-001] role_name is required (pass role_name, or an apply_url that carries the role)"
}
```

每个 action 的 `data` 字段细节见对应 `references/*.md`。
