---
name: prd2case-api
description: Generates text-based API test cases (case.md) from PRD and Spec documents. These cases serve as inputs for subsequent API automation testing.
user-invocable: true
---

## User Input

```text
$ARGUMENTS
```
**Instruction**: You **MUST** process the user input if it is not empty. If `$ARGUMENTS` contains a hyperlink, use the appropriate tool (e.g., `lark-docs` MCP for Lark documents) to read its content and replace the link with the extracted text before proceeding.

---

## [Global Rules] (Highest Priority)

**Rule 1: Strict Search Scope (No Global Scanning)**
- **IDL Discovery**: Restrict searches EXCLUSIVELY to `idl/` (or `IDL/`) directory and its subdirectories.
- **Dependency Resolution**: When resolving setup APIs for dynamic parameters, search ONLY within the specific IDL file defining the target API, **OR** sibling IDL files in the same directory/domain (to support read/write separated architectures).
- **Forbidden Actions**: NEVER use broad `grep`/`ls` across the repository. NEVER scan business code (`.go`, `.java`, `.ts`, etc.). Do NOT hallucinate APIs if not found.

**Rule 2: Read Efficiency**
- Use targeted reads (`grep -A <lines> "<pattern>" <file>`) for large structured files (>500 lines) instead of full reads.
- Reuse generated data: one `[tt-nova-datagen]` result applies to all matching scenarios; deduplicate before invocation.

**Rule 3: Variable Source Traceability (MANDATORY)**
Every `{{variable}}` reference in `case.md` **MUST** have a clearly traceable source from exactly ONE of these categories:
1. **Suite Static Global Variable** — Declared in Section 1.3 "Global Context Variables" and safe to copy into **any per-API Go test file** (source: User Provided / Utility Function / Model Generated). It MUST be static, replay-safe, non-secret, and independent of any test case execution result.
2. **API/File Context Variable** — Declared in the API-level context section for the API(s) that consume it. Use this for values that should only be emitted into the corresponding per-API Go test file, including API-specific constants, environment business samples, or dynamic setup helpers.
3. **Local Variable** — Extracted via "Variable Extraction" from a step **within the SAME test case**.
4. **Data Dependency** — Declared in the test case's "Data Dependencies & Local Variables" section (source: `[tt-nova-datagen]`, `[Manual Prompt]`, or Knowledge Base).

**Forbidden**:
- Cross-test-case local variable references. A local variable extracted in TC-001 **CANNOT** be used in TC-002.
- Promoting a runtime-extracted value from a specific test case into Section 1.3 Global Context Variables.
- Treating resource references (`*_id`, `*_uid`, `*_key`, `*_token`, etc.) as suite globals by default.

If a value is needed across multiple test cases, handle it by scope:
- **Same test case** → keep it as a Local Variable.
- **Multiple cases under the same API** → declare an API/File Context Variable or add a per-API setup/helper step that each generated Go file can own independently.
- **Multiple APIs** → re-resolve it per API, or mark it as an environment business sample/user-provided value only when it cannot be discovered safely.
- **Never** rely on one test case's execution order to provide data to another test case.

**Rule 4: Post-Generation Resolution First**
- During initial scenario generation, you MAY introduce placeholder variables such as `{{target_item_id}}`, `{{project_id}}`, `{{owner_user_id}}` when the exact source is not yet confirmed.
- Do **NOT** force dynamic ID resolution during scenario generation.
- After all batches are written, you **MUST** re-open `case.md`, identify which parameters actually require dynamic resolution or user input, and resolve them in a dedicated post-processing phase.

**Rule 5: Go Test Split Compatibility**
The generated `case.md` will later be converted into Go tests where the same API is placed in the same file and different APIs may be placed in different files. Therefore:
- Section 1.3 MUST contain only suite-level static variables that are safe for all API files.
- API-specific variables MUST include explicit consumer API(s) and MUST NOT be emitted into unrelated API files.
- Dynamic resource references should become local setup steps or per-API helpers, not package-level constants.
- Secrets and runtime auth material (tokens, cookies, auth headers) MUST be represented as runtime environment requirements, not committed as Global Context Variables.

**Rule 6: HTTP `Content-type` Header (MANDATORY)**
Every HTTP request step in `case.md` **MUST** include a `Content-type` entry under `Request Parameters -> Headers`, even when the request is `GET` or has no body. The value MUST be filled according to the actual interface protocol / request encoding discovered from IDL annotations, API docs, or spec examples; do **NOT** blindly default to JSON.

Required mapping examples:
- JSON HTTP API / HTTP-wrapped RPC JSON payload → `Content-type: application/json`
- Form URL encoded API → `Content-type: application/x-www-form-urlencoded`
- Multipart upload API → `Content-type: multipart/form-data`
- Protobuf / binary HTTP API → `Content-type: application/x-protobuf` or the exact binary media type documented by the interface
- Plain text API → `Content-type: text/plain`

If the actual request encoding cannot be determined after the allowed scoped discovery, ask the user to confirm it; never omit `Content-type` from an HTTP test case.

---

## Context & Settings

1. **Language Setting**: Read `preferred_language` from `.ttadk/config.json` (default: `en`). Overridden by `.test_config.ini` `[prd2case]` `language`. All outputs MUST use the resolved language.
2. **Business Knowledge**: If `.test_config.ini` has `business_knowledge_path`, read it (use local Read or url fetch tools).
   - **Directory Strategy**: If the path is a directory, do NOT blindly read all files. Prioritize reading files whose names match the current API/module keywords, or strictly read `index`/`README` files first to get an overview before reading specific files on demand.
   - Output: *"Querying business knowledge base from `{path}`..."*.
   - Apply its domain rules to test scenarios.

---

## Workflow

### Phase 0: Bootstrap
1. **Find repo root**: `git rev-parse --show-toplevel`. On failure, abort.
2. **Read configs**: Read language config and test config as defined above.
3. **Read Specs**: Locate `spec.md` from `$ARGUMENTS` or `specs/`. Read it. On failure, abort.
4. **Read Task Context**: Check `FEATURE_DIR/test/task.md` (if exists). Extract authorization info for test cases.

### Phase 1: IDL & Schema Discovery
1. **IDL Path**: Locate IDL path via spec.md. If missing, strictly follow **Rule 1** to find it. If still not found, ask the user to provide the exact path.
2. **API Schema**: Extract response schema/examples from spec.md or linked docs (use `lark-docs-skill` for lark urls, `Read` tool for local files).
   - **Link Depth Limit**: ONLY parse links directly referenced in spec.md; do NOT recursively follow secondary links.
   - Do NOT scan repo for schemas.
3. **Protocol Detection**: Check IDL/codebase to determine if it uses **HTTP wrapping RPC**.
4. **Confirmation**: Ask the user: *"HTTP or RPC interface for test cases?"* AND confirm the current branch. **Proceed only after confirmation.**

### Phase 2: API Analysis & Selection (Single-Round)
1. **Analyze Affected APIs**: List all affected APIs containing Name, PSM, Endpoint, and Logic Changes.
2. **User Selection**:
   - Build a numbered list of all affected APIs (e.g., `1. SearchMusic - GET /api/v1/search`, `2. ...`).
   - Use `AskUserQuestion` to ask user: *"Which APIs do you want to generate test cases for?"* (support multiple selections, default: all).
   - **STOP AND WAIT** for the user's reply in the chat.
3. **Parse Selection**: Parse the user's choice to form `selected_apis`. If none selected, abort.

### Phase 3: Test Scenario Design & Writing (Batched)
To avoid context limit, process `selected_apis` in chunks of **maximum 3 APIs per batch**.
For each batch, do the following:

#### 3A: Generate Scenarios
Apply these rules to generate cases for the current batch:
- **Test Count**: Base cases on spec `API 自动化` points. Merge points with identical requests.
- **Negative Cases**: Ensure a **minimum** baseline of `N+1` negative cases per API (`N` = number of required parameters), including missing params and invalid values. If the spec or business knowledge defines additional negative scenarios (e.g., authentication failures, rate limiting, unauthorized access, concurrency conflicts), you MUST generate extra test cases for them.
- **Pagination**: MUST include limit/offset boundary scenarios.
- **Placeholder Parameters Allowed**: If a scenario needs a resource identifier or other unresolved runtime value, use a clearly named placeholder variable such as `{{target_order_id}}`, `{{seed_project_id}}`, or `{{owner_user_id}}`.
- **Do Not Resolve Yet**: Do **NOT** search for `List/Create/Get` setup APIs during this step unless the source is already explicit in spec.md or the current API schema.
- **Mock Rules (Downstream)**: ONLY mock for abnormal downstream testing (timeout, panic, errcode) or hard-to-reach states. Default to RPC mode. Must output valid JSON matching downstream IDL.
- **Case Priority (P0 / P1 / P2)** — assign **Priority** on each TC (respect ff `PRIORITY` filter; omit cases outside the selected set):
  - **P0**: Core **positive** happy-path scenarios from spec `API 自动化` / main business flow (no §3 Mock).
  - **P1**: Key **negative** or important variation scenarios **without** downstream mock — e.g. missing/invalid required params, auth/business negatives reachable without §3.
  - **P2**: Edge, boundary, optional-field, or hard-to-reach scenarios; **MANDATORY: any case that requires §3 Mock Setup MUST be P2** (including rows in §3 for that Case ID, or Data Dependencies referencing mock / §3). This rule **overrides** positive/negative-based defaults.
  - When writing §3, every listed Case ID MUST already be **P2** on its TC block.
- **HTTP Header Rule**: For every HTTP step, include `Content-type` in `Headers` and set it to the real request encoding (`application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`, `application/x-protobuf`, `text/plain`, etc.). This applies to `GET` requests and empty-body requests as well; `Content-type` must not be omitted.
  
#### 3B: Assertion Rules (Strict 3-Step Workflow)
For every scenario generated, build assertions sequentially:
- **Step 1: Baseline (Mandatory)**: `1` Outer HTTP status/RPC equivalent + `1` Inner JSONPath on top-level business status (e.g., HTTP uses `status_code == 200`; RPC uses `$.BaseResp.StatusCode == 0`).
- **Step 2: Field Categorization (Single Tag)**: Identify fields in response. Assign ONLY the highest-priority tag:
  - **[Priority 1] Scheme Change**: Newly added/modified fields by current PRD.
  - **[Priority 2] Business Key**: Core business fields (IDs, statuses).
  - **[Priority 3] High-Volatility**: Optional/conditional fields. Only assert type/non-null if present.
- **Step 3: Coverage Generation**:
  - *Positive Scenarios*: Generate at least one assertion for EVERY tag present. (For P3, only assert type/non-null if present; don't fail if absent).
  - *Negative Scenarios*: If no business data is returned, skip P1/P2/P3 assertions and document inline (e.g., `// Negative scenario: no business data`).
  - *Constraint*: Precise `jsonpath` ONLY. "Matches expectations" is forbidden.
  - *Runtime-compatible syntax only*: assertions MUST use the api-mind Go runtime supported syntax: `status_code`, `$.path`, `len($.path)`, `typeof($.path)`, operators `==`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `contains`, and literal values. Do NOT emit `StatusCode`, `.length`, `IS NOT NULL`, or `matches`; use `status_code`, `len(...)`, `!= null`, or a supported `contains`/non-empty assertion instead.

#### 3C: Batched Write to `case.md`
- **File path**: `<target_dir>/test/case.md`
- **First Batch**: Copy `resources/api_test_template.md` to path. Write current scenarios.
- **Subsequent Batches**: Append to the existing file. Do NOT overwrite.
- **Progress**: Output *"Batch N written to case.md ({api_names})"* to the user.

#### 3D: Update Variable Registry (Cross-Batch Tracking)
After each batch is written, maintain an in-memory **Variable Registry** tracking all variables defined so far:
- **Suite Static Global Variables**: All entries from Section 1.3 that are safe for every per-API Go test file.
- **API/File Context Variables**: Variables declared for specific consumer API(s), including API-specific constants, environment business samples, and per-API dynamic setup helpers.
- **Local Variables (per test case)**: Each TC's extracted variables.
- **Data Dependencies**: Each TC's declared data dependency variables.

**When generating the next batch**, consult this registry:
- If a needed variable already exists as a **Suite Static Global Variable** → reference it directly.
- If a needed variable already exists as an **API/File Context Variable** and the current test case belongs to one of its consumer APIs → reference it directly; otherwise do not use it.
- If a needed variable exists only as a **Local Variable** in a previous TC → you **MUST** re-extract it in the current test case via its own setup step + Variable Extraction, or create a per-API setup/helper if the current API needs it repeatedly. Do **NOT** promote runtime-extracted values to Section 1.3.
- If a needed variable does not exist at all → declare it as a placeholder or a **Data Dependency**, to be resolved in later phases.

*(Repeat 3A-3D until all selected APIs are processed)*

#### 3E: Transition to Phase 4 (MANDATORY — No User Confirmation)
After all batches are written:
- **Immediately proceed to Phase 4** without asking the user.
- Phases 4, 5, and 6 are mandatory continuation steps that complete
`case.md` to a runnable state. They are NOT optional follow-ups.
- Do NOT output a summary and ask "shall I continue?" — only pause
if an unresolvable error or blocker is encountered.

### Phase 4: Post-Generation Dynamic Parameter Resolution
After all batches have been written, re-open the complete `case.md` and resolve only the parameters that are actually needed.

#### 4A: Identify Candidate Parameters
1. Parse the entire `case.md` for all `{{...}}` variable references.
2. Identify **candidate dynamic parameters** by checking:
   - variable names that indicate identifiers or runtime-bound references, such as `*_id`, `*_ids`, `*_uid`, `*_code`, `*_key`, `*_token`
   - variables used in request path/query/body fields for resource targeting, ownership, parent-child linkage, or mutation preconditions
3. Exclude variables that are clearly:
   - utility values (`timestamp`, `uuid`, `nonce`)
   - fixed constants already declared in Section 1.3 or the matching API/File Context Variables section
   - values already extracted within the same test case
4. Build a resolution list of only the parameters that still lack a confirmed source.

#### 4B: Decide Resolution Strategy Per Parameter
For each unresolved candidate parameter, determine exactly ONE strategy:

1. **Dynamic IDL Resolution**
   Use this when the value is a resource identifier that can likely be obtained from an API in the same IDL file or its domain siblings.

   **4B.1 Setup API Discovery for Update/Delete/Mutation Targets (MANDATORY)**
   - When the target API is an `Update*`, `Delete*`, `Remove*`, `Patch*`, `Enable*`, `Disable*`, `Bind*`, `Unbind*`, or other mutation API that requires an existing resource identifier (for example `{{target_xxx_id}}`, `{{xxx_id}}`, `{{xxx_uid}}`, `{{resource_key}}`):
     1. Search for setup APIs within the IDL file defining the target API, **OR** sibling IDL files in the same directory/domain (to support Read/Write separated architectures).
     2. Candidate setup API names MUST include resource-oriented variants:
        - `Create<Resource>` / `BatchCreate<Resource>` 
        - `List<Resource>` / `<Resource>List` / `Search<Resource>` / `Query<Resource>`
        - `Get<Resource>` (ONLY when input identifier is already available from the same test case or context)
     3. **Setup Strategy Preference (Isolation First)**:
        - **ALWAYS prefer `Create` / `BatchCreate`** for ANY mutation targets (`Update*`/`Delete*`). Creating a fresh, isolated resource per test case is mandatory to prevent flaky tests caused by shared data state.
        - **Fallback to `List` / `Search`** ONLY if a `Create` API is strictly unavailable or not defined in the scope.
     4. If a setup API is selected, convert the single-API case into a multi-step scenario:
        - Add the setup API as `Step 1` before the target action.
        - The setup step MUST include its own API Contract, Request Parameters, and Variable Extraction.
        - **Extraction Rule**: Use a concrete JSONPath. If extracting from a List/Search response, you MUST use explicit array indexing (e.g., `$.BaseResp.Data.List[0].ID`).
        - Assign it to a local variable (e.g., `{{LOCAL_TARGET_RESOURCE_ID}}`) consumed by the subsequent target step.
     5. **Dependency Depth Limit**: If the chosen Setup API itself requires a dynamic resource ID (e.g., `parent_id`), do NOT search for a second-level setup API (max depth = 1). Directly mark that secondary requirement as `User Provided (Env Business Sample)` or `Data Dependency` to avoid recursive loops.
     6. **Teardown**: If a `Create` API is used as setup, you SHOULD append a `Delete<Resource>` (if available) as the final step of the test case to clean up `{{LOCAL_TARGET_RESOURCE_ID}}`.
     7. If no setup API is found in the related IDLs, do NOT guess. Fall back to **User Provided** or **Generated Data Dependency**.

   **General Dynamic Resolution Rules**
   - Search within the defining IDL file or its immediate domain siblings.
   - If found and used as setup:
     - Add the setup API as a **normal test step** with **Variable Extraction** (using precise JSONPath).
     - Register the extracted variable as a **Local Variable** when used only within the same test case.
     - If reused by multiple cases of the same API, declare an **API/File Context Variable** with scope `DynamicSetup` to document the setup API + extraction JSONPath, but still ensure each generated case or per-API helper performs its own setup (do not rely on cross-case execution order).
     - If reused by multiple APIs, re-resolve it per API or require an environment business sample; do **NOT** promote the runtime-extracted value to Section 1.3.

2. **User Provided**
   Use this when the parameter depends on:
   - a fixed test account
   - a tenant/environment-specific value
   - an external system resource
   - a business precondition that cannot be safely created or discovered from the same IDL
   Then:
   - Add it to **Section 1.3 Global Context Variables** only if it is suite-wide, static, non-secret, and safe for every per-API Go test file
   - Otherwise add it to the relevant API/File Context Variables section with explicit consumer API(s) and scope `APIStatic` or `EnvBusinessSample`
   - Mark source as `User Provided (Constant)` or `User Provided (Env Business Sample)`
   - Use placeholder format: `[USER_INPUT_REQUIRED: explain exactly what value is needed and why]`

3. **Generated Data Dependency**
   Use this when the value should be created per test case and is not best resolved from existing resources.
   Then:
   - Add it to the relevant test case's **Data Dependencies & Local Variables**
   - Use `[tt-nova-datagen]` if suitable, otherwise `[Manual Prompt]`

4. **Utility Function**
   Use this for generic runtime values like UUID/timestamp/random suffix.
   Then:
   - Add it to **Section 1.3 Global Context Variables** only if it is reusable across APIs and does not encode API-specific state
   - Otherwise add it to the relevant API/File Context Variables or the test case's Data Dependencies & Local Variables section
   - Mark source as `Utility Function`

#### 4C: Resolution Constraints
- Do **NOT** attempt dynamic resolution for every `*_id` blindly.
- Prefer **User Provided** over dynamic resolution when the resource is environment-specific or requires business-state assumptions; however, for Update/Delete/Mutation target IDs, you MUST first perform the 4B.1 setup API discovery before falling back.
- Do **NOT** search outside the target IDL file and its immediate domain siblings.
- Do **NOT** introduce setup APIs that are not explicitly found.
- If multiple setup APIs are possible, choose the one with the lowest dependency cost and the clearest extraction path (e.g., preferring Create over List for isolation).
- If no reliable resolution path exists, mark it as **User Provided** instead of guessing.
- Do **NOT** put tokens, cookies, auth headers, or other secrets into Section 1.3. Represent them as runtime environment requirements in Global Pre-conditions / task context.

### Phase 5: Variable Validation & Resolution
After dynamic parameter resolution, perform a comprehensive variable audit:

1. **Scan**: Parse the entire `case.md` for ALL `{{...}}` variable references.
2. **Classify**: For each variable, identify its source:
   - Declared in Section 1.3 "Global Context Variables" and scope is suite-static / utility / model constant → **OK**
   - Declared in an API/File Context Variables section whose consumer API matches the test case API → **OK**
   - Extracted via "Variable Extraction" in the same test case → **OK**
   - Declared in the same test case's "Data Dependencies & Local Variables" → **OK**
   - None of the above → **ORPHANED**
3. **Resolve Orphaned Variables**:
   - Suite-wide fixed constant → add to Section 1.3 as `Model Generated (Constant)` with scope `SuiteStatic`
   - API-specific fixed constant → add to that API's API/File Context Variables with scope `APIStatic`
   - User-specific/environment-specific resource sample → add to the relevant API/File Context Variables as `User Provided (Env Business Sample)` unless it is truly suite-wide and safe for every API file
   - Per-case generated value → add as test-case Data Dependency
   - Utility value → add to Section 1.3 as `Utility Function` only if reusable across APIs; otherwise use API/File Context or test-case-local data dependency
4. **Update `case.md`**: Apply all resolutions by editing the file. Ensure Section 1.3 contains only suite-static globals, API-specific variables are declared with consumer API(s), and every test case declares all local variables and data dependencies.
5. **Report**: Output a summary:
   - *"Variable audit complete: N variables scanned, M unresolved after generation, X dynamically resolved from IDL, Y added as user input/env samples, Z added as data dependencies, W added as utility/suite constants, V added as API/File context variables."*

### Phase 6: Resolve Data Dependencies
1. Parse `case.md` for all `[tt-nova-datagen]` tags and deduplicate them.
2. If the `Skill` tool is available and `tt-nova-datagen` is supported, invoke the Skill. Replace the tags in `case.md` with generated results.
3. If unsupported or unavailable, strictly replace the tag with `[Manual Prompt]` in the markdown file and report that `case.md` still contains manual inputs. Such a file is valid as a design artifact, but is **not directly executable by `api-mind`** until the user either fills the manual values or lets `api-mind` skip them with zero values/TODO comments during its pre-generation gate.

---

## Completion
Output: *"All tasks completed. Output: `<target_dir>/test/case.md`."*
