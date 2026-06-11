# Aeolus — Dashboard Chart Queries

This module is for **Aeolus dashboards**: list a dashboard's charts and
filters, fetch the data of a single chart, or on-demand look up the candidate
values for a multi-select filter. It does NOT run ad-hoc SQL — see
[query_editor.md](./query_editor.md) for that.

Authentication: Titan Passport via the user's ByteCloud JWT. Run `gdpa-cli login`
once; no extra credential setup needed.

## Actions

All dashboard actions accept optional `http_timeout_ms` to override the
underlying HTTP timeout. Use it for slow networks or large chart queries, for
example `120000` for 120 seconds.

### `get_dashboard` — list charts and filters

Use this **first** when the user gives you a dashboard URL and wants to know
what's available before drilling in. This call is cheap — it returns schemas
only and does NOT fan out to fetch candidate values.

| Param | Required | Notes |
|-------|---------|-------|
| `dashboard_url` | one of url/(id+sheet) | Will auto-extract `dashboard_id`, `app_id`, `sheet_id`, `region` |
| `dashboard_id` | one of url/(id+sheet) | Numeric dashboard ID |
| `sheet_id` | required if no url | Numeric sheet ID |
| `app_id` | optional | Will fall back to dashboard metadata |
| `region` | optional | `cn` (default), `sg`, `va`, `ttp` — auto-set from URL host |

```bash
gdpa-cli run aeolus --input '{
  "action": "get_dashboard",
  "dashboard_url": "https://data.bytedance.net/aeolus/pages/dashboard/1421544?appId=1008589&sheetId=1960002"
}'
```

Output highlights:

- `reports[]`: `{#, reportId, name, displayType}` — show this list to the user.
- `filters[]`: each filter's `name`, `filter_type`, `default_value`, `scope`,
  `report_count`, and `has_candidates` (true for `multi_select` with a known
  field expression). Candidate values are NOT included — fetch them lazily with
  `get_filter_candidates`.
- `task_id`: opaque, reused internally — no need to surface it.
- `hint`: short next-step instruction.

### `get_filter_candidates` — fetch candidate values on demand

Call only for a specific filter the user cares about, not preemptively for all
filters. Results are scoped to the dashboard's current filter context (defaults
plus anything you pass via `filters`), so you get options that are actually
selectable, not the global set.

| Param | Required | Notes |
|-------|---------|-------|
| `dashboard_url` or `dashboard_id`+`sheet_id` | yes | Same as `get_dashboard` |
| `filter_name` | yes | Must match a filter from `get_dashboard`'s `filters[].name` |
| `filters` | optional | Current context for other filters (e.g. `{"p_date": "2026-04-12"}`). The target filter's own value is intentionally ignored so it doesn't constrain its own candidates. |

```bash
gdpa-cli run aeolus --input '{
  "action": "get_filter_candidates",
  "dashboard_url": "https://data.bytedance.net/aeolus/pages/dashboard/1421544?appId=1008589&sheetId=1960002",
  "filter_name": "project",
  "filters": {"p_date": "2026-04-12"}
}'
```

Output: `{filter_name, filter_type, candidates[], context_used, ...}`.
`context_used=true` means the returned set was scoped by the dashboard's
filter context; `false` means the API fell back to the global dimension set
(e.g. because no owning report could be resolved).

### `query_report` — fetch one chart's data

Call this after `get_dashboard` (or when the user already knows which chart).

| Param | Required | Notes |
|-------|---------|-------|
| `dashboard_url` or `dashboard_id`+`sheet_id` | yes | Same as `get_dashboard` |
| `report_id` **or** `report_name` | yes | `report_name` accepts fuzzy substring; an exact match wins |
| `filters` | optional | `map<filter_name, value>` to override the chart's where clauses. See [Filter override shapes](#filter-override-shapes) below. Names are **case-sensitive** and must match the chart's own filter names (use `get_dashboard` / `get_filter_candidates` to discover them). |
| `params` | optional | `map<param_name, value>` to override **dashboard-level parameters** (the top parameter panel of the dashboard, distinct from per-chart where filters). |
| `dynamic_fields` | optional | `map<dynamicPillId, fieldId or [fieldId...]>` to pick which concrete dimension a dynamic-pill placeholder resolves to (the UI switcher like "按 OS 拆 / 按机房拆"). Pill ids are exposed as `dynamic...` placeholders in the chart schema. |
| `date` | optional | Backward-compat shortcut. **Scoped to the target report only** — overrides the first date filter defined on that chart; no effect on sibling charts. Prefer explicit `filters` when the dashboard has multiple date filters. |
| `dry_run` | optional (bool) | When `true`, build the query body and return it as `request_preview` **without sending any network request**. Use to verify your overrides (whereList / paramList / groupByIdList) before paying for a real query. |

#### Filter override shapes

The `filters` map accepts three shapes per key — pick the one that matches
what the chart's filter expects:

| Shape | Example | Effect |
|-------|---------|--------|
| plain string | `{"p_date": "2026-04-12"}` | single value; for `date` filters acts as `between [day, day]` |
| range string | `{"p_date": "2026-04-01,2026-04-12"}` | for `date` filters → `between` |
| array | `{"os": ["android", "ios"]}` | for `multi_select` filters → `in` |
| structured | `{"date": {"op":"lastSync","val":[7]}}` | advanced — explicit `op` / `val[ / valOption]`. Supports `lastSync` (relative windows), `between`, `in`, `not in`, `!=`, etc. |

```bash
gdpa-cli run aeolus --input '{
  "action": "query_report",
  "dashboard_url": "https://aeolus-va.tiktok-row.net/pages/dashboard/404168?appId=1002298&sheetId=453043",
  "report_name": "首帧时长-PCT50 (ms)",
  "filters": {"date": {"op":"lastSync","val":[7]}}
}'
```

#### `dry_run` — preview the request body without querying

Highly recommended whenever you're building a complex override (new `params`,
multiple `filters`, `dynamic_fields`) and want to double-check before firing
the real query. Returns `request_preview` with the exact `whereList` /
`paramList` / `groupByIdList` / `dimMetList` the client would send, and
`unmatched_filters` / `warning` if any override key didn't match anything on
the chart.

```bash
gdpa-cli run aeolus --input '{
  "action": "query_report",
  "dashboard_url": "https://aeolus-va.tiktok-row.net/pages/dashboard/404168?appId=1002298&sheetId=453043",
  "report_name": "首帧时长-PCT50 (ms)",
  "filters": {"date": {"op":"lastSync","val":[7]}, "OS": ["android"]},
  "dry_run": true
}'
```

Typical dry-run output:

```json
{
  "queried_report": {"reportId": 3077167, "name": "首帧时长-PCT50 (ms)", ...},
  "effective_filters": [
    {"name": "date",     "op": "lastSync", "value": [7],     "source": "override"},
    {"name": "dim_name", "op": "in",       "value": ["os"], "source": "default"}
  ],
  "unmatched_filters": ["OS"],
  "warning": "filters [OS] not found on chart \"首帧时长-PCT50 (ms)\"; valid filter names: [date dim_name]. Names are case-sensitive; call get_filter_candidates for candidate values.",
  "dry_run": true,
  "request_preview": {
    "api_path": "/aeolus/vqs/api/v2/vizQuery/query (primary) — falls back to /aeolus/glue/api/v1/dashboard/query on routing errors",
    "reportId": 3077167,
    "dataSourceId": 577,
    "query": {
      "whereList":     [...],
      "paramList":     [],
      "groupByIdList": ["1700037135281", "1700037246790"],
      "dimMetList":    [],
      "hasDynamicField": false,
      "limit": 10000,
      "sort":  {"type": "sort", "orderByList": []}
    },
    "body_json_size": 8724
  }
}
```

Use `dry_run` as a zero-cost sanity check: confirm `effective_filters[*].source`
are what you expect, confirm `unmatched_filters` is empty, then drop `dry_run`
to run for real.

#### Output (normal, non-dry-run mode)

- `queried_report`: `{reportId, name, dataSetId, displayType}`
- `effective_filters[]`: every filter actually applied, with `source` — either
  `override` (came from the caller's `filters`/`date` param) or `default` (the
  dashboard's configured default). Use this to confirm the effective date /
  dimensions before showing the user.
- `unmatched_filters[]` + `warning` (only when something was ignored): names
  in your `filters` map that did **not** match any filter on the chart. The
  query still ran, just without those overrides — typically a typo (`OS` vs
  `os`) or a filter that lives on a different chart.
- `query_route`: `vqs` or `glue` — which backend served the request (VQS is
  the primary path; glue is the fallback for a small set of legacy chart types).
- `query_data`:
  - `columns[]` and `rows[]`: human-readable table view (already alias-translated).
  - `costMs`, `sqlList`: timing / debug info.

## Driving-model tips

1. If the user provides only a URL and nothing else, **do not** jump straight
   to `query_report`. Either call `get_dashboard` first and present the
   chart/filter list, or use `AskUserQuestion` to ask whether they want
   overview, specific chart, or just the underlying dataset.
2. For `multi_select` filters, only call `get_filter_candidates` for the
   one(s) the user is actively choosing — not for every filter up-front. A
   large dashboard can have many filters and each call is a round trip.
3. When matching a chart by name, prefer surfacing the matched report's `name`
   and `reportId` back to the user before showing data.
4. To compare across dates, call `query_report` repeatedly with different
   `filters.p_date` values rather than asking the user to construct multiple
   URLs.
5. Prefer `filters` over `date`. The `date` shortcut rewrites only the first
   date filter of the **target chart**, and does nothing on sibling charts —
   if the user's intent is "change the whole dashboard's date", pass
   `filters` explicitly on each chart you query.
6. When building a non-trivial override (multiple `filters`, `params`, or
   `dynamic_fields`), run once with `dry_run: true` first. Inspect
   `effective_filters[*].source` and `unmatched_filters` — fix any typos —
   then re-run without `dry_run`. This avoids silent "why isn't my filter
   working?" loops.

## Errors you may see

### Caller-side (skill rejects the call)

- `query_report requires report_id or report_name` — caller forgot to pass the
  chart selector.
- `report_name "X" matched N reports` — the fuzzy match was ambiguous; ask the
  user to pick from the listed candidates.
- `filter_name "X" not found` / `filter ... does not support candidate lookup`
  — the filter either doesn't exist on this dashboard or isn't a `multi_select`
  with a resolvable field.
- `unmatched_filters` non-empty in `query_report` output — your `filters` /
  `params` / `dynamic_fields` map contained keys the chart doesn't have. The
  query still ran with the remaining (matched) overrides; fix the typos and
  re-run. Common cause: case mismatch (`OS` vs `os`), or the filter belongs
  to a sibling chart.

### Server-side (Aeolus / ClickHouse pushes back)

These come back as the chart's `code` field; the skill surfaces them
verbatim so the model can decide whether to retry, change inputs, or escalate.

- `aeolus/clickhouse/unknownIdentiferExplict` with `Missing columns: 'X' 'Y' …`
  — **dataset schema drift**: the dataset's metric / dimension definitions
  reference ClickHouse columns that no longer exist in the underlying table.
  This is **not fixable from the client** — opening the dashboard in the
  browser fails on the same chart with the same error. Action: tell the user
  which chart fails and which columns are missing, and suggest contacting the
  dataset / dashboard owner. Do NOT keep retrying with different overrides.
- `aeolus/clickhouse/readFailed` / `aeolus/clickhouse/sqlParseFailed` /
  `aeolus/clickhouse/illegalARgType` — the server-rendered SQL was rejected by
  ClickHouse (data missing for the requested partition, type mismatch, etc.).
  First sanity check: try a different `filters.p_date` (often the underlying
  table just doesn't have data for the requested day). If a partition with
  data still errors, treat it like `unknownIdentiferExplict` above —
  server-side dataset issue.
- `aeolus/user/forbidden` / `aeolus/user/unauthorized` — the user's Titan
  Passport session does not have permission for that `appId` / dashboard /
  dataset. The skill cannot bypass this. Tell the user to apply for access on
  the dashboard's `?appId=…` page (or `gdpa-cli login` again if the session
  expired).
- `aeolus/unknown` with `extra_msg` containing a measure / dimension id (e.g.
  `avgday_<dayId>_sum_<fieldId>`, `ratio_<id>_<id>`) — a derived measure shape
  the client doesn't recognize. The current skill already passes through
  unknown derived measures from the schema; if you still see this, the chart
  is using an even more exotic shape — surface the id and escalate to the
  dashboard owner.
- `147999` from Aeolus — a small number of charts (e.g. raw-data preview) are
  not stably queryable via this API; report the failure and suggest opening
  the dashboard directly.

### Partial dashboard failures

A dashboard often has a mix of working and broken charts. `get_dashboard`
always lists the full set, but `query_report` is per-chart. When asked to
"summarize this dashboard", the right shape is: query each chart, and for
each one report either the data or the chart-level `code`/`msg`. **Do not**
hide chart-level failures behind a top-level "everything failed"; surface
each one with its `reportId` and `name` so the user can decide what to do.
