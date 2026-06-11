# py_driver execute(remote)

本文件仅在 `execution_mode=remote` 时读取。remote 只在用户明确要求“远端运行 / TTAT / 平台执行 / remote / 触发远端”，或上层显式传入 `execution_mode=remote` 时使用。

## 1. 输入与输出

输入：

- `api_test_repo`: 本地 api_test 仓库路径，用于校验目标目录与 Git 状态
- `target_case_dir`: api-test 中 case 所在目录，必须是仓库内相对路径或可转换为相对路径
- `target_branch`: 已 push 的目标分支
- `username`: 触发执行的用户名
- `user_token`: TTAT 鉴权 token
- `tag_env`: 执行环境 runtime_config，例如 `prod`
- `idc`: 执行环境 IDC，例如 `sg1` / `maliva`
- `resolve_plan`: 是否在 trigger 后继续解析 `plan_id` / `ttat_task_id`，默认 true

输出：

- `execution_mode=remote`
- `trigger_uuid`
- `plan_id`（若已解析）
- `ttat_task_id`（若已解析）
- `execution_url`（若已解析）
- `status`
- `error`

## 2. 脚本契约

必须复用 `scripts/ttat_execute.sh`，并按需读取 `scripts/README.md`。

- `trigger` 子命令负责调用 TTAT trigger API。
- 成功后必须输出：`TTAT_TRIGGER_UUID=<uuid>`。
- `get-trigger-result` 子命令负责将 uuid 解析为：`TTAT_PLAN_ID=<plan_id>`、`TTAT_TASK_ID=<task_id>`、`TTAT_EXECUTION_URL=<url>`。

## 3. 标准流程

1. 确认执行模式是 remote；默认 execute 不允许误触发远端 TTAT。
2. 确认代码已 push 到 `target_branch`。
   - 若分支本地有未 push 改动，不得触发远端执行。
   - 若发现远端领先或本地污染，先返回失败并说明原因。
3. 确定远端执行目录：`target_case_dir` 必须是 api-test 仓库内路径，传给 TTAT 的 `directory_paths` 使用仓库内相对路径，不使用本机绝对路径。
4. 确定执行环境：优先使用本次 case 目标配置中已确认的 `tag_env` 与 `idc`，不得在 execute 阶段擅自切换环境。
5. 调用脚本触发执行，成功后解析并记录 `trigger_uuid`。
6. 若 `resolve_plan=true`，继续调用 `get-trigger-result` 解析 `plan_id` / `ttat_task_id` / `execution_url`。
7. 返回执行元信息。remote execute 当前只负责“远端触发 + 元信息采集”，不负责自动修复，也不负责本地重跑。

## 4. 调用示例

```bash
py_driver/scripts/ttat_execute.sh trigger \
  --branch <target_branch> \
  --directory-path <target_case_dir_relative_to_repo> \
  --username <username> \
  --tag-env <tag_env> \
  --idc <idc> \
  --resolve \
  --wait-seconds 30
```

至少解析：

```bash
TTAT_TRIGGER_UUID=...
```

开启 `--resolve` 时还需解析：

```bash
TTAT_PLAN_ID=...
TTAT_TASK_ID=...
TTAT_EXECUTION_URL=...
```

## 5. 安全约束

- 未显式 remote 意图时禁止触发 TTAT。
- 目标代码未 push 时禁止触发 TTAT。
- 不自动 `push --force`，不在 execute 阶段替用户补做未确认的提交 / push。
- 远端执行失败不触发本地自动修复；如需修复，应回到 generate 或 local execute 的修复流程。
