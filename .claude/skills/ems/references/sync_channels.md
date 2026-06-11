# EMS · Storage sync channel actions

`get_storage_sync_channel`（list of edges）和 `get_storage_sync_channel_detail`（one edge 的子任务级 lag / link / throughput）。先读 `SKILL.md`，再回到这里。

## `get_storage_sync_channel`

List the sync edges of a storage. Maps to `GET /sdp/v1/dts/operation/edge/list?storageURI=...` (served through the ent.tiktok-row.net proxy onto `tiktok-sdp-va`).

This is the **list** endpoint and it is the only one you need for "show me the sync topology" / "what links does this storage have". It is NOT a substitute for `get_storage_sync_channel_detail` — that endpoint returns the per-edge sub-task breakdown which is more expensive and only worth fetching when the user has already identified ONE edge they care about. See "When talking to the user" below.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `storage_uri` | string | One of these | e.g. `tiktok/mysql/new_one_rds`. Fast path — no extra round-trip. |
| `psm` | string | One of these | e.g. `toutiao.mysql.ies_item`. Convenience — the skill resolves PSM → URI via one `list_storages` hop, then calls SDP. Use this when the user only knows the service PSM. |

When BOTH are set, `storage_uri` wins (the canonical identifier is already in hand; we skip the resolution to keep the fast path fast). Either / or input is also enough — at least one of `storage_uri` or `psm` must be provided, otherwise the action returns `INPUT-001`.

### Response fields

- `data` — raw SDP envelope, carries `intention_diff` (pre-check diff against SOT) and `edge_list` (actual sync links). For programmatic consumers.
- `edge_count` — number of sync edges.
- `storage_uri` — the URI actually queried (echoed verbatim if the caller passed `storage_uri`; populated from the PSM resolution otherwise).
- `resolved_from_psm` — present only when the URI was looked up from the input `psm`. Echoes the PSM so the caller can audit "did the right storage get queried?".
- `mermaid` — ready-to-render `flowchart LR` source (no fence). Nodes are grouped by `(VRegion / VDC)` subgraphs; edge labels carry `taskType | status | ops: <allow_operate>`. Empty list → a placeholder `empty["No sync links"]` node.
- `ascii` — multi-line plain-text topology. Unique nodes render as Unicode-box cards numbered `[1]`, `[2]`, ... (`VRegion / VDC` on the header line, `PSM` on the body line, uniform box width). Edges below reference nodes by index: `[1] ──► [2]   DFLOW · STOPPED · ops: start`. Empty list → `(no sync links)`.

  Example:

  ```
  Nodes:
    ┌────────────────────────────────────┐
    │ [1] US-East / maliva               │
    │     toutiao.mysql.hw0310test       │
    └────────────────────────────────────┘
    ┌────────────────────────────────────┐
    │ [2] Singapore-Central / sg1        │
    │     toutiao.mysql.hw0310test       │
    └────────────────────────────────────┘

  Edges:
    [1] ──► [2]   DFLOW · STOPPED · ops: start
    [2] ──► [1]   DFLOW · STOPPED · ops: start
  ```

### When talking to the user (agent guidance)

Default to a "list first, ask before detail" flow:

1. Call `get_storage_sync_channel` once. The response already carries each edge's `overall_info` (taskType, status, lag, qps, throughput, consistency_rate) inside `data.edge_list`, so it is enough for any "give me the sync topology" question without paying for a per-edge detail call.
2. Render the topology using `mermaid` (preferred — wrap it in a ```mermaid fenced block) or fall back to `ascii` for plain-text contexts. Pair it with a compact per-edge table: `(direction, taskType, status, lag, qps, throughput)`. Do **not** dump `data.edge_list` verbatim — it is for programmatic consumers and contains debug fields users don't need to read.
3. End with a one-line offer: e.g. "如需某条 edge 的子任务级 lag / link / throughput 详情，告诉我具体方向（例如 `Singapore-Central → US-TTP`）即可。" Do NOT pre-fetch `get_storage_sync_channel_detail` for any edge until the user has explicitly named one — for storages with many sync links this would multiply latency by edge count for data the user may not even read.

When the user has named ONE edge (e.g. clicked into the EMS `storage_iac/detail?syncNodeId=A->B&uri=...` page, or asked "查询 X→Y 这条同步链路的延迟/状态"), call `get_storage_sync_channel_detail` — only that endpoint returns the sub-task breakdown (one DTS task per VDC inside the source / target VRegion) that powers EMS's per-edge detail page.

### Response example

```json
{
  "success": true,
  "action": "get_storage_sync_channel",
  "data": {
    "storage_uri": "tiktok/mysql/new_one_rds",
    "edge_count": 2,
    "mermaid": "flowchart LR\n    subgraph sg1 [\"US-East / maliva\"]\n        n1[\"toutiao.mysql.hw0310test\"]\n    end\n    subgraph sg2 [\"Singapore-Central / sg1\"]\n        n2[\"toutiao.mysql.hw0310test\"]\n    end\n    n1 -->|\"DFLOW | STOPPED | ops: start\"| n2\n    n2 -->|\"DFLOW | STOPPED | ops: start\"| n1\n",
    "ascii": "Nodes:\n  ┌────────────────────────────────────┐\n  │ [1] US-East / maliva               │\n  │     toutiao.mysql.hw0310test       │\n  └────────────────────────────────────┘\n  ┌────────────────────────────────────┐\n  │ [2] Singapore-Central / sg1        │\n  │     toutiao.mysql.hw0310test       │\n  └────────────────────────────────────┘\n\nEdges:\n  [1] ──► [2]   DFLOW · STOPPED · ops: start\n  [2] ──► [1]   DFLOW · STOPPED · ops: start",
    "data": { "edge_list": [ ], "intention_diff": null, "config": { } }
  }
}
```

## `get_storage_sync_channel_detail`

Get the detail for ONE edge inside a storage's sync channel. Maps to `POST /sdp/v1/dts/operation/edge/detail` (the same SDP backend that powers EMS's `storage_iac/detail?syncNodeId=...&uri=...` page). The response carries the per-edge lag / throughput / link metadata and the breakdown of sub-tasks (one per VDC inside the source / target VRegion), which `get_storage_sync_channel` does not return.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `storage_uri` | string | Convenience | e.g. `tiktok/mysql/ies_item`. Required (alongside src/dst hints) when caller does NOT supply all five SDP fields below. |
| `psm` | string | Convenience | e.g. `toutiao.mysql.ies_item`. Alternative to `storage_uri` — the skill resolves PSM → URI via one `list_storages` hop. URI wins when both are set. |
| `src_vdc` | string | Convenience | e.g. `useast5`. Wins over `src_vregion` when both are set. |
| `dst_vdc` | string | Convenience | e.g. `useast8`. Wins over `dst_vregion` when both are set. |
| `src_vregion` | string | Convenience | e.g. `US-TTP`. Used only when `src_vdc` is not provided; matched case-insensitively against the edge_list. |
| `dst_vregion` | string | Convenience | e.g. `US-TTP2`. Used only when `dst_vdc` is not provided. |
| `src_psm` | string | Direct | One of the five SDP body fields. Bypasses the convenience lookup. |
| `dst_psm` | string | Direct | — |
| `type` | string | Direct | Storage type as a **lower-case string** (`mysql`, `abase`, `bytedoc`, ...). Note: NOT the integer `ResourceType` enum used by `list_storages`. |

### Two input modes

1. **Convenience mode** (recommended) — pass `storage_uri` (or `psm`) + a src hint (`src_vdc` or `src_vregion`) + a dst hint (`dst_vdc` or `dst_vregion`). The skill resolves any input `psm` to a URI via `list_storages`, calls `get_storage_sync_channel(storage_uri)` once, finds the unique edge whose endpoints match, and uses its `src_psm` / `dst_psm` / `src_vdc` / `dst_vdc` / `type` to call the SDP detail endpoint. If the hint matches zero or multiple edges, the action returns an error listing the available `(src_vregion/src_vdc -> dst_vregion/dst_vdc)` pairs so the caller can disambiguate.
2. **Direct mode** — pass all five SDP body fields (`src_psm` + `dst_psm` + `src_vdc` + `dst_vdc` + `type`). The skill skips both lookups (PSM resolution AND edge list) and calls `POST /sdp/v1/dts/operation/edge/detail` verbatim. Useful when the caller already has the exact tuple from `get_storage_sync_channel.edge_list[i].base_info`. `psm` and `storage_uri` are ignored in this mode (no need to resolve them).

The two modes can be mixed: explicit `src_psm` / `dst_psm` / `type` always win over fields resolved from the edge list, so the convenience lookup only fills in the *missing* values.

### Response fields

- `request` — echoed body (`src_psm`, `dst_psm`, `src_vdc`, `dst_vdc`, `type`) actually sent to SDP. Useful audit trail when the convenience path resolved fields automatically.
- `storage_uri` — echoed only when convenience mode was used.
- `resolved_from_psm` — present only when convenience mode resolved the URI from an input `psm`. Echoes the PSM so the caller can audit which storage was actually queried.
- `resolved_vregions` — `{src_vregion, dst_vregion}` resolved from the edge list when the caller passed VDCs only (or vice versa). Omitted when neither side is known.
- `data` — raw SDP detail payload. Forward-compatible passthrough; do not rely on its exact shape.

### When talking to the user (agent guidance)

- Lead with the human-friendly summary (status + lag + throughput) extracted from `data`, not the full payload. The full `data` object is for programmatic consumers.
- If the convenience lookup failed because the caller's hint matches multiple edges, surface the candidate list verbatim — the user typically just needs to pick the exact `src_vdc -> dst_vdc` pair to disambiguate.

### Response example

```json
{
  "success": true,
  "action": "get_storage_sync_channel_detail",
  "data": {
    "request": {
      "src_psm": "toutiao.mysql.ies_item",
      "dst_psm": "toutiao.mysql.ies_item",
      "src_vdc": "useast5",
      "dst_vdc": "useast8",
      "type": "mysql"
    },
    "storage_uri": "tiktok/mysql/ies_item",
    "resolved_vregions": {
      "src_vregion": "US-TTP",
      "dst_vregion": "US-TTP2"
    },
    "data": { }
  }
}
```

### Examples

```bash
# Convenience by storage_uri: just point at the storage and the two VDCs.
gdpa-cli run ems --session-id "$SESSION_ID" --input '{
  "action": "get_storage_sync_channel_detail",
  "storage_uri": "tiktok/mysql/ies_item",
  "src_vdc": "useast5",
  "dst_vdc": "useast8"
}'

# Convenience by PSM: single hop, the skill resolves PSM → URI for you.
gdpa-cli run ems --session-id "$SESSION_ID" --input '{
  "action": "get_storage_sync_channel_detail",
  "psm": "toutiao.mysql.ies_item",
  "src_vdc": "useast5",
  "dst_vdc": "useast8"
}'

# Convenience by VRegion (when there is only one VDC per side):
gdpa-cli run ems --session-id "$SESSION_ID" --input '{
  "action": "get_storage_sync_channel_detail",
  "storage_uri": "tiktok/mysql/ies_item",
  "src_vregion": "US-TTP",
  "dst_vregion": "US-TTP2"
}'

# Direct: the exact tuple captured from the curl / from edge_list.
gdpa-cli run ems --session-id "$SESSION_ID" --input '{
  "action": "get_storage_sync_channel_detail",
  "src_psm": "toutiao.mysql.ies_item",
  "dst_psm": "toutiao.mysql.ies_item",
  "src_vdc": "useast5",
  "dst_vdc": "useast8",
  "type":   "mysql"
}'
```
