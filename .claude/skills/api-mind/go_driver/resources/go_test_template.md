# Go Test File Template

This template is the **canonical shape** for the `*_test.go` files emitted by the api-mind skill.

It runs against the in-repo `apitest` Go runtime (`{{APITEST_IMPORT_PATH}}`, resolved by `go list -m` + `/tests/integration/apitest`), which sends requests through `paas-gw`. Execute captures `go test -v` stdout/stderr to `api_test_logs/execution_result.log` for report generation; the runtime also writes per-case `apitest_<case_id>.log` files, which reports may read only for failed / Error cases.

## 1. File Location

```
<REPO_ROOT>/tests/integration/<METHOD_SNAKE_CASE>/<METHOD_SNAKE_CASE>_test.go
```

- One file per **target method** (HTTP path or RPC func).
- Package name: `<METHOD_SNAKE_CASE>_test`.
- Test func name: `Test<MethodPascalCase>`.

## 2. Skeleton

The generated style intentionally follows Tesla-Go's readable shape:
`TestXxx(t)` → context → request → call → assert.

`{{REQUEST_TYPE}}` is `HTTP` or `RPC`, chosen per the target interface type. `{{REQUEST_METHOD_FIELD}}` expands differently for each:

| `{{REQUEST_TYPE}}` | `{{REQUEST_METHOD_FIELD}}` expansion | Example |
|---|---|---|
| `HTTP` | `Method: "<VERB>",`<br>`Path: "<path>",` | `Method: "POST",`<br>`Path: "/api/v2/example/detail",` |
| `RPC` | `Method: "<RPCFuncName>",` | `Method: "SearchBank",` |

Every generated test file embeds a package-level `specDir()` helper that resolves the absolute path to `FEATURE_DIR/test/` purely from the test source file location (`runtime.Caller(0)`), so the file works for anyone who clones the repository — **no `APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR` env vars are read or supported**. Only `APITEST_TOKEN` (paas-gw JWT) is expected at run time.

`{{SPEC_DIR_REL}}` is the relative path from the test file's directory (`<REPO_ROOT>/tests/integration/<METHOD_SNAKE>/`) up to `FEATURE_DIR/test/`. The skill computes it once during Generate using `filepath.Rel` and bakes it into the file.

```go
package {{METHOD_SNAKE}}_test

import (
	"path/filepath"
	"runtime"
	"testing"

	"{{APITEST_IMPORT_PATH}}"
)

// specDir returns the absolute path to FEATURE_DIR/test/, resolved purely from
// the location of this generated source file. Anyone who pulls the repo can run
// `go test` directly — no path-related env vars are required.
func specDir() string {
	_, thisFile, _, _ := runtime.Caller(0)
	return filepath.Join(filepath.Dir(thisFile), "{{SPEC_DIR_REL}}")
}

func Test{{METHOD_PASCAL}}(t *testing.T) {
	ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("{{CASE_ID}}")
	// Non-sensitive headers (Content-Type, X-Trace-Id, etc.) layer on top of auth.
	// Source of truth = scan_case.py `case_headers[].non_auth_headers` for THIS case_id.
	// If that list is non-empty you MUST build a local map and add every entry:
	//   h := ctx.AuthHeaders()
	//   h["Content-Type"] = "application/json"   // one line per non_auth_headers entry
	//   Headers: h,
	// Direct `Headers: ctx.AuthHeaders()` is ONLY allowed when this case has zero
	// non-sensitive headers — otherwise those headers get silently dropped.
	req := apitest.{{REQUEST_TYPE}}Request{
		{{REQUEST_METHOD_FIELD}}
		Headers: ctx.AuthHeaders(),
		Body: apitest.JSON{
			// Built per SKILL.md §2.2 request data construction strategy.
		},
		Extract: map[string]string{
			// "var_name": "$.jsonpath",   // only when case.md has Extract column
		},
	}

	resp := apitest.Call{{REQUEST_TYPE}}(ctx, req)

	// Use extracted values in subsequent steps (multi-step scenarios):
	// val := resp.ExtractString("var_name")
	// num := resp.ExtractInt64("var_name")

	apitest.Assert(t, resp,
		"status_code == 200",
		"$.code == 0",             // HTTP: AGW {code, data, message} wrapper
		// RPC: "$.BaseResp.StatusCode == 0",   // RPC: raw IDL response
	)
}
```

## 3. Per-Case Block (one per `case.md` TC block)

> **CRITICAL — HTTP vs RPC 响应结构差异**:
> - **HTTP**: paas-gw 经 AGW (Janus Mini) 转发，业务响应被包裹为 `{"code": N, "data": {...}, "message": "..."}`。断言使用 `$.code == 0`，业务字段加 `$.data.` 前缀。网关始终返回 HTTP 200，负向测试用 `$.code != 0` 判断业务错误。
> - **RPC**: 直连服务，响应保持原始 IDL 结构。断言使用 `$.BaseResp.StatusCode == 0`，业务字段不加前缀。

For every `### [TC-xxx]` test case block in `case.md` emit one ordinary `TestXxx(t)` function. Add a
one-line comment immediately above each generated test function in the format
`// TC-xxx: <case.md test scenario>` so reviewers can understand the case intent without
opening `case.md`. Keep the body flat: build request, call gateway, then assert.
Multi-step scenarios use multiple `CallHTTP` / `CallRPC` calls and explicit Go variables.

**HTTP example:**

```go
h := ctx.AuthHeaders()
h["Content-Type"] = "application/json" // from case.md Request Parameters → Headers

resp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
	Method:  "GET",
	Path:    "/api/v2/example/detail",
	Headers: h,
	Params: map[string]string{
		"id": id,
	},
})
apitest.Assert(t, resp, "status_code == 200", "$.code == 0")
```

`case.md` HTTP `Request Parameters → Headers` are **business request headers**. They must flow through `apitest.HTTPRequest.Headers` only; never generate separate gateway / AGW outer-header arguments for them.

**RPC example:**

```go
resp := apitest.CallRPC(ctx, apitest.RPCRequest{
	Method:  "SearchBank",
	Headers: ctx.AuthHeaders(),
	Body:    apitest.JSON{"Bizlines": []string{"tiktok-photo"}},
})
apitest.Assert(t, resp, "$.BaseResp.StatusCode == 0")
```

**Multi-step scenario with Extract:**

```go
// Step 1: create resource
createResp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
	Method:  "POST",
	Path:    "/api/v2/example/resource",
	Headers: ctx.AuthHeaders(),
	Body:    apitest.JSON{"name": apitest.UniqueName("test")},
	Extract: map[string]string{
		"resource_id": "$.data.id",
	},
})
apitest.Assert(t, createResp, "status_code == 200", "$.code == 0")

// Step 2: query by extracted id
id := createResp.ExtractString("resource_id")
queryResp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
	Method:  "GET",
	Path:    "/api/v2/example/resource/detail",
	Headers: ctx.AuthHeaders(),
	Params:  map[string]string{"id": id},
})
apitest.Assert(t, queryResp, "status_code == 200", "$.data.name != ''")
```

### Conditional Assertions ([High-Volatility] fields)

Fields marked `[High-Volatility]` in `case.md` use conditional assertion syntax:

```
IF $.path EXISTS THEN $.path <operator> <expected>
```

These fields are optional or conditional — the assertion only checks when the field exists. When the field is absent, the test must not fail.

**Code generation rules:**

1. **Parse**: extract `$.path` and the assertion expression after `THEN` from the `case.md` assertion line.
2. **Existence check**: use `resp.ExtractString("$.path")` — returns empty string `""` when the field is missing, `null`, or the path doesn't match.
3. **Wrap assertion**: place `apitest.Assert` inside a Go `if` block. Put the existence check and assertion in the same block for readability.

**HTTP example:**

```go
// [High-Volatility] IF $.data.promotion_tag EXISTS THEN $.data.promotion_tag in ["HOT","NEW","SALE"]
if tag := resp.ExtractString("$.data.promotion_tag"); tag != "" {
    apitest.Assert(t, resp, `$.data.promotion_tag in ["HOT","NEW","SALE"]`)
}
```

**RPC example:**

```go
// [High-Volatility] IF $.orderInfo.ExpireAt EXISTS THEN $.orderInfo.ExpireAt > 0
if expireAt := resp.ExtractString("$.orderInfo.ExpireAt"); expireAt != "" {
    apitest.Assert(t, resp, "$.orderInfo.ExpireAt > 0")
}
```

**Multi-field conditional assertions:**

```go
// [High-Volatility] IF $.data.items[0].stock EXISTS THEN $.data.items[0].stock >= 0
// [High-Volatility] IF $.data.items[0].cover_url EXISTS THEN $.data.items[0].cover_url != ""
if stock := resp.ExtractString("$.data.items[0].stock"); stock != "" {
    apitest.Assert(t, resp, "$.data.items[0].stock >= 0")
}
if url := resp.ExtractString("$.data.items[0].cover_url"); url != "" {
    apitest.Assert(t, resp, `$.data.items[0].cover_url != ""`)
}
```

**Type-specific existence checks:**

| case.md expression | Go check pattern | Notes |
|---|---|---|
| `IF $.x EXISTS THEN...` | `if v := resp.ExtractString("$.x"); v != "" { ... }` | Returns empty string when field is missing/null |
| `IF $.x != null THEN...` | Same as above | JSON null value is extracted as empty string |
| `IF $.x EXISTS AND $.x > 0 THEN...` | `if v := resp.ExtractInt64("$.x"); v > 0 { ... }` | Zero value means not present; check business condition directly |
| `IF $.x EXISTS AND $.x != '' THEN...` | `if v := resp.ExtractString("$.x"); v != "" { ... }` | Empty string means not present |

**Hard constraints:**

- Conditional assertions must NOT be placed in unconditional `apitest.Assert(t, resp, ...)` calls. They must reside in separate `if` blocks.
- When the field is absent, the test must PASS (not FAIL), because this is expected behavior.
- The original `[High-Volatility]` comment line from `case.md` must be preserved above conditional assertions for traceability.

## 4. Field-by-Field Mapping (case.md → template tokens)

| case.md / task.md / IDL field | Template token | Notes |
| --- | --- | --- |
| Interface type (HTTP path vs RPC func) | `{{REQUEST_TYPE}}` | `HTTP` when `case.md` specifies an HTTP path; `RPC` when it specifies an RPC method name. Drives `HTTPRequest`/`RPCRequest` and `CallHTTP`/`CallRPC`. |
| HTTP method + path | `Method: "<VERB>",` `Path: "<path>",` | Only for `{{REQUEST_TYPE}} == HTTP`. `<VERB>` is GET/POST/PUT/DELETE; `<path>` is the API path (e.g. `/api/v2/example/detail`). |
| RPC method name | `Method: "<RPCFuncName>",` | Only for `{{REQUEST_TYPE}} == RPC`. `<RPCFuncName>` is the PascalCase RPC function name (e.g. `SearchBank`). No `Path` or `Params` fields. |
| Method name (derived) | `{{METHOD_NAME}}`, `{{METHOD_PASCAL}}`, `{{METHOD_SNAKE}}` | Snake → file path; Pascal → Go func name |
| Go module import path | `{{APITEST_IMPORT_PATH}}` | Resolve once with `go list -m`, then append `/tests/integration/apitest`; never hardcode the current repository path. |
| Spec directory relative path | `{{SPEC_DIR_REL}}` | The `filepath.Rel` result from `<REPO_ROOT>/tests/integration/<METHOD_SNAKE>/` to `FEATURE_DIR/test/`. Baked into the `specDir()` helper at generation time so the test resolves `.env` / `auth.yaml` / log dir purely from disk layout, with zero path env vars. |
| Env routing (`psm/host/env/branch/zone/idc/cluster`) | `<specDir>/.env` | Generated Go calls `apitest.NewContextFromSpec(t, specDir())`, which loads `<specDir>/.env`. Single-PSM cases may use legacy flat fields; multi-PSM cases must use `services.<service_key>` bindings plus `default_service`. Must not inline these fields anywhere else. |
| Service selector | `HTTPRequest.Service` / `RPCRequest.Service` | Optional service key from `<specDir>/.env services`. Omit only for the default service. For every request targeting a non-default PSM, emit `Service: "<service_key>"`. |
| **CRITICAL**: `Request Parameters → Headers` sub-section (HTTP headers like `Hex-Auth-Key`, `Cookie`, `Authorization`, `Content-Type`, `X-*`, etc.) | `Headers: ctx.AuthHeaders()` / `Headers: ctx.AuthHeadersFor("<profile>")` / `Headers: h` where `h` is a local map merged from `ctx.AuthHeaders()` plus literal non-sensitive headers | **HTTPRequest only, and always as downstream business headers.** These headers must not be emitted as paas-gw / AGW outer headers, gateway parameters, `.env` fields, `RpcContext`, `Params`, `Path`, or `Body`. Business auth headers live in `<specDir>/auth.yaml` profiles (see `env_template.md`). **Non-sensitive headers are driven by `scan_case.py`'s `case_headers[].non_auth_headers` for this case_id**: when that list is non-empty you MUST emit `h := ctx.AuthHeaders(); h["<key>"] = "<value>"` for EVERY entry and assign `Headers: h` — `Headers: ctx.AuthHeaders()` alone is forbidden because it drops them. Use bare `ctx.AuthHeaders()` only when the case's `non_auth_headers` is empty; omit `Headers` entirely only when the case has zero headers and zero auth requirement. |
| **CRITICAL**: `Request Parameters → Query Parameters` sub-section | `Params: map[string]string{...}` | Only in `HTTPRequest`. Appended to the URL as query string. RPC requests do NOT support query params. |
| **CRITICAL**: `Request Parameters → Body Parameters` sub-section (JSON body, form body, etc.) | `Body: apitest.JSON{...}` | For both HTTP and RPC. `{{VAR}}` placeholders in the body must be converted to `${{var}}` (type-preserving in Body) or ordinary Go variables. **UNDER NO CIRCUMSTANCES** may body variables end up in the `Headers` map — Headers and Body are completely independent fields in the request struct. |
| Each `### [TC-xxx]` block in case.md | one `TestXxx(t)` function | Add `// TC-xxx: <test scenario>` above the function; `WithCaseID` keeps the original id |
| `Assertions` list in a step | `apitest.Assert(t, resp, ...)` | one expression per line; normalize to runtime-supported syntax before emitting. **HTTP**: `$.code == 0`, `$.data.*` for business fields (AGW wrapper). **RPC**: `$.BaseResp.StatusCode == 0`, raw IDL field paths. If expected value contains `{{VAR}}`, emit `fmt.Sprintf(..., goVar)` — never copy the case.md line verbatim. |
| `Variable Extraction` list in a step | `Extract: map[string]string{...}` | varname → JSONPath. Read back via `resp.ExtractString("varname")` or `resp.ExtractInt64("varname")`. Only emit `Extract` when the value is needed by a subsequent step. **HTTP**: JSONPath must include `$.data.` prefix for business fields. |
| `### Mock Setup` block (downstream PSM + method) | Mock rule comment + optional `RpcContext` | Per `mock.md`. Emit a short Go comment near the mock-required case with `rule_name` and `mock_rule_url`. For RPC rows, also emit `RpcContext: map[string]string{"DYECP_FD_MOCK": "new_mock_tns_sdd_apitest_mock_group", "MOCK_TAG": "tns_sdd_apitest_mock_group", "APITEST_MOCK_CASE_ID": "<repo>__<caller>__<case_id>"}`. HTTP rows do not inject `RpcContext`. |

## 5. Guardrails

- **Config separation enforced by `SKILL.md §3`**: routing fields go to `<specDir>/.env`; business auth headers go to `<specDir>/auth.yaml` profiles and are accessed via `ctx.AuthHeaders()` / `ctx.AuthHeadersFor("<profile>")`. **Auth literals MUST NEVER appear inline in `*_test.go`** and MUST NEVER be written into `.env`. When a case calls multiple PSMs, `.env` MUST group routes under `services.<service_key>` and each non-default request MUST set `Service: "<service_key>"`; Go code MUST NOT inline `psm` / `host` / `env` / `branch`.
- **CRITICAL — HTTP case headers are not gateway outer headers**: every header declared in `case.md → Request Parameters → Headers` belongs to the target business HTTP request and must be supplied through `apitest.HTTPRequest.Headers`. Do not create or populate `gatewayHeaders`, `outerHeaders`, paas-gw request headers, `.env` keys, `RpcContext`, `Params`, or `Body` from those case headers. The runtime owns the gateway outer headers (`Domain`, `X-Jwt-Token`, paas-gw `Content-Type`) internally.
- **CRITICAL — non-auth headers must come from the `scan_case.py` list, not memory**: for each case, the authoritative set of non-sensitive headers is `scan_case.py`'s `case_headers[].non_auth_headers` (keyed by `case_id`). Generate exactly one `h["<key>"] = "<value>"` line per entry and assign `Headers: h`. After generation, verify every such key appears in the package with `grep -rn '"<key>"' <package_dir> --include='*_test.go'`; a missing key means a dropped header and must be fixed before returning success. Never substitute "re-read case.md and recall the headers" for this list-vs-code check.
- **`specDir()` is path-autonomous**: every generated test embeds the helper that resolves `FEATURE_DIR/test/` purely from `runtime.Caller(0)` + a relative path baked at generation time. **Never** read `APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR`. Only `APITEST_TOKEN` is honored at run time.
- **CRITICAL — NEVER mix Body and Headers**: `Body Parameters` content (incl. `{{VAR}}` placeholders) MUST go into `Body: apitest.JSON{...}` and MUST NEVER appear in `Headers: map[string]string{...}`. Conversely, Headers content MUST NOT be emitted into `Body`. If you see body variable names appear as `--header` keys in any curl trace, the generated code violated this rule and must be regenerated.
- **CRITICAL — HTTP 断言必须适配 AGW 包裹层**: paas-gw HTTP 请求经 AGW 转发后响应格式为 `{"code": N, "data": {...}, "message": "..."}`。生成 HTTP 用例时：
  - 禁止使用 `$.BaseResp.StatusCode`，必须用 `$.code == 0`
  - 禁止直接用 IDL 字段名作为 JSONPath，必须加 `$.data.` 前缀
  - 禁止对负向测试使用 `status_code != 200`，必须用 `$.code != 0`（网关始终返回 HTTP 200）
  - `fmt.Sprintf` 动态路径中的字段名同样需要 `$.data.` 前缀
- **Auth profile references must be valid**: every literal passed to `ctx.AuthHeadersFor("<profile>")` MUST exist as a key under `profiles:` in `auth.yaml` (typo = hard fatal at run time). If a case needs a new identity, add the profile to `auth.yaml` first.
- **Normalize case variables (CRITICAL)**: convert every `case.md` `{{VAR}}` before emitting Go — in **Body/Params/Path AND every `apitest.Assert` argument**. Never leave raw `{{VAR}}` in generated `*_test.go` (runtime does not resolve them anywhere). Dynamic expected values in assertions MUST use `fmt.Sprintf`, e.g. `fmt.Sprintf("$.data.scenarioId == %q", scenarioID)` or `fmt.Sprintf("$.data.triggerMetas[0].triggerKey == %q", "sdt_trigger_key_"+suffix)`.
- **Normalize assertions**: emit only runtime-supported assertions: `status_code`, `$.path`, `len($.path)`, `typeof($.path)`, with operators `==` / `!=` / `>` / `>=` / `<` / `<=` / `in` / `contains`. Do not emit `StatusCode`, `.length`, `IS NOT NULL`, or `matches`.
- **Single entry point**: use `apitest.NewContextFromSpec(t, specDir())` so env / auth / token / log-dir wiring stays centralized. The runtime self-skips with a runnable hint when `APITEST_TOKEN` is absent.
- **Set `WithCaseID("TC-...")`** so logs use the original `case.md` id and `auth.yaml.case_profiles` resolves correctly.
- **Use `apitest.JSON{...}` for bodies**, not raw `map[string]any`.
- **Prefer ordinary Go values over placeholders**. Use `${{var}}` / `${var}` only when a value must flow through the runtime variable map.
- **One file per method**. Multiple cases become multiple `Test<Method><CaseSlug>` functions in the same package. `CaseSlug` MUST describe the case intent, not the TC-ID. **Forbidden**: opaque ID-only names such as `TestTCT0602`, `TestTCS0901`, or `TestTCG0201`; keep TC-ID only in `WithCaseID("TC-...")` and the `// TC-...` comment.
- **Mock traceability comments**: for mock-required cases, emit **exactly two** comment lines immediately above the mocked request block — line 1 `// Mock: <mode> (rule <rule_id>)` (`<mode>` from `case.md` Mock Setup `Mode`: `data` / `panic` / `errcode_<C>` / `timeout_<N>s`); line 2 `// <mock_rule_url>` (BAM Mock console URL per `mock.md §3.6`). Do not embed mock payloads in generated Go.
- **Chain over hardcoded samples**: `resource_ref` fields must be acquired by chaining a List/Query call + `resp.ExtractString(...)` from a package-level `anyExisting<X>(t, ctx)` helper that `t.Skip`s on empty environments. Do not hoist values to package-level `const`.
- **Dynamic construct helpers (replay-safe)**: replay-fragile fields (entity Name with uniqueness, current/past/future timestamps, random description, enum-pick) must use `apitest.UniqueName` / `apitest.NowSec` / `apitest.NowMilli` / `apitest.NowMicro` / `apitest.PastSec` / `apitest.PastMilli` / `apitest.PastMicro` / `apitest.FutureSec` / `apitest.RandString` / `apitest.RandInt` / `apitest.PickOne`. Hardcoded literals are forbidden — they break repeated runs.
- **Environment business samples**: when a business field cannot be chained and its value differs across environments, declare a package-level `var envSamples = map[string]map[string]string{...}` (outer key = `env.Env`, inner key = business token) and read with `apitest.Sample(t, env, "<KEY>", envSamples)`. Missing slots `t.Skip` automatically; never fabricate a value or push it into `.env`. For non-default service samples, obtain the route with `ctx.EnvFor("<service_key>")` before calling `apitest.Sample`.

## 6. Full Example (three-section layout with chained / dynamic / env-sample helpers)

The complete shape generated by the skill when a target uses chained samples, dynamic construction, and per-env business values together:

```go
package search_bank_test

import (
	"fmt"
	"path/filepath"
	"runtime"
	"testing"

	"{{APITEST_IMPORT_PATH}}"
)

// specDir resolves FEATURE_DIR/test/ purely from this source file's location,
// so .env / auth.yaml / api_test_logs/ are picked up regardless of where the
// repository is cloned. Only APITEST_TOKEN is required at run time.
func specDir() string {
	_, thisFile, _, _ := runtime.Caller(0)
	return filepath.Join(filepath.Dir(thisFile), "{{SPEC_DIR_REL}}")
}

// ── ① Protocol constants (cross-env stable) ──
const (
	pathSearchBank     = "/api/v2/infa/sds/bank/search"
	mappedSDSBizline   = "tiktok_live"
	nonExistingBankKey = "__NONEXISTENT_BANK_KEY_FOR_TESTING__"
)

// ── ② Environment business samples (emit only if at least one env_business_sample field exists) ──
var envSamples = map[string]map[string]string{
	"boei18n": {},
	"prod":    {},
}

// ── ③ Test functions ──

// Chained-sample helper: acquires one existing bankKey; t.Skip on empty env.
func anyExistingBankKey(t *testing.T, ctx *apitest.TestContext) string {
	resp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
		Method: "POST", Path: pathSearchBank,
		Headers: ctx.AuthHeaders(),
		Body:    apitest.JSON{},
	})
	key := resp.ExtractString("$.data.bankInfo[0].bankKey")
	if key == "" {
		t.Skip("no existing bank in this env; cannot drive bankKey-filter case")
	}
	return key
}

// TC-G02-02: filter by bankKeys (uses chained sample, no hardcoded literal)
func TestSearchBankByBankKeys(t *testing.T) {
	ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-G02-02")

	bankKey := anyExistingBankKey(t, ctx)

	resp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
		Method:  "POST",
		Path:    pathSearchBank,
		Headers: ctx.AuthHeaders(),
		Body:    apitest.JSON{"bankKeys": []string{bankKey}},
	})
	apitest.Assert(t, resp,
		"status_code == 200", "$.code == 0",
		fmt.Sprintf("$.data.bankInfo[0].bankKey == '%s'", bankKey),
	)
}

// TC-...: write API uses dynamic helpers + env sample (replay-safe)
func TestCreateCustomRiskTag(t *testing.T) {
	ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-...")
	env := ctx.Env()

	name := apitest.UniqueName("api_testing_crt")          // unique per run
	desc := "api testing crt " + apitest.RandString(6)     // random filler
	owner := apitest.Sample(t, env, "DEFAULT_OWNER", envSamples)

	resp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
		Method:  "POST",
		Path:    "/api/v2/custom_risk_tag",
		Headers: ctx.AuthHeaders(),
		Body: apitest.JSON{
			"name":          name,
			"description":   desc,
			"owners":        []string{owner},
			"stages":        []int{1, 2, 3},
			"releaseConfig": apitest.JSON{"isReleaseNow": true},
		},
	})
	apitest.Assert(t, resp, "$.code == 0", "$.data.customRiskTagId > 0")
}

// TC-...: privilege-escalation comparison — same case, two identities.
// Use AuthHeadersFor("<profile>") to pick a non-default profile; profile
// names must exist as keys under `profiles:` in auth.yaml.
func TestSearchBankAsAdmin(t *testing.T) {
	ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-G02-99")

	resp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
		Method:  "POST",
		Path:    pathSearchBank,
		Headers: ctx.AuthHeadersFor("admin"),
		Body:    apitest.JSON{},
	})
	apitest.Assert(t, resp, "status_code == 200", "$.code == 0")
}
```
