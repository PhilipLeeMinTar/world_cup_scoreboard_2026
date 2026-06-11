# meego-manage · update 详解

`action=update` 的完整使用文档。先读 `SKILL.md` 拿全局参数表与本地配置约定。

更新工作项时，**禁止在首次调用中传入 `confirm_update=true`**。必须严格执行以下两步流程：

## Step 1: 获取更新预览（必须先执行）

调用时传入 `work_item_id` + `update_fields`，**不传 `confirm_update`**：

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action": "update",
  "work_item_id": 6921539228,
  "update_fields": [
    {"field_key": "priority", "field_value": "1"}
  ]
}'
```

Agent 会返回 `update_suggestion`（`needs_confirmation=true`），包含每个字段的 **当前值 → 拟更新值** 对比。**你必须将此对比展示给用户，并明确询问用户是否确认更新。**

> 注意：单选字段（如 `priority`）的 `field_value` 必须传选项的 **value**（如 `"0"`、`"1"`），不是 label（如 `"P0"`、`"P1"`）。详见下方「字段值格式说明」。

## Step 2: 用户确认后执行更新

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action": "update",
  "work_item_id": 6921539228,
  "confirm_update": true,
  "update_fields": [
    {"field_key": "priority", "field_value": "1"}
  ]
}'
```

## 字段值格式说明

- **文本字段**（text）：`field_value` 直接传字符串值
- **单选字段**（select）：`field_value` 传选项的 value（如 `"0"`、`"1"`），非 label
- **角色人员字段**（role_owners）：覆盖更新，`field_value` 为 JSON 数组，如 `[{"role":"rd","owners":["user_key"]}]`
- **日期字段**（date）：`field_value` 传毫秒时间戳（如 `1646409600000`）
- **不支持**：模版字段、投票字段、计算字段
