# EMS · Entity actions

`list_entities`、`get_entity`、`get_entity_online_ddl`。先读 `SKILL.md` 拿全局 region / output envelope 约定，再回到这里。

## `list_entities`

List entities. Maps to `GET /api/platform/v1/entity` (the same path the EMS UI uses; the V2 path is intentionally avoided — it returns no `list` array under `mode=3` and uses a different array field name for `mode=1/2`). This one action covers both "browse my entities" and "list entities (tables) under a storage" — mode is inferred from whether `storage_uri` is set.

> **Smart mode inference** (applies when `mode` is NOT explicitly provided):
> - `storage_uri` set → `mode=1` (ALL entities under that storage; e.g. all tables under a MySQL storage)
> - `storage_uri` unset → `mode=2` (only entities owned by the JWT user — "my entities")
>
> Explicit `mode` always wins. To list entities **owned by a specific user**, use `mode=2` — the backend derives the user from JWT automatically. **Do NOT pass a free-form `owner` param.** In owner mode the skill echoes the resolved `query_user` in the response.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `mode` | int | No (inferred) | `1`=all, `2`=owned by JWT user, `3`=subscribed. If omitted, inferred from `storage_uri`. |
| `storage_uri` | string | No | Narrow to a specific storage. When set and `mode` is unset, triggers `mode=1` default. |
| `table_name` | string | No | Filter by underlying table name (MySQL) |
| `entity_name` | string | No | Fuzzy match on entity name |
| `serial` | string | No | Filter by entity serial id |
| `exact` | bool | No | V1-only flag controlling whether `entity_name` / filters match exactly. Default `false` (matches the EMS UI). |
| `page_num` | int | No | Default `1` |
| `page_size` | int | No | Default `20` |

Response shape (under `data.data`):
- `list`: array of `{entity, version, subscribed}`. Each `entity` is the standard entity envelope (`name`, `serial`, `owners`, `description`, `fields[]`, …) used by `get_entity`.
- `page_info`: `{page_num, page_size, total}`.

Examples:

```bash
# my entities (owner)
gdpa-cli run ems --input '{"action":"list_entities"}'

# all tables / entities under an RDS storage (previously list_storage_entity)
gdpa-cli run ems --input '{"action":"list_entities","storage_uri":"tiktok/mysql/new_one_rds"}'

# explicit override: my entities inside a specific storage
gdpa-cli run ems --input '{"action":"list_entities","storage_uri":"tiktok/mysql/new_one_rds","mode":2}'
```

## `get_entity`

Get entity detail (schema / columns). Maps to `GET /api/platform/v2/entity/:uri`.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `uri` | string | Yes | e.g. `tiktok/mysql__new_one_rds__new_table_1` |

```bash
gdpa-cli run ems --input '{
  "action": "get_entity",
  "uri": "tiktok/mysql__new_one_rds__new_table_1"
}'
```

## `get_entity_online_ddl`

Query an RDS table's online DDL across vregions. Maps to `POST /api/platform/v2/entity/ddl/query_online`.

The **backend** is scoped at `(storage_uri, table_name, vregions)`, NOT the entity uri. The skill provides a convenience layer: if you only pass the entity `uri`, it calls `GetEntity` first to resolve `storage_uri` + `table_name` from the entity mapping (`resource.entity_mapping.mapping.mysql.storageUri` / `tablename`).

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `storage_uri` | string | One of the two groups | e.g. `tiktok/mysql/ies_item` |
| `table_name` | string | One of the two groups | Physical MySQL table name (may differ from the entity name, e.g. entity `tiktok/item_info` → table `item`) |
| `uri` | string | Alternative | Entity URI; skill resolves storage_uri + table_name automatically |
| `vregions` | []string or csv | No | e.g. `["Singapore-Central", "US-East"]`; omitted → all vregions the storage is deployed to |

Response:
- `storage_uri`, `table_name`, `vregions`, `entity_uri` (if resolved via uri) are echoed in `data` for traceability.
- The actual DDLs are in `data.data.online_ddl_list` / `ddl_list` keyed by vregion.

```bash
# By entity uri (convenience — resolves storage_uri + table_name automatically).
gdpa-cli run ems --input '{
  "action": "get_entity_online_ddl",
  "uri": "tiktok/item_info",
  "vregions": ["Singapore-Central", "US-East"]
}'

# By storage_uri + table_name (skips the GetEntity hop).
gdpa-cli run ems --input '{
  "action": "get_entity_online_ddl",
  "storage_uri": "tiktok/mysql/ies_item",
  "table_name": "item",
  "vregions": ["Singapore-Central"]
}'
```
