# meego-manage · create 详解

`action=create` 的完整使用文档。先读 `SKILL.md` 拿全局参数表与本地配置约定，再回到这里。

## 两步流程（必须严格遵循）

创建工作项**禁止首次调用就传 `confirm_create=true`**。流程是：先预览取字段元数据 → 用户确认 → 再 confirm 创建。

### Step 1: 获取字段元数据（必须先执行）

只传 `action=create` + `work_item_type_key` + `name`：

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action":"create",
  "work_item_type_key":"issue",
  "name":"example issue"
}'
```

Agent 调用「获取创建工作项元数据」接口，返回 `create_meta`（`needs_confirmation=true`），包含工作项类型在页面布局中配置的所有字段。

### 优先读 `create_meta.summary`

完整的 `field_configs` / `template_options` / `local_template.candidates` 加起来很容易上千行（story 类型常见），不要再用 `python/jq` 切片。Agent 默认输出 **compact 预览** + **顶层 summary**：

| summary 字段 | 说明 |
|---|---|
| `required_field_keys` / `conditional_required_keys` | 只列 key，不带枚举/默认值 |
| `missing_required_field_keys` | 当前还差哪些必填 |
| `supplied_field_keys` | 你这次传进去的 field_value_pairs |
| `template_options` | `[{label, template_id}]` 精简版（细节看 `create_meta.template_options`） |
| `effective_template_id` / `template_options_count` | 是否已经选定模板 |
| `local_template.status` | `none` / `bootstrap_available` / `loaded` |
| `local_template.top_candidate` | 最推荐的 bootstrap 种子（`work_item_id` + `same_template`） |
| `local_template.template_mismatch` | 本地模板与目标 template_id 不一致时为 `true` |
| `next_action_hint` | 一句话告诉你下一步该传什么参数（step1 选模板 / step2a bootstrap / step2b 补字段 / step3 confirm_create） |

想看完整字段元信息时再传 `verbose=true`（compact 模式默认 `field_configs` 只保留：`is_required=1/3` + 用户已传 + 有历史值的字段；select 类 `options` 截断到前 12 条，超出时附带 `options_truncated=true` 与 `options_total`）。如果只是想浏览整套字段定义，更推荐 `action=fields` 单独取。

### 解读 Step 1 返回的建议顺序

1. **先看 `summary.next_action_hint`**：照着提示直接给出下一次入参。
2. 看 `summary.template_options` → 让用户选一个 `template_id`（如果还未选）。
3. 看 `summary.local_template`：
   - `status=loaded` → 不用做任何事，本地模板已注入；如果 `template_mismatch=true` 还要提示用户。
   - `status=bootstrap_available` → 把 `top_candidate.work_item_id` 推给用户（带上 `same_template` 标识），让用户决定是否用它 bootstrap。
   - `status=none` → 没有可参考的历史，只能逐字段问用户。
4. 看 `summary.missing_required_field_keys`：把这些 key 对应的 `field_configs[i]`（含 `options`）展示给用户填值。
5. 仅在 `verbose=true` 或用户明确要看全量字段时，才解读 `field_configs` / `missing_required_fields` 完整结构。
6. 最后调用 `confirm_create=true` 真正创建。

### Step 2: 用户确认后执行创建

```bash
gdpa-cli run meego-manage --session-id "$SESSION_ID" --input '{
  "action":"create",
  "work_item_type_key":"issue",
  "name":"example issue",
  "confirm_create": true,
  "field_value_pairs": [
    {"field_key":"priority","field_value":"1"}
  ]
}'
```

用户通过 `field_value_pairs` 传入必填字段值。有默认值（`default_appear=1`）的字段会自动使用默认值。

## 本地默认创建模板（推荐 — 一次配置，反复复用）

新建工作项时常见痛点：必填字段记不全、字段值（select/role_owners/复合字段）格式难构造、不同模板字段差异大。本 Agent 在 `./.gdpa/meego.yaml` 维护一份**按 `(project_key, work_item_type_key)` 索引的本地创建模板**：

- **首次创建**：本地无模板时，Agent 会拉取近 5 条同类型历史工作项作为候选，让你选一个 `work_item_id` 作为模板种子
- **后续创建**：Agent 自动从本地模板加载所有 required + optional 字段值，作为 `field_value_pairs` 的默认值（不会覆盖你本次显式传入的字段）
- **可改可删**：通过 `action=template, template_action=set/delete/save` 调整模板

### 顶层参数（在 `action=create` 上）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `use_local_template` | bool | `true` | 是否读取本地模板自动注入 `field_value_pairs` |
| `bootstrap_template` | bool | `true` | 本地无模板时，Step 1 是否拉取候选历史工作项让用户选 |
| `template_source_work_item_id` | int64 | — | 显式指定一个历史工作项 ID 作为模板种子（创建成功后会自动保存为本地模板） |
| `save_template` | bool | 首次自动 true，已有时默认 false | 是否在创建成功后写回本地模板。首次创建（无模板）默认会保存；已有模板时需要显式置 true 才会覆盖 |

> **避免跨 template 字段被 Meego 拒为 illegal**：Meego 的字段在 _工作项类型_ 维度可见，但在 _template_ 维度才有真正的 ACL。如果你选的源工作项是在另一个 template 下创建的，bootstrap 自动注入的字段大概率会被服务端以 `err_code=20006 / field [xxx] is illegal` 拒绝。
>
> 本 Agent 的两道护栏：
>
> 1. **候选排序**：`bootstrap_template=true` 拉到的候选会优先把 `template_id` 与你（或 `effective_template_id`）匹配的工作项排在前面，并在每条候选上标 `same_template=true|false`。优先选 `same_template=true` 的种子。
> 2. **跨 template 告警**：当 `template_source_work_item_id` 指向的源 `template_id` 与目标 `template_id` 不一致，或本地缓存模板的 `source_template_id` 与目标 `template_id` 不一致时，`create_meta.local_template.warning` / `notes` 会显式提示，建议你换一个同 template 的种子（或显式重写冲突字段）。

### 推荐使用流程

```bash
# 首次创建（本地无模板）：Step 1 返回候选 work_item_id 列表
gdpa-cli run meego-manage --input '{
  "action": "create",
  "work_item_type_key": "task",
  "name": "新任务-XXX"
}'
# → create_meta.local_template.status == "needs_pick"
# → create_meta.local_template.candidates: [{work_item_id, name, updated_at}, ...]

# Step 2：选定一个候选作为模板种子并确认创建（自动保存为本地默认模板）
gdpa-cli run meego-manage --input '{
  "action": "create",
  "work_item_type_key": "task",
  "name": "新任务-XXX",
  "template_source_work_item_id": 6921539228,
  "confirm_create": true,
  "field_value_pairs": [
    {"field_key": "owner", "field_value": "\"new_owner_user_key\""}
  ]
}'
# → create_meta.local_template.status == "bootstrap_pending_save"
# → 创建成功后 result.saved_local_template 列出已保存的 required/optional 字段
```

下一次创建该 `(project, task)` 时只需要：

```bash
gdpa-cli run meego-manage --input '{
  "action": "create",
  "work_item_type_key": "task",
  "name": "下一个任务",
  "confirm_create": true
}'
# → Agent 自动从本地模板加载所有字段；只需覆盖你想改动的字段即可
# → create_meta.local_template.status == "loaded" / source == "local_cache"
```

### Step 1 预览阶段的 `local_template` 字段

`create_meta.local_template` 始终返回，结构：

```json
{
  "status": "loaded" | "bootstrap_pending_save" | "needs_pick" | "absent",
  "source": "local_cache" | "bootstrap_source",
  "applied_fields": ["priority", "owner"],
  "skipped_fields": [{"field_key": "tags", "reason": "user_provided"}],
  "template": { /* templateToSummary，含 required_fields/optional_fields */ },
  "bootstrap_source": {"work_item_id": 6921539228, "work_item_name": "..."},
  "candidates": [{"work_item_id": ..., "name": "...", "updated_at": ...}],
  "warning": "..."
}
```

### 管理本地模板（`action=template`）

| `template_action` | 必填参数 | 说明 |
|---|---|---|
| `list` | — | 列出所有本地模板（可用 `project_key` 过滤） |
| `show` | `work_item_type_key` | 查看某个模板 |
| `save` | `work_item_type_key`, `template_source_work_item_id` | 强制从某个工作项重建/覆盖模板（可附带 `display_name` / `notes`） |
| `delete` | `work_item_type_key` | 删除指定模板 |
| `clear` | — | 清空所有模板（可用 `project_key` 限定项目） |
| `set` | `work_item_type_key`, `template_fields` | 增量编辑：上探/移除模板内的字段值 |

`template_fields` 接受数组或 JSON 字符串，每项可声明：

| key | 说明 |
|---|---|
| `field_key` | **必填**，要编辑的字段 |
| `field_value` | 字段值（字符串/数字/对象/数组都可，自动 JSON 编码；JSON 字面量字符串会原样存储） |
| `field_type_key` | 可选，方便复核 |
| `is_required` | true → 写入 `required_fields`；false → 写入 `optional_fields`（默认 false） |
| `remove` | true 时移除该 `field_key`（无需 `field_value`） |

示例：

```bash
# 把 priority 改成 P0 并写入 required；同时移除 tags
gdpa-cli run meego-manage --input '{
  "action": "template",
  "template_action": "set",
  "work_item_type_key": "task",
  "template_fields": [
    {"field_key": "priority", "field_value": "P0", "is_required": true},
    {"field_key": "tags", "remove": true}
  ]
}'

# 强制从某个新的历史工作项重建模板
gdpa-cli run meego-manage --input '{
  "action": "template",
  "template_action": "save",
  "work_item_type_key": "task",
  "template_source_work_item_id": 6925000000,
  "display_name": "线上故障跟进模板"
}'

# 删除该 work_item_type 的模板
gdpa-cli run meego-manage --input '{
  "action": "template",
  "template_action": "delete",
  "work_item_type_key": "task"
}'
```

### 一次性参考（advanced — 不写本地模板）

如果只想临时参考一次而不影响本地模板，仍然支持以下顶层参数：

| 参数 | 说明 |
|---|---|
| `reference_work_item_id` | 显式指定参考的历史工作项 ID |
| `auto_reference` | 未指定时自动选最近同类型工作项 |
| `apply_reference` | Step 2 把参考字段合入 `field_value_pairs` |
| `reference_exclude_fields` | 跳过的 `field_key` 列表 |

返回中通过 `create_meta.reference` 暴露选择源、应用情况和告警，结构同既有 reference 字段。本地模板与一次性 reference 互不冲突——两者都会按"用户显式 > 本地模板 > 一次性 reference > meta 默认值"顺序合并。

### 注意事项

- 模板按 `(project_key, work_item_type_key)` 唯一；同类型只保留一份
- `name` / `template` / `template_id` / 附件 / 计算字段不会写入模板，避免误覆盖
- 模板字段值以 raw JSON 字符串存储在 `./.gdpa/meego.yaml`，便于人工编辑 / git diff 审阅
- 富文本（multi_text，如 `description`）只在 reference 模式中以 hint 展示，不会被本地模板自动写入
- 候选 / fetch 失败不会阻塞创建，只在 `create_meta.local_template.warning` 与 `notes` 中提示

## template_id（模板字段必读）

部分工作项类型（典型如 `task`/`issue`）会在 Step 1 的 `field_configs` 中返回一个 `field_key=="template"` 的字段。**该字段的取值必须通过顶层 `template_id`（int64）传入**，**严禁**写在 `field_value_pairs.template`（Meego Open API 会以 `err_code=20006 / field [template] is illegal` 拒绝）。

获取候选 `template_id` 的两种方式（推荐第 1 种）：

1. **从 Step 1 预览结果中读取**：
   - `create_meta.template_options[].template_id`：本 Agent 已经把 `field_key=="template"` 的 `options.value` 解析成 `int64`。
   - 也可以从 `create_meta.field_configs` 里 `field_key=="template"` 的 `options[].value` 字符串自行解析。

兼容行为：

- 若用户/调用方仍把 `template` 放进 `field_value_pairs`，Agent 会在 Step 2 自动剥离并把它"抬升"到顶层 `template_id`，并通过 `create_meta.notes` / 成功返回的 `notes` 给出说明。顶层 `template_id` 优先级更高。
- 若顶层 `template_id` 为 0 且未传，Meego 按 Open API 约定使用该工作项类型的第一个可用模板。`create_meta.notes` 会提示这一行为。

模板化创建示例：

```bash
gdpa-cli run meego-manage --input '{
  "action": "create",
  "work_item_type_key": "task",
  "name": "demo task",
  "template_id": 88712,
  "confirm_create": true,
  "field_value_pairs": [
    {"field_key": "priority", "field_value": "\"1\""}
  ]
}'
```

## bypass_meta_required（绕过本地必填校验，谨慎使用）

`GetWorkItemMeta` 返回的字段元数据是**工作项类型级别**的，**不会随 `template_id` 变化**。当某些字段在元数据里被标记为 `is_required=1`，但 Meego Web UI 在所选模板下并不强制要求时，本 Agent 的本地校验会"误报"为缺失必填，阻塞 Step 2 创建。

此时可以传入顶层布尔参数 `bypass_meta_required=true`：

```bash
gdpa-cli run meego-manage --input '{
  "action": "create",
  "work_item_type_key": "task",
  "name": "demo task",
  "template_id": 88712,
  "confirm_create": true,
  "bypass_meta_required": true,
  "field_value_pairs": [
    {"field_key": "priority", "field_value": "\"1\""}
  ]
}'
```

行为：

- 跳过本地 `missing_required_fields` 校验，直接把请求交给 Meego 服务端做最终判定。
- 若服务端仍返回必填缺失，会照常以 `Invalid Param(20006)` 抛错。
- 成功返回结果中的 `bypass_meta_required=true` 会做留痕。
- **使用约束**：仅当用户明确说"Web UI 能创建/某模板下无需此字段"时启用；不要默默开启，否则会绕过有效校验。

## 字段配置返回格式

每个字段配置包含以下信息：

```json
{
  "field_key": "priority",
  "field_name": "优先级",
  "field_type_key": "select",
  "is_required": 1,
  "options": [
    {"label": "P0", "value": "0"},
    {"label": "P1", "value": "1"}
  ],
  "default_value": {"default_appear": 2},
  "field_tips": "请选择优先级"
}
```

| 字段 | 含义 |
|---|---|
| `is_required` | `1`=必填 / `2`=非必填 / `3`=条件必填 |
| `options` | 选项型字段的可选值列表（已过滤禁用选项） |
| `default_value.default_appear` | `1`=默认出现（自动填充） / `2`=默认不出现 / `3`=条件出现 |
| `default_value.value` | 默认值（当 `default_appear=1` 时自动使用） |
| `role_assign` | 角色字段的角色配置（角色名称、是否默认出现、成员分配方式） |
| `user_provided` | `true` 表示用户已在 `field_value_pairs` 中传入该字段 |
| `compound_fields` | 复合字段的子字段配置列表 |
