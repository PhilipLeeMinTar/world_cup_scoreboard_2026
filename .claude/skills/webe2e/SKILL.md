---
name: webe2e
description: 从 case.md 生成 Web E2E 执行计划，支持 TTAT 远程执行或基于 playwright-cli 的本地执行（每个 case 独立 `-s=<caseId>` session，进程级隔离），并在同一技能内支持平台查询、按 task_id 查询状态、显式分析失败报告，以及用户主动调用的 Midscene YAML 脚本批量生成（gen-yaml）。
user-invocable: true
---

# Web E2E

## 适用场景

- 用户已经准备好 `case.md`，希望直接跑 Web E2E 自动化
- 用户说"根据这个 case.md 跑自动化测试""帮我创建并执行 Web E2E 用例"
- 用户希望一条链路完成：`case.md` -> TTAT 任务 或 playwright-cli 本地执行 -> `test_report.md`
- 用户想查询 Web E2E 当前可用的平台列表
- 用户想查看某个 Web E2E 平台的详情，以及该平台对应需要补充的环境变量

## 输入

1. 必须提供 `case.md`
2. 可选提供：`title`、`creator`
3. 如用户需要，可按需查询 Web E2E 可用平台列表或某个平台详情；这两个能力是对外提供的独立查询能力，不要求在主流程中主动调用
4. 环境参数通过 `.env` 文件配置；其中 `EXECUTION_MODE` 控制执行分支；本地模式固定使用 `LOCAL_RUNNER=playwright-cli`
5. 本地模式可通过 `LOCAL_CASE_CONCURRENCY` 控制 case 级并发度；默认 `10`
6. `.env` 初始化时，会优先尝试从同任务目录的 `task.md` 提取 `RUN_ENV`、`SWIMLANE`、`TEST_IDC` 默认值；提取不到也可以，后续仍由用户确认

## 执行规则

### ⚠️ 强制确认流程

**必须严格按照以下顺序执行，不得跳过用户确认步骤：**

1. **init-env** - 初始化环境配置文件
2. **show-env** - 展示环境配置给用户
3. **确认执行模式** - 执行前必须确认 `EXECUTION_MODE`；若为 `local`，还必须确认 `LOCAL_RUNNER=playwright-cli`、`LOCAL_CASE_CONCURRENCY`，并完成 `playwright-cli` 检测/首次安装确认（见下方"本地执行模式 §0"）
4. **等待用户确认** - 用户必须明确回复"确认"、"继续"、"OK"等
5. **按执行模式进入对应执行分支** - 用户确认后才可执行

进入执行命令时，必须显式带上 `--confirmed-env`，表示当前 `.env` 已经展示给用户且用户已确认。

**禁止行为**：
- ❌ 展示配置后直接执行 run 命令
- ❌ 未确认 `EXECUTION_MODE` 就直接开始执行任务
- ❌ `EXECUTION_MODE=local` 时未确认 `LOCAL_RUNNER`、未完成 `playwright-cli` 安装检查就直接执行 case
- ❌ 未拿到用户确认就带着默认值直接执行，或省略 `--confirmed-env` 强行执行
- ❌ 假设用户已确认而跳过等待
- ❌ 在用户修改配置后未重新展示就执行

### 其他规则

- 已有 `case.md` 时，不要再走 PRD/Bits 用例生成流程
- 创建用例组和任务时无需逐个 curl 向用户确认接口调用
- 只要进入执行阶段，无论用户说"执行"、"开始跑"、"run"还是"run-local"，都必须先确认执行模式；不能自行假定默认值
- `test_report.md` 默认写到 `case.md` 同目录，文件名固定为 `test_report.md`
- 写 `test_report.md` 时要参考 `prd2case-web` 的产物放置习惯：结果文件放在当前测试任务目录内，通常与 `case.md` 同级
- 本地模式与 TTAT 远程模式的 `test_report.md` 顶层格式必须保持一致，至少统一使用 `执行概览` 与 `任务状态` 两个主章节；本地不存在的远程字段使用 `-` 占位
- `EXECUTION_MODE=ttat` 时，创建任务成功后，必须立即把任务信息和报告文件路径写入 `test_report.md`
- `EXECUTION_MODE=local` 时，不创建 TTAT `case_group_id` / `task_id`，而是先生成本地执行计划，再通过 `playwright-cli`（每个 case 独立 `-s=<caseId>` session）实际执行，并把结果写回 `test_report.md`
- 所有接口调用细节统一收敛在 `scripts/case2webe2e.py` 中，技能文档只描述流程与约束，不再展开每个接口请求体
- 技能本身不自动轮询 TTAT 任务状态，也不自动分析报告
- 如何查询任务状态、什么代表任务完成、以及如何显式进入报告分析阶段，统一写在 `SKILL.md` 中，不写入 `test_report.md`
- 任务完成后，如需分析报告，应继续使用当前 `webe2e` 技能的分析子命令，并把当前 `task_id` 作为输入；不要在 `run` 完成后自动触发
- **`prd2case-web` 边界**：`prd2case-web` 只负责从 PRD/spec 产出 `test_analysis.md` / `case.md`；**不包含** `analyze-task`、`test_report.md` 的撰写规范，也不描述 TTAT 失败报告的 Markdown/HTML 拉取与解析优先级。凡属「跑完之后的报告与归因」，一律在本 skill（含下文 `analyze-task` 分析规范）内完成；若用户要在失败迭代里改用例，应先按本 skill 落盘分析结论，再决定是否回到 `prd2case-web` 改文档。
- `analyze-task` 以终端返回和可选文件落地为主；如调用方未明确要求，不需要额外生成 Excel 汇总文件
- 当用户询问"Web E2E 有哪些平台可选"时，可按需调用 `list-platforms` 能力，并向用户列出 `nameZh`、`platform`、`domain`、`poc`
- 当用户询问"某个平台的详情"时，可按需调用 `platform-detail` 能力，并向用户解释该平台需要补充哪些环境变量、哪些值可沿用默认值

## 生成 Midscene YAML 脚本（原子能力，用户主动调用）

这是一个**独立原子能力**，不包含在默认的 `run` / `run-local` 主流程中，**必须由用户主动触发**才执行。典型触发话术：

- `/webe2e 生成YAML`
- `yaml-gens`
- "把 case.md 转成 midscene YAML 脚本"
- "生成一批可以喂给 midscene 的 yaml"
- "gen-yaml"

命令：

```bash
python3 $SKILL_DIR/scripts/case2webe2e.py gen-yaml \
  --case-md test/case.md
```

行为：

- 统一调用 `markdown2midscene` 解析 `case.md`（与 `run` / `run-local` 共用）
- 未显式指定 `--case-priority` 时默认只保留 `P0` case；支持 `P1`、`P2`、`P3`、`all`
- 解析结果按 case 拆成多个 YAML 文件，**每个 case 写一个 `<用例编号>.yaml`**，例如 `WEB-001.yaml`
- 默认输出目录为 `case.md` 同级的 `test/yaml-scripts/`（可通过 `--out-dir` 覆盖）
- 每个 YAML 文件顶层结构固定为 `web:` + `tasks:`，结构对齐 `resources/midscene_template.yaml`：
  - `web.url`：取该 case flow 中**第一条 URL 步骤**作为起始页；被提升的这一条会从 `tasks[].flow` 中移除
  - 若一个 case 解析结果里没有 URL 步骤，且未提供 `--default-url`，则**跳过该 case 并在输出的 `skipped` 列表里记录原因**，不写出 YAML
  - 其余步骤（`ai` / `aiAction` / `aiAssert` / `sleep` / `aiQuery` / `aiWaitFor` / `javascript` 等）在 flow 中**原样保留**
- 文件名优先使用 case 中的用例编号；若无法提取用例编号，再退回 case 名称 slugify，冲突时追加序号
- `ai` 等原始标签不会被改写；多行 `ai` 内容会用 `|` block scalar 展示，并按 `步骤:` / `断言：` 分组编号，提升可读性

示例：模板 `resources/midscene_template.yaml`

```yaml
web:
  url: https://www.bing.com

tasks:
  - name: Search for weather
    flow:
      - ai: Search for "today's weather"
      - sleep: 3000
      - aiAssert: The results show weather information
```

参数：

- `--case-md`：`case.md` 路径，必填
- `--case-priority`：可选，支持 `P0`/`P1`/`P2`/`P3`/`all`；默认 `P0`
- `--out-dir`：可选，覆盖默认的 `yaml-scripts/` 输出目录
- `--default-url`：可选，当某个 case 的 flow 里没有 URL 步骤时，用此值作为 `web.url`；未提供时对应 case 会被跳过
- 其他 `--title` / `--creator` / `--env-file` / `--platform` 等通用参数与 `run` / `run-local` 一致，大多数情况下无需传入

输出：

- stdout 打印 JSON 汇总：`case_md`、`out_dir`、`case_count`、`written_count`、`skipped_count`、`case_priority_filter`、`files`；若存在跳过项，会额外带 `skipped` 列表

**严禁**在未经用户明确要求的情况下自动触发 `gen-yaml`；它与 `run` / `run-local` 是并列的独立能力，不属于任一主流程。

## 本地执行模式

当 `EXECUTION_MODE=local` 时，执行流程改为本地 `playwright-cli` 驱动，不创建 TTAT 任务。

### 0. playwright-cli 安装检查（首次必经）

`run-local` 启动前必须先确保本机已安装 `playwright-cli`：

1. 在 shell 里探测：`command -v playwright-cli`（或 `playwright-cli --version`）。
2. 命中即跳过；未命中时**给用户展示一次安装命令并请求一次性确认**：

   ```bash
   npx @tiktok-fe/skills add microsoft/playwright-cli --source github --skill playwright-cli
   ```

   - 用户首次确认（"OK / 安装"）后即执行，并在终端回显安装结果。
   - 安装成功后将检查结果记入 `local_execution_plan.json` 的 `runtime.playwright_cli`（包含 `installed=true`、`version=<x.y.z>`、`auto_install_ran=true|false`），下次同一仓库的 run-local 不再重复确认。
3. 用户拒绝安装时，停止 run-local 并报告原因；不允许回退到任何"模拟执行"或"用其他工具替代"。

### 1. Runner / 计划生成

- 本地模式固定使用 `playwright-cli`；`.env` 中的 `LOCAL_RUNNER` 必须为 `playwright-cli`。
- `.env` 中可通过 `LOCAL_CASE_CONCURRENCY` 配置 case 级并发度；默认值为 `10`。
- 本地模式不需要查询平台详情，也不依赖 TTAT 平台变量来补齐执行前置。
- 本地模式仍然先调用 `markdown2midscene` 解析 `case.md`：未显式指定 `--case-priority` 时默认只保留 `P0` case，可用 `--case-priority P1` / `P2` / `P3` / `all` 显式覆盖（`all` 包含未标记 priority 的 case）；解析结果写到 `local_execution_plan.json`。
- AI 必须基于 `local_execution_plan.json` 执行；默认只启动一个执行 agent 负责编排，由 `playwright-cli` / runner 按 `LOCAL_CASE_CONCURRENCY` 做 case 级并发调度，避免多个 subagent 并发写报告、注册 mock 或归档共享产物；单个 case 内的 flow 顺序不能重排、不能跳步骤。

### 1.1 执行 agent 委派（本地模式必做）

`run-local` 生成 `local_execution_plan.json` 和初始化 `test_report.md` 后，当前主 agent 优先调用一次 `Subagent` 启动单一执行 subagent，并把执行上下文交给它；禁止按 case 启动多个 subagent。

如果当前 AI 工具没有 subagent 能力，允许回退为主 agent 自己执行 case，但主 agent 此时必须承担同一份执行 agent 约束：只允许一个运行时写入者、按 `LOCAL_CASE_CONCURRENCY` 编排 case 并发、不得再启动多个并行写入方。

传给执行 subagent 的 prompt（或主 agent 回退执行时的自检清单）必须包含：

- `local_execution_plan.json` 的路径，以及 `test_report.md` 的路径。
- 要求读取 plan 中的 `case_concurrency`、`browser_headers`、`browser_header_setup`、`auth_profile`、`cases[].case_id` 和 `cases[].artifacts`。
- 要求由该执行 agent 统一编排 `playwright-cli`，按 `LOCAL_CASE_CONCURRENCY` 做 case 级并发；每个 case 使用独立 `playwright-cli -s=<caseId>` session。
- 要求该执行 agent 是本轮本地执行的唯一运行时写入者：它可以写 `test_result/<caseId>/` 和执行完成后的 `test_report.md` 结果段；若使用 subagent，主 agent 不得同时写这些运行时结果。
- 要求每个 case session 在 `open` 后、首次 `goto` 前按 `browser_header_setup` 执行 `playwright-cli -s=<caseId> run-code '<code>'`，其中 `<code>` 会调用 `page.setExtraHTTPHeaders(browser_headers)`；禁止只读取 `browser_headers` 但不执行注入。
- 要求 mock / route / state-load 都在对应 case session 内完成；`playwright-cli` 的网络 mock 必须使用其 `route` 能力（对应原生 Playwright `page.route`），不要调用不存在的 `intercept` 子命令；失败、抛错、超时路径必须先拍 `failure.png`，再拍/保留 `final.png`，最后 close session。

### 2. Session 与隔离（playwright-cli `-s=<caseId>`）

- 每个 case 在自己的 `playwright-cli -s=<caseId>` session 里跑，`<caseId>` 用 case 在 `local_execution_plan.json` 里的稳定 id（不是 case 名）。
- session 名 = caseId，**进程级隔离**——不同 case 之间不共享浏览器进程、cookie、storage；这是替代旧版 "browser context per case" 的正式方案。
- 每个 case 的生命周期固定为：
  1. `playwright-cli -s=<caseId> open`：启动该 case 的隔离浏览器进程。
  2. 顺序执行 case flow：`goto` / `snapshot` / `click <ref>` / `fill <ref> "..."` / `press` / `aiAction` / 等等，全部带 `-s=<caseId>`。
  3. **case 结束截图（强制，无论成功 / 失败 / 抛错都要拍）**：`playwright-cli -s=<caseId> screenshot test_result/<caseId>/final.png`，文件名固定 `final.png`。这是结果留痕，不依赖断言通过与否。
  4. case 结束后**精确**关闭该 session：`playwright-cli -s=<caseId> close`；禁止 `close-all` 等批量关闭。
- **截图强制规则**：
  - 每个 case **至少**两张：`step_001_<动作短名>.png`（首步进入页面后立刻拍一张，作为入口校验）+ `final.png`（case 结束前最后一张，状态留痕）；其余每个关键 step（点击 / 表单提交 / 跳转 / 断言前一刻）都建议各拍一张 `step_NNN_<动作短名>.png`。
  - 失败 / 抛错 / 超时路径**必须**拍 `failure.png`（在 catch / finally 分支里立即拍，**早于** `close`）；同时保留 `final.png`，两张都要在。
  - 所有截图通过 `playwright-cli -s=<caseId> screenshot <path>` 落到 `test_result/<caseId>/screenshots/`（或直接 `test_result/<caseId>/`，二选一保持一致）；执行器**不得**把"没失败就不用截图"作为优化跳过这一步。
  - trace / 录像 / console log 一并落到 `test_result/<caseId>/`，case 结束前完成归档；不能先批量执行再回头按记忆补归档。
- 任何无法把产物 1:1 映射到 case 目录的执行方式都**禁止**使用。

### 3. Chrome profile / 登录态导出（本地模式强制）

本地模式默认从当前机器的 Chrome 登录态生成 `playwright-cli` 可用的 storage state，但**禁止**直接假设 `~/Library/Application Support/Google/Chrome/Default` 就是用户实际登录的 profile。

1. `.env` 支持以下字段：
   ```bash
   STORAGE_STATE_MODE=chrome-profile
   CHROME_USER_DATA_DIR=
   CHROME_PROFILE_NAME=
   ```
   - `CHROME_USER_DATA_DIR` 为空时使用系统默认 Chrome user data dir。
   - `CHROME_PROFILE_NAME` 为空时，AI / 执行器必须枚举 `Default`、`Profile 1`、`Profile 2` 等候选 profile，并优先选择/展示实际包含目标域名登录态的 profile；**不得**直接读取 `Default` 后把空 cookie 当作结论。
2. 导出 cookie 时必须按运行中 Chrome 的 SQLite/WAL 语义处理：
   - 如果 Chrome 正在运行，不能只复制 `Cookies` 主文件；必须连同 `Cookies-wal`、`Cookies-shm` 一起复制到临时目录后查询。
   - 更推荐启动一个克隆 profile，让 Chrome / Playwright 自己加载 profile 后调用 storage state 导出；这样能同时覆盖 cookie、localStorage、sessionStorage、IndexedDB 相关状态。
3. 如果某个 profile 的目标域名 cookie 为空，必须继续检查：
   - 是否选错 profile（`Default` vs `Profile 1` / `Profile 2`）。
   - 是否只拷贝了 `Cookies`，遗漏 WAL 中的新 cookie。
   - 登录态是否落在 localStorage / sessionStorage / IndexedDB，而不是 cookie。
   - cookie domain 是否挂在父域、SSO 域或子域，不能只按当前页面 host 精确匹配。
4. `local_execution_plan.json` 必须写出 `auth_profile`：
   - `storage_state_mode`
   - `chrome_user_data_dir`
   - `chrome_profile_name`
   - `profile_detection_required`
   - `cookie_db_read_rule`

若无法确认实际登录 profile，必须停下来让用户确认 profile，而不是继续生成“空 cookie”的 storage state。

脚本已提供原子能力：

```bash
# 先列出候选 profile，观察哪个 profile 对目标域名有 cookie / storage 迹象
python3 $SKILL_DIR/scripts/case2webe2e.py export-storage-state \
  --user-data-dir "$HOME/Library/Application Support/Google/Chrome" \
  --target-domain example.com \
  --list-profiles

# 用户确认 profile 后导出 playwright storageState
python3 $SKILL_DIR/scripts/case2webe2e.py export-storage-state \
  --user-data-dir "$HOME/Library/Application Support/Google/Chrome" \
  --profile-name "Profile 1" \
  --target-url "https://example.com/path" \
  --output test/.webe2e/storage_state.json
```

`run-local` 在 `STORAGE_STATE_MODE=chrome-profile` 时会调用同一套导出逻辑；如果 `CHROME_PROFILE_NAME` 为空，会输出候选 profile 并停止，要求用户明确设置，而不是继续生成可能为空的登录态。

### 4. 浏览器请求头

每个 case 启动时按 `.env` 注入默认请求头：

- `SWIMLANE` 非空 → `x-tt-env: ${SWIMLANE}`
- `RUN_ENV=ppe` → `x-use-ppe: 1`
- `RUN_ENV=boe` → `x-use-boe: 1`
- `RUN_ENV=local` / `online` → 不额外添加 `x-use-*`

`local_execution_plan.json` 会同时写入：

- `browser_headers`：最终请求头 key/value，例如 `{"x-tt-env": "<swimlane>", "x-use-ppe": "1"}`。
- `browser_header_setup`：每个 session 必须执行的注入步骤。由于 `playwright-cli open` 没有全局 header 参数，且 `route --header` 是 mock response 相关能力，不是默认请求头透传，执行 agent 必须在 `open` 后、首次 `goto` 前运行：

  ```bash
  playwright-cli -s=<caseId> run-code 'async (page) => { await page.setExtraHTTPHeaders({...}); }'
  ```

  未执行这一步时，`RUN_ENV=ppe` + `SWIMLANE` 虽然会出现在 plan 的 `browser_headers` 中，但真实页面请求不会带 `x-use-ppe` / `x-tt-env`。

### 5. 报告

- 执行完成后，必须把每个 case 的执行结果、关键证据和本地产物路径回写到同一份 `test_report.md`。
- `test_report.md` 顶层结构继续沿用远程模式的 `执行概览` / `任务状态`；本地模式不存在的远程字段（如 `case_group_id` / `task_id`）使用 `-` 占位。
- `task_url` 改为本地执行目录路径（默认 `test_result/`）。

## 平台查询能力

### 1. 查询当前 Web E2E 可用平台列表

当用户明确要求"查看 Web E2E 当前支持哪些平台"时，可按需调用：

```bash
python3 $SKILL_DIR/scripts/case2webe2e.py list-platforms
```

- 接口返回的是平台列表
- 面向用户展示时，保留 `nameZh`、`platform`、`domain`、`poc`
- 推荐以表格形式返回，便于用户直接选择平台值写入 `.env`
- 如果同一个 `platform` 在不同 `domain` 下重复出现，应提醒用户后续查询详情时尽量同时带上 `domain`
- 如果返回中还有 `description` 等字段，可内部参考，但默认不主动展开给用户

推荐展示格式：

| 平台名称 | platform | domain | poc |
|------|------|------|------|
| TSOP MM | tsop-mm | growth | liqiang.leo |
| Live Campaign | live-campaign | ads | - |

### 2. 按平台查询平台详情

当用户已经指定 `platform`，并要求"查看这个平台详情"或"看看这个平台需要补哪些环境变量"时，可按需调用：

```bash
python3 $SKILL_DIR/scripts/case2webe2e.py platform-detail --platform <platform> [--domain <domain>]
```

- 返回结果是该平台详情中的环境变量配置项列表
- 如果接口返回了 `domain`，或用户已从平台列表中拿到 `domain`，应一并展示给用户，避免同名平台歧义
- 关键字段说明：
  - `key`：环境变量名
  - `value`：默认值；为空时通常表示需要用户补充
  - `useDefault`：是否可直接使用默认值
  - `description`：该变量的获取方式或填写说明
- 面向用户展示时，应明确区分：
  - 哪些变量已经有默认值，可直接保留
  - 哪些变量没有默认值，需要用户从浏览器 `Cookies`、`Local Storage` 或接口响应里补充
- 如果该接口返回 `platform` 本身也作为配置项，仍应保留并提示用户 `.env` 中应填写对应的平台值

推荐展示格式：

| 参数 | 默认值 | 是否可直接使用 | 说明 |
|------|--------|----------------|------|
| platform | tsop-mm | 是 | 固定使用 tsop-mm |
| X_MPSSO_TOKEN | - | 否 | 从 Local Storage 获取 |

## 完整流程

### 步骤 1：检查并创建环境配置文件

检查 `case.md` 同目录下是否存在 `.env` 文件：

- 若不存在，使用脚本自动创建默认配置文件
- 若同任务目录存在 `task.md`，优先从中提取 `RUN_ENV`、`SWIMLANE`、`TEST_IDC` 作为 `.env` 初始值
- 默认配置如下：
  ```
  EXECUTION_MODE=ttat
  LOCAL_RUNNER=playwright-cli
  LOCAL_CASE_CONCURRENCY=10
  STORAGE_STATE_MODE=chrome-profile
  CHROME_USER_DATA_DIR=
  CHROME_PROFILE_NAME=
  platform=live-campaign
  RUN_ENV=ppe
  TEST_IDC=sg
  SWIMLANE=
  TASK_TIMEOUT=10
  ```

### 步骤 2：读取并展示环境配置

读取 `.env` 文件内容，以表格形式展示给用户：

| 参数 | 当前值 | 说明 |
|------|--------|------|
| creator | your_name | 创建者邮箱前缀（必填） |
| EXECUTION_MODE | ttat | 执行模式（`ttat` / `local`） |
| LOCAL_RUNNER | playwright-cli | 本地模式 runner（固定为 `playwright-cli`） |
| LOCAL_CASE_CONCURRENCY | 10 | 本地模式 case 级并发度 |
| STORAGE_STATE_MODE | chrome-profile | 本地登录态来源；默认从 Chrome profile 导出 storage state |
| CHROME_USER_DATA_DIR | - | Chrome user data dir；空值使用系统默认目录 |
| CHROME_PROFILE_NAME | - | Chrome profile 名称；空值表示必须先自动探测/让用户确认，不能默认 `Default` |
| platform | live-campaign | 测试平台 |
| RUN_ENV | ppe | 运行环境 (boe/ppe/online) |
| TEST_IDC | sg | 测试机房 |
| SWIMLANE | - | 泳道标识 |
| TASK_TIMEOUT | 10 | 任务超时时间（分钟） |

**注意**：`creator` 优先级为 `命令行参数 > 环境文件 > git user.email`

**补充**：

- `RUN_ENV`、`SWIMLANE`、`TEST_IDC` 在初始化 `.env` 时会优先参考 `task.md`，但最终仍以用户确认后的 `.env` 内容为准
- `EXECUTION_MODE=ttat` 走 TTAT 远程执行链路
- `EXECUTION_MODE=local` 走本地 `playwright-cli` 执行链路，此时必须再确认 `LOCAL_RUNNER` 与 `playwright-cli` 安装状态
- `EXECUTION_MODE=local` 时，不需要查询平台详情或补平台变量；但若 `SWIMLANE` / `RUN_ENV` 已配置，必须据此生成浏览器默认请求头并通过 `playwright-cli` 注入
- `EXECUTION_MODE=local` 时，还必须明确看到 `LOCAL_CASE_CONCURRENCY`，用于后续 case 级并发执行
- `EXECUTION_MODE=local` 且 `STORAGE_STATE_MODE=chrome-profile` 时，必须确认实际 Chrome profile；若 `CHROME_PROFILE_NAME` 为空，先枚举候选 profile 并确认目标域名登录态，不得直接读取 `Default`

### 步骤 3：等待用户确认（必须）

**AI 必须在此步骤暂停，先确认执行模式，再等待用户明确确认后才能继续。**

确认要求：

- 必须明确看到 `EXECUTION_MODE`
- 若 `EXECUTION_MODE=local`，必须明确看到 `LOCAL_RUNNER` 和 `LOCAL_CASE_CONCURRENCY`
- 若用户只说"执行"但未明确模式，或 `.env` 中模式值不清楚，必须先让用户确认，不能直接运行 `run` / `run-local`

向用户展示确认提示：

```
当前环境配置：

| 参数 | 值 |
|------|-----|
| creator | xxx |
| EXECUTION_MODE | xxx |
| LOCAL_RUNNER | xxx |
| LOCAL_CASE_CONCURRENCY | xxx |
| local_browser_headers | xxx |
| platform | xxx |
| RUN_ENV | xxx |
| TEST_IDC | xxx |
| ... | ... |

请确认以上执行环境配置是否正确。你可以：
1. **直接确认** - 回复"确认"或"继续"
2. **修改文件** - 编辑 `.env` 后回复"继续"
3. **逐项修改** - 告诉我需要修改的参数，如"RUN_ENV 改为 boe"
```

**用户确认后才可执行步骤 4**。如果用户修改了配置，或执行模式从 `ttat` 改成 `local`，需重新展示配置并再次确认。

### 步骤 3.5：case.md 变更时的下游同步（硬规则）

`case.md` 是 Web E2E 链路上所有下游产物的唯一源头。一旦 `case.md` 发生任何改动（内容、步骤、前置条件、预期结果、标签、优先级均算），必须同步更新所有依赖产物。

依赖 `case.md` 的下游产物清单：

- **本地 payload 快照**：`case_group_payload*.json`、`local_execution_plan.json` 等如已存在，必须删除后按新 `case.md` 重新生成。
- **Bits 用例**：必须以新 `case.md` 覆盖回 Bits，`case_id` 不变（见 `prd2case-web` 技能的 `scripts/case_management.py save --case-id <已有 id>`）。
- **TTAT case group**：必须调用 `edit_with_cases` 更新同一个 `case_group_id`，严禁新建一个平行 case group。
- **test_report.md**：必须重新写一次，`case_group_action` 字段记为 `updated`。

判定流程：

1. 读取当前任务目录的 `test_report.md`（或历史命令行输出）是否已经有 `case_group_id`。
2. 如果没有，走 `create-group` / `run` 新建路径。
3. 如果有，一律走更新路径：
   - 只更新用例组：`python3 $SKILL_DIR/scripts/case2webe2e.py edit-group --case-md test/case.md --env-file test/.env --case-priority <...> --confirmed-env --case-group-id <已有 id>`
   - 更新并触发任务：`python3 $SKILL_DIR/scripts/case2webe2e.py run --case-md test/case.md --env-file test/.env --case-priority <...> --confirmed-env --case-group-id <已有 id>`

底层 API 说明：`edit-group` / `run --case-group-id` 封装的是 TTAT OpenAPI `POST https://ttat-openapi-sg.tiktok-row.net/ui/web_e2e/case_group/edit_with_cases`，请求体与 [`create_case_group`](https://ttat-openapi-sg.tiktok-row.net/ui/web_e2e/create_case_group) 一致，只是多一个 `case_group_id`。

**默认 tag**：`create_case_group` / `edit_with_cases` 两条路径走的是同一份 `tasks[]`（脚本里 `_build_tasks` 是唯一出口），每条 task 默认都会带上 `tags = ["ttat", "e2e", "newFeature"]`、`tag_names = ["ttat", "e2e", "newFeature"]`；其中 `newFeature` 必须保留，保证新建 / 更新后的 TTAT case group 能继续被 `newFeature` 过滤命中。如需追加业务 tag，请改 `_build_tasks` 的常量列表，**不要**在调用方零散拼接，避免两条路径漂移。

**更新已有 case group 的推荐链路**：先在 `prd2case-web` Stage-4.1 把新 `case.md` 覆盖回同一个 Bits 用例，再按 TTAT UI 的一键更新形态更新 case group：`get_case_detail_by_url` → `bits2midscene_batch` → `edit_with_cases`。脚本侧生成的 `edit_with_cases` payload 会保持 `case_id: null`、`itemKey: case_<index>`、`tags/tag_names = ["ttat", "e2e", "newFeature"]`，并从 `save_result.json.data.case_expectations` 注入 `case_extra.expectation_ids`，避免破坏已绑定的 Bits 结构。

拼装 TTAT 请求体时，Bits 绑定走 payload 级 `extras.extras.bitsConfig.url`，不写入每个 `tasks[]` 的 `bits_case_url` / `case_id`。`bitsConfig.url` 解析优先级：`.env` 的 `BITS_CASE_DETAIL_URL` → 与 `case.md` 同目录的 `save_result.json`（`case_management.py save -o` 产出）→ `case.md` 中首次出现的 `https://bits.bytedance.net/.../caseDetail/<id>`。

**Bits 归档硬门禁**：进入 `create-group` / `edit-group` / `run` 之前必须确认 payload 中存在非空 `extras.extras.bitsConfig.url`。解析不到 Bits 链接时，**禁止**下发请求；先回 `prd2case-web` Stage-4.1 用 `case_management.py save -o save_result.json` 把当前 `case.md` 归档到 Bits（首次 → 不带 `--case-id` 新建；已有 `case_id` → 带 `--case-id` 更新同一条），再回到本流程。**不允许**用空 `bitsConfig.url` 创建 / 更新 case group——TTAT 任务回到 Bits 反查时会断链。

**Bits 预期结果节点门禁**：`save_result.json` 还必须包含 `data.case_expectations`，其中每个 `expectation_nodes[]` 对应 `case.md` 的一个 `##### **预期结果**` 节点，并包含 Bits 节点 `id` 与 `path: [操作步骤序号, 预期结果序号]`。节点数量只与 `case.md` 的 `预期结果` 节点数对齐，不与 `####` 用例数或 TTAT task 数对齐。脚本会按每个 task 覆盖到的预期结果集合写入 `tasks[].case_extra.expectation_ids`；如果任一 task 缺失该字段，`create-group` / `edit-group` / `run` 必须 STOP，并要求回 `prd2case-web` Stage-4.1 重新归档当前 `case.md`。

### 步骤 4：执行自动化链路并初始化测试报告

用户确认后，必须先读取 `.env` 中的 `EXECUTION_MODE`，确认本次执行到底走 `ttat` 还是 `local`，再进入对应分支：

#### 分支 A：`EXECUTION_MODE=ttat`

**前置（Bits 归档硬门禁）**：进入 TTAT 链路前，必须确认 `case.md` 已经归档到 Bits，并且能解析出 payload 级 `extras.extras.bitsConfig.url` 与 task 级 `tasks[].case_extra.expectation_ids`——优先使用 `.env` 的 `BITS_CASE_DETAIL_URL` 解析 Bits 链接，其次使用 `case.md` 同目录的 `save_result.json`，最后才读取 `case.md` 内嵌的 `https://bits.bytedance.net/.../caseDetail/<id>` 链接；`expectation_ids` 只能来自 `save_result.json.data.case_expectations` 或转换结果自带字段。解析不到 Bits 链接或任一 task 缺 expectation_ids → STOP，提示用户回 `prd2case-web` Stage-4.1 用 `case_management.py save -o save_result.json` 完成归档（首次 / 增量都按那条规则），不允许带空 `bitsConfig.url` 或空 `expectation_ids` 创建 / 更新 case group。

1. 读取 `case.md`
2. 由 `scripts/case2webe2e.py` 统一调用 `markdown2midscene` 并生成 Midscene 内容；未显式指定 `--case-priority` 时默认只保留 `P0` case
3. 如需覆盖默认行为，可显式传入 `--case-priority P1`、`--case-priority P2`、`--case-priority P3` 或 `--case-priority all`；其中 `all` 会包含未标记 priority 的 case
4. 解析返回内容并拼装 TTAT 请求体；脚本会按"`.env` `BITS_CASE_DETAIL_URL` → `save_result.json` → `case.md` 内嵌 Bits 链接"顺序填充 `extras.extras.bitsConfig.url`，并按 `save_result.json.data.case_expectations` 给每个 task 写入 `case_extra.expectation_ids`。任一字段为空必须停止下发，把当前 case 标题报回让用户回 `prd2case-web` Stage-4.1 补归档
   - URL 初始化参数处理：`case.md` 的 `访问:` URL 应保留稳定业务上下文参数；对页面初始化依赖的动态参数（如相对当前时间生成的时间窗），必须由 Stage-2 在 `test_analysis.md` 记录处理策略。通用脚本不内置业务页面专项补参逻辑；若某业务页面确实需要动态 URL，应在用例生成阶段产出明确的业务前置脚本或稳定时间范围。
5. 读取环境配置并写入 `extras.execEnv`
6. 确定 case group 走"新建"还是"更新"：
   - 若当前任务目录从未创建过 case group（未指定 `--case-group-id`，也没有上一次 `test_report.md` 里可读出的 id），调用 `create_case_group`，拿到新的 `case_group_id`
   - 若已有 `case_group_id`，必须走 `edit_with_cases` 更新同一 case group
7. 获取动态 `X-Custom-Token`
8. 调用 TTAT OpenAPI 创建自动化任务，拿到 `task_id`
9. 立即创建/覆盖 `test_report.md`，至少写入以下内容：
   - `case_group_name`、`case_group_id`、`task_name`、`task_id`、`task_url`
   - `case_group_action`：`created` 或 `updated`
   - 当前环境文件路径
   - Bits 绑定信息：`extras.extras.bitsConfig.url`
10. 返回任务链接，供用户查看执行结果

#### 分支 B：`EXECUTION_MODE=local`

1. 运行：
   ```bash
   python3 $SKILL_DIR/scripts/case2webe2e.py run-local \
     --case-md test/case.md \
     --confirmed-env \
     --plan-out out/local_execution_plan.json
   ```
2. 未显式指定 `--case-priority` 时，脚本默认只保留 `P0` case；如需覆盖默认行为，可显式传入 `--case-priority P1`、`--case-priority P2`、`--case-priority P3` 或 `--case-priority all`，其中 `all` 会包含未标记 priority 的 case
3. 脚本会统一调用 `markdown2midscene`，并将过滤后的解析结果写入 `local_execution_plan.json`
4. **playwright-cli 安装检查**：探测本机是否已有 `playwright-cli`；未安装时按"本地执行模式 §0"展示并请求一次性确认 `npx @tiktok-fe/skills add microsoft/playwright-cli --source github --skill playwright-cli`。用户拒绝则停止 run-local
5. 主 agent 优先调用一个执行 subagent，并把 `local_execution_plan.json` 与 `test_report.md` 路径交给它；若当前工具没有 subagent 能力，则主 agent 按同一约束自行执行。由单一执行 agent 读取 plan 后交给 `playwright-cli` / runner 按 case 级并发跑用例；每个 case 各自一条 `playwright-cli -s=<caseId> open` → `goto` / 业务 flow → 入口截图 `step_001_*.png` → 关键步骤截图 → `final.png`（无条件）→ `close`；并发上限由 `LOCAL_CASE_CONCURRENCY` 或 `--local-case-concurrency` 决定
6. 单个 case 内的 flow 必须保持顺序、不得跳步骤；不同 case 之间通过 `-s=<caseId>` 进程级隔离，不共享浏览器 / cookie / storage
7. 执行前必须读取 `browser_headers` 和 `browser_header_setup`，并在每个 `playwright-cli -s=<caseId> open` 后、首次 `goto` 前用 `run-code` 注入：
   - `SWIMLANE` 非空时添加 `x-tt-env: ${SWIMLANE}`
   - `RUN_ENV=ppe` 时添加 `x-use-ppe: 1`
   - `RUN_ENV=boe` 时添加 `x-use-boe: 1`
   - `RUN_ENV=local` / `online` 时不添加 `x-use-*`
8. **截图强制（成功 / 失败都要拍）**：每个 case 至少有 `step_001_*.png`（入口校验）+ `final.png`（结束留痕）；失败 / 抛错 / 超时路径必须**先**拍 `failure.png`，再 `close`。`final.png` 不依赖 case 是否通过，无条件落地
9. 执行阶段必须把截图、trace、录像、console log 通过 `playwright-cli -s=<caseId>` 实时落到 `test_result/<caseId>/`，case 结束前完成归档；禁止批量执行后再按记忆补归档，禁止使用无法 1:1 映射到 case 目录的方式
10. case 结束**精确**关闭其 session：`playwright-cli -s=<caseId> close`；禁止 `close-all` 等批量关闭
11. 执行完成后，立即更新/覆盖 `test_report.md`，并保持与 TTAT 模式一致的主结构，至少写入：
    - `case.md`、`report_file`、`env_file`、`creator`、`case_group_name`、`case_group_id`、`case_count`、`task_name`、`task_id`、`task_url`
    - 其中本地模式不存在的 `case_group_id`、`task_id` 使用 `-` 占位；`task_url` 改为本地执行目录路径（默认 `test_result/`），作为远程任务链接的本地对应物
    - `execution_mode`、`local_runner`（`playwright-cli`）、`case_concurrency`、`case_isolation`（`session_per_case`）、`plan_file`、`browser_headers`、`runtime.playwright_cli`（`installed` / `version` / `auto_install_ran`）
    - 初始化阶段只写每个 case 的本地产物目录；截图、trace、录像、控制台日志等具体路径必须等执行完成后再补充
    - 每个 case 的执行结果（通过 / 失败 / 阻塞）+ `final.png` 路径（必有）+ 失败时 `failure.png` 路径
    - 失败 case 的关键证据、失败现象、建议处理方式
    - 其余截图、trace、日志等本地产物路径（若有）
12. 本地模式不返回 `task_id`，也不进入 TTAT 查询 / 分析子流程

### 步骤 5：告知任务状态查询方式（仅 TTAT 模式）

创建任务成功后，使用本技能时必须按下面这个请求方式查询任务状态：

```bash
python3 $SKILL_DIR/scripts/case2webe2e.py query-task --task-id <task_id>
```

```bash
curl 'https://ttat-openapi-sg.tiktok-row.net/ui/task/query_task_execution' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://ttat-us.byteintl.net' \
  -H 'Pragma: no-cache' \
  -H 'Referer: https://ttat-us.byteintl.net/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: cross-site' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  -H 'X-Custom-Token: <your_x_custom_token>' \
  -H 'sec-ch-ua: "Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"page_request":{"page_size":1,"cur_page":1,"sort_key":"","sort_descending":true},"task_id":<task_id>}'
```

- 查询接口：`https://ttat-openapi-sg.tiktok-row.net/ui/task/query_task_execution`
- 请求方式：`POST`
- 请求头中必须带 `X-Custom-Token`
- 请求体中必须带 `task_id`
- `query_task_execution` 返回顶层 `status_code=0` 只代表查询接口调用成功，不代表任务本身已执行完成
- 只有同时满足以下条件，才代表任务执行完成：
  - 顶层 `status_code=0`
  - `tasks[0].execute_status=10`
- 若 `status_code=0` 但 `tasks[0].execute_status` 仍不是 `10`，则任务仍在执行中

### 步骤 6：任务完成后的后续处理（仅 TTAT 模式）

当任务状态查询接口同时满足 `status_code=0` 且 `tasks[0].execute_status=10` 后，说明任务执行完成。此时如需继续做失败 case 收集或报告分析，应显式执行当前 `webe2e` 的分析子命令，而不是在 `run` 阶段自动执行。

- 推荐触发方式：`python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task --task-id <当前task_id> --case-md test/case.md`
- 默认第一轮只写 Overview 到 `test_report.md`，并给出"是否继续下钻详细分析"的确认提示与预计耗时
- AI 在 Overview 写完后必须暂停，等待用户明确确认，再继续详细分析
- 只有在用户明确确认后，才继续执行详细分析：`python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task --task-id <当前task_id> --case-md test/case.md --detail`
- 详细分析阶段按失败 case 逐条增量写回 `test_report.md`；如果命令因超时或中断未完成，必须明确告诉用户"当前只完成了部分 case 的详细分析"
- 重新执行同一条 `--detail` 命令时，脚本会自动跳过已完成 case，只继续剩余 case
- 执行 `analyze-task --detail` 时，外层 `Bash timeout` 应设置为 `>= 900000ms`（15 分钟）；否则可能先于脚本内部超时被调用方中断
- 整个流程仍然是显式人工触发，不自动串行到分析阶段

#### 下钻确认前的预计耗时

在用户进入详细分析前，必须先根据当前任务的失败 case 数量给出预计耗时，并让研发确认是否继续。

- `<= 10` 个失败 case：约 `1-3 分钟`
- `20-30` 个失败 case：约 `3-6 分钟`
- `50-60` 个失败 case：约 `6-12 分钟`
- `100` 个失败 case左右：约 `12-25 分钟`

也可以用粗略公式表达：

```text
基础约 1 分钟 + 每 10 个失败 case 约 1-2 分钟
```

确认提示必须至少包含：

1. 当前失败 case 总数
2. 预计详细分析耗时
3. 接下来会逐个拉取节点执行信息，并优先拉取 `.md.tar` 中的 Markdown 报告与截图；仅当 tar 不可用时回退 HTML 报告
4. 明确等待研发确认是否继续下钻

推荐确认话术：

```text
当前任务共有 59 个失败 case。
按历史分析耗时估算，完整下钻分析预计需要 6-12 分钟。
我会逐个拉取失败 case 的节点执行信息，并优先解析 `.md.tar` 中的 `report.md` 与截图做根因分析；tar 不可用时再回退 HTML 报告。
请确认是否继续详细分析。
```

## 脚本

```bash
# 按需查看当前所有已注册平台
python3 $SKILL_DIR/scripts/case2webe2e.py list-platforms

# 按需查看某个平台需要补充的环境变量
python3 $SKILL_DIR/scripts/case2webe2e.py platform-detail --platform tsop-mm --domain growth

# 步骤 1：初始化环境配置文件（在 case.md 同目录创建）
python3 $SKILL_DIR/scripts/case2webe2e.py init-env --case-md test/case.md

# 步骤 2：读取并展示当前环境配置
python3 $SKILL_DIR/scripts/case2webe2e.py show-env --case-md test/case.md

# 步骤 3：用户确认后执行；未传 --case-priority 时默认只执行 P0 case
python3 $SKILL_DIR/scripts/case2webe2e.py run \
  --case-md test/case.md \
  --confirmed-env \
  --payload-out out/case_group_payload.json

# 如需覆盖默认行为，可显式指定优先级；all 会包含未标记 priority 的 case
python3 $SKILL_DIR/scripts/case2webe2e.py run \
  --case-md test/case.md \
  --case-priority all \
  --confirmed-env \
  --payload-out out/case_group_payload.json

# case.md 更新后：更新同一个 TTAT 用例组，不新建
python3 $SKILL_DIR/scripts/case2webe2e.py run \
  --case-md test/case.md \
  --case-group-id <已有 case_group_id> \
  --confirmed-env \
  --payload-out out/case_group_payload.json

# 本地模式：未传 --case-priority 时默认只执行 P0 case
python3 $SKILL_DIR/scripts/case2webe2e.py run-local \
  --case-md test/case.md \
  --confirmed-env \
  --plan-out out/local_execution_plan.json

# 本地模式：如需覆盖默认行为，可显式指定优先级；all 会包含未标记 priority 的 case
python3 $SKILL_DIR/scripts/case2webe2e.py run-local \
  --case-md test/case.md \
  --case-priority all \
  --confirmed-env \
  --plan-out out/local_execution_plan.json

# 原子能力（用户主动调用）：把 case.md 转成 test/yaml-scripts/<case>.yaml
python3 $SKILL_DIR/scripts/case2webe2e.py gen-yaml \
  --case-md test/case.md

# 步骤 4：按 task_id 查询任务状态
python3 $SKILL_DIR/scripts/case2webe2e.py query-task --task-id <task_id>

# 步骤 5：任务完成后，先写 Overview 到 test_report.md
python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task --task-id <task_id> --case-md test/case.md

# 步骤 6：用户确认后，再继续详细分析
python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task --task-id <task_id> --case-md test/case.md --detail
```

## 子命令说明

### 1. `init-env`

- 在 `case.md` 同目录下创建默认 `.env` 文件
- 若存在 `task.md`，优先用其中的 `RUN_ENV`、`SWIMLANE`、`TEST_IDC` 预填 `.env`
- 若文件已存在，则跳过创建
- 输出文件路径

### 2. `show-env`

- 读取并输出当前环境配置，便于展示给用户确认
- 输出格式为 JSON，包含 `env_file` 和 `config` 字段

### `list-platforms`

- 按需查询当前所有可用的 Web E2E 平台
- 底层调用 `https://po3gp9uh.fn.bytedance.net/getWebE2EPlatform?withMeta=true`
- 输出 JSON，包含 `count` 和 `platforms`
- `platforms` 里默认保留 `nameZh`、`platform`、`domain`、`poc`

### `platform-detail`

- 按 `platform` 查询某个 Web E2E 平台详情
- 如已知 `domain`，建议一并透传，避免同名平台冲突
- 底层调用 `https://po3gp9uh.fn.bytedance.net/getWebE2EPlatformDetail?platform=<platform>&withMeta=true[&domain=<domain>]`
- 输出 JSON，包含 `platform`、`domain`、`variables`、`default_keys`、`required_keys`
- `variables` 中会标记哪些字段可直接使用默认值，哪些字段仍需用户手动补充

### 3. `prepare`

- 只做解析和 payload 拼装
- 未显式指定 `--case-priority` 时默认只保留 `P0` case
- 可通过 `--case-priority P1`、`--case-priority P2`、`--case-priority P3` 或 `--case-priority all` 覆盖默认行为；其中 `all` 会包含未标记 priority 的 case
- 用于调试 `markdown2midscene` 返回结果和 `create_case_group` 请求体

### 4. `create-group`

- 创建用例组但不触发执行
- 未显式指定 `--case-priority` 时默认只保留 `P0` case
- 可通过 `--case-priority P1`、`--case-priority P2`、`--case-priority P3` 或 `--case-priority all` 覆盖默认行为；其中 `all` 会包含未标记 priority 的 case
- 支持 `--case-group-id <id>`：传入后改走 `edit_with_cases` 更新同一用例组，不再新建
- 输出 `case_group_name`、`case_count`、`case_group_id`、`case_group_action`

### 4.1 `edit-group`

- 专门用于 `case.md` 更新后，把已有 TTAT 用例组同步到最新
- 强制参数：`--case-group-id <id>`
- 内部直接调用 `edit_with_cases`，复用和 `create-group` 一致的 payload
- 不触发 TTAT 任务，也不新建 case group
- 输出 `case_group_name`、`case_count`、`case_group_id`、`case_group_action: updated`

### 5. `run`

- `EXECUTION_MODE=ttat` 时：执行完整链路，创建或更新用例组并直接触发 TTAT 自动化任务
- `EXECUTION_MODE=local` 时：等价转到 `run-local`
- 未显式指定 `--case-priority` 时默认只保留 `P0` case
- 可通过 `--case-priority P1`、`--case-priority P2`、`--case-priority P3` 或 `--case-priority all` 覆盖默认行为；其中 `all` 会包含未标记 priority 的 case
- 支持 `--case-group-id <id>`：已有 case group 时必须带上该参数，`run` 会先更新 case group，再触发新任务
- 默认在 `case.md` 同目录写入 `test_report.md`
- 创建任务后会立即把任务基础信息和 `case_group_action` 写入 `test_report.md`
- 输出 `case_group_id`、`case_group_action`、`task_id`、`task_url`、`report_file`

### 6. `run-local`

- 生成 `local_execution_plan.json`，并初始化本地模式的 `test_report.md`
- 未显式指定 `--case-priority` 时默认只保留 `P0` case
- 可通过 `--case-priority P1`、`--case-priority P2`、`--case-priority P3` 或 `--case-priority all` 覆盖默认行为；其中 `all` 会包含未标记 priority 的 case
- 统一调用 `markdown2midscene` 解析 `case.md`
- 后续执行阶段必须由主 agent 优先调用一个执行 subagent，并把 `local_execution_plan.json` 与 `test_report.md` 路径交给它；若当前工具没有 subagent 能力，则主 agent 按同一约束自行执行。该单一执行 agent 编排 `playwright-cli`（每个 case 一条 `-s=<caseId>` session），再由 `playwright-cli` / runner 按 `LOCAL_CASE_CONCURRENCY` 做 case 级并发；把截图、trace、录像、控制台日志通过 `-s=<caseId>` 实时落到 `test_result/<caseId>/`；每个 case 至少有 `step_001_*.png` 入口截图和 `final.png` 结束截图（无条件落地）；失败 / 抛错 / 超时路径还需在 `close` 之前补 `failure.png`
- 不允许采用无法把产物稳定归档到 `test_result/<caseId>/` 的批量执行方式
- 启动前必须完成 `playwright-cli` 安装检查；未安装时一次性请求确认安装命令 `npx @tiktok-fe/skills add microsoft/playwright-cli --source github --skill playwright-cli`，用户拒绝则停止
- 会把 `LOCAL_CASE_CONCURRENCY` 解析为 `case_concurrency` 写入本地执行计划；若未配置则默认 `10`
- 会把基于 `RUN_ENV` / `SWIMLANE` 生成的 `browser_headers` 与 `browser_header_setup` 写入本地执行计划；执行 agent 必须在每个 session `open` 后、首次 `goto` 前运行 `browser_header_setup.code`
- 输出 `execution_mode`、`local_runner`（`playwright-cli`）、`runner_mode`、`case_concurrency`、`case_count`、`plan_file`、`report_file`、`runtime.playwright_cli`
- 不创建 TTAT `case_group_id` / `task_id`

### 7. `gen-yaml`（原子能力，用户主动调用）

- 把 `case.md` 转成多个 Midscene YAML 脚本，每个 case 一个 `<case名称>.yaml`
- 默认输出目录为 `case.md` 同级的 `yaml-scripts/`，可用 `--out-dir` 覆盖
- 与 `run` / `run-local` 共用 `markdown2midscene` 解析和 `--case-priority` 过滤语义；默认只保留 `P0` case
- 文件结构对齐 `resources/midscene_template.yaml`：`web.url` 取该 case flow 中第一条 URL 步骤并从 flow 中移除；其他 `ai` / `aiAssert` / `sleep` 等步骤原样保留
- Case flow 中缺少 URL 步骤时，若未提供 `--default-url` 则跳过该 case，并在 stdout JSON 的 `skipped` 数组中给出原因
- **严禁**自动触发；只有在用户主动通过 `/webe2e 生成YAML`、`yaml-gens`、"生成 YAML" 等话术明确要求时才运行

### 9. `query-task`

- 按 `task_id` 查询 TTAT 任务状态
- 输出 JSON，包含 `task_id`、`task_name`、`execute_status`、`task_counts`、`status_line`、`done` 和原始响应

### 10. `analyze-task`

- 按 `task_id` 显式进入报告分析流程
- 仅当任务状态同时满足 `status_code=0` 且 `execute_status=10` 时才会真正进入分析；否则只返回当前状态，不自动等待
- 默认模式只收集失败 case 概览，并把 Overview 写入 `test_report.md`
- 默认模式必须给出"是否继续下钻详细分析"的确认提示，以及基于失败 case 数量推算的预计耗时
- 默认模式必须把"失败 case 数量 -> 预计耗时"的推算结果明确展示给研发，不能只说"耗时较久"这类模糊描述
- 只有显式带 `--detail` 时，才继续读取节点执行信息，并优先下载对应 `.md.tar` 归档解析其中的 `report.md` 与 `screenshots/`；仅当 `.md.tar` 不可用时才回退 HTML 报告，生成详细分析
- `--detail` 会逐 case 增量落盘到 `test_report.md`，每完成一个 case 就立即更新进度
- 如果 `--detail` 过程中因超时或中断没有跑完，报告里必须明确标注"详细分析未完成"，并提示重新执行同一条命令继续
- 再次执行 `--detail` 时，必须自动跳过已完成 case，避免重复分析
- 调用 `--detail` 时，建议外层命令超时不少于 `900000ms`（15 分钟）
- 为避免重复，Overview 保留失败 case 清单；详细分析阶段只保留"根因汇总 + 逐 case 下钻"，不再重复输出原始失败清单
- 默认输出 Markdown；可用 `--format json` 输出结构化结果
- `--report-out` 可改写分析结果落地路径；未传时优先写 `--case-md` 同目录下的 `test_report.md`

## analyze-task 分析规范

### 批量分析流程

执行 `analyze-task --task-id <task_id>` 时，必须按以下顺序处理：

1. 查询任务状态，确认任务已完成
2. 查询失败 case 列表
3. 根据失败 case 数量估算详细分析耗时
4. 先将 Overview 写入 `test_report.md`，内容只包含任务概览、失败 case 列表、下一步确认提示和预计详细分析耗时
5. AI 必须在终端明确提示：当前失败 case 数、预计耗时、分析范围，并在此处暂停等待确认
6. 只有用户明确确认后，才继续执行带 `--detail` 的详细分析
7. 详细分析阶段再对每个失败 case 查询 `query_task_case_node_execution`
8. 详细分析阶段优先拉取对应 Markdown 归档：`https://tosv-sg.tiktok-row.org/obj/tiktok-ttat-uimost-sg/webui/{task_id}_{case_execution_id}.md.tar`，解压读取 `report.md` 和 `screenshots/`；仅当归档 404 / 不可用时回退 HTML：`https://tosv-sg.tiktok-row.org/obj/tiktok-ttat-uimost-sg/webui/{task_id}_{case_execution_id}.html`
9. 每分析完 1 个 case，就立即把最新进度和已完成 case 的详细结果写回 `test_report.md`
10. 如果命令因超时或中断结束，必须在报告和终端中明确说明"当前仅完成部分 case 详细分析"，并提示重新执行同一条 `--detail` 命令
11. 重新执行 `--detail` 时，自动跳过已完成 case，只继续剩余 case
12. 如调用方明确要求，再额外生成 Excel 或其他汇总产物

### 首步截图优先检查

详细分析任何失败 case 前，必须先做首步页面校验。这一条优先级高于单个错误摘要，也高于后续步骤里的业务细节。

1. 先取第一个 execution 的第一张有效截图，确认首步是否真的进入了目标页面
2. 必须优先识别以下首步异常：`404` / `Page not found` / 登录页 / 权限页 / 白屏 / 启动页
3. 如果首步已经异常，后续 case 的失败大概率是连锁反应；此时仍要记录各 case 的局部现象，但汇总时必须收敛到共享上游原因
4. 不要因为首步 `waitFor` 返回成功，就默认认为页面正确；页面有内容 ≠ 已进入正确业务页
5. 如果首步截图与首个节点 instruction 指向的 URL / 页面不一致，优先把问题定位在 URL、登录态、权限或环境前置条件

### 单 case 必须包含的信息

每个失败 case 的分析结果必须至少包含：

- 失败步骤序号
- 失败步骤原始 instruction（来自节点执行接口的 `step_name`）
- 若 instruction 为空，必须明确标注"当前节点没有拿到可执行步骤文本"
- 报告关键片段：Markdown 路径下引用 `report.md` 中失败 `## N. <TaskType>` 区块的 `Error` / `Error stack`；HTML 回退路径下引用 `reasoning_content`
- 失败截图与首步截图的验证结论；Markdown 路径下直接读取 tar 内 `screenshots/` JPEG，HTML 回退路径下再使用内嵌截图
- **截图引用必须落到具体文件**：在 `单 case 必须包含的信息` 与下游产物（根因汇总表 / Excel）里引用 Markdown 报告时，**不要**只贴 `.md.tar` 归档地址；要直接贴本次分析所依据的**具体截图**——即 `screenshots/<step_or_failure>.jpg`（解压后的本地路径或 `tos*` 直链都行）。tar 是来源，但读者要看的是"这一帧画面是什么"，不是"去哪个压缩包里翻"。每个 case 至少给 `首步截图` + `失败截图` 两条具体路径；只贴 tar 视为分析未完成。
- 失败现象
- 关键证据（至少 2 条，优先来自 instruction / 节点错误 / reasoning / 截图）
- 排除判断（为什么不是更常见的相似类）
- 直接原因
- 根本原因
- 归因类别（见下方归因分类体系）
- 归因子分类
- 置信度（高 / 中 / 低）
- 修复建议

额外约束：

- 每个 case 都必须做 **原始 instruction + 报告错误/推理片段 + 截图** 三方交叉验证；不能只读错误摘要就下结论
- 如果 HTML 回退路径中的 `reasoning_content` 与截图结论冲突，或 Markdown 路径中的错误描述与截图不一致，以截图体现的页面状态为准，并把这种冲突写进分析结果
- 如果首步截图已经显示 404 / 登录页 / 权限页 / 白屏，则后续 case 默认按连锁失败思路继续分析，除非有更强证据证明失败发生在独立步骤
- 如果 instruction 为空，但 `error_message`、截图、页面状态或 Markdown/HTML 报告已经给出更强证据，则必须优先采用这些更强证据归因
- 如果没有足够证据，结论只能写"当前证据不足以确定根因"，不能直接写"instruction 为空"
- `instruction 为空` 只能作为现象或证据，不能自动等于最终根因；只有原始报错明确指出空 instruction 时，才允许归为 `Bits2Midscene-解析步骤`
- 如果没有 `关键证据`、`排除判断` 或 `置信度`，则视为分析不完整

### 截图与推理的强制校验

分析时不能只看错误摘要，必须同时核对报告关键片段、原始 instruction 与截图线索。TTAT 模式下报告读取优先级固定为 `.md.tar` 的 `report.md` + `screenshots/`，HTML 仅作为回退：

1. 先看第一步是否已经进入正确页面
2. 第一优先级是核对首步页面是否为 `404`、`Page not found`、登录页、权限页、白屏/启动页；若首步已异常，后续失败大多属于连锁反应
3. 第二优先级是核对失败步骤的原始 instruction、报告中的 `Error` / `Error stack`（或 HTML 回退的 `reasoning_content`）与失败截图是否相互印证
4. 如果报告文本与截图线索不一致，以截图体现的页面状态为准；分析结果里必须写清楚冲突点
5. 不能只写"AI 操作失败""断言失败""页面加载问题"这类泛化结论，必须说清楚失败发生在什么页面、哪一步、哪里不一致
6. `failed to locate element`、`Replanned 100 times`、`instruction incomplete` 都只是现象，不能直接跳到模型或 `Bits2Midscene`
7. 如果 Markdown/HTML 报告没有明确 `failed task`，必须继续检查执行任务序列是否存在长时间循环
8. 判断循环时，**优先看多步 `Planning` prompt 是否高度重复、`Action Space` 是否反复穿插、执行是否长期没有前进**；不要依赖 `BOE`、`TikTok Test` 这类业务关键词做结论
9. 循环摘要应写成抽象结论，例如"重复 prompt 模式累计出现 24 次，执行未进入稳定的后续步骤"，而不是抄具体业务词当根因

### 归因分类体系（v2 - 对齐人工标准）

> **重要变更**：归因输出不再使用旧的"改动方"单一字段，改为输出 **归因类别 + 归因子分类** 双层结构。以下分类体系与业务 QA 人工归因标准完全对齐。

#### 一级归因类别

| 归因类别 | 定义 | 典型场景 |
|---------|------|---------|
| **Case 测试数据问题** | 测试数据不满足前置条件 | 页面数据为空、搜索无结果、账号不存在、测试数据被占用、预期数据已过期 |
| **Case 描述 - 业务QA** | 用例步骤/断言本身的描述有问题 | 步骤描述不清晰、断言文案与页面不一致、URL 填写错误、预期与实际页面结构不匹配 |
| **Bits2Midscene-解析步骤** | markdown2midscene 转换阶段产生的问题 | 空步骤（instruction 为空）、URL 解析错误、节点文本丢失、步骤拆分异常 |
| **工具问题 - 模型** | 模型本身的执行或规划能力问题 | 模型 429、LLM 返回空、JSON 解析失败、Replanned 100 次、明确的元素定位失败（排除数据/描述问题后）、规划路径不合理 |
| **Midscene** | Midscene 框架层面的问题 | 首步 waitFor timeout、白屏启动页、页面未稳定、浏览器内部截图错误 |
| **环境问题** | 运行环境相关的非业务问题 | 登录凭证失效、Google 登录页弹出、session 过期、网络连接错误、CDN 超时 |
| **Bug** | 被测产品的实际 Bug | 页面功能异常，操作和断言均正确但产品行为不符合 PRD |

#### 二级归因子分类

| 一级类别 | 子分类 | 典型证据 |
|---------|--------|---------|
| Case 测试数据问题 | **空数据** | 页面/表格显示 No result、No tasks found、空列表 |
| Case 测试数据问题 | **断言描述** | 断言中的预期文案/顺序/结构与页面实际不一致（如侧边栏新增了 Shop 条目） |
| Case 描述 - 业务QA | **步骤描述** | 步骤指令模糊（如"点击右上角按钮"但存在多个按钮）、操作路径不正确 |
| Case 描述 - 业务QA | **步骤清晰度** | 步骤可执行但歧义导致模型选错目标 |
| Case 描述 - 业务QA | **断言描述** | 断言条件本身写错或不可验证 |
| Case 描述 - 业务QA | **URL** | Case 中配置的 URL 不正确或缺少必要参数 |
| Bits2Midscene-解析步骤 | **空步骤** | markdown2midscene 转换后 instruction 字段为空 |
| Bits2Midscene-解析步骤 | **URL** | 转换后 URL 丢失或拼接错误 |
| 工具问题 - 模型 | **规划能力** | 模型规划路径不合理、错误地跳过关键步骤 |
| 工具问题 - 模型 | **执行边界** | 模型无法处理复杂交互（如拖拽、多级下拉） |
| 工具问题 - 模型 | **断言太快** | 操作执行后未等待页面稳定就发起断言 |
| Midscene | **启动失败** | 首步 timeout、白屏 |
| Midscene | **截图异常** | Protocol error (Page.captureScreenshot) |
| 环境问题 | **网络错误** | 请求超时、DNS 解析失败、CDN 错误 |
| 环境问题 | **登录态** | 登录弹窗、凭证失效、Google / TikTok SSO 登录跳转或嵌入式 SSO 登录卡片（含子站点 SSO） |
| 环境问题 | **访问拦截** | 请求被 ROW Operations Gateway / 网络隔离策略拒绝、`network_segregation_rejected`、`IP not allowed`、`rejected by gateway`、防火墙阻断 |
| Bug | **功能异常** | 产品行为与 PRD 不一致 |

#### ⚠️ 不再使用的旧分类

以下旧标签已废弃，**禁止在输出中使用**：
- ❌ `改动方: 模型` → 改用 `归因类别: 工具问题 - 模型`
- ❌ `改动方: prd2case-web` → 改用 `归因类别: Bits2Midscene-解析步骤`（确认是转换阶段问题）或 `归因类别: Case 描述 - 业务QA`（确认是用例描述问题）
- ❌ `改动方: 业务QA` → 改用 `归因类别: Case 测试数据问题` 或 `归因类别: Case 描述 - 业务QA`（必须区分数据问题 vs 描述问题）
- ❌ `改动方: 业务QA（待确认）` → 已废弃，如证据不足直接标注置信度为"低"并给出最可能的归因方向
- ❌ `改动方: 待确认` → 已废弃，同上

#### 与旧 report-analysis 口径的映射

为兼容历史分析习惯，阅读旧报告时可按下面方式映射到当前 `webe2e` 的 v2 归因体系：

| 旧口径 | 当前归因类别 | 常见落点 |
|------|------|------|
| `改动方: 业务QA` | `Case 测试数据问题` 或 `Case 描述 - 业务QA` | 空数据、前置条件未满足、步骤描述不清、断言文案不符 |
| `改动方: prd2case-web` | `Bits2Midscene-解析步骤` | 空步骤、URL 丢失、节点拆分异常 |
| `改动方: 模型` | `工具问题 - 模型` | 规划能力、执行边界、断言太快 |
| `改动方: Midscene` | `Midscene` | 启动失败、截图异常、页面未稳定 |
| `改动方: Bug` | `Bug` | 功能异常 |
| `改动方: 环境问题` | `环境问题` | 登录态、网络错误、权限页、环境不可达 |

如果旧报告里只有 `改动方`，没有进一步细分，迁移时必须继续补全到当前格式：`归因类别 + 归因子分类 + 根因摘要`，不能只保留旧标签。

### 强制分层归因决策树

> **重要变更**：原规则写了"分层排除不能跳步"但执行中经常跳步。现改为强制决策树，每个 case 必须在输出中逐层展示排除过程。

每个 case 必须严格按以下顺序逐层排除，**每一层的判断结果必须在输出中显式写出**（即使结论是"排除"）：

```text
┌─ Layer 1: 证据充分性检查
│  Q: 是否同时具备节点执行信息 + Markdown/HTML 报告 + 截图/错误或推理片段？
│  → 否：置信度强制降为"低"，在归因结论前标注"⚠️ 证据不足"
│  → 是：继续 Layer 2
│
├─ Layer 2: 测试数据检查
│  Q: 页面是否显示空数据/No result/空列表？搜索/筛选后无匹配结果？
│  Q: 账号/前置数据是否不满足条件？
│  → 命中：→ Case 测试数据问题 / 空数据
│  → 不命中，继续 Layer 3
│
├─ Layer 3: 断言一致性检查
│  Q: 断言预期的文案/结构/顺序是否与页面实际不一致？（如页面新增/移除了元素）
│  → 命中：→ Case 测试数据问题 / 断言描述
│  → 不命中，继续 Layer 4
│
├─ Layer 4: 步骤/instruction 检查
│  Q: instruction 是否为空？
│  → 空：→ Bits2Midscene-解析步骤 / 空步骤
│  Q: 步骤描述是否清晰可执行？是否有歧义/错误？
│  → 不清晰/有错：→ Case 描述 - 业务QA / 步骤描述 或 步骤清晰度
│  Q: URL 是否正确？
│  → URL 错误：→ Case 描述 - 业务QA / URL 或 Bits2Midscene-解析步骤 / URL
│  → 全部通过，继续 Layer 5
│
├─ Layer 5: 时序检查（断言太快）
│  Q: 失败步骤中是否同时包含「操作」和「断言」？
│  Q: 操作刚执行后是否立即进行了断言（无等待）？
│  Q: 截图是否显示页面处于加载态/动画进行中/搜索结果未返回？
│  → 全部命中：→ 工具问题 - 模型 / 断言太快
│  → 不命中，继续 Layer 6
│
├─ Layer 6: 环境检查
│  Q: 请求是否被网关 / 网络隔离策略直接拒绝？(network_segregation_rejected / rejected by gateway / IP not allowed / fail to discover office network)
│  → 命中：→ 环境问题 / 访问拦截（最高优先级，断言失败、空数据等都是连锁结果）
│  Q: 首步页面是否为 404、登录页、权限页、白屏？
│  Q: 是否出现登录弹窗、TikTok/Google SSO 登录卡片、session 过期、网络错误？
│       —— 注意：嵌入式 SSO 登录卡片（外框已渲染但内容区是 `Enter email or email prefix` / `TikTok SSO` 卡片）也算登录态命中
│  Q: Markdown/HTML 报告是否出现前置步骤长循环，同时伴随 Request Error / RPC error / service error？
│  → 命中：→ 环境问题 / 对应子分类，或 Midscene / 启动失败
│  → 不命中，继续 Layer 7
│
│  归因器实现说明：Layer 1.5 与 Layer 6 共享同一组 login / access-block 信号检测，
│  且 gate 同时考察「首步截图摘要 + 失败截图摘要 + error_message 文本」三路输入；
│  当 `error_message` 同时含 `assertion failed` 与登录/访问拦截信号时，Layer 3 会主动
│  让出，把案件交给 Layer 6（断言失败仅是被前置拦截后的连锁现象，不是独立根因）。
│
├─ Layer 7: 产品 Bug 检查
│  Q: 操作步骤和断言本身都正确，但产品行为不符合预期？
│  → 命中：→ Bug / 功能异常
│  → 不命中，继续 Layer 8
│
└─ Layer 8: 模型能力问题（兜底层）
   只有以上所有层级都排除后，才归为模型问题：
   Q: 模型是否返回 429 / empty content / JSON 解析失败？
   → 是：→ 工具问题 - 模型 / 执行边界
   Q: 模型是否 Replanned 100 次 / 规划路径明显不合理？
   → 是：→ 工具问题 - 模型 / 规划能力
   Q: Markdown/HTML 报告是否显示多步 `Planning` prompt 高度重复、`Action Space` 反复穿插，但没有更强的环境错误信号？
   → 是：→ 工具问题 - 模型 / 规划能力
   Q: 模型是否在步骤清晰、数据存在的情况下仍定位失败？
   → 是：→ 工具问题 - 模型 / 执行边界
```

**强制输出格式**：每个 case 的分析中必须包含一个"归因决策路径"段落，格式如下：

```text
归因决策路径：
- Layer 1 证据充分性：✅ 具备节点信息 + Markdown/HTML 报告 + 截图
- Layer 2 测试数据：✅ 排除（页面有数据展示）
- Layer 3 断言一致性：❌ 命中 → 侧边栏新增 Shop 条目，预期顺序为 For You → Explore，实际为 For You → Shop → Explore
- 归因结论：Case 测试数据问题 / 断言描述
```

### 根因摘要格式约束

> **重要变更**：禁止使用泛化现象描述作为根因摘要。失败 case 详细分析里的 `根因摘要` **必须直接包含下钻到的细节**——即把"决定责任的那条具体证据"写进摘要，不得写"详见下文 / 详见关键证据"或只贴一个分类标签。读者看 `根因摘要` 一行就能知道为什么、责任落在谁。

根因摘要必须包含四要素：**[失败环节] + [具体现象 + 触发条件] + [关键证据指针] + [责任判定]**

- **失败环节**：第几步 / 哪个 instruction / 哪个节点。
- **具体现象 + 触发条件**：页面 / 接口 / 模型实际怎么了，**直接抄那条决定性的证据原文**（错误信息、报错码、URL diff、断言期望 vs 实际、空 instruction、循环 prompt 摘要等），不要二次抽象。
- **关键证据指针**：把决定结论的证据落到具体来源——`报告 ## N. <TaskType> 的 Error/Error stack` 行号 / `screenshots/step_NN_*.jpg` 文件名 / `reasoning_content` 节选片段；这一条让读者能直接跳到证据，而不是再读一遍下面的详细分析。
- **责任判定**：括号里写 `归因类别 / 归因子分类`，与下文 `最终归因` 字段保持一致。

**禁止的根因摘要示例**（现象描述 / 标签化 / 把读者甩到下文）：
- ❌ "指令不完整"
- ❌ "登录问题"
- ❌ "Follow 按钮问题"
- ❌ "Explore 页面问题"
- ❌ "内部错误"
- ❌ "需进一步分析"
- ❌ "Bits2Midscene-解析步骤"（只剩归因标签，没有具体现象 + 证据）
- ❌ "详见下方关键证据 / 详细分析"（强制读者下钻才知道答案）

**正确的根因摘要示例**（含失败环节 + 具体证据 + 指针 + 责任判定）：
- ✅ "第 2 步 instruction 为空（`report.md` `## 2. AIAction` 中 `step_name` 字段为空，`screenshots/step_02_aiAction.jpg` 显示模型未发出动作），markdown2midscene 转换时丢失了操作步骤文本（Bits2Midscene-解析步骤 / 空步骤）"
- ✅ "首步跳转到 `accounts.google.com/...`（`screenshots/step_01_landing.jpg`，与 case 配置的目标 URL `https://platform/.../detail` 不一致），case 中 URL 未包含登录态参数（Case 描述 - 业务QA / URL）"
- ✅ "Explore 页面无视频封面展示（`screenshots/step_03_failure.jpg` 空列表 + `report.md` 节点 3 的 `Error: HTTP 502 from /api/explore/feed`），网络请求 502，非 case 问题（环境问题 / 网络错误）"
- ✅ "第 3 步断言侧边栏顺序 `For You → Explore`，页面实际 `For You → Shop → Explore`（`screenshots/step_03_assert.jpg` 与 `Error stack` 中 `expected ['For You','Explore'] received ['For You','Shop','Explore']`），新增了 Shop 入口（Case 测试数据问题 / 断言描述）"
- ✅ "第 4 步点击 Close 后模型返回 `empty content from AI`（`report.md` `## 4. AIAction` 的 `Error: empty content from AI`），模型服务异常（工具问题 - 模型 / 执行边界）"
- ✅ "第 2 步搜索后立即断言表格有数据，截图 `screenshots/step_02_assert.jpg` 显示结果仍在加载（loading skeleton 可见，断言早于数据返回 280ms），断言太快（工具问题 - 模型 / 断言太快）"

### 连锁失败收敛

详细分析时，不能把明显共享上游原因的 case 机械拆成多个独立根因。至少要检查是否存在以下模式：

- 首步 URL / 登录态异常，导致后续所有断言一起失败
- 某个核心动作提交失败，后续 toast、状态更新、列表持久化全部跟着失败
- 同一类数据缺失导致多个 case 同时出现 `No tasks found`、`No result`、空列表
- 同一 UI 变更（如侧边栏新增条目）导致多个 case 断言失败

如果命中这类模式：

- 单 case 里仍要写各自失败现象
- 但汇总里必须把它们收敛为共享上游原因，避免"11 个 case，11 个不同根因"的假象
- 单 case 分析中增加字段：`收敛标记: "与 Case-XXX 共享上游原因：[原因简述]"`

### 常见归因规则（更新版）

#### `Bits2Midscene-解析步骤`（原 prd2case-web 部分场景）

- 真实报错明确指出 instruction 为空、`No specific instruction was provided`
- URL 在 markdown2midscene 转换后丢失或拼接错误
- 节点文本在转换阶段丢失，导致模型拿不到操作目标
- **⚠️ 判定标准**：必须确认问题出在 markdown → midscene 转换环节；如果 case.md 原始步骤本身就不清晰，应归为 `Case 描述 - 业务QA`
- **⚠️ 与模型的区分**：如果 instruction 不完整但模型仍然可以合理推断操作（只是执行失败），应归为 `工具问题 - 模型`

#### `工具问题 - 模型`

- 模型服务 `429`
- `empty content from AI model`
- `failed to parse LLM response into JSON`
- `Replanned 100 times`
- Markdown/HTML 报告里多步 `Planning` prompt 高度重复，`Action Space` 反复出现，但没有更强的环境错误信号时，可归为 `规划能力`
- **断言太快**：操作执行后未等待页面稳定即断言，截图显示加载态
- **⚠️ 前置排除**：归为模型问题前，必须已排除 Layer 2-6 的所有可能；如果步骤描述不清晰导致定位失败，根因在 Case 描述而非模型

#### `Midscene`

- 首步 `waitFor timeout`
- 截图显示 TikTok logo 白底启动页、白屏、长时间 loading
- `Protocol error (Page.captureScreenshot): Internal error`（Midscene 框架的截图异常）
- 任务失败点主要发生在页面尚未稳定时

#### `Case 测试数据问题`

- 账号不存在
- 前置数据不满足，例如没有可用收藏视频、测试数据已被占用
- 页面/表格显示 `No result`、`No tasks found`、空列表
- 断言中的预期文案/结构/顺序与页面实际不一致（**UI 更新导致断言过期**）

#### `Case 描述 - 业务QA`

- 步骤描述不清晰或有歧义，导致模型无法准确执行
- 步骤路径本身不正确（如元素不存在、导航路径错误）
- 断言条件写错或不可验证
- Case 中配置的 URL 不正确

#### `环境问题`

- 登录凭证失效、Google 登录页弹出
- Session 过期
- 网络连接错误、CDN 超时
- Markdown/HTML 报告显示执行长时间卡在同一前置步骤循环，同时伴随 `Request Error`、`RPC error`、未处理服务错误提示
- **⚠️ 与 Case 描述的区分**：如果 URL 本身就配错了（写的就不对），归 Case 描述；如果 URL 正确但环境不可达，归环境问题

### Markdown/HTML 报告循环判定

当节点执行接口没有给出明确失败步骤，或 Markdown/HTML 报告里没有明确 `failed task` 时，必须进一步检查执行任务序列：

- 重点看 `Planning` 是否连续高频出现，且中间反复穿插 `Action Space`
- 重点看多个 `Planning` 的 prompt 是否属于同一类语义，经过归一化后仍高度重复
- 如果重复 prompt 模式持续出现，且执行没有进入新的稳定步骤，可视为"卡在同一阶段循环"
- 如果循环同时伴随 `Request Error` / `RPC error` / service error，优先归为 `环境问题 / 网络错误`
- 如果循环存在，但没有更强的环境或服务异常信号，再考虑归为 `工具问题 - 模型 / 规划能力`
- 输出时必须总结成抽象模式，例如：
  - `重复 prompt 模式累计出现 24 次，执行未进入稳定的后续步骤`
  - `Planning / Action Space 在同一前置阶段反复切换，但没有形成有效前进`
- 禁止把页面里的业务实体词直接当作根因；业务词最多只能作为辅助证据，不能代替循环判定本身

#### `Bug`

- 页面功能异常，操作步骤和断言本身都正确，但产品行为不符合预期
- 需要截图或 Markdown/HTML 报告中有充分证据证明是产品问题

### 禁止的通用归因

以下表述不能直接作为最终结论：

- "任务执行失败"
- "AI 操作失败"
- "断言不通过"
- "页面加载问题"
- "元素定位失败"
- "全部都是 prd2case-web"
- "没有证据，但先归因为 instruction 为空"
- "指令不完整"
- "登录问题"
- "XXX 按钮问题"
- "XXX 页面问题"
- "内部错误"
- "需进一步分析"
- "待确认"

必须替换成带上下文的结论，例如：

- "第 5 步点击视频封面后实际跳转到 `@haniawooga` 的视频详情页，与预期 `@testhmuhdwstmh` 不一致"
- "第 2 步首屏仍停留在 TikTok logo 白底启动页，`waitFor` 多次判断页面处于加载态，未进入目标 profile 页面"
- "第 2 步 instruction 为空，模型没有可执行动作，因此直接返回 `No specific instruction was provided`"
- "当前只有节点元数据缺失，尚无足够证据判断是步骤生成缺陷还是业务态异常，需要继续结合错误信息或页面状态确认"

### 建议输出骨架

每个失败 case 的文字分析建议固定按下面结构输出：

- `失败步骤信息`：步骤序号、原始 instruction、节点/执行名称
- `报告关键片段`：Markdown 路径引用 `report.md` 的 `Error` / `Error stack`，HTML 回退路径引用 `reasoning_content`
- `截图验证`：必须落到具体文件名，例如 `首步截图: screenshots/step_01_landing.jpg → 显示 ...`、`失败截图: screenshots/step_03_failure.jpg → 显示 ...`；若与 reasoning 不一致，必须明确写出差异。**禁止**只写"参见 `.md.tar`"或"见归档"。
- `失败现象`：页面 / 日志里实际发生了什么
- `关键证据`：至少 2 条
- `归因决策路径`：逐层排除记录（见上方强制格式）
- `排除判断`：为什么不是其他高相似类
- `直接原因`：具体错误现象，禁止泛化描述
- `根本原因`：为什么会发生，必须落到前置条件、步骤描述、转换链路、模型能力、环境或产品行为
- `最终归因`：`归因类别 / 归因子分类 / 根因摘要`；其中 `根因摘要` 必须按上文 `根因摘要格式约束` 直接写出"失败环节 + 具体现象+触发条件 + 关键证据指针 + 责任判定"，不得写"详见上文"或只剩归因标签
- `归因理由`：为什么责任落在这里
- `置信度`：高 / 中 / 低
- `收敛标记`：如有共享上游原因，标注关联 case
- `修复建议`：具体到用例、步骤或链路

### 可选汇总产物

- 默认先更新 `test_report.md` 中的 Overview，再由用户决定是否继续详细分析
- 详细分析阶段的"根因汇总"建议至少包含 `Case 名称`、`执行节点`、`归因类别`、`归因子分类`、`根因摘要`、`置信度`、`详情页`、`关键截图`、`Markdown 报告`、`HTML 回退报告`
- **`根因摘要` 列必须落地到下钻细节**：直接写出"哪一步 + 具体证据原文 + 责任判定"，不允许只贴归因标签或"详见下方"。详细分析章节的同名字段与汇总表保持一致。
- **`关键截图` 列必须给具体截图，不是 tar**：贴本次分析所依据的具体图片路径或直链（至少 `首步截图` 和 `失败截图` 各一张），格式如 `screenshots/step_01_landing.jpg`、`screenshots/step_03_failure.jpg`，或 markdown 图片语法 `![失败步](screenshots/step_03_failure.jpg)` 直接内嵌。`Markdown 报告` 列只放 `report.md` 的来源链接（tar 直链或解压目录），用于追溯，不是给读者去 tar 里翻图用的。
- 只有当用户明确要求导出 Excel、表格化汇总、或需要二次分发材料时，才额外生成 Excel
- 如果需要生成 Excel，建议包含：`Case 名称`、`执行节点`、`归因类别`、`归因子分类`、`根因摘要`、`置信度`、`失败步骤`、`失败现象`、`关键证据`、`排除判断`、`直接原因`、`根本原因`、`修复建议`、`详情链接`、`首步截图链接`、`失败截图链接`、`Markdown 报告链接`、`HTML 回退报告链接`
  - 其中 `首步截图链接` / `失败截图链接` 必须是具体图片直链，不允许用 `.md.tar` 归档地址替代。

## 参数说明

### list-platforms 命令

- 无额外参数

### platform-detail 命令

- `--platform`: 平台标识，必填
- `--domain`: 平台域，可选；当平台列表里存在同名 `platform` 时建议一并传入

### init-env 命令
- `--case-md`: `case.md` 路径，必填

### show-env 命令
- `--case-md`: `case.md` 路径，必填
- `--env-file`: 环境变量文件，可选

### gen-yaml 命令

- `--case-md`: `case.md` 路径，必填
- `--case-priority`: 可选；支持 `P0`/`P1`/`P2`/`P3`/`all`，默认 `P0`
- `--out-dir`: 可选；覆盖默认的 `yaml-scripts/` 输出目录（默认位于 `case.md` 同级）
- `--default-url`: 可选；当某个 case 的 flow 里没有 URL 步骤时，用此值作为 `web.url`；未提供时对应 case 会被跳过并在 stdout 的 `skipped` 列表中列出
- 其他 `--title` / `--creator` / `--env-file` / 平台相关参数与 `run` / `run-local` 共用，大多数场景下无需传入

### prepare / create-group / edit-group / run / run-local 命令

- `--case-md`: `case.md` 路径，必填
- `--title`: 用例组标题，可选；默认优先取 `case.md` 一级标题
- `--creator`: 创建者，可选；默认从 `git user.email` 推导
- `--env-file`: 环境变量文件，可选；默认读取 `case.md` 同目录的 `.env`
- `--case-priority`: 可选；支持 `P0`、`P1`、`P2`、`P3`、`all`，未传时默认只执行 `P0` case；`all` 会包含未标记 priority 的 case
- `--execution-mode`: 可选；覆盖 `.env` 里的 `EXECUTION_MODE`
- `--local-runner`: 可选；覆盖 `.env` 里的 `LOCAL_RUNNER`
- `--payload-out`: 仅 `prepare` / `create-group` / `edit-group` / `run` 常用；将 TTAT payload 写到本地，便于排查
- `--case-group-id`: `create-group` / `edit-group` / `run` 可用；有既有 TTAT 用例组时传入该值以更新同一组
- `--plan-out`: 仅本地模式使用；将 `local_execution_plan.json` 写到指定路径
- `--task-name`: 仅 `run` 使用；指定任务名，默认沿用 `case_group_name`
- `--token-name`: 仅 `run` 使用；获取动态 token 时的 name，默认使用 `creator`
- `--report-out`: `run` / `run-local` 使用；指定 `test_report.md` 输出路径，默认写到 `case.md` 同目录
- `--confirmed-env`: `run` / `run-local` 必填语义参数；只有在 `show-env` 展示完成且用户明确确认后才能传

### query-task 命令

- `--task-id`: TTAT 任务 ID，必填

### analyze-task 命令

- `--task-id`: TTAT 任务 ID，必填
- `--case-md`: 可选；用于把 Overview / 详细分析默认回写到 `case.md` 同目录的 `test_report.md`
- `--detail`: 可选；只有用户确认后才使用，开启失败 case 详细下钻分析
- `--format`: 输出格式，可选 `markdown` / `json`，默认 `markdown`
- `--report-out`: 自定义分析结果写入路径；不传时默认写 `test_report.md`

### export-storage-state 命令

- `--case-md`: 可选；用于读取同目录 `.env` 的 Chrome profile 配置
- `--env-file`: 可选；显式指定 `.env`
- `--user-data-dir`: 可选；覆盖 `CHROME_USER_DATA_DIR`
- `--profile-name`: 可选；覆盖 `CHROME_PROFILE_NAME`
- `--target-url`: 可重复；导出前让克隆 Chrome profile 访问目标 URL，用于把对应 origin 的 localStorage 等写入 storageState
- `--target-domain`: 可重复；profile 列举时用于统计目标域名 cookie
- `--output`: storageState 输出路径；不传时默认写当前目录 `.webe2e/storage_state.json`
- `--list-profiles`: 只枚举候选 Chrome profile，不导出
- `--headless`: 导出时以 headless 方式启动 Chrome；默认非 headless，便于 SSO/Keychain 场景稳定加载

### 超时恢复说明

- `analyze-task --detail` 的脚本内部 HTTP 超时是 15 分钟，因此外层 `Bash timeout` 也应至少设置为 `900000ms`
- 若 `--detail` 执行过程中被外层 `cc` 或其他执行器超时中断，`test_report.md` 中仍会保留已经完成的 case 详细分析
- 报告中的"分析进度"会明确展示已完成数、剩余数，以及"可能因超时或中断未完成"的提示
- 重新执行同一条 `--detail` 命令即可继续，脚本会自动跳过已完成 case

## 环境文件 `.env`

### 模板文件
模板文件位于 `resources/.env`，当执行 `init-env` 命令时会复制到 `case.md` 同目录下。

### 文件位置
执行时默认读取 `case.md` 同目录下的 `.env` 文件。

### 支持的参数
| 参数 | 说明 | 示例值 | 是否必需 |
|------|------|--------|----------|
| creator | 创建者邮箱前缀（必填） | yourname | 是 |
| EXECUTION_MODE | 执行模式 | ttat, local | 是 |
| LOCAL_RUNNER | 本地模式 runner，固定为 playwright-cli | playwright-cli | 是 |
| LOCAL_CASE_CONCURRENCY | 本地模式 case 级并发度 | 10 | 否 |
| STORAGE_STATE_MODE | 本地登录态来源；默认从 Chrome profile 导出 storage state | chrome-profile | 否 |
| CHROME_USER_DATA_DIR | Chrome user data dir；空值使用系统默认目录 | /Users/me/Library/Application Support/Google/Chrome | 否 |
| CHROME_PROFILE_NAME | Chrome profile 名称；空值表示必须先探测/确认实际登录 profile | Profile 1 | 否 |
| platform | 测试平台；仅 TTAT 远程链路使用，本地 playwright-cli 模式忽略 | live-campaign | 否 |
| RUN_ENV | 运行环境；`local` 表示前端本地部署环境，本地 playwright-cli 模式仅用于生成 header | local, boe, ppe, online | 否 |
| TEST_IDC | 测试机房 | sg, boe, ppe | 否 |
| SWIMLANE | 泳道标识；本地 playwright-cli 模式用于生成 `x-tt-env` header；`x-use-ppe` / `x-use-boe` 由 `RUN_ENV` 决定 | your_swimlane | 否 |
| TASK_TIMEOUT | 任务超时时间（分钟） | 10 | 否 |
| *自定义变量* | 任意自定义参数，会一并传入 TTAT | any_key=any_value | 否 |

### 默认模板（resources/.env）
```text
# Web E2E 执行环境配置
# 创建者邮箱前缀（必填，用于 TTAT 用例和任务创建）
creator=
# 执行模式: ttat, local
EXECUTION_MODE=ttat
# 本地执行 runner: playwright-cli
LOCAL_RUNNER=playwright-cli
# 本地 case 级并发度
LOCAL_CASE_CONCURRENCY=10
# 本地登录态来源: chrome-profile, none
STORAGE_STATE_MODE=chrome-profile
# Chrome user data dir；空值表示使用当前系统默认目录
CHROME_USER_DATA_DIR=
# Chrome profile 名称；空值表示必须先自动探测/展示候选，不得直接假设 Default
CHROME_PROFILE_NAME=
# 测试平台，如 live-campaign, your-platform
platform=live-campaign
# 运行环境: local, boe, ppe, online
RUN_ENV=ppe
# 测试机房: sg, boe, ppe 等
TEST_IDC=sg
# 泳道标识（可选）
SWIMLANE=
# 任务超时时间（分钟）
TASK_TIMEOUT=10
```

### `task.md` 预填规则

- 搜索路径：从 `case.md` 所在目录开始，逐级向上查找 `task.md`
- 预填变量：`RUN_ENV`、`SWIMLANE`、`TEST_IDC`
- 支持格式示例：

```md
- RUN_ENV: ppe
- TEST_IDC: sg
- SWIMLANE: ppe_xxx
```

```md
| RUN_ENV | ppe |
| TEST_IDC | sg |
| SWIMLANE | ppe_xxx |
```

- 如果 `task.md` 中没有这些值，也不会报错，用户仍可在环境确认阶段手动修正

## 推荐用法

### TTAT 模式（推荐）

```bash
# 1. 初始化环境配置文件
python3 $SKILL_DIR/scripts/case2webe2e.py init-env --case-md test/case.md

# 2. 展示当前环境配置（供用户确认）
python3 $SKILL_DIR/scripts/case2webe2e.py show-env --case-md test/case.md

# 3. 用户确认后执行完整链路；未传 --case-priority 时默认只执行 P0 case
python3 $SKILL_DIR/scripts/case2webe2e.py run \
  --case-md test/case.md \
  --confirmed-env \
  --payload-out out/case_group_payload.json

# 3b. 如需覆盖默认行为，可显式指定优先级；all 会包含未标记 priority 的 case
python3 $SKILL_DIR/scripts/case2webe2e.py run \
  --case-md test/case.md \
  --case-priority all \
  --confirmed-env \
  --payload-out out/case_group_payload.json

# 4. 显式查询任务状态
python3 $SKILL_DIR/scripts/case2webe2e.py query-task --task-id <task_id>

# 5. 任务完成后，先把 Overview 写入 test_report.md
python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task --task-id <task_id> --case-md test/case.md

# 6. 用户确认后，再继续详细下钻
python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task --task-id <task_id> --case-md test/case.md --detail
```

### 本地模式（playwright-cli）

```bash
# 1. 初始化环境配置文件
python3 $SKILL_DIR/scripts/case2webe2e.py init-env --case-md test/case.md

# 2. 展示当前环境配置（确认 EXECUTION_MODE=local，LOCAL_RUNNER=playwright-cli）
python3 $SKILL_DIR/scripts/case2webe2e.py show-env --case-md test/case.md

# 2b. 探测 playwright-cli；缺失时一次性请求确认安装
command -v playwright-cli >/dev/null 2>&1 || \
  npx @tiktok-fe/skills add microsoft/playwright-cli --source github --skill playwright-cli

# 3. 用户确认后，生成本地执行计划并初始化报告；未传 --case-priority 时默认只执行 P0 case
python3 $SKILL_DIR/scripts/case2webe2e.py run-local \
  --case-md test/case.md \
  --confirmed-env \
  --local-case-concurrency 10 \
  --plan-out out/local_execution_plan.json

# 3b. 如需覆盖默认行为，可显式指定优先级；all 会包含未标记 priority 的 case
python3 $SKILL_DIR/scripts/case2webe2e.py run-local \
  --case-md test/case.md \
  --case-priority all \
  --confirmed-env \
  --local-case-concurrency 10 \
  --plan-out out/local_execution_plan.json

# 4. 主 agent 优先调用一个执行 subagent，把 local_execution_plan.json / test_report.md 路径交给它；
#    如果当前工具没有 subagent 能力，则主 agent 按同一约束自行执行。
#    由单一执行 agent 用 playwright-cli 做 case 级并发执行，每个 case 一条独立 session：
#      playwright-cli -s=<caseId> open
#      playwright-cli -s=<caseId> goto / snapshot / click / ...
#      playwright-cli -s=<caseId> screenshot test_result/<caseId>/step_001_landing.png  # 入口校验，必须拍
#      ... 业务 flow 中按需补 step_NNN_*.png ...
#      # 失败 / 抛错 / 超时路径：先拍 failure.png 再 close
#      playwright-cli -s=<caseId> screenshot test_result/<caseId>/failure.png   # 仅失败路径
#      playwright-cli -s=<caseId> screenshot test_result/<caseId>/final.png     # 成功 / 失败都要拍
#      playwright-cli -s=<caseId> close
#    截图 / trace / 录像 / console 实时落到 test_result/<caseId>/，final.png 无条件落地

# 5. 执行完成后，将结果补充回 test_report.md
```

## 测试报告 test_report.md

### 默认位置

- 默认写到 `case.md` 同目录，例如 `test/test_report.md`
- 如需改路径，使用 `--report-out`

### 必须写入的内容

1. TTAT 模式：用例组和任务基础信息、本次环境文件路径、当前任务状态说明
2. 本地模式：沿用远程模式相同的 `执行概览` / `任务状态` 主结构；其中 `task_url` 写为本地执行目录路径（默认 `test_result/`），并补充 `execution_mode`、`local_runner`（`playwright-cli`）、`runtime.playwright_cli`（`installed` / `version` / `auto_install_ran`）、`plan_file`、`browser_headers`、每个 case 的本地产物目录；`playwright-cli` 的截图、trace、录像、console log 必须在执行后通过 `-s=<caseId>` 落到 `test_result/<caseId>/`，每个 case 至少包含 `step_001_*.png` 入口截图与 `final.png` 结束截图（失败路径还要 `failure.png`），再把这些实际产物路径和执行结果、关键证据回写到报告
3. `analyze-task` 仅适用于 TTAT 模式，且默认先回写 Overview 到 `test_report.md`
4. 只有用户确认后执行 `--detail`，才继续把详细下钻结果写回 `test_report.md`

### 仅创建用例组

```bash
python3 $SKILL_DIR/scripts/case2webe2e.py create-group \
  --case-md test/case.md \
  --payload-out out/case_group_payload.json
```

## 输出

TTAT 模式执行成功后，脚本会输出：

- `case_group_name`
- `case_count`
- `case_group_id`
- `task_name`
- `task_id`
- `task_url`
- `report_file`

本地模式执行计划生成成功后，脚本会输出：

- `execution_mode`
- `local_runner`（`playwright-cli`）
- `task_url`
- `artifacts_root`
- `runtime.playwright_cli`（`installed` / `version` / `auto_install_ran`）
- `runner_mode`
- `case_count`
- `plan_file`
- `report_file`

## 失败处理

- `case.md` 不存在：直接报错并停止
- `markdown2midscene` 无法解析：保留 `prepare` 能力方便排查返回内容
- 创建用例组失败：输出接口响应并停止
- 创建任务失败：输出接口响应并停止
- 本地模式下 `EXECUTION_MODE` / `LOCAL_RUNNER` 非法：直接报错并停止
- 本地模式下 `playwright-cli` 未安装且用户拒绝一次性安装确认（`npx @tiktok-fe/skills add microsoft/playwright-cli --source github --skill playwright-cli`）：停止执行，提示用户手动安装后重试；不允许回退到任何"模拟执行"或替代工具
