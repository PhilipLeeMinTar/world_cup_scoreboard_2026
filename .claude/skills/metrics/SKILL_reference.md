# Metrics Reference

This file keeps the long-form reference material for `metrics`. Read it only when the quick entry in [SKILL.md](./SKILL.md) is insufficient.

## Command Format

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '<json_params>'
```

## Additional Examples

### Upstream callers

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "query_type": "upstream",
  "psm": "your.service.psm",
  "vregion": "Singapore-Central"
}'
```

### Overview with extra method filter

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "query_type": "overview",
  "psm": "your.service.psm",
  "vregion": "Singapore-Central",
  "filters": [
    {"tagk": "_method", "filter": "GetUser", "type": "literal_or"}
  ]
}'
```

### Multi-field metric

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "metric": "tce.host.tcp.mt",
  "tenant": "computation.tce",
  "multi_field_expr": "tcp_retrans_rate",
  "aggregator": "sum",
  "top_k": "top-10-max",
  "vregion": "China-North",
  "filters": [
    {"tagk": "cluster", "filter": "koala-lf", "type": "literal_or", "group_by": true},
    {"tagk": "host", "filter": "n196-032-155", "type": "literal_or", "group_by": true}
  ]
}'
```

### Query log event rate

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "metric": "bytedtrace.sdk.event.log.rate",
  "psm": "your.service.psm",
  "vregion": "Singapore-Central",
  "filters": [
    {"tagk": "_log_level", "filter": "4|5|6", "type": "literal_or", "group_by": true}
  ]
}'
```

## PPE and BytePlot `_region`

PPE shares the same Metrics gateway / control plane as production. The main difference is the BytePlot query parameter `_region`, not a separate VRegion type.

- If `_region` or `metrics_region` is provided, it overrides `vregion`.
- PPE still uses the JWT of the corresponding online region.

| `_region` / `vregion` (PPE) | Gateway |
|-----------------------------|---------|
| `Singapore-PPE`, `US-PPE`, `Asia-SouthEastBD-PPE` | `metrics-fe-i18n.tiktok-row.org` |
| `EU-TTP2-PPE`, `US-EastRed-PPE` | `metrics-fe-eu.tiktok-eu.org` |
| `US-TTP-PPE`, `US-TTP2-PPE` | `metrics-svc-platform-ttp.tiktok-us.org` |
| `China-PPE`, `China-East-PPE`, `China-North6-PPE` | `metrics-fe.byted.org` |

## Suggest Tag Keys Mode

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Must be `suggest_tagk` |
| `metric_name` | string | Yes | Metric name to inspect |
| `vregion` | string | No | Region to query |
| `_region` / `metrics_region` | string | No | Explicit BytePlot `_region`, overrides `vregion` |

## Smart Query Mode

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_type` | string | Yes | `overview`, `downstream`, `upstream` |
| `psm` | string | Yes | Target service PSM |
| `vregion` | string | No | Region to query |
| `_region` / `metrics_region` | string | No | Explicit BytePlot `_region`, overrides `vregion` |
| `duration_minutes` | int | No | Default `60` |
| `start` | int64 | No | Millisecond Unix timestamp |
| `end` | int64 | No | Millisecond Unix timestamp |
| `tenant` | string | No | BytePlot tenant, default `default` |
| `filters` | array | No | Extra filters merged into each preset query |

### Supported `query_type`

| `query_type` | Aliases | Description |
|--------------|---------|-------------|
| `downstream` | `caller` | Outbound call analysis |
| `upstream` | `callee`, `server` | Inbound caller analysis |
| `overview` | `service` | Service-level health overview |

## Custom Query Mode

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `metric` | string | Yes | Metric name |
| `psm` | string | No | Auto-added as `_psm` filter when provided |
| `vregion` | string | No | Region to query |
| `_region` / `metrics_region` | string | No | Explicit BytePlot `_region`, overrides `vregion` |
| `duration_minutes` | int | No | Default `60` |
| `start` | int64 | No | Millisecond Unix timestamp |
| `end` | int64 | No | Millisecond Unix timestamp |
| `aggregator` | string | No | `sum`, `avg`, `max`, `min`, `count` |
| `downsample` | string | No | Such as `1m-avg`, `5m-sum` |
| `top_k` | string | No | Such as `top-10-max` |
| `rate` | bool | No | Rate calculation. Auto-enabled when the metric name looks like a cumulative counter (`throughput`, `.count`, `.failure`, `.success`, `.qps`, `request.*`, etc.) AND the user did not pass `rate` AND `multi_field_expr` is empty. Pass `rate: false` (or set `multi_field_expr`) to opt out and avoid double rate calculation. |
| `tenant` | string | No | Non-default tenant support |
| `is_multi_field` | bool | No | Enable multi-field mode |
| `multi_field_expr` | string | No | Field expression, auto-enables multi-field mode |
| `filters` | array | No | Tag filters |

## Filter Format

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tagk` | string | Yes | Tag key |
| `filter` | string | Yes | Tag value or pattern |
| `type` | string | No | `literal_or` (default), `wildcard`, `regexp` |
| `group_by` | bool | No | Group results by this tag |

## Metrics Reference

### BytedTrace server span metrics

| Metric | Description |
|--------|-------------|
| `bytedtrace.sdk.span.server.rate` | Server QPS |
| `bytedtrace.sdk.span.server.latency.us.pct99` | Server latency P99 in microseconds |
| `bytedtrace.sdk.span.server.send.bytes` | Response size |
| `bytedtrace.sdk.span.server.receive.bytes` | Request size |

Common tags: `_method`, `_from_service`, `_from_dc`, `_from_cluster`, `_is_error`, `_status_code`, `_biz_status_code`, `_service_type`

### BytedTrace client span metrics

| Metric | Description |
|--------|-------------|
| `bytedtrace.sdk.span.client.rate` | Client QPS |
| `bytedtrace.sdk.span.client.latency.us.pct99` | Client latency P99 in microseconds |
| `bytedtrace.sdk.span.client.send.bytes` | Request size |
| `bytedtrace.sdk.span.client.receive.bytes` | Response size |

Common tags: `_method`, `_to_service`, `_to_method`, `_to_dc`, `_to_cluster`, `_to_service_type`, `_is_error`, `_status_code`, `_biz_status_code`

### Event / log metrics

| Metric | Description |
|--------|-------------|
| `bytedtrace.sdk.event.log.rate` | Log event rate |

Important tag: `_log_level` where `4` = Warn, `5` = Error, `6` = Fatal.

### Classic metrics

| Metric | Description |
|--------|-------------|
| `toutiao.service.thrift.callee.success.throughput` | Callee success throughput |
| `toutiao.service.thrift.callee.error.throughput` | Callee error throughput |
| `toutiao.service.thrift.callee.success.latency.us` | Callee success latency |
| `toutiao.service.thrift.caller.success.throughput` | Caller success throughput |
| `toutiao.service.thrift.caller.error.throughput` | Caller error throughput |
| `toutiao.service.thrift.caller.success.latency.us` | Caller success latency |
| `service_mesh.des_rpc.request.failure` | Service mesh DES-RPC failure |

### Global tags

`_psm`, `_dc`, `_cluster`, `_env`, `_deploy_stage`

### Pre-aggregation dimensions

High-cardinality client / server rate and latency metrics are commonly pre-aggregated on:

`_psm`, `_dc`, `_cluster`, `_env`, `_deploy_stage`, `_status_code`, `_is_error`, `_biz_status_code`, `_method`, `_to_service`, `_from_service`, `_to_cluster`, `_from_cluster`, `_to_dc`, `_from_dc`

## Output Schemas

### Smart query output

```json
{
  "success": true,
  "query_type": "downstream",
  "psm": "your.service.psm",
  "data": {
    "query_type": "downstream",
    "psm": "your.service.psm",
    "vregion": "Singapore-Central",
    "section_count": 3,
    "sections": [
      {
        "label": "Downstream QPS by Service & DC",
        "metric": "bytedtrace.sdk.span.client.rate",
        "series_count": 2
      }
    ]
  }
}
```

### Custom query output

```json
{
  "success": true,
  "metric": "bytedtrace.sdk.span.server.rate",
  "psm": "your.service.psm",
  "data": {
    "metric": "bytedtrace.sdk.span.server.rate",
    "vregion": "Singapore-Central",
    "series_count": 1,
    "series": [
      {
        "metric": "bytedtrace.sdk.span.server.rate",
        "tags": {"_psm": "your.service.psm"},
        "datapoints_count": 60
      }
    ]
  }
}
```

### Suggest tag keys output

```json
{
  "success": true,
  "action": "suggest_tagk",
  "metric_name": "service_mesh.des_rpc.request.failure",
  "data": {
    "metric_name": "service_mesh.des_rpc.request.failure",
    "vregion": "US-East",
    "tag_keys": ["_psm", "error_type"],
    "tag_count": 2
  }
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `either 'metric' or 'query_type' parameter is required` | Missing both | Provide one mode selector |
| `'psm' is required when using 'query_type'` | Missing PSM | Add `psm` |
| `unknown query_type` | Bad preset value | Use `overview`, `downstream`, `upstream` |
| `invalid vregion` | Unknown region | Use a supported VRegion |
| `authentication failed` | JWT issue | Check `gdpa-cli login` |

## Notes

- Default time range is the last 60 minutes.
- `start` / `end` must be millisecond Unix timestamps.
- Counter / QPS metrics often auto-enable rate calculation.
- Use `downsample` for large time windows.
- This skill is read-only.
