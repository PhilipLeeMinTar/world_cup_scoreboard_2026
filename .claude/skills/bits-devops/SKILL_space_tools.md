# 空间与配置工具

## get_recent_spaces — 获取最近访问的空间

返回当前用户最近访问的 BITS 空间列表。**不需要 space_id**，可用于在不知道 space_id 时先查询，让用户选择对应空间。

**参数**：无。

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{"action": "get_recent_spaces"}'
```

**返回**：

```json
{
  "success": true,
  "action": "get_recent_spaces",
  "total": 3,
  "spaces": [
    {
      "id": "1058659382530",
      "name": "gdpa_verifier",
      "identification": "gdpa_verifier",
      "description": "GDPA 代码推改自动化测试"
    },
    {
      "id": "94017024770",
      "name": "gdp_workplace",
      "identification": "gdp_workplace"
    }
  ]
}
```

> **提示**：返回的 `id` 字段即为其他 action 所需的 `space_id`。

---

## search_projects — 搜索项目

根据关键词搜索 BITS 项目，返回项目名称、唯一 ID、类型等信息。适用于只知道项目名称但需要查询项目数字 ID 的场景（例如 Web 项目在创建开发任务时需要数字 ID）。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | 是 | 搜索关键词（项目名称或 ID 片段） |
| `project_type` | string | 是 | 项目类型，如 `tce`、`faas`、`web`（BITS API 要求必传） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "search_projects",
  "keyword": "TT4D website",
  "project_type": "web"
}'
```

**示例（搜索 TCE 项目）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "search_projects",
  "keyword": "llm_remote",
  "project_type": "tce"
}'
```

**返回**：

```json
{
  "success": true,
  "action": "search_projects",
  "keyword": "TT4D website",
  "count": 1,
  "projects": [
    {
      "project_type": 4,
      "project_type_name": "Web",
      "project_unique_id": "85959",
      "project_name": "TT4D website",
      "created_by": "marsdong"
    }
  ]
}
```

> **提示**：Web 项目创建开发任务时，`psm_list` 中的 PSM 需填写 `project_unique_id`（数字 ID），而非项目名称。如果只知道项目名，先用此接口查询。

---

## get_workspace_info — 获取空间信息

返回 BITS 空间的基本信息，包括名称、描述、类型等。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `space_id` | number | 是 | BITS 空间 ID（可通过 `get_recent_spaces` 获取） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_workspace_info",
  "space_id": 94017024770}'
```

**返回**：

```json
{
  "success": true,
  "action": "get_workspace_info",
  "data": {
    "space_id": 94017024770,
    "name_en": "GDP LLM Remote",
    "name_zh": "GDP LLM Remote",
    "devops_space_type": "...",
    "created_by": "..."
  }
}
```

---

## get_dev_templates — 获取开发任务模板列表

返回空间下所有开发任务流程模板，包含启用/禁用状态。**创建开发任务时应选择 `enabled: true` 的模板。**

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `space_id` | number | 是 | BITS 空间 ID（可通过 `get_recent_spaces` 获取） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_templates",
  "space_id": 94017024770}'
```

**返回**：

```json
{
  "success": true,
  "action": "get_dev_templates",
  "templates": [
    {
      "workflow_id": "26036",
      "name": "火车流程",
      "name_i18n": "Train Release",
      "is_default": true,
      "deleted": false,
      "enabled": true,
      "team_flow_id": 424613124354,
      "team_flow_type": 1,
      "team_flow_name": "火车研发流程"
    },
    {
      "workflow_id": "26037",
      "name": "需求研发",
      "name_i18n": "Feature Dev",
      "is_default": false,
      "deleted": false,
      "enabled": false,
      "team_flow_id": 424660152834,
      "team_flow_type": 2,
      "team_flow_name": "需求研发流程"
    }
  ]
}
```

**返回字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `workflow_id` | string | 模板 ID，对应 `create_dev_taskv2` 的 `dev_task_template_id` |
| `name` | string | 模板名称 |
| `is_default` | bool | 是否为空间默认模板 |
| `enabled` | bool | **该模板在空间中是否启用。`false` 表示已被空间管理员禁用，不可用于创建开发任务。创建任务时必须选择 `enabled: true` 的模板。** |
| `deleted` | bool | 是否已删除 |
| `team_flow_id` | number | 关联的研发流程 ID |
| `team_flow_type` | number | 流程类型：1=火车, 2=需求, 3=hotfix, 4=增量交付 |
| `team_flow_name` | string | 研发流程名称 |

---

## get_dev_template_detail — 获取模板详情

返回开发任务模板的完整配置，包括工作流编排、阶段配置等。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_template_id` | number | 是 | 模板 ID（5位数字） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_template_detail",
  "dev_task_template_id": 26037}'
```

---

## check_template_meego — 检查模板是否要求 Meego

检查指定模板是否配置了 `workitem_must`，即创建开发任务时是否必须关联 Meego 需求。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_template_id` | number | 是 | 模板 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "check_template_meego",
  "dev_task_template_id": 26037}'
```

**返回**：

```json
{
  "success": true,
  "action": "check_template_meego",
  "workitem_must": true
}
```

---

## get_team_flow — 获取研发流程配置

返回研发流程的详细配置，包括关联的开发任务模板、CD 工作流等。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `team_flow_id` | number | 是 | 研发流程 ID（12位数字） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_team_flow",
  "team_flow_id": 424660152834}'
```

**返回**：

```json
{
  "success": true,
  "action": "get_team_flow",
  "team_flow": {
    "id": 424660152834,
    "name": "需求研发流程",
    "workspace_id": 94017024770,
    "dev_workflow_ids": [26037]
  }
}
```
