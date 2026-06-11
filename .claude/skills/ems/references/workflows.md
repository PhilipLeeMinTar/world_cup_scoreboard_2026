# EMS · Workflow inspection actions

`list_workflows`、`get_workflow`。这两个是 read-only：浏览 schema-change workflow + 看 pipeline / BPM 状态。**写流程**（创建/批准/推进/关闭 workflow）见 `references/schema_change.md`。

## `list_workflows`

List schema-change workflows. Maps to `GET /api/platform/v1/schema_change`.

Three common modes of use:

1. **"my workflows"** — no filters. Defaults to `mode=2`, backend derives the author from JWT. Skill echoes `query_user`.
2. **"workflows on this storage"** — pass `storage_uri`. Mirrors the EMS UI Storage → Workflow tab: skill auto-fills `key=<storage_uri>`, `exact=true`, `type_list=[<storage_resource_type>, 11=Topology]`, and switches `mode` to `1` (ALL).
3. **"workflows on this entity"** — pass `entity_uri`. Mirrors the EMS UI Entity → Workflow tab: skill auto-fills `key=<entity_uri>`, `exact=true`, `type=1` (Entity), and switches `mode` to `1`.

Any explicit `key` / `type` / `type_list` / `mode` / `exact` you pass **overrides** the convenience defaults, so advanced callers can hand-craft the exact query shape.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `storage_uri` | string | No (convenience) | Shortcut for the Storage → Workflow tab. Mutually exclusive with `entity_uri`. |
| `entity_uri` | string | No (convenience) | Shortcut for the Entity → Workflow tab. Mutually exclusive with `storage_uri`. |
| `mode` | int | Defaulted | `1`=all visible workflows, `2`=only workflows authored by the JWT user. Default `2` when no convenience URI is set; `1` when `storage_uri` / `entity_uri` is set. |
| `key` | string | No | Fuzzy keyword match on the changed resource name (entity name / storage uri). Auto-filled from `storage_uri` / `entity_uri`. |
| `exact` | bool | No | Whether `key` must match exactly. Auto-set to `true` when `storage_uri` / `entity_uri` is used. |
| `type` | int | No | `ResourceType` enum. `1`=Entity, `2`=MySQL, `3`=Redis, `4`=Abase, `5`=ByteKV, `6`=ByteGraph, `7`=ByteDoc, `8`=EntStore, `9`=BCache2, `11`=Topology. |
| `type_list` | []int or csv | No | Multiple `ResourceType` filters; sent as `type_list[]=...&type_list[]=...`. Used internally when resolving `storage_uri`. |
| `change_state` | int | No | `SchemaChangeRequestState` enum filter (see table below). |
| `page_num` | int | No | Default `1` |
| `page_size` | int | No | Default `20` |

### `SchemaChangeRequestState` enum

Applies to both the `change_state` filter and the `state` field on returned workflows.

| Value | Name | Meaning |
|-------|------|---------|
| 0 | Unknown | — |
| 1 | Local | Draft stored locally |
| 2 | Remote | Pushed to remote, awaiting review |
| 3 | Merged | Code merged into master, change not yet executed on the storage |
| 4 | Applied | Schema change executed on the target storage |
| 5 | Closed | Terminal — finished (often after Applied) |
| 6 | Rejected | Review rejected |
| 7 | Approved | Review approved, not yet merged |

### Examples

```bash
# "my workflows"
gdpa-cli run ems --input '{"action":"list_workflows"}'

# Workflows on a MySQL storage (UI Storage → Workflow tab)
gdpa-cli run ems --input '{"action":"list_workflows","storage_uri":"tiktok/mysql/hw0318testa"}'

# Workflows on an Abase storage (type_list auto-becomes [4, 11])
gdpa-cli run ems --input '{"action":"list_workflows","storage_uri":"tiktok/abase/demo_ns"}'

# Workflows on an entity (UI Entity → Workflow tab)
gdpa-cli run ems --input '{"action":"list_workflows","entity_uri":"tiktok/user_replica"}'

# Only merged-but-not-yet-applied workflows on an entity (change_state=3)
gdpa-cli run ems --input '{"action":"list_workflows","entity_uri":"tiktok/user_replica","change_state":3}'

# Low-level escape hatch: hand-craft the exact query
gdpa-cli run ems --input '{"action":"list_workflows","mode":1,"key":"tiktok","type_list":[2,11],"page_size":50}'
```

## `get_workflow`

Get workflow detail by id. Maps to `GET /api/platform/v1/schema_change/:id`.

On top of the raw workflow payload, the skill also aggregates what the UI shows on the right-hand side of `https://ent.tiktok-row.net/workflow/detail/<id>`:

1. **Pipeline status** — fetched from `GET /api/platform/v1/siacflow/:id` (`build_id`, `status`, `active_jobs`) and then from BITS `GET /api/v1/pipelines/open/runs/:build_id` to expose the full job list (with `status_label` per node and any nested sub-pipeline URLs).
2. **BPM tickets** — for each nested sub-pipeline discovered inside the main pipeline (e.g. the "资源部署" / IaC Deployment node), the skill walks the sub-pipeline's jobs and extracts every entry from `jobAtom.output.bpm_ticket_info_map`, so you get a flat list of BPM ticket IDs, statuses, and links (`https://bpm-i18n.tiktok-row.net/record/<id>`) grouped by parent job + sub job.

Authentication note: `bits.bytedance.net` is a CN service and rejects the default I18N JWT. The skill therefore prefers the CN JWT (falling back to I18N). If no BITS-compatible JWT is available (e.g. you have only logged into ent.tiktok-row.net), pipeline / BPM enrichment is skipped with a `pipeline.detail_error` string instead of failing the whole call. If the outer siacflow lookup itself fails (rare), a `pipeline_error` field is added at the root of `data` instead.

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | Yes | Workflow ID, e.g. `119090688003`. **NOTE**: the param name is `id` (not `workflow_id`), to match the URL `.../workflow/detail/<id>`. The DDL-change actions (`approve_workflow_owner_gate` / `advance_workflow_bpm_ticket` / `close_workflow`) take `workflow_id` instead — that's deliberate (those operate on a workflow), but `get_workflow` reads it as a resource. |
| `include_pipeline` | bool | No | Default `true`. Set `false` to skip the siacflow + BITS pipeline fetch (plain schema_change only). |
| `include_bpm_tickets` | bool | No | Default `true`. Set `false` to skip the nested sub-pipeline traversal (keeps the main pipeline summary but omits `bpm_tickets`). Automatically forced off when `include_pipeline=false`. |

### Example response shape (trimmed)

```json
{
  "id": "119090688003",
  "data": { },
  "pipeline": {
    "build_id": 1141866277890,
    "build_url": "https://bits.bytedance.net/devops/4085329154/pipeline/open_build/1141866277890",
    "top_status": "RUNNING",
    "run_status": 2,
    "run_status_label": "RUNNING",
    "active_jobs": [
      {"id": 2633133476, "atomic_service_name": "IaC Deployment OpenAPIv2", "status": "RUNNING", "priority": 1}
    ],
    "jobs": [
      {"job_name": "Schema 校验", "job_status": 14, "status_label": "SUCCEEDED"},
      {"job_name": "资源部署",   "job_status": 3,  "status_label": "RUNNING",
       "sub_pipelines": [
         {"label": "Singapore-Central (Running)", "build_id": 1142010722050, "space_id": "1071185616642",
          "url": "https://bits.bytedance.net/devops/1071185616642/pipeline/open_build/1142010722050"}
       ]}
    ]
  },
  "bpm_tickets": [
    {"parent_job": "资源部署", "sub_job": "Execute DDL SQL",
     "id": "40927815", "vregion": "Singapore-Central",
     "status": "start", "is_finished": false, "creator": "qinmingshuai",
     "url": "https://bpm-i18n.tiktok-row.net/record/40927815"}
  ]
}
```

### Usage examples

```bash
# Default — full detail + pipeline + BPM tickets
gdpa-cli run ems --input '{"action":"get_workflow","id":"119090688003"}'

# Only the workflow payload (no BITS enrichment at all)
gdpa-cli run ems --input '{"action":"get_workflow","id":"119090688003","include_pipeline":false}'

# Keep the main pipeline summary, but skip drilling into nested sub-pipelines
gdpa-cli run ems --input '{"action":"get_workflow","id":"119090688003","include_bpm_tickets":false}'
```
