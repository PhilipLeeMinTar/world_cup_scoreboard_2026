# 可用 Skill 速查与选择指南

> **重要**：在调用任何 Skill 前，**必须先阅读对应的 Skill** 获取完整的参数说明、输入输出格式和使用示例。
> **Workflow Session 约束**：本文件中的 `gdpa-cli run` 示例都要显式携带同一个 `--session-id <sid>`。CLI 不再全局强校验，但 bits-dev-workflow 必须依赖这个 Session-ID 才能串联 `.gdpa/{session-id}/status.json` 与阶段恢复。

## Skill 速查表

| 分类 | Skill 名称 | 一句话说明 | 典型场景 |
|------|-----------|-----------|---------|
| **BITS DevOps** | `bits-devops` | BITS 开发任务生命周期管理 | 创建/查询/关闭任务、通过阶段、运行流水线、查看部署详情 |
| **信息收集** | `repo2psm` | 从仓库代码自动检测 PSM | Phase 0 自动填充 PSM |
| **任务管理** | `meego-manage` | Meego 任务搜索与关联 | Phase 0 搜索 Story 供用户选择关联、搜索 Issue |
| **接口 & API** | `bam-api` | 查询 BAM 上的 API 接口定义 | 查看下游接口 Schema |
| | `bam-query` | BAM 接口测试（发送 RPC/HTTP 请求） | 测试接口、调试端点 |
| **服务 & 调用** | `overpass` | 获取服务 IDL 信息和生成调用代码 | 获取方法列表、生成 overpass 代码 |
| **代码 & 仓库** | `repotalk` | 代码仓库智能查询 | 语义搜索代码、分析调用链 |
| | `codebase` | 代码库管理（MR、分支、文件） | 创建 MR、查看代码审查 |
| **动态配置 & 数据** | `tcc-query` | 查询 TCC 远程配置 | 查询开关状态、AB 实验 |
| | `rds` | 执行 RDS 数据库 SQL 查询 | 查询数据库数据、验证表结构 |
| **监控 & 日志** | `argos-query` | 查询 Argos 服务日志 | 按 PSM/关键字/时间搜索日志 |
| | `metrics` | 查询 Metrics 监控数据 | 查看吞吐量、延迟、错误率 |
| **事件** | `eventbus` | EventBus 消息查询与发布 | 搜索事件消息、发送测试消息 |
| **部署 & 服务** | `tce` | TCE 服务/集群/Pod 查询 | 查看 Pod 状态、集群信息 |
| | `scm` | 代码版本管理 | 查询/创建版本、查看构建日志 |
| **权限** | `iam` | IAM 权限申请 | 为服务账号申请 MCP 调用权限 |

## Skill 选择决策指南

```
需要管理 BITS 开发任务？
  ├─ 创建/查询/关闭任务 → bits-devops
  ├─ 通过开发/准入阶段 → bits-devops (pass_dev_task_stage)
  ├─ 运行流水线 → bits-devops (run_pipeline)
  ├─ 查看工作流阶段 → bits-devops (get_dev_task_stages)
  ├─ 查看流水线列表 → bits-devops (get_dev_task_pipelines)
  ├─ 查看部署详情（Job 状态/失败原因） → bits-devops (get_pipeline_run)
  └─ 排查流水线失败 → get_dev_task_pipelines → get_pipeline_run（逐层追踪子流水线）

需要自动检测仓库 PSM？（Phase 0）
  └─ 是 → repo2psm（在 bootstrap.sh / settings.py / build.sh / atum.yaml 中查找）

需要搜索关联 Meego 任务？（Phase 0 或任意阶段）
  ├─ 搜索用户最近 Story → meego-manage（work_item_type_key=story, updated_at_start=4380h）
  ├─ 按关键字搜索 → meego-manage（work_item_name=关键字）
  └─ 按 ID 查询 → meego-manage（work_item_ids=[id]）

需要了解下游服务的接口定义/Schema？
  ├─ 知道 PSM → bam-api
  └─ 不知道 PSM → bam-api (get_api_definition_info_without_psm)

需要测试接口（发送 RPC/HTTP 请求）？
  └─ 是 → bam-query（VRegion 和 VDC 必须使用用户确认后的值）

需要生成下游服务调用代码？
  ├─ 获取方法列表 → overpass (get_psm_method_list)
  └─ 获取调用代码 → repotalk (get_rpcinfo)

需要理解代码仓库结构/搜索代码？
  ├─ 语义搜索 → repotalk (search_nodes)
  ├─ 查看定义 → repotalk (get_nodes_detail)
  └─ 查询组件用法 → repotalk (infra_search)

需要管理 MR / 代码审查？
  └─ 是 → codebase（创建 MR、查看审查状态）

需要查看 TCC 远程配置？
  └─ 是 → tcc-query

需要执行数据库查询？
  └─ 是 → rds

需要查看监控指标？
  └─ 是 → metrics（吞吐量、延迟、错误率）

需要查询/分析服务日志？
  └─ 是 → argos-query

需要查询/发布 EventBus 消息？
  └─ 是 → eventbus

需要查看 TCE 服务/Pod 信息？
  └─ 是 → tce

需要管理代码版本？
  └─ 是 → scm

需要申请 MCP 服务调用权限？
  └─ 是 → iam
```

## 关键阶段 Skill 调用示例

### info_collection — 自动检测与预获取

**Step 1: 自动检测 PSM**（使用 `repo2psm` 策略，在仓库中查找）

```bash
# 按优先级检查以下文件获取 PSM：
# 1. script/bootstrap.sh → PSM 变量
# 2. script/settings.py → PRODUCT.SUBSYSTEM.MODULE
# 3. build.sh → RUN_NAME 变量
# 4. atum.yaml → PSM 字段
```

**Step 2: 获取 BITS 模板列表**

```bash
# 获取空间的开发任务模板
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_templates",
  "space_id": 94017024770
}'

# 检查模板是否要求关联 Meego
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "check_template_meego",
  "dev_task_template_id": 26037
}'
```

**Step 3: 预搜索 Meego 需求**（如模板要求关联 Meego）

```bash
# 搜索用户最近 6 个月的 Story
gdpa-cli run meego-manage --session-id <sid> --input '{
  "work_item_type_key": "story",
  "page_size": 10,
  "updated_at_start": "4380h"
}'

# 如用户提供了关键字，可按关键字过滤
gdpa-cli run meego-manage --session-id <sid> --input '{
  "work_item_name": "用户年龄",
  "work_item_type_key": "story",
  "page_size": 10,
  "updated_at_start": "4380h"
}'
```

**Step 4: 汇总展示确认单**（所有参数来源都标注清楚，等待用户确认）

### task_setup — 创建 BITS 开发任务

```bash
# 创建开发任务
gdpa-cli run bits-devops --session-id <sid> --input '{
  "space_id": 94017024770,
  "branch": "feat/xxx",
  "psm_list": ["tiktok.xxx.service"],
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/123"
}'

# 获取工作流阶段
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_stages",
  "dev_task_id": 2147497
}'

# 获取泳道信息
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_lane_info",
  "dev_task_id": 2147497
}'
```

### deploy — 运行流水线与查看部署详情

```bash
# 自测流水线（默认）
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "run_pipeline",
  "dev_task_id": 2147497,
  "space_id": 94017024770,
  "control_planes": ["CONTROL_PLANE_I18N"]
}'

# 查看流水线列表（获取 pipeline_run_id）
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_pipelines",
  "dev_task_id": 2147497
}'

# 查看流水线运行详情（各 Job 状态、耗时、失败原因）
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_pipeline_run",
  "pipeline_run_id": 1123659494658
}'
```

**流水线失败排查流程**：

```bash
# 1. get_dev_task_pipelines 找到失败的 pipeline_run_id
# 2. get_pipeline_run 查看失败 Job 的 fail_reason
# 3. 如果主流水线因子流水线失败，从 fail_reason 提取 driven_pipeline_run_id，再次调用 get_pipeline_run
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_pipeline_run",
  "pipeline_run_id": <driven_pipeline_run_id>
}'
```

### dev_stage_pass — 通过开发阶段

```bash
# 提测流水线
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "run_pipeline",
  "dev_task_id": 2147497,
  "space_id": 94017024770,
  "task_name": "DevDevelopStageRDTestTask",
  "control_planes": ["CONTROL_PLANE_I18N"]
}'

# 通过开发阶段
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "pass_dev_task_stage",
  "dev_task_id": 2147497,
  "stage_action": "pass_development_stage"
}'
```

### code_review — 代码审查流水线

```bash
# 触发代码审查流水线
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "run_pipeline",
  "dev_task_id": 2147497,
  "space_id": 94017024770,
  "task_name": "DevGatekeeperStageCodeReviewTask",
  "control_planes": ["CONTROL_PLANE_I18N"]
}'

# 查看代码审查状态
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_code_review_info",
  "dev_task_id": 2147497
}'
```

### access_stage_pass — 通过准入阶段

```bash
# 通过准入阶段
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "pass_dev_task_stage",
  "dev_task_id": 2147497,
  "stage_action": "pass_access_stage"
}'
```

### testing — 接口测试与日志分析

> **VRegion 和 VDC 必须使用用户确认后的值**，不可假设。

```bash
# 接口测试（使用用户确认的 VRegion/VDC）
gdpa-cli run bam-query --session-id <sid> --input '{
  "action": "rpc",
  "psm": "tiktok.xxx.service",
  "func_name": "GetUserInfo",
  "request": "{\"user_id\": 123}",
  "vregion": "Singapore-Central",
  "vdc": "sg1"
}'

# 日志查询
gdpa-cli run argos-query --session-id <sid> --input '{
  "action": "search",
  "psm": "tiktok.xxx.service",
  "keyword": "error",
  "minutes": 10
}'
```

### 通用 — 按需查询上下文

```bash
# 查询 TCC 配置
gdpa-cli run tcc-query --session-id <sid> --input '{
  "action": "get_config",
  "key": "enable_xxx_feature",
  "psm": "tiktok.xxx.service"
}'

# 查询下游接口定义
gdpa-cli run bam-api --session-id <sid> --input '{
  "action": "get_api_definition_info",
  "psm": "tiktok.xxx.downstream",
  "method": "GetUserDetail"
}'

# 语义搜索代码
gdpa-cli run repotalk --session-id <sid> --input '{
  "action": "search_nodes",
  "question": "如何处理 UserInfo 的 age 字段",
  "repo_names": "tiktok/xxx-service"
}'

# 查询监控指标
gdpa-cli run metrics --session-id <sid> --input '{
  "action": "query",
  "psm": "tiktok.xxx.service",
  "metric_type": "throughput"
}'

# 执行数据库查询
gdpa-cli run rds --session-id <sid> --input '{
  "action": "query",
  "sql": "SELECT * FROM user_info LIMIT 5",
  "db_name": "xxx_db"
}'

# 查询 EventBus 消息
gdpa-cli run eventbus --session-id <sid> --input '{
  "action": "search",
  "event_name": "user_info_updated"
}'
```
