# Analysis To Data Requirements

Use this reference when the test analysis doc is high-level and you need to convert it into concrete per-case data-selection or data-seeding requirements. This is **Phase 1** of the skill workflow.

The output of this phase is a per-case requirement table. Every later phase (knowledge lookup, code research, query, creation plan, backfill) reads from this table.

## What To Extract From Each Row

**Read both `前置条件` AND `操作步骤` for every row.** The operation steps frequently determine the sample's *initial* state, which the prerequisites prose may not state directly (or worse, may describe in post-action terms like "已有引用…随后将该 KB 禁用").

For every row that needs real data, extract:

- **Page / operation** — what UI surface is exercised
- **Backing entity** — primary entity, plus any required child entity / version / chunk / row
- **Initial state / subtype** — the state the sample must be in **before step 1 runs** (e.g. `Available` for a "disable then observe" row, even when prerequisites prose mentions both Available and Disabled). Walk the operation steps in order; the state required at step 1 is the initial state. Anything mutated by later steps is *not* a sample requirement.
- **Permission requirement** — what the *current user* must be: viewer / member / admin / owner
- **Quantity / shape requirement** — number of rows, chunks, items, parents, references
- **Scenario type** — read / write / config / preview / multi-state / constraint regression
- **Stateful flag** — `stateful` if the operation steps mutate the picked sample (verbs like `禁用 / 启用 / 删除 / 编辑 / 创建 / 切换 / 修改 / 上传`); `read-only` otherwise
- **Multi-sample flag** — whether the row needs ≥ 2 samples in distinct initial states
- **Scenario concreteness** — `concrete` / `vague`. A row is `concrete` only when every operation step names (a) the UI control used, (b) the literal input value or named sample, and (c) the observable effect that proves the step happened. Otherwise it is `vague` and must go through Gate D (Case Refinement) before data prep proceeds.
- **Structural invariants required** — list any non-trivial invariants the sample must satisfy beyond "exists": graph connectivity, child objects, cross-entity references, required node configuration. This column feeds the Phase 5 Creation Plan (which must include follow-up calls to establish each invariant) and the Phase 6 verification (which must re-check each invariant).
- **Operational preconditions (enable chain)** — for every `stateful` / write-type row, record the *ambient* conditions around the sample that the UI uses to enable/disable the button step 1 clicks. Distinct from initial state (which is about the sample) and from structural invariants (which are about the sample's internal shape); this is about the **chain from the outermost container down to the button**. See "Operational preconditions" below.
- **Ingredient vs Sample** — mark whether the requirement depends on an external ingredient (Lark Doc/Sheet/Notion URL, external file, third-party handle). If yes, the row is NOT closed until an ingestion call has produced a verified **internal id** (e.g. `documentId` inside the KB). A user-supplied URL alone is an ingredient, not a sample — see "Ingredient-based rows" below.
- **Ingestion auth mode** — for ingredient-based rows, `non-interactive` / `interactive` / `unknown`. If Phase 4 finds the ingestion flow uses QR code / OAuth consent / OTP / external browser step, it is `interactive`, which forces the row to `manual-prep` regardless of whether the ingredient URL is available.
- **Feasibility** — `auto` / `manual-prep` / `unknown` (see classification rules below)
- **Reuse vs create likelihood** — only meaningful for `auto` rows (will be confirmed in Phase 3/5)

Capture each item explicitly. Do not collapse them into prose.

### Initial-state pitfalls (real failures to avoid)

- Prerequisites cell: `已有一个 Workflow RAG 节点引用某 KB；随后将该 KB 禁用`. Step 1: `禁用该 KB`. **Initial state = Available**, not Disabled. Picking a Disabled KB makes step 1 a no-op and the assertion silently degenerates.
- Prerequisites cell: `存在 1 条已配置且已生成可用内容的记录`. Step 1: `修改 chunking 配置`. Initial state = "configured + has content"; do not pick a freshly-imported sample whose chunks are still `Processing`.
- Prerequisites cell: `存在 1 个 Disabled KB`. Step 1: `打开 Toggle`. **Initial state = Disabled**. Here the prose state and the initial state happen to match — but verify by reading the steps, do not assume.
- General rule: the prerequisites cell describes the *world after setup is done*; the operation steps describe what the test does to that world. The sample must match the world at the **start of step 1**, not the world the prerequisites paragraph ends with.

### Scenario concreteness — vague vs concrete

A row's operation steps must name **control + input + observable effect** for every step, otherwise the data requirement cannot be precise and the downstream executor will improvise.

Vague vs concrete examples:

- Vague: `打开 KB 选择器；Available KB 可选择，Disabled KB 不在可选列表或明确不可选`
- Concrete: `在 RAG 节点 KB 搜索框输入 Available KB 的 name，断言下拉项出现且可点击、点击后保存成功；再输入 Disabled KB 的 name，断言下拉项出现但置灰、点击无反应或有明确禁用提示`

- Vague: `对某内容执行禁用/启用`
- Concrete: `点击 Content 列表某行的状态 Toggle，在确认弹窗点 Confirm Disable；断言 Toast "Disabled" 出现、该行状态变为 Disabled`

- Vague: `运行该 Workflow 的一次检索`
- Concrete: `在该 Workflow 的 Run 页点击 Run 按钮（input 使用样例 query "hello"），断言 Run History 新增一条 Success 记录、结果面板展示非空结果`

When a row is `vague`:

1. Do a targeted UI code pass to discover the actual control (search input vs dropdown vs modal, etc.) and the observable effect.
2. Draft a Case Refinement Proposal that rewrites the vague steps into concrete ones, citing the code found.
3. Present to the user and wait for approval. Do not run Phase 2–6 for the row until it is `concrete`.
4. If the user keeps it vague, classify the row as `manual-prep` with category *ambiguous case*, not as `auto`.

### Observable-anchor check — the assertion must point at something the UI actually shows

Concrete wording is necessary but not sufficient. The *observable* each assertion hangs on must be a real thing the UI, DOM, or an API hook exposes. Without a real anchor, the case is not executable no matter how concrete the operation steps read.

Examples (real case):

- Assertion: `正常召回结果仅来自 Available 内容；Processing/Failed/Disabled 不会作为正常检索结果返回`. This requires, per-result, a readable signal of the source doc's state. Before accepting the assertion, Phase 4 must check the Retrieval Testing result renderer: is there a state tag on each result? a `document_id` cross-lookupable via API? a data attribute? If none, the assertion is **unverifiable as stated** — the test can go green or red on the wrong basis.
- Assertion: `删除成功后列表自动刷新`. Requires the page to emit a Toast or re-fire a list API within a known window. Phase 4 proves which.
- Assertion: `某段文本高亮`. Requires a CSS class or ARIA hint the executor can detect; without it, "highlight" is not observable.

Before locking in Phase 1, walk each assertion and record **one of**:

- UI-anchor: a visible element (tag/label/status pill) per unit the assertion targets
- DOM-anchor: a data attribute / id the executor can read but the user might not see
- API-anchor: an API call the test agent makes alongside the UI step, using ids rendered on the page
- **none → not verifiable**: the assertion cannot be directly confirmed; rewrite to a weaker verifiable form, or split the case so the manual-only portion becomes its own manual-prep child.

Record the anchor per assertion in the Per-Case Requirement Table (e.g. add an `Assertion Anchors` column or inline note). The anchor decides which data the test actually needs (e.g. if the anchor is `document_id` cross-lookup, the data requirement must guarantee distinct ids for same-text content).

### Exception / negative-path cases — match a sub-pattern, then rewrite

Exception and negative-path rows are a distinct class. Gate D's "make it concrete" fix is necessary but insufficient — these cases have four recurring sub-patterns, and each rewrites differently. Misclassifying them produces confidently-concrete but still-unexecutable steps.

#### Detection signals (scan every row for these first)

- trigger-without-mechanism: `触发超时 / 触发失败 / 模拟异常 / 出错时 / 遇到问题时 / 网络异常时`
- negative existence: `不出现 / 不会作为 / 不展示 / 不可选中 / 不召回 / 不参与 / 不存在于`
- silent-failure / robustness: `不要静默失败 / 不能 crash / 应给出明确提示 / 保持稳定 / 体验友好 / 有兜底`
- undefined boundary / illegal input: `输入非法值 / 超出范围 / 异常输入 / 错误格式 / 边界值`
- generic robustness: `系统应稳定 / 兜底正确 / 容错 / 降级合理`

If none present → continue with normal Gate D. If any present → classify and rewrite per the table below before normal concreteness finalization.

#### Sub-pattern rewrite table

| Sub-pattern | Typical wording | Rewrite discipline | Likely child routing |
|---|---|---|---|
| 1. Failure-trigger not specified | `触发超时后页面显示错误`, `检索失败时报错` | **Research first, escalate second.** Do a Phase 4 failure-trigger pass (page error handlers / backend branches / error-code map / PRD "错误/异常" / limits / upstream-state errors / permission-denied / ingestion failures). Enumerate every in-scope trigger as its own child case with concrete input + observable. Only after the research finds NO reachable trigger, escalate as `manual-prep / failure-injection` with the inspected paths cited. | Most triggers end up `auto`; some children (different account, transient state) split out as manual-prep. Pure infra failures (true network partition / backend 5xx) are the only honest failure-injection tail |
| 2. Negative-existence assertion | `Disabled 内容不会作为结果返回` | Expand into paired positive (id `<P>` IS present) + negative (id `<N>` IS NOT present). Data must supply both ids under the same filter condition. Confirm the UI exposes per-item ids (observable-anchor). | Usually `auto` if positive+negative are stable states; split out transient-state siblings |
| 3. Silent-failure / robustness guard | `不是静默失败`, `应给出明确提示`, `保持稳定` | **Research first, escalate second.** Do a Phase 4 error-marker pass: `Toast.error` / `<ErrorState>` / i18n keys / shared error-code map / error boundaries / field-level errors. Pick one literal text + stable DOM hook as the positive marker; tie it to the trigger(s) from Sub-pattern 1. Only after the pass finds NO marker candidate, declare the case not UI-testable, citing what was inspected. | Usually `auto` once a marker is in hand; pure "feels stable" rows drop out of UI coverage |
| 4. Undefined boundary / illegal input | `输入非法值应报错` | Enumerate boundary classes (empty / max-length / max-length+1 / special chars / type mismatch / cross-tenant id). One case per class. For each class, still do the Sub-pattern 3 marker pass to find the literal validation text. | Mix of auto + manual-prep per class |

#### Research-first principle (applies to Sub-patterns 1 and 3)

Exception cases are where the skill is most tempted to shrug and hand everything back as manual-prep. Resist this. The product almost always reaches its error surfaces via deterministic, in-scope triggers — and the literal error text is almost always already in the code (often in i18n files). A single focused Phase 4 pass usually turns `manual-prep / failure-injection` into 2–4 `auto` child cases plus one honest manual-prep residue. Skipping the pass is how real coverage gets silently dropped.

The research targets for these two sub-patterns are enumerated in `references/code-and-api-research.md` under "Failure-Trigger & Error-Marker Research". Use that checklist when doing the pass; cite the inspected paths in any eventual escalation so the stop reason is evidence-backed.

#### Rewrite examples

- Before: `触发检索失败或超时时，页面给出明确错误提示，不是静默失败`. This mixes sub-patterns 1 + 3. Rewrite: split into concrete UI-reachable triggers first. If Phase 4 only finds backend timeout / fault-injection as the trigger, keep it as a separate manual-prep case with the inspected error paths recorded.
- Before: `Disabled / Failed / Processing 内容不会出现在结果里`. Sub-pattern 2. Rewrite: 3 child cases, each with a named positive Available doc id AND a named negative id in the target state; `Processing` child is routed manual-prep (transient), the other two are auto.
- Before: `系统应保持稳定`. Sub-pattern 3 with no marker candidate. Rewrite: refuse the case or move to a stress-test suite; do not pretend it is E2E-executable.
- Before: `输入非法的名称应拦截`. Sub-pattern 4. Rewrite: 5 child cases — empty / whitespace / 256-char / emoji / `<script>` — each with an expected error (literal toast or field-level error text proven by Phase 4).

After rewrite, every child goes through normal Phase 1 finalization (concreteness, observable-anchor, feasibility, stateful flag, structural invariants). Expect most rewrites to cross the mixed-feasibility threshold — that's fine, the split rule handles it.

### Mixed-feasibility rows — split, don't block

A row whose acts or assertions span **different feasibility classes** must be split before any data prep. Examples of mixing:

- one act is a normal query (auto), another is "trigger a backend timeout" (failure-injection manual-prep)
- one assertion covers `Available/Disabled/Failed` (auto) and another covers `Processing` (transient-state manual-prep)
- assertions target two unrelated UI surfaces with separate data requirements

Why splitting matters: stamping the whole row `manual-prep` because of one manual-only act drags perfectly automatable assertions into BLOCKED. Conversely, trying to run the whole row as `auto` silently skips the manual-only parts and produces false green.

Procedure:

1. List each act + each assertion as an atomic unit.
2. Annotate each unit with its own feasibility (`auto` / `manual-prep + category`).
3. If feasibilities differ, draft a Case Refinement Proposal that splits the original row into ≥ 2 child cases, one per feasibility class.
4. Each child inherits the parent's priority/scope tags. Add narrowing tags if helpful (e.g. `[Manual]` on the failure-injection child).
5. Present split to the user for approval (Gate D). After approval, run Phase 1 classification per child.

Splitting heuristics:

- one case per observable anchor (if two assertions read two different signals, they usually want separate cases — especially when one anchor is uncertain)
- one case per state axis at most (Available-vs-Disabled is one axis; Processing is its own axis; failure/timeout is its own axis)
- if a parent case has three axes, it becomes three children; the parent row is removed from the table and replaced with a pointer to the three children

### Structural invariants — "exists ≠ usable"

For any row whose test directly interacts with a composite entity (workflow with nodes, KB with documents/chunks, document with table rows), record the non-trivial invariants the sample must satisfy beyond mere existence. These feed the Phase 5 Creation Plan and the Phase 6 verification.

Common invariants to record:

- **Graph connectivity** — for a workflow-with-KB-RAG-node row: graph must have `start → ... → KB node`. A bare workflow from `workflow/create` has no connected graph; the KB selector in the UI is unreachable until wired.
- **Child objects** — document with ≥ N chunks; table document with ≥ N rows; workflow with ≥ 1 non-draft strategy.
- **Cross-entity references** — "workflow that references KB X" row needs the reference saved into the workflow, not just both objects existing independently.
- **Node configuration** — required upstream inputs on a node; required form fields set; correct node type.
- **Published / draft state** — step 1 may require a published strategy, not a draft.

Do not merge these into the generic "shape / volume" column — structural invariants are usability contracts and are re-checked in Phase 6 by inspecting specific fields in detail responses. Mixing them with "≥ 3 KBs total" style counts loses the verification anchor.

### Operational preconditions — the ambient gating chain

A UI write action is usually enabled by a **chain** of booleans: outer container OK → intermediate parent OK → resource OK → permission OK → transient gates OK → button clickable. If any link is broken, the button greys out regardless of the sample's own state. This is a distinct axis from both initial state (sample-internal) and structural invariants (sample-shape).

For every `stateful` / write-type row, list the chain in positive form — things that must be true for the button to be interactive:

- **Container-enabled gate**: outer container is in its operable state (e.g. `parent KB is Available`)
- **Resource-state gate**: the resource itself is in an operable state (e.g. `document is Available`, not Failed/Processing/Disabled)
- **Permission gate**: the current user has the frontend's actual check (not just "has token"; Phase 4 proved which helper — `canEdit`, `isAdmin`, `administrators.includes(uid)`)
- **Lifecycle gate**: the object is in an operable lifecycle phase (e.g. workflow is DEVELOP, not Published)
- **Transient busy gate**: no blocking background job is in progress (e.g. no running import / export / training)
- **Row-count / shape gate**: the operation requires ≥ N child items before the trigger is rendered (e.g. row-edit icon only appears when `rowCount ≥ 1`)
- **Cross-reference gate**: the sample is not currently locked by another entity (e.g. not referenced by a running export)

Failure modes these catch (real examples):

- Picked a table document whose own state was Available, but the parent KB was Disabled. Edit/Delete buttons greyed. **Container-enabled gate broken.**
- Picked a workflow that was Published. Strategy-update rejected by backend. **Lifecycle gate broken.**
- Picked a doc that was currently mid-import (`Processing` chunk job). Chunk-config page rendered with a "正在导入" banner and all inputs disabled. **Transient busy gate broken.**
- Picked a KB whose `administrators` list did not contain the current uid. Page loaded, rows visible, but write buttons hidden. **Permission gate broken.**

Record the chain the way Phase 4 returns it from code (each term has a code-backed field it can be checked against), then use it in:

- **Phase 3 filtering** — reject any candidate whose chain is not fully green, using the detail-API fields Phase 4 pointed at.
- **Phase 5 creation plan** — ensure the creation sequence leaves every term green (may need follow-up calls to flip a term, e.g. `kb/update status=Available` if the factory created the KB as Disabled by default).
- **Phase 6 verification** — read back each term from the detail response; the button is "clickable" only when all terms are true.

### Ingredient-based rows — do not close on the URL

Some rows need an externally-sourced artifact (Lark Doc/Sheet, Notion page, external file URL, third-party account handle). For every such row, extract the requirement as **three separate facts**, not one:

1. **Ingredient** — the raw external material (URL/file/token). Supplied by the user via a Manual-Prep Request. Does NOT close the row.
2. **Ingestion call** — the API inside the target system that imports the ingredient and produces an internal id (e.g. `POST /api/v1/knowledge_base/document/import_from_lark` returning `documentId`). This is the step that turns an ingredient into a sample.
3. **Internal sample** — the ingested entity inside the target system, verifiable via the containing entity's detail API, in a UI-exercisable state (typically `Available`; not `Processing` / `Failed`).

Phase 4 must additionally check the ingestion's **auth mode** (see "Ingestion auth mode" column above). If the flow pops a QR code / OAuth consent / OTP step the first time a given account uses it, the row is `manual-prep` with category *ingestion-time interactive auth* — the ingredient alone is not enough, and agent-side retry will not unblock it.

Ingredient-vs-sample pitfalls (real failures):

- The user sent a Lark Doc URL. The skill wrote the URL into `前置条件` and marked the row CLOSED. Later the executor opened the KB page and found zero imported docs. **The ingredient never became a sample.** The row should have stayed BLOCKED with a follow-up Manual-Prep Request asking the user to either (a) complete the import in a logged-in session and give back `documentId`, or (b) substitute a different document source whose import is non-interactive.
- A row needed "KB with a Lark Doc containing a table" (specific external content shape + ingredient). Phase 4 did not check auth mode; automation tried the import, hit Feishu QR code, and produced a half-imported document in `Processing`/`Failed` state that looked present in list APIs but was unusable in the UI. Interactive auth must be flagged in Phase 1, not discovered at execution.

## Feasibility Classification

Decide each row's Feasibility before any API or code search. The classification routes the row to the rest of the workflow.

Mark as **`manual-prep`** (skip Phase 2–6, go straight to Phase 7.5) if the row matches any of:

- **Different user account** — needs a non-admin / viewer / member account, or any account other than the current authenticated one. Account provisioning is out of scope of the codebase APIs in scope.
- **External ingredient needs ingestion** — needs an ingredient (Lark Doc/Sheet, Notion, external HTTP file, third-party handle) that must be imported into the target system to become a sample. The ingredient URL is not itself a sample. Even when ingestion is automatable, the ingredient itself must come from a human.
- **Ingestion-time interactive auth** — the ingestion flow opens a QR code / OAuth consent / OTP / external browser step. No agent-side retry recovers from this; must be solved by a logged-in human session or substituted with a non-interactive ingestion path.
- **Specific external content shape** — needs an externally-prepared artifact whose content matters (e.g. "a Lark Doc that contains an embedded table", "a CSV with a specific header row layout"). Typically combined with the ingredient category.
- **Transient runtime state** — needs a state that exists only momentarily (`Processing`, `Pending`, `Uploading`). These cannot be deterministically held; either pause a real run.
- **Failure injection** — needs a network/timeout/backend failure to be triggered. Out of band.
- **Third-party credentials / OAuth tokens** — needs auth surface outside the current tenant's JWT.

Mark as **`auto`** if the row needs an entity the codebase exposes a list/create API for, with the current user's auth, in the current tenant, AND any required ingestion step is non-interactive (confirmed in Phase 4).

Mark as **`unknown`** only when you cannot decide from the row alone. Resolve to `auto` or `manual-prep` with a *single* quick code-research pass; do not let `unknown` survive into Phase 3.

Examples (from target-system KB analysis):

- `权限：User 仅可查看不可管理` → **manual-prep** (different user account)
- `导入 Lark Doc（一次性快照）` → **manual-prep** (external ingredient needs ingestion + typically ingestion-time interactive auth for first-time Feishu OAuth)
- `Lark Doc 内表格支持 chunking` → **manual-prep** (external ingredient + specific external content shape; also interactive-auth for the ingestion)
- `导入 Lark Sheet（一次性快照）` → **manual-prep** (external ingredient needs ingestion; check interactive-auth in Phase 4)
- `预览范围约束：Lark 文档不提供原生预览` → **manual-prep** (depends on an ingested Lark Doc — the ingestion step is a prerequisite, even though this row's own operation is read-only). The row closes only when the containing KB's `content/list` actually shows an imported Lark Doc.
- `Retrieval Testing：Processing 内容不参与召回` → **manual-prep** (transient runtime state)
- `Retrieval Testing：失败/超时错误可见` → **manual-prep** (failure injection)
- `编辑 KB 元信息` / `创建 Advanced workflow` / `表格 Row ≥ 11` → **auto**

Note: a row that depends on an already-ingested artifact (e.g. "KB contains at least one imported Lark Doc") is **not** a separate category from the ingestion row itself — if the upstream ingestion row is blocked by manual prep, every downstream row that depends on the same ingested artifact is also BLOCKED until the ingestion completes. Track this as a dependency in the Manual-Prep Request, not as "multiple independent manual preps".

## Translation Patterns

Common analysis wording → concrete requirement:

- `编辑页` → writable object **and** current user has edit/admin permission
- `查看页` → readable object; write permission unnecessary
- `配置页` → object exists **and** the configuration surface is enabled (not in a state that disables it)
- `禁用态` → sample whose status is actually `Disabled` (not merely uneditable)
- `分页` → enough rows to cross the page-size threshold
- `批量操作 / 限制 N` → enough child items to hit the bulk limit (and a case to exceed it)
- `预览 / 详情` → object plus any required child object or version
- `引用关系` → parent and referenced object both exist, **with the link already established**
- `多状态对比` → distinct samples for each state (Available / Processing / Failed / Disabled)
- `权限：User 不可管理` → a non-admin user account in the same tenant space

## Questions That Force Clarity

Ask internally before any API call:

- What exact entity ID(s) must appear in the page URL?
- Does the page depend on a child ID in addition to a parent ID?
- Is the scenario validating read behavior or write behavior?
- Does the user need to be owner / admin / editor, or merely have access?
- Is one sample enough, or are multiple state-specific samples required?
- Does the test row also imply a *negative* sample (e.g. one that should not appear)?

## Per-Case Requirement Table Template

Use this exact shape (markdown table is fine; the columns are the contract):

| Case ID | Page / Operation | Entity (+ child) | Initial State (at step 1) | Permission | Shape / Volume | Scenario Type | Stateful? | Multi-Sample? | Scenario Concreteness | Structural Invariants | Operational Preconditions (Enable Chain) | Ingredient? | Ingestion Auth | Feasibility | Reuse vs Create |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KB-list-1 | KB list page | Knowledge Base | ≥3 KBs: 1 Available+OwnedByMe, 1 Available+notOwnedByMe, 1 Disabled; ≥1 description >2 lines | Admin | ≥3 KBs total | read + filter | read-only | Yes (3) | concrete | none | n/a (read-only) | no | n/a | auto | Likely reuse |
| KB-edit-1 | Edit KB modal | Knowledge Base | Available, name unique | Admin + in `administrators` | 1 sample + 1 extra for name-collision | write | stateful | Yes (2) | concrete | none | `kb.status=Available`; `currentUid ∈ kb.administrators` | no | n/a | auto | Reuse if owner match |
| KB-disable-ref-1 | Disable KB then run RAG (referenced KB unaffected) | KB + Workflow RAG node referencing it | **Available** KB; workflow already references this KB | Admin on both | 1 KB + 1 workflow with the reference wired | write/multi-step | stateful (KB will be disabled) | No | concrete | **graph: start → KB node connected**; **cross-entity: workflow's KB node config points to the KB id**; workflow is Advanced + has an editable strategy | `kb.status=Available` (pre-disable); `workflow.type=DEVELOP`; `currentUid ∈ kb.administrators ∧ workflow.administrators` | no | n/a | auto | **Likely create full sequence** (workflow/create → strategy/update with connected nodeList+edgeList → set KB node's selected KB) — never a bare workflow/create |
| WF-rag-select-1 | KB selector in RAG node (Available selectable, Disabled not) | Workflow + RAG node + 1 Available KB + 1 Disabled KB | Workflow Advanced + editable strategy + RAG node wired; both KBs exist with **known searchable name/id** | Admin | 1 workflow + 2 KBs | write/multi-sample | stateful (may save selection) | Yes (2 KBs) | **originally vague** — needed Gate D refinement to "type name/id into search box; assert enabled vs greyed". After refinement: concrete | graph: start → RAG node connected; RAG node input wired; KB names contain a distinctive searchable substring | `workflow.type=DEVELOP`; RAG node upstream wired (both Disabled and Available KB are simply candidates, their states drive the enable/disable of the dropdown item, not of the selector itself) | no | n/a | auto | Create workflow + graph; reuse Available/Disabled KBs if suitable |
| KB-doc-table-edit-1 | Table document detail — edit 1 row, bulk-delete 10 rows, bulk-delete 11 rows | KB + table document + table rows | Doc Available; `rowCount ≥ 11`; no running import | Admin | 1 KB + 1 doc + ≥ 11 rows | write / bulk | stateful | No | concrete | doc has ≥ 11 rows; all rows editable (no mid-import rows) | **`parentKb.status=Available`** (else toolbar read-only); `document.state=Available`; `currentUid ∈ parentKb.administrators`; `!document.hasRunningImport` | no | n/a | auto | Usually create fresh KB + doc unless existing candidate's entire chain is green |
| KB-perm-1 | KB list page (User role) | KB + non-admin account | Any KB visible; account is non-admin | non-admin | 1 KB + 1 account | read + permission | read-only | No | concrete | none | `kb.status=Available`; verifier checks that write buttons are hidden for non-admin | no | n/a | manual-prep | Needs user-provided account |
| KB-import-lark-1 | Import Lark Doc (verify snapshot semantics) | KB + Lark Doc ingredient → ingested document | Available KB + a reachable Lark Doc URL; post-import document must reach `Available` before the snapshot assertion runs | Admin | 1 ingredient + 1 resulting internal document | write + ingestion | stateful | No | concrete | **internal invariant: `content/list` shows document whose `source=<lark_url>` and `state=Available`** | `kb.status=Available`; `currentUid ∈ kb.administrators`; `!kb.hasRunningImport` | yes (Lark Doc URL) | **interactive** (first-time Feishu OAuth/QR) | manual-prep | Need ingredient URL **and** human-driven ingestion session returning `documentId`; or substitute a non-interactive source |
| KB-preview-lark-1 | Lark Doc preview is external-link-only | KB containing ≥ 1 imported Lark Doc document | KB has ≥ 1 document with `source=lark` in state `Available` | Admin | 1 KB + 1 ingested document | read-only | read-only | No | concrete | **depends on the ingested document produced by KB-import-lark-1** | n/a (read-only) | no (depends on upstream) | n/a (inherits from upstream) | manual-prep | BLOCKED until `KB-import-lark-1` produces a `documentId`; do not close on "user gave me the Lark URL" |
| KB-rt-1 | Retrieval Testing (Processing exclusion) | KB content in `Processing` | content held at `Processing` during test | Admin | 1 sample | multi-state | read-only | Yes (per state) | concrete | none | n/a (read-only) | no | n/a | manual-prep | Processing is transient |

Per-row notes accepted alongside the table:

- ownership detail (e.g. "current user uid: `dengshiqi.17` must appear in `administrators`")
- the *negative* sample requirement (e.g. "needs 1 KB the current user does **not** own, to verify Owned-by-me toggle")
- known anti-patterns (e.g. "do not reuse demo KB X — it is shared and not safe to mutate")

## Anti-Patterns

Reject the row and re-extract if you find yourself writing:

- `some available data`
- `a sample should exist`
- `probably one KB is enough`
- `any workflow will do`

These are not requirements; they are wishes. Sharpen them into concrete constraints before moving to Phase 2.

## Handing Off To The Next Phase

After Phase 1, the requirement table routes rows by Feasibility:

- `auto` rows →
  - **Phase 2** uses entity + scenario to look up business knowledge.
  - **Phase 3** uses state / permission / shape to build list-API filters.
  - **Phase 5** uses the same fields when drafting the Creation Plan.
- `manual-prep` rows → **Phase 7.5** directly. Each one becomes a line item in the Manual-Prep Request, telling the user exactly what is needed (account uid, link URL, file artifact, etc.).
- `unknown` rows → resolved with a single Phase 4 pass, then re-routed.

Keep the table in the working scratchpad / spec directory so later phases (and future runs) can refer back to it.
