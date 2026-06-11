# MR 操作

> 管理 BITS 合并请求（Merge Request）：创建、查询、审查、标签绑定等。

## 项目与配置查询

### `get_group_projects` - 获取 Group 下项目列表

查询某个 Group 关联的所有项目，可用于获取 `project_gitlab_id`。支持分页和关键词过滤。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `group_name` | string | **是** | Group 名称（如 `TikTok_iOS`） |
| `filter_indirect_host` | bool | 否 | 过滤间接宿主，默认 `true` |
| `keyword` | string | 否 | 按项目名/git_url 过滤 |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页条数，默认 `50` |

返回：`total`、`page`、`page_size`、`total_pages`、`data`（项目列表）。

### `get_develop_configs` - 获取 Group 开发配置

查询 Group 的开发配置，包括自定义表单字段（`custom_forms`），返回 `create_mr` 时可用的 `custom_fields` 定义。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `group_name` | string | **是** | Group 名称 |

返回：`group_name`、`root_project_id`、`custom_forms`（按场景分类的字段列表，每项含 `key`、`label`、`field_type`、`default_value`）。

## 创建 MR

### `create_mr` - 创建合并请求

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `host_group_name` | string | **是** | Group 名称（如 `TikTok_iOS`） |
| `project_gitlab_id` | int | **是** | 项目 GitLab ID（可通过 `get_group_projects` 获取） |
| `source_branch` | string | **是** | 源分支名 |
| `target_branch` | string | **是** | 目标分支名 |
| `type` | string | 否 | MR 类型，默认 `feature`（可通过 `get_mr_types` 获取可选值） |
| `title` | string | 否 | MR 标题 |
| `tags` | string[] | 否 | 标签名称数组（可通过 `get_tags_list` 获取可选值） |
| `remove_source` | bool | 否 | 合并后删除源分支，默认 `true` |
| `custom_fields` | map | 否 | 自定义 CI 字段（可通过 `get_develop_configs` 获取可用字段） |

> **提示**：对于 `feature` / `optimize` / `bug` 等类型的 MR，创建后通常需要使用 `bind_mr_feature` 关联需求任务。
> 该操作支持多次调用以绑定多条需求。

```bash
gdpa-cli run bits-devops --session-id "$SESSION_ID" --input '{
  "action": "create_mr",
  "host_group_name": "TikTok_iOS",
  "project_gitlab_id": 114467,
  "source_branch": "feat/my-feature",
  "target_branch": "develop",
  "type": "feature",
  "title": "my feature",
  "tags": ["TEST"]
}'
```

## MR 查询

### `get_mr_basic` - 获取 MR 基本信息

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID（即 optimus_mr_id / dev_id） |

返回：标题、类型、状态、创建者、标签、是否可编辑等。

### `get_mr_branch_detail` - 获取 MR 分支详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：源/目标分支、冲突状态、项目名称、GitLab URL、版本号等。

### `get_mr_repo_state` - 获取仓库状态

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：冲突状态、空内容标记、合并目标状态、目标分支新提交数等。

### `get_mr_graph` - 获取 MR 流水线阶段

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：流水线阶段列表（CI Check、Code Review、Meego Check、Lock、After Check、Host Merge 等），每个阶段包含名称、类型、状态。

### `get_mr_permission` - 获取 MR 权限

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：`can_close`、`can_retry`、`can_force_merge`、`can_merge_base` 等权限标志。

### `get_mr_host_id` - 获取 MR 宿主项目信息

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：MR ID、项目 ID、IID、Git 仓库地址、Group 名称。

## 配置查询

### `get_mr_types` - 获取可用 MR 类型

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `group_name` | string | **是** | Group 名称 |
| `source_branch` | string | **是** | 源分支名 |
| `target_branch` | string | **是** | 目标分支名 |

返回：可用类型列表（如 `["feature", "optimize", "bug", "package", "lite"]`）。

### `get_tags_list` - 获取标签列表

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `group_project_name` | string | **是** | Group/Project 名称 |
| `keyword` | string | 否 | 按标签名过滤 |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页条数，默认 `50` |

返回：`total`、`page`、`page_size`、`total_pages`、`data`（标签列表）。

### `bind_mr_tags` - 批量绑定标签

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |
| `tag_names` | string[] | **是** | 标签名称数组 |

## 代码审查

### `get_code_review_detail` - 获取代码审查详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID（host_mr_id） |

返回：审查状态、全局规则结果、各项目审查规则结果。

## QA 审查

### `get_qa_review_status` - 获取 QA 审查状态

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：是否已审批、各 host 审查状态、QA 测试人员、审查 URL。

### `start_qa_review` - 启动 QA 审查

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |
| `group_name` | string | **是** | Group 名称 |
| `emails` | string[] | 否 | QA 人员邮箱列表，默认空 |
| `qa_review_mode` | int | 否 | 审查模式，默认 `2` |
| `is_need_qa` | bool | 否 | 是否需要 QA，默认 `true` |

### `get_qa_review_rules` - 获取匹配的 QA 规则

支持两种查询方式：

**方式一**：按 MR ID 查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

**方式二**：按条件查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `group_name` | string | **是** | Group 名称 |
| `mr_type` | string | 否 | MR 类型 |
| `target_branch` | string | 否 | 目标分支 |
| `project_ids` | string | 否 | 项目 ID（逗号分隔） |

## Feature 任务关联

### `get_user_tasks` - 搜索用户 Feature 任务

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `group_name` | string | **是** | Group 名称 |
| `task_type` | string | 否 | 任务类型，默认 `issue` |
| `text` | string | 否 | 搜索关键词 |
| `platform` | string | 否 | 平台，默认 `meego,rocket` |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页条数，默认 `20` |

### `bind_mr_feature` - 关联 MR 与 Feature 任务

每次调用绑定一条需求。**支持多次调用**以关联多条需求到同一个 MR。

> 对于 `feature`、`optimize`、`bug` 类型的 MR，关联需求通常是必需的。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |
| `group_name` | string | **是** | Group 名称 |
| `task_id` | string | **是** | 任务 ID |
| `task_title` | string | 否 | 任务标题 |
| `platform` | string | 否 | 平台，默认 `meego` |
| `task_type` | string | 否 | 任务类型，默认 `issue` |
| `feature_config_id` | int | 否 | Feature 配置 ID |

```bash
# 绑定第一条需求
gdpa-cli run bits-devops --session-id "$SESSION_ID" --input '{
  "action": "bind_mr_feature",
  "mr_id": 8021428,
  "group_name": "TikTok_iOS",
  "task_id": "7074064311",
  "task_title": "需求 A"
}'

# 绑定第二条需求
gdpa-cli run bits-devops --session-id "$SESSION_ID" --input '{
  "action": "bind_mr_feature",
  "mr_id": 8021428,
  "group_name": "TikTok_iOS",
  "task_id": "7074064322",
  "task_title": "需求 B"
}'
```

## MR 操作

### `get_mr_checkpoint` - 获取准入检测信息

查询 MR 的准入检测（Security & Compliance & Gate、Pipeline Jobs 等）状态。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |
| `lang` | string | 否 | 语言，默认 `zh` |

返回：分组列表，每组含 `title` 和 `checks`（每项含 `name`/`status`/`check_type`/`retryable`/`link`）。

### `get_mr_timeline` - 获取 MR Timeline

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页条数，默认 `20` |

返回：事件列表，每项含 `type`（如 `create_mr`、`pipeline_start`、`mr_rerun`）、`operator`、`timestamp`。

### `get_mr_block_error` - 获取 MR 阻塞错误

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID |

返回：阻塞错误列表（无阻塞时为空数组）。

### `retry_workflow` - 重试工作流

触发 MR 工作流重新执行（等同 UI 上的"重试工作流"按钮）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `project_id` | int | **是** | 项目 GitLab ID（可通过 `get_mr_host_id` 获取） |
| `iid` | int | **是** | MR IID（可通过 `get_mr_host_id` 获取） |

### `close_mr` - 关闭 MR

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `mr_id` | int | **是** | MR ID（host_mr_id） |

### `sync_target_branch` - 同步目标分支

将 MR 的源分支同步到目标分支的最新代码（Merge Target 或 Rebase）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `project_id` | int | **是** | 项目 GitLab ID（可通过 `get_mr_host_id` 获取 `projectID`） |
| `iid` | int | **是** | MR IID（可通过 `get_mr_host_id` 获取 `iID`） |
| `sync_type` | string | 否 | 同步目标：`develop`（默认，稳定分支）或 `rc`（RC 分支） |

```bash
# 同步到 develop 分支
gdpa-cli run bits-devops --session-id "$SESSION_ID" --input '{
  "action": "sync_target_branch",
  "project_id": 114467,
  "iid": 267379,
  "sync_type": "develop"
}'

# 同步到 RC 分支
gdpa-cli run bits-devops --session-id "$SESSION_ID" --input '{
  "action": "sync_target_branch",
  "project_id": 114467,
  "iid": 267379,
  "sync_type": "rc"
}'
```

---

## 附录：`custom_fields` 参考

`create_mr` 的 `custom_fields` 参数用于控制 CI 行为，不同 Group 的可用字段不同。
可通过 `get_develop_configs` 动态获取当前 Group 的完整字段列表。

以下为 **TikTok_iOS** Group 的常见 `custom_fields` 参考：

| key | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `CUSTOM_CI_ENABLE_SQUASH_COMMITS` | switch | `true` | Squash Commits |
| `JOJO_ENABLE_ODR` | switch | `false` | Integrate Gecko ODR |
| `CUSTOM_CI_VERIFY_COMPILATION` | switch | `false` | Compare build artifacts |
| `JOJO_ENABLE_ODR_I18N` | switch | `false` | Integrate I18N ODR |
| `CUSTOM_CI_BUILD_TIKTOK_T` | switch | `false` | Build TikTok-T |
| `CUSTOM_CI_BUILD_WHEE_INHOUSE` | switch | `false` | Build Whee |
| `CUSTOM_CI_BUILD_WHEE_RELEASE` | switch | `false` | Build Whee Release Without Inhouse Tools |
| `CUSTOM_CI_BUILD_TIKTOKCHECK` | switch | `false` | Build TTLS |
| `CUSTOM_CI_BUILD_TIKTOKCOIN` | switch | `false` | Build TikTok-Pro(Coin) |
| `CUSTOM_CI_BUILD_MUSICALLY_US` | switch | `false` | Build Musically-US |
| `CUSTOM_CI_BUILD_STUDIO_INHOUSE` | switch | `false` | Build TikTok-Studio |
| `CUSTOM_CI_BUILD_DRAMA_INHOUSE` | switch | `false` | Build Drama |
| `CUSTOM_CI_BUILD_DRAMA_RELEASE` | switch | `false` | Build Drama Release Without Inhouse Tools |
| `CUSTOM_CI_BUILD_ECSAAS` | switch | `false` | Build EC-Saas |
| `CUSTOM_CI_BUILD_MUSICALLY_RELEASE` | switch | `false` | Build TikTok-M Release Without Inhouse Tools |
| `CUSTOM_CI_BUILD_TIKTOK_RELEASE` | switch | `false` | Build TikTok-T Release Without Inhouse Tools |
| `CUSTOM_CI_BUILD_TIKTOKCOIN_RELEASE` | switch | `false` | Build TikTok-Pro(Coin) Release Without Inhouse Tools |
| `CUSTOM_CI_BUILD_MUSICALLY_LARK_INHOUSE` | switch | `false` | Build TikTok-M Lark Inhouse Release |
| `CUSTOM_CI_BUILD_TIKTOK_LARK_INHOUSE` | switch | `false` | Build TikTok-T Lark Inhouse Release |
| `CUSTOM_CI_BYTEST_MEMORY_CKECK` | switch | `true` | Run ByTest Memory Check |
| `THIRD_PARTY_SDK_BIN_ADDRESS_ANALYZE` | switch | `false` | 3rd Party SDK Bin Address Analyze |
| `SEER_DISABLE_BITNEST_US` | switch | `false` | Disable TTP Pods |
| `CUSTOM_CI_BUILD_TRIGGER_UNIT_TESTS` | text | `""` | Trigger Unit Tests with Names |
| `COCOAPODS_CLEAN_ALL_CACHES` | switch | `false` | Re-download all external components |

> **注意**：以上为 TikTok_iOS 的快照参考，其他 Group 的字段可能完全不同。建议使用 `get_develop_configs` 获取准确列表。
