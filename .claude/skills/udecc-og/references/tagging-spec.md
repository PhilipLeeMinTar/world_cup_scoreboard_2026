# UDECC OG 字段打标完整规范

适用范围：`create_web_endpoint`（OpenHTTPSchema）、`create_web_endpoint` 的
`common_object`、以及作为 server-side 校验参考。

## OpenJsonField 五要素

每条字段（无论在 query / path / cookie / header / body / common_object）都用同一个
`OpenJsonField` 表达：

```thrift
struct OpenJsonField {
  1: string type,                            // 必填
  2: string description,                     // 必填
  3: string tx_catalog_id,                   // primitive 必填，object/array/map 可省
  4: string common_object_ref,               // 引用 common_object 时填，与 tx_catalog_id 二选一
  5: string special_attribute,               // 可选，需 endpoint.has_special_tagging=true
  6: map<string, OpenJsonField> properties,  // type=object 时填
  7: OpenJsonField mapKey,                   // type=map 时填
  8: OpenJsonField mapValue,                 // type=map 时填
  9: OpenJsonField items,                    // type=array 时填
}
```

### 1. `type` 字段允许值（按 scope）

| scope | 允许的 type |
|---|---|
| `query_params` | string / integer / boolean |
| `path_params` | string / integer |
| `cookies` | string / integer / boolean |
| `request.headers` / `response.headers` | string / integer / boolean |
| `request.body` / `response.body` | string / integer / boolean / object / array / map |
| `common_object` 顶层 | object（必带 properties，不能用 common_object_ref） |

### 2. `description` 写作规则

- 必填，全 ASCII（建议英文）
- 写"字段是什么"，不要写"为什么互通"
- 不要把字段名抄一遍当 description（如 `user_id` → "user_id"），审核会被打回
- 嵌套字段也要逐层写 description（包括 object / array / map 节点本身）

### 3. `tx_catalog_id` 来源

- Texas Data Catalog 叶子代码，形如 `"1.5.1"` / `"6.1"`
- 平台浏览：<https://decc.tiktok-row.net/category>
- 名字 → code 查询：`gdpa-cli run udecc-og --input '{"action":"fetch_meta","query":"<keyword>"}'`
- **primitive 字段必填**（string / integer / boolean）
- **object / array / map 容器节点不需要**（由内部叶子各自填）
- **使用 `common_object_ref` 时不需要**（由 common_object 内部叶子填）

### 4. `common_object_ref`

- 引用同 endpoint 下 `common_object` 的某个 key
- 引用方写法：`{"type": "object", "description": "...", "common_object_ref": "<key>"}`
- 不能再带 `properties` / `tx_catalog_id`
- 适用于多个 endpoint 复用同一份结构（用户信息、地址、设备指纹等）

### 5. `special_attribute` 矩阵

设置 `has_special_tagging=true` 后，`special_attribute` 才生效。
**写在不允许的位置 → server 报错**。本 skill 在 preview 阶段会列出 `invalid_special_attr`。

| 字段所在位置 | 允许的 special_attribute |
|---|---|
| `path_params` | DSL / TCC |
| `cookies` | DSL / TCC |
| `request.headers` | DSL / TCC |
| `response.headers` | DSL / TCC |
| `common_object` 内任意叶子 | DSL / TCC |
| `query_params` | DSL / TCC / METRIC_TAG |
| `request.body` | DSL / TCC / METRIC_TAG |
| `response.body` | DSL / TCC / ARGOS_LOG / LOG_MESSAGE_CONTENT |

## 5 种字段类型示例

### Primitive（string / integer / boolean）

```json
{
  "type": "string",
  "description": "username",
  "tx_catalog_id": "1.1"
}
```

### Object（带 properties）

```json
{
  "type": "object",
  "description": "user info",
  "properties": {
    "id": {"type": "string", "description": "user id", "tx_catalog_id": "1.2"}
  }
}
```

### Object（通过 common_object_ref 复用）

```json
{
  "type": "object",
  "description": "user ref",
  "common_object_ref": "UserMeta"
}
```

> 注意：`common_object_ref` 必须存在于同 endpoint 的 `common_object` map 里。

### Array

```json
{
  "type": "array",
  "description": "tags",
  "items": {
    "type": "string",
    "description": "tag",
    "tx_catalog_id": "2.1"
  }
}
```

### Map

```json
{
  "type": "map",
  "description": "user labels",
  "mapKey":   {"type": "string",  "description": "key",   "tx_catalog_id": "2.2"},
  "mapValue": {"type": "integer", "description": "value", "tx_catalog_id": "2.3"}
}
```

## OpenHTTPSchema 总体形态（create_web_endpoint）

```json
{
  "query_params": { "<param-name>": <OpenJsonField>, ... },
  "path_params":  { "<param-name>": <OpenJsonField>, ... },
  "cookies":      { "<cookie-name>": <OpenJsonField>, ... },
  "request_schema": {
    "headers": { "<header-name>": <OpenJsonField>, ... },
    "body":    { "<field-name>":  <OpenJsonField>, ... }
  },
  "response_schema": {
    "<status-code>": {
      "headers": { "<header-name>": <OpenJsonField>, ... },
      "body":    { "<field-name>":  <OpenJsonField>, ... }
    }
  }
}
```

`response_schema` 的 key 是字符串状态码（"200" / "400" / ...），可同时配置多个。

## 端点级（endpoint-level）参数

| 参数 | 必填 | 备注 |
|---|---|---|
| `psm` | ✅ | 后端服务标识 |
| `region` / `gateway` | ✅ | 见兼容矩阵 |
| `http_path` / `http_method` | ✅ | path 中的占位符要在 `path_params` 出现 |
| `description` | ✅ | endpoint 用途简述 |
| `has_special_tagging` | ✅ | 决定 `special_attribute` 是否生效 |
| `endpoint_audience` | EU AG 必填 | TT-4D / TT-User / TT-4B / TT-Family，必须在 entity audiences 列表内 |
| `endpoint_tx_catalog_id` | EU AG 必填 | 端点级别 catalog 叶子 code |
| `operator` | ✅ | 提单人 username |
| `common_object` | ❌ | 提供后才能用 `common_object_ref` |

## Preview `schema_summary` 字段含义

`create_web_endpoint` preview 返回的 `schema_summary` 由本 skill 在客户端计算：

| 字段 | 含义 | 期望值 |
|---|---|---|
| `leaf_count` | 总叶子字段数 | 与人工预期匹配 |
| `missing_description` | 缺 description 的叶子路径列表 | `[]` |
| `missing_tx_catalog_id` | 缺 tx_catalog_id 且未引用 common_object 的叶子 | `[]` |
| `invalid_special_attr` | special_attribute 写错位置的字段 | `[]` |
| `used_special_attribute` | 是否真的用上了 special_attribute | 与 `has_special_tagging` 一致 |

> 三个 `*_*` 数组任一非空 → 不要让用户 confirmed，先回去补字段。

## 常见 reviewer 拒绝原因

| 拒绝原因 | 修复方式 |
|---|---|
| Field description lacks detail | 把字段语义写清楚，不要 reuse field name |
| Missing tx_catalog_id on leaf | `fetch_meta` 找最贴近的 catalog code |
| special_attribute disabled | `has_special_tagging` 没开 |
| Invalid special_attribute position | 见上面位置矩阵，挪到允许的 scope |
| Endpoint description too generic | endpoint-level description 也要交代用途 |
| Missing endpoint_audience (EU AG) | EU AG 必填 |
| Missing endpoint_tx_catalog_id (EU AG) | EU AG 必填 |

> Submit 前可以再调一次 `fetch_meta include=rejection_templates query=<关键字>`，
> 看一眼当前模板库里相关的拒绝模板，确认字段不会触发。
