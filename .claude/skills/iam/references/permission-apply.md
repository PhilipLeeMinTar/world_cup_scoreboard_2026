# 权限申请（RBAC）

覆盖 `/iam/workorder/apply` 页面的权限申请流程，以及配套的资源 / owner / 用户组查询 action。

## Action 汇总

| Action | 描述 | 必填 | 可选 |
|---|---|---|---|
| `apply_permission` | 提交 RBAC 权限申请（**提交前自动去重**：命中待审批同类申请时不再重复创建，详见 [去重守卫](#去重守卫apply_permission-提交前自动检查)） | `apply_url` **或** (`role_name` + `resource_value`) | `vregion`, `user_type`, `username`, `duration`, `reason`, `resource_type`, `resource_owner_assignees`, `force` |
| `check_apply_exists` | 查询是否有同一 (resource, role, principal) 的待审批申请单 | `apply_url` **或** (`role_name` + `resource_value`) | `vregion`, `user_type`, `username` |
| `get_resource_owner` | 查询资源的审批人列表（永久 / 用户组申请前置） | `apply_url` **或** (`role_name` + `resource_value`) | `vregion`, `user_type`, `username` |
| `get_resource_info` | 查询资源元信息（名称、provider、owners、node_path、是否冻结） | `resource_value`（或 `node_id`） | `vregion`, `resource_type` |
| `list_apply_groups` | 查询当前用户可代表提交申请的 org + 自定义用户组（Mode C 获取 `username`） | - | `vregion`, `username` |

## 三种申请模式

`apply_permission` 支持三种等价输入，按优先级合并：`state 显式字段 > apply_url 解析 > 默认值`。

### Mode A — 直接粘贴 `apply_url`（最省事）

适用场景：`gdpa-cli test` / codebase agent 报错里带有申请链接，直接粘进来即可。

```bash
# 对应 test 报错：
# psm=desrpc.stability.thrift_server, method=GetItem, vregion=US-TTP,
# details: You have not permission to run this rpcCall,
# apply permission with this ticket: https://cloud-ttp-us.bytedance.net/bpm/apply?cid=806&defaultValues=...

gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "apply_permission",
  "vregion": "us-ttp",
  "apply_url": "https://cloud-ttp-us.bytedance.net/bpm/apply?cid=806&defaultValues=%7B%22node_id%22%3A1421926%2C%22auth_type%22%3A%22person_account%22%2C%22org_user%22%3A%22yuehongwei.harvey%22%2C%22service_account%22%3A%22%22%2C%22role%22%3A%5B%22ms.interface_tester.tx%22%5D%7D",
  "duration": "7d",
  "reason": "联调 desrpc.stability.thrift_server.GetItem"
}'
```

支持两种链接形式：

1. 旧版：`https://<host>/bpm/apply?cid=<cid>&defaultValues=<urlencoded-json>`
2. 新版：`https://<host>/iam/workorder/apply?resourceType=...&resourceValue=...&specifiedRoleName=...`

> `vregion` 可省略，按 URL host 自动推断（`cloud-ttp-us*` → us-ttp、`bpm-i18n*` / `tiktok-row*` → i18n 等）。推断不准时显式传 `vregion` 覆盖。

### Mode B — 显式个人 / 服务账号申请

```bash
# 个人账号（username 默认取 JWT）
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "apply_permission",
  "vregion": "us-ttp",
  "role_name": "ms.interface_tester.tx",
  "resource_value": "1421926",
  "user_type": "person_account",
  "duration": "7d",
  "reason": "联调 desrpc.stability.thrift_server.GetItem"
}'

# 服务账号
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "apply_permission",
  "vregion": "i18n",
  "role_name": "ms.interface_tester.i18n",
  "resource_value": "1421926",
  "user_type": "service_account",
  "username": "watchman",
  "duration": "24h",
  "reason": "USEastRed 调试"
}'
```

### Mode C — 以用户组 / 组织节点身份申请

```bash
# 自定义用户组（username 填 custom_group 的 uid）
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "apply_permission",
  "vregion": "us-ttp",
  "role_name": "ms.interface_tester.tx",
  "resource_value": "1421926",
  "user_type": "custom_group",
  "username": "tx_hyx0l5b1d6",
  "duration": "24h",
  "reason": "组内共享权限"
}'

# 组织（部门）节点（username 填 list_apply_groups 返回的 org_id 对应 username；通常就是部门 brn 末段）
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "apply_permission",
  "vregion": "us-ttp",
  "role_name": "ms.interface_tester.tx",
  "resource_value": "1421926",
  "user_type": "org_group",
  "username": "912144",
  "duration": "permanent",
  "reason": "部门长期需要"
}'
```

> Mode C 先调 `list_apply_groups` 枚举当前用户可代表的所有 group uid / org id，再填入 `username`。

## `user_type` 枚举

| 取值 | 别名 | 场景 |
|---|---|---|
| `person_account` | `person`, `user`, 省略 | 个人申请（自然人账号） |
| `service_account` | `sa`, `service` | 服务账号申请 |
| `custom_group` | `group` | 以自定义用户组身份申请（组内成员共享权限） |
| `org_group` | `org` | 以组织（部门）节点身份申请 |

## `duration` 枚举

默认 `7d`（与页面默认保持一致）。

| 别名 | 秒数 | 含义 |
|---|---|---|
| `1h` | 3600 | 1 小时 |
| `3h` | 10800 | 3 小时 |
| `8h` | 28800 | 8 小时 |
| `24h` / `1d` | 86400 | 1 天 |
| `3d` | 259200 | 3 天 |
| `7d` | 604800 | 1 周（默认） |
| `14d` | 1209600 | 2 周 |
| `30d` | 2592000 | 30 天 |
| `permanent` / `long` / `0` | 0 | 永久（必须由 owner 审批） |

> `duration` 也支持直接传秒数（整型或数字字符串，0 表示永久）。非法取值会在 submit 之前就返回 `INPUT-002`。

## `resource_owner_assignees` 自动补齐

1. `user_type = person_account` **且** 非永久申请（`duration != permanent`）：不需要 owner，**无需传**。
2. 其他任意组合（永久申请、service_account、custom_group、org_group）：未传时 **自动**调用 `get_resource_owner` 获取并回填，用户不需要关心。
3. 若服务端返回空 owners，申请流程会提前失败，并提示 escalate 到人工管理员（避免上送一个必挂的 request）。

## 配套查询 action

### `check_apply_exists` — 查询是否有待审批的同类申请

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "check_apply_exists",
  "vregion": "us-ttp",
  "role_name": "ms.interface_tester.tx",
  "resource_value": "1421926",
  "user_type": "person_account"
}'
# → data.exists=true 表示已有同参数工单，可直接用返回的 ticket_url 追审批，而非重复提交
```

> 从 v0.3.1 起 `apply_permission` 在提交前会自动做同样的去重检查（见 [去重守卫](#去重守卫apply_permission-提交前自动检查)），因此绝大部分情况 **不需要** 先手动调这个 action；只在需要探测是否有待审批工单（但不打算立刻提交）的查询场景下才需要单独调用。

### `get_resource_owner` — 查询资源 owner（永久 / 组申请的审批人）

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "get_resource_owner",
  "vregion": "us-ttp",
  "role_name": "ms.interface_tester.tx",
  "resource_value": "1421926",
  "user_type": "custom_group",
  "username": "tx_hyx0l5b1d6"
}'
```

### `get_resource_info` — 查询资源元信息

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "get_resource_info",
  "vregion": "us-ttp",
  "resource_value": "1421926"
}'
# → data.owners = ["laihongquan"], data.disable_permission_apply = false, ...
```

### `list_apply_groups` — 查询我可以代表申请的 org + 用户组

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "list_apply_groups",
  "vregion": "us-ttp"
}'
# → data.org_id / data.org_name_display + data.custom_groups: [{uid, name}, ...]
```

## 去重守卫（`apply_permission` 提交前自动检查）

`apply_permission` 在提交前会先调用 `ExistApply`（与 `check_apply_exists` 同一接口），若控制面已有同 `(resource_type, resource_value, user_type, username, role_name)` 五元组的 **待审批** 工单，则**直接返回已有工单，不再创建新单**。

目的：用户在 `test run` 失败时经常连续多次调用 `apply_permission`，原先每次都会创建一张新的同内容工单，导致审批人（通常就是 `laihongquan` 等资源 owner）收到一堆重复消息。新逻辑下第 2 次以后的调用会直接命中同一个 pending ticket。

### 返回 `already_exists: true` 的结构

```json
{
  "success": true,
  "action": "apply_permission",
  "vregion": "US-TTP",
  "data": {
    "already_exists": true,
    "ticket_id": "7631565162104800270",
    "url": "https://cloud-ttp-us.bytedance.net/cloud_ticket/apply/detail/7631565162104800270/drawer?isNew=1",
    "role_name": "ms.interface_tester.tx",
    "resource_type": "node_id",
    "resource_value": "1421926",
    "user_type": "person_account",
    "username": "yuehongwei.harvey",
    "reason": "联调 desrpc.stability.thrift_server.GetItem",
    "home_vregion": "US-TTP",
    "home_vregion_alias": "us-ttp",
    "message": "A pending apply ticket already exists for this (resource, role, principal). Pass force=true to submit anyway."
  }
}
```

字段要点：

- `already_exists`：布尔，区分是命中去重（`true`）还是刚提交的新工单（`false`）。
- `ticket_id`：从 `url` 路径里提取的字符串形式工单号，保证精度；可以直接继续链 `get_ticket` / `cancel_ticket`。
- `bpm_id`：去重路径下 **不返回**（`ExistApply` 不返回该字段）。需要 int 型 id 时请用 `get_ticket` 取。
- `home_vregion_alias`：与新建路径语义一致，用来给下游 action 选对子区域。

### 绕过去重重新提交（`force: true`）

当已有工单被驳回 / 取消 / 过期，或你确实想再提交一份时，显式传 `"force": true`：

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "apply_permission",
  "vregion": "us-ttp",
  "apply_url": "https://cloud-ttp-us.bytedance.net/bpm/apply?cid=806&defaultValues=...",
  "duration": "7d",
  "reason": "原工单已被取消，重新提交",
  "force": true
}'
```

> 绝大部分场景**不要**手动加 `force`。正确的做法是先用 `check_apply_exists` / `get_ticket` 看已有工单的状态：如果是 pending 就去催审批，如果是已取消 / 过期再带 `force: true` 重提。

## 返回结果（apply_permission）

新建工单（未命中去重）：

```json
{
  "success": true,
  "action": "apply_permission",
  "vregion": "US-East",
  "data": {
    "already_exists": false,
    "bpm_id": 7631425525378040000,
    "ticket_id": "7631425525378040848",
    "url": "https://cloud-i18n.bytedance.net/cloud_ticket/apply/detail/7631425525378040848/drawer?isNew=1&x-resource-account=i18n&x-bc-vregion=Singapore-Central",
    "home_vregion": "Singapore-Central",
    "home_vregion_alias": "i18n-sg",
    "result": true,
    "role_name": "argos.streamlog_viewer.i18n",
    "resource_type": "psm",
    "resource_value": "tiktok.nlb.migrate",
    "user_type": "person_account",
    "username": "yuehongwei.harvey",
    "principal": "brn::iam:::person_account:yuehongwei.harvey",
    "auth_duration": 604800,
    "auth_duration_label": "7d",
    "request_key": "permission-apply"
  }
}
```

链路建议：

- 用 `already_exists` 做分支：`true` 走催审批流程，`false` 才是真正的新 submit。
- `ticket_id`（string）与 `bpm_id`（int64）内容一致，前者用于安全地链到下游 `get_ticket` / `cancel_ticket`，避免 JSON number 精度丢失。
- `home_vregion_alias` 会告诉你这张工单实际落在哪个子区域（目前只有 i18n 有子区域分片）。后续 `get_ticket` / `cancel_ticket` 请用这个 alias，别沿用 apply 用的 `vregion`，否则会命中 `1000030003: ticket not found`。
