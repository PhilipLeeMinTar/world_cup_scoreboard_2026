# go_driver execute

本文件仅在 Go `execute` 阶段读取，负责风险拦截、Mock 协调、执行 `go test` 与安全自愈。

## 0. 前置门禁检查

上层必须已完成 `apimind-metrics start execute`，且 `<工作目录>/.api-mind/metrics.json` 存在并包含 `start_time`。缺失时立即中断。

## 1. 风险拦截

1. 写操作接口（POST / PUT / DELETE 等）只能在安全隔离环境（BOE / localhost 等）执行；高危环境且无白名单豁免时终止。
2. 扫描生成代码中的 `ctx.AuthHeadersFor("<profile>")`，确认 `<specDir>/auth.yaml.profiles` 均已定义。
3. 如 `state.json.warnings[]` 含 `secret_runtime_missing`，按依赖环境阻断处理，fail-fast 或标记 `SKIPPED/BLOCKED`。

## 2. Mock 协调

若用例包含 Bytemock 配置，按需读取 `../../mock.md`：

- 安装 / 准备 api-mock 技能
- 准备 Bytemock 前置资源
- 协调 permanent rules

## 3. 触发测试

1. 处理依赖鉴权，例如通过 `user_jwt` 获取 PaaS GW Token，并仅在本次 shell 中 `export APITEST_TOKEN=<jwt>`。
2. 不设置 `APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR`；这些路径由生成代码的 `specDir()` 自治解析。
3. 清理旧版日志后，必须先创建 `<specDir>/test/api_test_logs/`，并将 `go test` 的 stdout/stderr 完整保存为 `<specDir>/test/api_test_logs/execution_result.log`。
4. 执行命令必须包含 `GOTOOLCHAIN=auto GOWORK=off`，通过 `tee` 落盘并保留 `go test` 的真实退出码。示例：

```bash
export APITEST_TOKEN=<paas-gw JWT>
set -o pipefail
mkdir -p "<specDir>/test/api_test_logs"
GOTOOLCHAIN=auto GOWORK=off go test -v -count=1 -run '^Test<MethodPascal>$' ./tests/integration/<method_snake>/... 2>&1 | tee "<specDir>/test/api_test_logs/execution_result.log"
```

   若运行其他生成用例，仅替换 `-run` 与 package 路径；`execution_result.log` 的路径和文件名不得改变。
5. runtime 仍会写入 `<specDir>/test/api_test_logs/apitest_<case_id>.log`；该类细粒度日志仅作为失败 case 的排障证据，不作为成功 case 报告生成的默认输入。

## 4. 安全自愈修复

仅当 `auto_fix=true` 且失败高置信度归因为用例实现问题时，才允许修复并重跑；最多 `max_retries` 次。

允许修复：断言 JSONPath 错误、响应 Wrapper 取层错误、IDL 结构更新导致字段拼写错误、生成代码接线错误。

禁止修复：放宽 / 删除业务预期断言、把 actual 抄成 expected、篡改源逻辑代码、将环境 / 鉴权 / 被测服务问题包装成用例修复。

## 5. 埋点业务字段

执行结束后（无论 success / failed），默认使用脚本采集 metrics，避免模型上下文膨胀：

- **默认路径**：调用 `../../metrics/scripts/build_execute_metrics.py`，LLM 仅需提供失败 case 的 `--failure-category` 小映射；已有内存 PSM 时可传 `--psm`，否则脚本复用 `metrics.json.psm`。详见 `../../metrics/docs/business_fields.md` 的"脚本化采集"章节。
- **手动兜底**：仅当脚本输入缺失且 case 数 < 10 时允许，复用 `execution_result.log`、`triage.yaml` 与 `apitest_<case_id>.log` 文件名快速写入摘要；不得在响应中展开大段 `case_info_list[]`。LogID 只能对指定 `apitest_<case_id>.log` 做定向查询；只有识别到失败 / ERROR case 时，才允许读取对应日志做失败归因并按需读取 `failure_category` 枚举。

成功 case 的 `failure_category` 写 `""`；一条 case 都没跑出来时写 `[]`。不得为埋点扫描无关日志目录、阅读全文补字段或重新执行测试。

## 6. 执行后强制检查清单

execute 阶段结束前，**必须逐项确认**以下步骤全部完成，缺一不可：

- [ ] `go test` 已执行，stdout/stderr 已保存到 `<specDir>/test/api_test_logs/execution_result.log`
- [ ] 已调用 `build_execute_metrics.py` 脚本采集 execute 业务字段（`case_info_list`、统计计数等）
- [ ] `metrics.json` 中已包含 `execute_status`、`total_count`、`pass_count`、`fail_count`、`case_info_list` 字段
- [ ] 已执行 `apimind-metrics end execute --workdir <工作目录>/.api-mind --jwt "<会话内存 JWT>"`，并确认埋点上报成功；若失败按 metrics end 失败策略处理，不得跳过上报动作

> 脚本调用示例：
> ```bash
> python3 .cursor/skills/api-mind/metrics/scripts/build_execute_metrics.py \
>   --workdir <specDir>/test/.api-mind \
>   --log-dir <specDir>/test/api_test_logs \
>   --test-file tests/integration/<method>/<method>_test.go \
>   --psm '["<psm>"]'
> ```
