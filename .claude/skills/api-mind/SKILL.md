---
name: api-mind
description: API 测试用例自动化 SKILL。支持将 case.md 生成 Go / Python 可执行用例、执行用例、在安全准入内自动修复、生成报告；支持仅生成、仅执行、生成并执行、执行并报告、全流程等组合与可重入。用户提到用例生成、case 转代码、API 测试、测试执行、自动修复用例、测试报告时触发。
---

# api-mind

API 测试用例自动化主入口。主 SKILL 只做**任务分类、语言路由、状态维护、埋点门禁与结果汇总**，具体生成 / 执行 / 报告逻辑由 `go_driver/` 或 `py_driver/` 实现。

## 1. 文件读取原则（强约束）

- **按需、局部、单路径读取**：只读取当前任务、当前语言、当前阶段必需的文件；禁止为“了解全貌”读取全文。
- **优先摘要 / 搜索 / 脚本**：状态用 `state_manager.py summary`，日志和配置优先用定向搜索或脚本；仅在摘要不足以决策时读取局部片段。
- **禁止无谓展开大文件**：不得完整读取 / 粘贴 `state.json`、`case.md`、`spec.md`、大日志、`metrics.json`、driver 全部文档或运行时源码。
- **driver 懒加载**：确定语言后只读取对应 driver 的 `SKILL.md`；确定子任务后只读取对应阶段文档。不得同时加载 Go 与 Python driver，除非用户显式要求对比。
- **metrics 懒加载**：常规流程只调用 CLI / 脚本；仅 CLI 缺失、安装排障或字段含义不清时读取 `metrics/METRICS.md` 或其索引指向的单个字段文档。
- **配置读取最小化**：判断语言时优先读取 `.test_config.ini` 中 `[api-mind] language`；其次在 `agent.md` 中定向搜索 `api-mind` / `language` 附近内容，不读取全文。

## 2. 目录速览

| 路径 | 用途 | 读取时机 |
| --- | --- | --- |
| `scripts/state_manager.py` | 初始化 / 摘要 / 增量维护状态 | 每轮必用脚本，不读源码 |
| `metrics/METRICS.md` | 埋点 CLI、生命周期、字段文档索引 | CLI 缺失或字段不清时 |
| `go_driver/SKILL.md` | Go driver 调度契约 | 语言为 Go 时 |
| `py_driver/SKILL.md` | Python driver 调度契约 | 语言为 Python 时 |
| `go_driver/docs/*.md`、`py_driver/docs/*.md` | 阶段细节 | 执行对应阶段时 |
| `mock.md` | ByteMock 规则 | case 含 Mock 且 driver 阶段需要时 |

## 3. 任务与语言路由

### 3.1 任务类型

| 标识 | 含义 | 执行方 |
| --- | --- | --- |
| `generate` | 将 `case.md` 转成 Go / Python 用例代码 | driver |
| `execute` | 执行已有用例；失败时按 driver 准入规则尝试修复 | driver |
| `report` | 根据执行结果生成报告 | driver / 主流程收口 |

常见组合：`generate`、`execute`、`generate → execute`、`execute → report`、`generate → execute → report`。任一子任务失败时停止后续任务并保留状态。

### 3.2 语言选择优先级

1. 用户显式指定 Go / Python。
2. 当前仓库 `.test_config.ini` 的 `[api-mind] language`。
3. 当前仓库 `agent.md` 的 `api-mind` 语言配置。
4. 默认 **Go**。

路由：Go → `go_driver/`；Python → `py_driver/`。

Python `execute` 模式：默认 `local`（运行 `py_driver/scripts/run_api_test.sh`）；仅当用户明确要求“远端 / 平台 / remote”时使用 `remote`（`py_driver/scripts/ttat_execute.sh`）。不得默认触发远端执行。

## 4. 状态与可重入

状态文件：`<工作目录>/.api-mind/state.json`，以工作目录为任务实例边界。字段至少包含 `task_id`、`language`、`tasks.<generate|execute|report>.status/inputs[]/outputs[]/error`、`warnings[]`；自动修复记录使用 `fix_attempts` / `fix_history`。禁止写入模型推断的 `timestamp`、`created_at`、`updated_at`。

必须通过脚本维护状态，避免模型展开 / 重写完整 JSON：

```bash
python3 <api-mind>/scripts/state_manager.py summary --workdir <工作目录>
python3 <api-mind>/scripts/state_manager.py init --workdir <工作目录> --task-id <task_id> --language <go|python>
python3 <api-mind>/scripts/state_manager.py set-task --workdir <工作目录> --task <generate|execute|report> --status <pending|running|completed|failed|skipped>
python3 <api-mind>/scripts/state_manager.py warn --workdir <工作目录> --code <warning_code> --message "<简短说明>"
python3 <api-mind>/scripts/state_manager.py fix --workdir <工作目录> --task execute --summary "<修复摘要>" --result <success|failed>
```

仅当摘要不足以定位单个子任务输入 / 输出 / 修复历史时，读取该子任务详情：

```bash
python3 <api-mind>/scripts/state_manager.py show-task --workdir <工作目录> --task <generate|execute|report>
```

恢复规则：先 `summary`；存在未完成任务则从 `next` 或首个非 `completed` 子任务继续；不存在状态则 `init`；已完成子任务不重复执行，除非用户显式要求。

## 5. 执行协议

### 5.1 请求解析

从用户输入和最小配置中确定：任务链、语言、`case.md` 路径（默认 `FEATURE_DIR/test/case.md`）、工作目录（默认 `FEATURE_DIR/test/`）、可选执行模式。Go 代码默认落在 `<REPO_ROOT>/tests/integration/...`，运行时库同步到 `<REPO_ROOT>/tests/integration/apitest/`。

### 5.1.1 快速路径与跳过规则

在不改变用户语义的前提下优先走快速路径，避免重复执行耗时步骤：

- **已完成子任务不重跑**：`state_manager.py summary` 显示某子任务 `completed` 且输出仍存在时，后续组合任务直接复用其输出；除非用户显式要求“重新生成 / 重新执行 / 强制刷新”。
- **纯 report 不触发 execute**：用户只要求报告且已有 execute 输出 / 日志时，只运行 `report`；不得为了“确认最新”自动重跑测试。
- **纯 execute 不触发 generate**：已有 `code_file` 或状态中有 generate 输出时直接执行；只有代码文件缺失或用户要求重新生成时才进入 generate。
- **公共信息单轮缓存**：同一轮会话内的语言、工作目录、`case_file`、`task_id`、JWT、`user_name`、metrics CLI 可用性、driver `SKILL.md` 内容只解析 / 读取一次，后续子任务复用内存结果。

### 5.2 metrics 前置门禁

进入任一子任务前必须确认 `apimind-metrics` CLI 可用；未就绪不得执行 `generate` / `execute` / `report`。同一轮只检查一次 Node.js / CLI，只执行一次 `gdpa-cli login -p cn`；JWT 与 `user_name` 仅内存复用，禁止落盘。CLI 缺失时按 `metrics/METRICS.md` 的安装命令处理，不改 registry / version。

`start` 成功前禁止：完整阅读 `case.md` / `spec.md`、探索 `api_test` 仓库、读取 driver 阶段文档、AskUserQuestion、代码生成、写入非 `.api-mind/` 文件。只允许完成 CLI / JWT 准备和状态运行态更新。

### 5.3 每个子任务固定顺序

对任务链中的每个 `<cmd>`（`generate|execute|report`）严格执行：

1. 标记运行中：
   ```bash
   python3 <api-mind>/scripts/state_manager.py set-task --workdir <工作目录> --task <cmd> --status running --create --task-id <task_id> --language <go|python>
   ```
2. 埋点 start（成功前仍受 5.2 禁止项约束）：
   ```bash
   apimind-metrics start <cmd> --workdir <工作目录>/.api-mind
   ```
3. 写公共字段，优先复用 `metrics_common.json`；缓存缺失时脚本有限读取 `test/task.md` / `case.md` 并执行最少 git 命令：
   ```bash
   python3 <api-mind>/metrics/scripts/build_common_metrics.py \
     --workdir <工作目录>/.api-mind \
     --user-name "<本轮会话内存 username>"
   ```
   仅当主流程已持有更准确 PSM 时追加 `--psm '["..."]'`；不得为传参额外读取大文件。
4. 读取当前语言 driver `SKILL.md`，再按 `<cmd>` 读取对应阶段文档并执行；同一轮已读取过的 driver `SKILL.md` 不重复读取，阶段文档只在首次进入该阶段时读取。
5. 写业务字段：`generate` / `execute` 由 driver 写入；`report` 在拿到报告绝对路径后直接写 `report_file_path`，不得重新搜索报告文件。
6. 埋点 end（不可跳过）：
   ```bash
   apimind-metrics end <cmd> --workdir <工作目录>/.api-mind --jwt "<本轮会话内存 JWT>"
   ```
   schema 校验失败只修业务字段后重试 `end`；网络 / JWT 问题最多重试 3 次；严禁为修复 `end` 重新 `start`。子任务崩溃 / 用户中断且未走到 `end` 时，不补调 `end`，丢弃本次 `metrics.json`，下次正常重新 start/end；必要时按需读取 `metrics/docs/end_handling.md`。
7. 状态收口：成功写 `completed` 与结构化 output；失败写 `failed` 与结构化 error。

## 6. 自动修复

仅 `execute` 失败后由 driver 触发。driver 必须先归因，只有高置信度属于“用例实现问题”且满足自身安全准入时才可修改测试资产并重跑；API / 鉴权 / 环境 / 基础设施问题不得自动改 case。Python 仅 `local execute` 支持自动修复，最多 fix-and-rerun 3 次；Go 按 `go_driver/SKILL.md`。

## 7. Driver 最小契约

| 子任务 | 最小输入 | 最小输出 | 细节 |
| --- | --- | --- | --- |
| `generate` | `case_file`、`output_dir`、`language` | `code_file`、`status`、`error` | 对应 driver |
| `execute` | `code_file`、`output_dir`、`language`、可选 `execution_mode` | `status`、`results`、`error` | 对应 driver |
| `report` | `execute_results`、`output_dir`、`language` | `report_file`、`status`、`error` | 对应 driver |

主 SKILL 不承载语言私有参数；Python `execution_mode` 由 3.2 决定，其余字段按 driver 文档。

## 8. 输出给用户

最终只汇总必要信息：各子任务状态、生成 / 修改文件路径、执行摘要、报告路径、失败原因与修复历史（如有）。响应中不得展开大段日志、完整状态 JSON 或 `case_info_list[]`。
