# UDECC OG 报错速查

## 客户端校验（本 skill 在 validate_params 阶段直接拒绝）

| 报错前缀 | 触发条件 | 修复 |
|---|---|---|
| `action parameter is required` | 没传 `action` | 加上 `action` 字段 |
| `unknown action "<x>"` | `action` 不在 6 个候选里 | 改成 fetch_meta / read_entity_schema / create_web_service / create_log_service / create_web_endpoint / create_uf_endpoint |
| `<key> is required for <action>` | 必填字段缺失 | 补上对应参数；详见 SKILL.md Input Schema |
| `invalid region "<x>"` | `region` 不是 US/EU | UDECC OG 仅这两个 region |
| `invalid gateway "<x>" for region <r>` | gateway 与 region 不匹配 | US: OG / OG_VPC1_1 / SGW；EU: OG / AG |
| `invalid http_method "<x>"` | method 不在 8 个标准方法里 | 改成 GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/CONNECT |
| `invalid log_type "<x>"` | `create_log_service` 用了非法 log_type | sdk / framework / non-framework |
| `create_log_service only supports gateway=OG` | log service gateway != OG | 改成 OG |
| `http_schema must be an object` | `http_schema` 非 map | 传 JSON 对象 |
| `assurance_path must be an object with caller_vpc + callee_vpc` | UF 端点缺 assurance_path | 补 caller_vpc + callee_vpc |

## 认证类

| 报错 | 原因 | 修复 |
|---|---|---|
| `authentication failed: ...` | `region.GetJWT(vregion)` 失败 | 检查是否登录了 ByteCloud（gdpa-cli login）；vregion 写错也会导致拿不到 token |

## UDECC OpenAPI 服务端错误

服务端错误统一以 `UDECC OpenAPI error (status_code=<n>): <msg>` 形态返回。常见：

| msg 关键字 | 含义 | 修复 |
|---|---|---|
| `description is required` | endpoint 或字段 description 为空 | 补 description |
| `invalid tx_catalog_id: ...` | catalog code 不是叶子 | `fetch_meta` 重查；只能用叶子 tag（最深一层） |
| `endpoint_audience should not be provided because entity has no audiences defined` | 非 EU AG 传了 endpoint_audience，或 entity 没配 audiences | 删 `endpoint_audience` |
| `invalid endpoint_audience [X]. Allowed values: [...]` | audience 不在 entity 允许列表 | 用列表内的值 |
| `psm not found` | psm 不存在或没在 ByteTree 注册 | 先去 ByteTree 注册；`byte_tree_id` 也要正确 |
| `invalid special_attribute on <path>` | special_attribute 写在不允许的 scope | 见 tagging-spec.md 矩阵 |
| `has_special_tagging is false but special_attribute used` | 字段加了 special_attribute 却没开 endpoint flag | 把 `has_special_tagging` 改 true |
| `common_object_ref <X> not found` | `common_object_ref` 引用了不存在的 key | 在 `common_object` 里定义对应 key，或改名 |
| `endpoint already exists` | 同 psm + path + method 已注册 | 走 update 接口（本 skill v0.1 暂未支持 update，请用 UI） |

## HTTP 状态码

| HTTP code | 含义 |
|---|---|
| 200 | 业务层结果在 body `status_code` 字段，0=成功 |
| 401 / 403 | JWT 无效或没权限调 OpenAPI |
| 404 | base URL 写错或 path 不存在；检查 `base_url` |
| 5xx | UDECC 服务端故障；稍后重试或找 platform owner |

## 调试建议

1. 第一次 `create_*` 不要带 `confirmed`，认真审 preview。
2. 对 `create_web_endpoint` 务必检查 `schema_summary.missing_description` /
   `missing_tx_catalog_id` / `invalid_special_attr` 三个数组是否为空——
   非空就别 confirmed，先回去补 schema。
3. 不知道 `tx_catalog_id` 写啥时，永远先 `fetch_meta query=<关键字>`。
4. 不要直接传 confirmed=true 当快捷方式：审核失败 → 1-2 周窗口浪费。
