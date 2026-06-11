# py_driver scripts

本目录是 `api-mind/py_driver` 的脚本契约说明，覆盖三类执行资产：

- `run_api_test.sh`：本地执行 Python api-test 用例，默认路径。
- `ttat_execute.sh`：显式 remote / TTAT / 平台执行时触发远端任务并解析执行 ID。
- `ttat_report.sh`：基于远端执行 ID 抓取 TTAT 结果并生成 JSON / Markdown 报告。

Python case 默认走本地执行；只有用户或上层显式指定 `execution_mode=remote`，或明确表达“远端执行 / TTAT / 平台执行”时，才允许触发 TTAT。

---

## 1. 通用约束

1. `execute(local)` 与 `execute(remote)` 同一轮只能选择一个。
2. 本地执行不得直接在任意目录运行 `pytest`，必须通过 `run_api_test.sh` 进入 `api_test_repo` 后执行。
3. 远端执行前必须确认代码已 push 到目标分支；未 push、远端领先或本地污染时不得触发 TTAT。
4. 远端报告必须依赖 execute 产出的 `plan_id` / `ttat_task_id`，不得猜测或拼接远端结果路径。
5. 本地执行不调用 `ttat_report.sh`，只返回本地日志证据或最小摘要。

---

## 2. `run_api_test.sh`：本地执行入口

### 2.1 作用

`api_test` 仓库的 `pyproject.toml`、`conftest.py`、顶层 import（`state` / `constants` / `clients` / `common` / `tools`）和部分脚本都假定：

```text
cwd == <api_test_repo>
```

直接从外层仓库运行 `pytest` 可能导致 rootdir、import 或日志目录错误。`run_api_test.sh` 负责先切换到 `api_test_repo`，再通过 Poetry 转发命令。

### 2.2 `api_test_repo` 解析顺序

1. `--api-test-dir <dir>` / `--api-test-repo <dir>`
2. `API_TEST_REPO=<dir>` / `API_TEST_DIR=<dir>`
3. 兼容旧布局：脚本位于外层仓库 `scripts/` 下时使用 `../tests/api_test`
4. 脚本父目录存在 `pyproject.toml` 时使用父目录

本地 execute 若外层仓库缺少 `scripts/run_api_test.sh`，可直接调用本 skill 资源脚本并显式传入 `--api-test-dir`，也可复制到外层仓库 `scripts/` 并赋予可执行权限。若目标脚本已存在且与资源不同，不要静默覆盖，应复用并记录 warning。

### 2.3 子命令

```bash
scripts/run_api_test.sh --api-test-dir <api_test_repo> pytest <args>      # poetry run pytest <args>
scripts/run_api_test.sh --api-test-dir <api_test_repo> test <case_path>   # poetry run pytest -v <case_path>
scripts/run_api_test.sh --api-test-dir <api_test_repo> manage <args>      # poetry run python manage.py <args>
scripts/run_api_test.sh --api-test-dir <api_test_repo> python <args>      # poetry run python <args>
scripts/run_api_test.sh --api-test-dir <api_test_repo> poetry <args>      # poetry <args>
scripts/run_api_test.sh --api-test-dir <api_test_repo> shell              # shell in api_test_repo, activates .venv when available
scripts/run_api_test.sh --api-test-dir <api_test_repo> -- <cmd> [args...] # poetry run <cmd> [args...]
```

标准用例执行：

```bash
TEST_ENV=sg_prod TAG_ENV=prod IDC_ENV=my DUCK_AUTH_TOKEN=<token> \
  scripts/run_api_test.sh --api-test-dir <api_test_repo> test \
  tests/path/to/test_xxx.py <pytest_args...>
```

### 2.4 环境变量提示

脚本会对常见缺失项打印 warning：

- `TEST_ENV`：如 `sg_prod` / `va_prod` / `ttp_prod`
- `IDC_ENV`：如 `my` / `sg` / `va`
- `TAG_ENV`：如 `prod`
- `DUCK_AUTH_TOKEN` 或 `SECRET_KEY_TOKEN`：api-test / duck 鉴权 token

如需关闭提示：`export RUN_API_TEST_QUIET=1`。

---

## 3. `ttat_execute.sh`：远端执行入口

### 3.1 作用

用于显式 remote 场景，调用 TTAT trigger API 并按需把 trigger UUID 解析为 plan / task 信息。

依赖：`curl`、`python3`。鉴权 token 通过 `--user-token <token>` 或 `TTAT_USER_TOKEN` 传入，并以 `X-Custom-Token` 发送。

### 3.2 子命令与输出契约

- `trigger`：触发远端执行，成功后必须输出 `TTAT_TRIGGER_UUID=<uuid>`。
- `get-trigger-result`：将 uuid 解析为：
  - `TTAT_PLAN_ID=<plan_id>`
  - `TTAT_TASK_ID=<task_id>`
  - `TTAT_EXECUTION_URL=<ui_url>`

`trigger` 请求体关键字段：`branch`、`directory_paths`、`plan_type=regular`、`reruns`、`notify_users`、`disable_parallel`、`environment_configuration`、`trigger_by`、`trigger_platform=manual`、`plan_owner`、空 `markers`、空 `test_names`。

### 3.3 调用示例

```bash
py_driver/scripts/ttat_execute.sh trigger \
  --branch <target_branch> \
  --directory-path <target_case_dir_relative_to_repo> \
  --username <username> \
  --tag-env <tag_env> \
  --idc <idc> \
  --resolve \
  --wait-seconds 30 \
  --user-token "$TTAT_USER_TOKEN"
```

---

## 4. `ttat_report.sh`：远端报告入口

### 4.1 作用

基于 `plan_id` / `ttat_task_id` 抓取 TTAT task detail、suites、per-case report JSON 与日志附件，并解析生成：

- machine-readable JSON
- Markdown `test_report.md`

依赖：`curl`、`jq`、`python3`。鉴权 token 通过 `--user-token <token>` 或 `TTAT_USER_TOKEN` 传入。

### 4.2 子命令与输出契约

- `fetch`：拉取原始 TTAT 产物，写入 `raw/`、`meta/` 等目录。
- `parse`：解析已拉取产物，生成 JSON 与 Markdown 报告。
- `fetch-and-parse`：串联执行上述两步。

`fetch` / `fetch-and-parse` 至少输出：

- `TTAT_PLAN_ID=...`
- `TTAT_TASK_ID=...`
- `TTAT_SUB_TASK_ID=...`
- `TTAT_RESULT_DIR=...`
- `TTAT_EXECUTION_URL=...`

`parse` / `fetch-and-parse` 至少输出：

- `REPORT_JSON_PATH=...`
- `REPORT_MD_PATH=...`

### 4.3 解析规则与报告字段

- `--proto http`：从日志中的 `"resp": ...` 区域解析响应体。
- `--proto rpc`：从日志中的 `Response: {...}` 区域解析响应体。

Markdown 报告保持 Python driver 的简化格式：执行时间、执行链接、执行概况、结果详情。结果详情至少包含：`状态`、`测试类`、`用例名`、`UID`、`日志附件`、`响应解析`、`失败原因`。

### 4.4 调用示例

```bash
py_driver/scripts/ttat_report.sh fetch-and-parse \
  --plan-id <plan_id> \
  --task-id <ttat_task_id> \
  --output-dir <report_output_dir> \
  --proto <http_or_rpc> \
  --user-token "$TTAT_USER_TOKEN"
```

---

## 5. Driver 集成摘要

### 5.1 模式选择

1. 用户明确“本地运行 / local / pytest / 跑本地用例” → `execution_mode=local`
2. 用户明确“远端运行 / TTAT / 平台执行 / remote / 触发远端” → `execution_mode=remote`
3. 未明确指定 → `execution_mode=local`

### 5.2 Local execute

1. 接收并校验 `api_test_repo`，确保 `<api_test_repo>/pyproject.toml` 存在。
2. 确保可用且可执行的 `run_api_test.sh`。
3. 将 `code_file` 转为 `api_test_repo` 内相对路径。
4. 设置 `TEST_ENV`、`TAG_ENV`、`IDC_ENV`、`DUCK_AUTH_TOKEN`（或沿用外部已有值）。
5. 执行 `run_api_test.sh --api-test-dir <api_test_repo> test <case_path> [pytest_args...]`。
6. 将 stdout / stderr 写入 `<output_dir>/.api-mind/logs/py_driver_local_execute.log`。
7. 返回 `execution_mode=local`、exit code、log file、fix / retry 信息与状态。

### 5.3 Remote execute

1. 确认执行模式为 remote，且代码已 push 到 `target_branch`。
2. 使用仓库内相对路径作为 `directory_paths`，不得传本机绝对路径。
3. 使用已确认的 `tag_env` 与 `idc`，不得在 execute 阶段擅自切换环境。
4. 调用 `ttat_execute.sh trigger`，记录 `TTAT_TRIGGER_UUID`。
5. 若 `resolve_plan=true`，继续解析 `TTAT_PLAN_ID`、`TTAT_TASK_ID`、`TTAT_EXECUTION_URL`。

### 5.4 Report

1. 仅 remote 模式调用 `ttat_report.sh`。
2. 必须已有 `plan_id` 与 `ttat_task_id`。
3. 调用 `fetch-and-parse` 后解析 `TTAT_SUB_TASK_ID`、`REPORT_JSON_PATH`、`REPORT_MD_PATH`。
4. 本地模式返回 local execute 日志作为主要证据。

---

## 6. 当前限制

- `ttat_report.sh` 当前跟随 TTAT task detail 中第一个主 `sub_task`。
- HTTP / RPC 日志解析依赖当前 TTAT 日志格式；日志格式变化时需要调整解析规则。
- Python driver 报告是简化版，尚未完整对齐 Go driver 的失败分类能力。
