# py_driver generate/context

## 1. 先读取当前 spec 侧最小上下文

必须并行读取：

1. `case.md`
2. `spec.md`
3. `test/task.md`（如不存在则跳过）

严禁主动搜索或扫描 api_test 仓库来推导 `target_case_dir`，也严禁使用 Explore Agent 探索 api_test 仓库。确认 `api_test_repo` 与用户输入的 `target_case_dir` 后，以下探索必须使用定向工具，不得发起全仓扫描：

- 查找 `conftest.py`：仅检查用户确认的 `<target_case_dir>/conftest.py`。
- 查找已有 config JSON：仅搜索 `<target_case_dir>/config/*.json`。
- 查找 client 中的目标方法：`Grep` 在 `clients/http/` 或 `clients/http_gen/` 中搜索 `apipath` 或方法名。
- 查找已有同类测试：`Glob` 搜索 `<target_case_dir>/**/*.py` 或同级目录的 `test_*.py`。

基于 `test/task.md` 推导本地 `.env` 候选内容，参考 `../../resources/env_template.md`。在关键输入完成确认前，候选内容只能保存在推理上下文中，不得落盘。

## 2. 必须确认的信息（合并为一次确认）

在任何代码生成、分支切换、写文件动作之前，必须用一次 `AskUserQuestion`（multi-panel）合并确认：

1. `api_test_repo`：由 pydriver 提供 api_test 仓库**绝对路径**作为确认信息（例如 `/Users/bytedance/Desktop/api_test`）。不得为了寻找 `target_case_dir` 主动搜索 api_test 仓库；若无法从上层输入或既有状态中确定 `api_test_repo`，仅询问用户提供 api_test 仓库绝对路径。
2. `target_case_dir`：必须通过 `AskUserQuestion` 让用户主动输入希望存放用例的目录，且用户输入必须是相对 `api_test_repo` 的仓库内相对路径（例如 `tests/content_discovery/llm_gen/cases`）。不得基于仓库扫描、同类测试目录或父级 `conftest.py` 自动推荐 / 决定落点；确认后再拼接为 `<api_test_repo>/<target_case_dir>` 用于后续校验与写入。
3. 生成策略 / 目标分支：
   - 本地生成或 `generate + execute(local)`：默认 `generate_strategy=generate_only_local`，不强制追问 `target_branch`。
   - 明确提交 / push / 远端 TTAT：使用 `generate_strategy=generate_and_push`，必须确认 `target_branch`。
