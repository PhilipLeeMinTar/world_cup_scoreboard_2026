# Code And API Research (And Knowledge Sedimentation)

Use this reference when business knowledge is missing or incomplete (Phase 4 of the skill workflow). The output of this phase is **a new or updated knowledge entry** in the relevant `data_queries.md` (or equivalent), so the next run can hit it directly without re-reading code.

This is the only path to growing reusable data-query knowledge. Do not skip the sedimentation step — undocumented findings will be re-discovered (and possibly mis-discovered) next time.

## When To Trigger Code Research

Trigger this phase when, for a given requirement:

- knowledge doc has no entry for the entity (**MISS**), or
- knowledge doc covers query but not create (or vice versa) (**PARTIAL**), or
- the documented selection rule disagrees with what the API actually returns
- enum values, permission rule, or URL pattern is unclear

Do **not** start code research for **HIT** requirements that already query successfully.

## Research Order

Inspect frontend code in this order (cheapest first, most authoritative last):

1. **route / page component** — reveals URL pattern and the page's required params
2. **local hooks used by the page** — reveals which list/detail/mutation calls power it
3. **shared query / mutation hooks** — reveals queryKeys, polling, and invalidation
4. **API wrapper / client** — reveals endpoint, method, base path
5. **generated typings / IDL schema** — authoritative payload shape and enum values
6. **renderers / selectors that map enum values to labels** — confirms what an enum actually means in UI
7. **permission helpers** — confirms the actual permission check the frontend uses

Stop as soon as a fact is proven. Do not over-explore.

## Minimum Facts To Prove (Before Sedimentation)

A new knowledge entry is only valid if you can prove all of:

- the **entity** behind the page (with parent/child relations, if any)
- the **route pattern** that produces the final page URL, including route provenance: target app, `basename`, route path, query/hash requirements, and source file(s)
- the **list API** that locates candidates (endpoint + minimal request body + key response fields)
- the **detail API** that verifies suitability
- the **create / update API** if seeding is needed (endpoint + minimal request body + side effects)
- the **enum values** for required UI labels or states (with code reference)
- the **actual permission check** the frontend uses (e.g. `administrators` includes current uid)
- for every mutating action: the **enable chain** (positive boolean terms with code citations) — see "Enable-Chain Research" below

If any one is unprovable from code alone, run a live API call with the user-provided auth and record the runtime result.

## Route Provenance (Required Before URL Backfill)

Before writing any direct page URL into `test_analysis.md`, prove the URL shape from the frontend entry configuration. Do not infer it from naming.

Minimum proof:

- Identify the target app and its router / entry config (for example `apps/<app>/src/routers/index.tsx`, route table, Next route folder, or a page-entry registry).
- Record the app `basename` separately from the business route. Example: `basename=/moderation-system`, route `/recall-strategy/strategy-group/list` → final path `/moderation-system/recall-strategy/strategy-group/list`.
- Record query / hash parameters that are required for the target state, and which API/detail response supplies their values.
- If host is environment-dependent, record the environment source (known platform host, `.env`, deployment config, or user-provided URL). Do not guess host from a sibling app.
- If route config is not findable, mark the row `UNVERIFIED — route provenance missing` or escalate; do not close it with a guessed URL.

Red flags that require re-checking router/basename:

- Adjacent duplicate path segments such as `/recall-strategy/recall-strategy/...`.
- The same token appears as app directory, basename, and route segment.
- Historical URLs disagree with current router config.
- A generated URL later shows NotFound / 404 in screenshot or logs; treat this as a generation-stage route provenance failure and update the knowledge entry, not as a TTAT-only flake.

## Good Search Targets

Look for these patterns in the codebase:

- `routes/**/page.tsx`, `routes/**/layout.tsx`, dynamic segment folders `[id]/`
- `useList*`, `useGet*`, `useCreate*`, `useUpdate*`, `useDelete*`
- `api/` wrappers (e.g. `platform_api/index.ts`, `platform_api/hooks/**`)
- generated `Request` / `Response` interfaces under `api/typings/**`
- `render*Tag`, `statusMap`, `typeMap`, `labelMap`, `*Select` components
- permission helpers: `isAdmin`, `hasPermission`, `canEdit`, `useKaniPermission`, ownership checks like `administrators.includes(currentUid)`

## Enable-Chain Research (For Every Write / Stateful Row)

Every row whose step 1 clicks a button, toggles a switch, or opens a modal to mutate state must have its **enable chain** traced in code before any query or creation. Skipping this step is the most common source of "sample exists in the right state, but step 1 can't click the button" failures — typically because an *outer container's* state disables the whole action surface.

### What to trace

Trace the boolean expression the UI uses for the `disabled` / `hidden` / conditional-render prop of the **exact control step 1 uses**. Follow helper calls down to base terms. The output is a flat list of positive conditions (things that must be true for the button to be interactive).

### Search targets

1. **The target control's render site** — find the exact button / menu item / cell-renderer. Grep for its label text (often matches a UI literal or `t('…')` key), or the test-id / class attribute.
2. **The `disabled` prop's expression** — read the JSX / template. Typical shapes:
   - `disabled={!canEdit || doc.state !== 'Available' || parentKb.status !== 'Available'}`
   - `disabled={!permissions.kbEdit}` — keep tracing `permissions.kbEdit`
3. **Permission helpers** — `useOperablePermission`, `useKaniPermission`, `canEdit`, `hasPermission`, `isAdmin`. Walk into them and record the base terms (which fields on which entity decide the helper's result).
4. **Parent-state gates** — often the row renderer receives `parentKb` / `parent` as a prop, and uses a field like `status` / `state`. Confirm which field, which comparison, which enum value.
5. **Lifecycle gates** — publishing state / draft-vs-released / archived: fields like `workflow.type`, `workflow.publishStatus`.
6. **Transient busy gates** — flags like `hasRunningImport`, `isPolling`, `jobInProgress`; or the presence/absence of an in-progress job in a list API.
7. **Row-count / shape gates** — the control may only render when `items.length > 0` or `rowCount >= 1`.
8. **Toolbars / page-wrappers** — the button may be technically enabled, but the whole toolbar is replaced by a read-only variant based on parent state. Read the page-level wrapper, not just the button itself.

### Output shape (to sediment)

Record the chain as part of the knowledge entry for the feature:

```text
Enable chain for "<action label>" on <page>:
- <entity>.<field> == <value> (source: <file:line>, <one-line reason>)
- <entity>.<field> in <set> (source: ...)
- currentUid ∈ <entity>.administrators (source: <permission helper path>)
- !<entity>.<transient-busy-flag> (source: ...)
- <sibling>.count >= <N> (source: ...)
```

Rules:

- One line per atomic term. Do not collapse "user has edit permission" into a single term when the helper decomposes into 2–3 base booleans.
- Positive form only. Rewrite `!disabled` as `enabled`, `!locked` as `not locked` → then phrase each term positively.
- Each term must cite a code location. Terms without code backing are rejected.
- If the chain ends up having > 6 terms, re-check — a too-long chain often means you conflated multiple actions (e.g. edit + delete) that have different chains. Split them.

### How the chain is used downstream

- **Phase 3 filtering** — each term becomes a filter on candidate detail responses; break any term → reject the candidate.
- **Phase 5 creation plan** — the sequence must end with every term green; may need follow-up calls (e.g. enable a KB that was created Disabled by default).
- **Phase 6 verification** — re-read each term from detail APIs before declaring the sample ready; include it in step-1 mental simulation.

### Common failures this prevents

- Table document inside a Disabled KB → Edit/Delete buttons greyed (container-enabled gate).
- Workflow in Published lifecycle → strategy edit rejected (lifecycle gate).
- Doc with running import → chunk editor shows "正在导入" banner, all inputs disabled (transient busy gate).
- KB with `administrators` not including current uid → write buttons rendered but hidden (permission gate).
- Empty table document → row-level edit icon not rendered per row (row-count gate).

## Failure-Trigger & Error-Marker Research (For Exception / Negative-Path Cases)

Exception-path rows (Sub-pattern 1 "触发失败/超时", Sub-pattern 3 "应给出明确提示") require a dedicated research pass **before** classifying the row as `manual-prep / failure-injection` or "not UI-testable". The rule is: **do not default to "needs fault injection" — the product almost always has deterministic in-scope triggers for its error surfaces; find them first.**

### Failure-trigger research — how does this error surface actually appear?

For a row that asks for a "failure / timeout / error" UI, answer: **what concrete, reproducible action in the real product produces this error UI today?** Inspect, in order:

1. **Page's error handlers** — find the hook powering the page (`useRetrieve*`, `useRun*`, `useImport*`). Read its `onError` / `catch` blocks. Each branch implies a concrete upstream condition.
2. **Backend handler for the action** — if accessible in the repo, the handler's early-return branches enumerate the failure reasons: empty dataset, disabled resource, size limit, permission denial, invalid payload, dependency failure, etc.
3. **Shared error-code map** — search for things like `errorCodeMap`, `BUSINESS_CODE`, `ErrorCode`. Each entry ties a backend code to a UI message; each implies a trigger.
4. **PRD / spec doc for this feature** — grep for `错误 / 异常 / 失败 / 超时 / 限制 / 上限 / 下限 / 禁用`. The PRD usually enumerates the errors the product explicitly handles.
5. **Product-level limits in config / constants** — file size caps, token caps, row caps, expiration windows. Hitting them produces deterministic errors.
6. **Upstream-state errors** — e.g. retrieval on a KB with all content `Disabled` or `Failed`; run on a workflow whose node lacks required config. These produce the error UI without any fault injection.
7. **Permission-denied paths** — calls rejected by backend authz usually render a specific Toast. If the trigger needs a non-default account, it becomes manual-prep for the *account*, not the *error injection* — a different category.
8. **Ingestion failure paths** — imports that land in `Failed` state; any downstream operation on such items renders the error.

Record, for **each trigger you found**:

- trigger name (short label, e.g. `all-content-disabled`, `query-length-over-limit`, `unauthorized-user`, `import-malformed-csv`)
- the concrete action that produces it (input value, prior state, permission used)
- the UI effect the product renders (Toast text / ErrorState component / field error)
- the code path that proves the above (hook file : line, backend handler : line, i18n key, errorCodeMap entry)
- classify each trigger's data feasibility (`auto` / `manual-prep+category` / `needs refinement`)

### Error-marker research — what exactly does the error look like in the UI?

For a row that asserts "明确的错误提示" or "友好的提示", find the **literal positive marker** so the test has something concrete to assert on. Inspect:

1. `Toast.error('...')` / `Message.error('...')` / `Notification.error(...)` call sites in the hook or handler
2. `<ErrorState title="..." description="..." />` / `<EmptyState>` usages in the page
3. i18n keys: the call is often `t('error.xxx.yyy')`; resolve the key to its literal string in `locales/**` / `messages/**`
4. Shared error-boundary fallback UI used by this route
5. Error-code → message maps (so a specific backend code maps to a specific literal the UI shows)
6. Field-level error props: `errorMessage`, `validateStatus`, form `rules`

Record, for **each marker you found**:

- the literal text (in every locale the product supports, or at least the primary one)
- the stable DOM hook an executor can match on (component name / class / test-id / role + accessible name)
- which trigger from the failure-trigger list above produces it

### Proof standard (for escalation)

A row is only allowed to escalate to `manual-prep / failure-injection` after this research pass produces **no** in-scope trigger, **and** the Manual-Prep Request entry lists the specific hooks / handlers / error-code maps that were inspected and found empty. "I couldn't figure out how to fail it" is not acceptable as a stop reason; evidence of the specific inspection is.

Similarly, a row is only allowed to be declared "not UI-testable" after this research pass produces **no** marker candidate, **with** the inspected components / i18n keys cited.

### Sedimentation of error-surface knowledge

When a useful trigger / marker pair is found, add a short entry to the knowledge doc under an **Error Surfaces** heading. Shape:

```markdown
### Error Surface — <feature name>

- **UI entry**: <page URL / component>
- **Trigger 1 — <label>**:
  - action: <input + prior state>
  - data feasibility: <auto / manual-prep+category>
  - UI marker: <literal text + DOM hook>
  - code: <hook:line, i18n key>
- **Trigger 2 — <label>**: ... (same shape)
- **Markers index** (literal → component): `暂无可用内容` → `<ErrorState>` in `...`
```

This makes the next exception-case run across the same feature a Phase 2 **HIT** instead of another research pass.

## Common Mistakes (Reject These Findings)

- Assuming an enum value from the variable name (`Status.DISABLED` may not be `"disabled"`)
- Assuming ownership logic from a field name without finding the actual frontend check
- Assuming a create API produces a fully usable sample without checking detail API afterwards
- Assuming the page URL only needs the top-level object ID when route includes a child segment
- Treating IDL field optionality as runtime requiredness without checking server validation

## Proof Standard

A fact is strong enough to write into a knowledge doc only if backed by one of:

- a code path traced from page → hook → API wrapper → endpoint
- generated typings or IDL schema
- a successful live API response that matches the code

If code and runtime disagree, **record the runtime behavior** as the truth and add a `Caveat` line noting the discrepancy.

## Knowledge Sedimentation Template

After research succeeds, write (or update) an entry in the relevant knowledge doc — typically `business_knowledge/<platform>/modules/<module>/data_queries.md`. Use this exact shape:

````markdown
### N. <Short title, e.g. "查询某个租户下的可编辑 Advanced workflow">

- **目标 / Use case**: <when to use this query/create, written as a test-data requirement>
- **Entity**: <primary entity + parent/child relations>
- **API**:
  - `<METHOD> <path>` — <one-line purpose>
- **前端代码依据**:
  - `<repo-relative path 1>`
  - `<repo-relative path 2>`
- **Route provenance**:
  - app: `<app name>`
  - basename: `<basename from router or entry config>`
  - route: `<route path from router/page config>`
  - final URL pattern: `<host><basename><route>?<query>`
  - source: `<repo-relative router/page-entry path>`
- **最小入参**:
  - `<field>` — `<type>` — `<value rule, e.g. "current user uid">`
- **关键出参字段**:
  - `<field>` — `<meaning>`
- **Enum / 状态映射**:
  - `<enum value>` → `<UI label or behavior>` (源: `<file:line or component>`)
- **Permission rule**:
  - <e.g. `administrators` 包含当前 uid 即视为可编辑>
- **Enable chain (per mutating action)**:
  - `<action label>`:
    - `<entity>.<field> == <value>` (source: `<file:line>`)
    - `currentUid ∈ <entity>.<ownerField>` (source: `<file:line>`)
    - `!<entity>.<transient-busy-flag>` (source: `<file:line>`)
    - ... (one positive term per line, each with a code citation)
- **选择规则 (Phase 3)**:
  - <e.g. "优先选 type=2 且当前 uid 在 administrators 内的样本；每个 enable-chain 项在 list/detail 响应中都为 true">
- **创建规则 (Phase 5/6, 仅在需要造数时)**:
  - <minimum payload, side effects, follow-up calls needed — include follow-ups that flip any enable-chain term green if the default create leaves it false>
- **Caveat / 运行时差异**:
  - <known gotchas, e.g. "create 成功后会自动带一个 v1 DEVELOP strategy，无需再调 strategy/create">
- **curl 模板**:
```bash
curl '<full url>' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'permission-ns-id: <space>' \
  -H "x-jwt-token: $JWT" \
  -b "$COOKIE" \
  --data-raw '<minimal payload with placeholders>'
```
````

Notes when writing the entry:

- Redact concrete tokens / cookies / personal uids into placeholders (`$JWT`, `$COOKIE`, `<current_user_uid>`).
- Use repo-relative paths for code references so future readers can jump directly.
- Prefer **separate entries for query vs create** — they are used at different phases and one may exist without the other.
- If a finding contradicts an existing entry, update that entry rather than appending a new one, and add a `Caveat` line explaining the change.

## Handing Off To The Next Phase

After sedimenting:

1. Re-run **Phase 3** for that requirement using the new knowledge entry — query first.
2. Only if no sample is found, escalate to **Phase 5** (Creation Plan + user confirmation).

The next time this requirement appears (in this run or a future run), Phase 2 should hit the entry directly and skip back to Phase 3.
