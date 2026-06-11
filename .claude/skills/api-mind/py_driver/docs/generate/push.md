# py_driver generate/push

本文件仅在 `generate_strategy=generate_and_push`，或后续明确要 `execute(remote)` 且目标代码需要已 push 时读取。

## 1. generate_only_local（默认）

适用：仅生成 Python case、`generate + execute(local)`、先做静态校验 / 本地验证。

要求：生成代码与配置，完成静态校验；不要求 `target_branch`；不 commit、不 push；返回 `push_result=skipped`、`commit=null`。

## 2. generate_and_push

适用：用户显式要求 commit / push、后续明确要 `execute(remote)`、任务链要求同步远端分支。

要求：

1. 提交前再次用 `git log` / `git status` 检查目标路径是否被污染。
2. 仅 stage 本轮相关文件：case、config、必要 `conftest.py` / client。
3. commit 信息简洁，例如 `test(api-mind): add python case for <psm>`。
4. push 到用户指定分支。

push 失败时，远端已更新则说明 remote ahead，权限失败则明确报错；严禁 `push --force`。发现用户已自行上传同路径代码时，优先复用或确认增量修改，不重复生成 / push。

