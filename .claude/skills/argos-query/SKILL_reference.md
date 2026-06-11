# Argos Query Reference

This file keeps the long-form reference material for `argos-query`. Read it only when the quick entry in [SKILL.md](./SKILL.md) is insufficient.

## Command Format

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '<json_params>'
```

General `psm` queries use centralized search by default. Local file search is entered only when `env`, `env_type`, or `path` is provided.

## Input Schema

```json
{
  "psm": "my.service.name",
  "keywords": ["error"],
  "exclude_keywords": ["debug"],
  "keyword_operator": "OR",
  "log_level": "Error",
  "aggregator": "location",
  "logid": "021772604201988fdbddc55000210240c40819c720000d18743a7",
  "vregion": "Singapore-Central",
  "time_range": "10m",
  "limit": 10,
  "start": 1700000000,
  "end": 1700000600,
  "timeout_in_ms": 30000,
  "data_source_uid": "",
  "scan_span_in_min": 30,
  "env": "ppe",
  "env_type": "ppe",
  "path": "app/${psm}.log"
}
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `psm` | string | Required for centralized search, local file, and error analysis |
| `keywords` | array | Optional keyword array for centralized search |
| `exclude_keywords` | array | Keywords to exclude |
| `keyword_operator` | string | `AND` or `OR`, default `OR` |
| `log_level` | string | Log level filter for keyword search |
| `idc` | array | Optional IDC scope for keyword search (e.g. `["lf"]` / `["sinfonline","sinfonlinea"]`). Caller-supplied IDCs override the default vregion-derived scope. |
| `aggregator` | string | Error analysis dimension, commonly `location` |
| `logid` | string | Log ID for trace query |
| `vregion` | string | Region to search |
| `time_range` | string | Relative time window such as `10m`, `1h`, `24h` |
| `limit` | integer | Maximum returned log entries |
| `start` | integer | Absolute start timestamp |
| `end` | integer | Absolute end timestamp |
| `timeout_in_ms` | integer | Query timeout for keyword search |
| `data_source_uid` | string | Optional keyword search data source |
| `scan_span_in_min` | integer | LogID search-back window |
| `env` | string | Local file env |
| `env_type` | string | `ppe` or `prod` |
| `path` | string | Local file path template |

## VRegion and VDC Mapping

| VRegion | Aliases | VDCs | Argos BaseURI | JWT |
|---------|---------|------|---------------|-----|
| `Singapore-Central` | `sg`, `singapore` | sg1, my, my2, my3 | logservice-sg.tiktok-row.org | i18n |
| `US-East` | `us`, `useast`, `i18n` | maliva | logservice-us.tiktok-row.org | i18n |
| `China-North` | `cn`, `china` | lf, hl, lq, yg | logservice.byted.org | CN |
| `China-East` | `chinaeast`, `china-east` | pd, hj, yz | logservice-pd.byted.org | CN |
| `China-Pay` | `chinapay`, `china-pay` | lfzg, hlzg | logservice-zg.byted.org | CN |
| `China-Pay2` | `chinapay2`, `china-pay2` | hjzg | logservice-zg.byted.org | CN |
| `China-North6` | `cn6`, `chinanorth6` | zb, xh | logservice-cn6.byted.org | CN |
| `US-TTP` | `usttp`, `ttp` | useast5 | logservice-tx.tiktok-us.org | TTP-US |
| `US-TTP2` | `usttp2`, `ttp2` | useast8 | logservice-tx2.tiktok-us.org | TTP-US |
| `EU-TTP2` | `euttp2`, `eu-ttp2` | no1a | logservice-no1a.tiktok-eu.org | i18n |
| `US-EastRed` | `useastred`, `us-eastred` | useast2a | logservice-no1a.tiktok-eu.org | i18n |
| `China-BOE` | `boe`, `cn-boe` | boe | logservice-boe.byted.org | CN |
| `US-BOE` | `boei18n`, `boe-i18n` | boei18n | logservice-boei18n.byted.org | CN |
| `Asia-CIS` | `asia-cis`, `cis` | mycisa, mycisb, sgcisa | logservice-mycis.byted.org | i18n |
| `Asia-SouthEastBD` | `asia-southeastbd`, `asiasoutheastbd` | mya, myb, myc, bdsgdt, my5a | logservice-mya.sinf.net | i18n |
| `Europe-Central` | `europe-central`, `eu-central` | fr1a, be1a, awsfr, gcppl | logservice-sg.tiktok-row.org | i18n |
| `US-EastBD` | `us-eastbd`, `useastbd` | useast9a, useast14a | logservice-useast11a.byted.org | i18n |
| `US-EE` | `us-ee`, `usee` | va | logservice-mya.sinf.net | i18n |
| `US-TTP3` | `us-ttp3`, `ttp3` | useast15a | logservice-useast15a.lark-us.org | i18n |

## Extended Examples

### Keyword Search with multiple keywords

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "psm": "my.service.name",
  "keywords": ["error", "timeout"],
  "keyword_operator": "AND",
  "vregion": "Singapore-Central"
}'
```

### Keyword Search with exclude keywords

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "psm": "my.service.name",
  "keywords": ["error", "warn"],
  "exclude_keywords": ["debug", "test"],
  "keyword_operator": "OR",
  "vregion": "Singapore-Central"
}'
```

### Multi-region keyword search

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "psm": "my.service.name",
  "keywords": ["error"],
  "vregion": "sg,us"
}'
```

Use only when the user explicitly asked for multiple regions.

### Minimal centralized search example

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "psm": "my.service.name",
  "vregion": "China-North",
  "time_range": "1h"
}'
```

### Minimal local file example

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "psm": "my.service.name",
  "vregion": "Singapore-Central",
  "env_type": "ppe",
  "time_range": "1h"
}'
```

### LogID query with larger scan span

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "logid": "021772604201988fdbddc55000210240c40819c720000d18743a7",
  "vregion": "US-East",
  "scan_span_in_min": 60
}'
```

### Multi-region error analysis

```bash
gdpa-cli run argos-query --session-id "$SESSION_ID" --input '{
  "psm": "desrpc.test.client",
  "aggregator": "location",
  "vregion": "sg,us,euttp2"
}'
```

Use only when the user explicitly asked for multi-region aggregation.

## Output Formats

### Central Search output

```json
{
  "success": true,
  "psm": "my.service.name",
  "keywords": ["error", "timeout"],
  "log_level": "Error",
  "region": "Singapore-Central",
  "total": 5,
  "finished": true,
  "logs": [
    {
      "content": "2026-03-09 10:00:01 ERROR failed to process request",
      "highlight": true
    }
  ]
}
```

### Local File output

```json
{
  "success": true,
  "psm": "desrpc.stability.thrift_server",
  "region": "US-East",
  "total": 2,
  "pod": "dp-2a6b225666-559bd8c5fc-shnpr",
  "logs": [
    {
      "time": "2026-02-05 14:19:02.085",
      "content": "Info 2026-02-05 ..."
    }
  ]
}
```

### LogID output

```json
{
  "success": true,
  "logid": "021772604201988fdbddc55000210240c40819c720000d18743a7",
  "region": "Singapore-Central",
  "total": 3,
  "traces": [
    {
      "psm": "my.service.name",
      "pod": "pod-abc-123",
      "ip": "10.0.0.1",
      "env": "prod",
      "idc": "sg1",
      "level": "INFO",
      "message": "request processed successfully"
    }
  ]
}
```

### Error Analysis output

```json
{
  "success": true,
  "psm": "desrpc.test.client",
  "aggregator": "location",
  "region": "EU-TTP2",
  "total_items": 4,
  "total_errors": 57353,
  "items": [
    {
      "location": "rpcclient.go:141",
      "count": 55232,
      "level": "Warn",
      "message": "[DoRPCCall] succ for testcase ...",
      "cluster": "no1a",
      "idc": "no1a"
    }
  ]
}
```

### Multi-region output

```json
{
  "success": true,
  "multi_region": true,
  "regions": ["Singapore-Central", "US-East"],
  "total": 8,
  "results": [
    {
      "region": "Singapore-Central",
      "success": true,
      "total": 5
    },
    {
      "region": "US-East",
      "success": true,
      "total": 3
    }
  ]
}
```

## Timestamp and Timezone Rules

`start` and `end` are Unix timestamps, but the units differ by mode:

| Mode | Unit |
|------|------|
| Keyword Search | seconds |
| Local File | milliseconds |

Prefer `time_range` unless the user explicitly provided absolute timestamps.

If the user gives Beijing time such as `2026-03-09 03:00:00 ~ 11:00:00`, convert it directly with the local timezone. Do not manually subtract 8 hours.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `psm parameter is required` | Missing PSM and no logid | Add `psm` or `logid` |
| `invalid time_range format` | Bad format | Use `5m`, `1h`, `24h` |
| `authentication failed` | JWT issue | Run `gdpa-cli login` |
| `total: 0` | Wrong region / env / window | Confirm `vregion`, `env`, and time range; do not auto-switch |

## Notes

- Keyword Search is the best default for content search.
- Local File mode is commonly used for PPE validation.
- `total: 0` usually means the scope is wrong, not that logs do not exist.
- This skill is read-only.
