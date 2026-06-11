# Seeding And Backfill

Use this reference when you already know which APIs exist (either from existing knowledge or freshly sedimented in Phase 4) and need to safely query, **propose creation for user approval**, create, validate, and document test samples — or to **escalate** a row that cannot be auto-closed.

This file covers Phases 3, 5, 6, 7, **and 7.5** of the skill workflow.

## Order Of Operations (Reuse > Create > Escalate)

1. **List candidates** with filters that match the per-case requirement, **including the row's initial state from Phase 1** — never "any state of this entity".
2. **Inspect details** on the best candidates and confirm the initial state matches.
3. If a usable sample exists, **stop here** and lock it in. Do not create.
4. If no usable sample exists *and* the row is `auto`, draft a **Creation Plan** and present it to the user. Do **not** emit Manual-Prep merely because list/query returned empty. For ingredient-based rows, the plan must include the ingestion call as an explicit step (or the row stays `manual-prep`; see below).
5. **Wait for the user's explicit approval.** No silent creation.
6. After approval, call create APIs.
7. **Re-query detail** to verify usability (state matches initial-state requirement, child object exists, row counts ok, ownership ok, **ingredient-derived id present in container**).
8. **Backfill** analysis doc + knowledge doc with exact IDs/URLs and route provenance; for ingredient-based rows, record the **internal id** (e.g. `documentId`), not the ingredient URL.
9. If the row is `manual-prep`, **or** if no automatable create path exists, **or** if the post-Gate-B attempt budget is exhausted, **or** if the user rejects the Creation Plan, **or** if an ingredient was received but ingestion could not be completed → emit a **Manual-Prep Request** entry for this row, **mark the row `BLOCKED — needs manual prep` while keeping the row itself in `test_analysis.md` (and as a `skip` entry in `case.md`) with original tags preserved**, and move on. Do not loop. **Do not delete the row.** "Cannot auto-close" is a labelling outcome, not a removal outcome — removing a row from the analysis/case docs forfeits its coverage and is only allowed with explicit user approval that the row is genuinely not testable at this layer.

## Ingredient-Based Rows Contract (Read Before Closing Any Row That Touched An External URL/File)

A row whose data requirement depends on external material (Lark Doc/Sheet URL, Notion page, external HTTP file, third-party account handle) has three sub-steps. Closing the row requires all three — NOT just the first.

1. **Ingredient obtained.** User supplies the URL / file / handle via a Manual-Prep Request round-trip. This alone does NOT close the row. The ingredient URL is not a sample.
2. **Ingestion executed.** An API call inside the target system imports the ingredient and returns an internal id (e.g. `POST /api/v1/knowledge_base/document/import_from_lark` → `{ documentId }`). Phase 4 must have confirmed this API exists AND does not require interactive auth (no QR / OAuth consent / OTP / external browser step). If the ingestion is interactive, the row stays `manual-prep` with category *ingestion-time interactive auth* — do not attempt from the agent.
3. **Internal sample verified.** The containing entity's detail/list API (e.g. `kb/content/list`) shows the ingested object in a UI-exercisable state (typically `Available`; not `Processing` / `Failed`). Record the internal id as the sample id. The ingredient URL is downgraded to a provenance note.

### Two common misfires (both produce silent-close false positives)

- **"User gave me a URL; I wrote it into the analysis doc; row closed."** No. The ingredient lives outside the target system. When the executor opens the KB page, it sees zero imported docs. The row should stay BLOCKED with a follow-up ask for either a human-driven ingestion or a substitute non-interactive source.
- **"I ran the import API; it returned 200; row closed."** Not enough. 200 + `Processing` or 200 + `Failed` both leave the UI unable to exercise the artifact. Poll `content/list` until `state=Available` (or the test's required state) before closing.

### Manual-Prep Request must separate ingredient from ingestion

When an ingredient-based row is BLOCKED, the Manual-Prep Request item has **two distinct asks** if Phase 4 found interactive auth, and **one** otherwise:

- ingredient only (non-interactive ingestion, agent can complete the rest): ask for the URL/file/handle
- ingredient + completed ingestion (interactive auth in the flow): ask the user to either (a) perform the ingestion in their own logged-in session and return the resulting internal id, (b) substitute a different source whose ingestion is non-interactive, or (c) accept reduced coverage / exclude that row with the reason recorded

Do not conflate these. The user's answer differs, and silently mixing them is how "I sent a URL, why didn't it work" happens.

## Stateful Test Contract (Read Before Picking Or Creating Stateful Samples)

`stateful` rows (Phase 1 flagged them) mutate the picked sample during the test. They are the most common source of "passes by accident" failures. Apply these rules:

### 1. Match the *initial* state, not the current DB state

The candidate must be in the state required at **step 1**, before any mutation the test performs. This is non-negotiable.

Common trap: row says `禁用 KB 后…工作流仍可用`. A natural query is "find any KB referenced by a workflow". That returns both Available and Disabled KBs. Picking a Disabled KB makes step 1 (`disable the KB`) a no-op; the assertion may pass spuriously but the test never exercises the transition.

Filter at the list-API level when possible (`status = Available`); if the list API does not expose state, filter in the candidate-shortlist step before locking in.

### 2. No sharing between same-mutation stateful rows in the same run

Two `stateful` rows that mutate the same field of the same entity (e.g. both flip `status`) must use **different samples**. Otherwise the second row starts in a polluted state.

Read-only rows can share with anyone. Stateful + read-only sharing is allowed only if the read-only row tolerates the post-mutation state (rare — confirm explicitly).

### 3. Do not pick samples whose current state already matches the post-mutation state

If step 1 disables a KB, do not pick a KB that is already Disabled — even if every other constraint matches. The test must observe a transition, not a steady state.

### 4. Prefer fresh creation for stateful rows

Reuse is great for read-only rows. For `stateful` rows, **default to creating a fresh sample** (subject to the Creation Plan + user approval gate), unless an existing sample is *cleanly* in the initial state and not used by another stateful row in this run.

This bias is intentional: a freshly created sample has known initial state and zero coupling to other rows. The Phase 5 Creation Plan should explicitly call out which planned objects are for stateful rows and why reuse was rejected.

### 5. Pair every stateful CLOSED row with a post-test-state note

In the page-level data table (not in the per-row prerequisites cell), record what the sample will look like after the test runs:

```text
Post-test state: KB <id> will become Disabled. Do not reuse for an "Available KB" case in the same run. Re-enable manually or recreate before next run if needed.
```

This lets the executor and future runs reason about reusability.

### 6. Cell rewrite: state inline must be the initial state

Phase 7.1 backfill: the inline state fact in the `前置条件` cell must be the **initial** state at step 1.

Bad (sample is currently Disabled, executor will run "禁用 KB" against an already-Disabled KB):

```text
前置条件: [P0] KB 7629437301059371024 (Disabled) referenced by workflow 7629227911102398481
```

Good (initial state required for step 1 is Available; the picked sample is in fact Available right now):

```text
前置条件: [P0] KB <available-id> (Available, current user is admin, referenced by workflow <wf-id>); URL https://vine.tiktok-row.net/rd_test/knowledge_base
```

If the only sample you can find or create is in the wrong initial state, that is a Phase 3/5 failure — go fix the data, do not paper over it in the cell.

## Attempt Budget (Hard Stop)

Per requirement, cap effort. When a cap is hit, escalate to a Manual-Prep Request — do not "try one more filter".

- **Phase 3 (query):** at most **2 list-API calls** with distinct filter strategies. Examples of distinct strategies:
  - `(filter A: status=Available, ownedByMe=true)` then `(filter B: status=Available, ownedByMe=false)` — yes, distinct.
  - same filter twice with different page offsets — **no**, counts as one strategy.
- **Phase 4 (code research):** at most **one focused pass** through routes → hooks → API wrapper → typings for that entity. If the create API surface is still unclear after one pass, escalate.
- **Phase 5/6 (create):** at most **2 create attempts** for the same logical object. The second attempt may correct payload based on a server validation message; a third failure is automatic escalation.
- **Total per requirement:** if more than ~10 minutes of agent effort have been spent without convergence, escalate.

A row hitting the budget is **not** a failure of the skill — it is a successful early-stop. The user gets a clear ask instead of a long, fruitless trace.

## Curl Pattern (For Both Query And Create)

When debugging auth or business failures, separate HTTP status from the body:

```bash
curl -s -o /tmp/<response>.json -w '%{http_code}' '<url>' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'permission-ns-id: <space>' \
  -H "x-jwt-token: $JWT" \
  -b "$COOKIE" \
  --data-raw '<json>'
```

Then inspect each layer:

- HTTP status code
- body `code` (business code)
- body `message`
- `data` payload (created IDs / list entries / detail fields)

## Creation Confirmation Template (Gate B — Required)

A Creation Plan is a **sequence of API calls** per target object, not a single create call. A plan that stops at the top-level `create` for a composite entity (workflow with nodes, KB with documents, document with rows) is incomplete — it produces samples that exist in list/detail but fail at step 1 of the test because structural invariants (graph connectivity, child objects, cross-entity references) are not set.

Before calling **any** create/update API in Phase 5, present this to the user and wait for an explicit `approve` / `modify` / `reject`. Do not proceed on assumed approval.

````markdown
## Creation Plan (need your confirmation before I create)

Reason for creation: <one line — why no existing sample satisfies the requirement, with what was tried>

Auth in use: `permission-ns-id=<space>`, current user uid `<uid>` (from your last provided headers)

### Object 1 — <short label, e.g. "Workflow + RAG node wired to KB X, for KB-disable-ref test">

- Serves cases: `<Case ID 1>`, `<Case ID 2>`
- Entity: `<top-level entity>` (parent: `<parent or N/A>`)
- Structural invariants to establish (from Phase 4 research):
  - <e.g. "graph has path start → KB node">
  - <e.g. "KB node's selected KB = <target KB id>">
  - <e.g. "workflow type = Advanced; has ≥ 1 editable strategy">
- Sequence of calls (each one establishes listed invariants):
  1. `POST /api/v1/workflow/create` — establishes: entity + initial v1 DEVELOP strategy
     - payload:
       ```json
       { "name": "...", "administrators": ["<uid>"], "mediaType": 1, "type": 2 }
       ```
  2. `POST /api/v1/strategy/update` — establishes: **graph connectivity** (start → KB node)
     - payload: `{ "strategyId": "<from step 1>", "nodeList": [<start>, <kb>], "edgeList": [{ "source": "<start>", "target": "<kb>" }] }`
  3. `POST /api/v1/strategy/update` (or node-config call) — establishes: **cross-entity reference** (KB node → target KB id)
     - payload: `{ "strategyId": "...", "nodeConfig": { "<kb_node_id>": { "selectedKbId": "<target_kb_id>" } } }`
- Expected result: `<entity>` in initial state `<state>`, owned by current user, all invariants verifiable from detail API
- How I will verify each invariant in Phase 6:
  - <e.g. "call workflow/detail_v2; check strategy.graph.edges contains an edge with target = KB node id">
  - <e.g. "check strategy.graph.nodes[kb].config.selectedKbId == <target KB id>">
- Follow-up calls for correctness (beyond invariant establishment): <e.g. "call detail_v2 once more to snapshot the final state">, or `none`

### Object 2 — ...

(same shape)

### Order of creation

1. Object 1 — steps 1, 2, 3 in order (step 3 depends on step 2's strategyId)
2. Object 2 (depends on Object 1's id)

### What I will NOT create (and why)

- `<requirement>` — already covered by existing sample `<id>` (reuse)
- `<requirement>` — needs manual prep (e.g. Lark Doc link with valid permission, or interactive-auth ingestion), please provide

### Ingredient-based objects (if applicable)

For each object that ingests an external ingredient, this section must be present:

- Ingredient source: `<lark_url>` (supplied by user in Manual-Prep round-trip #N)
- Ingestion API: `POST /api/v1/knowledge_base/document/import_from_lark`
- Ingestion auth mode (from Phase 4): `non-interactive` <!-- if `interactive`, this object does NOT belong in a Creation Plan; move it to a Manual-Prep Request item instead -->
- Expected internal id shape: `documentId` (returned in `data.documentId`)
- Post-ingestion state wait: poll `knowledge_base/content/list` until the document's `state = Available`; timeout at 60s then escalate
- Verification: `content/list` returns a document whose `source = <lark_url>` and `state = Available`; `document/detail` returns non-zero `chunkCount`

Please reply with:
- `approve` — I will execute the full sequence in order
- `modify: <change>` — I will revise the plan
- `reject: <object label>` — I will drop that object and re-plan
````

Rules:

- **A plan is a sequence.** If the entity is composite (workflow with graph, KB with documents, etc.), the plan must list every follow-up call needed to satisfy the structural invariants identified in Phase 4. Single-call plans for composite entities are rejected.
- **Invariants are explicit.** Each object section lists the invariants it must satisfy and which call in the sequence establishes each. No invariant should be left as "probably set by default".
- **Verification is pre-declared.** For each invariant, state which detail-API field will prove it during Phase 6. Do not defer this decision.
- **One plan, all objects in one go.** Do not drip-feed creations. The user must see the full impact before approving.
- **Concrete payloads.** No `<TODO>` placeholders inside the payload. If a value isn't known, that's a Phase 4 (code research) gap, not something to ask the user to fill in.
- **Prefer current user as admin / owner** for write scenarios.
- **Stable, dated names** (e.g. `Test Disabled KB 20260420 01`) so created samples are easy to recognize and re-find later.
- **Always list the reuse counterpart**: which requirements are NOT triggering a create, and why. This makes the "minimize creation" principle visible to the user.

## Manual-Prep Request Template (Phase 7.5 — Required When Escalating)

Use this for any row that is `manual-prep` from Phase 1, or that exhausted the attempt budget, or whose Creation Plan was rejected. Emit **one consolidated** Manual-Prep Request at the end of the run that lists every escalated row.

````markdown
## Manual-Prep Request (need your help to close these cases)

I stopped researching these rows because they cannot be reliably auto-resolved with the current codebase APIs and the auth you provided. Each item below blocks specific test cases — please supply the listed prep so the cases can be closed.

### 1. <Short label, e.g. "Non-admin User account in current tenant">

- Blocks cases: `<Case ID 1>`, `<Case ID 2>`
- Category: `different user account` <!-- one of: different user account / external integration link / external content shape / transient runtime state / failure injection / third-party credentials / attempt-budget exhausted / Creation Plan rejected -->
- Why I stopped:
  - Tried: <very brief — e.g. "list user API in tenant `rd_test` requires admin grant; codebase has no provisioning API">
  - Stopped after: <e.g. "1 code-research pass + 1 list-API attempt">
- What I need from you (concrete):
  - A non-admin user uid that already exists in tenant `rd_test`, plus a way to obtain that user's `x-jwt-token` and cookies for one verification call.
- Once you provide it, I will:
  - Backfill `permission` row in the analysis doc with the uid and the page URL the User account sees.

### 2. <Short label, e.g. "Lark Doc imported into KB X (ingredient only — ingestion is non-interactive)">

- Blocks cases: `<Case ID>`
- Category: `external ingredient needs ingestion`
- Ingestion auth mode (Phase 4 finding): `non-interactive` (agent can complete the import once URL is provided)
- Why I stopped:
  - The target-system import API requires a Lark Doc URL the backend can fetch; access cannot be proven by code or by an empty link.
- What I need from you (concrete):
  - A Lark Doc URL you have already opened with the test account, with at least one paragraph of importable text (no embedded table for this row).
- Once you provide it, I will:
  - Call `POST /api/v1/knowledge_base/document/import_from_lark` with the URL
  - Poll `content/list` until the resulting document reaches `state=Available`
  - Backfill the per-row `前置条件` cell with `document <documentId>` inside `KB <kbId>`, plus the page URL
  - Record the Lark URL as a provenance note in the page-level data table only

### 3. <Short label, e.g. "Lark Doc imported into KB X (ingredient + ingestion-time Feishu OAuth)">

- Blocks cases: `<Case ID 1>`, `<Case ID 2>`
- Category: `external ingredient needs ingestion` + `ingestion-time interactive auth`
- Ingestion auth mode (Phase 4 finding): `interactive` — first-time Lark import for a target-system account triggers a Feishu OAuth / QR-code consent. Agent-side retry cannot proceed.
- Why I stopped:
  - Even if you give me a URL, the import will hang on the OAuth/QR step. A half-imported document would show up in list APIs in a `Failed` / `Processing` state and still break the test.
- What I need from you — please pick ONE:
  - **(a) Drive the ingestion yourself**: open the target system, import this Lark Doc into `KB <kbId>` in a logged-in session, wait until the document shows `state=Available` in the KB content list, then reply with the resulting `documentId` (shown in the URL after clicking the document, or via `document/detail`).
  - **(b) Substitute**: approve using a non-Lark document source whose ingestion is non-interactive (e.g. upload a text/PDF file instead), so we can stay on the `auto` path for the shape-equivalent cases.
- Once you reply (a), I will:
  - Verify the `documentId` via `document/detail` and `content/list`
  - Backfill the per-row `前置条件` cell with `document <documentId>` and the page URL
  - Mark the row CLOSED only after that verification
- If you reply (b) or (c), I will revise the Creation Plan / test plan accordingly and re-seek approval.

### 4. <Short label, e.g. "Lark Doc URL containing an embedded table">

- Blocks cases: `<Case ID>`
- Category: `external ingredient needs ingestion` + `specific external content shape` + (likely) `ingestion-time interactive auth`
- Why I stopped:
  - Same as item 3, plus an additional content shape requirement (must contain a table) that only a human can guarantee.
- What I need from you (concrete):
  - A Lark Doc URL you have already opened with the test account that contains at least one embedded table with ≥ 2 rows of body data, AND — if Phase 4 confirmed interactive ingestion — the resulting `documentId` after you drive the import in a logged-in session.
- Dependency note: if the upstream import is blocked, every downstream row that reads "KB containing imported Lark Doc with table" is also BLOCKED until this item is resolved.

### 5. <Short label, e.g. "Processing-state KB content sample">

- Blocks cases: `<Case ID>`
- Category: `transient runtime state`
- Why I stopped:
  - `Processing` is a transient status during ingestion; even if I trigger an import, by the time the test runs the status will have flipped to `Available` or `Failed`. There is no API to pin a sample at `Processing`.
- What I need from you (one of):
  - You manually trigger a fresh long-running import right before the test, and we capture that document id while it is still in `Processing`, **or**
  - Mark this case as not-auto-verifiable and exclude from the data-driven run.

---

How to reply:

- For each item, paste the missing artifact (uid, link, etc.) inline, **or** confirm "skip / exclude" with the reason.
- I will only resume work on items you explicitly unblock. The rest stay marked `BLOCKED — needs manual prep` in the analysis doc.
````

Rules for the Manual-Prep Request:

- **Be specific about the ask.** "Please give me a Lark Doc" is not enough; say what content shape, which account must have access, what the doc will be used for.
- **Tie every item to Case IDs** so the user can decide whether the case is worth unblocking.
- **Always state what was tried and the stop reason.** This proves you did not stop prematurely and helps the user judge whether to relax the requirement.
- **Always offer alternatives** for transient/failure-injection rows (exclude / accept reduced coverage) — these may not be worth a fresh sample.
- **One consolidated request per run.** Do not drip-feed asks.

After emitting the request, also update the analysis doc:

```text
| ... | ... | BLOCKED — needs manual prep: <one-line reason>; see Manual-Prep Request item #<N> |
```

This keeps the test plan honest about what is and isn't ready.

## Validation After Create (Phase 6) — Step-1 Reachability, Not Just Existence

"Exists in list" is not acceptance. After every create sequence, confirm **each structural invariant** the plan promised to establish, and mentally simulate step 1 of the test against the sample.

Mandatory checks (do all, in order):

1. **Existence & state** — the object appears in the list API and the detail API returns it in the required *initial* state.
2. **Invariant re-check** — walk the invariant list from the Creation Plan. For each invariant, read the detail response field the plan pre-declared and confirm the expected value. Examples:
   - graph connectivity: `strategy.graph.edges` must contain a path from the start node to the target node (e.g. KB node). If the entity returns a node list but no edges, the invariant is not satisfied — the sample is unusable.
   - cross-entity reference: the node's config/field that should hold the target id (e.g. `selectedKbId`) must match the intended value.
   - child objects: required child count (`chunkCount`, `rowCount`, `strategyList.length`) meets the requirement.
   - workflow subtype: `type = Advanced`, `status` allows editing.
3. **Enable-chain re-check (ambient gating)** — walk the enable chain recorded in the Phase 4 knowledge entry for the target action. For each term, read the detail response field the research pointed at and confirm it is true. This is a separate check from invariants — invariants are about the sample's internal shape; the enable chain is about ambient state around it.
   - parent container state: e.g. for a table-document edit case, re-read `parentKb.status` and require `Available`. The document itself being Available is not enough; the whole chain must be green.
   - lifecycle state: e.g. `workflow.type = DEVELOP`; a Published workflow will reject strategy-update.
   - transient busy flags: e.g. `!document.hasRunningImport`; a mid-import doc will render read-only.
   - permission: re-check the *frontend's actual helper terms*, not just "token works". `currentUid ∈ parentKb.administrators` is the usual term; confirm via the detail API field.
   - row-count gate: e.g. `rowCount ≥ 1` before the per-row action appears at all.
   - If any chain term is false, do NOT declare the sample ready. Either amend the Creation Plan (e.g. add a `kb/update status=Available` call, or choose a different parent) + re-seek user approval, or escalate per Gate C.
4. **Ingestion landed inside the target system (ingredient-based rows only)** — for every external ingredient the Creation Plan listed:
   - the containing entity's `content/list` (or equivalent) returns an item whose source identifies the ingredient (e.g. `source = <lark_url>`)
   - that item has a real internal id (e.g. `documentId`), and the id is what the `前置条件` cell will reference — **not** the ingredient URL
   - the item's state is UI-exercisable (typically `Available`); `Processing` / `Failed` / `Pending` are not closed
   - the KB page URL built from the internal id loads and shows the ingested item
   - if the test exercises content shape (table rows, chunk count), `document/detail` reflects that shape
5. **Ownership / permission** — the current user can operate on the sample if the row is writable (the frontend's actual check, not just "uid in admin list" — use the same check Phase 4 proved is the real one).
6. **Shape / volume** — row / chunk / item counts satisfy the target case (e.g. ≥ 11 rows for the bulk-delete-10 case).
7. **Step-1 mental simulation** — walk the row's step 1 literally:
   - "Open URL X" — does URL build from the resolved id(s), and does its path match the router/basename proven in Phase 4? Re-check suspicious duplicates like `/app/app/...` before closing the row.
   - "Click the Y button / open the Z selector" — walk the **enable chain** from outer container down to the button: every term green → button clickable; any term red → button greyed and step 1 fails. (E.g. a row-edit icon on a table document requires `parentKb.status=Available`, `document.state=Available`, `currentUid ∈ parentKb.administrators`, `!document.hasRunningImport`, `rowCount ≥ 1` — all simultaneously. Graph-based selectors additionally need their upstream edges wired.)
   - "Type <literal>" — does the sample expose a matching record by that literal? (e.g. if the case searches for a KB by name, the KB's name must contain the expected substring.)
   If any of these produces "the UI would not let the user proceed", the sample is not ready. Do **not** mark the row CLOSED.

If any check fails:

- **Do not silently retry with guessed payloads.**
- Identify which invariant or precondition is missing.
- Either (a) amend the Creation Plan with the follow-up call that fixes it and re-seek user approval, or (b) classify the row as blocked and escalate per Gate C.

Common failure mode the checks above catch: `workflow/create` returns a happy `workflow_id`, the workflow appears in list, but the graph has no edges. The row's step 1 "open RAG node → pick KB" is unreachable because the KB node has no upstream input. Existence passed, usability failed. Invariant re-check and step-1 simulation catch this before closing the row.

Another common failure mode (ingredient-based): the user hands over a Lark Doc URL; the skill writes the URL into the analysis doc and moves on; the executor opens the KB page and finds zero imported Lark Docs. Existence of the *ingredient* is not existence of the *sample*. Check 4 (ingestion landed inside the target system) catches this before closing the row — if no `documentId` is produced and verified, the row is not closed, period.

A third common failure mode (ambient gating): the picked sample's own state is exactly right, but an *outer container* is in a state that disables the action. Example: a table document is Available with ≥ 11 rows, but its parent KB is Disabled, so the detail page renders the toolbar read-only and the Edit/Delete icons are greyed — step 1 ("click Edit on a row") fails with "cannot click button". Check 3 (enable-chain re-check) catches this: read `parentKb.status` alongside `document.state`, and reject the sample when any chain term is false.

## Backfill Template (Phase 7)

The analysis doc is consumed by a downstream **executing test agent**. That agent treats the per-row `前置条件` / Prerequisites column as **commands to execute**. So after a row's data is closed, the prerequisites cell must stop describing setup and start pointing at the prepared sample.

### Always-preserved metadata tags

Some bracketed tokens are downstream metadata (priority / scope / scheduling), not setup steps. They MUST survive every rewrite:

- priority: `[P0]`, `[P1]`, `[P2]`, `[Pn]`
- scope: `[E2E]`, `[API]`, `[UI]`, `[Smoke]`, `[Regression]`
- any other `[Tag]` that appeared in the original cell

If a tag was originally in the `测试场景` cell (not in `前置条件`), leave it where it was — only rewrite tags that lived inside the prerequisites cell.

### Two cell shapes — pick one per row

**A. CLOSED row → resolved-data reference (tags preserved, no setup verbs)**

Required fields, in this order:

- preserved metadata tags from the original cell (e.g. `[P0] [E2E]`)
- entity reference: `<EntityType> <id>`
- direct page URL (built from the router/basename route pattern proven in Phase 4)
- route provenance: `route: <basename> + <route> (source: <router/page-entry file>)`
- minimum facts the executor must respect inline (state, ownership, child id, row counts) — written as facts, not instructions

Bad — executor will try to "make" these conditions:

```text
前置条件: [P0] 当前 space 至少存在 1 个 Available KB；当前账号为 Admin；该 KB 至少包含一条文本类内容
```

Good — executor uses what is prepared, tags preserved:

```text
前置条件: [P0] [E2E] KB 7615994420307066881 (Available, current user dengshiqi.17 is admin); document 7615994420307214337 (text, chunkCount=7); URL https://vine.tiktok-row.net/rd_test/knowledge_base/7615994420307066881/document/7615994420307214337; route=/rd_test/knowledge_base/:kbId/document/:documentId (source: apps/vine/src/routers/index.tsx)
```

For multi-sample rows, put tags on the first line and list each sample on its own line:

```text
前置条件: [P0] [E2E]
- Available sample: KB 7615994420307066881 (URL https://vine.tiktok-row.net/rd_test/knowledge_base)
- Disabled sample: KB 7618397736261648401 (URL https://vine.tiktok-row.net/rd_test/knowledge_base)
- Description-overflow sample: KB 7615994420307066881 (description spans 3 lines)
```

For rows that imply a *negative* sample (something that should **not** appear), make that explicit too:

```text
前置条件: [P0]
- Owned sample: KB 7615994420307066881 (current user dengshiqi.17 in administrators)
- Not-owned sample: KB 7618221345678901234 (current user not in administrators)
```

**B. BLOCKED row → explicit blocker pointer (tags preserved)**

Do **not** keep the original prose; the executor will still try to act on it. Replace with the tags + a blocker line:

```text
前置条件: [P0] [E2E] BLOCKED — needs manual prep: <one-line reason>; see Manual-Prep Request item #N
```

Tags must stay so downstream filters like "all P0 still blocked" continue to work.

### What goes where

- **Per-row `前置条件` cell** — terse, machine-actionable: ids, URLs, route provenance, inline facts. No setup verbs. No reasoning.
- **Page-level `测试执行信息` table (or a notes block under the section heading)** — longer narrative: why the sample fits, ownership reasoning, how it was created, router/basename evidence, runtime caveats. This is for human readers, not the executor.
- **Knowledge doc (`data_queries.md`)** — reusable selection / creation rules and payload templates for future runs.

### Setup-verb checklist (must be absent from CLOSED row cells)

Reject the cell and rewrite if you see any of:

- `需要 / 至少 / 必须 / 应当 / 准备 / 先 / 创建一个 / 存在一个`
- `当前账号为 Admin` (rewrite as a fact tied to the prepared sample, e.g. `current user dengshiqi.17 is in administrators of KB <id>`)
- `有可访问的 ... 链接` / `可用 Lark Doc URL: https://...` (this is an **ingredient**, not an internal sample — the row should be BLOCKED until the ingestion has produced an internal id, or CLOSED with the internal id inline instead of the URL)
- any sentence the executor could interpret as "go do this first"

Tags like `[P0]` / `[E2E]` are **not** setup verbs — keep them. Strip only the prose setup language.

### Ingredient rule for CLOSED cells

For ingredient-based rows that reached CLOSED, the cell must reference the **internal ingested object**, not the ingredient:

Good (ingested sample):

```text
前置条件: [P0] [E2E] KB 7629437301059305488 contains imported Lark Doc document 7629437701245960208 (source=lark, state=Available, chunkCount=12); URL https://vine.tiktok-row.net/rd_test/knowledge_base/7629437301059305488/document/7629437701245960208
```

Bad (ingredient masquerading as sample; the executor will open the KB page and find nothing imported):

```text
前置条件: [P0] 可用 Lark Doc: https://alidocs.dingtalk.com/i/nodes/abc123
```

If the only thing in hand is an ingredient URL and the ingestion has not produced an internal id, the row is **not** CLOSED — rewrite as BLOCKED with a pointer to the Manual-Prep Request item.

### Knowledge doc backfill (still required)

Also update the knowledge doc with anything new learned during create:

- payload caveats (e.g. "must include `mediaType: 1` even though IDL marks it optional")
- side effects (e.g. "create returns 200 even when name is duplicated; check `data.code`")
- post-create verification queries that turned out to be necessary

Avoid narrative notes anywhere (`seems okay` / `should work` / `created some sample, see above`).

## Failure Classification

When a row cannot be closed, classify the blocker so the user knows exactly what action to take. Every blocked row in the final report carries one of these tags:

Auto-resolvable with user action:

- **Expired auth** — refresh `x-jwt-token` / cookies; user provides.
- **Insufficient permission** — current user lacks role; need a different user or an admin grant.
- **Object exists but does not satisfy scenario** — go back to Phase 3 with tighter filters or to Phase 5 to create a better one (still within attempt budget).
- **Business validation blocked creation** — payload was rejected; payload needs revision (Phase 4 may need re-research).
- **Code path or schema unclear** — Phase 4 was incomplete; sediment more before retrying.
- **Unsatisfied structural invariant** — the sample exists but an invariant (graph connectivity, cross-entity reference, required node config) is not established. The Creation Plan was incomplete; amend with the follow-up calls and re-seek approval.
- **Broken operational precondition (ambient gate)** — the sample's own state is right but an outer container / lifecycle / transient-busy / permission gate is red, so the UI disables the target action. The frontend will grey out step 1. Remediation: either pick a different sample whose whole chain is green, or add follow-up calls (e.g. enable the parent KB) with a Creation Plan amendment. Most often caught by the Phase 6 enable-chain re-check.
- **Step-1 unreachable** — the sample passes existence checks but step 1 of the test cannot execute (e.g. selector locked, node disconnected, required UI state not reachable). Same remediation path as unsatisfied invariant or broken precondition.
- **Ingredient received but ingestion not completed** — user supplied the URL/file/handle, but the skill has no `documentId` (or equivalent internal id) to point at. Either the ingestion call was never made, or it landed in `Processing` / `Failed`. Row must stay BLOCKED; the follow-up Manual-Prep Request asks for either a human-driven ingestion or a substitute source.

Manual-prep-only (escalate via Phase 7.5, do not keep grinding):

- **Different user account needed** — non-admin / viewer / second user not available via APIs.
- **External ingredient needed** — Lark Doc / Sheet / Notion / external HTTP file URL / third-party handle that the user must supply. Closing this item alone does NOT close the test row if ingestion also needs to happen.
- **Ingestion-time interactive auth needed** — the ingestion flow requires a QR code / OAuth consent / OTP / external browser step. Agent-side retry will not succeed; ask the user to drive the ingestion in a logged-in session and return the resulting internal id, or accept a substitute.
- **External content shape needed** — externally-prepared artifact with a specific layout (tables, columns, file format). Typically combined with the ingredient category.
- **Transient runtime state needed** — `Processing` / `Pending` / etc. that cannot be pinned.
- **Failure injection needed** — backend timeout / 500 must be triggered out of band.
- **Third-party credentials needed** — OAuth or downstream service auth outside the current tenant.

Process-level:

- **Attempt budget exhausted** — query/research/create caps were hit without convergence.
- **User rejected creation plan** — record decision; offer manual-prep alternatives.
- **Ambiguous case — needs human judgment at execution time** — operation steps could not be refined to `concrete` (Gate D), and the user declined to sharpen them. Data prep cannot target a specific control/input/observable, so the row is left for manual verification.

Every blocked row in the final report MUST carry one of these tags **and** a corresponding entry in the Manual-Prep Request (when applicable). Do not leave a row in an ambiguous "still investigating" state.
