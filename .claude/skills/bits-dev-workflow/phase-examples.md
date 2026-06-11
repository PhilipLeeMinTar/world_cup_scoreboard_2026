# 各阶段产出文件与状态更新示例

每个阶段完成时需要：(1) 写入产出文件 (2) 更新 status.json。以下是各阶段的完整示例。

检查点（◆ 标记）完成时需要：(1) 展示方案并等待用户确认 (2) 写入产出文件 (3) 更新 status.json 的 checkpoints 字段和 history。

---

## Phase 0: info_collection

### 产出文件 `info/task_config.json`

```json
{
  "psm": "tiktok.xxx.service",
  "psm_list": ["tiktok.xxx.service"],
  "psm_source": "auto_detect:script/bootstrap.sh",
  "branch": "feat/add-user-age",
  "space_id": 94017024770,
  "template_id": 26037,
  "template_name": "需求研发",
  "team_flow_id": 424660152834,
  "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119",
  "meego_source": "user_selected:meego-manage#2",
  "control_planes": ["CONTROL_PLANE_I18N"],
  "test_vregion": ["Singapore-Central"],
  "test_vdc": ["sg1"],
  "user_lane_name": "ppe_gdpa_test_event",
  "lane_id": "gdpa_test_event"
}
```

> 用户给的 env / 完整环境名记到 `user_lane_name`，去 `boe_` / `ppe_` 前缀后写入 `lane_id` 作为 `create_dev_task` 入参；用户没指定时两者都置空，走默认 `feature_${dev_task_id}`。

### ◆ 检查点产出文件 `info/execution_plan.md`

```markdown
## 📋 执行计划

### 阶段概览

| # | 阶段 | 执行/跳过 | 具体内容 |
|---|------|----------|---------|
| 0 | 信息收集 | ✅ 完成 | 参数已确认 |
| 1 | 任务准备 | ✅ 执行 | 创建 BITS 开发任务 |
| 2 | 提交部署 | ✅ 执行 | Push 到 feat/add-user-age |
| 3 | 测试验证 | ✅ 执行 | 测试 GetUserInfo 接口 |
| 4 | 开发阶段通过 | ✅ 执行 | 确认后通过 BITS 开发阶段 |
| 5 | 代码审查 | ✅ 执行 | 发起 MR + CR |
| 6 | 准入阶段通过 | ✅ 执行 | 确认后通过 BITS 准入阶段 |
| 7 | 完成收尾 | ✅ 执行 | 生成报告 |

### 预期涉及的关键操作

1. 修改 handler.go 和 service.go 实现 age 字段的读写逻辑

### 潜在风险与注意事项

- age 字段为 optional，需处理缺省值情况
```

### status.json 更新（检查点确认后）

```json
{
  "current_phase": "task_setup",
  "phases": {
    "info_collection": {
      "status": "completed",
      "completed_at": "2026-03-05T18:05:00+08:00",
      "summary": "参数确认 + 执行计划确认完成 → info/task_config.json, info/execution_plan.md"
    }
  },
  "context": {
    "psm": "tiktok.xxx.service",
    "psm_list": ["tiktok.xxx.service"],
    "branch": "feat/add-user-age",
    "space_id": 94017024770,
    "control_planes": ["CONTROL_PLANE_I18N"],
    "meego_url": "https://meego.larkoffice.com/ttarch/story/detail/6874274119",
    "template_id": 26037,
    "team_flow_id": 424660152834,
    "test_vregion": ["Singapore-Central"],
    "test_vdc": ["sg1"],
    "lane_id": "gdpa_test_event",
    "user_lane_name": "ppe_gdpa_test_event"
  },
  "checkpoints": {
    "execution_plan": {
      "confirmed": true,
      "confirmed_at": "2026-03-05T18:05:00+08:00",
      "iterations": 1,
      "artifact": "info/execution_plan.md"
    }
  },
  "history": [
    { "phase": "info_collection", "action": "auto_detect_psm", "detail": "found tiktok.xxx.service in script/bootstrap.sh", "timestamp": "..." },
    { "phase": "info_collection", "action": "meego_search", "detail": "searched user stories, found 8 items", "timestamp": "..." },
    { "phase": "info_collection", "action": "params_confirmed", "detail": "user confirmed all params in confirmation form", "timestamp": "..." },
    { "phase": "info_collection", "action": "wrote_file", "detail": "info/task_config.json", "timestamp": "..." },
    { "phase": "info_collection", "action": "checkpoint_presented", "detail": "execution_plan v1", "timestamp": "..." },
    { "phase": "info_collection", "action": "checkpoint_confirmed", "detail": "execution_plan confirmed by user", "timestamp": "..." },
    { "phase": "info_collection", "action": "wrote_file", "detail": "info/execution_plan.md", "timestamp": "..." }
  ]
}
```

---

## Phase 1: task_setup

### 产出文件 `bits-devops/task_info.json`

```json
{
  "dev_task_id": 2147497,
  "reused": false,
  "space_id": 94017024770,
  "branch": "feat/add-user-age",
  "bits_link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2147497",
  "lane_info": {
    "nodes": [
      {
        "node_id": 12345,
        "node_name": "自测",
        "node_fixed_name": "DevDevelopStageSelfTestTask",
        "env_setting": {
          "ppe": { "enabled": true, "lanes": [{"lane_id": "gdpa_test_event", "overwrite_prefix": "ppe_"}] },
          "boe": { "enabled": false }
        }
      }
    ]
  },
  "stages_info": {
    "stages": [
      {
        "name": "开发阶段",
        "fixed_name": "DevDevelopStage",
        "tasks": [
          { "type": "self_testing", "fixed_name": "DevDevelopStageSelfTestTask" },
          { "type": "rd_test", "fixed_name": "DevDevelopStageRDTestTask" }
        ]
      },
      {
        "name": "准入阶段",
        "fixed_name": "DevGatekeeperStage",
        "tasks": [
          { "type": "code_review", "fixed_name": "DevGatekeeperStageCodeReviewTask" },
          { "type": "integration_testing", "fixed_name": "DevGatekeeperStageIntegrationTestTask" }
        ]
      }
    ]
  },
  "created_at": "2026-03-05T18:10:00+08:00"
}
```

### status.json 更新（创建新任务时）

```json
{
  "current_phase": "deploy",
  "phases": {
    "task_setup": {
      "status": "completed",
      "completed_at": "2026-03-05T18:10:00+08:00",
      "summary": "创建 BITS 任务 2147497 → bits-devops/task_info.json"
    }
  },
  "context": {
    "dev_task_id": 2147497,
    "bits_link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2147497",
    "lane_info": {},
    "stages_info": {},
    "test_env": "ppe_gdpa_test_event",
    "test_env_type": "ppe",
    "lane_id": "gdpa_test_event",
    "user_lane_name": "ppe_gdpa_test_event"
  },
  "checkpoints": {
    "create_params": {
      "confirmed": true,
      "confirmed_at": "2026-03-05T18:08:00+08:00",
      "iterations": 1,
      "artifact": ""
    }
  },
  "history": [
    { "phase": "task_setup", "action": "search_existing_tasks", "detail": "found 0 tasks matching branch feat/add-user-age", "timestamp": "..." },
    { "phase": "task_setup", "action": "checkpoint_confirmed", "detail": "user chose to create new task", "timestamp": "..." },
    { "phase": "task_setup", "action": "created_bits_task", "detail": "dev_task_id=2147497, lane_id=gdpa_test_event (stripped from ppe_gdpa_test_event)", "timestamp": "..." },
    { "phase": "task_setup", "action": "lane_name_verified", "detail": "test_env=ppe_gdpa_test_event 与 user_lane_name 一致", "timestamp": "..." },
    { "phase": "task_setup", "action": "wrote_file", "detail": "bits-devops/task_info.json", "timestamp": "..." }
  ]
}
```

### status.json 更新（复用已有任务时）

```json
{
  "current_phase": "deploy",
  "phases": {
    "task_setup": {
      "status": "completed",
      "completed_at": "2026-03-05T18:10:00+08:00",
      "summary": "复用已有 BITS 任务 2147490（按分支匹配） → bits-devops/task_info.json"
    }
  },
  "context": {
    "dev_task_id": 2147490,
    "bits_link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2147490",
    "lane_info": {},
    "stages_info": {},
    "test_env": "ppe_i18n_env_feature_2147490",
    "test_env_type": "ppe"
  },
  "checkpoints": {
    "create_params": {
      "confirmed": true,
      "confirmed_at": "2026-03-05T18:08:00+08:00",
      "iterations": 1,
      "artifact": ""
    }
  },
  "history": [
    { "phase": "task_setup", "action": "search_existing_tasks", "detail": "found 1 task matching branch feat/add-user-age: [2147490]", "timestamp": "..." },
    { "phase": "task_setup", "action": "checkpoint_confirmed", "detail": "user chose to reuse task 2147490", "timestamp": "..." },
    { "phase": "task_setup", "action": "reused_bits_task", "detail": "dev_task_id=2147490", "timestamp": "..." },
    { "phase": "task_setup", "action": "wrote_file", "detail": "bits-devops/task_info.json", "timestamp": "..." }
  ]
}
```

### status.json 更新（复用任务但分支不一致 — 用户选择切换本地分支）

```json
{
  "current_phase": "deploy",
  "phases": {
    "task_setup": {
      "status": "completed",
      "completed_at": "2026-03-05T18:10:00+08:00",
      "summary": "复用 BITS 任务 2147490，分支冲突已解决（本地切换到 feat/old-branch） → bits-devops/task_info.json"
    }
  },
  "context": {
    "dev_task_id": 2147490,
    "branch": "feat/old-branch",
    "bits_link": "https://bits.bytedance.net/devops/94017024770/develop/detail/2147490",
    "lane_info": {},
    "stages_info": {},
    "test_env": "ppe_i18n_env_feature_2147490",
    "test_env_type": "ppe"
  },
  "history": [
    { "phase": "task_setup", "action": "user_provided_task", "detail": "dev_task_id=2147490, task_branch=feat/old-branch", "timestamp": "..." },
    { "phase": "task_setup", "action": "branch_mismatch", "detail": "task_branch=feat/old-branch vs local_branch=feat/add-user-age", "timestamp": "..." },
    { "phase": "task_setup", "action": "branch_conflict_resolved", "detail": "user chose option 2: switch local branch to feat/old-branch", "timestamp": "..." },
    { "phase": "task_setup", "action": "reused_bits_task", "detail": "dev_task_id=2147490", "timestamp": "..." },
    { "phase": "task_setup", "action": "wrote_file", "detail": "bits-devops/task_info.json", "timestamp": "..." }
  ]
}
```

---

## Phase 2: deploy

### 产出文件 `deploy/deploy_info.json`

```json
{
  "branch": "feat/add-user-age",
  "commit_hash": "abc1234",
  "commit_message": "feat: add age field to UserInfo",
  "push_success": true,
  "pipeline": {
    "task_name": "DevDevelopStageSelfTestTask",
    "status": "SUCCESS",
    "control_planes": ["CONTROL_PLANE_I18N"],
    "pipeline_id": 12345,
    "pipeline_run_id": 1123659494658,
    "pipeline_run_url": "https://bits.bytedance.net/pipeline/run/1123659494658",
    "time_cost_sec": 320,
    "jobs": [
      { "job_name": "SCM编译", "job_status": "SUCCEEDED", "time_cost_sec": 120 },
      { "job_name": "部署PPE", "job_status": "SUCCEEDED", "time_cost_sec": 180 },
      { "job_name": "冒烟测试", "job_status": "SUCCEEDED", "time_cost_sec": 20 }
    ]
  },
  "completed_at": "2026-03-05T19:15:00+08:00"
}
```

### 流水线失败时的产出文件示例

```json
{
  "branch": "feat/add-user-age",
  "commit_hash": "abc1234",
  "commit_message": "feat: add age field to UserInfo",
  "push_success": true,
  "pipeline": {
    "task_name": "DevDevelopStageSelfTestTask",
    "status": "FAILED",
    "control_planes": ["CONTROL_PLANE_I18N"],
    "pipeline_run_id": 1123659494658,
    "pipeline_run_url": "https://bits.bytedance.net/pipeline/run/1123659494658",
    "time_cost_sec": 150,
    "fail_reason": "Job SCM编译 failed: build version failed",
    "jobs": [
      { "job_name": "SCM编译", "job_status": "FAILED", "time_cost_sec": 150, "fail_reason": "build version failed", "fail_type": 1 },
      { "job_name": "部署PPE", "job_status": "CANCELLED", "time_cost_sec": 0 }
    ]
  },
  "completed_at": "2026-03-05T19:15:00+08:00"
}
```

### status.json 更新（成功时）

```json
{
  "current_phase": "testing",
  "phases": {
    "deploy": {
      "status": "completed",
      "summary": "代码已 push (abc1234)，自测流水线 SUCCESS (耗时 320s) → deploy/deploy_info.json"
    }
  },
  "history": [
    { "phase": "deploy", "action": "pushed", "detail": "commit abc1234 to feat/add-user-age", "timestamp": "..." },
    { "phase": "deploy", "action": "pipeline_triggered", "detail": "DevDevelopStageSelfTestTask", "timestamp": "..." },
    { "phase": "deploy", "action": "pipeline_completed", "detail": "STATUS=SUCCESS, 3 jobs all passed, 320s", "timestamp": "..." },
    { "phase": "deploy", "action": "wrote_file", "detail": "deploy/deploy_info.json", "timestamp": "..." }
  ]
}
```

### status.json 更新（流水线失败时重新部署）

```json
{
  "current_phase": "deploy",
  "phases": {
    "deploy": {
      "status": "failed",
      "summary": "自测流水线 FAILED: SCM编译失败 (build version failed) → deploy/deploy_info.json"
    }
  },
  "history": [
    { "phase": "deploy", "action": "pushed", "detail": "commit abc1234 to feat/add-user-age", "timestamp": "..." },
    { "phase": "deploy", "action": "pipeline_triggered", "detail": "DevDevelopStageSelfTestTask", "timestamp": "..." },
    { "phase": "deploy", "action": "pipeline_failed", "detail": "SCM编译 FAILED: build version failed", "timestamp": "..." },
    { "phase": "deploy", "action": "wrote_file", "detail": "deploy/deploy_info.json", "timestamp": "..." },
    { "phase": "deploy", "action": "retry_needed", "detail": "需修复编译错误后重新部署", "timestamp": "..." }
  ]
}
```

---

## Phase 3: testing

### ◆ 检查点产出文件 `bam-query/test_plan.md`

```markdown
## 🧪 测试方案

### 测试环境（Phase 0/1 已确认）
- **控制面**: CONTROL_PLANE_I18N
- **VRegion**: Singapore-Central（Phase 0 确认）
- **VDC**: sg1（Phase 0 确认）
- **Env（泳道名）**: ppe_i18n_env_feature_2147497（Phase 1 从 lane_info 推导）
- **Env Type**: ppe

### 测试用例

| # | 接口/方法 | 类型 | VRegion | VDC | Env | 测试输入 | 预期结果 |
|---|----------|------|---------|-----|-----|---------|---------|
| 1 | GetUserInfo | 读 | Singapore-Central | sg1 | ppe_i18n_env_feature_2147497 | {"user_id": 123} | 返回包含 age 字段 |
| 2 | GetUserInfo | 读 | Singapore-Central | sg1 | ppe_i18n_env_feature_2147497 | {"user_id": 0} | 返回参数错误 |

### 日志验证计划
- **查询模式**: Local File（PPE 测试优先）
- **Env**: ppe_i18n_env_feature_2147497
- **Env Type**: ppe
- **搜索关键字**: error, GetUserInfo
- **预期结果**: 无异常错误日志
```

### 产出文件 `bam-query/test_result.json`

```json
{
  "test_cases": [
    {
      "name": "测试 GetUserInfo 接口 (Singapore-Central/sg1)",
      "action": "rpc",
      "psm": "tiktok.xxx.service",
      "func_name": "GetUserInfo",
      "vregion": "Singapore-Central",
      "vdc": "sg1",
      "env": "ppe_i18n_env_feature_2147497",
      "request": "{\"user_id\": 123}",
      "response_code": 200,
      "response_summary": "返回正常，包含 age 字段",
      "passed": true
    }
  ],
  "overall_passed": true,
  "tested_at": "2026-03-05T19:30:00+08:00"
}
```

### 产出文件 `argos-query/logs_summary.md`

```markdown
# Argos 日志分析摘要

- **查询时间**: 2026-03-05 19:25 ~ 19:35
- **PSM**: tiktok.xxx.service
- **关键字**: error, GetUserInfo
- **结论**: 未发现异常日志
```

### 测试通过时 status.json 更新

```json
{
  "current_phase": "dev_stage_pass",
  "phases": {
    "testing": {
      "status": "completed",
      "summary": "接口测试通过 (env=ppe_i18n_env_feature_2147497)，日志无异常 → bam-query/test_result.json, argos-query/logs_summary.md"
    }
  },
  "checkpoints": {
    "test_plan": {
      "confirmed": true,
      "confirmed_at": "2026-03-05T19:25:00+08:00",
      "iterations": 1,
      "artifact": "bam-query/test_plan.md"
    }
  }
}
```

### 测试不通过时回退

```json
{
  "current_phase": "deploy",
  "phases": {
    "testing": {
      "status": "failed",
      "summary": "接口返回 500: field not found → bam-query/test_result.json"
    },
    "deploy": {
      "status": "in_progress",
      "summary": "从 testing 回退，需修复代码后重新部署"
    }
  },
  "history": [
    { "phase": "testing", "action": "test_failed", "detail": "500: field not found", "timestamp": "..." },
    { "phase": "testing", "action": "rollback_to_deploy", "detail": "需修复代码后重新部署测试", "timestamp": "..." }
  ]
}
```

---

## Phase 4: dev_stage_pass

### 产出文件 `bits-devops/dev_stage_pass.json`

```json
{
  "dev_task_id": 2147497,
  "stage_action": "pass_development_stage",
  "rd_test_pipeline": {
    "task_name": "DevDevelopStageRDTestTask",
    "status": "SUCCESS",
    "pipeline_run_id": 1123659494700,
    "pipeline_run_url": "https://bits.bytedance.net/pipeline/run/1123659494700",
    "time_cost_sec": 180,
    "jobs": [
      { "job_name": "提测检查", "job_status": "SUCCEEDED", "time_cost_sec": 30 },
      { "job_name": "环境部署", "job_status": "SUCCEEDED", "time_cost_sec": 150 }
    ]
  },
  "pipelines_by_task": {
    "DevDevelopStage/DevDevelopStageSelfTestTask": [
      { "control_plane": "CONTROL_PLANE_I18N", "status": "SUCCEEDED", "is_main_pipeline": true }
    ],
    "DevDevelopStage/DevDevelopStageRDTestTask": [
      { "control_plane": "CONTROL_PLANE_I18N", "status": "SUCCEEDED", "is_main_pipeline": true }
    ]
  },
  "stages_snapshot": {
    "development": { "status": "passed" },
    "gatekeeper": { "status": "pending" }
  },
  "passed_at": "2026-03-05T19:45:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "code_review",
  "phases": {
    "dev_stage_pass": {
      "status": "completed",
      "summary": "开发阶段已通过，提测流水线 SUCCESS (180s) → bits-devops/dev_stage_pass.json"
    }
  },
  "checkpoints": {
    "dev_stage": {
      "confirmed": true,
      "confirmed_at": "2026-03-05T19:45:00+08:00",
      "iterations": 1,
      "artifact": "bits-devops/dev_stage_pass.json"
    }
  },
  "history": [
    { "phase": "dev_stage_pass", "action": "pipeline_triggered", "detail": "DevDevelopStageRDTestTask", "timestamp": "..." },
    { "phase": "dev_stage_pass", "action": "pipeline_completed", "detail": "DevDevelopStageRDTestTask SUCCESS, 180s", "timestamp": "..." },
    { "phase": "dev_stage_pass", "action": "checkpoint_confirmed", "detail": "user confirmed pass_development_stage", "timestamp": "..." },
    { "phase": "dev_stage_pass", "action": "stage_passed", "detail": "pass_development_stage SUCCESS", "timestamp": "..." },
    { "phase": "dev_stage_pass", "action": "wrote_file", "detail": "bits-devops/dev_stage_pass.json", "timestamp": "..." }
  ]
}
```

---

## Phase 5: code_review

### 产出文件 `code-review/review_info.json`

```json
{
  "mr_link": "https://code.byted.org/tiktok/xxx-service/merge_requests/123",
  "mr_title": "feat: add age field to UserInfo",
  "review_pipeline": {
    "task_name": "DevGatekeeperStageCodeReviewTask",
    "status": "SUCCESS",
    "pipeline_run_id": 1123659494800,
    "pipeline_run_url": "https://bits.bytedance.net/pipeline/run/1123659494800",
    "time_cost_sec": 90,
    "jobs": [
      { "job_name": "代码审查检查", "job_status": "SUCCEEDED", "time_cost_sec": 60 },
      { "job_name": "合规扫描", "job_status": "SUCCEEDED", "time_cost_sec": 30 }
    ]
  },
  "reviews": [
    {
      "reviewer": "zhangsan",
      "status": "approved"
    }
  ],
  "completed_at": "2026-03-05T20:00:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "access_stage_pass",
  "phases": {
    "code_review": {
      "status": "completed",
      "summary": "MR 已创建，CR 流水线 SUCCESS (90s) → code-review/review_info.json"
    }
  },
  "history": [
    { "phase": "code_review", "action": "mr_created", "detail": "MR #123", "timestamp": "..." },
    { "phase": "code_review", "action": "pipeline_triggered", "detail": "DevGatekeeperStageCodeReviewTask", "timestamp": "..." },
    { "phase": "code_review", "action": "pipeline_completed", "detail": "DevGatekeeperStageCodeReviewTask SUCCESS, 90s", "timestamp": "..." },
    { "phase": "code_review", "action": "wrote_file", "detail": "code-review/review_info.json", "timestamp": "..." }
  ]
}
```

---

## Phase 6: access_stage_pass

### 产出文件 `bits-devops/access_stage_pass.json`

```json
{
  "dev_task_id": 2147497,
  "stage_action": "pass_access_stage",
  "stages_snapshot": {
    "development": { "status": "passed" },
    "gatekeeper": { "status": "passed" }
  },
  "passed_at": "2026-03-05T20:10:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "completion",
  "phases": {
    "access_stage_pass": {
      "status": "completed",
      "summary": "准入阶段已通过 → bits-devops/access_stage_pass.json"
    }
  },
  "checkpoints": {
    "access_stage": {
      "confirmed": true,
      "confirmed_at": "2026-03-05T20:10:00+08:00",
      "iterations": 1,
      "artifact": "bits-devops/access_stage_pass.json"
    }
  },
  "history": [
    { "phase": "access_stage_pass", "action": "checkpoint_confirmed", "detail": "user confirmed pass_access_stage", "timestamp": "..." },
    { "phase": "access_stage_pass", "action": "stage_passed", "detail": "pass_access_stage SUCCESS", "timestamp": "..." },
    { "phase": "access_stage_pass", "action": "wrote_file", "detail": "bits-devops/access_stage_pass.json", "timestamp": "..." }
  ]
}
```

---

## Phase 7: completion

### 产出文件 `summary/report.md`

```markdown
# 研发总结

## 需求描述
为 UserInfo 新增 age 字段

## 变更内容
- handler.go: 新增参数校验
- service.go: 添加 age 处理逻辑

## 测试结果
- 接口测试: 全部通过
- 日志检查: 无异常

## BITS 任务信息
- BITS 任务 ID: 2147497
- BITS 链接: https://bits.bytedance.net/devops/94017024770/develop/detail/2147497
- 开发阶段: ✅ 已通过
- 准入阶段: ✅ 已通过
- MR: https://code.byted.org/tiktok/xxx-service/merge_requests/123

## 后续操作
- 发布单流程请在 BITS 平台上继续驱动
```

### status.json 更新

```json
{
  "current_phase": "completion",
  "phases": {
    "completion": {
      "status": "completed",
      "summary": "需求完成，报告已生成 → summary/report.md"
    }
  },
  "history": [
    { "phase": "completion", "action": "wrote_file", "detail": "summary/report.md", "timestamp": "..." },
    { "phase": "completion", "action": "workflow_completed", "detail": "all phases done", "timestamp": "..." }
  ]
}
```
