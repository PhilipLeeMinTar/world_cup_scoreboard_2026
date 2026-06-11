---
name: api-mind/py_driver
description: api-mind 的 Python 语言用例驱动。负责 Python API 测试用例的生成、执行与报告。支持 generate：将 case.md 转成 api_test 仓库规范的 Python 用例代码，补齐配置，并按策略决定是否提交 / 推送。支持 execute：默认本地运行 Python 用例；仅在用户或上层显式指定 remote / TTAT / 平台执行时触发远端执行。支持 report：远端 TTAT 结果抓取与报告生成；本地执行仅返回本地日志证据或最小摘要。由 api-mind 主 SKILL 分发调用，不直接面向用户。
---

# py_driver

Python 语言用例驱动。本文件只保留**调度契约、模式选择和强约束**；阶段细节按需加载，避免每次运行都加载本地执行、远端执行和报告的完整说明。

## 1. 按需加载规则

收到 api-mind 主 SKILL 分发后，先识别任务链，再只读取必要文件：

| 子任务 | 何时读取 | 必读文件 |
| --- | --- | --- |
| `generate` | 需要生成 / 更新 Python case、配置、conftest、client，或后续 remote 需要先生成并 push | 先读 `docs/generate.md`，再按其索引读取 `docs/generate/*.md` |
| `execute(local)` | 用户未指定远端执行，或明确说“本地运行 / local / pytest / 跑本地用例” | `docs/execute_local.md` |
| `execute(remote)` | 用户明确说“远端运行 / TTAT / 平台执行 / remote / 触发远端”，或上层显式传入 `execution_mode=remote` | `docs/execute_remote.md` |
| `report` | 需要基于 execute 结果生成报告 | `docs/report.md` |

互斥规则：`execute(local)` 与 `execute(remote)` **同一轮 execute 只能选择一个**。不得同时读取两个执行文件，除非用户要求比较两种模式或迁移执行模式。

资源索引：

- 生成模板：`resources/py_test_template.md`、`resources/conftest_template.md`、`resources/client_template.md`、`resources/env_template.md`
- generate 子阶段：`docs/generate/context.md`、`docs/generate/repo_prepare.md`、`docs/generate/config_client.md`、`docs/generate/case_code.md`、`docs/generate/push.md`
- 本地执行脚本：`scripts/run_api_test.sh`
- 远端执行脚本：`scripts/ttat_execute.sh`
- 远端报告脚本：`scripts/ttat_report.sh`
- 脚本细节：`scripts/README.md`

原则：**先复用，找不到再按模板最小生成**。

## 2. 职责边界

- `generate`：将当前特性的 `case.md` 转为 **api_test 仓库**中的 Python 测试代码，补齐 runtime config / conftest / client，并按 `generate_strategy` 选择仅本地生成或提交并推送。
- `execute`：执行已生成 / 已存在的 Python case。
  - 默认 `execution_mode=local`，通过 `scripts/run_api_test.sh` 在本地运行 pytest。
  - 仅在显式 remote 意图下使用 `scripts/ttat_execute.sh` 触发 TTAT。
- `report`：
  - 远端模式：通过 `scripts/ttat_report.sh` 抓取并解析 TTAT 结果，生成 JSON / Markdown 报告。
  - 本地模式：不调用 TTAT 报告脚本，只返回本地日志证据；如需要 Markdown，仅生成最小摘要，不能伪造 `plan_id` / `ttat_task_id`。

## 3. Execute 模式选择

1. 用户明确说“本地运行 / local / pytest / 跑本地用例” → `execution_mode=local`
2. 用户明确说“远端运行 / TTAT / 平台执行 / remote / 触发远端” → `execution_mode=remote`
3. 未明确指定 → `execution_mode=local`

速度优先约束：默认 local 是快速路径；不得为了生成报告或“更真实”自动升级到 remote / TTAT。只有用户明确远端意图，或状态中已有本轮 remote 触发元信息且用户要求追踪该远端结果时，才读取 remote 执行 / 报告文档并调用远端脚本。

状态文件必须记录实际执行模式：

```json
{
  "execute": {
    "status": "completed",
    "execution_mode": "local",
    "inputs": [
      {
        "type": "case_file",
        "path": "tests/.../test_xxx.py"
      }
    ],
    "outputs": [
      {
        "type": "execute_result",
        "exit_code": 0,
        "log_file": ".../.api-mind/logs/py_driver_local_execute.log"
      }
    ]
  }
}
```

## 4. Driver 接口摘要

### 4.1 Generate

输入：

- `case_file`: 当前特性目录下的 `case.md`
- `output_dir`: 当前特性工作目录，用于读取 `spec.md` / `test/task.md` 与写入 `.api-mind` 产物
- `api_test_repo`: pydriver 提供或用户确认的 api_test 仓库绝对路径
- `target_case_dir`: 用户通过 `AskUserQuestion` 主动输入的、相对 `api_test_repo` 的仓库内相对路径
- `generate_strategy`: `generate_only_local` / `generate_and_push`
- `target_branch`: 仅在 `generate_strategy=generate_and_push` 或后续 `execute(remote)` 时必填

输出至少包含：`code_file`、`config_files`、`branch`、`commit`、`generate_strategy`、`push_result`、`warnings`、`status`、`error`。

**埋点写入（强制执行）**：完成代码生成后，**必须**将本阶段内存记录的 `knowledge_base_read` / `knowledge_base_used` 写入 `<工作目录>/.api-mind/metrics.json`。不得为了埋点回溯读取历史、重新打开知识库或扫描文档；未读取外部领域知识库时直接写 `0`。此步骤不可跳过。

### 4.2 Execute

公共输入：

- `execution_mode`: `local` / `remote`，默认 `local`
- `api_test_repo`: 本地 api_test 仓库路径
- `code_file`: 需要执行的 Python case 文件；可为绝对路径，也可为 `api_test_repo` 内相对路径
- `target_case_dir`: case 所在目录；远端执行必填，本地执行可从 `code_file` 推导
- `output_dir`: 当前特性工作目录，用于写入 execute 日志与状态

本地额外输入：`test_env`、`tag_env`、`idc_env`、`duck_auth_token`、`pytest_args`、`run_api_test_quiet`。

远端额外输入：`target_branch`、`username`、`user_token`、`tag_env`、`idc`、`resolve_plan`。

输出按模式分支：

- local：`execution_mode`、`command`、`initial_exit_code`、`final_exit_code`、`log_file`、`fix_attempted`、`fix_applied`、`fix_reason`、`fix_summary`、`retry_count`、`status`、`error`
- remote：`execution_mode`、`trigger_uuid`、`plan_id`、`ttat_task_id`、`execution_url`、`status`、`error`

**埋点写入（强制执行）**：执行结束后（无论 success / failed），**必须**复用本次执行输出、pytest 摘要 / 本地日志路径与远端执行元信息快速写入 `case_info_list[]`。优先使用 metrics 脚本或 Python 执行脚本产出的结构化摘要写入，模型只补充失败归因小映射，不在响应中展开大段 JSON。只处理本次执行范围内的 case；失败 case 再读取 `../metrics/docs/failure_category.md` 选定枚举，成功 case 写 `""`；一条 case 都没跑出来时写 `[]`。不得为了埋点重复扫描 api_test 仓库、反复读取大日志或重新触发本地 / 远端执行。此步骤不可跳过。

### 4.3 Report

输入：`execution_mode`、`output_dir`；远端报告额外需要 `plan_id`、`ttat_task_id`、`user_token`、`proto`；本地报告只需要本地执行日志。

输出：`sub_task_id`、`report_json`、`report_file`、`local_log_file`（本地模式可选）、`status`、`error`。

## 5. 全局严格约束

1. **generate 关键信息先确认**：生成 / 更新代码前，必须通过 `AskUserQuestion` 明确确认 `api_test_repo` 与 `target_case_dir`；其中 `api_test_repo` 使用 pydriver 提供的绝对路径（如 `/Users/bytedance/Desktop/api_test`）或用户输入的绝对路径，`target_case_dir` 必须由用户主动输入为相对 `api_test_repo` 的仓库内相对路径（如 `tests/content_discovery/llm_gen/cases`）。`target_branch` 只在 `generate_and_push` 或后续远端执行时确认。
2. **确认前只读不写**：generate 关键输入确认前，只能读取 `case.md` / `spec.md` / `test/task.md` 并在内存中推导 `.env` 候选内容，不得写入 spec 工作目录或 api_test 仓库。
3. **不得扫描推导落点**：pydriver 不得主动搜索 / 扫描 api_test 仓库来推荐或决定 `target_case_dir`；只有在用户输入 `target_case_dir` 后，才能对该目标目录做定向校验与最小范围复用检查。
4. **默认本地执行**：execute 未显式指定远端时必须走 local，严禁误触发 TTAT。
5. **本地执行必须走脚本**：不得直接在任意目录运行 `pytest`；必须通过 `scripts/run_api_test.sh` 显式或隐式定位 `api_test_repo` 后执行。
6. **远端执行必须已 push**：目标代码未 push 到指定远端分支时，不得触发 TTAT。
7. **Git 审计**：切分支前、提交前、push 前必须用 `git status` / `git log` 审计目标路径，发现用户已有同路径提交或未推送改动时先沟通处理策略。
8. **配置唯一来源**：api_test runtime config 同步只能来自当前 spec `.env`；不能拿 sibling case 的路由配置当 source of truth。
9. **鉴权显式处理**：非公开 HTTP API 必须优先整合 `case.md` / `.env.test_account` / `.env.cookie` 中的 auth；若只能从 sibling case 推断，必须记录 warning。
10. **最小改动**：只改 case 文件、必要 config，以及确有必要时的最小 `conftest.py` / client 补丁或新建文件。
11. **复用优先、模板兜底**：`conftest.py` 仅复用用户确认的 `target_case_dir` 内文件；不得向父目录逐级查找或复用父级 `conftest.py`。目标目录缺失时按 resources 模板在 `target_case_dir` 最小生成；client 与命名风格优先复用当前目录既有约定。
12. **断言保持可读可审计**：自然语言或半结构化断言必须在 generate 阶段降解为明确的 Python `assert` 语句。
13. **报告依赖 execute 元信息**：远端报告没有 `plan_id` / `ttat_task_id` 时，不得猜测或拼接远端结果路径；本地报告只返回本地日志证据 / 最小摘要。
14. **避免重复确认与重复审计**：同一轮中用户已确认的 `api_test_repo`、`target_case_dir`、`target_branch`、`generate_strategy` 复用内存和状态，不再次 AskUserQuestion；Git 审计仅在切分支 / 提交 / push 前或目标目录发生变化时执行，local execute 不做 push 相关审计。
