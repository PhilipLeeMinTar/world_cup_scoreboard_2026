# py_driver execute(local)

本文件仅在 `execution_mode=local` 时读取。local 是 Python driver 的默认执行模式。

## 1. 输入与输出

输入：

- `api_test_repo`: 本地 api_test 仓库路径
- `code_file`: 需要执行的 Python case 文件；可为绝对路径，也可为 `api_test_repo` 内相对路径
- `output_dir`: 当前特性工作目录，用于写入日志与状态
- `test_env`: `TEST_ENV`，必须等于配置文件名 stem / JSON 顶层 key，例如 `sg_prod`
- `tag_env`: `TAG_ENV`，例如 `prod`
- `idc_env`: `IDC_ENV`，例如 `my` / `sg` / `va`
- `duck_auth_token`: 本地 TTAT / duck 鉴权 token；可由 `DUCK_AUTH_TOKEN` 或 `SECRET_KEY_TOKEN` 提供
- `pytest_args`: 额外 pytest 参数，例如 `-k some_case`
- `run_api_test_quiet`: 是否设置 `RUN_API_TEST_QUIET=1` 关闭环境变量提示，默认 false

输出：

- `execution_mode=local`
- `command`
- `initial_exit_code`
- `final_exit_code`
- `log_file`
- `fix_attempted`
- `fix_applied`
- `fix_reason`
- `fix_summary`
- `retry_count`（最多 3 次 fix-and-rerun）
- `status`
- `error`

## 2. 执行脚本

必须使用 `scripts/run_api_test.sh`，并按需读取 `scripts/README.md`。不得直接在任意目录运行 `pytest`。

脚本定位 `api_test_repo` 的方式：

1. `--api-test-dir /path/to/api_test`
2. 环境变量 `API_TEST_REPO=/path/to/api_test`
3. 兼容旧布局：脚本位于外层仓库 `scripts/` 下时回退到 `../tests/api_test`

如果外层仓库 `scripts/run_api_test.sh` 不存在，可以直接调用 SKILL 资源脚本，或复制到外层仓库后调用。若脚本已存在且与资源不同，不要静默覆盖，优先复用并记录 warning：`run_api_test.sh already exists and differs from skill resource`。

## 3. 标准流程

1. 确定 `api_test_repo`，调用脚本时通过 `--api-test-dir` 或 `API_TEST_REPO` 传入。
2. 校验 `<api_test_repo>/pyproject.toml` 存在。
3. 确保可用的 `run_api_test.sh` 存在且可执行。
4. 将 `code_file` 转为 `api_test_repo` 内相对路径。
5. 设置必要环境变量：`TEST_ENV`、`TAG_ENV`、`IDC_ENV`、`DUCK_AUTH_TOKEN`（或沿用外部已有值）。
6. 执行：

```bash
TEST_ENV=sg_prod TAG_ENV=prod IDC_ENV=my DUCK_AUTH_TOKEN=<token> \
  scripts/run_api_test.sh --api-test-dir <api_test_repo> test \
  tests/path/to/test_xxx.py <pytest_args...>
```

7. 将 stdout/stderr 写入 `<output_dir>/.api-mind/logs/py_driver_local_execute.log`。
8. 首次执行退出码为 0：返回成功，`fix_attempted=false`、`retry_count=0`。
9. 首次执行失败：基于日志 / traceback / pytest 摘要做失败归因。
10. 仅当高置信度归因为“用例实现问题”时执行最小修复；修复后做静态校验并重跑。
11. 最多允许 3 次 fix-and-rerun；每次重跑使用与首次完全相同的 `api_test_repo`、`code_file`、`TEST_ENV` / `TAG_ENV` / `IDC_ENV`、token 与 `pytest_args`。
12. 成功则返回 `status=success` 与修复摘要；耗尽 3 次仍失败或不满足修复准入则返回失败。

## 4. 失败归因与自动修复准入

只有失败更像**用例实现问题**，而不是被测 API 问题时，才允许自动修复。

允许自动修复的典型信号：

1. Python / pytest 级实现错误：`SyntaxError`、`IndentationError`、明显 import path 错误、fixture 名不匹配、`conftest.py` 未暴露所需 fixture。
2. client 接线错误：类名 / 方法名不一致，`query_params` / `params`、`json` / `data` 等调用参数与 client 约定不匹配，`HTTPGenericClient` / `HTTPClient` serialization 处理明显错误。
3. 配置接线错误：`TEST_ENV` 对应 config 存在但当前 PSM 缺失或字段名错误，`llm_config[test_env][psm]` 路径与配置结构不一致。
4. 生成代码内部取值错误：可由 `case.md` 直接验证的字段路径拼写错误，HTTP response object / `resp.json()` / RPC body 访问方式错误。

禁止自动修复的典型信号：

1. 疑似被测 API / 产品行为问题：HTTP `5xx`、业务码异常但请求结构 / 鉴权 / 环境看起来正确、响应与期望不一致且更像产品行为偏差。
2. 鉴权 / 账号 / 环境问题：`401` / `403`、cookie / token 缺失或过期、环境路由错误、host 不通、下游未部署、账号数据不满足前置条件。
3. 基础设施 / 外部依赖问题：网络超时、DNS / 代理 / 网关异常、Poetry / Python 依赖缺失。
4. 任何需要“把 expected 改成 actual 才能过”的场景：严禁削弱 / 删除断言，严禁把接口实际返回抄成新期望。

## 5. 自动修复边界

可修复范围仅限本轮生成或本轮直接依赖的 Python 资产：

- `code_file`
- 本轮最小补齐 / 修改过的 `conftest.py`
- 本轮最小补齐 / 修改过的 `client/*.py`
- 当前 case 所属 PSM 的 runtime config JSON 项

优先修复接线问题：fixture 参数名、client 导入路径 / 类名 / 方法名、request 参数名映射、config key / `TEST_ENV` / PSM 取值路径、response 取值路径与基础断言。

强制禁止：不得修改 `case.md` / `spec.md` / `test/task.md` 作为“修复”；不得为了通过测试改变被测 API 输入语义（除非能从 `case.md` 明确证明生成代码写错字段）；不得修改 sibling case 的断言或 auth；不得把远端 / 环境偶发错误包装成 case 修复。
