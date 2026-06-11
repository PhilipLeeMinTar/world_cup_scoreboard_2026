# TCC 配置变更工具

在 BITS 开发任务中管理 TCC 配置变更：查询可导入的配置列表、导入配置到开发任务、查看已导入的变更项。

> **前提**：已创建 TCC 类型的 BITS 开发任务（`project_type: "tcc"`）。

### 控制面与区域参考

实际可用控制面因 PSM 而异，可通过 `get_tcc_regions` 动态查询。

所有 `control_plane`、`source_control_plane`、`control_planes` 参数支持两种格式：
- **常量名**：`CONTROL_PLANE_CN`、`CONTROL_PLANE_I18N`
- **短别名**：`cn`、`i18n`、`eu-ttp`

| 常量名 | 别名 | TCC 区域 |
|--------|------|---------|
| `CONTROL_PLANE_CN` | `cn` | CN, China-East, China-North3, China-North5 |
| `CONTROL_PLANE_I18N` | `i18n` / `row` | Singapore-Central, US-East, US-West |
| `CONTROL_PLANE_EU_TTP` | `eu-ttp` | EU-TTP, EU-TTP2, US-EastRed |
| `CONTROL_PLANE_US_TTP` | `us-ttp` / `ttp` | US-TTP, US-TTP2 |
| `CONTROL_PLANE_BOE` | `boe` | China-BOE, US-BOE |
| `CONTROL_PLANE_I18N_BD` | `saas` / `i18n-bd` | Singapore-SaaS, US-EE, Asia-SouthEastBD |

---

## import_tcc_configs — 导入 TCC 配置到开发任务

将指定配置从多个控制面导入到 BITS 开发任务。系统自动完成权限检查、配置匹配、批量导入，并返回变更结果。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `import_tcc_configs` |
| `psm` | string | 是 | TCC 命名空间 PSM |
| `dev_task_id` | number | 是 | BITS 开发任务 ID |
| `conf_name` | string | 是 | 要导入的配置名称 |
| `control_planes` | string[] | 是 | 控制面列表（如 `["cn","i18n","boe"]`），见上方参考表 |
| `source_region` | string | 否 | 来源区域过滤（如 `US-East`、`Singapore-Central`、`CN`）。同一控制面下存在多个区域配置时，用此参数精确选取 |
| `source_dir` | string | 否 | 来源目录过滤（如 `/default`），用于在同区域多目录场景下消歧 |
| `import_draft` | bool | 否 | 是否导入草稿版本（最新未发布版本）。默认 `false` 导入线上版本；`true` 时导入 `latestVersion`（无草稿则退化为线上版本） |
| `space_id` | number | 否 | BITS 空间 ID，用于生成任务链接 |

> 版本语义：BITS 配置列表对每个 config 同时返回 `version`（线上）与 `latestVersion`（含草稿的最新版本）。`import_draft=false` 时 `baselineVersion=importVersion=version`；`import_draft=true` 时 `baselineVersion=version`、`importVersion=latestVersion`，与 BITS 页面"选版本→草稿"行为一致。

**示例（默认导入线上版本）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "import_tcc_configs",
  "psm": "ttarch.gdp.gdpa",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_planes": ["cn", "i18n", "boe"],
  "space_id": 94017024770
}'
```

**示例（导入草稿 + 指定来源区域）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "import_tcc_configs",
  "psm": "tiktok.feed.component",
  "dev_task_id": 2269474,
  "conf_name": "fcp_model_pred_white_list",
  "control_planes": ["i18n"],
  "source_region": "US-East",
  "import_draft": true
}'
```

**返回**：

```json
{
  "success": true,
  "action": "import_tcc_configs",
  "dev_task_id": 2272667,
  "psm": "ttarch.gdp.gdpa",
  "conf_name": "eval_base_key_config",
  "imported_count": 3,
  "total_change_items": 3,
  "link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2272667/tcc",
  "tcc_change_items": [...]
}
```

---

## list_tcc_configs — 查询可导入的配置列表

查询指定控制面下某 PSM 的 TCC 配置列表，用于确认配置名称、版本信息、是否存在未发布草稿。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `list_tcc_configs` |
| `psm` | string | 是 | TCC 命名空间 PSM |
| `control_plane` | string | 是 | 控制面（如 `"cn"`、`"CONTROL_PLANE_CN"`），见参考表 |
| `region` | string | 否 | 区域过滤（如 `US-East`、`Singapore-Central`），同 BITS 页面右上角的区域筛选 |
| `page_size` | number | 否 | 每页条数，默认 100 |
| `page_index` | number | 否 | 页码，默认 1 |

**示例（列出 `i18n` + `Singapore-Central` 下的配置）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "list_tcc_configs",
  "psm": "tiktok.feed.component",
  "control_plane": "i18n",
  "region": "Singapore-Central"
}'
```

> 返回结果里每条 config 都带 `has_unpublish_latest_version`，需要"只看有草稿的"时直接在客户端按该字段过滤即可。

**返回（重点字段）**：

```json
{
  "success": true,
  "action": "list_tcc_configs",
  "control_plane": 2,
  "region": "US-East",
  "total_count": 3,
  "draft_count": 1,
  "configs": [
    {
      "config_id": 123456,
      "conf_name": "fcp_model_pred_white_list",
      "version": "17",
      "latest_version": "18",
      "has_unpublish_latest_version": true,
      "region": "US-East",
      "dir": "/default"
    },
    {
      "config_id": 123457,
      "conf_name": "another_config",
      "version": "5",
      "latest_version": "5",
      "has_unpublish_latest_version": false,
      "region": "US-East",
      "dir": "/default"
    }
  ]
}
```

> **如何分辨是否有草稿**：每个 config 项都返回三元组 `version` / `latest_version` / `has_unpublish_latest_version`：
> - `has_unpublish_latest_version: true` ⇒ 存在未发布草稿，`version` 是当前线上发布版本，`latest_version` 是包含草稿在内的最新版本（一般 `latest_version > version`）
> - `has_unpublish_latest_version: false` ⇒ 无草稿，此时 `version == latest_version`
>
> 拿到 `conf_name` 后再调用 `import_tcc_configs` 时，传 `import_draft: true` 会把 `latest_version` 作为 `importVersion` 导入；不传或传 `false` 则导入 `version`（线上）。

---

## list_tcc_tags — 查询配置标签

查询指定控制面下 PSM 的 TCC 配置标签列表。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `list_tcc_tags` |
| `psm` | string | 是 | TCC 命名空间 PSM |
| `control_plane` | string | 是 | 控制面（如 `"cn"`），见参考表 |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "list_tcc_tags",
  "psm": "ttarch.gdp.gdpa",
  "control_plane": "cn"
}'
```

---

## get_tcc_regions — 查询 TCC 区域列表

查询开发任务中可用的 TCC 区域列表（按控制面分组）。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `get_tcc_regions` |
| `psm` | string | 是 | TCC 命名空间 PSM |
| `dev_task_id` | number | 是 | BITS 开发任务 ID |
| `control_planes` | string[] | 是 | 控制面列表（如 `["cn","i18n"]`），见参考表 |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_tcc_regions",
  "psm": "ttarch.gdp.gdpa",
  "dev_task_id": 2272667,
  "control_planes": ["cn", "i18n", "boe"]
}'
```

---

## list_tcc_change_items — 查询已导入的变更项

查询开发任务中已导入的 TCC 变更项列表，包含各区域的变更配置信息。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `list_tcc_change_items` |
| `dev_task_id` | number | 是 | BITS 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "list_tcc_change_items",
  "dev_task_id": 2272667
}'
```

---

## get_tcc_change_detail — 查询变更项详情

查询指定变更项的配置详情（配置 ID、描述、baseline 是否落后等）。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `get_tcc_change_detail` |
| `change_item_id` | string | 是 | 变更项 ID（从 `list_tcc_change_items` 获取） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_tcc_change_detail",
  "change_item_id": "1633284677236424"
}'
```

---

### 7. get_tcc_change_diff — 查询 TCC 配置变更 Diff

对比基线版本与草稿版本的配置内容差异。支持两种调用方式：
- **自动模式**：传入 `dev_task_id` + `conf_name`，自动从变更项列表中定位参数
- **手动模式**：直接传入 `change_item_id` + `source_config_id` + `config_id` + `storage_psm_version`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `get_tcc_change_diff` |
| `dev_task_id` | int64 | 自动模式必填 | 开发任务 ID |
| `conf_name` | string | 自动模式必填 | 配置名称（如 `common_config`） |
| `control_plane` | string | 否 | 自动模式下按控制面过滤（如 `"cn"`，见参考表），不传则匹配第一个 |
| `source_region` | string | 否 | 自动模式下按来源区域过滤（如 `CN`、`China-North3`、`Singapore-Central`），用于同控制面下多区域消歧 |
| `source_dir` | string | 否 | 自动模式下按来源目录过滤（如 `/default`），用于同区域下多目录消歧 |
| `change_item_id` | string | 手动模式必填 | 变更项 ID，标识某个区域下的一组配置变更，来自 `list_tcc_change_items` 返回的 `region_change_items[].change_item_id` |
| `source_config_id` | string | 手动模式必填 | 基线（线上）配置版本 ID，来自 `list_tcc_change_items` 返回的 `config_items[].source_config_id` |
| `config_id` | string | 手动模式必填 | 草稿（待发布）配置版本 ID，来自 `list_tcc_change_items` 返回的 `config_items[].config_id` |
| `storage_psm_version` | string | 手动模式必填 | PSM 级乐观锁版本号，来自 `list_tcc_change_items` 返回的 `storage_psm_version` |

**示例（自动模式 — 指定控制面）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_tcc_change_diff",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_plane": "boe"
}'
```

**示例（自动模式 — 不指定控制面，匹配第一个）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_tcc_change_diff",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config"
}'
```

**返回说明**：

返回 `from`（基线）和 `to`（草稿）两个版本的配置信息，包含：
- `content`：配置内容（JSON/YAML 等原始文本）
- `version`：版本号
- `region` / `region_name`：区域信息
- `data_type`：数据类型（json/yaml/text 等）
- `config_type`：配置类型（static 等）

---

### 8. discard_tcc_change — 放弃 TCC 配置变更

放弃指定配置的变更，将其从开发任务的变更列表中移除。支持两种调用方式：
- **自动模式**：传入 `dev_task_id` + `conf_name`（+ 可选 `control_plane`），自动定位变更项
- **手动模式**：直接传入 `change_item_id` + `config_id` + `storage_psm_version`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `discard_tcc_change` |
| `dev_task_id` | int64 | 自动模式必填 | 开发任务 ID |
| `conf_name` | string | 自动模式必填 | 配置名称（如 `common_config`） |
| `control_plane` | string | 否 | 自动模式下按控制面过滤（如 `"cn"`，见参考表），不传则匹配第一个 |
| `source_region` | string | 否 | 自动模式下按来源区域过滤（如 `CN`、`China-North3`、`Singapore-Central`） |
| `source_dir` | string | 否 | 自动模式下按来源目录过滤（如 `/default`） |
| `change_item_id` | string | 手动模式必填 | 变更项 ID，来自 `list_tcc_change_items` 返回的 `region_change_items[].change_item_id` |
| `config_id` | string | 手动模式必填 | 草稿配置版本 ID，来自 `list_tcc_change_items` 返回的 `config_items[].config_id` |
| `storage_psm_version` | string | 手动模式必填 | PSM 级乐观锁版本号，来自 `list_tcc_change_items` 返回的 `storage_psm_version` |

**示例（自动模式）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "discard_tcc_change",
  "dev_task_id": 2272667,
  "conf_name": "common_config",
  "control_plane": "cn"
}'
```

**返回说明**：

成功时返回 `success: true` 和 `message: "配置变更已放弃"`，该配置将从开发任务的变更列表中移除。

---

### 9. list_tcc_deploy_targets — 查询可选变更目标

查询指定变更项可设置的 BOE/PPE/Prod 部署目标区域列表，平铺展示所有可选区域并标注互斥状态。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `list_tcc_deploy_targets` |
| `dev_task_id` | int64 | 是 | 开发任务 ID |
| `conf_name` | string | 是 | 配置名称，用于定位变更项 |
| `control_plane` | string | 否 | 按控制面过滤（如 `"cn"`，见参考表），不传则匹配第一个 |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "list_tcc_deploy_targets",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_plane": "cn"
}'
```

**返回说明**：

- `available_targets.boe/ppe/prod`：每个环境的平铺区域列表，每项含 `region`、`control_plane`、`dir`、`occupied`（是否被其他变更项占用）、`occupied_by`（占用的 changeItemId）
- `current_targets`：当前变更项已设置的 BOE/PPE/Prod 目标区域名列表

---

### 10. set_tcc_deploy_target — 设置变更目标

为指定变更项设置 BOE/PPE/Prod 部署目标区域。设置前自动执行互斥校验，拒绝已被其他变更项占用的区域。

> **保留策略**：只有明确传入的环境列表会被更新。例如只传 `prod_targets` 时，已有的 `boe_targets` 和 `ppe_targets` 会被自动保留，不会被清空。如需清空某个环境的目标，显式传入空数组 `[]`。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `set_tcc_deploy_target` |
| `dev_task_id` | int64 | 自动模式必填 | 开发任务 ID |
| `conf_name` | string | 自动模式必填 | 配置名称，用于定位变更项 |
| `control_plane` | string | 否 | 按控制面过滤（如 `"cn"`，见参考表） |
| `source_region` | string | 否 | 按来源区域过滤（如 `CN`、`China-North3`） |
| `source_dir` | string | 否 | 按来源目录过滤（如 `/default`） |
| `boe_targets` | []string | 至少传一个 | BOE 目标区域名列表（如 `["China-BOE"]`），不传则保留现有值 |
| `ppe_targets` | []string | 至少传一个 | PPE 目标区域名列表（如 `["CN", "China-North3"]`），不传则保留现有值 |
| `prod_targets` | []string | 至少传一个 | 线上目标区域名列表（如 `["CN", "US-East"]`），不传则保留现有值 |
| `change_item_id` | string | 手动模式必填 | 变更项 ID |
| `storage_psm_version` | string | 手动模式必填 | PSM 级乐观锁版本号 |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "set_tcc_deploy_target",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_plane": "cn",
  "boe_targets": ["China-BOE"],
  "ppe_targets": ["CN", "China-North3", "China-North5"],
  "prod_targets": ["CN", "US-East"]
}'
```

**返回说明**：

成功时返回 `success: true` 和 `message: "变更目标已设置"`。若目标区域已被其他变更项占用，返回错误并标明冲突详情。

---

### 11. get_tcc_config_content — 读取配置内容

读取指定配置的当前草稿内容和在线版本，支持自动解析（dev_task_id + conf_name）或直传 config_id。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `get_tcc_config_content` |
| `config_id` | string | 直传模式必填 | TCC 配置 ID |
| `dev_task_id` | int64 | 自动模式必填 | 开发任务 ID |
| `conf_name` | string | 自动模式必填 | 配置名称 |
| `control_plane` | string | 否 | 按控制面过滤（如 `"cn"`，见参考表） |
| `source_region` | string | 否 | 按来源区域过滤（如 `CN`、`China-North3`、`Singapore-Central`） |
| `source_dir` | string | 否 | 按来源目录过滤（如 `/default`） |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_tcc_config_content",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_plane": "cn",
  "source_region": "China-North3"
}'
```

**返回说明**：

- `conf_name`、`region`、`description`：配置基本信息
- `latest_version.content`：当前草稿配置内容
- `latest_version.config_type`/`data_type`：配置类型（static/dynamic）和数据类型（json/text/...）
- `latest_version.version`：草稿版本号
- `online_version`（仅在线版本存在时返回）：线上配置内容和版本

---

### 12. edit_tcc_config — 编辑配置

修改已导入配置的内容和/或元数据。内部自动获取当前配置作为基线，仅覆盖用户指定的字段。

**可编辑字段**（至少传一项）：`content`、`description`、`note`、`tags`

**字段值语义**（三态）：

| 场景 | 行为 |
|------|------|
| 未传该字段 | 保留原值 |
| 传入空值（`""` / `[]`） | 清空该字段 |
| 传入有效值 | 更新为新值 |

> `withL4Data`、`enableEncryption`、`cdnSupported` 等开关型字段始终从当前配置继承，如需修改请在 BITS 平台操作。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `edit_tcc_config` |
| `dev_task_id` | int64 | 自动模式必填 | 开发任务 ID |
| `conf_name` | string | 自动模式必填 | 配置名称 |
| `control_plane` | string | 否 | 按控制面过滤（如 `"cn"`，见参考表） |
| `source_region` | string | 否 | 按来源区域过滤（如 `CN`、`China-North3`、`Singapore-Central`） |
| `source_dir` | string | 否 | 按来源目录过滤（如 `/default`） |
| `content` | string | 至少传一项 | 新的配置内容（完整替换），传 `""` 清空 |
| `description` | string | 至少传一项 | 配置描述，传 `""` 清空 |
| `note` | string | 至少传一项 | 变更备注，传 `""` 清空 |
| `tags` | []string | 至少传一项 | 配置标签，传 `[]` 清空，传 `["a","b"]` 设置 |
| `change_item_id` | string | 手动模式必填 | 变更项 ID |
| `config_id` | string | 手动模式必填 | 配置 ID |
| `storage_psm_version` | string | 手动模式必填 | PSM 级乐观锁版本号 |
| `psm` | string | 否 | TCC 命名空间 PSM（自动模式下自动获取） |

**示例**：

```bash
# 修改内容 + 备注
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "edit_tcc_config",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_plane": "cn",
  "content": "{\"KEY\": \"new_value\"}",
  "note": "update KEY value"
}'

# 清空标签
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "edit_tcc_config",
  "dev_task_id": 2272667,
  "conf_name": "eval_base_key_config",
  "control_plane": "cn",
  "tags": []
}'
```

**返回说明**：

成功时返回 `success: true` 和 `message: "配置已更新"`，以及 `content_updated`/`description_updated`/`tags_updated` 标记指示哪些字段被修改。

---

### 13. add_tcc_config — 新增配置项

在开发任务中创建全新的 TCC 配置（非导入已有配置）。内部自动解析目录 ID 和版本号。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `add_tcc_config` |
| `dev_task_id` | int64 | 是 | 开发任务 ID |
| `psm` | string | 是 | TCC 命名空间 PSM |
| `conf_name` | string | 是 | 配置名称 |
| `content` | string | 是 | 配置内容 |
| `source_control_plane` | string | 是 | 变更来源控制面（如 `"cn"`），见参考表 |
| `source_region` | string | 是 | 变更来源区域（如 `CN`、`China-North3`、`Singapore-Central`） |
| `description` | string | 否 | 配置描述，默认等于 `conf_name` |
| `data_type` | string | 否 | 数据类型：`json`（默认）、`yaml`、`string` |
| `config_type` | string | 否 | 配置类型：`static`（默认）、`downgrade` |
| `source_dir` | string | 否 | 来源目录（如 `/default`），默认自动匹配 |
| `tags` | []string | 否 | 配置标签 |
| `with_l4_data` | bool | 否 | 是否包含 L4 数据，默认 false |
| `cdn_supported` | bool | 否 | 是否发布到 CDN，默认 false |
| `enable_encryption` | bool | 否 | 是否加密配置，默认 false |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "add_tcc_config",
  "psm": "ttarch.gdp.gdpa",
  "dev_task_id": 2272667,
  "conf_name": "my_new_config",
  "content": "{\"key\": \"value\"}",
  "source_control_plane": "cn",
  "source_region": "CN",
  "description": "my new config",
  "data_type": "json"
}'
```

**返回说明**：

成功时返回 `success: true` 和 `message: "配置已创建"`，以及 `conf_name`、`source_control_plane`、`source_region`、`data_type`、`config_type`。
