# EMS · Schema change actions (RDS table create / alter)

This is the full RDS-table CREATE / ALTER lifecycle through EMS — five tightly-coupled actions:

| action | role |
|---|---|
| `validate_ddl_change` | (read-only) validate DDL + infer the resulting `entity_mapping` |
| `create_schema_change` | (write) publish a workflow on top of validated DDL |
| `approve_workflow_owner_gate` | (write) clear the workflow's Owner gate |
| `advance_workflow_bpm_ticket` | (write) drive the BPM tickets opened by the resource-deployment step |
| `close_workflow` | (write) terminate the entire workflow (cascades to all bound BPM tickets) |

先读 `SKILL.md` 拿全局 region / output envelope 约定，再回到这里。

> ⚠️ **`BOE-I18N` is NOT a supported publish target.** Every action in this group refuses to drive a release into `BOE-I18N`. Strip `BOE-I18N` out of `tables[i].vregions` and any top-level `vregions` before invoking these actions. If the user explicitly asks to release on BOE-I18N, surface the limitation rather than silently dropping or substituting the region.

The full release lifecycle is broken into four small actions so each step can be confirmed before the next one runs:

1. `validate_ddl_change` (read-only) — validate the DDL SQL and infer the resulting `entity_mapping`.
2. `create_schema_change` (write) — publish a workflow on top of the validated DDL. Returns a `workflow_id` + `workflow_url`.
3. `approve_workflow_owner_gate` (write) — approve the workflow's Owner-approval gate when the current JWT user is one of the entity owners.
4. `advance_workflow_bpm_ticket` (write) — list and drive the BPM tickets that the workflow's resource-deployment step opens (one per region).

Both `validate_ddl_change` and `create_schema_change` operate on a **batch** of tables on the same RDS via a required `tables: []` array. CREATE and ALTER rows can be mixed in the same batch; the skill auto-detects each row's operation by probing EMS, runs `ValidateAndInferFromDdl` concurrently per row (limit 5), and (for `create_schema_change`) publishes the entire batch as **a single workflow** via one `CreateSchemaChangeV2` call.

`create_schema_change` **internally re-runs `validate_ddl_change`** with the same parameters before publishing — there is no caching layer, so the inferred `entity_mapping` always matches what the backend will receive.

## Batch input contract (`tables: []`)

Both `validate_ddl_change` and `create_schema_change` take a **required `tables: []` array** — one entry per table you want to change on the same RDS. A single-table change is just a `tables: [{...}]` of length 1. Mixing CREATE and ALTER rows in the same batch is allowed; the skill auto-detects each row's operation by probing EMS for the entity. Validation is fanned out concurrently (limit 5) and the publish goes out as a **single** workflow regardless of row count.

### Top-level fields (shared defaults applied to every row)

| Field | Type | Notes |
|-------|------|-------|
| `rds_uri` / `storage_uri` | string | Resolves the **shared** target storage. One of `rds_uri` / `storage_uri` / `rds_psm` is required so the skill can pin every row to one RDS. |
| `rds_psm` | string | Same as `rds_uri`, but resolves via PSM lookup. |
| `vregions` | []string or csv | Default vregion list. Each row may override with its own `vregions`. Can be passed as IDC/VDC names — the skill maps them to canonical VRegions. ⚠️ Must NOT contain `BOE-I18N` — schema-change publish on BOE-I18N is not supported. |
| `sync_alter_to_stress_table` | bool | Default execution flag for every row. ALTER scenarios only. Each row may override. |
| `confirm` | bool | `create_schema_change` only — preview vs. publish. |

### `tables[]` (per-row, length ≥ 1)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `entity_uri` | string | One of `entity_uri` / `table_name` | Fully qualified entity URI, e.g. `tiktok/mysql__new_one_rds__foo`. If both `entity_uri` and `table_name` are supplied for a row, they must agree. |
| `table_name` | string | One of `entity_uri` / `table_name` | Physical MySQL table name. The skill derives the entity URI as `<scope>/<type>__<short_name>__<table_name>` from the shared storage. |
| `ddl_sql` | string | One of `ddl_sql` / `regional_sql_list` | DDL SQL applied to every vregion of this row. |
| `regional_sql_list` | []object | One of `ddl_sql` / `regional_sql_list` | Per-vregion DDL for this row: `[{"vregion":"Singapore-Central","sql":"..."}]`. |
| `vregions` | []string or csv | No | Per-row override of the shared default. ⚠️ Same restriction: `BOE-I18N` is not a supported publish target — keep it out of this list. |
| `operation` | string | No | Legacy entity-level override: `create` / `alter`. Forces what EMS does to the entity record (`create` = register new entity, `alter` = update existing entity registration). The **table-level** operation (CREATE TABLE vs ALTER TABLE) is always derived from the DDL keyword and cannot be overridden — surfaced in the response as `table_operation`. |
| `sync_alter_to_stress_table` | bool | No | Per-row override of the shared default. |
| `is_sharding_table` | bool | No (default `false`) | **CREATE rows only.** `create_schema_change` only. |
| `sharding_key` | string | When `is_sharding_table=true` | `create_schema_change` only. |
| `sharding_key_type` | string | Optional when `is_sharding_table=true` | `varchar` / `int`. Auto-inferred from the matched column when omitted. |

Auto-detection rule per row:

1. **Table-level operation** (`table_operation` in the response) — derived from the DDL keyword:
   - `CREATE TABLE …` → `create_table`
   - `ALTER TABLE …` → `alter_table`
   - This is what BPM physically runs against the RDS at the deploy stage.
2. **Entity-level operation** (`entity_operation` in the response) — derived from probing EMS for the entity URI:
   - Entity not registered yet → `create` (EMS will register a new entity record).
   - Entity already registered → `update` (EMS will update the existing entity record). Pass `operation: "alter"` / `"create"` on the row to force this entity-level decision when the auto-probe is wrong.

The two are normally aligned, but **legitimately diverge** in two scenarios:

- *Cancelled-workflow leftover*: a previous workflow registered the entity in EMS but was cancelled before BPM deployed the table. The user's next attempt re-submits `CREATE TABLE` → `entity_operation=update`, `table_operation=create_table`. The skill emits a Note explaining this on the row.
- *Out-of-band table*: a DBA created the physical table directly without going through EMS. The user submits `ALTER TABLE` → `entity_operation=create` (EMS catalog still empty), `table_operation=alter_table`.

When this happens, **do not tell the user "EMS is calling this an alter"** — the user wrote `CREATE TABLE`, the physical table is being created. Lead with `table_operation` in any human-facing description and only mention `entity_operation` if the divergence note is relevant.

Cross-row consistency is enforced — every row must resolve to the same shared storage; if a row's `entity_uri` belongs to a different storage the call is refused with `INPUT-002` so the user can split the request.

> ⚠️ **Migration from the pre-batch contract.** The old single-table top-level keys (`entity_uri`, `table_name`, `ddl_sql`, `regional_sql_list`, `operation`, `is_sharding_table`, `sharding_key`, `sharding_key_type`) at the **top level** are **no longer accepted**. Wrap them into a `tables: [{...}]` entry instead. Sending the old shape — or mixing top-level legacy keys alongside `tables` — is refused before any backend call with an `INPUT-002` error pointing at the new contract.
>
> **Before**:
> ```json
> {"action":"validate_ddl_change","rds_uri":"...","table_name":"foo","ddl_sql":"CREATE ..."}
> ```
> **After**:
> ```json
> {"action":"validate_ddl_change","rds_uri":"...","tables":[{"table_name":"foo","ddl_sql":"CREATE ..."}]}
> ```

### Override precedence (highest wins)

For every per-row field that has a top-level shared counterpart (`vregions`, `sync_alter_to_stress_table`):

1. Per-row value on `tables[i]` (if explicitly set)
2. Top-level shared default (when the row leaves the field unset)
3. Backend-inferred fallback (e.g. for `vregions`: derived from the existing entity for ALTER, or from the storage's deployed vregions for CREATE)

This means a typical batch sets a single top-level `vregions` and only the rows that need a different region carry their own override.

## `validate_ddl_change`

Validate a batch of DDL SQL statements against EMS and return per-row diagnostics + the inferred `entity_mapping` for each table. **Read-only** — does not publish anything. Use it to sanity-check a batch before invoking `create_schema_change`.

Validation is fanned out concurrently across rows (limit 5). If any row's diagnostics report a failure or the resolver itself rejects the batch, the action returns a single aggregated payload with **every** row's verdict so the user can see all problems at once instead of fixing them one at a time.

### Response highlights

- `storage_uri`, `psm`, `shared_vregions` — the shared resolution echoed back.
- `tables: [{entity_uri, table_name, operation, table_operation, entity_operation, vregions, validation, regional_sql_list, inferred_entity_mapping, entity_schema, notes?, warnings?, heuristic_rules?, ...}]` — one entry per `tables[i]`.
  - `operation` is the **user-facing** operation label and tracks the DDL keyword (`create_table` / `alter_table`). This is what BPM will run against the live RDS — when in doubt, show this value.
  - `table_operation` mirrors `operation` (the same value, exposed under a more explicit name for callers that want to be unambiguous).
  - `entity_operation` (`create` / `update`) is what EMS does to the entity catalog. Only surface this to the user when it diverges from `table_operation` — see the divergence note in `notes` for the rationale.
  - `entity_schema` is the **user-facing** rendering of the inferred (post-change) mapping: `fields[]` paired with their backing `table_column` / `column_type` / `description`, plus `primary_key` / `indices`. Show this as a table; do **not** dump the raw `inferred_entity_mapping`. We deliberately do **not** emit a diff against the existing entity — see the note in `create_schema_change` below.
  - `warnings` is the flat list of **non-blocking advisories** for the row (skippable heuristic rules + cross-region consistency drift). Always show these to the user when present, but do **not** treat them as a publish blocker.
  - `heuristic_rules` is the raw rule list (`[{content, position, can_skip_type, vregion, ...}, ...]`) for programmatic consumers — the live EMS shape nests these under `regional_ddl_validation_data_list[*].sql_validation_data.heuristic_rules` and the parser hoists them, tagging each rule with the originating `vregion`. Formatted versions already live in `validation.errors` (when blocking) and `warnings` / `validation.warnings` (when skippable).
  - `validation: {ok, errors?, warnings?, heuristic_rules?, regional, consistency}` — `ok=false` means a blocker exists in `errors`; warnings never flip `ok`.
- `summary: {total, create_count, alter_count, all_valid, warnings_count?}` — at-a-glance counts. `create_count` / `alter_count` reflect the **table-level** operation (DDL keyword), so a `CREATE TABLE` row whose entity is already registered still counts as a CREATE — matching what the user submitted. `warnings_count` is the number of rows carrying a non-blocking advisory.

> ⚠️ **Heuristic-rule contract** — every `heuristic_rules[i]` entry is mapped to one of two buckets based on its `can_skip_type` enum:
>
> - `can_skip_type=1` (Skippable) → **Warning**. Surfaced in `warnings`. The user MAY proceed to `create_schema_change` without fixing it; the agent should still display the rule so the user can decide consciously.
> - `can_skip_type=2` (Forbidden) → **Error**. Surfaced in `validation.errors`. The user MUST modify the DDL to clear the rule. EMS itself enforces this: when any rule is Forbidden, EMS returns no `inferred_entity_mapping`, so `create_schema_change` cannot proceed until every Forbidden rule is resolved.
> - Older / alternate EMS versions emit a boolean `can_skip` instead. The parser still respects it: `can_skip=true` ↔ Skippable (warning), `can_skip=false` ↔ Forbidden (error). Unknown enum values default to Forbidden so a future EMS-side enum addition cannot silently bypass the publish flow.

> ⚠️ **Consistency drift is a warning, not a blocker.** EMS surfaces drift via `consistency_check_data.inconsistent_column_list[]` and `consistency_check_data.inconsistent_unique_index_list[]`. **An entry only appears when EMS' projected post-change state would actually diverge across the storage's vregions** — empty / absent lists mean the change will land identically across all of the storage's vregions. Each entry carries the per-vregion projection (existence + column type / unique index spec) so the skill can describe the drift precisely.
>
> The skill emits one warning per drift entry (existence drift like "present in [SG, EU] but missing in [US-East, US-EastRed]" and/or type drift like "type `text` in [SG, EU] vs `varchar(255)` in [US-East]"). The publish flow is **not** blocked by drift — the deploy step runs per region and the user may have intentionally diverged DDL between regions; we just want them to consciously acknowledge the divergence. If you want strict cross-region equality, fix the per-region DDL before confirming.
>
> **History note**: an EMS server-side bug used to omit some vregions from `vregion_column_info_list`, leading to misleading drift reports (e.g. only listing the regions where the column would exist, hiding the regions where it would be missing). That bug is fixed; the lists now carry every vregion of the storage when drift is reported.

## `create_schema_change` (write)

Publish a batch of CREATE / ALTER TABLE changes on the same RDS as **a single workflow**. Two-phase: preview by default, pass `confirm=true` to apply. The skill internally re-runs `validate_ddl_change` for every row before publishing, so a stale validation result can never reach the backend.

Sharding parameters live on each `tables[i]` (CREATE-only). All other client-side validation rules from the previous contract still apply, but now run **per row**:

- `is_sharding_table=true` is rejected for ALTER rows (sharding can only be set at table creation).
- `sharding_key` must match an existing column of that row's inferred mapping (case-insensitive). Typos are caught with the full available column list, e.g. `tables[1].sharding_key "missing_col" is not a column of the table (available: [id user_id user_key payload created_at])`.
- The matched column's type must belong to the `int` family (TINYINT / SMALLINT / MEDIUMINT / INT / INTEGER / BIGINT) or the `varchar` family (VARCHAR / CHAR). Other types (TEXT, BLOB, JSON, TIMESTAMP, ...) are rejected.
- If `sharding_key_type` is omitted, the skill auto-fills it from the column's type. If supplied, it must equal the column's resolved kind — mismatches fail before any backend call.
- Setting `sharding_key` / `sharding_key_type` without `is_sharding_table=true` is rejected as an obvious caller bug.
- `sharding_key_type` (when supplied) must be the literal string `"varchar"` or `"int"` — anything else fails immediately.

Error messages pinpoint the failing row (e.g. `tables[2].sharding_key ...`) so the user knows exactly which entry to fix.

### Preview output

`confirm` omitted / `false` returns a compact **user-facing** payload:

- `display_action` — `"Release RDS Table"` for a single-row batch, `"Release RDS Tables"` (plural) for ≥ 2 rows. Don't show `create_schema_change`.
- `psm` (e.g. `tiktok.mysql.new_one_rds`), `storage_uri`, `shared_vregions` — top-level identifiers shared by every row.
- `tables: [{entity_uri, table_name, operation, vregions, ddl_statements, entity_schema, regional_sql_list, is_sharding_table, sharding_key, sharding_key_type, sync_alter_to_stress_table, validation}]` — one entry per `tables[i]`. `ddl_statements` groups DDLs by unique SQL. `entity_schema` is the inferred (post-change) fields view: each entry pairs an entity field with its backing `table_column` / `column_type` / `description`, plus `primary_key` / `indices`. Render the batch as a list of per-table cards in the agent UI, with `entity_schema.fields[]` shown as a markdown table (Entity Field / Type / Table Column / Column Type / Description) and the primary key + indices summarised below it.
  - **No diff is rendered, by design.** EMS persists the inferred entity record at workflow-create time, but the live RDS DDL is only deployed at the BPM stage. If a previous workflow was cancelled, the entity is already in the post-change shape but the RDS table is **not**, and re-submitting the same DDL is a legitimate request whose entity diff would (correctly) be empty. Surfacing that as "no-op" would mislead the user into thinking the workflow is unnecessary, when in fact the deploy must still run — so the preview always shows the full target schema and the agent should describe both CREATE and ALTER operations using the same field table.
- `summary: {total, create_count, alter_count, all_valid}` — at-a-glance counts so the user can verify the batch composition before confirming.
- `confirm_required: true` + `next_step` telling the user how to confirm. The next-step text is plural-aware (`"…N 张表，X CREATE / Y ALTER"`).
- Internal CAS / hash fields (`previous_hash_version`, `format_version`, raw `inferred_entity_mapping`) live under `tables[i].request_body` for programmatic consumers but should never be shown to the end user.

### Confirm output

`confirm=true` published — tightly focused on what the user needs next, and **embeds the Owner gate preview inline so the user only confirms once** (instead of `confirm publish` → `confirm gate`):

- `display_action` (singular / plural — same rule as preview).
- `published: true`.
- `workflow_id` and `workflow_url` (e.g. `https://ent.tiktok-row.net/workflow/detail/<id>`) — **one workflow regardless of row count**. Feed this id straight into `approve_workflow_owner_gate` and `advance_workflow_bpm_ticket`.
- `tables: [{entity_uri, table_name, operation}]` + `summary` — slim manifest of what was bundled, so the user can verify the workflow covers exactly the batch they reviewed.
- `next_step_owner_gate` — the same payload `approve_workflow_owner_gate` returns in preview mode (sans the duplicated `workflow_id` / `workflow_url` / `display_action`), plus a `next_action: "approve_workflow_owner_gate"` field. Keys to surface to the user:
  - `current_user`, `reviewers` (collaborators who can approve)
  - `workflow_summary` (entity + modification verb + DDL statements)
  - `expected_results` (what happens on Approve)
  - `next_step` — short Chinese guidance phrased for the publish flow, e.g. "当前用户 X 在 Reviewer 列表中，确认后即可完成 Owner 审批". CLI commands and field names (`confirm=true`, `action=...`) are deliberately suppressed so the user sees a clean prompt; the agent already knows the next action via `next_action`.
- The parent `next_step` is intentionally short ("工作流已发布，请确认下方 Owner 审批信息后继续") — the embedded gate carries the actionable detail.
- If the freshly-created workflow is not yet queryable (rare transient race) or the publisher is not in the reviewer set, `next_step_owner_gate.unavailable: "<reason>"` carries the error and the parent + embed `next_step` fall back to a single sentence pointing at `<workflow_url>` so the user can drive the gate manually in the EMS UI. The publish itself is **never masked** by this embed step.

The verbose EMS envelope (`create_schema_change_code` / `create_schema_change_message`) is **not** surfaced in the user-facing fields anymore; if a programmatic consumer needs it, read the raw `result.data.data` envelope instead.

On a workflow conflict (another open workflow on the same storage is blocking the change), the skill surfaces the same `conflict` block as `update_storage_owners` so the user can jump to that workflow and resolve it.

## `approve_workflow_owner_gate` (write)

Approve the Owner-approval gate of a schema-change workflow as the current JWT user. Two-phase: preview by default, pass `confirm=true` to submit the approval.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `workflow_id` | string | Yes | e.g. `119090688003` |
| `job_id` | int64 | No | Target a specific active job. Required when more than one job is currently active; otherwise the skill picks the single active job automatically. |
| `confirm` | bool | No | Default `false` (preview). Pass `true` to submit. |

### Pre-conditions enforced client-side

- The workflow must be an entity-scoped schema change (`resource_type=Entity`); other resource types do not have an Owner-approval gate.
- The current JWT user must already be in the entity's `owners` list. Otherwise the call is refused with `AUTH-005 AuthPermissionDenied` (the EMS backend trusts the caller for this action — the gate lives in the skill).
- Approving requires a CN-region JWT in the request body. The skill obtains it via the same login material BPM/BITS use; if no CN JWT is available the call is refused with `AUTH-002 AuthJWTInvalid` ("run `gdpa-cli login` and pick a CN region").

### Preview output (`confirm` omitted / `false`)

- `display_action: "Release RDS Table"` — paraphrased intent.
- `entity_uri`, `current_user`.
- `reviewers: [...]` — sourced from `schema_change.resources[*].reviewers` when present; falls back to the entity's `owners` list (and finally the workflow `author` for fresh CREATEs that don't yet have an entity record).
- `workflow_id`, `workflow_url`.
- `workflow_summary` — compact description of the change: `entity_uri`, `modification` (human label like "Create" / "Alter"), and either `ddl_statement` (when all regions share the same SQL) or `regional_ddls: [{vregion, sql}]` (when they diverge).
- `expected_results: [...]` — bullet list of what will happen on confirm (Owner-approval gate gets cleared, workflow advances to the BPM step, etc.). **Replaces the old `side_effects` field.**
- `confirm_required: true`, `next_step` (re-run with `confirm=true`).

### Confirm output (`confirm=true`)

- `display_action`, `published: true`, `workflow_id`, `workflow_url`, `next_step`.
- The low-level `siacflow_action_*` fields are intentionally **not** in the user-facing payload — they remain in the raw EMS envelope for debugging only.

Internal fields the preview deliberately does **not** surface (and the agent should never echo): `modification_type`, `target_job_id`, `target_job_service`, `target_job_status`, `top_status`, `active_jobs`, `workflow_author`, `siacflow_action_*`. These leak workflow-internal job naming that the human approver does not need.

## `advance_workflow_bpm_ticket` (write)

List BPM tickets bound to a schema-change workflow's resource-deployment step, or advance one. Two modes:

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `workflow_id` | string | Yes | e.g. `119090688003` |
| `ticket_id` | string | No | Provided ⇒ operate mode (advance this ticket); omitted ⇒ list mode. |
| `op_key` | string | When `ticket_id` is set | One of the `op_keys[].op_key` values returned in list mode. |
| `status` | string | When `ticket_id` is set | Target status from the matching `op_keys` entry. |
| `current_status` | string | No | Override the current status sent to BPM (defaults to the one in `op_keys`). |
| `bpm_vregion` | string | No | Override the BPM control-plane vregion (default: `China-North`). |
| `bpm_target_addr` | string | No | Override the BPM base URL. |
| `confirm` | bool | No | Default `false` (preview). Pass `true` to submit the BPM transition. |

### Behaviour

- **List mode** (no `ticket_id`): walks the BITS sub-pipelines bound to the workflow, returns one entry per BPM ticket with its status, link, parent/sub job, and (for non-finished tickets) the BPM op_keys + reviewers. Read-only.
  - **User-facing fields** the agent SHOULD render: `id`, `url` (always show this so the user can jump to BPM), `vregion`, `status`, `creator`, `approvers` (BPM `current_assignees` parsed into a list of usernames), and `display_actions: [{name, self_allowed}]`. `display_actions[].name` is the human label, with two label overrides applied so the agent UI matches what the user expects: `op_key=reject` renders as **"拒绝"** (BPM's default "误报" is internal jargon) and `op_key=cancel` renders as **"取消"** (templates that genuinely cancel the ticket). `op_key=stop` deliberately keeps BPM's native op_name "暂不处理" — submitting it does NOT terminate the workflow; the ticket can re-enter the queue at the next reviewer stage. All other op_keys keep BPM's `op_name` verbatim ("确认" for `assign`, etc.). `self_allowed` is `true` when the current JWT user can run the action themselves (i.e. they are not the ticket creator OR the op is in the SoD allowlist).
  - **Internal fields** the agent should NOT echo to the user: `op_keys` (low-level op_key strings + statuses, kept for programmatic callers that drive operate mode), `op_keys_error`, `approvers_error`, `bpm_base_url`. These are present in the response so that the next `advance_workflow_bpm_ticket` call can reference them, but exposing them in the chat output is noise.
  - For tickets where the current JWT user is the creator, the entry is also annotated with `creator_is_self: true`, `self_actionable_ops: ["reject","stop", ...]`, and `requires_other_approver: true` (set only when zero op_keys are self-actionable). The agent should phrase this as "you created this ticket — you can self-run Reject/Cancel; for Approve, ask one of `<approvers>`".
- **Operate mode** (`ticket_id` set): validates the supplied `(op_key, status)` against the ticket's `op_keys`, then — once `confirm=true` — calls BPM `UpdateStatus` to drive the ticket. Already-finished tickets short-circuit with `no_change=true`.

### Segregation-of-duties (RDS BPM)

The ticket creator **cannot self-Approve** their own ticket (e.g. `op_key=assign` / `approve`), but **CAN self-run Reject and the BPM `stop`/`cancel` ops** (`op_key=reject` "误报", `op_key=stop` "暂不处理", `op_key=cancel` for templates that expose it). The action enforces this client-side: any non-allowlisted op_key issued by the creator is refused before reaching BPM with `requires_other_approver: true` plus an `AUTH-005` error pointing at the BPM URL. The allowlist is conservative — `reject`, `stop`, `cancel` only — and lives next to `selfAllowedOpKeysOnOwnTicket` in `ddl_approve.go`. To Approve such a ticket, ask another collaborator (e.g. another entity owner or storage admin) to open the BPM URL.

> ⚠️ **`op_key=stop` ≠ cancel.** RDS BPM's `stop` op only postpones the individual ticket; the workflow keeps running and the ticket usually re-enters the queue at the next reviewer stage. To actually terminate a workflow (and cascade cancellation to all its BPM tickets), use the [`close_workflow`](#close_workflow-write) action below.

Beyond the creator check the action only enforces shape — the BPM backend is still the source of truth for "can this peer act on this ticket". A 403/permission error from BPM (e.g. peer is not in the approver pool) is surfaced verbatim.

## `close_workflow` (write) <a id="close_workflow-write"></a>

Terminate a schema-change workflow outright. Calls `SiacflowAction(ActionName="Close")` — the same path the "Close Workflow" button on `https://ent.tiktok-row.net/workflow/detail/<id>` uses. Two-phase: preview by default, pass `confirm=true` to apply.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `workflow_id` | string | Yes | e.g. `229489180419` |
| `comment` | string | No | Free-form reason. Forwarded to EMS verbatim and stored on the workflow record. |
| `job_id` | int64 | No | Pin the SiacflowAction call to a specific active job. Optional — Close terminates the entire workflow regardless, so the skill auto-picks the first active job when omitted. |
| `confirm` | bool | No | Default `false` (preview). Pass `true` to apply. |

### Pre-conditions enforced client-side

- The workflow must be entity-scoped (`resource_type=Entity`); other resource types do not have a Close path.
- The current JWT user must be either:
  1. the workflow author (`schema_change_request.author`), OR
  2. an owner of the target entity (`entity.owners`).
  Otherwise the call is refused with `AUTH-005 AuthPermissionDenied` and the response includes `authorized_closers` so the user knows whom to ask.
- A CN-region JWT is required in the SiacflowAction body (same constraint as `approve_workflow_owner_gate`). If unavailable the call is refused with `AUTH-002 AuthJWTInvalid` and the user is told to `gdpa-cli login` against a CN region.

### Preview output (`confirm` omitted / `false`)

- `display_action: "Close RDS Workflow"`.
- `workflow_id`, `workflow_url`, `entity_uri`, `current_user`.
- `authorized_closers: [...]` — flat list of usernames (workflow author + entity owners).
- `workflow_summary` — same compact change description used by the Owner-gate preview.
- `expected_results: [...]` — bullets explaining what Close does (terminate workflow, cascade-cancel BPM tickets, no automatic rollback of DDL already executed).
- `confirm_required: true`, `next_step` (re-run with `confirm=true`).

### Confirm output (`confirm=true`)

- `display_action: "Close RDS Workflow"`, `published: true`, `workflow_id`, `workflow_url`, `next_step`.
- `comment` is echoed back when supplied. Low-level `siacflow_action_*` fields are surfaced only when EMS returns a non-zero ack code (defensive — usually `code=0`).

Use this action — not `advance_workflow_bpm_ticket(op_key=stop)` — whenever the user wants to "cancel" or "abort" a workflow. The BPM `stop` op only snoozes one ticket; Close is the only path that truly ends the workflow at its source.

## When talking to the user (agent guidance)

When an agent surfaces these actions to the user it should paraphrase in user-visible terms and avoid leaking internal API names:

- **Validate** → "Here's how the change looks across regions, and the resulting table schema. Approve to publish?" Drive the table-by-table view from `tables[i].entity_schema` — never dump the raw `inferred_entity_mapping`. For multi-row batches, render one card per `tables[i]` (Entity URI / Table Name / DDL / fields). Render `entity_schema.fields[]` as a markdown table (Entity Field / Type / Table Column / Column Type / Description) regardless of whether the row is CREATE or ALTER — show the full post-change schema, do not synthesize a diff. Lead the overall response with the `summary` counts (`N tables: X CREATE / Y ALTER`, plus `warnings_count` when set). Use `tables[i].operation` (= the table-level operation, derived from the DDL keyword) as the per-row label — **never** describe a `CREATE TABLE` row as "ALTER" just because the EMS catalog already has the entity. The user wrote `CREATE TABLE`; the table is being CREATEd. See the divergence guidance below.
  - **Errors (blocking)** — when `validation.ok=false` for any row, lead with the `validation.errors` list and **refuse to suggest `create_schema_change`** until the user fixes the DDL. Forbidden heuristic rules (`can_skip_type=2`) land in this bucket and MUST be resolved before publishing — EMS itself withholds the inferred mapping for them, so the publish path cannot proceed. Phrase as "❌ 这条 DDL 还没法发布，请先修正以下问题"; do not propose `confirm=true`.
  - **Warnings (advisory)** — when `tables[i].warnings` is non-empty, render a "⚠️ Advisories" section underneath the schema preview that lists each warning verbatim. These come from skippable heuristic rules (`can_skip_type=1`) and cross-region consistency drift. The user MAY proceed; the agent should let them decide rather than auto-suggesting either way.
  - **Entity vs. Table operation divergence** — when `tables[i].entity_operation` differs from `tables[i].table_operation`, **do not** describe the row as "identified as ALTER, not CREATE" or similar entity-leaking phrasing. The user thinks in terms of the physical table, and a `CREATE TABLE` re-submitted after a cancelled workflow is a perfectly legitimate CREATE. Instead, surface the row's `notes[]` (which already carries the explanation: "entity is already registered in EMS but the physical RDS table will be CREATEd") in a small "ℹ️ Note" line under the table card. Keep the headline operation as `table_operation`. Mention `entity_operation` only inside that note, framed as informational ("EMS already has this entity registered from a prior workflow, so this run will only update the entity record while the physical CREATE TABLE deploys").
- **Create / preview** → Use the preview block as-is: lead with `display_action` (`"Release RDS Table"` for one row, `"Release RDS Tables"` for many), the shared `psm` / `storage_uri`, the `summary`, then one card per `tables[i]`. Each card MUST include the inferred-fields table from `tables[i].entity_schema` (Entity Field / Type / Table Column / Column Type / Description, plus the primary key + indices summary), the formatted `ddl_statements`, and the per-row `operation` / `vregions`. Use the same fields table for both CREATE and ALTER rows — do **not** invent or surface a diff against the existing entity (the schema is rendered as the post-change target, and an empty diff would falsely imply "no-op" when in fact a previously-cancelled workflow may have left the entity ahead of the live SQL). Render the per-row label from `table_operation` (CREATE TABLE / ALTER TABLE) — not `entity_operation`; if the two diverge, attach the row's `notes[]` as a small "ℹ️ Note" line so the user understands why EMS reuses an existing entity record. Don't reveal `previous_hash_version`, `format_version`, or the raw `inferred_entity_mapping` / `request_body`. The agent should phrase the confirm prompt around the batch ("Confirm to release these N tables in one workflow?") rather than per row.
  - When any row carries `warnings`, surface them in the same "⚠️ Advisories" section as in validate, and explicitly call them out in the confirm prompt (e.g. "⚠️ N warnings present; confirm to release anyway?"). They never block the publish, but the user should consciously acknowledge them.
- **Create / confirmed** → "Published. Workflow `<workflow_url>` is now running." Show **only** the `workflow_url` plus the slim `tables` manifest (so the user can verify the batch composition); the rest of the structured envelope is for debugging. Don't say "schema change request submitted via CreateSchemaChangeV2".
- **Owner approval / preview** → "You're a reviewer of this entity — approve workflow `<workflow_url>`?" Show `display_action`, the `reviewers` list, the `workflow_summary` (entity + modification + DDL), the `workflow_url`, and the `expected_results` bullets. Do **not** show `Modification Type`, `Target Job`, `siacflow_*`, or `token_bytecycle` — those are workflow-internal mechanics the user shouldn't have to read.
- **BPM ticket / list** → "These are the BPM tickets the workflow opened. Pick one and tell me which op to run." When a ticket has `creator_is_self: true`, surface the available self-ops: "You created this ticket — you can self-run `<self_actionable_ops>` (Reject/Cancel). For Approve, ask another collaborator to operate `<bpm_url>`." If `requires_other_approver: true` (no self-actionable op_keys), say "You created this ticket and only approve-style ops are available; please ask another collaborator to run the op at `<bpm_url>`."
- **BPM ticket / confirmed** → "Submitted `<op_name>` on ticket `<id>`. Re-fetch to see the new status."
- **BPM ticket / refused (creator self-Approve)** → "You're the creator of this ticket; RDS BPM doesn't let you Approve your own ticket. You CAN Reject (拒绝) or postpone the ticket (暂不处理) yourself; for Approve, ask a peer to open `<bpm_url>`. If you want to actually cancel the whole workflow, use `close_workflow`." Don't claim the action was submitted.
- **Close workflow / preview** → "This will terminate workflow `<workflow_url>` and cancel all its BPM tickets. Authorized closers: `<authorized_closers>`. Confirm to proceed?" Show `display_action`, the `workflow_summary`, `expected_results`, and `workflow_url`. Don't surface `siacflow_action_*` or the `job_id` we picked — those are mechanics.
- **Close workflow / confirmed** → "Workflow closed. Bound BPM tickets will be cancelled by the deploy pipeline. Open `<workflow_url>` to see the final state." Don't repeat the comment.
- **Workflow conflict** → "Another open workflow on this entity is blocking the change. Resolve it at `<workflow_url>` and retry."

The detailed payload fields (`previous_hash_version`, `siacflow_action_*`, `bpm_data`, etc.) are kept in the structured response for programmatic consumers and debugging — they should not be surfaced verbatim to end users.

## Examples

```bash
# 1. Validate a CREATE TABLE DDL — read-only. Single-row batch.
gdpa-cli run ems --input '{
  "action": "validate_ddl_change",
  "rds_uri": "tiktok/mysql/new_one_rds",
  "tables": [
    {
      "table_name": "foo",
      "ddl_sql": "CREATE TABLE foo (id BIGINT(20) UNSIGNED NOT NULL COMMENT '\''ID'\'', PRIMARY KEY (id)) ENGINE=INNODB CHARSET=utf8mb4"
    }
  ]
}'

# 2. Preview a CREATE TABLE schema change (no publish yet). Single-row batch.
gdpa-cli run ems --input '{
  "action": "create_schema_change",
  "rds_uri": "tiktok/mysql/new_one_rds",
  "tables": [
    {
      "table_name": "foo",
      "ddl_sql": "CREATE TABLE foo (id BIGINT(20) UNSIGNED NOT NULL, PRIMARY KEY (id)) ENGINE=INNODB CHARSET=utf8mb4"
    }
  ]
}'

# 3. Same change, but actually publish it. workflow_id / workflow_url will be in the response.
gdpa-cli run ems --input '{
  "action": "create_schema_change",
  "rds_uri": "tiktok/mysql/new_one_rds",
  "tables": [
    {
      "table_name": "foo",
      "ddl_sql": "CREATE TABLE foo (id BIGINT(20) UNSIGNED NOT NULL, PRIMARY KEY (id)) ENGINE=INNODB CHARSET=utf8mb4"
    }
  ],
  "confirm": true
}'

# 4. Sharded CREATE TABLE — sharding params live on the row, not the top level.
gdpa-cli run ems --input '{
  "action": "create_schema_change",
  "rds_uri": "tiktok/mysql/new_one_rds",
  "tables": [
    {
      "table_name": "bar",
      "ddl_sql": "CREATE TABLE bar (uid BIGINT NOT NULL, name VARCHAR(64), PRIMARY KEY (uid)) ENGINE=INNODB CHARSET=utf8mb4",
      "is_sharding_table": true,
      "sharding_key": "uid"
    }
  ],
  "confirm": true
}'

# 5. ALTER TABLE — entity_uri picks the row's target.
gdpa-cli run ems --input '{
  "action": "create_schema_change",
  "rds_uri": "tiktok/mysql/new_one_rds",
  "tables": [
    {
      "entity_uri": "tiktok/mysql__new_one_rds__foo",
      "ddl_sql": "ALTER TABLE foo ADD COLUMN created_at BIGINT NOT NULL DEFAULT 0"
    }
  ],
  "confirm": true
}'

# 6. Batch — three tables on the same RDS, mixing CREATE and ALTER. One workflow gets published.
gdpa-cli run ems --input '{
  "action": "create_schema_change",
  "rds_uri": "tiktok/mysql/new_one_rds",
  "vregions": ["Singapore-Central", "EU-TTP2"],
  "tables": [
    {
      "table_name": "new_a",
      "ddl_sql": "CREATE TABLE new_a (id BIGINT NOT NULL, PRIMARY KEY (id)) ENGINE=INNODB CHARSET=utf8mb4"
    },
    {
      "table_name": "new_b",
      "ddl_sql": "CREATE TABLE new_b (id BIGINT NOT NULL, attr TEXT, PRIMARY KEY (id)) ENGINE=INNODB CHARSET=utf8mb4",
      "vregions": ["Singapore-Central"]
    },
    {
      "entity_uri": "tiktok/mysql__new_one_rds__existing_t",
      "ddl_sql": "ALTER TABLE existing_t ADD COLUMN created_at BIGINT NOT NULL DEFAULT 0"
    }
  ],
  "confirm": true
}'

# 7. Preview the Owner-approval gate (shows entity owners + active jobs).
gdpa-cli run ems --input '{
  "action": "approve_workflow_owner_gate",
  "workflow_id": "119090688003"
}'

# 8. Submit the Owner approval as the current user.
gdpa-cli run ems --input '{
  "action": "approve_workflow_owner_gate",
  "workflow_id": "119090688003",
  "confirm": true
}'

# 9. List the BPM tickets bound to a workflow's resource-deployment step.
gdpa-cli run ems --input '{
  "action": "advance_workflow_bpm_ticket",
  "workflow_id": "119090688003"
}'

# 10. Advance a specific BPM ticket — pick the (op_key, status) pair from the list above.
#    NOTE: RDS BPM tickets are subject to segregation-of-duties — the creator
#    cannot self-action their own ticket. Have another collaborator run this.
gdpa-cli run ems --input '{
  "action": "advance_workflow_bpm_ticket",
  "workflow_id": "119090688003",
  "ticket_id": "40927815",
  "op_key": "assign",
  "status": "assign",
  "confirm": true
}'

# 11. Preview closing the entire workflow (cancels all bound BPM tickets).
gdpa-cli run ems --input '{
  "action": "close_workflow",
  "workflow_id": "119090688003"
}'

# 12. Close the workflow with a reason. Cascades to BPM tickets.
gdpa-cli run ems --input '{
  "action": "close_workflow",
  "workflow_id": "119090688003",
  "comment": "DDL written by accident — terminating",
  "confirm": true
}'
```
