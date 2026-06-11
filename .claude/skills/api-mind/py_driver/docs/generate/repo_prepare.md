# py_driver generate/repo_prepare

确认必要输入后：

1. 将 `.env` 候选内容落盘到当前 spec 工作目录。
   - 该 `.env` 是当前 spec 的安全产物，不属于 api_test 仓库提交内容。
   - 已存在时先比较差异；一致则复用，不一致则最小更新。
2. 验证 `api_test_repo` 是 Git 仓库。
3. 验证 `target_case_dir` 位于 `api_test_repo` 内。
4. 在任何分支切换 / commit / push 前做 Git 审计：
   - `git status --short`
   - `git branch --show-current`
   - `git log --oneline --decorate -n 20 -- <target_case_dir>`
   - 有 upstream 时补充检查本地未推送与远端领先：`@{u}..HEAD`、`HEAD..@{u}`。
5. 如目标目录 / 文件已有近期提交、未推送提交或用户自行上传过同类代码，不得覆盖；必须说明发现并确认复用、增量修改或换分支继续。
6. `generate_and_push` 时，审计后再切换到用户指定分支；若分支不存在，报错等待确认，不擅自新建业务分支名。
7. `generate_only_local` 不强制切分支，但仍需审计，避免覆盖用户本地改动。

约束：涉及分支切换时，必须先切分支，再生成代码。

