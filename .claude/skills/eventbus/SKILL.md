---
name: eventbus
description: Query, search, and publish EventBus messages — search event messages, view partition info, or send messages to events. Use whenever the user wants to search EventBus messages, check event partitions, debug event-driven services, send a test message to an event, or mentions EventBus / event messages / event-driven messaging. Also trigger when investigating message delivery issues, checking message content for a specific event, or verifying event message flow between services.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# EventBus Agent

Query, search, and publish EventBus messages for event-driven services.

> **When to Use**: Search event messages, view partition info, send messages to events, or debug EventBus message flow.

## Quick Start

```bash
# Browse latest messages (default storage)
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.servarch.desrpc_event"
}'

# Browse latest messages from PPE storage
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "storage_type": "ppe"
}'

# Search by time range
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 0,
  "start_time": 1776236108331,
  "end_time": 1776239708331
}'

# Search by message key
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 2,
  "msg_key": "1729437769145878051"
}'

# Get partition info for an event
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "sorted_partitions",
  "event_name": "tiktok.servarch.desrpc_event"
}'

# Step 1: Preview a message (dry run, won't actually send)
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "bind_msg",
  "event_name": "tiktok.servarch.desrpc_event",
  "ppe": "ppe_xxx",
  "key": "test_key",
  "tag": "test",
  "message": "{\"hello\":\"world\"}",
  "dc": "my",
  "mq_type": "rocketmq",
  "topic": "eb_tiktok_servarch_desrpc_event",
  "mq_cluster": "web_common"
}'

# Step 2: Confirm and send (add "confirm": true)
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "bind_msg",
  "event_name": "tiktok.servarch.desrpc_event",
  "ppe": "ppe_xxx",
  "key": "test_key",
  "tag": "test",
  "message": "{\"hello\":\"world\"}",
  "dc": "my",
  "mq_type": "rocketmq",
  "topic": "eb_tiktok_servarch_desrpc_event",
  "mq_cluster": "web_common",
  "confirm": true
}'
```

## Input Parameters

### Common (all actions)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | Yes | - | Action to perform: `search_msgs`, `sorted_partitions`, `bind_msg` |
| `event_name` | string | Yes | - | EventBus event name (e.g. `tiktok.servarch.desrpc_event`) |
| `vregion` | string | No | `Singapore-Central` | VRegion: `Singapore-Central`, `US-East`, `US-BOE`. Aliases: `sg`, `us`, `boei18n` |

### search_msgs — Search Event Messages

Supports 6 search types for flexible message discovery.

#### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_size` | int | `10` | Number of messages per page |
| `page_index` | int | `0` | Page index (0-based) |
| `search_type` | int | `5` | Search type (see below) |
| `storage_type` | string | `"default"` | Storage type: `"default"` (online) or `"ppe"` (PPE environment) |

#### Search Types

| search_type | Name | Description | Required Parameters |
|-------------|------|-------------|---------------------|
| `5` (default) | Preview | Browse latest messages (auto-fetches partitions) | `preview_num`, `preview_type` |
| `0` | Time Range | Search messages within a time window | `start_time`, `end_time` |
| `1` | Offset | Search by partition offset range | `partition`, `start_offset`, `end_offset` |
| `2` | Message Key | Search by message key | `msg_key`, `start_time`, `end_time` |
| `3` | Message ID | Search by EventBus message ID | `msg_id`, `start_time`, `end_time` |
| `4` | Search Key | Search by search key | `search_key`, `start_time`, `end_time` |

#### Type-Specific Parameters

| Parameter | Type | Used By | Description |
|-----------|------|---------|-------------|
| `preview_num` | int | type 5 | Number of preview items (default 1) |
| `preview_type` | int | type 5 | Preview type (default 0) |
| `start_time` | int | type 0,2,3,4 | Start time in milliseconds (default: 1 hour ago) |
| `end_time` | int | type 0,2,3,4 | End time in milliseconds (default: now) |
| `partition` | string | type 1 | Partition name (e.g. `"rmq_test_new_boei18n7:0"`) |
| `start_offset` | int | type 1 | Start offset in partition |
| `end_offset` | int | type 1 | End offset in partition |
| `msg_key` | string | type 2 | Message key to search for |
| `msg_id` | string | type 3 | EventBus message ID (UUID) |
| `search_key` | string | type 4 | Search key value |
| `rmq_key_count` | int | type 2,3 | RMQ key count (default 32) |

### sorted_partitions — Query Event Partitions

No additional parameters beyond `event_name` and `vregion`.

### bind_msg — Send Message to Event (PPE Only, Human Confirmation Required)

Messages can **only** be sent to PPE environments. The `ppe` parameter is required.

#### Mandatory two-step human confirmation workflow

When the user asks you to send an EventBus message, you MUST follow this workflow — do NOT skip any step:

1. **Preview first**: Call `bind_msg` WITHOUT `confirm` (or with `confirm: false`). This returns a preview of the constructed message without sending it.
2. **Show the preview to the user**: Present the full preview result (event_name, ppe, key, tag, message body, etc.) to the user in a readable format. Explicitly ask the user to confirm whether this is correct and whether they want to proceed.
3. **Wait for the user's explicit confirmation**: Do NOT proceed until the user explicitly says yes/confirm/ok/send/确认/发送 or similar.
4. **Send with confirmation**: Only after the user confirms, call `bind_msg` again with the same parameters plus `"confirm": true` to actually send the message.

If the user says no/cancel/取消 or wants to modify, do NOT send — help them adjust the parameters and repeat from step 1.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ppe` | string | **Yes** | PPE environment name (e.g. `ppe_xxx`) — **must be specified** |
| `key` | string | **Yes** | Message key |
| `message` | string | **Yes** | Message body (JSON string) |
| `confirm` | bool | No | Set to `true` to actually send. Default: `false` (preview only) |
| `tag` | string | No | Message tag |
| `dc` | string | No | Datacenter (e.g. `my`, `sg`) |
| `raw_schema` | string | No | Message schema (JSON string) |
| `entry` | string | No | Entry point |
| `msg_type` | int | No | Message type (default 0) |
| `mq_type` | string | No | MQ type (e.g. `rocketmq`) |
| `topic` | string | No | MQ topic (e.g. `eb_tiktok_servarch_desrpc_event`) |
| `mq_cluster` | string | No | MQ cluster (e.g. `web_common`) |

## VRegion Mapping

| VRegion | Aliases | API Region | Gateway |
|---------|---------|------------|---------|
| `Singapore-Central` (default) | `sg` | SGALI | cloud.tiktok-row.net |
| `US-East` | `us`, `i18n` | MVAALI | cloud.tiktok-row.net |
| `US-BOE` | `boei18n`, `boe-i18n` | BOEI18N | cloud-boei18n.bytedance.net |

## Output Format

### search_msgs

```json
{
  "success": true,
  "action": "search_msgs",
  "event_name": "tiktok.servarch.desrpc_event",
  "data": {
    "event_name": "tiktok.servarch.desrpc_event",
    "region": "SGALI",
    "total": 1,
    "page_index": 0,
    "page_size": 10,
    "messages": [
      {
        "msg_id": "9126282a-...",
        "msg_key": "2",
        "tag": "test",
        "env": "ppe_lhq",
        "partition": "web_common_my182:0",
        "offset": 0,
        "born_time": 1772451559049,
        "born_time_str": "2026-03-02T11:39:19+08:00",
        "body": "{...}",
        "header": {
          "event_name": "tiktok.servarch.desrpc_event",
          "born_region": "ALISG",
          "psm": "ies.eventbus.console"
        }
      }
    ]
  }
}
```

### sorted_partitions

```json
{
  "success": true,
  "action": "sorted_partitions",
  "event_name": "tiktok.servarch.desrpc_event",
  "data": {
    "event_name": "tiktok.servarch.desrpc_event",
    "region": "SGALI",
    "partition_count": 3,
    "oldest_time": 1772445164235,
    "oldest_time_str": "2026-03-02T09:52:44+08:00",
    "partitions": [
      {
        "storage_descriptor": 4,
        "partition": "web_common_my182:0",
        "oldest_offset": 0,
        "newest_offset": 5
      }
    ]
  }
}
```

### bind_msg (preview mode, default)

```json
{
  "success": true,
  "action": "bind_msg",
  "event_name": "tiktok.servarch.desrpc_event",
  "data": {
    "status": "preview",
    "confirmed": false,
    "event_name": "tiktok.servarch.desrpc_event",
    "ppe": "ppe_xxx",
    "region": "SGALI",
    "key": "test_key",
    "tag": "test",
    "message": "{\"hello\":\"world\"}",
    "hint": "This is a preview. Add \"confirm\": true to your input to actually send the message."
  }
}
```

### bind_msg (confirmed, message sent)

```json
{
  "success": true,
  "action": "bind_msg",
  "event_name": "tiktok.servarch.desrpc_event",
  "data": {
    "event_name": "tiktok.servarch.desrpc_event",
    "code": 0,
    "msg": "success",
    "message": "success"
  }
}
```

## Examples

### Preview Latest Messages (default, search_type=5)

```bash
# Default storage
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{"action": "search_msgs", "event_name": "tiktok.servarch.desrpc_event", "vregion": "sg"}'

# PPE storage
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{"action": "search_msgs", "event_name": "tiktok.ecom.stock.change", "vregion": "boei18n", "storage_type": "ppe"}'
```

### Search by Time Range (search_type=0)

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 0,
  "start_time": 1776236108331,
  "end_time": 1776239708331,
  "storage_type": "default"
}'
```

### Search by Offset (search_type=1)

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 1,
  "partition": "rmq_test_new_boei18n7:0",
  "start_offset": 54809270,
  "end_offset": 54813234,
  "storage_type": "default"
}'
```

### Search by Message Key (search_type=2)

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 2,
  "msg_key": "1729437769145878051",
  "start_time": 1776236172775,
  "end_time": 1776239772775,
  "storage_type": "default"
}'
```

### Search by Message ID (search_type=3)

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 3,
  "msg_id": "bfdae9dc-f77d-475f-9e69-d09f349e2fb9",
  "start_time": 1776236271374,
  "end_time": 1776239871374,
  "storage_type": "default"
}'
```

### Search by Search Key (search_type=4)

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "search_msgs",
  "event_name": "tiktok.ecom.stock.change",
  "vregion": "boei18n",
  "search_type": 4,
  "search_key": "1729437769145878051",
  "start_time": 1776236219923,
  "end_time": 1776239819923,
  "storage_type": "ppe"
}'
```

### Query Partitions

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{"action": "sorted_partitions", "event_name": "tiktok.servarch.desrpc_event"}'
```

### Send a Test Message (Two Steps)

Step 1 — Preview (review the constructed message):

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "bind_msg",
  "event_name": "tiktok.servarch.desrpc_event",
  "ppe": "ppe_xxx",
  "key": "test_key_1",
  "tag": "test",
  "message": "{\"data\":\"test payload\"}",
  "dc": "my",
  "mq_type": "rocketmq",
  "topic": "eb_tiktok_servarch_desrpc_event",
  "mq_cluster": "web_common"
}'
```

Step 2 — Confirm and send (add `confirm: true`):

```bash
gdpa-cli run eventbus --session-id "$SESSION_ID" --input '{
  "action": "bind_msg",
  "event_name": "tiktok.servarch.desrpc_event",
  "ppe": "ppe_xxx",
  "key": "test_key_1",
  "tag": "test",
  "message": "{\"data\":\"test payload\"}",
  "dc": "my",
  "mq_type": "rocketmq",
  "topic": "eb_tiktok_servarch_desrpc_event",
  "mq_cluster": "web_common",
  "confirm": true
}'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `event_name parameter is required` | Missing event name | Add `event_name` parameter |
| `no partitions found for event` | Event doesn't exist or has no partitions in this region | Check event name and vregion |
| `authentication failed` | JWT token issue | Run `gdpa-cli login i18n` to refresh |
| `ppe parameter is required` | Missing PPE for bind_msg | `bind_msg` only supports PPE — add `ppe` parameter |
| `BindMsg API error` | Message send failure | Check required fields (key, message, dc, mq_type, topic, mq_cluster) |
| `vregion not supported` | Using unsupported region | Use `Singapore-Central`, `US-East`, or `US-BOE` |

## Notes

- **Default Region**: Defaults to Singapore-Central; use `vregion` to switch (supports `Singapore-Central`, `US-East`, `US-BOE`)
- **Storage Type**: Use `storage_type` to specify storage: `"default"` (online, default) or `"ppe"` (PPE environment). For preview search (type 5), partitions are automatically filtered by storage type.
- **Search Auto-Discovery**: Preview search (type 5) automatically fetches partitions — no need to call `sorted_partitions` first
- **Default Time Range**: For time-based searches (types 0, 2, 3, 4), if `start_time`/`end_time` are not provided, defaults to the last 1 hour
- **PPE Only**: `bind_msg` only supports sending to PPE environments — the `ppe` parameter is required
- **Human Confirmation Required**: When sending messages via `bind_msg`, you must first preview (without `confirm`), show the result to the user, wait for their explicit confirmation, and only then call again with `confirm: true`. Never send a message without showing the preview to the user first and receiving their approval.
- **Message Body**: For `bind_msg`, the `message` field should be a JSON string
