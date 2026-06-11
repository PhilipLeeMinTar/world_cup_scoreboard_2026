# 开发任务工具

## create_dev_task — 创建开发任务

创建 BITS 开发任务，自动解析项目配置（控制面、集群、泳道等），构建代码变更和部署环境。不传 `action` 时默认为此操作。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `space_id` | number | 是 | BITS 空间 ID（可通过 `get_recent_spaces` 获取） |
| `branch` | string | 条件 | 全局开发分支名（当所有 PSM 共用同一分支时必填；若每个 PSM 都在 `psm_list` 对象中指定了 `branch` 则可省略） |
| `psm_list` | string[] 或 object[] | 是 | PSM 列表，支持三种格式（见下方说明）。也接受 `psm` 单个字符串 |
| `meego_url` | string | 条件 | Meego 需求链接（TCC 项目可选，其他类型必填） |
| `project_type` | string | 否 | 全局项目类型，默认 `PROJECT_TYPE_TCE`。支持 `PROJECT_TYPE_TCE`（别名 `tce`）、`PROJECT_TYPE_FAAS`（别名 `faas`）、`PROJECT_TYPE_WEB`（别名 `web`）和 `PROJECT_TYPE_TCC`（别名 `tcc`）。也可在 `psm_list` 对象中按 PSM 单独指定。**Web 项目的 `psm` 填数字 ID（而非 PSM 名），如不确定 ID 可先用 `search_projects` 查询**。**TCC 项目不需要 `branch` 和 `meego_url` 参数** |
| `dev_task_template_id` | number | 否 | 开发任务模板 ID，不传则自动获取默认模板。别名：`template_id`、`workflow_id` |
| `team_flow_id` | number | 否 | 研发流程 ID，不传则自动解析；空间无研发流程时以 0 创建 |
| `title` | string | 否 | 标题，不传则自动生成 |
| `target_branch` | string | 否 | MR 目标分支名（如 `master`、`main`），不传则自动获取仓库默认分支 |
| `lane_id` | string | 否 | 泳道后缀，默认 `feature_${development_task_id}`。任务创建后完整环境名如 `boe_<lane_id>` / `ppe_<lane_id>`；用户口中的「env / 环境名 / 泳道名 / lane」均指此参数，注意用户输入若带 `boe_` / `ppe_` 前缀，**去掉前缀**后再传入此参数 |
| `control_planes` | string[] | 否 | 控制面过滤列表（见下方说明） |
| `enable_boe` | boolean | 否 | 是否创建 BOE 环境，默认 `true`。设为 `false` 时跳过所有 BOE 泳道（CN 的 `boe_env_` 与 I18N 的 `prod_sg_env_`），任务只保留 PPE 流水线。**仅在创建任务时生效**（`add_project_to_dev_task` 不会修改环境配置） |

**psm_list 格式说明**：

支持三种格式，向后兼容：

1. **string[]**（旧格式）：所有 PSM 共用全局 `branch`
   ```json
   "psm_list": ["psm_a", "psm_b"]
   ```
2. **object[]**（新格式）：每个 PSM 可指定独立 `branch`、`target_branch` 和 `project_type`，未指定时 fallback 到全局参数
   ```json
   "psm_list": [
     {"psm": "psm_a", "branch": "feat/wallet", "target_branch": "release/v2"},
     {"psm": "psm_b", "branch": "feat/order", "project_type": "faas"},
     {"psm": "psm_c"}
   ]
   ```
3. **单个 `psm` 字符串**：使用全局 `branch`

注意：如果两个 PSM 共享同一个代码仓库但指定了不同分支，会报错。

**control_planes 说明**：

每个控制面覆盖一组 VRegion，便于从地域反查应选控制面；实际可用控制面以空间模板为准。

| 可选值 | 别称 | 说明 | 覆盖的典型 VRegion |
|--------|------|------|---------------------|
| `CONTROL_PLANE_CN` | cn | 中国控制面 | `China-North`、`China-East`、`China-North6`、`China-Pay`、`China-Pay2`、`Aliyun_NC2`、`China-Enterprise`、`China-HKPay`、`ChinaSinf-North`、`China-BOE` |
| `CONTROL_PLANE_I18N` | i18n / row | 国际化控制面 | `Singapore-Central`、`US-East`、`US-West`、`US-BOE` |
| `CONTROL_PLANE_US_TTP` | ttp / us-ttp | US-TTP 控制面 | `US-TTP`、`US-TTP2`、`US-EastRed` |
| `CONTROL_PLANE_EU_TTP` | eu-ttp | EU-TTP 控制面 | `EU-TTP`、`EU-TTP2` |

不传时自动使用项目支持的全部控制面（会根据模板配置自动过滤）。

**示例（最少参数）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 94017024770,
  "branch": "feat/my-feature",
  "psm_list": ["tiktok.gdp.llm_remote"],
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119"
}'
```

**示例（指定控制面）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 94017024770,
  "branch": "feat/my-feature",
  "psm_list": ["tiktok.gdp.llm_remote"],
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119",
  "control_planes": ["CONTROL_PLANE_I18N"]
}'
```

**示例（全部参数）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 94017024770,
  "team_flow_id": 424660152834,
  "dev_task_template_id": 26037,
  "branch": "master",
  "target_branch": "main",
  "psm_list": ["tiktok.gdp.llm_remote"],
  "title": "fix: bug fix",
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119",
  "lane_id": "feature_${development_task_id}",
  "control_planes": ["CONTROL_PLANE_CN", "CONTROL_PLANE_I18N"]
}'
```

**示例（不同 PSM 使用不同分支）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 112682196994,
  "psm_list": [
    {"psm": "tikcast.wallet.api_tiktok", "branch": "feat/wallet"},
    {"psm": "wallet.recharge.core_tiktok", "branch": "feat/recharge"},
    {"psm": "ies.order.channel_tiktok", "branch": "feat/order"}
  ],
  "meego_url": "https://meego.larkoffice.com/tiktok_live/story/detail/7022319078",
  "title": "feat: multi-branch task"
}'
```

**示例（混合格式 — 部分 PSM 指定分支，其余用全局分支）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 112682196994,
  "branch": "feat/default",
  "psm_list": [
    {"psm": "tikcast.wallet.api_tiktok", "branch": "feat/wallet"},
    {"psm": "ies.order.channel_tiktok"}
  ],
  "meego_url": "https://meego.larkoffice.com/tiktok_live/story/detail/7022319078"
}'
```

**示例（FaaS 项目类型）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4061513218,
  "branch": "feat/my-feature",
  "project_type": "faas",
  "psm_list": ["tt4d.portal.operation_script_async"],
  "meego_url": "https://meego.feishu.cn/tiktok/sub_task/detail/7075184517"
}'
```

**示例（Web 项目类型）**：

Web 项目的 `psm` 参数填写项目数字 ID（非 PSM 名）。如果只知道项目名称，先用 `action=search_projects` 查询获取 `project_unique_id`。

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4061513218,
  "branch": "@yc/test-embed",
  "project_type": "web",
  "psm_list": ["85959"],
  "meego_url": "https://meego.feishu.cn/tiktok/sub_task/detail/7075184517"
}'
```

**示例（TCC 项目类型）**：

TCC 项目不需要 `branch` 参数（无代码变更），`meego_url` 可选。系统会自动通过 TCC 权限接口检查 PSM 在各控制面上是否有 TCC 命名空间。

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4389122306,
  "project_type": "tcc",
  "psm": "tiktok.feed.component",
  "meego_url": "https://meego.feishu.cn/tiktok/sub_task/detail/7088119016",
  "title": "TCC config update"
}'
```

**示例（TCC 项目指定控制面）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4389122306,
  "project_type": "tcc",
  "psm": "tiktok.feed.component",
  "control_planes": ["CONTROL_PLANE_I18N"],
  "title": "TCC config update for I18N"
}'
```

**示例（混合 TCE 和 FaaS 项目）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4061513218,
  "branch": "feat/my-feature",
  "psm_list": [
    {"psm": "tiktok.gdp.llm_remote", "branch": "feat/my-feature"},
    {"psm": "tt4d.portal.operation_script_async", "branch": "feat/my-feature", "project_type": "faas"}
  ],
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119"
}'
```

**示例（混合 TCE + TCC + FaaS）**：

`psm_list` 中每个对象的 `project_type` 独立解析：TCC 项目走 `CheckTccauth` 探测命名空间、不创建 MR；非 TCC 项目走 `GetAppComponents` 拿 SCM 主仓库。各项目类型在同一个开发任务里可以自由组合。

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4389122306,
  "branch": "feat/cross-region-policy-control",
  "title": "Cross-Region Policy Control",
  "psm_list": [
    {"psm": "tiktok.feed.component", "project_type": "tcc"},
    {"psm": "tiktok.gdp.llm_remote", "branch": "feat/cross-region-policy-control", "project_type": "tce"},
    {"psm": "tt4d.portal.operation_script_async", "branch": "feat/cross-region-policy-control", "project_type": "faas"}
  ],
  "control_planes": ["CONTROL_PLANE_I18N", "CONTROL_PLANE_EU_TTP", "CONTROL_PLANE_US_TTP"],
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119"
}'
```

**示例（不创建 BOE 环境）**：

部分团队只用 PPE / 线上环境，不需要 BOE 自测环境。把 `enable_boe` 设为 `false` 后，本次创建的开发任务会跳过所有 BOE 泳道，环境列表里只剩 PPE。**仅在创建任务时生效**，对已创建的任务无效。

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 4389122306,
  "branch": "feat/my-feature",
  "psm_list": ["tiktok.gdp.llm_remote"],
  "control_planes": ["CONTROL_PLANE_I18N"],
  "enable_boe": false,
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119"
}'
```

**返回**：

当所有 PSM 共用同一分支时：
```json
{
  "success": true,
  "action": "create_dev_taskv2",
  "dev_task_id": 2147497,
  "title": "fix: bug fix",
  "branch": "master",
  "link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2147497"
}
```

当不同 PSM 使用不同分支时：
```json
{
  "success": true,
  "action": "create_dev_taskv2",
  "dev_task_id": 2147497,
  "title": "feat: multi-branch task",
  "branches": {
    "tikcast.wallet.api_tiktok": "feat/wallet",
    "wallet.recharge.core_tiktok": "feat/recharge"
  },
  "link": "https://bits.bytedance.net/devops/112682196994/develop/detail/2147497"
}
```

---

## add_project_to_dev_task — 向已有任务新增项目

向已创建的 BITS 开发任务新增项目（PSM），自动解析项目配置并创建对应的代码变更（MR）。已存在的项目和代码变更会被保留。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `add_project_to_dev_task` |
| `dev_task_id` | number | 是 | 开发任务 ID |
| `projects` | object[] | 是 | 要新增的项目列表（见下方说明） |

**projects 对象字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `psm` | string | 是 | 项目 PSM（TCC 项目填 TCC namespace 的 PSM） |
| `branch` | string | TCC 外必填 | 开发分支名。`project_type=tcc` 时无代码变更，可省略 |
| `target_branch` | string | 否 | MR 目标分支名（如 `master`、`main`），不传则自动获取仓库默认分支 |
| `project_type` | string | 否 | 项目类型，默认 `PROJECT_TYPE_TCE`。支持 `tce` / `faas` / `web` / `tcc`。Web 项目的 `psm` 填数字 ID；TCC 项目不会创建 MR、不需要 `branch`/`target_branch` |
| `control_planes` | string[] | 否 | 控制面过滤列表，不传则使用项目支持的全部控制面 |

**示例（单个项目）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "add_project_to_dev_task",
  "dev_task_id": 2250332,
  "projects": [
    {"psm": "tiktok.gdp.gemini_proxy", "branch": "feat/my-feature"}
  ]
}'
```

**示例（多个项目，指定控制面）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "add_project_to_dev_task",
  "dev_task_id": 2250332,
  "projects": [
    {"psm": "tiktok.gdp.gemini_proxy", "branch": "feat/my-feature", "control_planes": ["CONTROL_PLANE_CN"]},
    {"psm": "ies.gdp.open_api", "branch": "feat/my-feature", "control_planes": ["CONTROL_PLANE_CN", "CONTROL_PLANE_I18N"]}
  ]
}'
```

**示例（混合 TCE + TCC + FaaS）**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "add_project_to_dev_task",
  "dev_task_id": 2250332,
  "projects": [
    {"psm": "tiktok.gdp.gemini_proxy", "branch": "feat/my-feature", "project_type": "tce"},
    {"psm": "tiktok.feed.component", "project_type": "tcc", "control_planes": ["CONTROL_PLANE_I18N"]},
    {"psm": "tiktok.user_data_platform.scripts", "branch": "feat/my-feature", "project_type": "faas"}
  ]
}'
```

**返回**：

```json
{
  "success": true,
  "action": "add_project_to_dev_task",
  "dev_task_id": 2250332,
  "link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2250332"
}
```

**注意事项**：
- 已存在于任务中的 PSM 会自动跳过
- 如果新 PSM 的主仓库已有代码变更（MR），不会重复创建
- 已有的代码变更和项目配置（包括 SCM 依赖版本）会被完整保留

---

## remove_project_from_dev_task — 从任务删除项目

从已有的 BITS 开发任务中删除指定项目（PSM）。如果被删除项目的主仓库不再被其他项目引用，对应的代码变更也会一并删除。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | 固定值 `remove_project_from_dev_task` |
| `dev_task_id` | number | 是 | 开发任务 ID |
| `projects` | object[] | 是 | 要删除的项目列表，每项为 `{"psm": "xxx"}` |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "remove_project_from_dev_task",
  "dev_task_id": 2250588,
  "projects": [
    {"psm": "tiktok.gdp.gemini_proxy"}
  ]
}'
```

**返回**：

```json
{
  "success": true,
  "action": "remove_project_from_dev_task",
  "dev_task_id": 2250588,
  "removed_psms": ["tiktok.gdp.gemini_proxy"],
  "link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2250588"
}
```

**注意事项**：
- 任务中不存在的 PSM 会报错提示
- 如果被删除 PSM 的主仓库仍被其他项目引用，对应的代码变更会保留
- 如果被删除 PSM 是该仓库的最后一个项目，对应的代码变更也会一并删除

---

## close_dev_task — 关闭开发任务

关闭指定的开发任务。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |
| `force` | bool | 否 | 是否强制关闭，默认 false |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "close_dev_task",
  "dev_task_id": 2147497,
  "force": true
}'
```

---

## pass_dev_task_stage — 通过阶段

通过开发任务的指定阶段。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |
| `stage_action` | string | 是 | 阶段操作：`pass_development_stage` 或 `pass_access_stage` |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "pass_dev_task_stage",
  "dev_task_id": 2147497,
  "stage_action": "pass_development_stage"}'
```

---

## run_pipeline — 运行流水线

触发开发任务的流水线运行（使用 QuickRunPipelines 接口）。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |
| `space_id` | number | 是 | BITS 空间 ID（可通过 `get_recent_spaces` 获取） |
| `task_name` | string | 否 | 流水线任务的 fixedName（默认 `DevDevelopStageSelfTestTask`） |
| `control_planes` | string[] | 否 | 控制面列表，不传则自动从已有流水线检测（fallback `["CONTROL_PLANE_CN"]`） |

**task_name 说明**：

`task_name` 必须使用 fixedName 格式，可通过 `get_dev_task_stages` 获取（返回结果中每个 task 的 `fixed_name` 字段）。

常用 fixedName：

| fixedName | 所属阶段 | 说明 |
|-----------|----------|------|
| `DevDevelopStageSelfTestTask` | 开发 | 自测流水线 |
| `DevDevelopStageFeatureTestTask` | 开发 | 功能测试流水线 |
| `DevDevelopStageRDTestTask` | 开发 | 提测/免测 |
| `DevDevelopStageCustomTask` | 开发 | 自定义流水线 |
| `DevGatekeeperStageIntegrationTestTask` | 测试 | 测试流水线 |
| `DevGatekeeperStageCodeReviewTask` | 测试 | 代码审查 |
| `DevGatekeeperStageQualityRiskTask` | 测试 | 质量风险 |

**control_planes 可选值**：

与 **create_dev_task** 相同：`CONTROL_PLANE_CN`、`CONTROL_PLANE_I18N`、`CONTROL_PLANE_EU_TTP`、`CONTROL_PLANE_US_TTP`；与典型 VRegion 的对照见 **create_dev_task** 一节中的 **control_planes 说明** 表格。

**使用流程**：

1. 先调用 `get_dev_task_stages` 获取阶段和任务列表
2. 从结果中找到目标任务的 `fixed_name`
3. 将 `fixed_name` 作为 `task_name` 传入 `run_pipeline`

**示例**：

```bash
# 运行自测流水线（默认）
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "run_pipeline",
  "dev_task_id": 2147497,
  "space_id": 94017024770}'

# 指定流水线类型和控制面
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "run_pipeline",
  "dev_task_id": 2147497,
  "space_id": 94017024770,
  "task_name": "DevGatekeeperStageIntegrationTestTask",
  "control_planes": ["CONTROL_PLANE_CN", "CONTROL_PLANE_I18N"]}'
```

---

## get_opened_dev_task_list — 获取已开启任务列表

返回空间内状态为 opened 的开发任务，每次返回 10 条，支持游标分页。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `space_id` | number | 是 | BITS 空间 ID（可通过 `get_recent_spaces` 获取） |
| `last_id` | number | 否 | 分页游标，传入上一页返回的 `next_last_id` 获取下一页 |

**返回**中包含 `next_last_id` 字段，可直接用于下次请求的 `last_id` 实现翻页。

**示例**：

```bash
# 第一页
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_opened_dev_task_list",
  "space_id": 94017024770}'

# 下一页（使用上一页返回的 next_last_id）
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_opened_dev_task_list",
  "space_id": 94017024770,
  "last_id": 2131496}'
```

---

## get_dev_task_basic_info — 获取基本信息

返回开发任务的基本信息，包括标题、状态、创建者、关联发布单等。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_basic_info",
  "dev_task_id": 2147497}'
```

---

## get_dev_task_changes — 获取代码变更

返回开发任务关联的代码变更列表，包括分支、MR 状态等。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_changes",
  "dev_task_id": 2147497}'
```

---

## get_dev_task_project_info — 获取项目信息

返回开发任务的项目部署配置。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_project_info",
  "dev_task_id": 2147497}'
```

---

## get_dev_task_lane_info — 获取泳道信息

返回开发任务的泳道环境配置，部署环境信息。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_lane_info",
  "dev_task_id": 2147497}'
```

**完整泳道名拼接规则**：

完整泳道名（即 BITS 页面显示的泳道名）的拼接方式：

- 默认：**`lane_type` + `lane_id`**
- 如果 `overwrite_prefix` 不为空：**`overwrite_prefix` + `lane_id`**

此完整泳道名用于后续所有需要指定泳道的场景（如部署、环境配置、流量路由等）。

> 反向：传 `create_dev_task` 的 `lane_id` 若带 `boe_` / `ppe_` 前缀，需去掉前缀后再传入；详见 `create_dev_task` 章节。

示例（`lane_id` 为 `feature_2153786`）：

| lane_type | overwrite_prefix | 完整泳道名 |
|-----------|------------------|-----------|
| `boe_env_` | `boe_` | `boe_feature_2153786`（使用 overwrite_prefix） |
| `ppe_cn_env_` | `ppe_` | `ppe_feature_2153786`（使用 overwrite_prefix） |
| `prod_sg_env_` | _(空)_ | `prod_sg_env_feature_2153786`（使用 lane_type） |
| `ppe_i18n_env_` | _(空)_ | `ppe_i18n_env_feature_2153786`（使用 lane_type） |

---

## get_dev_task_code_review_info — 获取代码审查信息

返回代码审查状态，包括 reviewer、审查结论等。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_code_review_info",
  "dev_task_id": 2147497}'
```

---

## get_dev_task_stages — 获取工作流阶段

返回开发任务的工作流阶段信息，包括当前阶段、各阶段任务及其 `fixed_name`、是否可合并等。
每个任务的 `fixed_name` 可直接用于 `run_pipeline` 的 `task_name` 参数。

**注意**：BITS 返回的阶段/任务 `status` 是聚合状态，可能只要部分控制面通过就显示 `succeeded`。
返回中额外包含 `pipelines_by_task` 字段，按 `StageName/TaskName` 分组展示各控制面的真实流水线状态，
判断是否全部通过时应以此为准。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**返回**中除 `data`（阶段信息）外，还包含：

| 字段 | 说明 |
|------|------|
| `pipelines_by_task` | 按 `StageName/TaskName` 分组的流水线详情，每条包含 `control_plane`、`status`、`is_main_pipeline`、`project_name` |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_stages",
  "dev_task_id": 2147497}'
```

**返回示例（pipelines_by_task 部分）**：

```json
"pipelines_by_task": {
  "DevDevelopStage/DevDevelopStageSelfTestTask": [
    {"control_plane": "CONTROL_PLANE_US_TTP", "status": "SUCCEEDED", "is_main_pipeline": true, "project_name": ""},
    {"control_plane": "CONTROL_PLANE_I18N", "status": "FAILED", "is_main_pipeline": true, "project_name": ""}
  ]
}
```

---

## get_dev_task_vars — 获取变量设置

返回开发任务的运行时变量设置。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_vars",
  "dev_task_id": 2147497}'
```

---

## get_dev_task_pipelines — 获取流水线信息

返回开发任务关联的流水线运行信息。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dev_task_id` | number | 是 | 开发任务 ID |

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_pipelines",
  "dev_task_id": 2147497}'
```

---

## get_pipeline_run — 获取流水线运行详情

通过 `pipeline_run_id`（从 `get_dev_task_pipelines` 返回的 `pipeline_run_id` 字段获取）查询流水线的详细运行信息，包括每个 Job 的执行状态、耗时和失败原因。适合排查流水线失败原因。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pipeline_run_id` | number | 是 | 流水线运行 ID（来自 `get_dev_task_pipelines` 的 `pipeline_run_id`） |

**返回字段说明**：

| 字段 | 说明 |
|------|------|
| `run_id` | 流水线运行 ID |
| `pipeline_id` | 流水线 ID |
| `run_status` | 运行状态 |
| `run_name` | 流水线名称 |
| `time_cost_sec` | 总耗时（秒） |
| `pipeline_run_url` | 流水线运行页面链接 |
| `fail_reason` | 失败原因（仅失败时） |
| `jobs[]` | Job 列表 |
| `jobs[].job_name` | Job 名称 |
| `jobs[].job_status` | Job 状态 |
| `jobs[].time_cost_sec` | Job 耗时（秒） |
| `jobs[].fail_type` | 失败类型（仅失败时） |
| `jobs[].fail_reason` | 失败原因（仅失败时） |

**使用流程**：

1. 先调用 `get_dev_task_pipelines` 获取流水线列表
2. 从结果中取出目标流水线的 `pipeline_run_id`
3. 将 `pipeline_run_id` 传入 `get_pipeline_run` 查看详情

**示例**：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_pipeline_run",
  "pipeline_run_id": 1123659494658}'
```
