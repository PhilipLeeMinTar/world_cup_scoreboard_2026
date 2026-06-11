# status.json 完整结构

存放路径：`.gdpa/{session-id}/status.json`

## 字段说明

```json
{
  "session_id": "string — 会话唯一标识，必须与 workflow 中所有命令显式传递的 --session-id 保持一致（直接使用 gdpa-cli create-session 返回值）",
  "created_at": "string — 创建时间 ISO8601",
  "requirement": "string — 用户需求一句话描述",
  "current_phase": "string — 当前所在阶段（task_setup|idl_change|coding|deploy|testing|completion）",
  "phases": {
    "<phase_name>": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null — 开始时间",
      "completed_at": "string|null — 完成时间",
      "summary": "string — 该阶段执行摘要"
    }
  },
  "context": {
    "psm": "string — 服务 PSM",
    "branch": "string — Git 分支名",
    "vregion": ["string — 标准 VRegion 列表，取自 devflow develop_detail 的 VRegion 字段。标准值: Singapore-Central, US-East, China-North, China-BOE, US-BOE"],
    "vdc": ["string — VDC 列表，取自 devflow develop_detail 的 VDC 字段。如: sg1, maliva, lf, boe, boei18n"],
    "env": "string — 完整环境名（即泳道名），取自 devflow develop_detail 的 Env 字段。如: ppe_20260211, boe_20260211（不是 ppe 或 boe）",
    "task_id": "number|null — DevFlow 任务 ID",
    "task_link": "string — DevFlow 链接",
    "lanes": ["string — 泳道列表"],
    "pipeline_links": ["string — 流水线链接"]
  },
  "checkpoints": {
    "execution_plan": {
      "confirmed": "boolean — 用户是否已确认执行计划",
      "confirmed_at": "string|null — 确认时间 ISO8601",
      "iterations": "number — 方案修改轮次（首次确认为 1，每次修改后重新确认 +1）",
      "artifact": "string — 产出文件路径（info/execution_plan.md）"
    },
    "design_proposal": {
      "confirmed": "boolean — 用户是否已确认设计方案",
      "confirmed_at": "string|null — 确认时间 ISO8601",
      "iterations": "number — 方案修改轮次",
      "artifact": "string — 产出文件路径（coding/design_proposal.md）"
    },
    "test_plan": {
      "confirmed": "boolean — 用户是否已确认测试方案",
      "confirmed_at": "string|null — 确认时间 ISO8601",
      "iterations": "number — 方案修改轮次",
      "artifact": "string — 产出文件路径（bam-query/test_plan.md）"
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

新会话时创建 `.gdpa/{session-id}/status.json`：

```json
{
  "session_id": "sess_20260209_143052_abcd1234",
  "created_at": "2026-02-09T14:30:52+08:00",
  "requirement": "用户的需求描述",
  "current_phase": "task_setup",
  "phases": {
    "task_setup":  { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "idl_change":  { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "coding":      { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "deploy":      { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "testing":     { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "completion":  { "status": "pending", "started_at": null, "completed_at": null, "summary": "" }
  },
  "context": {
    "psm": "",
    "branch": "",
    "vregion": [],
    "vdc": [],
    "env": "",
    "task_id": null,
    "task_link": "",
    "lanes": [],
    "pipeline_links": []
  },
  "checkpoints": {
    "execution_plan": { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" },
    "design_proposal": { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" },
    "test_plan": { "confirmed": false, "confirmed_at": null, "iterations": 0, "artifact": "" }
  },
  "history": []
}
```
