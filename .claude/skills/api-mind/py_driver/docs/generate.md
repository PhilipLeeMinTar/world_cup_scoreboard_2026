# py_driver generate

本文件仅在需要生成 / 更新 Python case 时读取，作为 generate 阶段总控。细节按需读取子文件，避免一次性加载仓库准备、配置同步、代码规范与 push 策略的全部内容。

## 0. 前置门禁检查

上层 SKILL 必须已完成：

- `apimind-metrics start generate` 成功返回
- 5 个公共字段已写入 `<工作目录>/.api-mind/metrics.json`

防御性校验：如果 `metrics.json` 不存在，或缺少 `start_time`，立即中断并报告“埋点未就绪”。

## 1. 按需加载规则

| 场景 | 读取文件 | 说明 |
| --- | --- | --- |
| 读取 spec 侧上下文、确认 api_test 仓库与落点 | `generate/context.md` | 每次 generate 必读 |
| 准备 api_test 仓库、Git 审计、分支处理 | `generate/repo_prepare.md` | 确认关键输入后读取 |
| 同步 runtime config、复用 / 补齐 conftest 与 client | `generate/config_client.md` | 需要写配置、conftest 或 client 时读取 |
| 生成 Python 测试文件与静态校验 | `generate/case_code.md` | 写 case 文件前读取 |
| 提交并 push | `generate/push.md` | 仅 `generate_strategy=generate_and_push` 或后续远端执行需要已 push 时读取 |

## 2. Generate 总流程

1. 读取 `generate/context.md`，获取 `case.md` / `spec.md` / `test/task.md` 上下文，并合并确认 `api_test_repo`、`target_case_dir`、生成策略 / 目标分支。
2. 读取 `generate/repo_prepare.md`，验证仓库、落点与 Git 状态；如涉及分支切换，必须先切分支，再生成代码。
3. 读取 `generate/config_client.md`，落盘当前 spec `.env`，同步 api_test runtime config，并复用 / 最小补齐 `conftest.py` 与 client。
4. 读取 `generate/case_code.md`，生成 / 修改测试文件并做静态校验。
5. 若策略为 `generate_and_push`，读取 `generate/push.md`，提交并 push 到用户确认的分支。
6. 直接写入本阶段内存记录的 `knowledge_base_read` / `knowledge_base_used`；不得为 metrics 重新扫描文档或回溯读取历史。

## 3. 输出

至少返回：

- `code_file`
- `config_files`
- `branch`
- `commit`
- `generate_strategy`
- `push_result`
- `warnings`
- `status`
- `error`
