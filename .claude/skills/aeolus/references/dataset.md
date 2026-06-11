# Aeolus — Dataset / SQL Queries

This module is for working with Aeolus **datasets** directly: list authorized
resources, find a dataset by app, inspect dimensions/metrics, and run SQL
against the dataset. It is **not** for dashboards (see [dashboard.md](./dashboard.md))
and **not** for ad-hoc Query Editor SQL (see [query_editor.md](./query_editor.md)).

## Authentication

Dataset actions use **OAuth credentials per region**, not Titan Passport. If
credentials are missing the agent returns a `setup_required` block with the
correct developer URL. Set them up via:

```bash
gdpa-cli aeolus credential set --region <cn|sg|va>
```

Troubleshooting:

```bash
gdpa-cli aeolus credential path                        # show file location
gdpa-cli aeolus credential get --region cn             # check whether configured
gdpa-cli aeolus credential set --region cn \
  --client-id <id> --client-secret <secret>            # non-interactive
```

When the agent reports missing credentials, point the user at the region's
Aeolus developer page, run the `set` command (it prompts and hides the secret),
then retry.

## Discovery flow (when you only have a name or link)

1. `list_apps` → find the right `app_id` for the project/team.
2. `search_datasets` with that `app_id` → find the `dataset_id`.
3. `dataset_fields` on the `dataset_id` → see partition fields, dimensions, metrics.
4. `get_fabric_data_info` (optional) → only when the dataset is a *virtual table*
   composed of multiple Hive joins, and you need to know which underlying
   tables/partitions/joins back it.
5. `query` with a sample SQL → confirm data and date partitions.

If the URL contains `?sid=...` or `?rid=...`, you can sometimes use them as
`dataset_id` directly — but always run `dataset_fields` first.

## Actions

All dataset actions accept optional `http_timeout_ms` to override the
underlying HTTP read/write timeout. Use it for slow networks or large queries,
for example `120000` for 120 seconds.

### `list_authorized`

| Param | Required | Notes |
|-------|---------|-------|
| `region` | yes | `cn`/`sg`/`va` |
| `type` | optional | `dashboard` or `data_set` |
| `limit`, `offset` | optional | pagination |

### `list_apps`

| Param | Required | Notes |
|-------|---------|-------|
| `region` | yes | |
| `only_show_has_auth` | optional | default `"true"` |
| `is_need_statistics` | optional | default `"false"` |

### `search_datasets`

| Param | Required | Notes |
|-------|---------|-------|
| `region` | yes | |
| `app_id` | yes | from `list_apps` |

### `dataset_fields`

| Param | Required | Notes |
|-------|---------|-------|
| `region` | yes | |
| `dataset_id` | yes | |

Returns `dimensions[]` and `metrics[]`. Partition fields are inside `dimensions`
with `isPartitionField=1`; they MUST appear in the SQL `WHERE` clause.

### `get_fabric_data_info` — virtual-table physical composition

Use this to inspect how an Aeolus dataset (which can be a *virtual table*
joining several Hive sources) is physically composed. Complementary to
`dataset_fields`: that one returns the column catalog; this one returns the
underlying tables and join topology.

| Param | Required | Notes |
|-------|---------|-------|
| `region` | yes | `cn`/`sg`/`va` |
| `app_id` | yes | from `list_apps` or the dataset URL |
| `dataset_id` | yes | |

Returns:

- `base` — dataset metadata (name, owner, default partition filter, model
  type, parse engine, version, …).
- `nodes[]` — one entry per underlying physical table (cluster / db / table /
  alias / source type / partition predicates with operator + value, e.g.
  `date = ${date}` or `idc_region in ["EU","VA","TTP"]` / `field_count`).
- `joins[]` — directed edges between `nodes`, with `from`, `to`,
  `join_type`, `cardinality`, and the `join_fields` column pairs.
- `where_conf` — global WHERE clause (raw upstream object).
- `summary` — `node_count` / `join_count`.

Field-level catalogs are intentionally **not** returned here — call
`dataset_fields` for that. Pair the two when you need to write SQL against a
virtual table.

```bash
gdpa-cli run aeolus --input '{
  "action": "get_fabric_data_info",
  "region": "va",
  "app_id": 555771,
  "dataset_id": 2633293
}'
```

### `query` — dataset-bound SQL only

> `query` is **not** a generic SQL runner. It runs SQL **against exactly one
> known `dataset_id`** using Aeolus's dataset API. For generic/exploratory/
> multi-table SQL, use `qe_query` from the Query Editor group
> ([query_editor.md](./query_editor.md)).

Use `query` only when **all** of these are true:

- The user has given (or you have already resolved) a specific `dataset_id`.
- The SQL targets that single dataset.
- You need partition/field validation against that dataset (via `dataset_fields`).

If any of those are false — especially "the SQL joins multiple tables" or
"the user is just exploring" — stop and use `qe_query` instead. `query` will
reject cross-dataset SQL and will NOT route it to Query Editor automatically.

| Param | Required | Notes |
|-------|---------|-------|
| `region` | yes | |
| `dataset_id` | yes | single dataset only — no joins across datasets |
| `sql` | yes | use Aeolus quoting (see below); must reference only this dataset |
| `version` | optional | default `v2` |
| `limit` | optional | truncate rows in agent output only — does NOT rewrite SQL |

```bash
gdpa-cli run aeolus --input '{
  "action": "query",
  "region": "va",
  "dataset_id": 1576311,
  "sql": "SELECT `[p_date]`, `[scene]` FROM `[DatasetName]` WHERE `[p_date]` = '\''2026-03-01'\'' LIMIT 10"
}'
```

### Saved SQL sets — `save_sqlset` / `query_sqlset` / `list_sqlsets` / `get_sqlset` / `delete_sqlset`

Sqlsets are stored locally at `~/.gdpa/aeolus/sqlsets/<name>.sql`.

- `save_sqlset`: requires `sqlset_name` plus exactly one of `sql` or `file_path`
  (absolute path).
- `query_sqlset`: requires `region`, `dataset_id`, `sqlset_name`. Multi-statement
  files run in order; one result block per statement.
- `list_sqlsets` / `get_sqlset` / `delete_sqlset`: as their names suggest;
  `get_sqlset` returns full SQL plus parsed statement list.

## SQL syntax notes

- Table name: `` `[DatasetName]` ``
- Field name in `SELECT`: `[Field Name]` (brackets only — no backticks needed
  around the bracket form inside expressions).
- Partition field MUST appear in `WHERE` (e.g. `p_date = '2026-03-01'`).
- `dataset_fields` is the source of truth for available fields, including the
  exact field name token to put inside the brackets and which fields are
  partition fields (`isPartitionField=1`).

### Server-side rewriter quirks (workarounds)

Aeolus rewrites SQL before handing it to ClickHouse. Two cases bite often:

- **`WHERE [col] = …` may fail with `aeolus/clickhouse/readFailed`** even
  when `SELECT [col] …` works. Concretely, this has been seen on partition
  fields like `p_date`. Workaround: drop the brackets in the `WHERE` clause
  (`WHERE p_date = '2026-04-23'`). The bracket form is fine in `SELECT`.
- **`SUM([col])` may fail with `aeolus/clickhouse/illegalARgType` "sum 函数参数
  类型不正确，不应该为 Array(Nullable(Float64))"** on datasets where the rewriter
  wraps `[col]` into `array(col)`. Workaround: drop the brackets inside
  aggregations — `SUM(col)`, `COUNT(col)`, `AVG(col)` all work without
  brackets. Brackets are only required when the field name contains spaces or
  special characters that aren't valid identifiers.

If you hit either error, retry with the bracketless form before concluding
the dataset is broken.

## Driving-model tips

1. If the user gives only a name, never guess a `dataset_id`. Walk the
   discovery flow and confirm the match with the user.
2. **Do not default "I have a SQL" to `query`.** `query` is dataset-bound. If
   the user did not give you a `dataset_id`, or the SQL joins multiple tables,
   or they are just exploring — route to `qe_query`
   ([query_editor.md](./query_editor.md)) instead.
3. If `query` returns 0 rows, first check the partition field with a recent
   date before reporting "no data".
4. On error, distinguish: missing credentials (call out `setup_required`),
   missing/wrong partition, unauthorized dataset, and SQL syntax.
