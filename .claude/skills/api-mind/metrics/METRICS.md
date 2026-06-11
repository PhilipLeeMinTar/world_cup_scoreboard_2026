# api-mind 埋点协议（metrics/METRICS.md）

本文档只保留 `api-mind` 埋点生命周期、CLI 门禁、快速路径与按需加载索引；字段明细、枚举和异常处理按需读取 `docs/`。

## 1. 生命周期门禁

每个子任务（`generate` / `execute` / `report`）串行执行，并且生命周期固定为：

```text
start → 写入公共字段 → driver/SKILL 写入业务字段 → end
```

强约束：

1. 子任务异常退出（崩溃 / 用户中断）时不调用 `end`，本次数据丢弃。
2. `end` 因 schema 校验失败时，只修复 `metrics.json` 中的字段后重试 `end`，严禁重新 `start`。
3. `end` 因网络 / JWT 问题失败时，最多重试 3 次，仍不得重新 `start`。
4. 只有子任务完全重新执行时，才允许重新 `start`。

所有埋点产物落在：

```text
<工作目录>/.api-mind/
├── state.json              # 业务状态，不属于埋点协议
├── metrics_common.json     # 5 个公共字段缓存
└── metrics.json            # 当前子任务埋点数据，每个子任务覆盖
```

工作目录取当前 api-mind 调用上下文：单 PSM 通常为 `FEATURE_DIR/test/`，多 PSM 可为 `FEATURE_DIR/test/<PSM>/`。

## 2. 性能目标与快速路径

metrics 是旁路逻辑，除 `start/end` 外不得主导 api-mind 总耗时；无法快速获取的非必需字段直接降级（字符串 `""`、数组 `[]`、int `0`），不得重复执行核心任务。

快速路径强约束：

1. **会话级复用**：同一轮只检查一次 Node / CLI、只获取一次 `gdpa-cli login -p cn` 结果；JWT 仅内存复用，禁止落盘。`metrics/METRICS.md` 仅在安装 / 排障 / 字段含义不清时读取，且最多一次。
2. **脚本优先**：公共字段用 `scripts/build_common_metrics.py`，execute 字段优先用 `scripts/build_execute_metrics.py`；模型只传已有内存值与失败归因小映射，不在响应中展开大段 JSON。
3. **缓存优先**：`metrics_common.json` 完整时直接复用；缓存缺失时由脚本有限读取 `test/task.md` / `case.md` 并执行最少 git 命令。不得为 metrics 完整阅读 `spec.md`、扫描 api_test 仓库或查询外部系统。
4. **随主流程记录**：generate 记录知识库读取 / 使用布尔值；execute 复用执行结果、日志文件名和 `triage.yaml`；report 复用报告路径。禁止事后扫描产物反推字段。
5. **失败归因按需**：仅 execute 失败 / error case 读取 `docs/failure_category.md` 并归因；成功 / skip case 的 `failure_category` 写 `""`。
6. **组合任务少走子进程**：同一轮包含多个子任务时，Node/CLI/JWT 检查、`build_common_metrics.py` 缓存采集、driver 文档读取均只做一次准备；每个子任务仍必须独立 `start/end`，但不得在每个子任务前重复执行安装检查、重复 login 或重复读取字段文档。

## 3. CLI 用法 / 安装（使用 api-mind 前必须完成）

要求 Node.js ≥ 18。

```bash
npm install -g @byted/apimind-metrics@latest --registry=https://bnpm.byted.org
apimind-metrics --help
```

`start/end`：

```bash
apimind-metrics start <command> --workdir <工作目录>/.api-mind
apimind-metrics end <command> --workdir <工作目录>/.api-mind --jwt "<会话内存 JWT>"
```

- `<command>` 只能是 `generate` / `execute` / `report`。
- `--jwt` 使用会话开始时已获取的内存 JWT；若当前会话尚未获取，才允许执行一次 `gdpa-cli login -p cn` 兜底。

## 4. 按需加载规则

| 场景 | 读取文件 | 说明 |
| --- | --- | --- |
| 写入 5 个公共字段 | 优先执行 `scripts/build_common_metrics.py`；字段含义不清时才读 `docs/common_fields.md` | 脚本会先复用 `metrics_common.json`；缓存完整时不得读取字段文档 |
| 写入 generate 业务字段 | `docs/business_fields.md` 的 generate 小节 | 仅 generate 阶段首次需要字段定义时读取；字段值来自主流程内存标记 |
| 写入 execute 业务字段 | 优先执行 `scripts/build_execute_metrics.py`；字段含义不清时才读 `docs/business_fields.md` 的 execute 小节 | 字段值来自执行结果与定向日志查询；需要失败归因时再读 `docs/failure_category.md` |
| 写入 report 业务字段 | `docs/business_fields.md` 的 report 小节 | 仅 report 阶段读取；字段值直接使用已生成报告路径 |
| 处理 end 失败 / 异常退出 | `docs/end_handling.md` | 仅 end 失败或需要判断是否补报时读取 |

CLI 托管字段 `command`、`start_time`、`end_time` 由 CLI 自动管理。模型读写 `metrics.json` 时必须保留已有字段，不新增同名字段、不修改 CLI 字段。

## 5. 接入清单

- [ ] 会话开始：一次性确认 CLI 可用，并获取一次内存 JWT（供 `user_name` 解码与所有 `end` 调用复用）。
- [ ] 派发前：执行 `apimind-metrics start <cmd> --workdir <工作目录>/.api-mind`。
- [ ] start 后：执行 `scripts/build_common_metrics.py --workdir <工作目录>/.api-mind --user-name <username>`，由脚本复用缓存或最小采集并写回缓存。
- [ ] 执行中：driver / 主流程优先通过脚本写业务字段；只有字段定义不清时才按需读取 `docs/business_fields.md`。
- [ ] 派发后：执行 `apimind-metrics end <cmd> --workdir <工作目录>/.api-mind --jwt "<会话内存 JWT>"`。
