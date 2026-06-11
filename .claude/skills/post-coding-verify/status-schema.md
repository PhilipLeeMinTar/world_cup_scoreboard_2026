# status.json 完整结构

存放路径：`.gdpa/{session-id}/status.json`

## 字段说明

```json
{
  "session_id": "string — 会话唯一标识，必须与 workflow 中所有命令显式传递的 --session-id 保持一致（直接使用 gdpa-cli create-session 返回值）",
  "created_at": "string — 创建时间 ISO8601",
  "requirement": "string — 用户需求一句话描述",
  "current_phase": "string — 当前所在阶段（info_collection|deploy|api_testing|log_verify|completion）",
  "phases": {
    "info_collection": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null — 开始时间",
      "completed_at": "string|null — 完成时间",
      "summary": "string — 该阶段执行摘要"
    },
    "deploy": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "api_testing": {
      "status": "string — pending|in_progress|completed|skipped|failed",
      "started_at": "string|null",
      "completed_at": "string|null",
      "summary": "string"
    },
    "log_verify": {
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
    "branch": "string — Git 分支名（来源：info_collection，使用：deploy）",
    "biz": "string — 业务线 Tiktok/Aweme/Devflow/Tikcast（来源：info_collection，使用：deploy）",
    "region": "string — 区域 i18n/cn（来源：info_collection，使用：deploy）",
    "env": "string — 完整环境名（泳道名，如 ppe_20260213）（来源：deploy，使用：api_testing, log_verify）",
    "vregion": ["string — 标准 VRegion 列表，如 Singapore-Central, US-East（来源：deploy，使用：api_testing, log_verify）"],
    "vdc": ["string — VDC 列表，如 sg1, maliva（来源：deploy，使用：api_testing, log_verify）"],
    "task_id": "number|null — DevFlow 任务 ID（来源：deploy，使用：log_verify, completion）",
    "task_link": "string — DevFlow 链接（来源：deploy，使用：completion）",
    "lanes": ["string — 泳道列表（来源：deploy，使用：completion）"],
    "commit_hash": "string — Push 的 commit hash（来源：deploy，使用：completion）",
    "affected_interfaces": [
      {
        "method": "string — 接口方法名",
        "type": "string — rpc/http",
        "description": "string — 接口描述"
      }
    ]
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
  "session_id": "sess_20260213_143052_abcd1234",
  "created_at": "2026-02-13T14:30:52+08:00",
  "requirement": "用户的需求描述",
  "current_phase": "info_collection",
  "phases": {
    "info_collection": { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "deploy":          { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "api_testing":     { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "log_verify":      { "status": "pending", "started_at": null, "completed_at": null, "summary": "" },
    "completion":      { "status": "pending", "started_at": null, "completed_at": null, "summary": "" }
  },
  "context": {
    "psm": "",
    "branch": "",
    "biz": "",
    "region": "i18n",
    "env": "",
    "vregion": [],
    "vdc": [],
    "task_id": null,
    "task_link": "",
    "lanes": [],
    "commit_hash": "",
    "affected_interfaces": []
  },
  "history": []
}
```
