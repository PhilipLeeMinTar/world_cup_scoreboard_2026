# Test Report 生成指南

目标：基于生成的 Go 测试文件、`triage.yaml` 与 `api_test_logs/execution_result.log` 生成 `test_report.md`。报告必须先用主执行日志判定 case 状态；仅失败 / Error case 才读取对应 `apitest_{case_id}.log` 补充可复核证据、LogID 与服务端日志分析。

## 1. 输入与 case 映射

### 1.1 输入文件

- **测试文件**：`tests/integration/<method_snake>/<method_snake>_test.go`；scenario 用例位于 `tests/integration/scenario/<scenario_snake>/<scenario_snake>_test.go`。
- **用例定义**：每个 case id 对应 `case.md` 的一个 `### [TC-xxx]` block。
- **分类数据**：`FEATURE_DIR/test/triage.yaml`，用于覆盖矩阵、来源列与老用例失败识别。
- **日志目录**：`<specDir>/api_test_logs/`（即 `FEATURE_DIR/test/api_test_logs/`），由 `apitest.NewContextFromSpec(t, specDir())` 固定写入；不要读取 `APITEST_LOG_DIR`。
- **主执行日志**：`execution_result.log`，保存 execute 阶段 `GOTOOLCHAIN=auto GOWORK=off go test -v -count=1 -run ...` 的 stdout/stderr。
- **细粒度日志**：`apitest_{case_id}.log`，method 与 scenario 共用根目录，case id 在仓库范围内必须唯一；只在失败 / Error case 中读取。

### 1.2 case id 与 go test 名称映射

1. 优先从 `WithCaseID("<id>")` 提取 case id；兼容存量 helper 包装（如 `newContext(t, "<id>")`，见 `reuse_amend_guide.md §2.3`）。
2. 建立 `case_id -> TestName[/SubtestName]`：
   - 普通模板：`WithCaseID` 所在 `func TestXxx(t *testing.T)` 对应 `execution_result.log` 中的 `TestXxx`。
   - `t.Run` / runtime `Case` 多步骤形态：把 subtest 名纳入匹配路径，如 `TestXxx/StepName`。
3. 不要求 `go test -v` 输出 case id；case id 仅用于报告与细粒度日志文件名。

### 1.3 主日志优先状态映射

- 匹配到 PASS → `PASS`，不读取 `apitest_{case_id}.log`。
- 匹配到 FAIL → `FAIL`，读取对应细粒度日志提取失败证据。
- 测试进程级失败但无法定位 case → `ERROR`，证据来自 `execution_result.log` 的编译 / panic / setup 摘要。
- `execution_result.log` 不存在或不可读 → `ERROR`。
- `execution_result.log` 存在但 case 无运行记录 → `SKIPPED`。

## 2. 细粒度日志字段来源

`apitest_{case_id}.log` 分段解析，仅下列段落参与断言或失败证据：

| 段落 | 字段 / 用途 |
| --- | --- |
| `--- Response: Business (JSON) ---` | 业务响应体；所有 `jsonpath(...)` 断言的唯一数据源。空或 `N/A` 视为业务响应为空。 |
| `--- Metadata: Business ---` | `Business.StatusCode` 用于 `status_code`；`Business.LogID` 用于日志分析。 |
| `--- Metadata: Gateway ---` | `Gateway.HTTPStatusCode`、`Gateway.HasPermission`、`Gateway.ErrorCode`、`Gateway.LogID`。 |

以下段落只作排障上下文，不参与状态判定，也不能作为断言数据源：

- `--- Runtime: Gateway Request (Curl) ---`
- `--- Runtime: Gateway Response ---`

## 3. 断言表达式

断言来自 `apitest.Assert(...)`，逐条独立求值，全部通过才算断言通过。

### 3.1 LHS

| 表达式 | 取值规则 |
| --- | --- |
| `status_code` | `Business.StatusCode` |
| `jsonpath('$.path')` | 从 `Response: Business (JSON)` 解析 JSON 后提取 |
| `len(jsonpath('$.path'))` / `len($.path)` | 对提取到的数组或字符串求长度 |
| `typeof(jsonpath('$.path'))` | 返回 `'int'|'float'|'string'|'boolean'|'list'|'dict'|'null'` |

### 3.2 操作符与 RHS

- 操作符：`==`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `contains`。
- `in` 的 RHS 必须为列表；`contains` 的 LHS 必须为字符串。
- RHS 支持数字、单引号字符串、`true` / `false`、列表、`null`。

## 4. Case 状态判定

先按 §1.3 处理主执行日志。仅当 case 明确 FAIL 时，按以下顺序解析细粒度日志；任一步失败立即短路返回，不再执行后续步骤。

1. **网关 HTTP**：`Gateway.HTTPStatusCode != 200` → `FAIL`。
2. **权限**：`Gateway.HasPermission != True` → `FAIL`。
3. **网关错误码**：`Gateway.ErrorCode != 0` → `FAIL`。
4. **业务状态码**：
   - `apitest.CallRPC(...)`：跳过本步。
   - `apitest.CallHTTP(...)` 且存在 `status_code ...` 断言：只校验该断言；通过后继续，不能因 `Business.StatusCode != 200` 默认失败。
   - `apitest.CallHTTP(...)` 且不存在 `status_code` 断言：`Business.StatusCode != 200` → `FAIL`。
5. **业务响应为空**：`Response: Business (JSON)` 为空或 `N/A` → `FAIL`。
6. **字段级断言**：除 `status_code` 外逐条求值；字段不存在视为断言失败；任一不通过 → `FAIL`，全部通过 → `PASS`。

## 5. ERROR 场景

以下属于技术错误，返回 `ERROR` 而不是 `FAIL`：

- `execution_result.log` 或失败 case 的细粒度日志不可读。
- `Response: Business (JSON)` 非空且非 `N/A`，但 JSON 解析失败。
- 失败 case 的 `Metadata: Business` 或 `Metadata: Gateway` 缺少完成 §4 判定所需字段。

## 6. 报告输出格式

`test_report.md` 必须按以下顺序输出章节：

```markdown
# 测试执行报告
**执行时间**：YYYY-MM-DD HH:MM:SS

## 用例来源汇总
## 执行概况
## 结果详情
## Mock 配置        <!-- 条件输出：仅当 Bytemock reconcile 运行 -->
## 老用例失败（待修） <!-- 条件输出：仅当存在老用例失败 -->
```

### 6.1 用例来源汇总

数据源：`triage.yaml` 的 `decision` / `classification` / `changes` / `existing_case_ids` + `execution_result.log`。本节必须位于执行概况之前。

```markdown
## 用例来源汇总

| 接口 | 分类 | 复用 | 修改 | 新增 | 老用例失败（待修） |
| :--- | :--- | :---: | :---: | :---: | :---: |
| GetAllPolicyGroupMeta | case-only | 1 | 0 | 0 | 0 |
| SearchBank | idl-changed | 4 | 1 | 1 | 1 ← TC-G02-04 失败，根因：IDL 改名（详见“老用例失败”） |
| ListEnforcementRule | new-method | 0 | 0 | 3 | - |
| **合计** | — | **5** | **1** | **4** | **1** |
```

列口径：

- **接口**：`triage.yaml.<method>` 对应方法名。
- **分类**：`triage.yaml.<method>.classification`。
- **复用**：`decision == reuse` 时，统计 `existing_case_ids` 中所有仍执行的 existing case。
- **修改**：`decision == amend` 时，统计 `changes[].target_case_id` 去重数量；`kind == add_case` 不计入。
- **新增**：`decision == new` 的全部 case + `decision == amend` 且 `kind == add_case` 的 case。
- **老用例失败（待修）**：仅对 `decision ∈ {reuse, amend}` 统计执行结果 FAIL 且 case id 属于 `existing_case_ids`、并且不是本次新增 case 的存量用例。

老用例失败处置：

- `decision == reuse` 的失败：不阻塞本需求，但必须建议单独起 issue。
- `decision == amend` 中不在 `changes` 内的 case 失败：视为本需求回归，计入执行概况失败，不算老用例待修。
- `decision == amend` 中在 `changes` 内的 case 失败：常规失败处理，根因标注“补丁不充分”或“补丁错误”。

### 6.2 执行概况

```markdown
## 执行概况

| 总数 | 通过 | 失败 | 跳过 | 错误 |
| :---: | :---: | :---: | :---: | :---: |
| {X} | {Y} | {Z} | {S} | {E} |
```

`失败` 计数不与“老用例失败（待修）”重复：一条 case 要么按 §6.1 计为老用例待修，要么计入本节失败。

### 6.3 结果详情

列出所有 case（PASS / FAIL / SKIPPED / ERROR）：

```markdown
## 结果详情

| 状态 | 用例ID | 标题 | 接口 | 用例位置 | 来源 | 依赖Mock | 日志ID | 失败原因 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ✅ **PASS** | {case_id} | {case_title} | {METHOD} {path} 或 RPC {method_name} | {repo_relative_test_path} | {source_cell} | {mock_cell} | `N/A` | - |
```

字段规则：

- **状态**：`✅ **PASS**` / `❌ **FAIL**` / `⏭️ **SKIP**` / `⚠️ **ERROR**`。
- **用例ID**：从 `WithCaseID("<id>")` 或兼容 helper 提取。
- **标题**：取 `case.md` 中 `### [TC-xxx] ...` 标题；scenario 用例填 scenario 名。
- **接口**：HTTP 写 `<METHOD> <path>`；RPC 写 `RPC <method_name>`。
- **用例位置**：相对仓库根目录的 `*_test.go` 路径，来自 `triage.yaml.targets[].target_path` / `existing_path`。
- **来源**：`new`、`reuse·base`、`reuse·worktree`、`amend·base`、`amend·worktree`。`amend` target 中 `kind == add_case` 的新增 case 填 `new`。
- **依赖Mock**：
  - `否`：该 case 无 Mock Setup。
  - `是 [<rule_id>](<mock_rule_url>)`：mock-required 且 Bytemock reconcile 成功。
  - `跳过（<reason>）`：mock-required 但 reconcile 失败 / 工具缺失；该 case 状态应为 SKIPPED。
- **日志ID**：PASS / SKIPPED 不读细粒度日志，填 `N/A`；FAIL / ERROR 优先 `Business.LogID`，其次 `Gateway.LogID`，均无则 `N/A`。
- **失败原因**：
  - PASS：`-`（可附 mock 命中对照说明，不强制）。
  - SKIPPED：`execution_result.log 无该 case 运行记录` 或 mock 跳过原因。
  - FAIL / ERROR：用 `<br>` 换行，包含失败类型与关键证据、断言期望 vs 实际、失败分类、服务日志分析。

失败分类只能取：`test_contract_error`（测试契约，可自动修复）、`env_data_error`、`product_behavior_error`、`unknown`。

### 6.4 Mock 配置（条件输出）

当本次包含 Mock Setup 且 Bytemock reconcile 实际运行时输出：

```markdown
## Mock 配置

| 用例ID | 协议 | 下游PSM | 下游方法 | 规则 | 过滤器 | 动作 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| {case_id} | {RPC/HTTP} | `{callee_psm}` | `{method}` | [{rule_name}]({mock_rule_url}) | `{filter}` | {created/updated/reused/skipped} |
```

- `规则` 列必须用文本 + 超链接，不直接展开长 URL。
- `mock_rule_url` 来自 `mock.md §3.6`，并且必须与 §6.3“依赖Mock”列指向同一 BAM rule。
- 跳过的 mock setup 仍需写明原因与修复建议。

### 6.5 老用例失败（待修）（条件输出）

仅当 §6.1 “老用例失败（待修）”列 > 0 时输出：

```markdown
## 老用例失败（待修）

| 接口 | 用例ID | 根因猜测 | 建议修复 |
| :--- | :--- | :--- | :--- |
| SearchBank | TC-G02-04 | IDL 字段 `Bizlines` 改名为 `BusinessLines` | 单独提 issue 更新该 case Body，或将 method 从 reuse 升级到 amend |
```

根因猜测只按“IDL 改名 / handler 行为变 / 数据漂移 / 环境差异”粗分；不能确定填“待人工排查”。

## 7. 内部判定字段与自动修复边界

生成报告前可在 thought / 中间结构中记录，但不要输出到最终报告：

- `FailStep`：命中短路的步骤编号（§4.1~§4.6）。
- `Evidence`：PASS / SKIPPED 引用 `execution_result.log`；FAIL / ERROR 可补充细粒度日志关键字段。
- `AssertionDetails`：断言失败对比。
- `FailureCategory`：`test_contract_error` / `env_data_error` / `product_behavior_error` / `unknown`。
- `ServerLogAnalysis`：基于 LogID 调 `bam-cli api-test --act analyze-result` 后提取的“问题分析结论”；未查询或失败写 `skipped (<reason>)`。

自动修复只允许作用于 `test_contract_error`，且只修生成 / 补丁过的 `*_test.go`。严禁为通过测试而削弱业务断言、删除失败断言、把 expected 改成 actual，或因疑似产品行为问题修改用例。

## 8. 强约束

- 报告生成必须优先读取 `execution_result.log`；只有失败 / Error case 才允许读取对应 `apitest_{case_id}.log`。
- 不允许猜测缺失字段；缺失就按规则给出 `ERROR` 或 `FAIL`。
- 不允许把 `Runtime: Gateway Response` 当作断言数据源。
- `status_code` 断言只对比 `Business.StatusCode`。
- §6.1 的复用 / 修改 / 新增列必须等于 `triage.yaml` 推导值。
- “老用例失败（待修）”与 §6.2 的 `失败` 计数互不重叠。
- §6.3“依赖Mock”列与 §6.4“Mock 配置”的 `mock_rule_url` 必须一致。
