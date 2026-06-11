---
name: test-data-research-and-seeding
description: Use this skill when the user wants to derive concrete per-case data requirements from a test analysis doc, look up business data-query knowledge to find reusable samples (query-first, create-minimum), sediment new query/seeding knowledge from the frontend codebase when knowledge is missing, and only create samples after the user explicitly confirms a creation plan. Then backfill exact IDs and page URLs into the analysis doc.
---

# Test Data Research And Seeding

Use this skill for requests like:

- "根据测试分析补页面 URL / 样本 ID"
- "按测试要求找一份可用数据，找不到再造，造之前先报给我确认"
- "先查代码仓库沉淀取数知识，再去取数"
- "用我给的 curl 鉴权调接口造数"
- "把测试分析里每个用例的前置数据补齐"

## Operating Principle (Read First)

This skill is an append/backfill pass over an existing `test_analysis.md`. It must not regenerate the coverage matrix from PRD/spec, overwrite the analysis document, or delete rows to make execution easier. Executability is a status and backfill target, not a coverage gate: unresolved rows stay in the analysis and later become manual-review cases in `case.md`. If a missing verification point is discovered, hand it back to `prd2case-web` Stage-1 to add the row, then rerun this skill on the updated analysis.

The job is always:

1. From the test analysis doc, derive a per-case **concrete data requirement**.
2. **Classify feasibility** — auto-feasible / needs-manual-prep / unknown. Manual-prep cases are escalated immediately, not researched, and remain part of the downstream `case.md` coverage.
3. For auto-feasible rows, reuse business knowledge to **query existing samples first**.
4. If knowledge is missing, **inspect the frontend code, sediment the knowledge, then query**.
5. Only when no usable sample exists for an `auto` row, **enter Gate B: draft a creation plan and get user approval before executing it**.
6. After approved create, verify with list/detail APIs and backfill **exact IDs/URLs** into the analysis doc and any new facts into the knowledge doc.
7. Only after a row is proven non-automatable, the user rejects Gate B, or approved creation/verification fails within budget, **emit a Manual-Prep Request and stop searching**.

Hard rules:

- **Reuse > Create.** Never create when an existing sample satisfies the requirement. This rule is **strict, not aspirational**: if the user (or upstream `test_analysis.md` / spec / prior `case.md`) provides stable sample IDs / URLs / accounts / fixtures, you **must** plug those into the row and mark it `CLOSED with provided stable sample`. Defaulting to "create a fresh runtime KB / document / workflow" when a usable sample is already in hand is a Reuse-rule violation, not a creative choice.
- **User-provided stable sample = CLOSED, not BLOCKED.** When the user has already supplied an executable sample (e.g. "use KB `kb_xxx` and document `doc_yyy`"), the row's status is `CLOSED — provided stable sample: <ref>`, **not** `BLOCKED — needs manual prep`. Manual-Prep / BLOCKED is reserved for rows where (a) no automatable path exists *and* the user has *not* given a usable sample, or (b) the path needs interactive auth / out-of-band setup. Misclassifying a user-provided sample row as BLOCKED throws away coverage that was already fully resolved.
- **No silent creation.** Any creation step requires explicit Gate B confirmation, listing entity, API, payload, ownership, reason, and verification plan.
- **No premature Manual-Prep for auto rows.** "No reusable positive sample found" is a Gate B signal, not a Gate C signal. Do not mark an `auto` row `manual-prep` until you have either proven no automatable create path exists, the user rejects the Gate B plan, or approved creation/verification fails within budget.
- **Stateful sample isolation.** Every `stateful` row (verbs like `禁用 / 启用 / 删除 / 编辑 / 创建 / 切换 / 修改`) gets its **own dedicated sample id**. Do **not** reuse a single "current-round temporary KB / document / workflow" across multiple stateful scenarios — that creates ordering dependencies and dirty state, and a failure in one row can poison every row downstream of it. When the user provides distinct sample IDs per state-flow scenario, the backfill must preserve that 1-sample-per-scenario mapping; when creation is needed (Gate B), the creation plan must enumerate one sample per stateful row.
- **Fill, do not delete.** Rows that come in from upstream (PRD / `test_analysis.md` / earlier `case.md`) are the unit of coverage. If a row's data is not yet resolved, the right action is to **keep the row and continue Phase 2–6 to fill it in**, not to remove the row from `test_analysis.md` / `case.md`. The legitimate non-fill outcomes are status annotations, not coverage deletion: (a) Gate C → row stays put, marked `BLOCKED — needs manual prep` with original tags preserved; (b) Gate D → row is refined into child rows only after user approval, with original tags and parent provenance preserved; (c) the row is genuinely not testable at this layer (worked example: silent-failure row with no UI marker found by the Phase 4 pass) and the user explicitly approves excluding it with the inspected code paths recorded as evidence. "Looks hard / I couldn't find a sample in 1 query" is **not** in this list.
- **Preserve analysis ids.** Every upstream `test_analysis.md` row must keep its stable `分析ID` through TDRS. Backfill status, URLs, samples, and evidence in place; do not overwrite or regenerate ids. If a user-approved split is required, create new child ids that retain parent provenance (for example `WEB-012a`, `WEB-012b`) and ensure the parent no longer counts as a runnable verification row.
- **No guessed knowledge.** Every business fact written to a knowledge doc must be backed by code, generated typings, or a successful live API response.
- **No guessed page URLs.** Direct page URLs must be derived from the target app's real router / basename or an existing page-entry config. Do not concatenate app name + feature path by intuition. In micro-frontend repos, app name, basename, and business route often overlap or diverge; a CLOSED row needs route provenance before URL backfill.
- **Account for page initialization query params.** Route provenance proves the path; it does not prove the page can initialize from that URL. Before marking a row CLOSED, identify which query params are stable business context (for example tenant, owner, target id, filter enum) and which are dynamic initialization params (for example `startTime` / `endTime` defaulted from current time). Stable context params belong in the direct URL when they select the target data. Dynamic params must be recorded as an initialization strategy: either execution-time generation, or a deliberately chosen stable range that covers the verified sample. Do not blindly copy every final browser URL param into `case.md`, and do not omit dynamic params when the page white-screens without them.
- **No placeholders.** Final docs carry concrete executable references: entry point, data reference, initial state, observable anchor, or an explicit BLOCKED / HANDOFF marker. A BLOCKED / manual-prep marker is not a reason to omit the row from `case.md`.
- **No placeholder-first case generation.** Do not generate `case.md` with fake URLs / `<id>` / "correct entry" placeholders and plan to backfill later. Data research and backfill happen before case generation.
- **Historical sample search is mandatory.** Before querying or creating, search same-repo `specs/**`, prior `test_analysis.md`, prior `case.md`, `e2e-test-cases.md`, and feature-adjacent docs for reusable execution contexts, data references, fixtures, accounts, and known-good entry points.
- **No thrashing.** When a row is manual-prep-only, or a post-query phase hits its attempt budget, stop and ask. Do not loop on retries hoping a different filter will reveal the missing data.
- **Gate by evidence, not success.** Stage-2 completion means every `分析ID` has a terminal TDRS decision with evidence, not that every row found an executable sample. `CLOSED` needs live API / provided sample evidence plus backfilled URL. `BLOCKED` / `manual-prep` / `skip` need a concrete reason. `UNVERIFIED` is allowed only with attempted query / auth / API failure evidence. Empty conservative classification is not a terminal decision.
- **Keep the analysis table readable.** Prefer one compact `TDRS证据` cell over many query columns. Use semicolon-separated `key=value` entries: `数据要求=...; 查数API=...; 查数参数=...; 查数结果=...; 回填URL=...; 裁决证据=...; 查询次数=1; 造数次数=0`. Downstream `tdrs_gate.py` parses this compact form. Only expand into separate columns when a specific project asks for it.
- **Ask before terminal classification when auth/API is missing.** "No live sample data provided" / "用户未提供样本" is not a Gate C reason. If you lack auth, cookie, token, owner scope, or list/detail API curl, ask the user for that material first. Only after the user explicitly declines, says they cannot provide it, confirms no permission, or after a real API attempt proves the blocker, may you mark `BLOCKED`, `manual-prep`, or `UNVERIFIED`. Record the explicit outcome in `裁决证据` (for example: "已向用户请求鉴权 curl 和 owner scope，用户明确无法提供"). A bare "已请求材料" without user outcome is not terminal evidence.
- `查数结果=缺少鉴权/API 信息` by itself is not an API attempt. Pair it with explicit user-request evidence, or replace it with a real attempted request result (`curl ...`, `GET /api/...`, `HTTP 403`, `API 500`, etc.).
- **Respect finite budgets.** Default per-row budget is at most 2 live query attempts and 1 user-confirmed creation attempt. After that, record the terminal decision and evidence instead of looping. Downstream `tdrs_gate.py` enforces this before `case.md` generation.
- **No runtime self-seeding shortcut.** Designing the test data so the case "creates it at execution time" (temporary KBs, inline text content, ad-hoc CSV fixtures, etc.) is **not** an acceptable substitute for Phase 1–7.5. Every `auto` row must end with a real internal ID / direct URL backfilled into `test_analysis.md`, sourced from a live query or an explicitly user-approved Gate B creation. If you cannot do that, the row is `manual-prep` (Gate C), not "runtime self-seeded".
- **Strict data-prep order (no skipping levels).** For every row, the order is: (1) code analysis to sediment query knowledge into `business_knowledge/**/data_queries.md`; (2) live API queries against that knowledge to find a reusable sample (or direct adoption when the user has already provided one — mark `CLOSED — provided stable sample`); (3) only if no reusable sample is found, draft a Gate B creation plan and wait for explicit user confirmation; (4) Gate C / Manual-Prep Request when the row is non-automatable, the user rejects Gate B, or approved creation/verification fails within budget. Skipping straight to Gate B without code research + query, or creating samples without user confirmation, is a rule violation.
- **Phase 3 means calling the API.** Phase 3 query is a `curl` (or equivalent HTTP call) against the platform's list/detail API, using the auth material the user has already provided (`.env` SSO fields, the curl snippet pasted into chat, etc.). Grep over `specs/**` / sibling test docs is a Phase 0 historical-sample lookup; its results are unverified hints until a live API call confirms the sample currently satisfies the row's requirement. Do not mark a row CLOSED, and do not escalate to Gate B / Manual-Prep, without that live API call.
- **Pre-condition data must not be deferred to execution time.** All data a case's `前置条件` depends on must be discovered or Gate-B-created **during this skill** and backfilled as real internal IDs / direct URLs into `test_analysis.md`. The downstream `case.md` operation steps must start from data already in place; they must **not** include "create the prerequisite first, then assert" steps. The only exception is when the case's verification theme itself *is* the creation action — in that case, creation belongs in the operation steps by design, not as a workaround for missing pre-condition data.
- **No partial-execution claims.** Do not declare an individual row `CLOSED` unless **all** of the following are done: (a) per-test-point data requirements written, (b) code research with knowledge sedimented into `business_knowledge/**/data_queries.md` when missing, including route provenance and initialization-param handling for every direct page URL, (c) live API calls performed where auth / environment are available (query first; Gate B-confirmed creation second), (d) real internal IDs and direct URLs backfilled, replacing every placeholder pre-condition. If auth, owner scope, fault injection, large-volume data, or another manual-only dependency blocks closure, mark the row `BLOCKED` / `manual-prep` with evidence and keep it in scope.

Read these references on demand:

- Per-case requirement extraction: [references/analysis-to-data-requirements.md](references/analysis-to-data-requirements.md)
- Frontend code research and knowledge sedimentation: [references/code-and-api-research.md](references/code-and-api-research.md)
- Authenticated query/create curls, creation-confirmation template, post-create verification, backfill: [references/seeding-and-backfill.md](references/seeding-and-backfill.md)

## When To Use

Use this skill when the user provides or references:

- a test analysis doc / test case table
- a page URL checklist that needs real IDs
- a data requirement list
- an auth curl and asks you to query or create samples

Do not use this skill for pure UI work, pure code implementation, or pure test execution that does not involve data discovery or seeding.

## Inputs To Collect

Before changing anything, identify:

- target analysis or test doc (path, sections, rows)
- the **exact rows/scenarios** that need real data
- the relevant frontend code area
- sibling specs / historical test docs that may already contain reusable execution context or data for the same feature or platform
- the latest auth material (`x-jwt-token`, cookies, `permission-ns-id`, current user uid)
- whether each scenario is read-only or write-path
- existing business knowledge docs to consult (e.g. `business_knowledge/**`, module-level `data_queries.md`)

Reuse the latest auth the user provided. Never guess auth. The auth in `.env` (or pasted curl) is what **this skill** uses to call the API in Phase 3 — it is not a config that only TTAT / Playwright MCP consumes.

## Manual-Prep Categories (Recognize Early, Do Not Thrash)

Some requirements **cannot** be reliably resolved by querying or by hitting create APIs in the codebase. They depend on out-of-band setup that only a human can do. Recognize them in Phase 1 and route them straight to Phase 7.5 (Manual-Prep Request).

Default manual-prep categories:

- **Different user account** — e.g. a non-admin / viewer / member user in the same tenant. The codebase has no API to mint accounts; reuse may exist but only the user knows which account is safe to share.
- **Missing auth / owner scope** — e.g. no usable SSO/cookie/curl for live API calls, or the scenario requires a specific owner relationship such as strategy-only owner that the current account cannot prove or create safely.
- **External ingredient needs ingestion** — e.g. Lark Doc / Lark Sheet / Feishu / Notion / external HTTP file URLs that must be *imported* into the target system to become a real sample (see **Ingredient vs Sample** below). A URL alone is raw material, not a usable sample. The ingestion call itself may succeed, fail, or require interactive auth.
- **Ingestion-time interactive auth** — the ingestion API uses a flow that opens a QR code / OAuth consent / OTP / external browser step. No agent-side retry will succeed. Must be flagged up front and either solved by a human session, replaced by a different sample type, or moved to a reduced-scope / excluded row with evidence.
- **Specific external content shape** — e.g. "a Lark Doc that contains an embedded table", "a CSV with ≥ N rows and a specific header layout". Even when the integration works, the *content* must be prepared by a human. This is usually combined with the ingredient category.
- **Transient runtime states** — e.g. `Processing` / `Pending` / `Uploading` states that exist only during a short window. These cannot be deterministically held; either the user pauses a real run or the row is reduced / excluded with evidence. Do not try to "find" a long-lived `Processing` sample.
- **External-failure injection** — e.g. "ByteRAG timeout / network failure". Requires backend-side fault injection or a controlled environment, not a data sample.
- **Third-party credentials / tokens** — e.g. OAuth-backed downstream services where the auth surface is outside the current tenant.
- **Large-volume or special-shape samples** — e.g. thousands of rows, oversized files, or quota-sensitive data that cannot be safely queried or created within the current environment. Keep the row and mark the concrete missing sample requirement.

Treat any row matching one of these patterns as **needs-manual-prep** at Phase 1. Skip Phases 2–6 for that row and produce a **Manual-Prep Request** in Phase 7.5 (template in [references/seeding-and-backfill.md](references/seeding-and-backfill.md)).

When in doubt about whether a row is manual-prep-only, do **one** quick code-research pass (Phase 4) to check whether an automatable create API exists. If it does not, classify as manual-prep and stop.

## Ingredient vs Sample (Do Not Confuse Them)

The most dangerous silent failure in this skill: recording an **ingredient** as if it were the **sample** the test needs.

Definitions:

- **Ingredient** — raw external material: a URL, a file, an access token, an account handle. Provided by the user or sourced externally. By itself, it does **not** satisfy any test row's data requirement.
- **Sample** — an entity *inside the target system* that the test UI can read and act on. Identified by the system's internal id (e.g. `documentId`, `workflowId`), reachable via the system's list/detail APIs, and observable in the test's target URL.

Every ingredient-bearing row has **three** sub-steps that all must succeed, or the row is NOT closed:

1. **Ingredient obtained** — the user provided the URL/file/token (Manual-Prep Request item).
2. **Ingestion executed** — an API call inside the target system imported the ingredient and produced an internal sample with its own id (e.g. `POST /api/v1/knowledge_base/document/import_from_lark` returning a `documentId`).
3. **Internal sample verified** — the detail API for the containing entity shows the ingested sample (e.g. `KB detail` lists the `documentId` and it is in a post-ingestion state the test can exercise; not `Processing` / `Failed`).

Rules:

- **Do not mark a row CLOSED on ingredient availability alone.** "User gave me a Lark Doc URL" is not a closed row. The ingestion must have succeeded and the internal sample must have been verified.
- **Record the internal id, not the ingredient URL, in Phase 7.1.** The `前置条件` cell must reference `document <documentId>` and the test's real page URL, not the source Lark URL. The source URL can appear as a provenance note in the page-level table only.
- **If ingestion has interactive auth** (QR code, OAuth consent, OTP, external browser step), classify the row as *ingestion-time interactive auth* in Phase 1 and route to Phase 7.5. Do not attempt the ingestion from the agent — it will hang or fail in a way the downstream executor cannot recover from. Flag it up front.
- **If ingestion is possible non-interactively** (token-based, no consent needed), it is an automatable step and must appear in the Creation Plan (Phase 5) as an explicit call with expected response and verification.

## Attempt Budget (Hard Stop)

For any single requirement, cap the work as follows. Hitting the **query** cap on an `auto` row means "stop querying and move to Gate B", not "mark manual-prep". Manual-Prep Request is only for rows that are manual-only, have no automatable create path, are rejected by the user at Gate B, or fail approved create/verify within budget.

- **Phase 3 (query):** at most **2 list-API calls with distinct filter strategies**. If neither finds a usable candidate for an `auto` row, stop querying and proceed to Phase 4/5 to prepare Gate B. Do **not** emit Manual-Prep merely because reuse failed. The 2-call cap is on **live API calls**; grep / sibling-spec lookups don't count and don't substitute for the call.
- **Phase 4 (code research):** at most **one focused pass** through routes → hooks → API wrapper → typings. If the create/update path is still unclear, Gate C may emit Manual-Prep with the specific missing fact; if the path is clear, continue to Gate B.
- **Phase 5/6 (create):** at most **2 create attempts** for the same object (e.g. one with original payload, one with payload corrected per server-side validation message). A third failure is automatic escalation.
- **Total per requirement:** if more than ~10 minutes of agent effort have gone in without either (a) a reusable sample, (b) a complete Gate B creation plan awaiting user confirmation, or (c) a proven manual-only blocker, stop and escalate with the current evidence.

Escalation after Gate C means: emit a Manual-Prep Request entry for that row and move on to the next row. Do not block other rows on a stuck one. **Do not call the Phase 3 no-sample result "escalation" for `auto` rows**; that path is Gate B.

## Workflow

The workflow is intentionally linear. Do not skip phases. The non-negotiable gates are:

- **Gate A (Knowledge → Code):** if business knowledge is missing/incomplete, sediment it from code before touching APIs.
- **Gate B (Query → Create):** if an `auto` row has no reusable sample after the query/code-research path, present a creation plan and wait for user approval before executing. Gate B is mandatory before Manual-Prep for positive samples that the system can create.
- **Gate C (Stop → Ask):** if a row is manual-prep-only, has no automatable create path, has its Gate B plan rejected, or approved creation/verification fails within budget, stop and emit a Manual-Prep Request. No silent grinding.
- **Gate D (Ambiguity → Refine):** if operation steps are not concrete enough to verify, propose a Case Refinement and wait for user approval before doing data prep on that row.

### Phase 1. Build the per-case data requirement table (with Feasibility)

Read the test analysis. **Read both the `前置条件` cell AND the `操作步骤` cell of each row** — the operation steps frequently reveal the *initial state* the sample must be in, which the prerequisites text alone may not capture.

For every row that needs real data, produce one entry of:

- target page or operation
- backing entity (and any required child entity/version)
- **Initial state** the sample must be in *before step 1 runs* (e.g. `Available` for a "disable then observe" case, even if the prerequisites prose mentions both Available and Disabled)
- required ownership / permission for current user
- shape / volume requirement (rows, chunks, items)
- scenario type: read-only / write / config / preview / multi-state
- **Stateful flag** — `stateful` if the operation steps mutate the sample (verbs like `禁用 / 启用 / 删除 / 编辑 / 创建 / 切换 / 修改`), `read-only` otherwise
- whether multiple distinct samples are required (e.g. one Available + one Disabled in the same scenario)
- **Operational preconditions (ambient gating chain)** — the conditions around the sample that the UI uses to enable/disable the *specific action* the test performs. These are distinct from "initial state of the target sample" and from "structural invariants"; they are the **enable chain** from the outermost container down to the action button (see below).
- **Feasibility** — `auto` / `manual-prep` / `unknown` (decide using the Manual-Prep Categories above)

#### Initial-state extraction rules

- The prerequisites cell often describes the **post-setup** world ("已有一个引用…随后将该 KB 禁用"). That includes setup actions the *test* will perform. Do not encode the post-action state as the sample's required state.
- Walk the operation steps in order. The state required for **step 1** is the initial state. Anything the steps mutate is *not* a sample requirement — it is what the test does to the sample.
- Worked example (real failure): for a row whose steps are `1. 禁用该 KB  2. 运行 Workflow 检索`, the sample's initial state is `Available` (so step 1 has something to disable), even though the prerequisites prose mentions disabling. Picking a Disabled KB here makes step 1 a no-op and breaks the assertion.
- For multi-sample rows, each sample has its own initial state — record them separately (e.g. `Owned sample: Available`; `Not-owned sample: Available`).

#### Operational preconditions — the ambient gating chain

The sample's own state is not enough. A UI action button is usually enabled by a **chain of conditions** that cascades top-down: the outer container must be in an enabled state → the intermediate parent must be in an enabled state → the sample row must be in an enabled state → the user must have permission → (only then) the action button becomes clickable. Break **any** link in the chain and the button greys out, regardless of the sample's own state.

For every `stateful` / write-type row, explicitly record the ambient gating chain as **operational preconditions**, not just as a hope. The sample the skill picks / creates must satisfy every link in the chain.

Typical chain shapes (target-system examples, generalizable):

- **Container-enabled gate**: `parent KB is Available (not Disabled)` → otherwise all child document edit/delete/chunk-config buttons are disabled, regardless of the document's own state.
- **Resource-state gate**: `document is Available (not Failed / Processing / Disabled)` → otherwise table-row edit / chunk viewer / retrieval testing on that document is disabled.
- **Ownership/permission gate**: `current user ∈ administrators of parent KB` → otherwise write buttons render but are hidden or disabled.
- **Lifecycle gate**: `workflow is DEVELOP (not Published / Archived)` → otherwise strategy-update is rejected; `KB content is not locked by a running import job` → otherwise edit is temporarily disabled.
- **Cross-reference gate**: `resource is not currently referenced by a running export / training job` → otherwise delete is blocked.

Each recorded precondition should have the form:

```text
<container or resource> must be <state> — because <code location or UI observation> disables <the specific action the test performs>
```

Do not merge preconditions into the "initial state" field. Initial state describes the **sample under test**; preconditions describe the **ambient chain around it**. They fail differently: a wrong initial state typically makes step 1 a no-op (silent false-pass); a broken precondition typically greys out step 1 entirely (the executor reports "can't click button"). Both must be checked separately in Phase 3 filtering and Phase 6 verification.

Worked example (real failure): row `编辑表格 Row / 单次删除 10 行 / 单次删除 11 行`. The skill picked a table document inside a **Disabled** KB. The document itself was Available. But the KB's Disabled state cascades down: the detail page rendered the table in read-only mode, with the Edit / Delete / checkbox column all disabled. The test failed at step 1 ("click Edit on a row") because the Edit button was grey. Initial state was fine; the **container-enabled gate was broken**. The row's operational preconditions were never captured, so Phase 3 did not reject the candidate and Phase 6 did not catch it.

#### Scenario concreteness check (do not skip)

For every row, confirm each operation step is concrete enough that an executor agent can perform it and a verifier can assert on the result. Vague steps produce vague data requirements and hidden failures.

A step is **concrete** when it specifies:

- which UI control is used (button / dropdown / search input / toggle / modal)
- what the user types or selects (literal value, or "the prepared Available KB id/name")
- what observable effect proves the step happened (toast message / row visible / status changed)
- **and** the observable is actually exposed by the UI the test targets — this is the *observable-anchor* check (see below)

A step is **vague** when it relies on words like `选择 / 操作 / 触发 / 执行 / 查看 / 正常返回` without naming the control or the observable effect.

#### Observable-anchor check

Concrete language alone is not enough. The *observable* the assertion hangs on must be a thing the UI (or a DOM/API hook the test can read) actually surfaces. An assertion like "结果仅来自 Available 内容" is only verifiable if the Retrieval Testing UI exposes per-result source state — either a visible status tag per result card, a returned `document_id` the test can cross-look-up, or an API hook the test can inspect.

When you suspect the assertion targets an attribute the UI may not expose, do a targeted Phase 4 pass on the result-renderer component before finalizing Phase 1:

- find where each result card is rendered
- confirm which fields (state, source, documentId) are in the rendered DOM, a tooltip, or a dev-accessible data attribute
- if none, the assertion is **unverifiable as stated** — escalate with a Case Refinement Proposal that either (a) rewrites the assertion to an anchor the UI does expose, (b) adds a complementary API check the test can perform alongside the UI step, or (c) marks the row as manual-prep with category *assertion not observable from UI*.

Do not let a case coast past Phase 1 on an observable nobody has confirmed exists.

When a row has vague steps, do **not** start data prep on it. Instead:

1. Do a **targeted Phase 4 pass** on the UI code for that page to identify the actual controls (e.g. "the KB selector is a `Select` with async search; Disabled KBs appear grey and cannot be picked").
2. Draft a **Case Refinement Proposal** that rewrites the vague steps into concrete ones, citing the code you found. Example:
   - vague: `Disabled KB 不在可选列表或明确不可选`
   - concrete: `在 RAG 节点的 KB 选择器搜索框输入 Disabled KB 的 name；断言下拉项存在但置灰、点击无效。再搜索 Available KB 的 name；断言下拉项可选中，选中后保存成功。`
3. Present the proposal to the user and **wait for approval** before continuing. This is Gate D (Ambiguity Gate).
4. Only after the row's steps are concrete does Phase 1 finalize its data requirement for that row.

If the user declines refinement or says "keep it vague", treat the row as `manual-prep` (category: *ambiguous case — needs human judgment at execution time*) and route to Phase 7.5.

Output a structured per-case table (see template in [references/analysis-to-data-requirements.md](references/analysis-to-data-requirements.md)). Do not proceed until each requirement is concrete; replace fuzzy phrasing like "some sample exists" with explicit constraints.

#### Exception / negative-path cases — classify the sub-pattern before rewriting

Test analysis docs routinely contain **exception / negative-path cases** whose steps or assertions are inherently not executable as written — not because the author was sloppy, but because the case is describing an *outcome* (error UI, absence, robustness) without specifying the *trigger* or the *observable* that would verify it. These cases need a different rewrite discipline from ordinary vague cases. Do not just try to "make them concrete" — first classify which of the four sub-patterns you are looking at, because each has a different fix.

Detection signals (one or more usually present):

- trigger words without mechanism: `触发超时 / 触发失败 / 模拟异常 / 出错时 / 遇到问题时`
- negative-existence words: `不出现 / 不会作为 / 不展示 / 不可选中 / 不召回 / 不参与`
- silent-failure language: `不要静默失败 / 不能 crash / 应给出明确提示 / 保持稳定 / 体验友好`
- boundary/illegal-input without enumeration: `输入非法值 / 超出范围 / 异常输入 / 错误格式`
- generic robustness claims: `系统应稳定 / 兜底正确 / 容错 / 降级合理`

Once detected, classify into one of four sub-patterns and apply its rewrite template:

**Sub-pattern 1 — Failure-trigger not specified** (e.g. "触发超时后页面显示错误", "遇到网络错误时降级", "检索失败时报错")

- Core problem: the test describes the effect (an error UI) without naming the trigger that produces it.
- Anti-pattern to avoid: **do not default to `manual-prep / failure-injection`.** Most product-level errors are produced by deterministic, in-scope triggers; classifying them as "needs fault injection" without looking is how real coverage gets dropped.
- Mandatory **failure-trigger research pass** (Phase 4) before any escalation. Look in the UI and backend code + PRD for how the error surface is reachable without fault injection. Concrete search targets:
  1. Upstream state that already produces the error — e.g. "retrieval on a KB whose *all* documents are `Disabled` / `Failed`" may deterministically hit the empty-or-error branch without any injection. Read the retrieval controller / backend handler for the conditions under which it returns an error code.
  2. Permissioned action — e.g. "calling the run endpoint with a token lacking the required role" produces a `403` error surface that the UI already renders.
  3. Product-level size / count limits — e.g. "uploading a file at max-size + 1", "querying with > N tokens", "referencing > M KBs" — these usually emit a specific error the UI shows.
  4. Deliberately malformed but UI-reachable input — long strings, unsupported file types, unreachable Lark URL (404-able) — the UI's own validation path renders an error.
  5. Ingestion-time failure paths — e.g. "import a malformed CSV" produces a document stuck in `Failed`; any downstream operation that touches it hits the error UI.
  6. API-client error handlers in the frontend — search for `onError` / `catch` / error toast renderers in the hook that powers the page. Each handler implies a concrete upstream condition; the conditions are documentable and testable.
  7. PRD / spec doc language — search the spec for "错误场景 / 错误态 / 错误提示 / 异常" and the specific feature. The PRD usually lists the concrete triggers the product claims to handle.
- For every trigger found, write the test step **explicitly**, naming the input and how the trigger is produced. Example rewrites for "检索失败时报错":
  - `在 Retrieval Testing 对 KB <K-all-disabled> 输入查询 "hello"；断言 <ErrorState> 组件出现，文案包含 "暂无可用内容"` (trigger = all-Disabled KB — auto, stable data)
  - `在 Retrieval Testing 对 KB <K> 输入长度为 10001 字符的查询；断言字段级错误 "查询长度不能超过 10000"` (trigger = length limit — auto)
  - `在 Retrieval Testing 对 KB <K> 使用未授权账号请求；断言 Toast "无权限"` (trigger = permission — requires different-account manual-prep, but trigger is concrete)
- After the research pass, **enumerate every trigger you found as its own child case**, each with concrete data and a concrete observable. Write them into the analysis doc. Each child is then routed normally by Phase 1.
- Only if the research pass finds **no in-scope trigger** for the error surface (e.g. the error is genuinely only reachable via a backend 5xx or a network partition) does the case become `manual-prep / failure-injection` — and at that point, the Manual-Prep Request must state *which* error surface was not reachable and what was tried, so the user can decide exclude / fault-injection.
- Research-pass stop condition: 1 focused Phase 4 pass across frontend error-handling code + a grep of the PRD for "错误" language for this feature. Don't turn this into a deep spelunking session — but don't skip it either.

**Sub-pattern 2 — Negative-existence assertion** (e.g. "Disabled content 不会作为结果返回", "Failed 文档在列表里看不到")

- Core problem: proving a thing is **absent**. Absence is only verifiable if there is a known *positive counterpart* the test can also look for, AND a known **id** for the negative item so the test can confirm that specific id is missing.
- Rewrite discipline: expand every negative assertion into a **pair of checks**:
  - *positive*: "X (id `<positive_id>`) IS present in the returned list / visible in the DOM"
  - *negative*: "Y (id `<negative_id>`), which shares the trigger condition with X, IS NOT present"
  - Data prep must supply BOTH ids and guarantee both share whatever condition the UI filters on (same query term, same parent KB, same tab, etc.), so the only variable separating them is the state under test.
- Without known ids for the negative item, the assertion degenerates into "nothing suspicious showed up", which is not an observable.
- Manual-prep-only variant: if the negative item is in a transient state (`Processing`), the case moves to Sub-pattern overlap with transient-runtime-state and should be split out (see Mixed-feasibility rule below).

**Sub-pattern 3 — Silent-failure / robustness guard** (e.g. "不是静默失败", "不 crash", "体验友好", "系统应稳定")

- Core problem: double-negatives and subjective qualities are not observables.
- Rewrite discipline: convert the guard into **one positive marker** the executor can detect:
  - a specific Toast / error banner text (literal substring, not "some error")
  - a specific DOM element appearing (error page with a known id / class)
  - a specific API response shape (error code / message)
  - a specific absence-with-positive-replacement (loading spinner disappears AND result panel is replaced by a known error state)
- Mandatory **marker research pass** (Phase 4) before giving up. The literal toast text or DOM class is almost always already in the code — search for it, do not demand the user tell you. Concrete search targets:
  1. The page/hook's error handlers (`onError`, `catch`, `try/catch` around API calls) — they usually call `Toast.error('literal text')` or render `<ErrorState title="literal text" />`.
  2. i18n files — error messages often live in `locales/**`, `messages/**`, or inline `t('key')` calls; resolve the key to the literal.
  3. Error-boundary components used by the route — their fallback UI has known test-ids / classes.
  4. Server error-code → UI-message maps — sometimes a shared `errorCodeMap` turns backend codes into user-facing text. Record the mapping for the specific code the trigger produces.
  5. Component libraries — if the page uses a shared `<ErrorState>` / `<EmptyState>`, look up its DOM (usually has a stable class, icon, and a `title` prop).
- Only after this pass finds no marker candidate is the case not UI-testable. Then propose moving it to unit / API-contract coverage, or dropping it — with the code paths you inspected listed in the escalation, so the user can disagree based on evidence.
- Rule of thumb: if the assertion contains 两个 negation, rewrite to one positive observation (found via code) or refuse the case with evidence.

**Sub-pattern 4 — Undefined boundary / illegal-input cases** (e.g. "输入非法值应报错", "超出长度应拦截")

- Core problem: "illegal" is an infinite set; "boundary" without enumeration is a wish list.
- Rewrite discipline: enumerate the boundary classes **explicitly**, then produce one case per class:
  - empty / whitespace only
  - at max length / max length + 1
  - special chars (quotes, backslashes, emoji, RTL marks)
  - type mismatch (number where string expected, or vice versa)
  - cross-tenant / cross-ownership ids (if relevant)
- For each enumerated child, the data and assertion become concrete (specific input → specific toast/error). Parent "illegal input" row is not silently deleted: either keep it as a superseded note pointing to the child rows, or replace it with the approved child rows while preserving parent provenance and all original priority/scope tags. Children are routed as usual (some may be `auto`, some may need manual-prep because the validation lives on the backend).

After classification and rewrite, hand each resulting child back to the normal Phase 1 pipeline — scenario-concreteness, observable-anchor, feasibility. Most rewrites produce a mix of `auto` and `manual-prep` children, which then hits the mixed-feasibility split rule below. That is expected.

If you cannot map an exception row to any of the four sub-patterns, it is either (a) actually a positive-path row that was phrased loosely and needs ordinary Gate D, or (b) not testable at the layer in scope and should be dropped with an explicit note, not silently attempted.

#### Mixed-feasibility rows must be split, not blocked whole

Do **not** let a single row carry a mix of `auto` and `manual-prep` acts/assertions. The natural failure mode is: the whole row gets stamped `manual-prep` because one act is failure-injection or transient-state, which drags perfectly automatable assertions into BLOCKED territory.

Symptoms that a row is mixed:

- acts of different feasibility (e.g. "run a query" = auto; "trigger a retrieval failure" = failure-injection)
- assertions that span states of different feasibility (e.g. one assertion covers Available/Disabled/Failed — auto — AND Processing — transient-state)
- acts that target different UI surfaces (e.g. Retrieval Testing panel + backend fault injection)

When detected, draft a **Case Refinement Proposal** that splits the row into ≥ 2 independent cases, each with a single feasibility. Present it to the user as Gate D (Ambiguity → Refine); do not start data prep until the split is approved.

Rules of thumb for splitting:

- one case per observable (each assertion points at one UI or API anchor)
- one case per state axis (Available vs Disabled vs Failed is one axis; Processing is its own manual-prep axis; failure/timeout is its own manual-prep axis)
- the split preserves all original priority/scope tags — each child case inherits them, and may add its own narrowing tag (e.g. `[Manual]` for the failure-injection child)

After splitting, run normal Phase 1 classification on each child case. Typically: some children become `auto`, others become `manual-prep`. Route each accordingly — the `auto` children proceed to Phase 2; the `manual-prep` children go straight to Phase 7.5. Do not silently remove the parent row: keep a superseded note with a pointer to the child cases, or replace it only as part of the approved refinement while preserving parent provenance and all original priority/scope tags.

Routing after Phase 1:

- `auto` rows → continue to Phase 2.
- `manual-prep` rows → skip to Phase 7.5 immediately. Do not run Phase 2–6 on them.
- `unknown` rows → do **one** quick Phase 4 pass to check if an automatable create API exists. If yes, mark as `auto`, return to Phase 3 if query rules are now known, and if no reusable sample is found proceed to Gate B. If no create/query path exists, mark as `manual-prep` and route to 7.5.
- `mixed-feasibility` rows → do not route yet; emit a Case Refinement Proposal to split, then re-classify each child.
- `exception / negative-path` rows → classify the sub-pattern first (failure-trigger / negative-existence / silent-failure / boundary), rewrite per the matching template, then re-run Phase 1 on each resulting child. Skip nothing: if a child ends up `manual-prep` or non-testable, record that explicitly — don't absorb it into a sibling.

### Phase 2. Load existing business knowledge first

Before searching code or hitting any API, scan known historical and knowledge sources:

- sibling `specs/**` directories for the same product / route / feature family
- prior `test_analysis.md`, `case.md`, `e2e-test-cases.md`, execution notes, and QA handoff docs
- hard-coded or documented route examples in frontend code, fixtures, stories, seed data, screenshots, and README-style docs
- module-level `data_queries.md`
- `business_knowledge/**`
- `research/**`
- prior test notes under the same spec directory

For each requirement, record a **Data Evidence Ledger** entry before continuing:

- searched paths / keywords
- found candidate entry points, execution context, data references, fixtures, account/permission assumptions, and their source file
- why each candidate is reusable, rejected, or needs verification
- whether code research is still required to prove URL shape, enable chain, or observable anchor

For each requirement, mark one of:

- **HIT:** knowledge already explains how to query/create this entity
- **PARTIAL:** knowledge covers query but not create (or vice versa)
- **MISS:** no knowledge yet

If knowledge conflicts with code or runtime, treat code/runtime as truth and queue a knowledge-doc update.

#### Common skip rationalizations to reject

| Rationalization | Required response |
| --- | --- |
| "I'll generate `case.md` first and fill entry/data later." | Stop. Backfill `test_analysis.md` first; Stage-3 consumes only the backfilled doc. |
| "I don't know the entry point, so I'll use a placeholder." | Search sibling specs / code examples / route constants first; if still unknown, mark HANDOFF instead of inventing. |
| "The PRD says data exists, so the case can say data exists." | Convert that prose into concrete executable references (entry point + data reference + initial state + observable anchor), or BLOCKED / HANDOFF. |
| "Existing sample might not match exactly, but format generation can continue." | Reject. Candidate suitability is part of Phase 2/3; unresolved rows cannot become executable case steps. |

### Phase 3. Query first using existing knowledge

For every **HIT** requirement:

1. Call the documented list API with filters that match the requirement.
2. Shortlist candidates.
3. Call the detail API on the best candidates.
4. Reject candidates that do not meet ownership / **initial state** / shape constraints.
5. If a usable sample exists, **lock it in** for the case. No creation needed.
6. If no usable sample exists after the allowed query strategies, record the rejected candidates / missing-state reason and proceed toward Gate B for `auto` rows. **Do not** rewrite the row as Manual-Prep just because reuse failed.

Selection bias for write scenarios: current user is admin/owner, **state matches the required initial state from Phase 1** (not "any state of this entity"), correct subtype, simplest and most stable, **and every operational precondition from the enable chain is satisfied**.

For `stateful` rows, additionally enforce:

- the candidate is in the **initial state at step 1**, not in the post-mutation state. A "禁用 KB 后…" case requires an Available KB, never a Disabled one.
- the candidate is **not already assigned to another stateful row** that mutates the same way in the same run — see "Sample sharing rules" below.
- **every term in the Phase 4 enable chain is currently true for the candidate**. This is not the same check as "initial state matches". A table-row-edit case on a document inside a Disabled KB will pass initial-state-match (document is Available) but fail the enable chain (parent KB is not Available), and the UI will grey the Edit button. Use the detail-API fields the Phase 4 research pointed at as the filter — do not eyeball. If the filter rejects all existing candidates, that is a legitimate signal to escalate to Phase 5 (create a fresh sample whose entire chain is green).

If a sample is "close but not enough", do not force it — proceed to Phase 5 only after Phase 4 confirms what must be created or repaired. "Close but not enough" is still a Gate B input, not a Manual-Prep result, unless Phase 4 proves the missing property cannot be created automatically.

### Phase 4. Code research and knowledge sedimentation (Gate A)

Trigger this phase for every **MISS / PARTIAL** requirement, or when Phase 3 reveals the documented selection rule is wrong.

Inspect the frontend code in this order:

1. route/page component (URL pattern)
2. local hooks used by the page
3. shared query/mutation hooks
4. API wrapper/client + generated typings
5. UI renderers/selectors that map enum values to labels
6. permission helpers

Prove these minimum facts before moving on:

- entity behind the page
- list/detail/create/update endpoints with payload shape
- enum values for the required state
- the actual permission check used by the frontend
- the route pattern that produces the final page URL
- **structural invariants** — the properties the UI assumes about a usable sample that are *not* set by the minimum create payload (see below)
- **enable chain for the target action** — the exact boolean expression the UI uses to enable/disable the button the test will click. For any `stateful` / write-type row, this must include every ambient gate (container state, resource state, permission, lifecycle, cross-reference). See "Enable-chain research" below.
- **ingestion flow** (if the row depends on an external ingredient, see Ingredient vs Sample above):
  - the ingestion API endpoint (e.g. `POST /api/v1/knowledge_base/document/import_from_lark`)
  - the payload shape and required ingredient fields (URL, token, file multipart)
  - **whether the ingestion flow has interactive auth** — search for OAuth redirects, QR-code widgets, consent modals, `open_auth` / `external_login` URLs, SDK calls that pop a window. If any exist, classify the row's ingestion as interactive-auth and route the row to manual-prep in Phase 1, regardless of whether the ingestion API itself returns 200 in tests.
  - the post-ingestion state machine: what intermediate states exist (`Pending` / `Processing` / `Failed` / `Available`), how long they last, which endpoints poll the final state
  - the internal id shape returned by the ingestion call (e.g. `documentId`) and how to find that id in the containing entity's detail response

#### Structural invariants

A minimum create API often produces a sample that "exists" but is not yet exercisable through the UI. Identify and record these invariants so the Creation Plan (Phase 5) and verification (Phase 6) include the follow-up calls that make the sample actually usable.

Typical structural invariants to look for:

- **Graph/DAG connectivity** — a workflow may need its start node wired to the target node before any UI action works. Bare `workflow/create` produces an empty or disconnected graph; the KB selector in a RAG node cannot be reached until a valid input path exists.
- **Required child objects** — a workflow may need at least one strategy/version; a KB may need at least one document; a document may need chunks. The minimum create rarely provides these.
- **Required node configuration** — a node may demand upstream inputs, required form fields, or a specific type, before any downstream control (like a KB selector) becomes interactive.
- **Published / draft state** — some operations only work on published or draft versions; verify which state each test step expects.
- **Cross-entity references** — a "workflow that references KB X" test requires the reference to be saved into the workflow, not just both objects to exist independently.

When research finds an invariant, record it in the knowledge doc with:

- what the invariant is
- which API establishes it (endpoint, payload shape)
- how to verify it from a detail/list response (which field proves it)

Example invariant entry (target workflow + RAG node):

```text
Invariant: A KB-RAG test requires the workflow graph to have: start node → (optional middle nodes) → KB retrieval node → output. The KB node cannot be interacted with in the UI unless its upstream input is wired.
Establish via: `POST /api/v1/strategy/update` with a `nodeList` including a start node and a KB node, and an `edgeList` linking start → KB (or intermediate node → KB).
Verify via: `detail_v2` → `strategy.graph.edges` must include an edge whose target is the KB node id.
```

#### Enable-chain research (for every write-type row)

For any row whose step 1 clicks a button / opens a menu / toggles a control that mutates state, **trace the boolean chain that enables that control**. The sample is only valid if every boolean in the chain is currently true.

How to trace:

1. Find the exact button / menu item / cell renderer that the step 1 verb triggers (e.g. row-level Edit icon on the table-document detail page).
2. Read its `disabled` / `hidden` / conditional-render expression. The expression usually references:
   - a parent entity's field (e.g. `parentKb.status !== 'Disabled'`)
   - the resource's own state (e.g. `document.state === 'Available'`)
   - a permission helper (e.g. `canEditKb(currentUid, parentKb)`)
   - a transient busy flag (e.g. `!importJob.running`)
   - a lifecycle flag (e.g. `workflow.type !== 'Published'`)
3. Follow any helper calls (`canEdit`, `isOperable`, `useOperablePermission`) down to the base boolean terms.
4. Write the resolved chain out as a flat list of **positive** preconditions (things that must be true for the button to be clickable).

Record the chain in the knowledge doc so Phase 3 filtering and Phase 6 verification can read it back without re-inspecting code:

```text
Enable chain for "edit table row" on document detail page:
- parentKb.status === 'Available' (source: .../TableDocDetailPage.tsx:L218, disables toolbar when kb disabled)
- document.state === 'Available' (same file, L234)
- currentUid ∈ parentKb.administrators (source: canEditKb at .../permissions.ts:L55)
- !document.hasRunningImport (same file, L241)
- table has ≥ 1 row (otherwise edit icon is not rendered per row — row-count gate)
```

Rules:

- Every term must be backed by code, not guessed from variable names. If the UI uses a helper, trace the helper to its base terms.
- A term phrased as a negation (`!something.disabled`) should be rewritten as a positive (`something is not disabled`). Mixing positive and negative terms in the chain is a common source of wrong Phase 3 filters.
- If the chain contains a term the backend enforces but the frontend does not render differently for (rare but happens), keep it — Phase 5 creation must still respect it, and Phase 6 must verify it via the detail response.
- Do not collapse the chain into a single line like "the sample must be usable". Each term must be checkable independently so Phase 3 can reject candidates on a specific broken term, with a specific message the user can understand.

Then **sediment** the proven facts into the relevant knowledge doc (e.g. `business_knowledge/<platform>/modules/<module>/data_queries.md`). Use the entry template in [references/code-and-api-research.md](references/code-and-api-research.md). Only sediment facts backed by code, generated typings, or a successful live response.

After sedimenting, return to Phase 3 for that requirement and try to query first.

### Phase 5. Draft a creation plan and get user confirmation (Gate B)

Reach this phase only when:

- Phase 3 (with possibly Phase 4 sedimentation) has been attempted, and
- no existing sample satisfies the requirement.

This phase is **not optional** for `auto` rows. If the system has a credible non-interactive create/update path, you must stop here and show the user the plan. Do not skip straight to Manual-Prep because "query returned empty"; empty query results are exactly why Gate B exists.

A creation plan is a **sequence of API calls**, not a single create call. For each target object, include every follow-up call needed to satisfy the row's structural invariants (from Phase 4). A plan that only creates the top-level entity for a row whose test needs more (graph wiring, child objects, cross-entity references) is incomplete and must be rejected before presenting to the user.

For each object in the sequence include:

- target case(s) it serves
- entity and parent context (e.g. `KB <id>` / `workflow <id>`)
- API endpoint and method
- minimal payload (with concrete values, including admin = current user uid)
- **the invariants this call establishes** (reference the Phase 4 invariant list)
- expected resulting state and why it satisfies the requirement
- whether it depends on other objects in the plan (ordering)

Every Gate B plan must also include a short **query failure summary** before the API sequence:

- which reusable-sample queries were tried (endpoint + key filters)
- why each candidate was rejected, or why the list was empty
- which Phase 4 facts prove creation is automatable (endpoint, payload type, auth context, non-interactive flow)
- what exact sample IDs / URLs will be verified after creation

If you cannot fill those bullets, do not proceed to create and do not silently downgrade to Manual-Prep. Either finish the missing Phase 4 research within budget or emit Gate C with the specific missing fact ("create endpoint unknown", "payload cannot be derived", "interactive auth", etc.).

Worked example — a "workflow references a KB" row requires at minimum:

1. `POST /api/v1/workflow/create` (Advanced, admin = current user) — establishes entity + initial strategy
2. `POST /api/v1/strategy/update` with a `nodeList` (start + KB retrieval) and `edgeList` (start → KB) — establishes **graph connectivity invariant**; without this, the KB selector is unreachable from the UI
3. configure the KB node's selected KB to the target KB id — establishes **cross-entity reference invariant**
4. (if the test also needs an initial Available state for the KB) ensure the referenced KB is Available before test run

A plan that stops at step 1 is **rejected** — it will produce an entity that looks correct in list/detail but fails at step 1 of the test because the node is not reachable in the UI.

#### Ingestion sequence (for ingredient-based rows)

When a row depends on an external ingredient (Lark Doc/Sheet, Notion, external file URL) and Phase 4 confirmed the ingestion flow is **non-interactive**, the Creation Plan must include the ingestion call as an explicit step, with the internal sample id as its output:

1. (user-provided via Manual-Prep Request) ingredient URL `<lark_url>`, verified reachable by the current account
2. `POST /api/v1/knowledge_base/document/import_from_lark` with `{ kbId: <kb>, sourceUrl: <lark_url>, ... }` — establishes **ingested-document invariant**; returns `{ documentId }`
3. poll `document/detail` (or `kb/content/list` with filter) until the document's `state` reaches `Available` (or the test's required state). `Processing` / `Pending` is **not** a closed state.
4. record `documentId` as the sample id; record the Lark URL only as a provenance note

If Phase 4 found that the ingestion flow **has interactive auth**, do **not** put the ingestion in the Creation Plan. Classify the row as `ingestion-time interactive auth` in Phase 1 and route it to Phase 7.5. The Manual-Prep Request should then either (a) ask the user to complete the ingestion in a logged-in session and give back the resulting `documentId`, or (b) ask whether to substitute a different document type whose ingestion is non-interactive, or (c) ask whether to substitute a non-interactive source or reduce scope. Do not "try anyway" — a half-ingested doc is worse than a blocked row because it looks closed to list APIs but fails in the UI.

Use the **Creation Confirmation Template** in [references/seeding-and-backfill.md](references/seeding-and-backfill.md). Stop and wait for the user to approve, modify, or reject. Do not proceed on assumed approval.

If the user rejects an item, drop it and re-plan (e.g. relax constraints, ask user to provide a sample manually, or mark the case as "needs manual prep").

### Phase 6. Execute creation and verify step-1 reachability (not just existence)

After explicit user approval:

1. Call the sequence of APIs from the plan, in order. Save responses to `/tmp/<name>.json` and print HTTP status separately when debugging.
2. Inspect HTTP status, business `code`, `message`, and `data` payload at each step.
3. **Re-query via detail APIs and check each structural invariant from the plan.** For a workflow-with-KB-reference sample, this means:
   - `workflow/detail_v2` returns the expected type, admin list, and strategy list
   - `strategy/detail` (or equivalent) returns a connected graph: there is a path from the start node to the KB node in `edgeList`
   - the KB node's config points to the target KB id
4. **Simulate step 1 of the test mentally.** If step 1 is "in the RAG node, open the KB selector and search for X", confirm:
   - the workflow edit page URL (with strategyId) is openable
   - the KB node exists in the graph and has upstream inputs
   - the KB selector will be interactive (no disconnected-node lockout)
   - **every term in the Phase 4 enable chain is satisfied on the sample right now**, read back from detail APIs. If the action button for step 1 depends on `parentKb.status === 'Available'`, the detail response must show `Available`. Walk the chain top-down; a single broken term greys the button out and the test will fail at step 1 with "cannot click <Y>". This is separate from invariant re-check — invariants are about the sample's internal shape, the enable chain is about its ambient gates.
5. **For ingredient-based rows, verify the ingested artifact lives inside the target system, not just the ingredient URL.** For an imported Lark Doc, this means:
   - the containing KB's `content/list` (or equivalent) lists a document whose `source` matches the provided Lark URL AND whose `state` is a post-ingestion, UI-exercisable state (typically `Available`; not `Processing` / `Failed`)
   - the document has a real internal id (e.g. `documentId`) that will be recorded in Phase 7.1 — **the ingredient URL is not the id**
   - the KB detail page URL loads and shows the document row
   - if the test exercises content shape (table inside doc, row count), `document/detail` reflects the ingested shape
6. If any invariant fails, do **not** declare the sample ready. Either add follow-up calls to fix the invariant (requires a Creation Plan amendment + user re-approval) or classify the row as blocked and escalate per Gate C.
7. If verification fails, classify the blocker (expired auth / permission / business validation / missing API / unclear schema / **unsatisfied structural invariant** / **broken operational precondition** / **ingredient present but not ingested** / **ingestion blocked by interactive auth**) and report back to the user. Do not silently retry with guessed payloads.

"Existence ≠ usability." A sample is only "closed" when step 1 of its test can actually execute against it without any hidden fixup. "Ingredient ≠ sample." An external URL the user handed over is not a closed row — the ingested internal object must exist and be verifiable through the target system's own APIs.

### Phase 7. Backfill the analysis doc and knowledge doc

The analysis doc is consumed by a downstream **executing test agent** that treats every word in the `前置条件` / Prerequisites column as **steps to execute**. After data is closed, the prerequisites column must be rewritten so the executor *uses* the prepared sample instead of *re-creating* it.

#### 7.1 Rewrite the Prerequisites column for closed rows

URL / id replacement happens **only after** the row's sample has been **verified by a live API call** (Phase 6) to currently satisfy the data requirement (state, ownership, child objects, enable chain, etc.). Until then — i.e. while the row is `unverified` / `in-progress` / Phase 3 query in flight / Gate B awaiting confirmation — **keep the original data-requirement description** in the cell. Do **not** drop the requirement prose just because you have a candidate ID, and do **not** write a URL/ID into the cell as if it were resolved when the sample is not yet verified. A row in flight stays as `UNVERIFIED — data requirement: <original description>` (tags preserved); rewriting only happens when the sample is closed.

For every row whose data was successfully reused or created (status: CLOSED), replace the prose prerequisite description with a **resolved-data reference** — a short pointer the executor can consume directly. Drop the original setup narrative, **but keep all metadata tags** (see preservation list below).

> Scope note. Phase 7.1 governs the `前置条件` **column inside `test_analysis.md`** (and any equivalent analysis table). It is **not** the format used in the downstream `case.md`. The `prd2case-web` skill's Stage-3 collapses each closed row's analysis cell into a 2-line case.md prelude (`##### **前置条件** 访问: <bare URL>` + `**[tag]** e2e`) when generating `case.md`. Do not write `case.md`'s 2-line preamble back into the `test_analysis.md` cell, and do not paste Phase 7.1's full `[P0] [E2E] <entity> (state); URL ...` line into `case.md`'s preamble — they serve different consumers (analysis-driven planning vs. runner navigation) and must each keep their own format.

Required fields in the rewritten cell:

- preserved metadata tags from the original cell or row (priority `[P0]`/`[P1]`/`[P2]`, scope `[E2E]`/`[API]`/`[Smoke]`, regression markers, etc.)
- entity reference: `<EntityType> <id>` (e.g. `KB 7615994420307066881`)
- direct page URL (use the route pattern proven in Phase 4)
- if the case needs a child object / specific row count / specific state, include it inline as a fact, not as an instruction (e.g. `chunkCount=7`, `Available`, `current user is admin`)
- **the inline state fact must be the initial state at step 1**, not the sample's current DB state. A `stateful` row whose step 1 is "disable the KB" must say `Available`, even if the picked KB happens to currently be Disabled in the database (in which case it was the wrong pick — go back to Phase 3)

**Always preserve (do NOT strip during rewrite):**

- priority tags: `[P0]`, `[P1]`, `[P2]`, `[Pn]`
- scope tags: `[E2E]`, `[API]`, `[UI]`, `[Smoke]`, `[Regression]`
- any other square-bracketed tag that appears in the original cell (these are downstream filtering/scheduling metadata, not setup steps)

If a tag originally appeared in the `测试场景` cell rather than the `前置条件` cell, leave it where it was; do not move it. Only rewrite tags that were inside the prerequisites cell itself.

Bad (executor will re-run setup, tags lost):

```text
前置条件: [P0] 当前 space 至少存在 1 个 Available KB；当前账号为 Admin；该 KB 至少包含一条文本类内容
```

Good (executor jumps straight to the prepared sample, tags preserved):

```text
前置条件: [P0] [E2E] KB 7615994420307066881 (Available, current user dengshiqi.17 is admin); document 7615994420307214337 (text, chunkCount=7); URL https://vine.tiktok-row.net/rd_test/knowledge_base/7615994420307066881/document/7615994420307214337
```

Keep the rewritten cell terse — tags, IDs, URLs, and the minimum facts the executor must respect. Do not preserve the original "需要存在 / 应该是 / 至少有" phrasing; those are setup verbs and the executor will try to act on them.

**Ingredient-based rows:** the cell must reference the **internal ingested object's id** (e.g. `document <documentId>` inside `KB <kbId>`), not the ingredient URL. The ingredient URL can appear in the page-level data context table as a provenance note (source: `<lark_url>`), but never replaces the internal id in the per-row prerequisites cell. A row whose cell is still `前置条件: [P0] Lark Doc https://alidocs.dingtalk.com/...` is NOT closed — that is an ingredient sitting outside the target system; the executor will open the KB page and find zero imported documents.

Good (ingested):

```text
前置条件: [P0] [E2E] KB 7629437301059305488 contains imported Lark Doc document 7629437701245960208 (state=Available, chunkCount=12); URL https://vine.tiktok-row.net/rd_test/knowledge_base/7629437301059305488/document/7629437701245960208
```

Bad (ingredient-only, executor will fail with "no imported Lark Doc on this page"):

```text
前置条件: [P0] 可用 Lark Doc: https://alidocs.dingtalk.com/i/nodes/abc123
```

When a row needs **multiple distinct samples** (e.g. one Available + one Disabled), put the metadata tags on the first line and list each sample on its own line:

```text
前置条件: [P0] [E2E]
- Available sample: KB 7615994420307066881 (URL https://...)
- Disabled sample: KB 7618397736261648401 (URL https://...)
```

#### 7.2 BLOCKED rows: explicit blocker line, tags preserved

For rows escalated to Phase 7.5 (no closed sample yet), replace the cell with a blocker line **prefixed with the original metadata tags**:

```text
前置条件: [P0] [E2E] BLOCKED — needs manual prep: <one-line reason>; see Manual-Prep Request item #N
```

This keeps the executor from attempting the case while preserving the priority/scope tags so downstream filtering (e.g. "show me all P0 cases that are still blocked") still works.

#### 7.3 Where the data context lives instead

Move any longer narrative ("why this sample fits", "how it was created", "ownership reasoning") **out of the per-row prerequisites cell** and into:

- the existing `测试执行信息` table (the page-level data table at the bottom of the analysis doc), or
- a short note section directly under the affected scenario heading.

The per-row prerequisites cell stays minimal and machine-actionable.

#### 7.4 Update the knowledge doc

Update `business_knowledge/<platform>/modules/<module>/data_queries.md` (or equivalent) with:

- any new selection rule, enum mapping, payload caveat, or runtime caveat discovered during this run
- successful create payload as a reference template (with secrets/uids redacted into placeholders)

Avoid notes like `seems okay` / `should work`. Prefer concrete notes like `current user dengshiqi.17 is admin; KB Available; 12 rows for the bulk-delete-10 case`.

### Phase 7.5. Emit Manual-Prep Request for unclosed rows (Gate C)

Trigger this phase for any row that:

- was classified `manual-prep` in Phase 1, **or**
- has no automatable create/query path after the allowed Phase 4 research, **or**
- hit an attempt-budget cap in Phase 4 / 5 / 6 after Gate B was considered, **or**
- had its Creation Plan rejected by the user in Phase 5.

Do **not** trigger Gate C solely because Phase 3 found no reusable sample for an `auto` row. That result must be represented as a Gate B Creation Plan first. Gate C may follow only if Gate B is impossible, rejected, or fails.

Produce a single consolidated **Manual-Prep Request** that lists each unclosed row, what is needed from the user, and exactly which test cases are blocked. Use the template in [references/seeding-and-backfill.md](references/seeding-and-backfill.md).

Do **not** keep iterating on these rows. Record them in the analysis doc as `BLOCKED — needs manual prep: <reason>` so the test plan stays honest, and proceed to the final report.

## Selection Heuristics (When Multiple Candidates Exist)

Prefer the candidate that is:

- already owned/manageable by the current user (for write scenarios)
- already in the required **initial** state (not the post-mutation state)
- the simplest and least risky to reuse
- closest to the exact scenario
- stable enough to remain valid for future runs

When one object cannot serve all scenarios, prefer **separate samples per scenario** over overloading one object.

## Sample Sharing Rules (Stateful Cases)

When a row is `stateful`, the sample changes during the test. Follow these rules to avoid contaminating other rows or breaking re-runnability:

- **Do not share a sample across two `stateful` rows that mutate it the same way in the same run.** A KB that case A disables cannot be the "Available" sample for case B in the same run. Pick or create a separate sample for each.
- **Do not pick a sample whose current DB state already matches the post-mutation state.** That makes step 1 a no-op; the assertion may still pass spuriously but the test does not actually verify what it claims.
- **Pair every stateful row with a reset/cleanup note in the page-level data table** — either "test reverts the change at the end" or "sample is single-use; expect post-test state = X". This tells the executor and future runs not to reuse it without thinking.
- **If reset is hard to guarantee, prefer creating a fresh sample for stateful rows** (subject to the Phase 5 Creation Plan + user approval gate). Reused samples are great for read-only rows; stateful rows are where reuse most often misfires.

### Worked example 1 — initial-state mismatch

A real failure: row "Disabled KB 对已存在引用不产生破坏 [P0]" had operation steps `1. 禁用该 KB; 2. 运行该 Workflow 的检索`. The data prep matched on "KB referenced by some workflow" and returned a KB whose current state was `Disabled` — convenient, but wrong. The executor ran step 1 against an already-Disabled KB (no-op), then ran step 2 successfully (because the workflow had always been able to query that already-disabled KB). The assertion "禁用后引用仍可用" appeared to pass, but the test never actually exercised the disable transition.

The skill should have:

1. (Phase 1) read the operation steps, marked the row `stateful`, and recorded **initial state = `Available`**, not just "matches the entity type".
2. (Phase 3) filtered candidates with `state = Available` AND `referenced by an editable workflow`, rejecting any Disabled KB.
3. (Phase 7.1) written `KB <id> (Available, referenced by workflow <id>; step 1 will disable it)` so the executor knows the entry-state contract and that step 1 is non-trivial.

### Worked example 2 — structural invariant not established (existence ≠ usability)

A real failure: row "RAG 节点可选择 Available KB" had the skill create a workflow with `workflow/create` (type=Advanced, admin = current user). The workflow existed, had the expected type, and had an initial `v1 DEVELOP` strategy. On paper all verification passed: `workflow/detail_v2` returned the object, admin list matched, strategy list was non-empty. But the test failed at step 1: **the KB node in the RAG editor was unreachable** because the workflow graph had no edge from the `start` node into the KB node. The KB selector was locked because there was no valid upstream input to the node.

The skill should have:

1. (Phase 4) identified the **graph-connectivity invariant** — that a KB-RAG test case requires a graph path from start → KB node before any selector interaction is possible — and sedimented it into `data_queries.md`.
2. (Phase 5) drafted the Creation Plan as a **sequence**: `workflow/create` → `strategy/update` with a minimal connected `nodeList`/`edgeList` → configure KB node's `selected KB`. A plan that stopped at step 1 would have been rejected as incomplete.
3. (Phase 6) verified not just the workflow's existence but the graph's connectivity in `strategy.graph.edges`, and mentally simulated step 1 ("open RAG node → search KB selector") against the graph shape. Any disconnected node is a fail.

### Worked example 3 — vague operation steps (scenario concreteness)

Same row originally read: `操作步骤: 1. 进入 Workflow 编辑 2. 找到 RAG 节点配置 3. 打开 KB 选择器`, `预期结果: Available KB 可被选择；Disabled KB 不在可选列表或明确不可选`. This is vague — it does not say **how** to exercise the selector (scroll? search? click?) or **what exact observable** proves "可选择 / 不可选".

The skill should have (Phase 1, Gate D):

1. Triggered a targeted Phase 4 UI pass and found the selector is an async search input.
2. Proposed a **Case Refinement**:
   - concrete: `在 RAG 节点的 KB 搜索框输入 Available KB 的 name/id，断言下拉项存在且可点击、点击后保存成功；再输入 Disabled KB 的 name/id，断言下拉项存在但置灰、点击无反应或有禁用提示`.
3. Waited for user approval before finalizing the data requirement. Only after the case steps are concrete does Phase 1 lock the requirement (`needs 1 Available KB + 1 Disabled KB, both searchable by known name/id`) and move on.

Without Gate D, the vague steps would have silently driven vague data prep (e.g. create any Available + any Disabled KB without caring about searchability) — and the downstream executor would guess, producing low-signal passes or failures.

### Worked example 4 — ingredient mistaken for sample (no actual ingestion)

A real failure: row "预览范围约束：Lark 文档不提供原生预览，仅外链打开" required a KB containing at least one imported Lark Doc. The user provided Lark Doc URLs in the Manual-Prep Request round-trip. The skill recorded those URLs back into `test_analysis.md` as "可用 Lark Doc 链接" and marked the row CLOSED. The executor later opened the KB page and reported `There are no imported Lark Doc documents available on this page`. In a separate but related case ("导入 Lark Doc 并验证一次性快照语义"), the automation tried to actually perform the import and was blocked by `Feishu login/authorization requires manual QR code scanning`.

Two skill failures combined:

1. **Ingredient was mistaken for a sample.** The user's Lark URL was raw material, not an ingested KB document. No call to `document/import_from_lark` was made, no `documentId` was produced, no KB content-list verification was performed — yet the row was closed on the strength of "the URL exists and the user said it's accessible".
2. **Ingestion-time interactive auth was not detected up front.** Phase 4 never checked whether the Lark ingestion path required Feishu OAuth / QR code. The discovery happened at test run time, too late to route the row to manual-prep.

The skill should have:

1. (Phase 1) recognized that the row's requirement is `KB has an imported Lark Doc in state Available`, which is an **ingredient-based requirement** composed of `user-supplied URL` + `ingestion call` + `ingested-document verification`. None of these alone closes the row.
2. (Phase 4) inspected the Lark import flow and seen that it triggers a Feishu OAuth / QR-code consent the first time an account imports. That classifies the row's ingestion as **interactive-auth**, which means the row is `manual-prep` regardless of whether the user can give me a URL.
3. (Phase 5/7.5) emitted a Manual-Prep Request with two distinct asks:
   - provide the ingredient URL (Lark Doc link)
   - **perform the ingestion in a logged-in target-system session, then give back the resulting `documentId`** (or tell me to substitute a different document source whose ingestion is non-interactive; or approve excluding/reducing the row)
4. (Phase 7.1) refused to close the row until the `documentId` and KB-page URL are in hand, verified by `document/detail`, and only then rewritten the `前置条件` cell as `document <documentId>` inside `KB <kbId>`. The ingredient URL moves to the page-level provenance note, never the per-row cell.

Rule of thumb: if an ingredient changed hands but no internal id was produced and verified, the row is not closed — it is still `BLOCKED — needs manual prep: ingestion not completed`.

### Worked example 5 — one case with four incompatible goals (must be split)

A real failure: row `Retrieval Testing - state filtering + failure feedback` had:

```text
操作步骤:
  1. 在 Retrieval Testing 中执行目标查询
  2. 检查返回结果来源
  3. 触发一次检索失败或超时场景并观察页面反馈
断言:
  A. 正常召回结果仅来自 Available 内容
  B. Processing / Failed / Disabled 内容不会作为正常检索结果返回
  C. 失败/超时时，页面给出明确错误提示
```

Packed into this single row are **four different feasibility classes**:

1. **Act 1 query + Act 2 source check against Disabled/Failed**: `auto` — stable states, samples can be created or reused, assertion needs a `document_id` anchor confirmed by Phase 4.
2. **Act 1 query + Act 2 source check against Processing**: `manual-prep` (transient-runtime-state) — Processing cannot be pinned.
3. **Act 3 failure/timeout + Assertion C**: `manual-prep` (failure-injection) — agent cannot trigger backend timeout.
4. **All three acts' observable**: dependent on whether Retrieval Testing UI actually exposes per-result `source_state` / `document_id` — an **observable-anchor** question that needs Phase 4 before any assertion text is final.

Without the mixed-feasibility rule, the skill would likely stamp the whole row `manual-prep` because of (2) and (3), blocking the automatable (1) part too. Or — worse — it would try to pass (1) while quietly ignoring (2) and (3), producing a false green.

The skill should (Gate D, mixed-feasibility split):

1. Do one targeted Phase 4 pass on Retrieval Testing's result renderer and confirm which fields (state, doc id) are exposed per result.
2. Propose splitting the row into four independent cases, each with a single feasibility:
   - `RT-filter-disabled-1 [P0] [E2E]` (auto): KB contains 2 docs sharing the query term — one Available, one Disabled. Assertion: result list contains Available doc id; does NOT contain Disabled doc id.
   - `RT-filter-failed-1 [P0] [E2E]` (auto): KB contains Available + Failed docs sharing the query term. Assertion: result list contains Available doc id; does NOT contain Failed doc id.
   - `RT-filter-processing-1 [P1] [Manual]` (manual-prep, transient): Processing doc must be pinned during the test; user triggers a long import right before the run, or the case is excluded or accepted as reduced coverage.
   - `RT-failure-feedback-1 [P1] [Manual]` (manual-prep, failure-injection): needs backend timeout or fault injection; user decides exclude / accept reduced coverage.
3. Wait for user approval on the split. Only then run Phase 1 finalization per child case.
4. For each `auto` child, derive concrete data (2 docs in the same KB, sharing a known distinctive query term; doc-id-level assertion) and proceed to Phase 2+.
5. For each `manual-prep` child, emit a Phase 7.5 entry.

This preserves P0 coverage on the two stable-state halves, while honestly escalating the unautomatable halves instead of silently dropping them or blocking the whole row.

### Worked example 6 — ambient gating chain ignored (container state greys out child action)

A real failure: row `表格文档详情页：编辑 1 行 / 单次删除 10 行 / 单次删除 11 行 被阻止 [P0]`. Operation steps:

```text
1. 进入目标表格内容详情页
2. 编辑其中 1 行并保存
3. 选择 10 行并执行删除
4. 再选择 11 行尝试删除
```

The skill picked a document whose own state was Available, containing enough rows for the volume requirement. Initial-state check passed, row-count invariant passed. On the detail page, **the Edit icon was grey, the row checkboxes were disabled, and the Delete button was disabled**, because the document's **parent KB** was in `Disabled` state — and the table-document detail page renders the whole toolbar read-only when its parent KB is Disabled. The test failed at step 2 ("click Edit on a row") without ever reaching the business logic under test.

What the skill missed: **operational preconditions** — the ambient gating chain around the sample, distinct from the sample's own initial state and distinct from its structural invariants.

The skill should have:

1. (Phase 4, enable-chain research) traced the Edit/Delete button's `disabled` prop on the table-document detail page and found the chain: `parentKb.status === 'Available' && document.state === 'Available' && currentUid ∈ parentKb.administrators && !document.hasRunningImport && rowCount ≥ 1`. Sedimented this as an "Enable chain for table-row edit" entry in the KB knowledge doc.
2. (Phase 1) recorded the full enable chain as the row's **operational preconditions**, separate from the row's own initial state (`document=Available`) and structural invariants (`≥ 11 rows`).
3. (Phase 3) applied the precondition filter when shortlisting: reject any candidate whose `parentKb.status !== 'Available'`, regardless of how good a match the document itself is. The Disabled-KB's child document would have been rejected here.
4. (Phase 5, if creation was needed) planned a sequence: create a fresh Available KB → import a table doc into it with ≥ 11 rows → verify the enable chain is entirely green → lock in.
5. (Phase 6) read the detail API for `parentKb.status` (not just the doc's own state) and confirmed `Available` before declaring the sample ready. The step-1 mental simulation explicitly walks the enable chain.

Rule of thumb: for any row that clicks a button to mutate something, the sample is only ready when the **whole chain from the outermost container down to the button** is green. Checking the innermost resource's state alone is the most common source of "row looks right, step 1 can't be performed" failures.

## Validation Checklist (Before Reporting Done)

- [ ] Every test row has a concrete data requirement entry **with a Feasibility flag**
- [ ] Every `auto` row was attempted via query first (within the attempt budget)
- [ ] Every `manual-prep` row went straight to Phase 7.5 — no time wasted searching
- [ ] Every `auto` row with no reusable positive sample produced a Gate B Creation Plan before any Manual-Prep Request was considered
- [ ] No row says `BLOCKED — needs manual prep` merely because query/list APIs returned no candidate; the block reason must be manual-only, create-path-missing, user-rejected, or create/verify-failed
- [ ] **No row was deleted from `test_analysis.md` / `case.md` because data could not be found.** Unresolved rows stay in place as `BLOCKED` (with original tags preserved) and appear in the Manual-Prep Request. Removal is allowed only after explicit user approval that the row is genuinely not testable at this layer, and the inspected code paths are recorded as evidence.
- [ ] Every code-research finding has been written into a knowledge doc
- [ ] No object was created without an approved Creation Plan
- [ ] Every created object was verified via list/detail
- [ ] Every unclosed row appears in the Manual-Prep Request **and** is marked `BLOCKED — needs manual prep` in the analysis doc
- [ ] **Every CLOSED row has its `前置条件` cell rewritten to a resolved-data reference (entity id + URL + minimum facts) — no leftover setup verbs like `需要存在` / `至少 1 个` / `当前账号为 Admin` that the executor would try to act on**
- [ ] **All metadata tags from the original prerequisites cell are preserved verbatim (priority `[P0]`/`[P1]`/`[P2]`, scope `[E2E]`/`[API]`/`[Smoke]`, and any other square-bracketed tags) on both CLOSED and BLOCKED rows**
- [ ] **For every `stateful` row, the picked sample's actual DB state matches the recorded initial state at step 1 — not the post-mutation state. (e.g. a "disable then observe" row is paired with an Available sample, not a Disabled one.)**
- [ ] **No sample is shared between two `stateful` rows that mutate it the same way in the same run; each gets its own sample (or an explicit reset note).**
- [ ] **Every row's operation steps are concrete (UI control + input value + observable effect). Any originally-vague row has a Case Refinement Proposal approved by the user before data prep proceeded.**
- [ ] **Every created sample has all structural invariants established and re-verified in detail APIs: graph connectivity, required child objects, cross-entity references, required node configuration. "Exists in list" alone is not acceptance.**
- [ ] **For every `stateful` / write-type row, the Phase 4 enable chain (ambient operational preconditions) is traced, recorded, and re-verified on the picked/created sample. The check reads parent-container fields, lifecycle fields, permission helpers, and transient busy flags — not just the sample's own state.**
- [ ] **Step 1 of each test was mentally simulated against the picked/created sample; no hidden setup is required between "data ready" and "test can start".**
- [ ] **Every ingredient-based row (external URL/file/link) has a verified internal id (e.g. `documentId`) produced by an ingestion call and confirmed via the containing entity's detail API. No row is CLOSED on ingredient availability alone.**
- [ ] **Phase 4 explicitly checked whether the ingestion flow has interactive auth (OAuth/QR/OTP/external window). Rows whose ingestion is interactive are routed to Phase 7.5 up front, not discovered at test run time.**
- [ ] **The per-row prerequisites cell for an ingredient-based row references the internal id, not the ingredient URL. The ingredient URL appears only as a provenance note in the page-level data table.**
- [ ] **No row carries mixed feasibility (some acts/assertions `auto`, others `manual-prep`). Mixed rows were split via Case Refinement Proposal and each child has a single feasibility class.**
- [ ] **Every assertion's observable is anchored to a UI element, DOM field, or API hook that Phase 4 confirmed exists. No row coasts on an "implied" observable (e.g. "result source" when the UI may not show per-result state).**
- [ ] **Every exception / negative-path row was matched to one of the four sub-patterns (failure-trigger / negative-existence / silent-failure / boundary) and rewritten per its template. No row left as "描述异常情况" without either a named trigger, a paired positive+negative id set, a single positive marker, or an enumerated boundary set.**
- [ ] **For every Sub-pattern 1 row (failure-trigger), a Phase 4 research pass was done on the frontend error handlers + PRD error-scenario language, and every in-scope trigger discovered was enumerated as its own child case. `manual-prep / failure-injection` was chosen only after the research found no reachable trigger, and the escalation records what was inspected.**
- [ ] **For every Sub-pattern 3 row (silent-failure), a Phase 4 research pass was done on `Toast.error` / `<ErrorState>` / i18n / error-code maps for the literal marker. The case was declared non-UI-testable only after this pass, with the inspected code paths cited.**
- [ ] Each closed row has a concrete justification note in the page-level data table (not in the prerequisites cell)
- [ ] Final URLs are directly openable

## Output Expectations

When closing the task, report:

- Per-case data requirement table with Feasibility (Phase 1 output)
- Knowledge HIT / PARTIAL / MISS map (Phase 2 output)
- Knowledge docs updated (Phase 4 output)
- Samples reused vs samples created (with IDs)
- Final page URLs added to the analysis doc
- **Manual-Prep Request** consolidating every unclosed row, each with the exact item needed from the user (Phase 7.5 output)
- Failure classification per blocked row:
  - manual-prep-only by category (different account / external ingredient needs ingestion / ingestion-time interactive auth / specific external content shape / transient state / failure injection / third-party credentials)
  - expired auth
  - missing permission
  - business validation failure
  - missing create API
  - insufficient code or schema clarity
  - user rejected creation plan
  - attempt budget exhausted
  - **ingredient received but ingestion not completed** (row is not closed; Manual-Prep Request must follow up with either a human-driven ingestion or a substitute sample type)
