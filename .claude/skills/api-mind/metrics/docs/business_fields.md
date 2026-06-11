# metrics 子任务业务字段

本文件仅在需要写入具体子任务业务字段时读取。

业务字段必须走快速路径：优先使用子任务执行过程中已经得到的内存状态、输出路径、执行日志索引和文件名；不得为了补齐 metrics 字段重新扫描仓库、重复解析大文件、重复调用外部系统或重复执行核心任务。快速路径拿不到的非必需字段按默认值写入。

## generate（由 driver 写入）

### 知识库范围定义

**"知识库"仅指外部领域知识 SKILL**，即独立于 api-mind 的、提供业务/技术领域知识的 SKILL 文档。典型示例：

- `api-guidelines-knowledge` — API IDL 设计规范
- `code-styleguide-knowledge` — Go 代码规范
- `storage-knowledge` — 存储组件使用指南（RDS/Redis/ByteDoc 等）
- `kitex-knowledge` — Kitex 框架知识
- `hertz-knowledge` — Hertz 框架知识
- `testing-knowledge` — 单元测试知识
- 其他 `.coco/skills/` 或 `.claude/skills/` 下除 `api-mind/` 以外的 `*-knowledge` SKILL

**以下明确不属于"知识库"，读取它们不应计入 `knowledge_base_read` / `knowledge_base_used`**：

- api-mind 自身的所有内部文档：`SKILL.md`、`py_driver/**`、`go_driver/**`、`metrics/**`、`mock.md`
- api-mind 自身的模板与脚本：`py_driver/resources/**`、`py_driver/scripts/**`、`go_driver/resources/**`、`go_driver/runtime/**`
- 被测接口的 IDL 文件、BAM 文档、Overpass 查询结果
- `case.md`、`spec.md`、`test/task.md` 等测试规格输入文件
- `AGENTS.md`、`CONSTITUTION.md`、`.test_config.ini` 等仓库级配置文件

### 字段定义

generate 阶段不得在结束后回溯本轮读取历史。driver 应在主流程读取外部领域知识库时同步维护两个内存布尔值：`knowledge_base_read_seen` 与 `knowledge_base_used_seen`，结束时直接写入 `1/0`。

| 字段 | 类型 | 含义 | 获取方式 |
| --- | --- | --- | --- |
| `knowledge_base_read` | int | 本次 generate 是否实际读取了外部领域知识库内容；0=否，1=是 | 只要本轮真正打开 / 读取了上述"知识库范围定义"中列出的任一外部知识库文件就写 `1`，否则写 `0`。读取 api-mind 内部文档、模板、测试输入文件均不计入 |
| `knowledge_base_used` | int | 外部知识库内容是否影响生成结果；0=否，1=是 | 至少一条字段值 / 约束 / 代码模式源自外部知识库内容即写 `1`，只读未用写 `0`。源自 api-mind 模板或 case.md 的内容不计入 |

## execute（由 driver 写入）

`case_info_list` 是数组；一条 case 都没跑出来时也必须写 `[]`。

### 日志读取约束

写入 `case_info_list[]` 时，**禁止直接全量阅读实际的 `apitest_*.log` 文件**。字段获取必须优先使用文件名、`execution_result.log` 与定向 `grep`：

- `case_id`：通过 `apitest_<case_id>.log` 文件名解析，不读取文件内容。
- `status`：通过 `<specDir>/test/api_test_logs/execution_result.log` 中的执行结果解析。
- `biz_log_id`：仅允许在指定的 `apitest_<case_id>.log` 中用 `grep "Business.LogID: "` 查找。
- `bits_log_id`：仅允许在指定的 `apitest_<case_id>.log` 中用 `grep "Gateway.LogID: "` 查找。
- 只有需要分析失败原因时，才允许阅读**指定失败用例**对应的 `apitest_<case_id>.log`；成功 / 跳过用例不得为补充字段而阅读全文。
- `case_info_list[]` 只覆盖本次执行范围内的 case；不得为了发现历史 case 扫描整个仓库或无关日志目录。
- LogID 提取只对本次执行产出的、由文件名定位到的指定日志执行定向 `grep`；grep 无结果立即写 `""`，不得继续阅读全文补找。

| 字段 | 类型 | 说明 | 获取方式 |
| --- | --- | --- | --- |
| `case_info_list[].case_id` | string | 用例 ID | 从 `apitest_<case_id>.log` 文件名中提取 `<case_id>` |
| `case_info_list[].status` | string | `pass` / `fail` / `skip` / `error` | 解析 `<specDir>/test/api_test_logs/execution_result.log` 的 `go test -v` 结果 |
| `case_info_list[].mock` | int | 是否用到 mock；0=否，1=是 | 从用例定义 / triage 信息 / 生成时 mock 标记获取，不为该字段全量读取 `apitest_*.log` |
| `case_info_list[].has_to_be_filled` | int | 是否存在需用户补充字段；0=否，1=是 | 从用例定义 / 生成产物中的待补充标记获取，不为该字段全量读取 `apitest_*.log` |
| `case_info_list[].biz_log_id` | string | 业务接口 LOGID，缺失写 `""` | 对指定 `apitest_<case_id>.log` 执行 `grep "Business.LogID: "` 提取；不得阅读全文 |
| `case_info_list[].bits_log_id` | string | BITS 调用 LOGID，未使用写 `""` | 对指定 `apitest_<case_id>.log` 执行 `grep "Gateway.LogID: "` 提取；不得阅读全文 |
| `case_info_list[].psm` | string[] | 该 case 涉及的 PSM 列表 | 从用例定义、IDL / BAM 元信息或生成产物获取，不为该字段全量读取 `apitest_*.log` |
| `case_info_list[].failure_category` | string | 成功 case 写 `""`；失败 case 按 `docs/failure_category.md` 选枚举 | 仅失败 / error case 可阅读对应 `apitest_<case_id>.log` 辅助归因，并结合 `docs/failure_category.md` 选枚举 |

推荐写入顺序：

1. 从本次执行命令、测试包 / 文件或已知生成清单确定候选 case 范围；若存在 `apitest_<case_id>.log`，只用文件名补齐 `case_id`。
2. 单次解析 `execution_result.log`，生成 `case_id -> status` 映射；无法定位但本次进程级失败时写 `error`，完全无运行记录写 `skip`。
3. 读取已生成的 `triage.yaml` / 用例定义摘要补齐 `mock`、`has_to_be_filled`、`psm`；缺失则按默认值写入。
4. 对每个本次执行 case 的指定日志用 `grep` 提取 `Business.LogID: ` 和 `Gateway.LogID: `；无命中写 `""`。
5. 仅对 `fail` / `error` case 读取对应失败日志并按需读取 `docs/failure_category.md` 归因；其他 case 的 `failure_category` 直接写 `""`。

### 脚本化采集（默认路径，防上下文膨胀）

execute metrics 默认使用脚本构造 `case_info_list[]`，禁止 LLM 在响应中手动拼接 JSON。只有脚本缺少必要输入且本次 case 数很少时，才允许走手动兜底路径：

```bash
python3 .coco/skills/api-mind/metrics/scripts/build_execute_metrics.py \
  --workdir <specDir>/test/.api-mind \
  --log-dir <specDir>/test/api_test_logs \
  --test-file tests/integration/<method>/<method>_test.go \
  --psm '["tiktokqa.quality.god"]' \
  --failure-category '{"TC-002":"env_issue","TC-003":"business_bug"}'
```

脚本自动完成：case_id 提取、status 解析、LogID 定向提取、字段组装、统计计数。LLM 仅需提供 `--failure-category`（失败 case 的归因映射，JSON 格式）和可选 `--psm`（已有内存 PSM 列表）。脚本读取已有 `metrics.json` 中的公共字段，追加 execute 业务字段后写回。

手动兜底必须同时满足：case 数量 < 10、已有执行摘要足够、不会在响应中展开大段 JSON、不会阅读全文补字段。否则继续使用脚本并对缺失字段写默认值。

## report（由 api-mind 主流程写入）

report 阶段不得重新搜索报告文件。生成 `test_report.md` 的函数 / 子流程返回报告路径后，直接写入该绝对路径；如果报告生成失败且没有路径，写 `""`。

| 字段 | 类型 | 获取方式 |
| --- | --- | --- |
| `report_file_path` | string | 生成 `test_report.md` 后取绝对路径 / `realpath` |
