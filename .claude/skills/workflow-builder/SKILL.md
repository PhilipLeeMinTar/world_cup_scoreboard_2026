---
name: workflow-builder
description: Guide users through building custom workflow Skills via conversation. Use when the user wants to create a new workflow, assemble a business-specific development process, customize the base-workflow, or mentions "workflow builder" / "build workflow" / "create workflow".
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# Workflow Builder - 工作流组装器

> **定位**：这是一个「元 SKILL」—— 它不直接执行业务流程，而是通过对话引导用户设计并生成一套完整的自定义 Workflow SKILL。

---

## 核心理念

1. **对话驱动**：通过结构化提问逐步收集需求，而非要求用户一次性提供所有信息
2. **灵活组装**：用户自定义阶段、流转条件、回退策略，不局限于固定流程
3. **Context 透传**：自动生成 `status.json` schema，确保跨阶段信息传递
4. **信息记录**：每个阶段产出文件 + history 日志，支持断点恢复
5. **Skill 编排**：可引用已有的 gdpa-cli Agent Skills 作为阶段执行能力

---

## 引导流程总览

```
Phase 1: 需求画像        →  了解业务场景、目标、涉及的系统
Phase 2: 阶段定义        →  拆解工作流为有序阶段
Phase 3: 流转设计        →  定义阶段间的转换条件、分支、回退
Phase 4: Context 设计    →  定义跨阶段共享的上下文字段
Phase 5: 产出物设计      →  定义每个阶段的输出文件和完成条件
Phase 6: Skill 绑定      →  将已有 gdpa-cli Skills 绑定到对应阶段
Phase 7: 生成 & 确认     →  输出完整的 Workflow SKILL 文件
```

---

## Phase 1: 需求画像

**目标**：理解用户要构建什么样的工作流。

**向用户提问**（按需选择，不必全问）：

1. **场景描述**：「请用 1-2 句话描述这个 workflow 要完成什么？」
2. **触发条件**：「什么情况下会使用这个 workflow？」
3. **参与角色**：「这个流程中有哪些角色参与？（人、系统、AI Agent）」
4. **已有流程**：「目前是否有手动执行的流程？大致步骤是什么？」
5. **痛点**：「当前流程中最想自动化/优化的环节是什么？」

**信息整理**：将收集到的信息汇总为一份「需求画像」，向用户确认：

```markdown
## 工作流需求画像

| 项目 | 内容 |
|------|------|
| 名称 | {workflow-name} |
| 场景 | {一句话描述} |
| 触发条件 | {何时使用} |
| 涉及系统 | {相关的系统/工具/平台} |
| 核心目标 | {要达成什么} |
| 预计阶段数 | {大致几步} |
```

> 用户确认后进入 Phase 2。

---

## Phase 2: 阶段定义

**目标**：将工作流拆分为有序的执行阶段。

**引导策略**：

1. 基于 Phase 1 的需求画像，**先提出一个初始方案**（草稿阶段列表），让用户在此基础上调整，而非从零开始。
2. 对每个阶段收集：
   - **阶段名称**（snake_case）
   - **一句话描述**（目标是什么）
   - **入口条件**（什么时候进入这个阶段）
   - **操作要点**（这个阶段做什么，2-5 条）
   - **是否可跳过**（标记为 optional）
   - **退出条件**（怎样才算完成）

**向用户展示阶段总览表**：

```markdown
## 阶段定义（草稿）

| # | 阶段名 | 描述 | 可跳过 |
|---|--------|------|--------|
| 0 | {phase_name} | {描述} | 否 |
| 1 | {phase_name} | {描述} | 是 |
| ... | ... | ... | ... |
```

> 用户确认或调整后进入 Phase 3。

---

## Phase 3: 流转设计

**目标**：定义阶段间的转换规则，包括线性流转、条件分支和回退。

**支持的流转模式**：

| 模式 | 说明 | 示例 |
|------|------|------|
| **线性** | 前一阶段完成后自动进入下一阶段 | `coding → deploy` |
| **条件分支** | 根据条件选择不同的下一阶段 | `审核通过 → deploy`；`审核不通过 → coding` |
| **可跳过** | 满足条件时跳过该阶段 | 不涉及 IDL → 跳过 `idl_change` |
| **回退** | 当前阶段失败时回退到指定阶段 | `testing 失败 → coding` |
| **用户确认门** | 进入前需征求用户同意 | `testing 前需用户确认` |
| **循环** | 某些阶段可重复执行直到满足条件 | `compile_check ↔ fix_code`（最多 N 次） |

**向用户展示流转图**（ASCII）：

```
{phase_0} → {phase_1} → {phase_2} → ... → {phase_n}
                              ↑              │
                              └──────────────┘
                              (条件不满足时回退)
```

**收集每条流转规则**：

```markdown
| 从 | 到 | 条件 | 类型 |
|----|----|------|------|
| phase_a | phase_b | phase_a completed | 线性 |
| phase_b | phase_c | 审核通过 | 条件分支 |
| phase_b | phase_a | 审核不通过 | 回退 |
| phase_c | phase_d | 用户确认 | 确认门 |
```

> 用户确认后进入 Phase 4。

---

## Phase 4: Context 设计

**目标**：定义 `status.json` 中 `context` 结构，确保跨阶段信息正确传递。

**引导策略**：

1. 基于已定义的阶段，**自动推断**需要哪些 context 字段（如某阶段产出的 ID 被后续阶段使用）
2. 向用户展示推断结果，让其补充或修改

**Context 字段收集模板**：

```markdown
## Context 字段定义

| 字段名 | 类型 | 来源阶段 | 使用阶段 | 说明 |
|--------|------|----------|----------|------|
| psm | string | info_collection | 全部 | 服务 PSM |
| task_id | number | task_setup | deploy, testing | DevFlow 任务 ID |
| ... | ... | ... | ... | ... |
```

**关键原则**（写入生成的 SKILL 中）：

- **Context 优先读 status**：所有跨阶段信息从 `context` 读取，不重复询问用户
- **来源唯一性**：每个 context 字段有且仅有一个来源阶段负责写入
- **向后兼容**：新增字段使用可选类型（null 初始值），不破坏已有会话

> 用户确认后进入 Phase 5。

---

## Phase 5: 产出物设计

**目标**：为每个阶段定义产出文件和完成检查条件。

**引导策略**：

1. 基于阶段定义，为每个阶段建议一个默认产出文件
2. 定义完成检查条件（文件存在 + 关键字段校验）

**产出物收集模板**：

```markdown
## 各阶段产出物

| 阶段 | 产出文件路径 | 完成检查条件 |
|------|-------------|-------------|
| {phase_name} | {dir}/{file}.json | 文件存在且 {field} 有效 |
| ... | ... | ... |
```

**核心规范**（自动写入生成的 SKILL）：

- 每步四拍节奏：读 status → 执行操作 → 写产出文件 → 更新 status
- 标记 `completed` 前必须先写入产出文件
- `skipped` 阶段无需产出文件
- 大输出走文件，对话 context 仅传摘要 + 路径
- history 记录每次 `wrote_file`

> 用户确认后进入 Phase 6。

---

## Phase 6: Skill 绑定

**目标**：将已有的 gdpa-cli Agent Skills 绑定到对应阶段。

**引导策略**：

1. 列出当前可用的 gdpa-cli Skills 供用户选择
2. 对每个阶段，询问是否需要调用某个 Skill，以及调用方式

**可用 Skills 快速列表**：

| 分类 | Skill | 说明 |
|------|-------|------|
| 任务管理 | `devflow` | DevFlow 任务生命周期 |
| | `meego-manage` | Meego 任务搜索 |
| 接口 & IDL | `edit-idl` | IDL 编辑 + 编译检查 |
| | `bam-api` | 查询 API 接口定义 |
| | `bam-query` | 接口测试（RPC/HTTP） |
| 服务 | `overpass` | 服务 IDL + Kitex 调用代码 |
| 代码 | `repotalk` | 代码仓库智能查询 |
| | `codebase` | 代码库分析 |
| 配置 & 数据 | `tcc-query` | TCC 远程配置 |
| | `rds_query` | RDS 数据库元数据 |
| 日志 | `argos-query` | Argos 服务日志 |
| 部署 | `bits-cd` | BITS CD 部署 |
| | `scm` | 代码版本管理 |
| | `tce` | TCE 服务/集群/Pod |
| 权限 | `iam` | IAM 权限申请 |

**绑定收集模板**：

```markdown
## Skill 绑定

| 阶段 | 绑定 Skills | 用途说明 | 调用前必读 |
|------|------------|---------|-----------|
| {phase} | devflow | 创建任务 | 是 |
| {phase} | bam-query, argos-query | 接口测试 + 日志分析 | 是 |
| {phase} | (无) | 纯手动/AI 编码 | - |
```

> 用户确认后进入 Phase 7。

---

## Phase 7: 生成 & 确认

**目标**：基于前 6 步收集的信息，生成完整的 Workflow SKILL 文件集合。

### 7.1 确认输出位置

向用户确认生成的 SKILL 文件放在哪里：

| 选项 | 路径 | 适用场景 |
|------|------|---------|
| 项目级 | `.cursor/skills/{workflow-name}/` | 团队共享，跟随项目仓库 |
| gdpa 内置 | `pkg/skills/{workflow-name}/` | 作为 gdpa-agents 内置 Skill |
| 个人级 | `~/.cursor/skills/{workflow-name}/` | 个人使用 |

### 7.2 生成文件清单

基于收集的信息生成以下文件：

```
{workflow-name}/
├── SKILL.md                  # 主工作流指令（从模板生成）
├── status-schema.md          # status.json 完整结构定义
├── phase-examples.md         # 各阶段产出文件与状态更新示例
└── skills-reference.md       # 绑定的 Skill 速查（如有）
```

### 7.3 生成规则

生成时严格遵循以下规则：

> 生成模板和结构见 [generation-templates.md](generation-templates.md)

**SKILL.md 生成规则**：

1. **frontmatter**：`name` 为用户确认的 workflow 名称；`description` 包含 WHAT + WHEN
2. **强制执行约束**：继承 base-workflow 的核心约束（命令失败如实报告、调用前必读 Skill）
3. **启动与恢复**：必须明确写出“workflow 里所有 `gdpa-cli run` 都要显式复用同一个 `--session-id`”，并包含 session 检查、status.json 读取/创建、恢复逻辑
4. **阶段定义**：按用户定义的阶段顺序，每个阶段包含：入口条件、操作步骤、退出条件、产出文件
5. **流转规则**：ASCII 流转图 + 条件描述
6. **状态文件规范**：更新时机、四拍节奏、session 隔离、大输出走文件等规则
7. **附加资源**：链接到 status-schema.md、phase-examples.md、skills-reference.md

**status-schema.md 生成规则**：

1. `phases` 包含用户定义的所有阶段（status 字段固定为 pending/in_progress/completed/skipped/failed）
2. `context` 包含 Phase 4 定义的所有字段
3. `session_id` 字段说明必须明确“直接使用 gdpa-cli create-session 返回值，并与所有 workflow 命令里的 --session-id 保持一致”
3. 提供初始化模板

**phase-examples.md 生成规则**：

1. 为每个阶段提供产出文件 JSON 示例
2. 为每个阶段提供 status.json 更新示例
3. 包含 failed/rollback 场景示例

**skills-reference.md 生成规则**（仅当有 Skill 绑定时生成）：

1. 列出绑定的 Skills 速查表
2. 提供选择决策树
3. 列出关键阶段的 Skill 调用示例

### 7.4 用户确认

生成完成后，向用户展示文件清单并逐一确认。对每个文件：
- 简要说明内容
- 询问是否需要调整

全部确认后，写入文件。

---

## 对话策略

### 交互原则

1. **先提方案再确认**：不要只问空泛的问题，要基于已有信息给出具体建议让用户 Yes/No 或微调
2. **渐进式**：每个 Phase 收集一批信息后立即确认，不要等到最后一次性确认
3. **容错**：用户可以随时说「回到 Phase X」来修改之前的决定
4. **上下文记忆**：贯穿对话的信息存储在内部工作区，避免重复询问

### 快捷模式

如果用户已经提供了较完整的需求描述（如一个文档或详细说明），可以跳过逐步引导，直接：

1. 分析需求，生成所有 Phase 的草稿
2. 一次性展示完整设计给用户确认
3. 用户确认后直接生成

### 典型对话流程

```
用户: 我想创建一个数据库迁移的 workflow

AI: [Phase 1 - 需求画像]
    我来帮你构建数据库迁移的 workflow。先确认几个信息：
    1. 这个 workflow 涵盖哪些数据库？（MySQL/Redis/...）
    2. 迁移是指 schema 变更还是数据搬迁？
    3. 是否需要灰度/回滚机制？

用户: MySQL schema 变更，需要灰度和回滚

AI: [Phase 1 确认 + Phase 2 阶段草稿]
    收到。基于你的描述，我建议这样的阶段划分：
    
    | # | 阶段 | 描述 |
    |---|------|------|
    | 0 | schema_review | 审核 SQL 变更脚本 |
    | 1 | backup | 备份目标表 |
    | 2 | canary_migrate | 灰度执行（单个 VDC） |
    | 3 | verify_canary | 验证灰度结果 |
    | 4 | full_migrate | 全量执行 |
    | 5 | verify_full | 验证全量结果 |
    | 6 | completion | 清理 & 总结 |
    
    流转：verify_canary 失败 → rollback → schema_review
    
    是否需要调整？

用户: 好的，继续

AI: [Phase 3-6 继续引导...]
```

---

## 附加资源

- 生成模板与结构规范 → [generation-templates.md](generation-templates.md)
- 已生成 workflow 示例 → [examples.md](examples.md)
