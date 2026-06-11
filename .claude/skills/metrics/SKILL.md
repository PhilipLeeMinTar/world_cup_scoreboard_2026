---
name: metrics
description: Query Metrics monitoring data for service throughput, latency, error rate, success rate, downstream/upstream dependencies, and custom time-series metrics by PSM or metric name. Use when the user wants to inspect monitoring data, diagnose service performance, compare metrics, discover tag keys, or query a specific Metrics/BytePlot metric.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# Metrics Query Agent

Query Metrics (BytePlot / BytedTrace) monitoring data for services and custom metrics.

## When to Use

Use this skill when the user wants to:

- check QPS, latency, error rate, or success rate
- inspect upstream or downstream dependency traffic
- query a specific metric name directly
- discover available tag keys before building a query
- compare the same metric across regions that the user explicitly named

## Hard Rules

1. If the request depends on a specific deployment region and the user did **not** provide `vregion`, **ask the user first**. Do not guess.
2. Do **not** enumerate `Singapore-Central`, `US-East`, `EU-TTP2`, or other regions one by one to "try your luck".
3. If the user already gave an exact metric name, query it directly with `metric`. Do not reinterpret it as a PSM or rename it.
4. Use `query_type` only for the three preset scenarios: `overview`, `downstream`, `upstream`.
5. Use `suggest_tagk` only when you need to discover filterable/groupable tags for a metric.

## Quick Decision

| User intent | Recommended input |
|-------------|-------------------|
| "看看这个服务的 QPS/延迟/错误率" | `query_type` + `psm` + `vregion` |
| "看这个服务下游/上游调用" | `query_type: downstream/upstream` + `psm` + `vregion` |
| "查这个具体 metric" | `metric` (+ optional `psm`, `filters`, `vregion`) |
| "这个 metric 有哪些 tag" | `action: "suggest_tagk"` + `metric_name` |

## Quick Start

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '<json_params>'
```

## High-Frequency Examples

### 1. Service overview

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "query_type": "overview",
  "psm": "your.service.psm",
  "vregion": "Singapore-Central"
}'
```

Use this when the user asks for "整体看一下" service health.

### 2. Downstream dependency check

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "query_type": "downstream",
  "psm": "your.service.psm",
  "vregion": "US-East",
  "duration_minutes": 30
}'
```

Use this when the user asks which downstream services are being called, with what latency and error rate.

### 3. Query a custom metric directly

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "metric": "tiktok.passport.goapi.brief_result",
  "vregion": "Singapore-Central"
}'
```

If the user already gave the metric name, do this first.

### 4. Query a metric with filters

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "metric": "service_mesh.des_rpc.request.failure",
  "psm": "tiktok.gdpa.gdpa_go",
  "vregion": "US-East",
  "duration_minutes": 30,
  "filters": [
    {"tagk": "error_type", "filter": "*", "type": "wildcard", "group_by": true}
  ]
}'
```

Use this when the user wants a filtered or grouped breakdown instead of the preset views.

### 5. Discover tag keys

```bash
gdpa-cli run metrics --session-id "$SESSION_ID" --input '{
  "action": "suggest_tagk",
  "metric_name": "bytedtrace.sdk.span.server.rate",
  "vregion": "Singapore-Central"
}'
```

Use this before building filters when you do not know the available tags.

## Common Inputs

| Field | Required | Notes |
|-------|----------|-------|
| `query_type` | preset mode only | `overview`, `downstream`, `upstream` |
| `metric` | custom mode only | Query the exact metric name directly |
| `psm` | required for `query_type` | Optional for custom metric queries |
| `vregion` | usually yes | Ask user if region matters and is missing |
| `duration_minutes` | no | Default time window is 60 minutes |
| `filters` | no | Extra tag filters / grouping |
| `action` | suggest tag mode only | Use `suggest_tagk` |
| `metric_name` | suggest tag mode only | Metric to inspect for tags |

## Region Guidance

- If the user explicitly names a region, use exactly that `vregion`.
- If the user asks for multi-region comparison, only query the regions they named.
- If the user did **not** provide region and the answer may differ by region, stop and ask.
- Do not "probe" multiple regions as a fallback.

Examples of prompts you should ask instead of guessing:

- "这个指标要查哪个 vregion？例如 `Singapore-Central`、`US-East`。"
- "你要看单个 region，还是明确比较哪几个 region？"

## Output Expectations

### Smart query

Returns labeled `sections`, each with a summary of QPS / latency / error related series.

### Custom query

Returns the requested metric with grouped series, datapoints, and summary statistics.

### Suggest tag keys

Returns the metric's available tag keys so you can build filters safely.

## Defaults and Caveats

- Default time range is the last 60 minutes unless overridden.
- Latency values are usually in microseconds; convert to milliseconds when presenting results.
- `series_count: 0` may mean there is no traffic, no errors, or the wrong region/filter was used. Do not silently retry another region.
- Custom/business metrics are valid even if they do not follow BytedTrace naming conventions.

## Reference

Detailed parameter tables, PPE / `_region` mapping, metric families, output schemas, and extended examples live in [SKILL_reference.md](./SKILL_reference.md).
