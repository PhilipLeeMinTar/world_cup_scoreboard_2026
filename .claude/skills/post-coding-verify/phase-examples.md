# 各阶段产出文件与状态更新示例

每个阶段完成时需要：(1) 写入产出文件 (2) 更新 status.json。以下是各阶段的完整示例。

---

## Phase 0: info_collection

### 产出文件 `info/task_config.json`

```json
{
  "psm": "tiktok.gdpa.myservice",
  "branch": "feature/add-user-age",
  "biz": "Tiktok",
  "region": "i18n",
  "affected_interfaces": [
    {
      "method": "GetUserInfo",
      "type": "rpc",
      "description": "获取用户信息，新增 age 字段返回"
    },
    {
      "method": "UpdateUserProfile",
      "type": "rpc",
      "description": "更新用户资料，新增 age 字段写入"
    }
  ],
  "changed_files": [
    "handler/get_user_info.go",
    "handler/update_user_profile.go",
    "model/user.go"
  ],
  "confirmed_at": "2026-02-13T14:35:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "deploy",
  "phases": {
    "info_collection": {
      "status": "completed",
      "completed_at": "2026-02-13T14:35:00+08:00",
      "summary": "确认 PSM tiktok.gdpa.myservice，分支 feature/add-user-age，检测到 2 个变更接口 → info/task_config.json"
    }
  },
  "context": {
    "psm": "tiktok.gdpa.myservice",
    "branch": "feature/add-user-age",
    "biz": "Tiktok",
    "region": "i18n",
    "affected_interfaces": [
      { "method": "GetUserInfo", "type": "rpc", "description": "获取用户信息" },
      { "method": "UpdateUserProfile", "type": "rpc", "description": "更新用户资料" }
    ]
  },
  "history": [
    { "phase": "info_collection", "action": "branch_checked", "detail": "使用现有分支 feature/add-user-age", "timestamp": "..." },
    { "phase": "info_collection", "action": "interfaces_detected", "detail": "检测到 GetUserInfo, UpdateUserProfile", "timestamp": "..." },
    { "phase": "info_collection", "action": "user_confirmed", "detail": "用户确认信息", "timestamp": "..." },
    { "phase": "info_collection", "action": "wrote_file", "detail": "info/task_config.json", "timestamp": "..." }
  ]
}
```

---

## Phase 1: deploy

### 产出文件 `deploy/deploy_info.json`

```json
{
  "branch": "feature/add-user-age",
  "commit_hash": "abc1234",
  "commit_message": "feat: add age field to user profile",
  "push_success": true,
  "task_id": 366800,
  "task_link": "https://devflow.bytedance.net/space/1180/task/366800",
  "deploy_env": "ppe_20260213",
  "vregion": ["Singapore-Central", "US-East"],
  "vdc": ["sg1", "maliva"],
  "lanes": ["ppe_20260213"],
  "pipeline_links": ["https://devflow.bytedance.net/..."],
  "deploy_status": "success",
  "completed_at": "2026-02-13T14:45:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "api_testing",
  "phases": {
    "deploy": {
      "status": "completed",
      "completed_at": "2026-02-13T14:45:00+08:00",
      "summary": "代码已 push (abc1234)，任务 366800 已创建，PPE 部署成功 → deploy/deploy_info.json"
    }
  },
  "context": {
    "env": "ppe_20260213",
    "vregion": ["Singapore-Central", "US-East"],
    "vdc": ["sg1", "maliva"],
    "task_id": 366800,
    "task_link": "https://devflow.bytedance.net/space/1180/task/366800",
    "lanes": ["ppe_20260213"],
    "commit_hash": "abc1234"
  },
  "history": [
    { "phase": "deploy", "action": "pushed", "detail": "commit abc1234 to feature/add-user-age", "timestamp": "..." },
    { "phase": "deploy", "action": "task_created", "detail": "task_id=366800", "timestamp": "..." },
    { "phase": "deploy", "action": "deploy_success", "detail": "PPE deployment confirmed", "timestamp": "..." },
    { "phase": "deploy", "action": "wrote_file", "detail": "deploy/deploy_info.json", "timestamp": "..." }
  ]
}
```

---

## Phase 2: api_testing

### 产出文件 `testing/test_result.json`

```json
{
  "test_cases": [
    {
      "name": "测试 GetUserInfo (Singapore-Central/sg1)",
      "action": "rpc",
      "psm": "tiktok.gdpa.myservice",
      "func_name": "GetUserInfo",
      "vregion": "Singapore-Central",
      "vdc": "sg1",
      "env": "ppe_20260213",
      "request": "{\"user_id\": 123}",
      "response_code": 200,
      "response_summary": "返回正常，包含 age 字段",
      "passed": true
    },
    {
      "name": "测试 GetUserInfo (US-East/maliva)",
      "action": "rpc",
      "psm": "tiktok.gdpa.myservice",
      "func_name": "GetUserInfo",
      "vregion": "US-East",
      "vdc": "maliva",
      "env": "ppe_20260213",
      "request": "{\"user_id\": 123}",
      "response_code": 200,
      "response_summary": "返回正常，包含 age 字段",
      "passed": true
    },
    {
      "name": "测试 UpdateUserProfile (Singapore-Central/sg1)",
      "action": "rpc",
      "psm": "tiktok.gdpa.myservice",
      "func_name": "UpdateUserProfile",
      "vregion": "Singapore-Central",
      "vdc": "sg1",
      "env": "ppe_20260213",
      "request": "{\"user_id\": 123, \"age\": 25}",
      "response_code": 200,
      "response_summary": "更新成功",
      "passed": true,
      "note": "写接口，用户已授权测试"
    }
  ],
  "overall_passed": true,
  "tested_at": "2026-02-13T15:00:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "log_verify",
  "phases": {
    "api_testing": {
      "status": "completed",
      "completed_at": "2026-02-13T15:00:00+08:00",
      "summary": "3 个测试用例全部通过（2 VRegion × 2 接口，写接口仅测 sg1） → testing/test_result.json"
    }
  },
  "history": [
    { "phase": "api_testing", "action": "test_passed", "detail": "3/3 test cases passed", "timestamp": "..." },
    { "phase": "api_testing", "action": "wrote_file", "detail": "testing/test_result.json", "timestamp": "..." }
  ]
}
```

---

## Phase 3: log_verify

### 产出文件 1 `logs/verify_result.json`

```json
{
  "query_time_range": "2026-02-13T14:55:00+08:00 ~ 2026-02-13T15:05:00+08:00",
  "psm": "tiktok.gdpa.myservice",
  "keywords_searched": ["error", "panic", "GetUserInfo", "UpdateUserProfile"],
  "vregions_checked": ["Singapore-Central", "US-East"],
  "findings": {
    "errors_found": 0,
    "panics_found": 0,
    "request_logs_found": true,
    "anomalies": []
  },
  "conclusion": "pass",
  "verified_at": "2026-02-13T15:10:00+08:00"
}
```

### 产出文件 2 `logs/logs_summary.md`

```markdown
# Argos 日志分析摘要

- **查询时间**: 2026-02-13 14:55 ~ 15:05
- **PSM**: tiktok.gdpa.myservice
- **关键字**: error, panic, GetUserInfo, UpdateUserProfile
- **VRegion**: Singapore-Central, US-East
- **结论**: 未发现异常日志，GetUserInfo 和 UpdateUserProfile 请求正常处理
- **详细日志**: 见 logs/logs_raw.log
```

### 验证通过时 status.json 更新

```json
{
  "current_phase": "completion",
  "phases": {
    "log_verify": {
      "status": "completed",
      "completed_at": "2026-02-13T15:10:00+08:00",
      "summary": "日志无异常，请求链路正常 → logs/verify_result.json, logs/logs_summary.md"
    }
  },
  "history": [
    { "phase": "log_verify", "action": "logs_queried", "detail": "queried Singapore-Central, US-East", "timestamp": "..." },
    { "phase": "log_verify", "action": "verify_passed", "detail": "no errors, no panics", "timestamp": "..." },
    { "phase": "log_verify", "action": "wrote_file", "detail": "logs/verify_result.json", "timestamp": "..." },
    { "phase": "log_verify", "action": "wrote_file", "detail": "logs/logs_summary.md", "timestamp": "..." }
  ]
}
```

### 发现问题 + 用户选择重测时回退

```json
{
  "current_phase": "api_testing",
  "phases": {
    "log_verify": {
      "status": "failed",
      "summary": "发现 3 条 ERROR 日志: NullPointerException in GetUserInfo → logs/verify_result.json"
    },
    "api_testing": {
      "status": "in_progress",
      "summary": "从 log_verify 回退，需排查 GetUserInfo 的 NPE 问题后重新测试"
    }
  },
  "history": [
    { "phase": "log_verify", "action": "verify_failed", "detail": "3 errors found: NPE in GetUserInfo", "timestamp": "..." },
    { "phase": "log_verify", "action": "wrote_file", "detail": "logs/verify_result.json", "timestamp": "..." },
    { "phase": "log_verify", "action": "wrote_file", "detail": "logs/logs_summary.md", "timestamp": "..." },
    { "phase": "log_verify", "action": "rollback_to_api_testing", "detail": "用户选择重测", "timestamp": "..." }
  ]
}
```

---

## Phase 4: completion

### 产出文件 `summary/report.md`

```markdown
# 编码后验证报告

## 需求描述
为用户资料添加 age 字段

## 部署信息
- 分支: feature/add-user-age
- Commit: abc1234
- 环境: ppe_20260213
- VRegion: Singapore-Central, US-East
- VDC: sg1, maliva
- DevFlow: https://devflow.bytedance.net/space/1180/task/366800

## 接口测试结果

| 接口 | VRegion | VDC | 状态 | 响应码 | 备注 |
|------|---------|-----|------|--------|------|
| GetUserInfo | Singapore-Central | sg1 | PASS | 200 | 包含 age 字段 |
| GetUserInfo | US-East | maliva | PASS | 200 | 包含 age 字段 |
| UpdateUserProfile | Singapore-Central | sg1 | PASS | 200 | 写接口，已授权 |

## 日志验证
- 查询时间: 2026-02-13 14:55 ~ 15:05
- 结论: 未发现异常日志，请求链路正常

## 结论
全部验证通过，可进入 Code Review 阶段。
```

### status.json 更新

```json
{
  "current_phase": "completion",
  "phases": {
    "completion": {
      "status": "completed",
      "completed_at": "2026-02-13T15:15:00+08:00",
      "summary": "验证报告已生成 → summary/report.md"
    }
  },
  "history": [
    { "phase": "completion", "action": "wrote_file", "detail": "summary/report.md", "timestamp": "..." },
    { "phase": "completion", "action": "workflow_completed", "detail": "all phases done", "timestamp": "..." }
  ]
}
```
