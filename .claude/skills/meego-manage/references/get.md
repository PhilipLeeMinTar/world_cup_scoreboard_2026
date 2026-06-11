# meego-manage · get 详解

`action=get` 的完整使用文档。先读 `SKILL.md` 拿全局参数表与本地配置约定。

获取一个或多个工作项的完整详情，支持选择性返回字段和扩展信息。

## 基础用法

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action": "get",
  "work_item_type_key": "story",
  "work_item_ids": [301228001]
}'
```

## 选择性字段查询（fields 参数）

支持两种模式，**不可混用**：

- **指定字段**：仅返回列出的字段。如 `["priority","role_owners"]`
- **排除字段**：以 `-` 开头排除特定字段。如 `["-priority","-role_owners"]`

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action": "get",
  "work_item_type_key": "story",
  "work_item_ids": [301228001],
  "fields": ["priority", "owner", "description"]
}'
```

## 扩展查询（expand 参数）

| expand 字段 | 类型 | 说明 |
|---|---|---|
| `need_user_detail` | bool | 返回用户详细信息（邮箱、中英文名） |
| `need_workflow` | bool | 返回工作流节点/连接信息（仅节点流工作项有效） |
| `need_multi_text` | bool | 返回富文本信息（doc_html / doc_text） |
| `need_sub_task_parent` | bool | 返回子任务的父级工作项信息 |
| `relation_fields_detail` | bool | 返回关联字段详细信息 |

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action": "get",
  "work_item_type_key": "story",
  "work_item_ids": [301228001],
  "expand": {
    "need_user_detail": true,
    "need_workflow": true,
    "need_multi_text": true
  }
}'
```

## 返回字段说明

| 字段 | 说明 |
|---|---|
| `id` / `name` / `simple_name` | 工作项基础标识 |
| `pattern` | 工作流模式：`Node`（节点流）/ `State`（状态流） |
| `status` | 当前状态（含 `state_key`、`is_archived`、`is_initial`），附带 `history` 状态变更历史 |
| `current_nodes` | 当前进行中的节点（节点流有值），含 `owners` 和 `milestone` |
| `state_times` | 各状态停留时间记录（`start_time` / `end_time`） |
| `fields` | 所有字段值列表（`field_key` / `field_type_key` / `field_value`） |
| `multi_texts` | 富文本字段内容（需 `expand.need_multi_text=true`） |
| `user_details` | 用户详情（需 `expand.need_user_detail=true`） |
| `workflow_infos` | 工作流节点与连接详情（需 `expand.need_workflow=true`） |
| `sub_task_parent_info` | 子任务父级信息（需 `expand.need_sub_task_parent=true`） |
| `_summary` | 自动提取的摘要（description / priority / assignee） |
