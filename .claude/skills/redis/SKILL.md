---
name: redis
description: Query Redis (ByteCache) data via ByteCloud gateway across multiple regions. Use whenever the user wants to execute Redis read-only commands, check key values, query hash fields, search for Redis services by name, or list supported commands. Also trigger when the user mentions Redis, ByteCache, cache query, or wants to look up cached data.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# Redis Agent

Query Redis (ByteCache) data via ByteCloud gateway.

> **When to Use**: Execute Redis read-only commands against ByteCache clusters across Singapore, US, China, BOE, and EU environments.

## Quick Start

```bash
# Execute a GET command (resolves service name to cluster automatically)
gdpa-cli run redis --session-id "$SESSION_ID" --input '{
  "service_name": "toutiao.redis.my_service",
  "command": "GET",
  "args": "my_key"
}'

# Execute with specific VRegion
gdpa-cli run redis --session-id "$SESSION_ID" --input '{
  "service_name": "toutiao.redis.my_service",
  "command": "HGET",
  "args": "my_hash my_field",
  "vregion": "China-North"
}'

# List all supported commands
gdpa-cli run redis --session-id "$SESSION_ID" --input '{
  "action": "list_commands"
}'

# Search for a service by name
gdpa-cli run redis --session-id "$SESSION_ID" --input '{
  "action": "search_service",
  "keyword": "generator_test"
}'
```

## Input Parameters

### Required (for execute_command)

| Parameter | Type | Description |
|-----------|------|-------------|
| `service_name` | string | Redis service PSM (e.g. `toutiao.redis.my_service`). Agent resolves this to a cluster automatically |
| `args` | string | Key name or command arguments |

### Optional

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | `execute_command` | Action type: `execute_command`, `list_commands`, or `search_service` |
| `command` | string | `GET` | Redis command. Validated against the API's supported list (run `list_commands` to see all) |
| `vregion` | string | `Singapore-Central` | Target VRegion (see routing table below) |
| `keyword` | string | - | Search keyword (required for `search_service`, matches against PSM name) |

### Supported Commands

Commands are **not hardcoded** -- they are validated at runtime against the ByteCloud API's supported list. Use `action: "list_commands"` to see the full list (100+ commands including GET, HGET, HGETALL, TTL, EXISTS, ZSCORE, ZRANGE, etc.).

## How execute_command Works

1. **Resolve service**: Calls ByteHeart `deploy_info` by PSM to get the authoritative per-VRegion Redis `service_id` (exact PSM + VRegion match -- no fuzzy search). `service_id` namespace is partitioned by DeploySite (i18n / tx-ttp / eu-ttp / CN / BOE), not per-VRegion; `GetService(service_id)` is then called on the site's **resolve gateway** to fetch the cluster list.
2. **Pick cluster**: For each VDC the service exposes two clusters — `module=redis` (underlying instance) and `module=alchemy` (openapi proxy). For `architecture=alchemy` services the agent **must** pick the `module=alchemy` cluster whose VDC belongs to the requested VRegion; the `module=redis` cluster is not accepted by the openapi gateway and will return 403.
3. **Validate command**: Calls the ListCommands API to verify the command is supported.
4. **Execute**: Sends the command to the resolved cluster via the site's data-plane gateway (same host as the resolve gateway for i18n/TTP/EU/CN). The request body includes a `row_og_required_schema` block declaring `{PSM, cluster_name}` — ByteCloud openapi gateway uses it for resource-level IAM. Missing this field causes the gateway to demand `redis.resource.update` permission even for read-only commands.

## VRegion Routing

| VRegion | Aliases | Resolve Gateway (service_id) | x-bcgw-vregion | Data Gateway (execute) | JWT |
|---------|---------|------------------------------|----------------|------------------------|-----|
| `Singapore-Central` (default) | `sg` | cloud-i18n.bytedance.net | `sg` | cloud-i18n.bytedance.net | i18n |
| `US-East` | `us`, `i18n` | cloud-i18n.bytedance.net | `us` | cloud-i18n.bytedance.net | i18n |
| `US-TTP` / `US-TTP2` | `us-ttp` | cloud.tiktok-us.net | — | cloud.tiktok-us.net | US-TTP |
| `EU-TTP2` | `eu-ttp2` | bc-iedt-gw.tiktok-eu.net | — | bc-iedt-gw.tiktok-eu.net | EU-TTP |
| `US-EastRed` | `us-eastred` | bc-iedt-gw.tiktok-eu.net | — | bc-iedt-gw.tiktok-eu.net | EU-TTP |
| `China-North` | `cn`, `china` | cloud.bytedance.net | — | cloud.bytedance.net | CN |
| `China-East` | `chinaeast` | cloud.bytedance.net | — | cloud.bytedance.net | CN |
| `China-BOE` | `boe` | cloud-boe.bytedance.net | — | cloud-boe.bytedance.net | CN |
| `US-BOE` | `boei18n` | cloud-boei18n.bytedance.net | — | cloud-boei18n.bytedance.net | i18n |

> EU VRegions (EU-TTP2, US-EastRed) require non-restricted employee access (GCP).

## Output Format

```json
{
  "success": true,
  "action": "execute_command",
  "vregion": "Singapore-Central",
  "data": {
    "service_name": "toutiao.redis.my_service",
    "cluster_id": 152881,
    "cluster_name": "toutiao.redis.my_service",
    "command": "GET",
    "args": "my_key",
    "result": "my_value"
  }
}
```

## Examples

### Query a key by service name

```bash
gdpa-cli run redis --session-id "$SESSION_ID" --input '{"service_name": "toutiao.redis.my_service", "command": "GET", "args": "user:123", "vregion": "sg"}'
```

### Query a hash field in China

```bash
gdpa-cli run redis --session-id "$SESSION_ID" --input '{"service_name": "toutiao.redis.config", "command": "HGET", "args": "config rate_limit", "vregion": "cn"}'
```

### Search for a Redis service

```bash
gdpa-cli run redis --session-id "$SESSION_ID" --input '{"action": "search_service", "keyword": "des_mq"}'
```

### List supported commands

```bash
gdpa-cli run redis --session-id "$SESSION_ID" --input '{"action": "list_commands"}'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `service_name parameter is required` | Missing service name | Add `service_name` with the Redis PSM |
| `args parameter is required` | Missing key/arguments | Add `args` with key name or command arguments |
| `unsupported command` | Command not in API's supported list | Run `list_commands` to see available commands |
| `PSM ... is not deployed in vregion` | The PSM has no Redis deployment in the requested VRegion (ByteHeart deploy_info authoritative) | Check the `available vregions` list in the error message, or use `search_service` to inspect the PSM |
| `ByteHeart.GetDeployInfo returned no deployments for PSM` | PSM not recognized by ByteHeart global center | Double-check the PSM spelling; use `search_service` to find the correct PSM |
| `invalid vregion` | Unknown VRegion | Check supported VRegion list above |
| `authentication failed` | JWT token issue | Check login status (`gdpa-cli login`) |
| `EU VRegion requires non-restricted employee` | Restricted employee accessing EU gateway | Contact admin for GCP access |
| `Redis error (code=403)` | Permission denied | Apply for `redis.resource.update` permission on the cluster via IAM |

## Notes

- **Read-only**: Only read commands supported by the ByteCloud API are available
- **Auto-resolution**: The agent automatically resolves `service_name` to a cluster -- no need to look up cluster IDs manually
- **Timeout**: Large queries may timeout; keep queries targeted with specific keys
