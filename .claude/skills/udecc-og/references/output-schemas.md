# UDECC OG Skill 输出结构

每条响应都被包到统一外壳：

```json
{
  "udecc-og": {
    "success": <bool>,
    "action":  "<action>",
    "data":    <action-specific>,
    "error":   "<error string, present only when success=false>"
  }
}
```

下面只列 `data` 字段。

## fetch_meta

```json
{
  "texas_catalog": [
    {"tag": "1.5.1", "name": "User-Generated Content", "path": "User Data > UGC > ...", "description": "..."},
    ...
  ],
  "texas_catalog_hint": "Use the `tag` value as `tx_catalog_id` on each leaf field.",
  "docs_url": "https://decc.tiktok-row.net/category",
  "field_rejection_templates": ["...", "..."],     // include != catalogs_only
  "rejection_templates_hint":  "Skim before submit_*"
}
```

## read_entity_schema

服务端原样返回（透传 UDECC OpenAPI `data` 字段）。典型结构：

```json
{
  "entity":          { ... },
  "schema":          { ... },
  "common_objects":  { ... },
  "audit_status":    "...",
  "history_versions":[ ... ]
}
```

## create_web_service / create_log_service

### Preview 阶段（无 `confirmed`）

```json
{
  "preview": {
    "action":            "create_web_service",
    "target_url":        "https://decc.tiktok-row.net/unified_api/v2/open_api/v1/service/web/create",
    "body":              { ...完整请求体... },
    "ticket_prediction": ["Will create 1 ticket in US (Texas / USTS reviewer team) for gateway=OG"],
    "next_step":         "Re-issue the SAME input + `\"confirmed\": true` to actually submit the ticket(s).",
    "reminder":          "Service tickets typically take 1–2 weeks to be reviewed."
  }
}
```

### Confirmed 阶段（`confirmed=true`）

```json
{
  "submitted": true,
  "ticket_id": "<id-from-server>",   // 当 server 返回纯字符串时
  "raw":       <server original data>
}
```

## create_web_endpoint

### Preview 阶段

```json
{
  "preview": {
    "action":            "create_web_endpoint",
    "target_url":        "https://decc.tiktok-row.net/unified_api/v2/open_api/v1/endpoint/web/create",
    "body":              { ...完整请求体（含 http_schema 和 common_object）... },
    "schema_summary": {
      "leaf_count":             12,
      "missing_description":    ["request_schema.body.user_id", ...],
      "missing_tx_catalog_id":  ["query_params.lang", ...],
      "invalid_special_attr":   ["request.headers.x-foo [special_attribute=METRIC_TAG, scope=request.headers]"],
      "used_special_attribute": true,
      "hint":                   "Each leaf field must have BOTH `description` and `tx_catalog_id`. ..."
    },
    "ticket_prediction": ["Will create 1 endpoint ticket: region=EU gateway=AG path=/api/v1/demo method=POST"],
    "next_step":         "Review the schema_summary; if missing_description or missing_tx_catalog_id are non-empty, fix them first. Re-issue with `\"confirmed\": true` to submit.",
    "reminder":          "Endpoint tickets typically take 1–2 weeks. Tag every leaf field with `tx_catalog_id` and a meaningful `description`."
  }
}
```

> `schema_summary` 由本 skill 在客户端计算（不发任何请求），见 `tagging-spec.md`。

### Confirmed 阶段

```json
{
  "submitted":       true,
  "ticket_id":       "<id>",       // 当 server 返回 map 且包含 ticket_id
  "ticket_version":  <int>,
  "is_success":      true,
  "err_msg":         "",
  "raw":             <server original>
}
```

## create_uf_endpoint

### Preview 阶段

```json
{
  "preview": {
    "action":     "create_uf_endpoint",
    "target_url": "https://decc.tiktok-row.net/unified_api/v2/open_api/v1/uf_endpoint/web/create",
    "body":       { ...完整请求体... },
    "summary":    [
      "from_stage=from_swagger id=<uf-id> entity_id=<entity-id>",
      "path=/api/v1/uf/demo method=POST",
      "assurance_path=map[caller_vpc:Office_Net callee_vpc:US_VPC1]"
    ],
    "next_step":  "Re-issue the SAME input + `\"confirmed\": true` to actually submit the UF endpoint ticket.",
    "reminder":   "UF endpoint accepts the platform's full Unified Schema (from_swagger.* defs / Dynamic Params / Common Object). Make sure `defs` / `dynamic_params` are correctly set if your schema references them."
  }
}
```

### Confirmed 阶段

同 `create_web_endpoint` confirmed 形态。
