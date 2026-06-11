# Errors & Troubleshooting

按"看到的报错原文"反查。每条都给出根因 + 最短修复路径。

## 输入参数类

| 错误 | 根因 | 修复 |
|---|---|---|
| `action parameter is required` | 没传 `action` | 加 `action` 参数 |
| `channel parameter is required` | list_data 没传 channel | 加 `channel` 参数 |
| `name parameter is required` | create_channel 缺 name | 加 `name`（PSM 名/域名） |
| `description parameter is required` | create_channel 缺 description | 补上**英文** description |
| `owners parameter is required` | create_channel/create_data 缺 owners | 补 `owners: ["your.username"]` |
| `data_name parameter is required` | create_data 缺 data_name | 补 `data_name`（RPC 方法名/HTTP path） |
| `either data_id, or both channel and data_name are required` | create/update_data_version 入参不全 | 二选一：直接 `data_id` 或 `channel`+`data_name` |
| `version parameter is required for submit_data_version` | submit 缺 version | 加 `version`，或先 list_data_versions 看一下 |
| `scenario is required for submit_data_version` | 老版本 dv 没存 scenario，且没传入 | 显式传 `scenario` |
| `invalid description, Chinese characters are not allowed` | description 含中文 | 改成纯英文 |

## ASCII 校验类

| 错误 | 根因 | 修复 |
|---|---|---|
| `xxx contains non-ASCII character ...` | 该字段含中文/em-dash/全角符号 | 改 ASCII；常见替换 `—` → `--`，`<>` → `<->` |
| `description of contains Chinese character` | DECC 服务端返回，已被 skill 改写为友好提示 | 同上 |

## 通道 / 数据规则类

| 错误 | 根因 | 修复 |
|---|---|---|
| `channel not found: xxx` | 通道名拼错或区域错 | 检查通道名；试 `list_channels` 找接近的 |
| `data rule 'X' not found in channel 'Y'` | data_name 拼错 | 用 `list_data` 确认 |
| `data version not found` | data_id+version 组合错 | `list_data_versions` 复核 |
| `GetDataVersionDetail error` | API 错误 | 检查 data_id/version + 个人 JWT 有权限 |
| `LoadIDL error (... endpoint not found)` | BAM 上没有该 RPC 方法的 IDL 版本 | **先与业务方确认是否要在 BAM 新建 IDL 版本**，新建后再 load_idl |
| `LoadIDL returned empty IDL` | 同上 | 同上 |

## Submit / 打标类（最常见）

| 错误 | 根因 | 修复 |
|---|---|---|
| `description is empty in _request.properties.<field>` | json_schema 该字段缺**顶层** `description`（不是 `des.description`） | 跑 `tag_fields` 并提供 `description`（全局或 `field_overrides[<path>].description`），再 submit |
| `tag is empty in field _request.properties.<field>` / `annotation` 类 | 该字段没打 Texas/Clover catalog（`des.tag`）| 跑 `tag_fields` 时给全局 `catalog`；或对该字段 `field_overrides[<path>].catalog` |
| `empty properties` | 数据规则没有 IDL / json_schema | 按 [load_idl → parse_idl → tag_fields] 顺序补齐再 submit |
| `SubmitDataVersion error (code=...)` | 其它服务端校验失败 | 看完整 msg；常见是 IDL annotation 缺失 |

## Update 类

| 错误 | 根因 | 修复 |
|---|---|---|
| `version is not in draft` | 当前 latest 已 applied / cancelled / reviewing | 传 `auto_create_if_no_draft: true` 让 agent 自动新建草稿，或先 create_data_version |
| `UpdateDataVersion error (...) tag/annotation ...` | json_schema 内某字段已经有冲突标记 | 一般先 `tag_fields` 重写打标 |

## 反模式与隐藏陷阱（不会直接报错，但会被审核打回）

这些坑**不会以异常形式抛出**，而是 submit 之后审核侧返回 rejection，或者更糟——
你以为改了，其实根本没生效。**重点排查**。

| 反模式 | 现象 | 根因 | 正确姿势 |
|---|---|---|---|
| **凭感觉填 description** | 审核回 `description is generic / mismatch with field semantic` | 没读 IDL 注解，agent 按字段名硬猜 | **读 IDL `// 注释` / `(field.desc=...)` 抠原文**；不可靠时用 `fetch_meta` 验证 |
| **凭感觉填 catalog** | 审核回 `texas catalog mismatch with field semantic` | 全局 `catalog` 一把梭 | 字段级 `compliance.field.texas` → struct 级 `compliance.message.field_default.texas` → `fetch_meta query=...` |
| **upstream_version=1 后改全局参数** | preview diff 里 catalog 一动不动 | 全局参数**只覆盖空字段**，旧 tag 不动 | 改打标必须用 `field_overrides[<path>]` 逐路径写 |
| **map/list 容器只标外层** | 审核回 `<inner field> not tagged` 或 `tag mismatch` | `tag_fields` 不会把 ValueStruct 的 `compliance.message.field_default.texas` 自动下沉 | 用 `_response.foo{*}.bar` / `_response.foo[].bar` 路径，**逐叶子**写 `field_overrides` |
| **description 写在 `des.description`** | submit 报 `description is empty in _request.properties.<field>` | 位置错了 | 必须写在 field 节点顶层，与 `des` 同级（agent 内置已修正，自定义打标要小心） |
| **description 含中文 / China 字样** | 服务端校验拒绝 | 误判数据回流 CN | 改纯英文，国家用 ISO-2 缩写 |
| **reason 写成审批单号 / 套话** | 审核回 `reason is template / boilerplate` | 把 approval ID 塞进 reason | 写明跨 vgeo 的具体业务流程；不要复制审批人姓名 |
| **IDL 加新字段，data_version 没重建** | 新字段 schema 里没出现 / 没打标 | 老版本基于旧 IDL parse 出来的 | `load_idl` → `parse_idl` 重新生成 schema 后再 `tag_fields` |
| **base 类字段被 override** | 报 `field already tagged` | 给 `requestBase.*` / `responseBase.*` 强行写 override | 移除这些路径的 override，agent 默认会跳过 |

## 鉴权 / 网络

| 错误 | 根因 | 修复 |
|---|---|---|
| `authentication failed` | JWT 过期 / 没 login | `gdpa-cli login` 重新拿 token |
| `GetChannelList error` | 网络不通 / VRegion 不对 | 检查 `vregion` 参数（默认 `Singapore-Central`） |
| `service-account token unauthorized` | 内置 service-account token 失效（罕见） | 修改 `agent.go` 的 `serviceAccountBearerToken` 常量 |

## 一些约定

- 默认 VRegion = `Singapore-Central`（I18N）
- gateway 始终为 `2`（DES-RPC），调用方不需要传
- `query_caller_channel` 的 `callee` 可单独使用，不需要 `caller`
- Site 常见值：`ROW-TT`、`EU`、`US`、`BR`、`JP` 等
