# apitest — Go Runtime for API Integration Tests

`apitest` is the only runtime this skill targets. Runtime details live in `runtime/README.md`.

Library import path: resolve per repository with `go list -m`, then append `/tests/integration/apitest`. Do not hardcode this skill's home repository path into generated tests.

## 1. Skill responsibilities

When the api-mind skill runs, it must:

1. **Generate** one `*_test.go` per target, following `resources/go_test_template.md`. Every generated file embeds a `specDir()` helper computed from `runtime.Caller(0) + filepath.Join(...)` so the test resolves its `<specDir>` (= `FEATURE_DIR/test/`) without any path env var.
2. **Construct** request bodies per `SKILL.md §2.2` request construction strategy. `case.md` overrides always win; IDL shape is resolved per the Go driver contract.
3. **Wire** assertions / extracts from `case.md` into `apitest.Assert(...)` and request `Extract` maps.
4. **Use** `apitest.NewContextFromSpec(t, specDir())` as the only public entry point. It loads `<specDir>/.env` (routing; legacy flat or multi-PSM `services.<service_key>` bindings) and `<specDir>/auth.yaml` (business auth profiles), reads `APITEST_TOKEN` for the paas-gw JWT, and pins log output to `<specDir>/api_test_logs/`.

The three-layer config separation (routing `.env` / business `auth.yaml` / per-user `APITEST_TOKEN`) is mandated by `SKILL.md §3` — see there for the full rule set.

## 2. Wire format

| Concern | Behavior |
| --- | --- |
| Gateway endpoints | Selected inside `gateway.go` from the current request's resolved service binding (`zone` / `idc` / `env`). Domain table lives in `runtime/README.md §4.4`; do not duplicate it elsewhere and do not add gateway domain fields to `.env`. |
| Outer headers | Runtime-owned paas-gw headers only: `X-Jwt-Token` from `$APITEST_TOKEN` (or the workflow `user_jwt` step), `Domain: explorer`, `Content-Type: application/json`. Generated tests must not pass `case.md` headers here. |
| Inner business headers | All HTTP `case.md → Request Parameters → Headers` values are downstream business headers and must be supplied via `apitest.HTTPRequest.Headers`. Auth headers are loaded from `<specDir>/auth.yaml` profile via `ctx.AuthHeaders()` / `ctx.AuthHeadersFor("<profile>")`; non-auth headers are layered into the same map before assigning `HTTPRequest.Headers`. |
| Inner payload | JSON envelope with `psm/host/zone/idc/cluster/env/path/method/header/request/func_name/...` (see `gateway.go`). `psm/host/env/branch/zone/idc/cluster` are selected as one unit from `.env services.<service_key>` via `HTTPRequest.Service` / `RPCRequest.Service`; omitted `Service` uses `default_service`. |
| Variable syntax | `${{var}}` preserves type (use inside JSON literals); `${var}` always stringifies (use inside URL paths / strings) |
| Assertion grammar | `status_code == 200`, `$.x == y`, `typeof $.x == 'int'`, `len($.x) > 0`, `jsonpath('$.x') in [1, 2, 3]` — full grammar in `assert.go` |
| Main execution log | `<specDir>/api_test_logs/execution_result.log`, captured from `go test -v` stdout/stderr and used first by report generation |
| Per-case log filename | `<specDir>/api_test_logs/apitest_<case_id>.log`, read only for failed / Error cases as detailed evidence compatible with `resources/test_report_guide.md` |
| PASS conditions | gateway HTTP 200 AND `has_permission == true` AND every assertion truthy |

## 3. Skill-side execution contract

After the skill writes a target test package, it runs:

```bash
export APITEST_TOKEN=<paas-gw JWT>
set -o pipefail
mkdir -p "<specDir>/test/api_test_logs"
GOTOOLCHAIN=auto GOWORK=off go test -v -count=1 -run '^Test<MethodPascal>$' ./tests/integration/<method_snake>/... 2>&1 | tee "<specDir>/test/api_test_logs/execution_result.log"
```

`APITEST_TOKEN` is the only env var honored at run time. `APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR` are **not** read — the source-relative `specDir()` helper baked into the generated test resolves all paths.

Flags: `-count=1` (no cache) / `-run` (scoped) / `GOTOOLCHAIN=auto` (auto-select toolchain) / `GOWORK=off` (drop if your workspace is complete). `tee` is mandatory so `execution_result.log` always records the exact terminal result. Generated tests self-skip with a runnable hint when `APITEST_TOKEN` is unresolved.

## 4. Guardrails

- The runtime is the Go library + `go test`, nothing else. Do not introduce shell-outs to any external CLI.
- The single test-suite format is ordinary `*_test.go` code using `apitest.NewContextFromSpec`, `HTTPRequest` / `RPCRequest`, `CallHTTP` / `CallRPC`, and `Assert`. No parallel YAML / DSL representation.
- Three-layer config separation and the `APITEST_*` env-var ban are enforced by `SKILL.md §3` — generated code that violates them is rejected before Execute.

## 5. Runtime maintenance & versioning

The `apitest` runtime is shipped two ways simultaneously:

| Where it lives | Role |
|---|---|
| Per-repo `tests/integration/apitest/` | The actual Go package every generated test imports. Vendored, tracked in git, owned by the repo. |
| Skill-internal `go_driver/runtime/` (vendored baseline) + `runtime/manifest.json` | Source-of-truth baseline copied into repos by `go_driver/scripts/sync_runtime.py` during `generate` before feature-level code changes. |

### 5.1 Versioning contract (semver, enforced by the sync script)

Both `runtime/version.go` and the per-repo `tests/integration/apitest/version.go` expose `const Version = "X.Y.Z"`. The number is a **stability contract**:

| Bump kind | Allowed | Forbidden | sync behavior |
|---|---|---|---|
| `patch` (X.Y.Z+1) | bug fix; comment / log / impl-internal change | **any** public symbol added, removed, renamed, or signature-changed | silent overwrite after compile-verify |
| `minor` (X.Y+1.0) | adding new public symbols; loosening a parameter; new optional behavior | renaming / removing existing public symbols, breaking JSON shape | overwrite after compile-verify; if compile fails, rollback + ask user |
| `major` (X+1.0.0) | anything | none — but you MUST populate `manifest.breaking_changes[]` and bump `Version` accordingly | overwrite after compile-verify; if compile fails, rollback + ask user (users are expected to read `breaking_changes` first) |

### 5.2 How to bump the runtime version

A **single atomic change set** — all five steps in one MR:

1. **Edit the source** in `go_driver/runtime/*.go` (NOT the per-repo `tests/integration/apitest/`; that gets pushed by `scripts/sync_runtime.py` on next Go generate run).
2. **Bump `runtime/version.go`** `Version` per §5.1.
3. **Recompute sha256** for every changed file and update `runtime/manifest.json` `files[].sha256`. Bump `manifest.json` `version` to match `version.go`.
4. **For minor / major**: append an entry to `manifest.breaking_changes[]` with `from`, `to`, a one-line `summary`, and a `migration_hint` (concrete sed / regex / patch suggestion).
5. **Hand-test once** in this repo: run any generation flow that exercises the changed code path; confirm `tests/integration/apitest/` upgrades smoothly and existing tests still compile.

`source_commit` in `manifest.json` is informational — bump it whenever you re-import from an upstream source so the trail stays auditable.
