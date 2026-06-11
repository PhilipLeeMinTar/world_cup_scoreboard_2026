# Aeolus — Query Editor (ad-hoc SQL)

This module wraps Aeolus **Query Editor** for running ad-hoc SQL. **It is the
default SQL entry point for Aeolus** — use it whenever the user wants to run a
SQL statement and there is no single, known Aeolus dataset driving that SQL.

`qe_query` is the right choice for:

- Generic / ad-hoc SQL where the user just has a SQL string.
- Multi-table joins or cross-source queries.
- Temporary / exploratory investigation (no persistent dataset context).
- Anything the user calls "跑 SQL" / "临时查一下" / "Query Editor" / "QE".

Only fall back to the dataset-bound `query` action (see
[dataset.md](./dataset.md)) when the user has already resolved a specific
`dataset_id` and the SQL targets exactly that one dataset.

Authentication: Titan Passport via the user's ByteCloud JWT. Run `gdpa-cli login`
once.

## When to use vs the other groups

| Goal | Use |
|------|-----|
| **Default for "run this SQL"** — any ad-hoc / exploratory / multi-table SQL | `qe_query` |
| Run SQL in a specific QE folder/file (so it shows up in the user's QE workspace) | `qe_run` + `qe_status` |
| Inspect a finished/long-running task | `qe_status`, `qe_logs` |
| SQL that targets a **specific known** Aeolus `dataset_id` (single dataset, no joins) | `query` (see [dataset.md](./dataset.md)) |
| Look at a chart on a dashboard | `query_report` (see [dashboard.md](./dashboard.md)) |

## Common parameters

| Param | Notes |
|-------|-------|
| `region` | `cn` (default), `sg`, `va`, `ttp`. SG uses `aeolus-sg.tiktok-row.net`, VA uses `aeolus-va.tiktok-row.net`, CN uses `data.bytedance.net`, USTTP uses `aeolus-tx.tiktok-usts.net`|
| `queue` | optional, defaults to a built-in queue |
| `idc` | optional, defaults per region |
| `http_timeout_ms` | optional underlying HTTP timeout override; use larger values such as `120000` for slow networks or long-running queries |

## Actions

### `qe_query` — one-shot ad-hoc SQL

| Param | Required |
|-------|---------|
| `sql` | yes |
| `region`, `queue`, `idc` | optional |

```bash
gdpa-cli run aeolus --input '{
  "action": "qe_query",
  "sql": "SELECT 1"
}'
```

Internally: finds or creates a temp folder `_gdpa_agents_temp`, creates a
file, writes the SQL, runs it, and polls until the task completes (with a
timeout). Returns either the result rows or — if it timed out — the `task_id`
plus instructions to call `qe_status` later.

### `qe_run` — submit SQL with explicit folder/file

| Param | Required |
|-------|---------|
| `sql`, `folder_id`, `file_id` | yes |
| `queue`, `idc` | optional |

Returns a `task_id`. Useful when the user wants the SQL to live in a specific
QE workspace location instead of the temp folder.

### `qe_status` — check a task

| Param | Required |
|-------|---------|
| `task_id`, `file_id`, `folder_id` | yes |
| `display_size` | optional, max rows to return |

Returns task status, results (when ready), and any error messages.

### `qe_logs`

| Param | Required |
|-------|---------|
| `task_id` | yes |

### Workspace management

| Action | Required params |
|--------|----------------|
| `qe_whoami` | (none) — verifies authentication |
| `qe_folder_list` | optional `parent_id` |
| `qe_folder_create` | `name`, optional `parent_id` |
| `qe_file_create` | `name`, `folder_id` |
| `qe_file_search` | `keyword`, optional `page`, `page_size` |

## Driving-model tips

1. **Default to `qe_query` for generic SQL.** The dataset-bound `query`
   action is narrower than it sounds — if there is no single known
   `dataset_id`, or the SQL joins tables, route here, not to `query`.
2. Prefer `qe_query` for one-off SQL — it hides folder/file orchestration.
3. Use `qe_run` + `qe_status` only when the user specifically wants the SQL
   archived under a folder they own (or wants to re-run an existing file).
4. Long-running SQL: if `qe_query` times out, surface the returned `task_id`
   and tell the user you'll poll with `qe_status` rather than re-running.
5. If `qe_whoami` fails, the user needs to re-run `gdpa-cli login` — don't
   retry the actual query until then.
6. Region matters: SG / VA both use `tiktok-row.net` (`aeolus-sg.tiktok-row.net`
   / `aeolus-va.tiktok-row.net`), CN uses `data.bytedance.net` — pass
   `"region": "sg"` or `"region": "va"` explicitly when the SQL targets i18n
   data, otherwise it will hit the CN host and fail auth/routing.
