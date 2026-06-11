# 生成模板与结构规范

本文档提供 Workflow Builder 生成各文件时的模板。生成时使用 `{placeholder}` 标记的位置需要替换为实际内容。

---

## 1. SKILL.md 模板

```markdown
---
name: {workflow_name}
description: {workflow_description}。Use when {trigger_scenarios}。
---

# {workflow_title}

> **核心原则**：整个流程由 `.gdpa/{session-id}/status.json` 驱动。每次执行前先读取状态文件，确认当前阶段；每步操作后更新状态文件。
> **Session-ID 约束（workflow 专用）**：`gdpa-cli run` 全局不再强制要求 `--session-id`，但本 workflow 必须在整条链路里显式复用同一个 `--session-id <session_id>`。CLI 不会自动把 Session-ID 注入到 Skill 输入；如果漏传或中途更换，`.gdpa/{session-id}/status.json`、阶段产物和恢复链路都会断开。

---

## 强制执行约束（必须遵守）

**以下规则优先级最高，违反任何一条都视为执行失败：**

1. **命令失败时如实报告，不可伪造成功** — 如果命令执行失败，**必须如实向用户报告错误**并排查修复，不可跳过或伪造结果。
2. **调用 `gdpa-cli` 前必须先阅读对应 Skill** — 了解完整的参数格式、输入输出 Schema 和使用示例，确保命令参数正确。
{additional_constraints}

---

## 一、启动与恢复

**每次收到用户指令时，按以下顺序执行：**

### 0. 确定本次 workflow 使用的 session_id
- **当前对话或用户输入已提供 session_id**：直接复用这个值
- **未提供**：立即执行 `gdpa-cli create-session`，使用返回的 session_id
- **拿到后**：后续所有 `gdpa-cli run` 命令都必须显式追加同一个 `--session-id <session_id>`

### 1. 检查是否有进行中的会话

查找 `.gdpa/` 目录下是否有已存在的会话（`{session-id}/status.json`）：

- **存在 `status.json`**：读取文件，根据 `current_phase` 和 phase `status` 恢复到对应阶段继续执行
- **不存在**：使用当前 `session_id` 初始化新的 `.gdpa/{session-id}/status.json`

> 完整的 status.json 结构与初始化模板见 [status-schema.md](status-schema.md)

### 2. 恢复会话

读取 `status.json` 后，按 `current_phase` 定位到对应阶段：

| phase status | 行为 |
|-------------|------|
| `pending` | 开始该阶段 |
| `in_progress` | 从上次中断处继续（结合 `history` 判断进度） |
| `completed` | 跳到下一个阶段 |
| `skipped` | 跳到下一个阶段 |
| `failed` | 分析 `summary` 中的失败原因，尝试修复或询问用户 |

---

## 二、阶段定义与状态流转

### 流转总览

{flow_diagram}

各阶段 `status` 值：`pending` → `in_progress` → `completed` / `skipped` / `failed`

---

{phase_definitions}

---

## 三、状态文件规范

> 完整 status.json 结构见 [status-schema.md](status-schema.md)

### 3.1 状态更新规则

**必须在以下时机更新 status.json**：

| 时机 | 更新内容 |
|------|---------|
| 进入新阶段 | `current_phase`、该阶段 `status` → `in_progress`、`started_at` |
| 完成当前阶段 | 该阶段 `status` → `completed`、`completed_at`、`summary`；`current_phase` → 下一阶段 |
| 跳过阶段 | 该阶段 `status` → `skipped`、`summary` 注明跳过原因 |
| 阶段失败 | 该阶段 `status` → `failed`、`summary` 注明失败原因 |
| 回退阶段 | `current_phase` 回退、目标阶段 `status` → `in_progress` |
| 关键操作完成 | 追加 `history` 条目 |
| context 信息变更 | 更新 `context` 对应字段 |

### 3.2 各阶段产出文件

{artifact_table}

完整目录结构：

{directory_tree}

### 3.3 使用规则

1. **每步四拍节奏**：读 status → 执行操作 → 写产出文件 → 更新 status（缺一不可）
2. **产出文件是硬约束**：标记 `completed` 前必须先写入对应产出文件
3. **history 记录 wrote_file**：每次写入产出文件后，在 `history` 中追加 `{"action": "wrote_file", "detail": "文件路径"}`
4. **大输出走文件**：大体量输出写入文件，对话 context 仅传摘要 + 文件路径
5. **Session 隔离**：每次流程使用独立 `session-id`，互不干扰
6. **Git 忽略**：`.gdpa/` 目录应加入 `.gitignore`
7. **Context 优先读 status**：跨阶段信息统一从 `context` 读取，不重复询问用户
8. **Skipped 阶段无需产出**：被标记为 `skipped` 的阶段不需要写产出文件
9. **产出必须基于真实数据**：产出文件数据必须来自实际执行返回，禁止编造
{additional_rules}

---

## 四、附加资源

- 完整 status.json 结构与初始化模板 → [status-schema.md](status-schema.md)
- 各阶段产出文件与状态更新 JSON 示例 → [phase-examples.md](phase-examples.md)
{skills_reference_link}
```

---

## 2. 阶段定义子模板

每个阶段使用以下格式生成：

```markdown
### Phase {index}: {phase_name}（{phase_title}）

> {goal_description}
{bound_skills_note}

**入口条件**：{entry_condition}

{skip_condition}

**操作步骤**{execution_note}：

{operation_steps}

**退出条件**：{exit_condition}

**产出文件**：`{artifact_path}`（{artifact_description}）

> 完成检查：{completion_check}
{rollback_note}
```

### 阶段模板占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{index}` | 阶段序号（从 0 开始） | `0` |
| `{phase_name}` | snake_case 阶段名 | `schema_review` |
| `{phase_title}` | 中文标题 | `SQL 审核` |
| `{goal_description}` | 该阶段目标 | `审核 SQL 变更脚本的正确性和安全性` |
| `{bound_skills_note}` | 绑定 Skill 说明（可选） | `> 使用 \`rds_query\` Skill 完成。**调用前必读该 Skill。**` |
| `{entry_condition}` | 入口条件 | `上一阶段 completed 或 skipped` |
| `{skip_condition}` | 跳过条件（可选） | `**跳过判断**：无需 SQL 变更 → 标记为 \`skipped\`` |
| `{execution_note}` | 执行说明（可选） | `（必须在终端实际执行，禁止跳过或模拟）` |
| `{operation_steps}` | 操作步骤列表 | 1. xxx\n2. xxx |
| `{exit_condition}` | 退出条件 | `SQL 审核通过` |
| `{artifact_path}` | 产出文件路径 | `review/review_result.json` |
| `{artifact_description}` | 产出文件描述 | `审核结果、修改建议` |
| `{completion_check}` | 完成检查条件 | `review_result.json 存在且 approved=true → 标记 completed` |
| `{rollback_note}` | 回退说明（可选） | `> 失败时：\`current_phase\` 回退到 xxx` |

---

## 3. status-schema.md 模板

```markdown
# status.json 完整结构

存放路径：`.gdpa/{session-id}/status.json`

## 字段说明

\`\`\`json
{
  "session_id": "string — 会话唯一标识，必须与 workflow 中所有命令显式传递的 --session-id 保持一致（直接使用 gdpa-cli create-session 返回值）",
  "created_at": "string — 创建时间 ISO8601",
  "requirement": "string — 用户需求一句话描述",
  "current_phase": "string — 当前所在阶段（{phase_names_pipe_separated}）",
  "phases": {
    {phases_schema}
  },
  "context": {
    {context_schema}
  },
  "history": [
    {
      "phase": "string — 所属阶段",
      "action": "string — 操作标识",
      "detail": "string — 操作详情",
      "timestamp": "string — ISO8601 时间"
    }
  ]
}
\`\`\`

## 初始化模板

新会话时创建 `.gdpa/{session-id}/status.json`：

\`\`\`json
{init_template}
\`\`\`
```

### phases_schema 子模板

每个阶段生成一条：

```json
"<phase_name>": {
  "status": "string — pending|in_progress|completed|skipped|failed",
  "started_at": "string|null — 开始时间",
  "completed_at": "string|null — 完成时间",
  "summary": "string — 该阶段执行摘要"
}
```

### context_schema 子模板

每个字段生成一条：

```json
"<field_name>": "<type> — <description>（来源：<source_phase>，使用：<used_by_phases>）"
```

---

## 4. phase-examples.md 模板

```markdown
# 各阶段产出文件与状态更新示例

每个阶段完成时需要：(1) 写入产出文件 (2) 更新 status.json。以下是各阶段的完整示例。

---

{phase_examples}
```

### 每个阶段的示例子模板

```markdown
## Phase {index}: {phase_name}

### 产出文件 `{artifact_path}`

\`\`\`json
{artifact_example_json}
\`\`\`

### status.json 更新

\`\`\`json
{status_update_example_json}
\`\`\`

---
```

如有回退场景，在该阶段末尾追加：

```markdown
### 失败时回退

\`\`\`json
{rollback_status_example_json}
\`\`\`
```

---

## 5. skills-reference.md 模板（仅当有 Skill 绑定时生成）

```markdown
# 可用 Skill 速查与选择指南

> **重要**：在调用任何 Skill 前，**必须先阅读对应的 Skill** 获取完整的参数说明、输入输出格式和使用示例。

## Skill 速查表

{skills_table}

## Skill 选择决策指南

{decision_tree}

## 关键阶段 Skill 调用示例

{usage_examples}
```

---

## 6. 流转图生成规则

根据流转设计，生成 ASCII 流转图：

**线性流程**：
```
phase_a → phase_b → phase_c → phase_d
```

**带条件分支**：
```
phase_a → phase_b ──(条件A)──→ phase_c → phase_d
                   └─(条件B)──→ phase_e → phase_d
```

**带回退**：
```
phase_a → phase_b → phase_c → phase_d
                        ↑          │
                        └──────────┘
                        (失败时回退)
```

**带确认门**：
```
phase_a → phase_b → [用户确认] → phase_c → phase_d
```

**带循环**：
```
phase_a → phase_b ←──→ phase_c (最多N次)
                          │
                          ↓ (通过)
                       phase_d
```

---

## 7. 目录结构生成规则

根据阶段和产出物定义，生成会话目录结构：

```
.gdpa/{session-id}/
├── status.json                    # 流程状态（核心，每步更新）
├── {phase_0_dir}/
│   └── {phase_0_artifact}         # {phase_0_name} 产出
├── {phase_1_dir}/
│   └── {phase_1_artifact}         # {phase_1_name} 产出（skipped 时不存在）
├── ...
└── summary/
    └── report.md                  # 最终总结（如有 completion 阶段）
```

目录名使用阶段名或相关 Skill 名，与 base-workflow 保持风格一致。
