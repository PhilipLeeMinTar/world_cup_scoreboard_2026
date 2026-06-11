---
name: udecc-og
description: Register and tag UDECC OG (Operations Gateway) HTTP services and endpoints across US/EU regions on the UDECC platform (decc.tiktok-row.net). Use whenever the user mentions UDECC, OG (Operations Gateway), AG (Authorization Gateway), SGW, Web Service registration, Log Service registration, HTTP endpoint registration, endpoint tagging (tx_catalog_id / special_attribute), Unified Schema endpoint (uf_endpoint), reverse-lookup an entity / schema (read_entity_schema), or wants to look up a Texas Catalog code (fetch_meta) for OG endpoint tagging. Also trigger when the user provides a UDECC URL, asks how to file a UDECC ticket, or wants to do field-level "打标" on an HTTP endpoint before audit submission. Two-phase confirmation guards every write action.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# UDECC OG Skill

操作 UDECC 平台（`decc.tiktok-row.net`）上 OG（Operations Gateway，HTTP 网关）相关的
**服务注册、Endpoint 注册和字段级打标**。与 [decc-desrpc](../decc-desrpc/SKILL.md)
（DES-RPC，RPC 网关）平行：

| 维度 | decc-desrpc | **udecc-og（本 skill）** |
|---|---|---|
| 协议层 | RPC（Thrift / PB） | HTTP（OG / AG / SGW） |
| 数据来源 | IDL → BAM → DECC | OpenAPI Schema（手动 / Swagger 转） |
| 区域 | i18n 全套 + boe | i18n 单线（US / EU），无 BOE |
| 字段 5 项 | sync / catalog(texas) / entity(tt) / reason / description | description / tx_catalog_id / special_attribute / common_object_ref |
| 工单 | DES-RPC Audit Ticket | OG/AG/SGW 工单 |
| 工单 SLA | 1–2 周以上 | 1–2 周以上 |

## When to Use

- 在 UDECC 平台注册 **Web Service**（Service-level 工单，按 region 出 1-2 张）
- 在 UDECC 平台注册 **Log Service**（仅 OG，sdk / framework / non-framework 三种）
- 注册 **Web Endpoint** 并完成字段打标（**核心场景**）
- 注册 **Unified Schema Endpoint**（`uf_endpoint`，from_swagger / from_grpc / from_thrift）
- 反查已注册的 entity + schema（`read_entity_schema`）
- 查 Texas Catalog 名字 → code（`fetch_meta`，与 decc-desrpc 共用同一个枚举库）
- 写操作（`create_*`）调用前都需向用户明确确认

## 核心概念

| 概念 | 说明 | 参数 |
|---|---|---|
| **PSM** | 后端服务标识 | `psm` |
| **Region** | 部署区域：`US` / `EU` | `region` |
| **Gateway** | HTTP 网关类型 | `gateway` |
| **Endpoint** | 一条具体 HTTP API（path + method） | `http_path` + `http_method` |
| **HTTP Schema** | OpenJsonField 树（query / path / cookie / header / body） | `http_schema` |
| **Common Object** | 复用结构（多 endpoint 引用） | `common_object` |
| **tx_catalog_id** | Texas Data Catalog 叶子 code（如 `1.5.1`） | 字段级 |
| **special_attribute** | DSL / TCC / METRIC_TAG / ARGOS_LOG / LOG_MESSAGE_CONTENT | 字段级，需 `has_special_tagging=true` |

### Region × Gateway 兼容矩阵

| region | 允许的 gateway | 备注 |
|---|---|---|
| US | OG, OG_VPC1_1, SGW | OG_VPC1_1 同 OG，建于 VPC1 |
| EU | OG, AG | AG 必须配 `endpoint_audience` + `endpoint_tx_catalog_id` |

### `special_attribute` 位置矩阵

| 字段所在位置 | 允许的 special_attribute |
|---|---|
| `path_params` / `cookies` / `request.headers` / `response.headers` / `common_object` | DSL / TCC |
| `query_params` / `request.body` | DSL / TCC / METRIC_TAG |
| `response.body` | DSL / TCC / ARGOS_LOG / LOG_MESSAGE_CONTENT |

> 设置 `has_special_tagging=false` 时所有 `special_attribute` 都被忽略。
> 写在不允许的位置 → server 拒收。本 skill 在 preview 阶段会标红 `invalid_special_attr` 路径。

## Command Format

```bash
gdpa-cli run udecc-og --input '<json>'
```

默认 base URL：`https://decc.tiktok-row.net`（办公网入口）。
默认 vregion：`Singapore-Central`（i18n 单线，没有 BOE 部署）。

## ⚠️ Pre-submit Review Protocol（务必遵守）

UDECC 工单同样 **1–2 周以上** 才会跑完，被打回必须重新建 + 重打 + 重提，代价很高。
所以 `create_*` 一律走两阶段确认：

1. **第一次调用**（不传 `confirmed` 或 `confirmed:false`）→ Skill 不会真的提交；
   会原样回 `preview` 块：
   - `body`：将要 POST 的完整请求体
   - `ticket_prediction`：会落到哪个区域的哪个 reviewer team
   - `schema_summary`（仅 endpoint）：叶子总数 + `missing_description` / `missing_tx_catalog_id` / `invalid_special_attr` 路径列表
   - `next_step`：直接可拷贝的 "加 confirmed:true" 命令
   - **`preview_md`**：已渲染好的 Markdown 文档（请求摘要 + 字段打标明细 + 工单预测）

2. **请直接展示 `preview.preview_md` 给用户**（它已经是排好版的 Markdown，不需要再总结、不需要复述其它字段），
   然后问一次："确认提交吗？需要 `yes / 提交 / submit` 之类明确同意。"

3. 用户**显式同意**后，再次以**完全相同的输入** + `"confirmed": true` 调用，
   只有这一次才会真正 POST 到 UDECC OpenAPI。

不要为了"省一步"自己默认 `confirmed: true`。代码层守卫和文档守卫共同保证：
**human-in-the-loop 提单不可绕过**。

## ⚠️ 调用前不要追问的事（默认行为已经替你处理）

为了减少不必要的追问，下列输入项 **agent 不应该主动问用户**：

| 项 | 默认行为 |
|---|---|
| `operator` | 缺省自动取当前 ByteCloud 用户（JWT → session → git；调试时可用 `GDPA_USER_NAME` 覆盖）。**只在用户主动指定 operator 时才填它。** |
| `has_special_tagging` | 缺省 `false`。**只在用户明确说要给字段加 `DSL` / `TCC` / `METRIC_TAG` / `ARGOS_LOG` / `LOG_MESSAGE_CONTENT` 时才设 true。** |
| 是否有 path 参数 | 看 `http_path` 中是否含 `{xxx}` 占位即可，**不必再问用户**。如果有，把对应字段写到 `http_schema.path_params`。 |
| `tx_catalog_id` 分配是否合理 | preview 已经把每个叶子字段的分配清单展示给用户了，**不需要再单独追问**。 |
| `http_schema` 来源 | 缺省时（见下条）skill 会返回 `schema_required` preview 直接告诉你怎么从 `bam-api` 拉，**不需要先和用户确认 "schema 在哪里"**。 |

## ⚙️ http_schema 缺省时的默认链路

`create_web_endpoint` 时如果用户没提供 `http_schema`，skill 会返回 `preview.status = "schema_required"`，
里面 `suggested_skill_call` 直接给出可执行的 `bam-api` 调用：

```bash
gdpa-cli run bam-api --input '{"action":"get_api_definition_info_through_path","psm":"<psm>","path":"<http_path>","method":"<METHOD>"}'
```

agent 看到这个 preview 后应当：

1. 先调上面的 `bam-api`，拿到 BAM 上的接口定义；
2. 把 BAM 的请求/响应字段翻译成 UDECC 的 `OpenHTTPSchema`（query_params / path_params / cookies /
   request_schema / response_schema），叶子字段补 `description` + `tx_catalog_id`；
3. 重新调用 `create_web_endpoint`（带 `http_schema`），进入正常 preview → confirmed 流程。

只有在 `bam-api` 也找不到这个接口（比如尚未在 BAM 注册）时，再回头让用户手写或转换 swagger。

## ⚠️ 打标硬规则（务必遵守）

每个**叶子字段**（primitive）必须同时具备：

1. `description`：英文，说明字段语义（不是"为什么互通"）
2. `tx_catalog_id`：Texas Catalog 叶子 code，如 `1.5.1`、`6.1`；用 `fetch_meta` 查名字 → code

> 对于通过 `common_object_ref` 引用的字段，可省略 `tx_catalog_id`（由 common_object 内部约束）。

非叶子字段（`object` / `array` / `map`）只需 `type` + `description`，由 `properties` /
`items` / `mapKey,mapValue` 递归到叶子。

`special_attribute` 是可选项：如果字段需要 DSL / TCC / METRIC_TAG / ARGOS_LOG /
LOG_MESSAGE_CONTENT 标记，**先把端点的 `has_special_tagging` 设为 true**，再在字段上加。
不设 true 的话所有 `special_attribute` 都会被服务端静默忽略。

完整规范（5 种字段类型示例、`special_attribute` 详细矩阵、常见拒绝原因）见
**[references/tagging-spec.md](references/tagging-spec.md)**。

## Actions

### fetch_meta — 查 Texas Catalog 名字 → code

UDECC 字段打标依赖 Texas Catalog（`tx_catalog_id`）。本 action 复用 DECC Platform
的 `GetMeta`（同一份 catalog 数据源），返回扁平化后的叶子列表。

```bash
# 按业务名查 code（最常用）
gdpa-cli run udecc-og --input '{"action": "fetch_meta", "query": "engineering operational"}'
# → [{"tag":"6.1","name":"Engineering Operational Data","path":"Engineering Data > ..."}]

# 拉全表（输出会比较大）
gdpa-cli run udecc-og --input '{"action": "fetch_meta"}'

# 跳过 reviewer 拒绝模板，只看 catalog
gdpa-cli run udecc-og --input '{"action": "fetch_meta", "include": "catalogs_only"}'
```

参数：
- `query`：substring 过滤（case-insensitive，匹配 name + tag + path + description）
- `include`：`rejection_templates`（默认） / `catalogs_only` / `all`

### read_entity_schema — 反查已注册的 entity + schema

老接口，按 `entity_id` + `entity_version` + `entity_region` 查回完整的 entity
和 schema 配置，可选带上 `schema_id` 收敛到指定 schema。

```bash
gdpa-cli run udecc-og --input '{
  "action": "read_entity_schema",
  "entity_id": "<entity-id>",
  "entity_version": 1,
  "entity_region": "US"
}'

# 收敛到指定 schema 版本
gdpa-cli run udecc-og --input '{
  "action": "read_entity_schema",
  "entity_id": "<entity-id>",
  "entity_version": 1,
  "entity_region": "US",
  "schema_id": "<schema-id>",
  "schema_version": 2
}'
```

### create_web_service ⚠️ 写 + 两阶段确认

注册一个 PSM 在某个 region/gateway 下的 Web Service。**确认前先和用户对齐**
`region` / `gateway` / `owners` / `application_names` / `audiences`。
`operator` 不传时自动取当前用户。

```bash
# 第一次：返回 preview（不提交）
gdpa-cli run udecc-og --input '{
  "action": "create_web_service",
  "byte_tree_id": 12345,
  "psm": "tiktok.demo.svc",
  "region": "US",
  "gateway": "OG",
  "description": "Demo service",
  "owners": ["alice", "bob"],
  "application_names": ["DemoApp"]
}'

# 用户审阅 preview.preview_md 后，加 confirmed:true 真提单
gdpa-cli run udecc-og --input '{
  "action": "create_web_service",
  "byte_tree_id": 12345,
  "psm": "tiktok.demo.svc",
  "region": "US",
  "gateway": "OG",
  "description": "Demo service",
  "owners": ["alice", "bob"],
  "application_names": ["DemoApp"],
  "confirmed": true
}'
```

EU AG 还要传 `audiences`（数组，候选 `TT-4D` / `TT-User` / `TT-4B` / `TT-Family`）。

### create_log_service ⚠️ 写 + 两阶段确认 — 仅 OG

注册 Log Service。`log_type` 必须为 `sdk` / `framework` / `non-framework` 之一，
`gateway` 必须为 `OG`。`log_service_info` 是一个 object（具体字段以平台 UI 为准）。

```bash
gdpa-cli run udecc-og --input '{
  "action": "create_log_service",
  "log_type": "sdk",
  "region": "US",
  "gateway": "OG",
  "description": "MyApp client log",
  "owners": ["alice"],
  "log_service_info": { ... }
}'
```

> `operator` 不传时取当前 ByteCloud 用户。

### create_web_endpoint ⚠️ 写 + 两阶段确认 — **核心场景**

注册一条 HTTP endpoint 并附带字段打标。**preview 阶段会做 schema audit**，列出
缺 description / 缺 tx_catalog_id / special_attribute 写错位置的所有字段路径。
直接展示 `preview.preview_md` 给用户。

> `operator` 缺省取当前用户；`has_special_tagging` 缺省 `false`，**只在用户要打 DSL/TCC/METRIC_TAG/ARGOS_LOG/LOG_MESSAGE_CONTENT 时才设 true**。
> `http_schema` 缺省时会返回 `preview.status="schema_required"`，里面 `suggested_skill_call` 会指引去 `bam-api` 拉接口定义（详见上文「http_schema 缺省时的默认链路」）。

```bash
gdpa-cli run udecc-og --input '{
  "action": "create_web_endpoint",
  "psm": "tiktok.demo.svc",
  "region": "EU",
  "gateway": "AG",
  "http_path": "/api/v1/demo",
  "http_method": "POST",
  "description": "Demo endpoint",
  "has_special_tagging": true,
  "endpoint_audience": "TT-User",
  "endpoint_tx_catalog_id": "1.2",
  "common_object": {
    "UserMeta": {
      "type": "object",
      "description": "user metadata",
      "properties": {
        "uid": {"type": "string", "description": "user id", "tx_catalog_id": "1.1"}
      }
    }
  },
  "http_schema": {
    "query_params": {
      "lang": {"type": "string", "description": "language code", "tx_catalog_id": "6.1"}
    },
    "request_schema": {
      "body": {
        "user": {"type": "object", "description": "user ref", "common_object_ref": "UserMeta"}
      }
    },
    "response_schema": {
      "200": {
        "body": {
          "ok": {"type": "boolean", "description": "success flag", "tx_catalog_id": "6.1"}
        }
      }
    }
  }
}'
```

EU AG 必填：`endpoint_audience` + `endpoint_tx_catalog_id`。
US OG / SGW 不要传 `endpoint_audience`（server 会报 "should not be provided"）。

### create_uf_endpoint ⚠️ 写 + 两阶段确认 — Unified Schema endpoint

支持 `from_swagger` / `from_grpc` / `from_thrift` 三种 stage 的统一 schema endpoint，
可带 `defs`（type 定义） / `dynamic_params`（动态参数）。

```bash
gdpa-cli run udecc-og --input '{
  "action": "create_uf_endpoint",
  "operator": "alice",
  "from_stage": "from_swagger",
  "id": "<uf-id>",
  "entity_id": "<entity-id>",
  "type": "<type>",
  "name": "DemoUFEndpoint",
  "http_method": "POST",
  "http_path": "/api/v1/uf/demo",
  "description": "Demo UF endpoint",
  "has_special_tagging": false,
  "owners": ["alice"],
  "assurance_path": {
    "caller_vpc": "Office_Net",
    "callee_vpc": "US_VPC1"
  },
  "http_schema": { ... full Unified Schema ... },
  "defs": { ... },
  "dynamic_params": [ ... ]
}'
```

> UF endpoint 的 `http_schema` 形态是平台的 Unified Schema（带 `defs` 和 `$ref`），
> 不是 `OpenHTTPSchema`，本 skill 暂不对它做 schema audit（依赖服务端校验）。

## Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["action"],
  "properties": {
    "action": {
      "type": "string",
      "enum": ["fetch_meta", "read_entity_schema", "create_web_service", "create_log_service", "create_web_endpoint", "create_uf_endpoint"]
    },

    "base_url": {"type": "string", "description": "Override UDECC base URL (default: https://decc.tiktok-row.net)"},
    "vregion":  {"type": "string", "default": "Singapore-Central", "description": "VRegion for JWT lookup. UDECC is i18n-line only."},

    "query":   {"type": "string", "description": "[fetch_meta] case-insensitive substring filter against name + code + path + description"},
    "include": {"type": "string", "enum": ["rejection_templates", "catalogs_only", "all"], "default": "rejection_templates", "description": "[fetch_meta] whether to include reviewer rejection templates"},

    "entity_id":      {"type": "string", "description": "[read_entity_schema, create_uf_endpoint] entity id"},
    "entity_version": {"type": "integer", "description": "[read_entity_schema] entity version"},
    "entity_region":  {"type": "string", "enum": ["US", "EU"], "description": "[read_entity_schema] entity region"},
    "schema_id":      {"type": "string", "description": "[read_entity_schema] optional schema id"},
    "schema_version": {"type": "integer", "description": "[read_entity_schema] optional schema version"},
    "assurance_path": {"type": "object", "description": "[read_entity_schema, create_uf_endpoint] {caller_vpc, callee_vpc}"},

    "byte_tree_id":      {"type": "integer", "description": "[create_web_service] ByteTree node id"},
    "psm":               {"type": "string",  "description": "[create_web_service, create_web_endpoint] PSM"},
    "region":            {"type": "string",  "enum": ["US", "EU"], "description": "[create_web_service, create_log_service, create_web_endpoint] region"},
    "gateway":           {"type": "string",  "description": "[create_web_service, create_log_service, create_web_endpoint] one of OG / OG_VPC1_1 / SGW (US) or OG / AG (EU). create_log_service must be OG"},
    "description":       {"type": "string",  "description": "[all create_*, read_entity_schema] short summary"},
    "operator":          {"type": "string",  "description": "[all create_*, OPTIONAL] username (without @bytedance.com). Defaults to the current ByteCloud user (resolved from JWT/session/git). Do NOT prompt the user for this."},
    "owners":            {"type": "array",   "items": {"type": "string"}, "description": "[create_web_service, create_log_service, create_uf_endpoint] owner usernames"},
    "application_names": {"type": "array",   "items": {"type": "string"}, "description": "[create_web_service] application names"},
    "audiences":         {"type": "array",   "items": {"type": "string"}, "description": "[create_web_service, EU AG only] one of TT-4D / TT-User / TT-4B / TT-Family"},

    "log_type":         {"type": "string", "enum": ["sdk", "framework", "non-framework"], "description": "[create_log_service]"},
    "log_service_info": {"type": "object", "description": "[create_log_service] log-type-specific info object"},

    "http_path":             {"type": "string",  "description": "[create_web_endpoint, create_uf_endpoint] HTTP path"},
    "http_method":           {"type": "string",  "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT"], "description": "[create_web_endpoint, create_uf_endpoint] HTTP method"},
    "has_special_tagging":   {"type": "boolean", "default": false, "description": "[create_web_endpoint, create_uf_endpoint, OPTIONAL] enable special_attribute on fields. Default false; ALL special_attribute values are ignored when false. Only set true when the user explicitly asks for DSL / TCC / METRIC_TAG / ARGOS_LOG / LOG_MESSAGE_CONTENT tagging."},
    "endpoint_audience":     {"type": "string",  "description": "[create_web_endpoint, EU AG only] TT-4D / TT-User / TT-4B / TT-Family"},
    "endpoint_tx_catalog_id":{"type": "string",  "description": "[create_web_endpoint, required for EU AG] endpoint-level Texas Catalog leaf code"},
    "http_schema":           {"type": "object",  "description": "[create_web_endpoint, OPTIONAL] OpenHTTPSchema (query_params/path_params/cookies/request_schema/response_schema). When omitted, the skill returns a `schema_required` preview that points the agent at `bam-api` to fetch the canonical schema first. [create_uf_endpoint, REQUIRED] Unified Schema (from_swagger/from_grpc/from_thrift)."},
    "common_object":         {"type": "object",  "description": "[create_web_endpoint] map<string, OpenJsonField> of reusable type definitions referenced via common_object_ref"},

    "from_stage":     {"type": "string", "enum": ["from_swagger", "from_grpc", "from_thrift"], "description": "[create_uf_endpoint]"},
    "id":             {"type": "string", "description": "[create_uf_endpoint] UF endpoint id (string)"},
    "type":           {"type": "string", "description": "[create_uf_endpoint] UF endpoint type"},
    "name":           {"type": "string", "description": "[create_uf_endpoint] UF endpoint name"},
    "audience":       {"type": "string", "description": "[create_uf_endpoint, optional]"},
    "tx_catalog_id":  {"type": "string", "description": "[create_uf_endpoint, optional] endpoint-level catalog leaf code"},
    "format_type":    {"type": "string", "description": "[create_uf_endpoint, optional]"},
    "defs":           {"type": "object", "description": "[create_uf_endpoint] type definitions referenced by $ref in http_schema"},
    "dynamic_params": {"type": "array",  "description": "[create_uf_endpoint] dynamic parameters list"},
    "diff_content":   {"type": "array",  "description": "[create_uf_endpoint, optional]"},

    "confirmed": {
      "type": "boolean",
      "default": false,
      "description": "Two-phase confirmation guard for create_*. First call without (or false) returns a `preview` block and does NOT submit. Re-issue the SAME input with `confirmed: true` to actually create the ticket."
    }
  }
}
```

## 进一步阅读

- 字段打标完整规范（OpenJsonField 5 项 / 5 种类型 / special_attribute 矩阵 / 拒绝原因）
  → **[references/tagging-spec.md](references/tagging-spec.md)**
- 各 action 的完整返回字段
  → **[references/output-schemas.md](references/output-schemas.md)**
- 报错速查与修复路径
  → **[references/errors.md](references/errors.md)**
- API Client 与 IDL（5 个 RPC、`json.RawMessage` 透传策略）
  → `pkg/devflow-api-clients/idl/protobuf/udecc_og/` + `pkg/devflow-api-clients/impl/udecc_og/`
