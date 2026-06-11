# py_driver report

本文件仅在需要生成 Python driver 执行报告时读取。

## 1. 职责

report 阶段负责：

1. 基于 execute 产出的 `plan_id` / `ttat_task_id` 抓取 TTAT 执行结果。
2. 获取 suites / per-case report json / log attachments。
3. 解析 HTTP 或 RPC 响应内容。
4. 生成结构化 JSON 结果与 Markdown `test_report.md`。

约束：完整报告抓取仅针对 `execution_mode=remote` 的 TTAT 结果。若 execute 使用本地模式：

1. 不调用 `ttat_report.sh`。
2. 返回本地执行日志作为主要证据：`local_log_file=<.../py_driver_local_execute.log>`。
3. 如上层需要 Markdown，可基于本地日志生成最小摘要，但不得伪造 `plan_id` / `ttat_task_id`。

## 2. 输入与输出

输入：

- `execution_mode`: execute 阶段使用的模式，默认继承 execute 输出
- `plan_id`: 远端 execute 阶段产出的 TTAT plan id
- `ttat_task_id`: 远端 execute 阶段产出的 TTAT task id
- `user_token`: TTAT 鉴权 token
- `proto`: `http` / `rpc`，用于决定日志解析方式
- `output_dir`: 报告输出目录

输出：

- `sub_task_id`: TTAT sub task id
- `report_json`: 结构化解析结果 JSON 路径
- `report_file`: Markdown 报告路径，通常为 `test_report.md`
- `local_log_file`: 本地模式下的日志证据（如适用）
- `status`
- `error`

## 3. 脚本契约

远端报告必须复用 `scripts/ttat_report.sh`，并按需读取 `scripts/README.md`。不要在 SKILL 主流程中散写另一套 TTAT 抓取逻辑。

脚本调用示例：

```bash
py_driver/scripts/ttat_report.sh fetch-and-parse \
  --plan-id <plan_id> \
  --task-id <ttat_task_id> \
  --output-dir <report_output_dir> \
  --proto <http_or_rpc>
```

至少解析：

```bash
TTAT_SUB_TASK_ID=...
REPORT_JSON_PATH=...
REPORT_MD_PATH=...
```

## 4. 标准流程

1. 接收 execute 元信息。
   - 远端报告依赖 `plan_id` / `ttat_task_id`。
   - 信息缺失时不得猜测路径或拼接 URL。
2. 抓取远端结果：调用 `fetch` 或 `fetch-and-parse`。
3. 解析执行产物：
   - suites 枚举测试类与测试用例。
   - per-case report json 提取 `status`、`uid`、`statusTrace`、attachment source。
   - attachment log 提取响应数据。
4. 按协议解析日志：
   - `proto=http`：解析 log 中 `"resp": ...` 对应响应体。
   - `proto=rpc`：解析 log 中 `Response: {...}` 对应响应体。
5. 输出 machine-readable JSON 与 Markdown `test_report.md`。

## 5. Markdown 报告格式

当前 Markdown 报告参考 go driver 的报告结构，使用 Python driver 简化字段：

- `测试执行报告`
- `执行时间`
- `执行链接`
- `执行概况`
- `结果详情`

`结果详情` 至少包含列：

- `状态`
- `测试类`
- `用例名`
- `UID`
- `日志附件`
- `响应解析`
- `失败原因`
