---
name: api-mind/go_driver
description: api-mind 的 Go 语言测试用例驱动。负责将 case.md 生成 / 修改为基于 apitest runtime 的 *_test.go，执行 go test，并按日志生成报告。本文件只保留调度契约、阶段路由和全局底线；阶段细节按需读取 docs/ 下文件。
---

# Go Driver: `apitest` + `go test`

本 Driver 只接受 `*_test.go` + `apitest` runtime 作为执行载体，由 `api-mind/SKILL.md` 调度，不直接处理用户上层意图与任务组装。

## 1. 按需加载规则

收到上层分发后，先识别子任务，再只读取必要文件：

| 子任务 | 必读文件 | 何时读取 |
| --- | --- | --- |
| `generate` | `docs/generate.md` | 需要解析 `case.md`、同步 runtime、生成 / 修改 Go 测试代码或配置时 |
| `execute` | `docs/execute.md` | 需要运行 `go test`、做风险拦截、Mock 协调或安全自愈时 |
| `report` | `docs/report.md` | 需要基于执行日志生成 `test_report.md` 时 |
| 复用 / 新建 / 修改决策 | `docs/decision.md` | `generate` 阶段进入用例分流时，或需要判断 Reuse / Amend / New 时 |

资源索引：

- API 测试规范：`apitest.md`
- 模板：`resources/go_test_template.md`、`resources/env_template.md`
- 报告指南：`resources/test_report_guide.md`
- 可用区映射：`resources/zone_mapping.md`
- runtime 基准：`runtime/manifest.json` 与 `runtime/*.go`
- 脚本（确定性操作优先用脚本，避免读大文件进上下文）：
  - `scripts/sync_runtime.py`：同步 `runtime/` 到业务仓库 `tests/integration/apitest/`（`generate` §2），免读 `manifest.json` 哈希清单
  - `scripts/scan_case.py`：扫描 `case.md` 未解析项与鉴权变量（`generate` §1），免全文读 `case.md`；并提取每个 case 的非鉴权 header 清单（`case_headers[]`），作为 Headers 生成与自检的**权威来源**，降低非鉴权 header 遗漏概率
- Mock：上层或阶段文档按需读取 `../mock.md`

## 2. Driver 接口摘要

### 2.1 Generate

输入：

- `case_file`: `case.md` 文件路径，默认 `FEATURE_DIR/test/case.md`
- `output_dir`: 当前特性工作目录，默认 `FEATURE_DIR/test/`

输出：

- `code_file`: 生成或修改的测试代码文件及包路径信息
- `status`: `success` / `failed`
- `error`: 失败时的具体链路错误信息

埋点：生成过程中同步维护外部知识库读取 / 使用的内存布尔值，生成完成后直接写入 `knowledge_base_read` / `knowledge_base_used`；不得为埋点回溯读取历史或重新扫描文档。

### 2.2 Execute

输入：

- `code_file`: 需执行的代码路径或包配置
- `work_dir`: 工作目录
- `auto_fix`: 是否开启自动修复，默认 `true`
- `max_retries`: 最大重试次数，默认 `3`

输出：

- `status`: `success` / `failed`
- `results`: 日志目录绝对路径和执行状态摘要
- `fix_history`: 修复历史与核心改动点
- `error`: 最终失败原因

埋点：执行结束后（无论成功 / 失败），默认调用 `../metrics/scripts/build_execute_metrics.py` 复用本次执行结果、日志文件名、`execution_result.log` 与 `triage.yaml` 快速写入 `case_info_list[]`；模型仅提供失败归因小映射。仅失败 / error case 做失败归因，不得为埋点重复扫描日志、在响应中展开大段 JSON 或重新执行测试。

### 2.3 Report

输入：

- `execute_results`: Execute 阶段结果与日志目录
- `output_dir`: 报告输出目录

输出：

- `report_file`: `test_report.md` 路径
- `status`: `success` / `failed`
- `error`: 报告生成错误

## 3. 全局严格底线

1. **唯一执行路径**：禁止用 `curl`、外部脚本或第三方客户端替代 `go test` + `apitest`；`go test` 执行 stdout/stderr 必须保存到 `<specDir>/test/api_test_logs/execution_result.log`，报告优先以该文件为执行结果来源，只有失败 / Error case 才读取对应 `apitest_<case_id>.log`。
2. **上层埋点门禁**：进入任一阶段前，`<工作目录>/.api-mind/metrics.json` 必须存在且包含 `start_time`。缺失时立即中断，提示上层未执行 `apimind-metrics start`。
3. **配置三层分离**：
   - `<specDir>/.env` 只存路由：`psm` / `host` / `env` / `branch` / `zone` / `idc` / `cluster`，多 PSM 使用 `default_service` + `services.<service_key>`。
   - `<specDir>/auth.yaml` 存业务鉴权 header profile，Go 代码通过 `ctx.AuthHeaders()` / `ctx.AuthHeadersFor(...)` 引用；`case.md → Request Parameters → Headers` 是被测业务 HTTP 请求头，只能经 `apitest.HTTPRequest.Headers` 传入，不得作为 paas-gw / AGW 外层 header、`.env` 字段或 `RpcContext` 传递。
   - PaaS-GW 用户 JWT 只通过 `APITEST_TOKEN` 环境变量提供，不写入 git-tracked 文件。
4. **路径自治**：生成代码必须通过 `runtime.Caller(0) + {{SPEC_DIR_REL}}` 解析 `<specDir>`，不得读取 `APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR`。
5. **先查后问**：业务未决数据排查路径为 `case.md` → IDL 契约 → 知识库 → 同级现有用例；穷尽后才向用户提问，并附排查轨迹。
6. **依赖环境阻断**：鉴权 profile 缺失、`secret_runtime_missing` 等依赖缺失时，必须 fail-fast / `SKIPPED` / `BLOCKED`，不得发起无效请求。
7. **模板合规**：新建或修改后的 Go 代码必须符合 `resources/go_test_template.md` 三段式结构，并以 `apitest.NewContextFromSpec(t, specDir())` 为唯一入口。
