# DES 字段打标规范（Field Tagging Spec）

来源：内部《DES 字段标注说明 / DES Annotation Checklist》+ 真实打标审核反馈沉淀。

读这一篇就够：把 `tag_fields` 之前不放心的"哪些字段要打、写什么内容、信息从哪来"
一次性讲清楚。本规范的核心立场是 **IDL-driven**：能从 IDL 注解读出来的，就**绝不要**
靠经验或感觉填。

---

## 0. 术语速查

| 名称 | json_schema 字段 | 数据来源（IDL 注解） |
|---|---|---|
| Sync | `node.des.sync` | `(rule.sync = "YES")`，默认 `YES` |
| Texas Data Catalog | `node.des.tag` | `compliance.message.field_default.texas` 或字段级 `compliance.field.texas` |
| TikTok Data Catalog | `node.des.entity` | `compliance.message.field_default.tiktok` 或字段级 `compliance.field.tiktok` |
| Reason | `node.des.reason` | IDL 上的 `@sync_reason: ...` / `(rule.sync_reason = "...")` 或顶层注释 |
| Description | `node.description`（**field 顶层，不是 des 下**） | IDL 字段紧贴的 `// 英文注释` 或 `(field.desc = "...")` |
| Catalog Type | `data_id` 维度的"通道类型" | 由 channel + data_rule 确定，不在 schema 里 |

---

## 1. 标注 5 项（写到 json_schema 哪里）

每个**叶子字段**（不是 root / `_request` / `_response` 这类 wrapper）需要齐 5 项：

| UI 名称 | 写入位置 | 示例 | 说明 |
|---|---|---|---|
| **Sync** | `node.des.sync` | `"YES"` / `"NO"` | 是否跨 vgeo 同步 |
| **Texas Data Catalog** | `node.des.tag` | `"1.1"` | Texas/Clover 数据类别（单选码点） |
| **TikTok Data Catalog** | `node.des.entity` | `"1.2.2"` | 业务自定义三级标签（单选码点） |
| **Reason** | `node.des.reason` | `"Required for cross-region item lookup..."` | **互通原因**（为什么这条数据需要跨 vgeo） |
| **Description** | `node.description`（**field 顶层，与 `des` 同级**） | `"User-generated video unique identifier"` | **字段语义**（这个字段是什么） |

> ⚠️ **位置坑（最常见）**：`description` 必须在 field 节点顶层，**不是** `des.description`。
> DECC submit 时校验 `node.description`；只放在 `des.description` 仍会报
> `description is empty in _request.properties.<field>`。

> ⚠️ **语义坑**：`description` ≠ `reason`：
> - `description`：字段是什么 — `"item_id is the user-generated video unique identifier"`
> - `reason`：为什么互通 — `"Required for cross-region item lookup in TT_TTP↔EU mesh"`
>
> 不要把审批人、approval、申请单号塞 `description`，那种话属于 `reason`。

> 关键：DECC submit 时校验 **`_request` 端**也要有 vgeo annotation，所以 `tag_fields`
> 默认 5 项**同时应用 request + response 两侧**，没有 request/response 之分。

---

## 2. 权威来源表（IDL → json_schema 的映射）

**所有字段的 5 项标注按三档优先级取值，越靠左越优先**：

| 标注项 | ① IDL 注解（首选） | ② IDL 设计背景 / 仓库上下文（兜底） | ③ 启发式推断（最后兜底） | ❌ 严禁来源 |
|---|---|---|---|---|
| `description` | 字段紧贴的 `// 英文注释` 或 `(field.desc = "...")` | struct 顶部 `// @doc` / 设计文档；调用方代码 `grep` 字段名的 setter/getter；相邻已注解字段的语义类比；PR/MR 描述里对该字段的说明 | 字段名的合理英文翻译（`item_id` → `"video unique identifier"`） | 凭"应该是什么意思"瞎猜；中文；纯字段名复读 |
| `tag` (Texas) | 字段级 `compliance.field.texas` → struct 级 `compliance.message.field_default.texas` | 同 struct 内已有注解字段类比；按字段实际业务用途用 `fetch_meta` 查 catalog name 对应的 code | `fetch_meta` 查 `texas_catalog`，按字段名/类型最贴近的 catalog name 取 code | 全局默认；猜；填顶层兜底值 |
| `entity` (TikTok) | 字段级 `compliance.field.tiktok` → struct 级 `compliance.message.field_default.tiktok` | 同 channel 同业务方向已通过的 data version 复用；scenario 默认表 | `fetch_meta` 查 `tiktok_catalog`，按字段语义对应 | 同上 |
| `reason` | IDL 顶层注释 / method 注释里的 `@sync_reason: ...` | method 在仓库 README / commit message / 调用链里的业务用途，写成"X 服务在 A，需要 B 的 Y 数据用于 Z" | 同 channel 内其他已通过字段的 reason 类比改写 | 套话："required for cross-region sync"；引用 approval ID |
| `sync` | `(rule.sync = "YES"/"NO")` | 默认 `YES` | — | — |

**信息流的标准动作**：

```text
1. parse_idl                       → 拿到原始 json_schema（不带 5 项标注）
2. 阅读 IDL 注解                   → 提炼每个字段的真实 description / catalog / reason
   ├─ 注解齐全           → 直接用
   ├─ 注解缺失（首选）   → 回去 patch IDL，再 parse_idl
   └─ 注解缺失（次选）   → 看 IDL 设计背景 + 仓库上下文推断，把依据写进 explanation
3. fetch_meta catalog_type=…       → 把 catalog name → code 翻译过来
4. tag_fields field_overrides      → 路径级精准下发 5 项
5. submit_data_version preview     → 自审 + 二阶段确认
```

> **走 ② 第二档时的纪律**：必须能给出 **可验证的引用**（文件路径 + 行号、文档章节、PR
> 链接、相邻字段名），并把它写进 `update_data_version` 的 `explanation`。**第二档不是
> "自由发挥"的开闸**——审核员看到 description/catalog 与字段语义对不上、又没有依据，
> 会直接拒。如果第二档的依据都凑不出来，就回去补 IDL。

---

## 3. Default Data 5 项

普通数据（Default Data）必须齐：

- **Description**：字段语义 + 使用场景
- **Texas Data Catalog**：Texas 数据类别
- **TikTok Data Catalog**：业务自定义三级标签
- **Exemption Fields**：豁免字段原因（**一般不填**，由 IDL `exemption` 注解自动占位）
- **Reason**：为什么需要跨 vgeo 互通

---

## 4. Non-US User Data 额外 2 项

非美国用户数据（Non-US User Data）额外补：

- **Non-US User Data Proof Field**：YES/NO，该字段能否证明记录为非美国用户
- **Entity Type**：何种用户标识（`user_id` / `device_id` / ...）

`parse_idl` 在识别到 `non_us_user_data` 类的 catalog 时，会自动占位 `non_us_user_data_proof_field`
等字段，**不要去 override**，它们已经带 tag，会被跳过。

---

## 5. `description` 写作硬规则

1. ❌ **不能用中文**，避免 `China` / `Chinese` 字眼（防止误判数据回传中国机房）
2. ❌ **不要简单复制字段名**（`item_id` → `"item id"` 是 ❌）
3. ✅ **解释字段业务含义**（`item_id` → `"User-generated video unique identifier"`）
4. ✅ **名称易误解的字段必须详细解释**：
   - `audience id`：是直播嘉宾，还是广告定向人群包？
   - `age`：用户真实年龄段，还是定向年龄区间？
5. ✅ **聚合字段**（如 `detection_uv`）必须解释计算口径
6. ✅ **枚举字段** description 里必须列出值的含义
   （`"BYTE enum: 0=public, 1=private, 2=friends_only"`）

---

## 6. 容器/嵌套类型坑（map / list / nested struct）

> ⚠️ **map 的 value struct 不会继承父 struct 的 catalog**。
> ⚠️ **list 的 element struct 不会继承父 struct 的 catalog**。

如果某字段是 `map<string, ValueStruct>` 或 `list<ValueStruct>`，
**就算 ValueStruct 自己在 IDL 里有 `compliance.message.field_default.texas`**，
`tag_fields` 也只会把 catalog **应用到那一层 map/list 节点**，
里面叶子字段的 `tag` 仍然是空的，会 fallback 到顶层全局 `catalog`。

这是审核被拒的高频原因之一。**正确做法**：用 `field_overrides` 显式写每一个 map/list value 下的叶子字段。

### 6.1 路径写法

| 容器形态 | 路径 |
|---|---|
| 普通 struct 字段 | `_request.user_info.user_id` |
| 数组元素 | `_response.items[].name` |
| 数组里的嵌套 struct | `_response.items[].author.user_id` |
| map value | `_response.tags{*}.value` |
| map value 是 struct | `_response.buyer_info{*}.user_id` |
| map of list of struct | `_response.zone_users{*}.users[].user_id` |

`{*}` 表示"任意 key"，`[]` 表示"任意元素"。

### 6.2 示例

IDL：

```protobuf
message BuyerInfo {
  option (compliance.message.field_default.texas) = "1.5.1"; // Account Basic Info
  string user_id    = 1; // Buyer's TikTok user id
  int64  created_at = 2; // Buyer account creation timestamp (ms)
  string country    = 3; // Buyer registered country (ISO-2)
}
message Resp {
  map<string, BuyerInfo> buyer_info = 10; // key = buyer's TikTok handle
}
```

正确的 `field_overrides`：

```jsonc
"field_overrides": {
  "_response.buyer_info":              {"description": "Map of buyer profiles keyed by TikTok handle"},
  "_response.buyer_info{*}.user_id":   {"description": "Buyer TikTok user id",                 "catalog": "1.5.1"},
  "_response.buyer_info{*}.created_at":{"description": "Buyer account creation timestamp (ms)","catalog": "1.5.1"},
  "_response.buyer_info{*}.country":   {"description": "Buyer registered country (ISO-2)",     "catalog": "1.5.1"}
}
```

错误示范（线上被拒过）：

```jsonc
"catalog": "1.1",   // 顶层全局
"field_overrides": {
  "_response.buyer_info": {"catalog": "1.5.1"}   // 只标了 map 节点，没下沉
}
// 结果：buyer_info{*}.user_id 等三个叶子的 tag 都被填成 "1.1"，被审核打回
```

---

## 7. 默认跳过的"豁免字段"（非必要不要 override）

`tag_fields` 已经内建以下跳过规则，正常情况下别去碰：

- **顶层 root / `_request` / `_response`** wrapper 节点
- **base 类**：`requestBase` / `responseBase` 及其子字段，已自带 catalog（如 `"6.1"`）
- **自动占位字段**：`tpg_account_info_tag` / `ciphered_tag` /
  `non_us_user_data_proof_field` 等 `parse_idl` 生成的例外字段（已带 `tag`，会被跳过）

如果对某个豁免字段强行 override，会报 "field already tagged" 类的警告。

---

## 8. upstream_version 继承坑

`create_data_version` 默认会 `upstream_version=1`，**继承上一版的全部 tag**。
对继承来的版本：

- 全局参数（顶层 `catalog` / `entity` / `description` / `reason`）**只对空字段生效**
- 旧字段已经有 tag 的，**纹丝不动**

修正打标必须用 `field_overrides` 逐路径写。否则你看到的现象是：
"我明明把全局 catalog 改成 1.5.1 了，preview diff 里还是 1.1"。

---

## 9. 自审与常见拒因（rejection templates）

DECC 审核会用一组固定模板回复。`fetch_meta include=rejection_templates` 会拉到这些
模板。**submit 之前自审，把这些坑都过一遍**：

| 模板关键词 | 实际含义 | 怎么避开 |
|---|---|---|
| `description is empty in _request.properties.<field>` | description 没写到 field 顶层 | `field_overrides[<path>].description` 一定要写在 `_request` 那侧也覆盖（`tag_fields` 默认会两侧应用，但你 override 了一侧就只会改一侧） |
| `description is too short / generic` | 比如只写 "user id" | 加上业务上下文 |
| `description in Chinese / mentions China` | 中文或 China 字样 | 改成纯英文，国家名用 ISO-2 缩写 |
| `texas catalog mismatch with field semantic` | catalog 选错 | `fetch_meta query=...` 重新对照 |
| `reason is template / boilerplate` | reason 套话 | 写明跨 vgeo 的具体业务流程 |
| `<field> not tagged` | 叶子字段漏标 | 检查 map/list 嵌套是否漏下沉 |

---

## 10. 审批 / 风险

- 审批流程长（**EU ≥ 2 周**），打标准确性直接影响过审速度
- 审批通过后**不会自动生效**，需要手动 apply
- 避免：
  - 复杂结构体打包成 json 字符串而**未注册子字段**
  - 二进制/加密字段未主动申报
  - 把 IDL 加了新字段，但 data_version 没重建 → 漏标
  - map/list 嵌套结构体只标外层，漏标内部叶子（见 §6）

---

## 11. 通道选择（与字段打标弱相关，仅作背景）

- 用户数据**只能走 DES，不能走 OG**
- 结构化数据优先 **DES-MQ**（在线）/ **DES-HDFS**（离线），少用 DES-RPC
- **DES-TOS** 只传非结构化（视频/音频/图片），不传结构化数据

---

## 12. 推荐 `tag_fields` payload（IDL-driven 模板）

最常见的 `TT_TTP <> EU` 三方 mesh 打标，**完全由 IDL 注解驱动**：

```bash
gdpa-cli run decc-desrpc --input '{
  "action":  "tag_fields",
  "data_id": "<your-data-id>",
  "mode":    "all_yes",
  "reason":  "<copy from IDL @sync_reason on the method>",

  "field_overrides": {
    "_request.item_id": {
      "description": "User-generated video unique identifier",
      "catalog":     "1.1",
      "entity":      "1.2.2"
    },
    "_request.item_region": {
      "description": "Owning vgeo of the item, used for routing",
      "catalog":     "1.1"
    },
    "_response.item_id": {
      "description": "User-generated video unique identifier (echoed)",
      "catalog":     "1.1"
    },
    "_response.item.p1": {
      "description": "Item visibility flag (0=public, 1=private, 2=friends_only)",
      "catalog":     "1.1"
    }
  }
}'
```

写作约束：

- **不要**只用顶层全局 `catalog` / `description` 就 submit；那只是兜底
- 至少给每个 _request / _response 叶子字段在 `field_overrides` 里写一条独立 entry
- 优先级：`field_overrides[path].<key>` > 全局参数 > （description 缺省时镜像 reason）
- 容器（map/list）下的 value struct，**每一个叶子都要单独写** `field_overrides`
