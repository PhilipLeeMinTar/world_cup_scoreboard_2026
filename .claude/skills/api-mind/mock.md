# Bytemock Contract for api-mind

## Run-Level Inputs

Resolve once per run:

| Input | Source | Notes |
|---|---|---|
| `case.md` | `FEATURE_DIR/test/case.md` | The only source of mock declarations. The file follows the `prd2case-api` block template. |
| helper | this `mock.md` contract | Owns user-level `api-mock` detect/install/skip before Bytemock calls. |
| cli | `bam-cli api-mock` | Operation entrypoint for Bytemock. |
| `repo` | basename of `git rev-parse --show-toplevel` | Used in deterministic rule names. Keep the basename as-is; do not convert `_` to `.` unless Bytemock name rules are verified. |
| `caller_method` | resolved from the `Case ID`'s owning TC block and its mocked step's `API Contract`; legacy parent `## 接口 N: <CallerMethod>` heading may be used only for backward compatibility | Used in deterministic rule names and case UID. |
| `vregion` / `site` | resolved from `.env` / task env | Used for `bam-cli api-mock` auth and requests. |
| RPC namespace / mock tag | `tns_sdd_apitest_mock_group` | Permanent singleton with `flow_mode=tag`. Injected as `MOCK_TAG`. |
| RPC dyeing value | `new_mock_tns_sdd_apitest_mock_group` | Permanent singleton. Injected as `DYECP_FD_MOCK`; `put-flow-dyeing` uses `MOCK:<dyeing value>`. |
| RPC case filter key | `APITEST_MOCK_CASE_ID` | Fixed Bytemock Header filter key for RPC. It matches RPC persistent metainfo propagated from paas-gw `rpc_context`. |
| BAM Mock console URL | derived after rule planning | Used in generated Go comments and `test_report.md`; display as a Markdown link in reports. |

Current scope: this version supports **RPC downstream mocks only**. HTTP downstream mock rows must not be executed in this version; skip affected cases with `http mock unsupported in current version`.

**Generation-only mode**: dry-run planning without touching Bytemock. Triggered when go_driver calls only §1 + §3 during the `generate` phase. In this mode, skip §2 (install), §4 (prerequisites), §5 (reconcile), and §6 (return); produce only `runtime_metainfo_by_case` + `skipped_cases`. Full-run mode (generate+execute) additionally runs §2 + §4 + §5 and produces `created_rules` / `updated_rules` / `reused_rules` + `managed_rule_identities`.

## Workflow

This workflow owns RPC mock planning and Bytemock state. It does **not** own `go test` execution; it returns runtime injection and skip information to go_driver.

### 1. Locate Mock Setup and parse rows

Do not read the whole `FEATURE_DIR/test/case.md` by default. First use targeted search for `Mock Setup`, `## 3. Mock Setup`, and `### Mock Setup`. If no match exists, return `mock_required=false`. Only after a match, read the matched section plus the referenced `### [TC-xxx]` blocks needed to resolve `caller_method`.

The canonical format from `prd2case-api` is the global section `## 3. Mock Setup (Optional Downstream Dependency Mocks)`. For backward compatibility, legacy per-interface `### Mock Setup` sections may also be parsed.

- No Mock Setup section anywhere -> return `mock_required=false` and stop here. Do not call helper, auth, Bytemock, cleanup, or report mock sections.
- Global `## 3. Mock Setup` exists -> parse rows and use each `Case ID` to locate the corresponding `### [TC-xxx]` block under `## 2. Test Cases`; resolve `caller_method` from that TC's mocked step `API Contract` / `Protocol`.
- Legacy `### Mock Setup` exists -> parse rows under the nearest parent `## 接口 N: <CallerMethod>` heading.
- Invalid row -> fail before any Bytemock operation.

Expected block:

```markdown
## 3. Mock Setup (Optional Downstream Dependency Mocks)
| Case ID | 下游协议 | 下游 PSM | 下游 Method | Mode | Mock Data | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| TC-R01-01 | RPC | tns.live.ubom | RetraceStrategy | data  | `{"BaseResp":{"StatusCode":0}}` | ... |
| TC-R01-02 | RPC | tns.live.ubom | RetraceStrategy | panic | - | ... |
```

Row validation:

| Column | Required | Allowed | Failure |
|---|---|---|---|
| `Case ID` | yes | matches a `### [TC-xxx]` block in `## 2. Test Cases`; Chinese alias `用例 ID` is accepted for backward compatibility | parse error |
| `下游协议` | no | `RPC`; missing means `RPC` for backward compatibility | unsupported protocol rows are skipped |
| `下游 PSM` | yes | `^[a-z0-9_]+\.[a-z0-9_]+\.[a-z0-9_]+$` | parse error |
| `下游 Method` | yes | downstream IDL method name | parse error |
| `Mode` | yes | `data` / `panic` / `timeout_<N>s`（N 为正整数，范围 1-60）/ `errcode_<C>`（C 为非零整数） | parse error |
| `Mock Data` | conditional | JSON literal for `data`; empty or `-` otherwise | parse error |
| `备注` | no | free text | none |

One case may declare several downstream mocks. Reject a case that has two rows with the same `(callee_psm, method)` but different `Mode`. Different downstream pairs may coexist.

### 2. Pre-flight: ensure api-mock is installed

Run this step only when `mock_required=true` and not in Generation-only mode. Generation-only skips this step and continues to step 3 to prepare dry-run rule inputs.

When `api-mock` is needed, check whether the user-level skill exists. If it is missing, install it with the command below.

| Helper | Discovery path | Install command (when missing) |
|---|---|---|
| `api-mock` | `~/.agents/skills/api-mock/SKILL.md` | `npm_config_registry="https://bnpm.byted.org" npx -y skills@latest add code.byted.org/inf/bam_skill --skill api-mock --version 0.1.3 -g -a cursor` |

Pre-flight contract:

1. **Detect**: `test -f "$HOME/.agents/skills/api-mock/SKILL.md"`. Cache the result for the rest of the run; do not re-detect per step.
2. **Install if missing**: run the install command exactly as listed above. Do NOT prepend `sudo`. Do NOT vary registry / version / agent flag. On a non-zero exit, capture stderr verbatim, then go to step 4.
3. **Hand-off**: read `~/.agents/skills/api-mock/SKILL.md` and follow that skill's own contract for the requested operation. Never duplicate or paraphrase its tool-call instructions inline.
4. **Install failure -> skip, do not abort the run**:
   - Mark every case whose `### Mock Setup` block declared at least one mock row as `SKIPPED — api-mock unavailable`.
   - Continue executing the remaining cases (those without mock declarations) normally. Failed install MUST NOT cascade into a hard run failure.
   - Surface the captured stderr + the install command in the test report's "Mock setup skipped" section so the user can re-run the install themselves.

### 3. Prepare Mock Rule Inputs

Input: parsed rows from step 1.

Full-run output:
- `desired_rules`: Bytemock rules that should exist after reconcile.
- `runtime_metainfo_by_case`: per-case RPC context values injected into generated Go.
- `managed_rule_identities`: report/audit metadata for managed rules.
- `skipped_cases`: cases that must not execute because their mock cannot be supported or reconciled.

#### 3.1 Filter unsupported rows

- RPC rows continue through the plan.
- Unsupported non-RPC rows are added to `skipped_cases` and are not added to `desired_rules`.

#### 3.2 Derive identities

For each supported RPC row, derive deterministic IDs:

```text
repo           = basename(git root)
caller_method  = parent interface heading
case_id        = row["Case ID"] or row["用例 ID"]
callee_psm     = row["下游 PSM"]
callee_method  = row["下游 Method"]
mode           = row["Mode"]
case_uid       = "{repo}__{caller_method}__{case_id}"
rule_name      = case_uid, unless the same case has multiple mock rows; then append "__{callee_psm}__{callee_method}" to keep names distinguishable
```

If a derived rule name exceeds 128 字符（Bytemock rule name 上限），add affected cases to `skipped_cases` with `api-mock reconcile failed: rule name exceeds 128 chars`。

#### 3.3 Build runtime injection

Populate `runtime_metainfo_by_case` for each non-skipped RPC row:

```text
runtime_metainfo_by_case[case_id] = {
  "DYECP_FD_MOCK": "new_mock_tns_sdd_apitest_mock_group",
  "MOCK_TAG": "tns_sdd_apitest_mock_group",
  "APITEST_MOCK_CASE_ID": case_uid
}

header_filter = [{"key":"APITEST_MOCK_CASE_ID","op":"eq","value":case_uid}]
```

`header_filter` is the Bytemock API/UI field name. For RPC callees, it matches RPC persistent metainfo propagated from `Step.RpcContext` through paas-gw `rpc_context`; it is not an ordinary HTTP header.

The plan output from this subsection is available to go_driver during test generation. go_driver uses `runtime_metainfo_by_case` to emit `Step.RpcContext` before Bytemock reconcile runs.

#### 3.4 Generation-only stop point

Generation-only mode stops here and returns the dry plan (only `runtime_metainfo_by_case` from §3.3 plus any `skipped_cases` from §3.1 are populated). It must not call helper, auth, Bytemock, or report mock fixtures, and must not run §3.5/§3.6.

#### 3.5 Build desired Bytemock rules

Build `desired_rules` for each non-skipped RPC row. `endpoint_id` is a placeholder at this stage and is resolved in step 4 before reconcile.

| Field | Value |
|---|---|
| `namespace` | `tns_sdd_apitest_mock_group` |
| `endpoint_id` | BAM endpoint id for row `(callee_psm, callee_method)`; resolved in step 4 before reconcile |
| `caller_psm` | `*` |
| `callee_psm` | row `下游 PSM` |
| `method` | row `下游 Method` |
| `protocol` | `thrift` |
| `name` | `rule_name` |
| `filter_type` | `header` |
| `header_filter` | `APITEST_MOCK_CASE_ID == case_uid` |

Mode mapping:

| Mode | Bytemock `mode` | `sub_mode` | `mock_data` | `delay_ms` |
|---|---|---|---|---|
| `data` | `json` | `default_json` | row `Mock Data` | 0 |
| `panic` | `panic` if accepted; otherwise fallback below | `default` | `""` | 0 |
| `timeout_<N>s` | `json` | `default_json` | minimal valid response for the target IDL | `N*1000` |
| `errcode_<C>` | `json` | `default_json` | exact RPC response JSON representing the target error | 0 |

`Mock Data` must use the target RPC response field names, not the HTTP-gateway wrapped field names. For example, a Thrift response field `Message` must be emitted as `{"Message":"..."}`, not `{"message":"..."}`.

If Bytemock rejects a desired rule during reconcile, preserve the original error as `api-mock reconcile failed: <bytemock error>` and do not execute affected cases.

#### 3.6 Build report/audit metadata

Build `managed_rule_identities` for report and audit. `endpoint_id` and final `mock_rule_url` are completed after step 4 resolves `endpoint_id`.

BAM Mock console URL template:

```text
mock_rule_url = <cloud_host>/bam/mock/service/detail?psm=<callee_psm>&namespace=tns_sdd_apitest_mock_group&mock_env=<mock_env>&x-bc-region-id=bytedance&api_branch=<api_branch>&endpoint_id=<endpoint_id>
```

Rules:
- `<cloud_host>` follows the target control plane. For I18N/BOEi18N use `https://cloud.tiktok-row.net`; for CN use the matching ByteCloud host.
- `<mock_env>` is the platform mock environment. For BOE/BOEi18N use `boe`.
- `<api_branch>` is the service API/IDL branch used to create the mock service relation, normally `.env branch` / task env branch / `master`.
- `<endpoint_id>` is resolved in step 4 before reconcile.
- URL-encode query parameters when rendering the final URL.

### 4. Ensure Bytemock prerequisites

Run this only when `mock_required=true` and not in Generation-only mode. For `please login` or HTTP 401 from any `bam-cli api-mock` command, follow "Failure And Auth Recovery".

#### 4.1 Load existing prerequisite state

Query existing namespace, service relation, and flow-dyeing state. Use these results only to decide what step 4.3 needs to create. Cache results for the run; fetch next pages only when `total > page_size`.

| State | Query | Local key |
|---|---|---|
| Namespace | `get-namespaces {"namespace":"tns_sdd_apitest_mock_group","page":1,"page_size":100}` | `name` |
| Services | `list-service {"namespace":"tns_sdd_apitest_mock_group","psm":"<callee_psm>","protocol":"thrift","page":1,"page_size":100}` once per callee PSM | `(psm, protocol)` |
| Dyeing | `list-flow-dyeing {"namespace":"tns_sdd_apitest_mock_group","callee":"<callee_psm>","kind":"rpc","page":1,"page_size":100}` | `(callee, method, dyeing)` |

`bam-cli` is a Go binary; it prepends a single `&{...}` debug line before the JSON body. Always extract the JSON starting at the first standalone `{` line (e.g. `python3 -c "import sys,re,json; raw=sys.stdin.read(); m=re.search(r'^\\{', raw, re.M); print(json.dumps(json.loads(raw[m.start():])))"`). Do not slice on the first `{` character — the prefix line `&{0  0x...}` will trip naive parsers.

#### 4.2 Resolve endpoint IDs

Resolve `endpoint_id` per `(callee_psm, callee_method)`. This is mandatory before reconcile because every `create-rule` requires `endpoint_id`. Use the canonical command — do not try `bam method query` / `bam method query-by-method-path` first; their indexes are inconsistent across vregions and frequently return EOF or empty results.

```bash
bam-cli bam method list --psm <callee_psm> --branch <api_branch> --vregion <V>
```

- `--branch` defaults to the service IDL branch the BAM service relation was created against; `master` works for the vast majority of services and matches the default `idl_version` used in `create-service-relation` below. Override only when the target service has registered IDL on a non-master branch.
- The response is a JSON object whose `data` is a flat array of endpoints. Each entry exposes `endpoint_id`, `rpc_method` (RPC) and/or `path` (HTTP). For thrift mock targets, filter by `rpc_method == callee_method` and pick `endpoint_id`.
- Cache by `(callee_psm, callee_method)` for the run.
- Empty result for a `(callee_psm, callee_method)` -> add affected cases to `skipped_cases` with `api-mock reconcile failed: endpoint not found in BAM (psm=<p>, method=<m>, branch=<b>)`. The downstream service likely never registered its IDL on BAM and Bytemock cannot mock it.

#### 4.3 Create missing prerequisites

Create only the resources missing from step 4.1:

- Missing namespace -> `create-namespace` with `flow_mode=tag`; treat "already exists" as success.
- Missing service relation -> `create-service-relation` with `protocol=thrift` (required, even though `tools.md` lists it as optional); treat existing relation as success. Minimal input:
     ```bash
     bam-cli api-mock --act create-service-relation --vregion <V> --input '{
       "namespace":"tns_sdd_apitest_mock_group",
       "psm":"<callee_psm>",
       "protocol":"thrift",
       "idl_version":"master"
     }'
     ```
- Missing dyeing for `(callee_psm, method, MOCK:new_mock_tns_sdd_apitest_mock_group)` -> `put-flow-dyeing` with `type=rpc`. **`is_valid` and `status` are `bool`, not int** — passing `1`/`0` triggers `json: cannot unmarshal number into Go struct field PutFlowDyeingRequest.is_valid of type bool` from `bam-cli`. Minimal input:
     ```bash
     bam-cli api-mock --act put-flow-dyeing --vregion <V> --input '{
       "callee":"<callee_psm>",
       "callee_cluster":"default",
       "caller":"*",
       "caller_cluster":"*",
       "method":"<method>",
       "dyeing":"MOCK:new_mock_tns_sdd_apitest_mock_group",
       "type":"rpc",
       "is_valid":true,
       "status":true
     }'
     ```
- Successful creates do not require refetch. Refetch only after 409 / duplicate errors, and only for the affected local key.

#### 4.4 Stop on unrecoverable prerequisite failure

If prerequisite loading, endpoint resolution, or bootstrap makes all mock-required cases skipped, return `skipped_cases` immediately; do not create or update rules.

### 5. Reconcile permanent rules

RPC rules are permanent and isolated by `APITEST_MOCK_CASE_ID`. Reconcile is create/update/reuse only; no automatic deletion.

Reconcile in this order:

1. Detect duplicate desired identity with different rule body -> abort reconcile with `case_id collision`; affected cases go to `skipped_cases`.
   - Identity: `(namespace, callee_psm, method, case_uid)`，即 `header_filter` 中 `key="APITEST_MOCK_CASE_ID"` 对应的 `value`。
2. Fetch actual rules once per distinct `(callee_psm, method)`:
   ```text
   query-rules {"namespace":"tns_sdd_apitest_mock_group","psm":"<callee_psm>","method":"<method>","page":1,"page_size":100}
   ```
   Cache by `(callee_psm, method, case_uid)`；fetch next pages only when needed.
3. For each desired rule:
   - Existing rule body equals desired body -> reuse.
   - Existing rule body differs from desired body -> update the rule. Body comparison includes `mock_data`, mode/sub_mode, delay, encoding, filter_type, and `header_filter`.
   - Missing rule -> create it.
   - HTTP 409 / "already exists" / "duplicate name" -> refetch only the affected `(callee_psm, method)` and treat as successful concurrent creation if the resulting body matches desired.
   - `panic` create/update rejected -> retry once using `mode=json`, `sub_mode=default_json`, and a valid error-shaped response for the target IDL.
   - Other create/update failures -> add only cases depending on that rule to `skipped_cases`; continue reconciling other rows.

Output:

| Field | Meaning |
|---|---|
| `created_rules` / `updated_rules` / `reused_rules` | Rule actions for the report. |
| `skipped_cases` | `case_id -> reason` for every mock-required case that must not execute. |
| `runtime_metainfo_by_case` | `case_id -> RpcContext key/value pairs` for non-skipped mock-required cases. |
| `managed_rule_identities` | Desired permanent rule identities for report/audit only; not a deletion list. Include `rule_name`, `endpoint_id`, `namespace`, `mock_env`, `api_branch`, and `mock_rule_url`. |

### 6. Return execution control to go_driver

This workflow does not edit `*_test.go` and does not run `go test`. It returns execution control to go_driver.

Return:

| Field | Consumer responsibility |
|---|---|
| `runtime_metainfo_by_case` | Produced during mock planning; go_driver injects these entries into generated `Step.RpcContext`. |
| `skipped_cases` | go_driver excludes these cases from execution, or aborts the affected package command if case-level exclusion is impossible. |
| `created_rules` / `updated_rules` / `reused_rules` | go_driver renders Mock Fixtures in `test_report.md`. |
| `managed_rule_identities` | go_driver renders the desired permanent rule set for audit and emits per-case Go comments per `go_test_template.md §5` (single source for the comment format). |

Generated Go must inject only `RpcContext`; it must not embed mock payloads.

```go
RpcContext: map[string]string{
    "DYECP_FD_MOCK":        "new_mock_tns_sdd_apitest_mock_group",
    "MOCK_TAG":             "tns_sdd_apitest_mock_group",
    "APITEST_MOCK_CASE_ID": "tsop_ms_api__ReleaseStrategyGroup__TC-R01-01",
}
```

`gateway.go.buildRpcContext` materializes these entries into `rpc_context: [{key,value,type:"persistent",status:0}]`. Bytemock Header filter matches `APITEST_MOCK_CASE_ID` after it becomes RPC persistent metainfo.

Execution is owned by go_driver, but it must consume this workflow output:

- Exclude skipped mock-required cases from `go test`, or abort the affected package command if case-level exclusion is impossible.
- Never real-call downstream for a skipped mock-required case.
- Non-mock cases must not inject `DYECP_FD_MOCK`, `MOCK_TAG`, or `APITEST_MOCK_CASE_ID`.
- When the response contract exposes `BaseResp.Extra["Mock-Rule-Id"]` or `["Mock-Rule-Name"]`, mock-required cases should assert `Mock-Rule-Name != null` so dropped dyeing fails visibly.

## Failure And Auth Recovery

If any `bam-cli api-mock` command returns `please login` or HTTP 401, prompt the user to log in, retry the failed command once, and skip only the affected mock-required cases if the retry still fails.

```bash
bytedcli --site <site> auth logout              # discards any "downgrade":true JWT
bytedcli --site <site> auth login               # opens browser -> full SSO -> fresh JWT
bam-cli api-mock --act get-namespaces \
        --vregion <V> --input '{"page_size":1}'  # smoke test
```

Where:
- `<site>` = the SSO realm: `boei18n` for this repo, `cn` for prod CN, `i18n-tt` for TikTok.
- `<V>` = the BAM region matching `<site>` (`boei18n`, `Singapore-Central`, ...).

If the login command prints a device URL, best-effort open it automatically (`open "<url>"` on macOS); if that fails, show the URL/code for manual authorization.
If `bam-cli` still cannot read the login state in sandboxed execution, rerun the same `bam-cli` command outside the sandbox.

## Known Constraints

| # | Constraint | Current behavior |
|---|---|---|
| C1 | Bytemock Header filter naming is misleading for RPC. | Treat it as the Bytemock API field name. For RPC, the matched data is RPC persistent metainfo from `Step.RpcContext`, not ordinary HTTP headers. |
| C2 | Same case mocking the same `(callee_psm, method)` twice with different responses needs sequence semantics. | Reject for now; ask the user to split the case or use a single deterministic response. |
| C3 | `errcode_<C>` depends on the target RPC response schema. | Use exact RPC response JSON, or `Mode=data` when the schema is non-standard. |
| C4 | Permanent RPC rules can accumulate. | Report managed RPC rules and warn when namespace rule count is high; do not auto-delete. |
| C5 | Concurrent create-rule race. | Treat HTTP 409 / "already exists" as success only after refetch confirms the body matches desired. |
| C6 | `bam-cli` auth can be flaky after login. | Prompt login, retry the failed command once, then skip affected cases only if the retry still fails. |
| C7 | HTTP downstream mock is not supported in this version. | Skip affected cases with `http mock unsupported in current version`; do not create HTTP namespaces, dyeing, rules, or URL rewrites. |

## Strict Constraints

1. `### Mock Setup` is the only trigger.
2. Generation-only must not touch Bytemock.
3. Helper pre-flight stays in this `mock.md` contract.
4. Reconcile must output `skipped_cases`; skipped mock-required cases must not execute against real downstreams.
5. RPC `RpcContext` is the only runtime injection channel; mock payloads stay out of generated Go code.
6. `DYECP_FD_MOCK`, `MOCK_TAG`, and `APITEST_MOCK_CASE_ID` are injected only for RPC mock-required cases.
7. `APITEST_MOCK_CASE_ID` is the only per-case rule filter key.
8. RPC namespace, service relations, flow-dyeing rules, and mock rules are permanent by default.
9. Do not create, update, or delete HTTP mock resources in this version.
