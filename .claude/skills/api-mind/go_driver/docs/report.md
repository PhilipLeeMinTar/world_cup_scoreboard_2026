# go_driver report

本文件仅在 Go `report` 阶段读取，负责聚合测试元数据、`go test` 执行结果与必要的失败证据，输出 Markdown 报告。

## 1. 输入与输出

输入：

- `execute_results`: Execute 阶段返回的结果与日志目录
- `output_dir`: 报告输出目录

输出：

- `report_file`: 最终 `test_report.md` 路径
- `status`: `success` / `failed`
- `error`: 失败原因

## 2. 标准流程

1. 读取代码中的 `WithCaseID(...)` 元信息、`triage.yaml` 分类状态，以及 `<specDir>/test/api_test_logs/execution_result.log`。
2. 报告状态判定必须优先来自 `execution_result.log` 中的 `go test -v` 结果（例如 `--- PASS` / `--- FAIL` / `FAIL` / `PASS` 行），不得默认遍历每个 `apitest_<case_id>.log`。
3. 只有当 `execution_result.log` 显示存在失败 / Error case 时，才允许读取对应的 `apitest_<case_id>.log`，提取断言证据、请求 `LogID`，并尝试调用调试工具抓取服务端分析结论。
4. 抓取成功时，仅提取【问题分析结论】的精要内容补充进报告，作为研发修复建议；成功 case 不查细粒度 runtime 日志。
5. 按 `../resources/test_report_guide.md` 渲染并覆写 `test_report.md`。

## 3. 埋点业务字段

Go report 自身不写 `report_file_path`；由 `api-mind/SKILL.md` 在报告生成后取绝对路径，并按 `../../metrics/METRICS.md` 写入。

## 4. 报告后强制检查清单

report 阶段结束前，**必须逐项确认**以下步骤全部完成，缺一不可：

- [ ] 已生成 / 覆写 `test_report.md`，并在返回结果中提供 `report_file` 路径
- [ ] 上层 `api-mind/SKILL.md` 已在拿到报告路径后取绝对路径 / `realpath`，并写入 `<工作目录>/.api-mind/metrics.json` 的 `report_file_path` 字段
- [ ] `metrics.json` 中已包含 `report_file_path` 字段；若报告生成失败且没有路径，字段值已写为 `""`
- [ ] 未为了埋点重新搜索报告文件或扫描无关目录
- [ ] 已执行 `apimind-metrics end report --workdir <工作目录>/.api-mind --jwt "<会话内存 JWT>"`，并确认埋点上报成功；若失败按 metrics end 失败策略处理，不得跳过上报动作
