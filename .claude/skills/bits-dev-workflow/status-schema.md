# status.json 完整结构

存放路径：`.gdpa/{session-id}/status.json`

## 字段说明

```json
{
  "session_id": "string — 会话唯一标识，必须与 workflow 中所有命令显式传递的 --session-id 保持一致（直接使用 gdpa-cli create-session 返回值）",
  "created_at": "string — 创建时间 ISO8601",
  "requirement": "string — 用户需求一句话描述",
  "current_phase": "string — 当前所在阶段（info_collection|task_setup|deploy|testing|dev_stage_pass|code_review|access_stage_pass|completion）",
  "phases": {
    "info_collection": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null — 开始时间",
      "completed_at": "string|null — 完成时间",
      "summary": "string — 该阶段执行摘要"
    },
    "task_setup": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "deploy": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "testing": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "dev_stage_pass": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "code_review": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "access_stage_pass": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "completion": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    }
  },
  "context": {
    "psm": "string — 服务 PSM（来源：info_collection，使用：全部）",
    "psm_list": ["string — PSM 列表（来源：info_collection，使用：task_setup）"],
    "branch": "string — Git 分支名（来源：info_collection，使用：全部）",
    "space_id": "number — BITS 空间 ID（来源：info_collection，使用：task_setup、deploy、dev_stage_pass、access_stage_pass）",
    "dev_task_id": "number|null — BITS 开发任务 ID（来源：task_setup，使用：deploy 以后所有阶段）",
    "bits_link": "string — BITS 任务链接（来源：task_setup，使用：completion）",
    "control_planes": ["string — 控制面列表，如 CONTROL_PLANE_CN、CONTROL_PLANE_I18N（来源：info_collection，使用：deploy、dev_stage_pass）"],
    "lane_info": "object|null — 泳道配置信息（来源：task_setup，使用：testing）",
    "stages_info": "object|null — BITS 工作流阶段信息（来源：task_setup，使用：dev_stage_pass、access_stage_pass）",
    "meego_url": "string — Meego 链接，可选（来源：info_collection，使用：task_setup）",
    "template_id": "number — 开发任务模板 ID（来源：info_collection，使用：task_setup）",
    "team_flow_id": "number — 研发流程 ID（来源：info_collection，使用：task_setup）",
    "test_vregion": ["string — 用户确认的测试 VRegion 列表（来源：info_collection，使用：testing）"],
    "test_vdc": ["string — 用户确认的测试 VDC 列表（来源：info_collection，使用：testing）"],
    "test_env": "string — 测试泳道名，从 lane_info 自动推导（来源：task_setup，使用：testing）",
    "test_env_type": "string — 测试环境类型 ppe|boe|prod（来源：task_setup，使用：testing）",
    "lane_id": "string — 泳道后缀（已去 boe_/ppe_ 前缀），传给 create_dev_task；为空走默认（来源：info_collection，使用：task_setup）",
    "user_lane_name": "string — 用户原始 env / 完整环境名，用于 task_setup 推导后对账（来源：info_collection，使用：task_setup）"
  },
  "checkpoints": {
    "execution_plan": {
      "confirmed": "boolean — 用户是否已确认执行计划",
      "confirmed_at": "string|null — 确认时间 ISO8601",
      "iterations": "number — 方案修改轮次",
      "artifact": "string — 产出文件路径（info/execution_plan.md）"
    },
    "create_params": {
      "confirmed": "boolean — 用户是否已确认创建参数",
      "confirmed_at": "string|null",
      "iterations": "number",
      "artifact": "string"
    },
    "test_plan": {
      "confirmed": "boolean — 用户是否已确认测试方案",
      "confirmed_at": "string|null",
      "iterations": "number",
      "artifact": "string — 产出文件路径（bam-query/test_plan.md）"
    },
    "dev_stage": {
      "confirmed": "boolean — 用户是否已确认通过开发阶段",
      "confirmed_at": "string|null",
      "iterations": "number",
      "artifact": "string"
    },
    "access_stage": {
      "confirmed": "boolean — 用户是否已确认通过准入阶段",
      "confirmed_at": "string|null",
      "iterations": "number",
      "artifact": "string"
    }
  },
  "history": [
    {
      "phase": "string — 所属阶段",
      "action": "string — 操作标识",
      "detail": "string — 操作详情",
      "timestamp": "string — ISO8601 时间"
    }
  ]
}
```

## 初始化模板

新会话创建 `.gdpa/{session-id}/status.json`：

```json
{
  "session_id": "sess_20260305_180000_abcd1234",
  "created_at": "2026-03-05T18:00:00+08:00",
  "requirement": "用户的需求描述",
  "current_phase": "info_collection",
  "phases": {
    "info_collection":    { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "task_setup":         { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "deploy":             { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "testing":            { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "dev_stage_pass":     { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "code_review":        { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "access_stage_pass":  { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "completion":         { "status": "pending", "started_at": null, "completed_at": null, "summary": "" }
  },
  "context": {
    "psm": "",
    "psm_list": [],
    "branch": "",
    "space_id": 0,
    "dev_task_id": null,
    "bits_link": "",
    "control_planes": [],
    "lane_info": null,
    "stages_info": null,
    "meego_url": "",
    "template_id": 0,
    "team_flow_id": 0,
    "test_vregion": [],
    "test_vdc": [],
    "test_env": "",
    "test_env_type": "",
    "lane_id": "",
    "user_lane_name": ""
  },
  "checkpoints": {
    "execution_plan":  { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" },
    "create_params":   { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" },
    "test_plan":       { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" },
    "dev_stage":       { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" },
    "access_stage":    { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" }
  },
  "history": []
}
```
