# 工单操作（Cloud Ticket）

覆盖 `/cloud_ticket/apply/detail/<id>` 页面及"我的工单"列表页的查询 / 撤销能力。

## Action 汇总

| Action | 描述 | 必填 | 可选 |
|---|---|---|---|
| `get_ticket` | 查询工单详情（对应 `/cloud_ticket/apply/detail/<id>/drawer` 弹窗数据） | `ticket_id` **或** `bpm_id` **或** `url` | `vregion`, `flow_type` |
| `list_tickets` | 查询工单列表，支持三种 scope（我发起的 / 待我审批 / 全部） | - | `vregion`, `scope`, `start_time`, `end_time`, `page`, `page_size`, `ticket_status` |
| `cancel_ticket` | 撤销待审批工单（对应页面右上角"撤销"按钮） | `ticket_id` **或** `bpm_id` **或** `url` | `vregion`, `flow_type` |

## `scope` 枚举（list_tickets）

默认 `mine`。

| 取值 | 别名 | 对应页面 Tab | 对应后端接口 |
|---|---|---|---|
| `mine` | `my`, `created`, `created_by_me`, `apply`, `apply_list`, `我发起的` | 我发起的 | `/cloud_ticket/apply/list` |
| `pending` | `audit`, `to_audit`, `to_review`, `wait_audit`, `审批`, `待我审批` | 待我审批 | `/cloud_ticket/audit/list` |
| `all` | `notice`, `cc`, `全部` | 全部 | `/cloud_ticket/notice/list` |

## 时间窗与分页

| 参数 | 默认值 | 说明 |
|---|---|---|
| `start_time` | 180 天前 | unix 秒 |
| `end_time` | now | unix 秒 |
| `page` | `1` | 1-based |
| `page_size` | `10` | 单页数量 |
| `ticket_status` | 不传 | 仅对 `pending` scope 有意义；页面默认会传 `3` |

## VRegion / sub-region 路由

| Alias | 解析为 | Ticket 网关 host | 说明 |
|---|---|---|---|
| `cn`（默认） | `China-North` | `cloud.bytedance.net` | - |
| `us-ttp` | `US-TTP` | `cloud.tiktok-us.net` | - |
| `eu-ttp` | `EU-TTP` | `bc-iedt-gw.tiktok-eu.net` | - |
| `i18n` / `us-east` / `i18n-use` | `US-East`（i18n 子区域） | `bc-maliva-gw.tiktok-row.net` | 默认 i18n 子区域 |
| `i18n-sg` / `sg` / `singapore` / `singapore-central` | `Singapore-Central`（i18n 子区域） | `cloud-sg.tiktok-row.net` | 新加坡子区域 |

i18n 控制面在前端右上角有"美国东部 / 新加坡中部"的子区域切换器（见 `iam-ticketlist-i18n-cloud.tiktok-row.net.har`）。工单存储按子区域分片，**只能在对应的子区域网关上查询 / 撤销**：

- `apply_permission` 入口统一打 `cloud.tiktok-row.net`，结果中的 `home_vregion_alias` 会告诉你这张工单真正的子区域（例如 `i18n-sg`）。
- `get_ticket` / `cancel_ticket` / `list_tickets` 必须带上对应子区域的 alias，否则后端会返回 `status_code=1000030003: ticket not found`（错区域查不到）。
- `list_tickets` 在两个子区域会返回不同的工单集合（不会 merge），需要时请分别请求。

```bash
# apply（i18n 入口）
gdpa-cli run iam --input '{"action":"apply_permission","vregion":"i18n","resource_type":"psm","resource_value":"...","role_name":"..."}'
# → data.home_vregion_alias == "i18n-sg"

# 用 home_vregion_alias 继续操作
gdpa-cli run iam --input '{"action":"get_ticket","vregion":"i18n-sg","ticket_id":"<bpm_id>"}'
gdpa-cli run iam --input '{"action":"cancel_ticket","vregion":"i18n-sg","ticket_id":"<bpm_id>"}'
```

## `ticket_id` 接受的形式

`get_ticket` / `cancel_ticket` 的 `ticket_id` 字段对以下输入都正确处理：

1. 纯数字 id：`"7631182889505358861"`
2. `apply_permission` 返回的 `bpm_id`（int64 / string 都可）
3. 工单详情页 URL：`https://cloud-ttp-us.bytedance.net/cloud_ticket/apply/detail/7631182889505358861/drawer?isNew=1`
4. 带 `?ticket_id=...` 的 URL

## 示例

### 查询工单详情

```bash
# 直接用 bpm_id / ticket_id
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "get_ticket",
  "vregion": "us-ttp",
  "ticket_id": "7631182889505358861"
}'

# 或粘贴工单详情页 URL
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "get_ticket",
  "vregion": "us-ttp",
  "ticket_id": "https://cloud-ttp-us.bytedance.net/cloud_ticket/apply/detail/7631182889505358861/drawer?isNew=1"
}'
# → data.ticket_id / data.audit_status / data.can_cancel / data.flow_info.cur_nodes / data.params
```

### 查询工单列表

```bash
# 我发起的（默认 scope）
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "list_tickets",
  "vregion": "us-ttp"
}'

# 待我审批
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "list_tickets",
  "vregion": "us-ttp",
  "scope": "pending"
}'

# 全部 + 分页
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "list_tickets",
  "vregion": "us-ttp",
  "scope": "all",
  "page": 1,
  "page_size": 20
}'
# → data.scope / data.total / data.tickets: [{ticket_id, status_name, current_node, detail_url, ...}]
```

### 撤销工单

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "cancel_ticket",
  "vregion": "us-ttp",
  "ticket_id": "7631182889505358861"
}'
# → data.cancelled=true 表示已撤销
# 对已 Cancelled 的工单再次撤销：后端当前返回 status_code=0（幂等成功），agent 如实透传
```

## 典型链路（apply → get → list → cancel → get）

1. `apply_permission` 返回 `{ already_exists, ticket_id, url, ...}`。新建工单还会带 `bpm_id`；命中去重（`already_exists: true`）只返回 `ticket_id` / `url`，因为此时 ExistApply 不提供 `bpm_id`。
2. 用 `ticket_id`（string）或 `url` 调 `get_ticket`，检查 `audit_status` / `can_cancel`
3. 用 `list_tickets` 定位同批工单或查进度
4. 发现需要放弃 → `cancel_ticket`
5. 再调 `get_ticket` 确认 `audit_status = 7`（cancelled）且 `can_cancel = false`

> 全链路建议透传 `ticket_id`（string）而非 `bpm_id`（int64），避免上层框架把 JSON number 转 float64 造成精度丢失（19 位的 Snowflake id 已经超过 2^53）。
