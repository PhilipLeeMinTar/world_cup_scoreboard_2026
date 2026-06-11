# Test Report 断言指南

目标：给定用例配置（`api_test_case.yaml` 或 `api_test_case.md`）与执行日志（`api_mind_{case_id}.log`），生成每个 case 的 Pass/Fail/Skipped/Error 断言结论，并输出可复核的失败原因与证据。

## 1. 输入与映射

- **用例文件**：YAML 或 Markdown 格式，结构为 `test_suite.test_cases[]`，每个用例至少包含：
  - `id`：用例 ID（例如 `TC-G01-06`）
  - `steps[].assert`：断言表达式列表
- **日志文件**：`api_mind_{case_id}.log`
- **映射规则**：对每个 `case_id`，匹配同名日志文件：
  - 找不到日志文件 → `SKIPPED`（用例未执行）
  - 找到 → 进入解析与断言

## 2. 日志结构（必须严格按字段来源理解）

日志按分隔段落组织，断言只依赖下列段落：

- `--- Response: Business (JSON) ---`
  - **业务响应体**，是所有 `jsonpath(...)` 断言的唯一数据源
  - 若内容为空、或为 `N/A` → 视为“业务响应为空”（见 4.5）
- `--- Metadata: Business ---`
  - `Business.StatusCode`：业务请求的 HTTP 状态码（用于 `status_code` 断言）
  - `Business.LogID`：业务日志 ID（如存在）
- `--- Metadata: Gateway ---`
  - `Gateway.HTTPStatusCode`：调用网关的 HTTP 状态码
  - `Gateway.HasPermission`：是否有权限（True/False）
  - `Gateway.ErrorCode`：网关错误码（0 表示无错）
  - `Gateway.LogID`：网关日志 ID（如存在）

以下段落始终存在于日志中，但**不参与**状态判定与断言数据源，仅用于工具调试：

- `--- Runtime: Gateway Request (Curl) ---`
- `--- Runtime: Gateway Response ---`

## 3. 断言表达式（最小语法约定）

断言表达式来自 `steps[].assert`，每条表达式独立求值，全部通过才算断言通过。

### 3.1 LHS（左值）

- `status_code`
  - 取值来源：`Metadata: Business` 的 `Business.StatusCode`
  - ⚠️ **注意**：`Business.StatusCode` 与 `Gateway.HTTPStatusCode` 是两个独立字段，值可能不同。`status_code` 断言**必须**取 `Business.StatusCode`，不能复用 4.1 中已检查的 `Gateway.HTTPStatusCode`。
- `jsonpath('$.path')`
  - 取值来源：`Response: Business (JSON)` 解析后的 JSON
- `typeof(jsonpath('$.path'))`
  - 返回类型字符串：`'int' | 'float' | 'str' | 'bool' | 'array' | 'object' | 'null'`

### 3.2 操作符（仅支持这些）

- 比较：`==`, `!=`, `>`, `>=`, `<`, `<=`
- 集合：`in`, `not in`
- 包含：`contains`, `not contains`
- 字符串匹配：`startswith`, `endswith`
- 逻辑组合：`and`, `or`
- 函数：`len()`, `typeof()`, `exists()`

完整语法说明参见 `test_case_template.md` 第 6 章。

### 3.3 RHS（右值）

- 数字（int/float）：`200`, `3.14`
- 字符串：单引号（`'InvalidArgument'`）
- 布尔：`true` / `false`
- 列表：`[1, 2, 3]`, `['active', 'pending']`
- 空：`null`

## 4. Case 状态判定（3 步短路）

每个日志文件对应一个 case（文件名 `api_mind_{case_id}.log`）
必须严格按以下 3 步顺序检查，任一步失败立刻返回 `FAIL`，不再执行后续步骤：

### 4.1 网关校验
- **取值**：`--- Metadata: Gateway ---` 段落
- 依次检查以下三个字段，任一不通过 → `FAIL`：
  - `Gateway.HTTPStatusCode != 200` → `FAIL`
  - `Gateway.HasPermission != True` → `FAIL`
  - `Gateway.ErrorCode != 0` → `FAIL`

### 4.2 业务响应校验
- **取值**：`--- Metadata: Business ---` 段落中的 `Business.StatusCode`，以及 `--- Response: Business (JSON) ---` 段落的内容

**第一步：检查业务状态码**

⚠️ **关键**：`Gateway.HTTPStatusCode` 和 `Business.StatusCode` 是两个独立字段，值可能不同。例如：`Gateway.HTTPStatusCode = 200`（网关正常），但 `Business.StatusCode = 401`（业务未登录）。`status_code` 断言必须取 `Business.StatusCode`，不能复用 4.1 中已检查的 `Gateway.HTTPStatusCode`。

根据 case.yaml 中 `steps[].request.type` 字段区分：
- `type: "RPC"` → 跳过状态码检查（RPC 无 HTTP 状态码概念），直接进入第二步
- `type: "HTTP"` →
  - 若 case 中**存在** `status_code` 断言（例如 `status_code == 400`）：按断言表达式求值，不通过 → `FAIL`，通过 → 继续（即使 `Business.StatusCode != 200` 也不默认失败）
  - 若 case 中**不存在** `status_code` 断言：若 `Business.StatusCode != 200` → `FAIL`

**第二步：检查响应体是否为空**
- 若第一步中存在 `status_code` 断言且期望值**不是 200**（即预期的错误场景），则**跳过此检查**
- 否则，若 `Response: Business (JSON)` 为空或为 `N/A` → `FAIL`

### 4.3 字段级断言
- **取值**：`--- Response: Business (JSON) ---` 段落解析后的 JSON 对象
- 对除 `status_code` 外的所有断言逐条求值（例如 `jsonpath('$.code') == 'InvalidArgument'`）
- **字段不存在视为失败**：若 `jsonpath('$.field')` 提取的字段在 JSON 中不存在 → 该断言 `FAIL`
  - **注意区分以下三种情况**：
    - 字段不存在（JSON 中无此 key）→ 断言**直接 FAIL**，不论操作符是什么
    - 字段存在，值为 `null` → 正常求值（`== null` 通过，`!= null` 失败）
    - 字段存在，值为空字符串 `""` → 正常求值（`== null` 失败，因为 `""` 不等于 `null`）
  - 如需判断字段是否存在，应使用 `exists()` 函数，而非 `== null`
- 任一不通过 → `FAIL`
- 全部通过 → `PASS`

## 5. 解析错误（ERROR）

以下属于技术错误，返回 `ERROR`（不是 PASS/FAIL）：

- 日志文件无法读取
- `Response: Business (JSON)` 非空且非 `N/A`，但 JSON 解析失败
- `Metadata: Business` 或 `Metadata: Gateway` 缺少必需字段（无法完成 4.1~4.2）

## 6. 输出报告格式（必须严格按此格式生成 test_report.md）

### 6.1 Summary Section

必须包含日期和汇总表格：

```markdown
# Test Execution Report
**Date**: YYYY-MM-DD HH:MM:SS

## Summary
| Total | Passed | Failed | Skipped | Error |
| :---: | :---: | :---: | :---: | :---: |
| {X} | {Y} | {Z} | {S} | {E} |
```

### 6.2 All Cases Section

列出**所有** case（包括 PASS / FAIL / SKIPPED / ERROR），使用表格格式：

```markdown
## All Cases

| Case ID | Status | Log ID | Error Details |
| :--- | :--- | :--- | :--- |
| {case_id} | **{STATUS}** | `{log_id}` (or N/A) | - {Error type}: {message}<br>- Expected `{key}` = `{val}`, got `{actual}` |
```

**字段说明**：
- **Case ID**：用例 ID（来自 case.yaml）
- **Status**：PASS / FAIL / SKIPPED / ERROR（必须加粗 `**{STATUS}**`）
- **Log ID**：**每个用例都必须填写**。从对应的 `api_mind_{case_id}.log` 中提取，优先取 `Business.LogID`，其次 `Gateway.LogID`，都没有则填 `N/A`。**PASS 用例同样需要提取 Log ID，不可省略。**
- **Error Details**：
  - PASS 用例填 `-`
  - FAIL / ERROR 用例用 `<br>` 换行，包含：
    - 失败类型和关键证据（如 `Gateway.HasPermission: False`）
    - 断言失败时：期望值 vs 实际值
  - SKIPPED 用例填 `日志文件未找到`

### 6.3 内部判定字段（用于 thought 过程，不出现在最终报告中）

在生成报告前，模型应内部记录：
- `FailStep`：命中短路的步骤编号（4.1~4.3）
- `GatewayStatusCode`：4.1 中检查的 `Gateway.HTTPStatusCode` 值
- `BusinessStatusCode`：4.2 中检查的 `Business.StatusCode` 值（必须从 `Metadata: Business` 段落重新取值，不能复用 `Gateway.HTTPStatusCode`）
- `Evidence`：直接引用日志中的关键字段
- `AssertionDetails`：断言失败的详细对比

## 7. 强约束（必须遵守）

- 不允许猜测缺失字段；缺失就按规则给出 `ERROR` 或 `FAIL`
- 不允许把 `Runtime: Gateway Response` 当作断言数据源
- `status_code` 断言只对比 `Business.StatusCode`
- 判定结果只能基于断言表达式的求值结果，不允许根据 AI 自身对 API 语义的理解额外判定 `FAIL`（例如：即使响应中 `message` 字段包含 "error"，只要断言列表中没有检查 `$.message`，就不能因此判 `FAIL`）