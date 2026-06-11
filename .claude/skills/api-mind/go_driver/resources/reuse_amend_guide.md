# Reuse / Amend / New — Triage Guide

This document is the contract for `SKILL.md` §1.1 Generate 第 3 步（用例分流）和第 4 步（代码生成与校验）. Read it whenever you handle a target (method or scenario) that already has an integration test on disk.

---

## 1. Why triage

`tests/integration/` is a long-lived asset. Every feature should:

- **Reuse** already-passing cases when nothing in the contract changed.
- **Amend** existing files in place when a field, an assertion, or one extra case is needed — never rewrite.
- **Create new** files only when no prior coverage exists.

The triage step makes this explicit so the LLM can decide once, then mechanically dispatch.

### 1.1 Classification → triage prior

`triage.yaml.targets[]` produced during `SKILL.md` §1.1 Generate 第 3 步（用例分流）tags every impacted target with one of four classifications. Use the tag as the **strong prior** when picking a triage decision (the on-disk lookup in §3 just confirms or overrides it):

| classification | What it means | Default decision |
|---|---|---|
| `new-method` | The target is explicitly introduced by SDD artifacts (`spec.md` / `case.md`), or a handler entry exists only on the current branch, or local IDL confirms a new method. For `scenario`, use `new-method` when any contributing method is new or the scenario itself has no base coverage. | `new` when absent on base; if base coverage already exists, usually `amend` unless the existing test already covers the same SDD contract. |
| `idl-changed` | Local IDL is available and request/response struct, method signature, or annotation changed for at least one existing method touched by the target. IDL absence must not block targets discovered from SDD artifacts. | Likely `amend`; promote to `new` if the change reshapes `Steps`. |
| `handler-changed` | Handler / domain code maps to this target while local IDL is stable or unavailable. | Likely `amend`; demote to `reuse` only when the change is observably a no-op (see §1.3). |
| `case-only` | SDD artifacts require testing this target, but no local code/IDL diff maps to it. | Likely `reuse` if base coverage already matches the SDD case; promote to `amend` when `case.md` changes input, assertion, extract, setup, or adds a case/scenario. |

The `classification` MUST be preserved in `triage.yaml.targets[].classification` so the report in `SKILL.md` §1.3 Report can build the coverage matrix without re-deriving anything.

### 1.2 Multi-source priority

A single target can be discovered by more than one source (IDL diff + handler diff + case.md mention is common). Record every contributing source in `triage.yaml.targets[].source` (a list, not a string), and pick `classification` by taking the highest of:

```
new-method  >  idl-changed  >  handler-changed  >  case-only
```

Example: a method that is both `idl-changed` and `case-only` ⇒ `classification: idl-changed`, `source: [case, idl]`.

SDD sources (`case.md`, `spec.md`, `task.md`) are authoritative for **what to test**. Code/IDL sources are evidence for classification and dispatch. Missing local IDL is not a reason to drop or downgrade a target discovered from SDD artifacts.

### 1.3 Objective `handler-changed` → `reuse` demotion

Demoting `handler-changed` to `reuse` is the only place where a code diff is silently ignored, so the bar is high. Demote ONLY when **every** contributing diff hunk satisfies one of:

- Comment-only edit (Go `//` or `/* */`).
- Log-line edit (`log.*`, `klog.*`, `logger.*`, `t.Log*`) with no captured value used downstream.
- Pure local variable rename (no exported identifier touched, no struct field renamed, no JSON tag touched).
- Whitespace / `gofmt` reflow.

If any hunk falls outside this set, default to `amend`. Capture the demotion justification in `triage.yaml.targets[].reason` so reviewers can audit.

### 1.4 Keep base audit separate from worktree coverage

> Keep `<base-branch>` as the stable audit baseline, but do not ignore the working tree. `SKILL.md` §1.1 Generate 第 3 步（用例分流）first checks base coverage (`git ls-tree <base-branch> -- <path>` / `git show <base-branch>:<path>`), then checks the current working tree target path. A file that exists only in the working tree (for example, from a previous unfinished run) is not base coverage, but it **is** candidate executable coverage and MUST enter the same reuse/amend/new decision:
>
> - If it fully matches `case.md` and current generator/runtime contracts, use `decision: reuse`, `coverage_source: worktree`.
> - If it is relevant but needs normalization or additional cases/assertions, use `decision: amend`, `coverage_source: worktree`.
> - If it is unrelated or unsafe to patch, keep `decision: new`, but §4.c MUST ask whether to overwrite, backup-then-overwrite, or abort. It must never silently run the stale worktree file.

---

## 2. `triage.yaml` schema

Path: `FEATURE_DIR/test/triage.yaml`. One YAML document with a header + one entry per impacted target.

```yaml
# header — written during SKILL.md §1.1 Generate 第 3 步（用例分流）
base_branch: origin/master                  # resolved during 第 3 步; may be <none> only if all fallback steps fail
generated_at: 2026-04-25T10:30:00+08:00     # local time, ISO-8601

targets:
  - target: get_all_policy_group_meta       # snake_case method (kind=method) or scenario id (kind=scenario)
    kind: method                            # method | scenario
    classification: case-only               # see §1.1; highest of all contributing sources
    source: [case]                          # list; subset of {case, spec, task, handler, idl}
    decision: reuse                         # reuse | amend | new
    coverage_source: base                   # base | worktree | generated
    existing_path: tests/integration/get_all_policy_group_meta/get_all_policy_group_meta_test.go
    existing_case_ids: [TC-G01-01]          # parsed from BASE-BRANCH copy in §3.b (audit snapshot, immutable)
    worktree_case_ids: [TC-G01-01]          # parsed from WORKING-TREE copy in §3.b; identical here = no local divergence
    reason: case.md keeps existing coverage; no IDL or handler diff under this method.

  - target: search_bank
    kind: method
    classification: idl-changed
    source: [case, idl]
    decision: amend
    coverage_source: base
    existing_path: tests/integration/search_bank/search_bank_test.go
    existing_case_ids: [TC-G02-01, TC-G02-02, TC-G02-03, TC-G02-04, TC-G02-05, TC-G02-06]
    worktree_case_ids: [TC-G02-01, TC-G02-02, TC-G02-03, TC-G02-04, TC-G02-05, TC-G02-06]
    changes:
      - kind: patch_body                    # change a field in an existing case
        target_case_id: TC-G02-04
        jsonpath: $.Bizlines[0]
        from: "tiktok-live-room"            # MUST occur exactly once in the case block
        to: "tiktok-photo"
      - kind: append_assert                 # add an extra Asserts entry
        target_case_id: TC-G02-04
        expression: 'len($.BankInfo) > 0'
      - kind: add_case                      # append a brand-new case to the same file
        new_case_id: TC-G02-07
        summary: SearchBank returns owner-restricted results when Owner is set together with Bizlines

  - target: list_enforcement_rule
    kind: method
    classification: new-method
    source: [idl]
    decision: new
    coverage_source: generated
    target_path: tests/integration/list_enforcement_rule/list_enforcement_rule_test.go
    reason: no prior coverage in tests/integration/.

  - target: policy_group_full_lifecycle     # scenario id (snake_case, derived from 用例 ID 或 测试场景)
    kind: scenario
    methods: [CreatePolicyGroup, UpdatePolicyGroup, ReleasePolicyGroup, GetPolicyGroupDetails]
    classification: idl-changed             # propagated from the highest-classified contributing method
    source: [case, idl]
    decision: new
    coverage_source: generated
    target_path: tests/integration/scenario/policy_group_full_lifecycle/policy_group_full_lifecycle_test.go
    reason: case.md introduces a new cross-method scenario; no scenario file exists on origin/master.
```

### Field reference

| Field | Required when | Meaning |
|---|---|---|
| `base_branch` (header) | always | Branch resolved during `SKILL.md` §1.1 Generate 第 3 步（3-step fallback）. If all fallback steps fail, write `<none>`, skip diff-derived buckets that require a base, and warn once. |
| `generated_at` (header) | always | When the seed `triage.yaml` was written. Helps audit stale artifacts. |
| `target` | always | snake_case key. For `kind: method`, the snake_case method name. For `kind: scenario`, the scenario id derived from `case.md` (`用例 ID` first, then `测试场景`). |
| `kind` | always | `method` or `scenario`. Drives every path resolution downstream. |
| `methods` | scenario | Ordered list of RPC / HTTP method names exercised by the scenario, in the order they appear in `case.md` `Steps`. |
| `classification` | always | Highest of all contributing sources per §1.2. |
| `source` | always | List of discovery sources: subset of `{idl, handler, case}`. Never empty. |
| `decision` | always | `reuse` / `amend` / `new`. Single source of truth for §4.c dispatch. |
| `coverage_source` | always | `base` when the decision is anchored by base-branch coverage; `worktree` when base is absent but the current working tree contains relevant coverage; `generated` when no usable existing file is used and §4.c will emit a fresh file. |
| `existing_path` | reuse, amend | Repo-relative path to the existing `*_test.go`. For `coverage_source: base`, it was found under `<base-branch>` and may also exist in the working tree. For `coverage_source: worktree`, it exists only in the current working tree. |
| `existing_case_ids` | reuse, amend with base coverage | Pre-parsed list of case ids from the **base-branch** copy (`git show <base-branch>:<path>`). Audit snapshot — never mutated by §4. Used by §7's base coverage matrix. Extraction MUST support both direct `WithCaseID("<id>")` and local helper wrappers such as `newContext(t, "<id>")`; see §2.3. Use `[]` when `coverage_source: worktree` and base has no copy. |
| `worktree_case_ids` | reuse, amend (when working-tree file exists) | Pre-parsed list of case ids from the **working-tree** copy. This is the actual §4.c REUSE/AMEND execution anchor. It may differ from `existing_case_ids`; divergence is logged in `reason:` but does NOT abort. Extraction MUST use the same rules as `existing_case_ids`; see §2.3. |
| `target_path` | new | Where the new file will be written. Resolved by `kind`. |
| `changes` | amend | List of edits. Each entry has a `kind` from §2.1. |
| `reason` | always | One sentence: why this decision. Helps human reviewers; mandatory when overriding the §1.1 default. |

### 2.1 `changes[].kind`

| `kind` | Other fields | Effect at step 4.c |
|---|---|---|
| `patch_body` | `target_case_id`, `jsonpath`, `from`, `to` | StrReplace inside the matching `Test...` function / request block, only on the named JSON path. **`from` MUST occur exactly once within the target case block** — see §2.2. |
| `append_assert` | `target_case_id`, `expression` | Insert one new argument into that case's `apitest.Assert(t, resp, ...)` call. |
| `add_extract` | `target_case_id`, `var_name`, `jsonpath` | Insert one new entry into the request's `Extract: map[string]string{...}`. |
| `add_case` | `new_case_id`, `summary` | Append a fresh `Test<TargetPascal><CaseSlug>` function after the last existing case test in the same file. |

If a change does not fit any `kind` above (e.g. you need to restructure the call chain), promote the target's decision to `new` and write a brand-new file alongside; do not over-stretch `amend`.

### 2.2 AMEND must re-read the working tree

Before applying any `changes[]` entry, **re-read the on-disk file** (working tree, not `<base-branch>`) and rebuild a fresh `case_ids_now` list from `WithCaseID("<id>")` calls. Compare it against `worktree_case_ids` (also from §3.b — the working-tree snapshot at triage time):

- **Match** → proceed: use `case_ids_now` as the patch anchor.
- **Mismatch** → the working tree changed *between* §3.b (triage) and §4.c (apply patch) — typically a parallel agent edit or a manual hand-patch landed in the meantime. Refresh `worktree_case_ids` in the in-memory triage object, log the diff to `reason:`, and proceed using `case_ids_now`. Do **NOT** loop back into §3 — §3 anchors on `<base-branch>` (which has not changed); re-running it would just rebuild the same `existing_case_ids` and miss the working-tree update.

Then enforce per `changes[]` entry:

- For every `patch_body`, `append_assert`, `add_extract`: `target_case_id` MUST be present in `case_ids_now`. If absent — the case was deleted by a parallel edit — abort with `target_case_id '<id>' missing from working tree (was present in §3.b worktree_case_ids: <list>); the case was likely deleted by a parallel edit. Refresh case.md or restore the case, then re-run §4.` Do not silently downgrade to `add_case`.
- For every `patch_body`: `from` MUST occur **exactly once** inside the matching case function (use the surrounding `WithCaseID("<target_case_id>")` and the next `func Test...` as the lookup window). Zero matches ⇒ stale plan, abort. Multiple matches ⇒ disambiguation needed, abort and ask the user to widen `from` with surrounding context.
- For every `add_case`: `new_case_id` MUST NOT collide with any ID in `case_ids_now`, AND MUST be globally unique across the whole `tests/integration/` tree (search for `WithCaseID("<new_case_id>")`). Collision ⇒ abort and ask the user to renumber.

The `existing_case_ids` list (built from `<base-branch>`) is the **audit baseline** — never mutated. The `worktree_case_ids` list (built from the working tree at §3.b) is the **execution/patch anchor candidate**, refreshed against `case_ids_now` at §4.c. Together they protect against (a) confusing base coverage with working-tree-only coverage and (b) concurrent edits that landed between plan and apply.

### 2.3 Case ID extraction compatibility

Generated NEW files should use direct literals (`apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-...")`) because this is easiest to audit. Existing repository tests, however, may wrap context creation in local helpers, and older generated files may still use the legacy `apitest.NewContext(t, env)` form. Triage and report parsing MUST therefore extract case IDs from all of these shapes:

```go
apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-G01-01")        // current
apitest.NewContext(t, apitest.EnvFromFile(t)).WithCaseID("TC-G01-01")   // legacy, still supported for parsing
newContext(t, "TC-G01-01")
newContext(t, someSetup, "TC-G01-01") // helper wrapper; last literal arg may be the case id
```

Extraction rule:
- Primary: collect all string literals passed directly to `.WithCaseID(...)`.
- Compatibility: collect string literals matching `TC-[A-Z0-9-]+` in calls to local helper functions whose name contains `Context` / `context` (for example `newContext`, `newTestContext`).
- De-duplicate while preserving source order.
- If no case IDs are found in a file that contains `apitest.CallHTTP` or `apitest.CallRPC`, warn in `triage.yaml.targets[].reason` and treat the file as not safely reusable until the user confirms the mapping.

---

## 4. Dispatch rules at step 4.c

### 4.1 REUSE

Action: nothing on disk.

Outputs:
- Add the file path to the report's coverage matrix under "Reused".
- The execution step (§6) still runs `go test` against this file — a regression here is real news.

### 4.2 AMEND — worked example (method)

Existing file (read from working tree per §2.2):

```go
// TC-G02-04: SearchBank Bizlines = tiktok-live-room
func TestSearchBankBizlinesTiktokLiveRoom(t *testing.T) {
    ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-G02-04")

    resp := apitest.CallRPC(ctx, apitest.RPCRequest{
        Method:  "SearchBank",
        Headers: ctx.AuthHeaders(),
        Body:    apitest.JSON{"Bizlines": []string{"tiktok-live-room"}},
    })
    apitest.Assert(t, resp,
        "$.BaseResp.StatusCode == 0",
    )
}
```

`triage.yaml` says:

```yaml
- target_case_id: TC-G02-04
  changes:
    - kind: patch_body
      jsonpath: $.Bizlines[0]
      from: '[]string{"tiktok-live-room"}'
      to:   '[]string{"tiktok-photo"}'
    - kind: append_assert
      expression: 'len($.BankInfo) > 0'
```

Apply two StrReplace edits:

| Step | `old_string` | `new_string` |
|---|---|---|
| 1 | `[]string{"tiktok-live-room"}` | `[]string{"tiktok-photo"}` |
| 2 | `"$.BaseResp.StatusCode == 0",` | `"$.BaseResp.StatusCode == 0",`<br>`            "len($.BankInfo) > 0",` |

Both `old_string` values must be unique within the `TC-G02-04` test function (per §2.2). If `[]string{"tiktok-live-room"}` happens to appear in another case in the same file too, widen the patch with surrounding context (e.g. include `WithCaseID("TC-G02-04")` and nearby request lines) until the match is unique.

Resulting file:

```go
// TC-G02-04: SearchBank Bizlines = tiktok-live-room
func TestSearchBankBizlinesTiktokLiveRoom(t *testing.T) {
    ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-G02-04")

    resp := apitest.CallRPC(ctx, apitest.RPCRequest{
        Method:  "SearchBank",
        Headers: ctx.AuthHeaders(),
        Body:    apitest.JSON{"Bizlines": []string{"tiktok-photo"}},
    })
    apitest.Assert(t, resp,
        "$.BaseResp.StatusCode == 0",
        "len($.BankInfo) > 0",
    )
}
```

Things that did NOT change: imports, the `TestSearchBankBizlinesTiktokLiveRoom` signature, the `apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-G02-04")` chain, all other case functions in the file, and the `// TC-G02-04: ...` intent comment (rename only if `case.md` explicitly asks for it).

### 4.3 AMEND — append a new case

For an `add_case` change, locate the end of the last existing generated `Test...` function in the same file and insert a new flat test function immediately after it:

```go
// <new_case_id>: <summary from case.md>
func Test<TargetPascal><CaseSlug>(t *testing.T) {
    ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("<new_case_id>")

    resp := apitest.CallHTTP(ctx, apitest.HTTPRequest{
        Method:  "<method>",
        Path:    "<path>",
        Headers: ctx.AuthHeaders(),
        Body:    apitest.JSON{ /* per case.md row */ },
    })
    apitest.Assert(t, resp,
        /* per case.md row */
    )
}
```

Use `case.md` as the source of truth for `Body` / `Asserts` / `Extract` (same rules as `new`).

### 4.4 NEW — `kind: method`

Whole-file generation per `resources/go_test_template.md`. File path: `tests/integration/<target>/<target>_test.go`. Function name: `Test<TargetPascal>`. No special handling.

### 4.5 NEW — `kind: scenario`

Whole-file generation per `resources/go_test_template.md`, with two adjustments:

- File path: `tests/integration/scenario/<target>/<target>_test.go` (run `mkdir -p tests/integration/scenario/<target>` on demand if the `scenario/` root does not yet exist).
- Function name: `TestScenario<TargetPascal>`.
- The scenario test function contains 2+ flat `apitest.CallHTTP` / `apitest.CallRPC` calls, one per method in `triage.yaml.targets[].methods`, in the same order as `case.md`. Use `resp.ExtractString(...)` / `resp.ExtractInt64(...)` and ordinary Go variables to thread IDs from earlier calls into later ones.

Everything else (imports, `ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-...")`, `apitest.JSON` bodies, and `apitest.Assert(...)` calls) is identical to `kind: method`. Do not add obsolete `apitest.New(t).WithEnv(...)`, `WithLogDir(...)`, `apitest.NewContext(t, apitest.EnvFromFile(t))`, or `os.Getenv("APITEST_TOKEN")` guards to generated files; runtime env, JWT, and log-dir handling are owned by the workflow/runtime contracts.

---

## 5. Self-check before you mark step 4 complete

Run through this list every time:

- [ ] Every entry in `triage.yaml.targets[]` has a non-empty `target`, `kind`, `classification`, `source` (list), `decision`, and `reason`.
- [ ] Header has `base_branch` and `generated_at` filled in. `base_branch` is the value resolved during `SKILL.md` §1.1 Generate 第 3 步（never empty, never the local short branch name).
- [ ] `decision` is consistent with `classification` per §1.1 — overrides MUST be justified in the `reason` field. `handler-changed → reuse` demotions cite §1.3 criteria.
- [ ] Existence checks for every `reuse` / `amend` entry came from `git ls-tree <base-branch> -- <path resolved by kind>`, not from `ls tests/integration/...`. Working-tree-only files MUST NOT silently become REUSE/AMEND baselines.
- [ ] For each `amend` decision: the file was **re-read from the working tree** (per §2.2) before applying patches; every `patch_body.from` matched **exactly once** inside the target case block; every `add_case.new_case_id` is unique across the whole `tests/integration/` tree.
- [ ] For each `amend` decision, `git diff tests/integration/<...>/...` shows ONLY the changes listed in `triage.yaml.changes`. No reformat, no boilerplate moves, no other case touched.
- [ ] For `kind: scenario` targets, the file lives under `tests/integration/scenario/<target>/`, the function is `TestScenario<TargetPascal>`, and flat `apitest.CallHTTP` / `apitest.CallRPC` calls cover every method in `triage.yaml.targets[].methods` in `case.md` order.
- [ ] Every NEW or AMEND generated case uses `apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-...")`; no generated file contains obsolete `env := apitest.EnvFromFile(t)`, `apitest.NewContext(t, env)`, `apitest.New(t).WithEnv(...)`, `WithLogDir(...)`, or inline `os.Getenv("APITEST_TOKEN")` guards.
- [ ] Existing `WithVars` / `Extract` variable plumbing present before this run is still present with the same semantics (no AMEND silently rewrote unrelated variable flow).
- [ ] `GOWORK=off go test -run '^NoMatch$' -count=1 ./tests/integration/<target>/...` (or `./tests/integration/scenario/<target>/...`) passes for every NEW or AMEND target — compiles **and links** without executing any test body. Compile or link errors triggered the §4.d 3-retry loop, not silent skips.
