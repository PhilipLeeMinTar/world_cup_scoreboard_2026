# go_driver generate

本文件仅在 Go `generate` 阶段读取，负责前置检查、上下文收集、runtime 同步、用例分流与代码生成。

## 0. 前置门禁检查

上层 SKILL 必须已完成：

- `apimind-metrics start generate` 成功返回
- 5 个公共字段已写入 `<工作目录>/.api-mind/metrics.json`

防御性校验：如果 `metrics.json` 不存在，或缺少 `start_time`，立即中断并报告“埋点未就绪”。

## 1. case.md 前置校验

准入不通过不得进入后续步骤：

1. 文件存在性：`case_file` 不存在时终止 generate，并提示先调用 `prd2case-api` 生成测试用例。
2. 脚本扫描（优先，避免全文读 case.md）：执行
   ```bash
   python3 <SKILL_DIR>/go_driver/scripts/scan_case.py --case-file <case_file> --json --compact
   ```
   脚本一次性返回三类确定性清单：
   - `unresolved_items[]`：`[tt-nova-datagen]` / `[USER_INPUT_REQUIRED: ...]` / `[Manual Prompt]` 命中及行号。
   - `secret_runtime_hits[]`：Cookie / Hex-Auth-Key / Authorization / JWT 等鉴权变量命中及行号。
   - `case_headers[]`：默认只包含**存在非鉴权 header 的 case 清单**（`{case_id, non_auth_headers:[{key,value,line}]}`），并附 `non_auth_header_count` / `has_non_auth_headers`；`case_headers_omitted_empty` 仅表示被压缩省略的空 header case 数。该清单是后续 §3.3 Headers 生成与 §5.9 自检的**唯一权威来源**——非鉴权 header 必须照此清单逐项生成，**不得**改为凭记忆通读 case.md。

   仅在脚本对 `unresolved_items` / `secret_runtime_hits` 有命中时，才按行号定向读取 case.md 局部片段。`case_headers` 已是结构化清单，直接使用即可；未出现在压缩清单中的 case 视为无非鉴权 header。
3. 用户确认：`has_unresolved` 为真时，通过 `AskUserQuestion` 提供“补充参数”或“全部跳过”。选择跳过时记录 `skip_list`，对应字段使用零值，并在赋值行上方插入 TODO 注释。
4. SecretRuntime 校验：`has_secret_runtime` 为真时，将 `secret_runtime_hits` 写入 `state.json.warnings[]`，不阻塞 generate；Execute 阶段再按风险门禁拦截。

## 2. runtime 同步

在生成 / 修改测试代码前只做三件事：

1. 在仓库根目录执行 `GOWORK=off go list -m`，确认 Go Module 并记录模块路径。
2. 调用脚本同步 skill 内置 runtime，禁止手读 / 手改 `manifest.json` 哈希清单：
   ```bash
   python3 <SKILL_DIR>/go_driver/scripts/sync_runtime.py sync \
     --dest <REPO_ROOT>/tests/integration/apitest --json --trust-version
   ```
   只消费脚本 JSON 的 `status`、`synced[]`、`extra[]`、`replaced_skip[]`、`trusted_version`；`extra[]` 仅记录告警，不阻塞；`status=error` 才中断。`trusted_version=true` 表示目标 `manifest.json.version` 匹配且托管文件存在，脚本已跳过逐文件 sha256 热路径校验；如用户怀疑仓库内 runtime 被手改，才去掉 `--trust-version` 做全量校验。
3. runtime 编译检查采用**按需执行**：当 `sync_runtime.py` 返回 `status=synced` / `needs-sync` / `version-mismatch`，或目标 runtime 首次创建 / 本轮修改过 runtime 文件时，执行 `GOWORK=off go test -run '^NoMatch$' -count=1 ./tests/integration/apitest/`；当 `status=up-to-date` 且 `trusted_version=true` 时，跳过该 runtime-only 编译检查，依赖后续目标 package 编译检查覆盖 runtime 可用性，避免每次 generate 都重复编译 runtime 包。

## 3. 上下文解析

1. 读取 `case_file`，关联获取 `spec.md` 与 `test/task.md`。
2. 按 `prd2case-api/resources/api_test_template.md` 的 block 结构解析：`### [TC-xxx]` 为 case 边界，`**Step N:**` 为步骤边界，`API Contract` / `Protocol` / `Request Parameters` / `Assertions` / `Variable Extraction` 为字段来源。不要按旧版 row/column 表格解析。
3. `Request Parameters` 必须严格分流：
   - `Headers` → **仅能进入 `apitest.HTTPRequest.Headers`**。`case.md` 中 HTTP 请求的 `Headers` 是被测业务接口的 header 参数（下游业务请求头），不是 paas-gw / AGW 外层请求头，也不是 `.env` 路由字段、`RpcContext`、query/path/body 参数。Headers 分两类处理，缺一不可：
     - **鉴权 header**（`secret_runtime_hits` 命中的，如 Cookie / Hex-Auth-Key / Authorization）→ 写入 `<specDir>/auth.yaml` profile，Go 代码通过 `ctx.AuthHeaders()` / `ctx.AuthHeadersFor(...)` 注入，**不得**内联到 `*_test.go`。
     - **非鉴权 header**（来自 `scan_case.py` 的 `case_headers[].non_auth_headers`，如 `Content-Type` / `X-Device-Type` / `X-Trace-Id`）→ **必须**对该 case 清单中的每一项，先构造本地 `map`、逐项叠加、再整体赋给 `Headers`：`h := ctx.AuthHeaders(); h["Content-Type"] = "application/json"; h["X-Device-Type"] = "iOS"; req.Headers = h`。**只要该 case 的 `non_auth_headers` 非空，就禁止直接写 `Headers: ctx.AuthHeaders()`**（那样会丢掉非鉴权 header）。仅当某 case 的 `non_auth_headers` 为空时才允许直接用 `ctx.AuthHeaders()`。
   - `Query Parameters` → `HTTPRequest.Params: map[string]string{...}`。
   - `Body Parameters` → `HTTPRequest.Body` / `RPCRequest.Body` 的 `apitest.JSON{...}`。
   - `Path Parameters` → 拼接到 `HTTPRequest.Path` 模板。
4. Headers 跨 case 差异检测：鉴权一致写入 `profiles.default`；鉴权有差异时拆分 profile，并在 `auth.yaml.case_profiles` 显式映射 `case_id → profile_name`。
5. 生成 `<specDir>/.env`（路由，来自 `task.md`）和 `<specDir>/auth.yaml`（业务鉴权 profile，来自 case.md Headers + 用户补充），schema 见 `../resources/env_template.md`。

## 4. 用例分流

进入 Reuse / Amend / New 决策时读取 `decision.md` 与 `../resources/reuse_amend_guide.md`，生成 / 更新 `triage.yaml`。

## 5. 代码生成与校验

1. 载荷构造：严格区分 explicit / resource_ref / dynamic_construct / env_business_sample 字段；不得随意传假 ID 或 `[0]`。
2. 变量转换：`case.md` 中 `{{VAR}}` 在 Body 中按类型转换为 `${{var}}` 或 Go 变量；URL / path / header / query 使用 `${var}` 或字符串变量；不得把 `{{VAR}}` 原样写入 Go 代码。
3. `specDir` 计算：用 `filepath.Rel` 计算 `<REPO_ROOT>/tests/integration/<METHOD_SNAKE>/` 到 `FEATURE_DIR/test/` 的相对路径，注入 `specDir()`。
4. 断言归一化：支持 `status_code`、`$.path`、`len($.path)`、`typeof($.path)`；操作符限 `==` / `!=` / `>` / `>=` / `<` / `<=` / `in` / `contains`。将 `StatusCode` 改为 `status_code`，`.length` 改为 `len(...)`，`IS NOT NULL` 改为 `!= null`；不要生成未被 runtime 支持的 `matches`。
5. Mock 注入：若包含 Bytemock 配置，按需读取 `../../mock.md` 的 Mock Setup / dry-run / metainfo 注入规则。
6. 代码落地：遵循 `../resources/go_test_template.md`，同步落地 `.env` 与 `auth.yaml`；`case_profiles` 引用的 profile 必须真实存在。Headers 数据流强约束：
   - 鉴权 header（`Cookie` / `Authorization` / `Hex-Auth-Key` 等）必须经 `ctx.AuthHeaders()` / `auth.yaml` 注入，不得内联。
   - **非鉴权 header 必须以 `scan_case.py` 的 `case_headers[]` 为生成驱动**：为每个 `case_id` 取其 `non_auth_headers`，对其中**每一项** `{key, value}` 在该 case 的测试函数里生成一行 `h["<key>"] = "<value>"` 叠加（先 `h := ctx.AuthHeaders()`，最后 `req.Headers = h`）。生成时即逐项核对，不要凭记忆通读 case.md。
   - 任意 HTTP header key 都不得被生成为 gateway 外层 header、`.env` 字段、`RpcContext`、`Params` 或 `Body`。
7. 编译检查：执行 `GOWORK=off go test -run '^NoMatch$' -count=1 <package>`；编译错误最多修复 3 次。若本轮生成 / 修改了多个 package，优先合并成一次 `go test -run '^NoMatch$' -count=1 <pkg1> <pkg2> ...`，避免逐包重复启动 Go toolchain。
8. 生成自检与非鉴权 Header 自检优先使用**单次脚本 / 单次搜索**完成：对本次生成 / 修改的 `*_test.go` 文件一次性扫描 `{{` 残留和 `scan_case.py` 返回的 `case_headers[].non_auth_headers[].key`。禁止对每个 header key 各执行一次 `grep`，避免 header 多时产生 O(N) shell 调用。任一 key 缺失即视为遗漏，必须补齐叠加语句后重新编译，全部命中才返回成功。本步骤以脚本清单为权威对照源，**禁止**改回“重新通读 case.md 凭记忆补 header”。

## 6. 埋点业务字段

完成代码生成后，直接写入本阶段内存记录的：

- `knowledge_base_read`
- `knowledge_base_used`

不得在生成结束后为了 metrics 回溯本轮读取历史、重新打开知识库或扫描文档；若本阶段未读取外部领域知识库，两个字段均写 `0`。

## 7. 生成后强制检查清单

generate 阶段结束前，**必须逐项确认**以下步骤全部完成，缺一不可：

- [ ] 已在生成过程中同步维护外部领域知识库读取 / 使用的内存布尔值（`knowledge_base_read_seen`、`knowledge_base_used_seen`）
- [ ] 已将本阶段内存值写入 `<工作目录>/.api-mind/metrics.json` 的 `knowledge_base_read`、`knowledge_base_used` 字段
- [ ] `metrics.json` 中 `knowledge_base_read`、`knowledge_base_used` 均为 `0` 或 `1`，且未因埋点回溯读取历史、重新打开知识库或扫描文档
- [ ] 已执行 `apimind-metrics end generate --workdir <工作目录>/.api-mind --jwt "<会话内存 JWT>"`，并确认埋点上报成功；若失败按 metrics end 失败策略处理，不得跳过上报动作
