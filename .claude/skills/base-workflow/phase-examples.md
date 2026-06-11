# 各阶段产出文件与状态更新示例

每个阶段完成时需要：(1) 写入产出文件 (2) 更新 status.json。以下是各阶段的完整示例。

检查点（◆ 标记）完成时需要：(1) 展示方案并等待用户确认 (2) 写入产出文件 (3) 更新 status.json 的 checkpoints 字段和 history。

---

## Phase 0: info_collection

### ◆ 检查点产出文件 `info/execution_plan.md`

```markdown
## 📋 执行计划

基于需求分析，以下是本次研发的完整执行计划：

### 阶段概览

| # | 阶段 | 执行/跳过 | 具体内容 |
|---|------|----------|---------|
| 1 | 任务准备 | ✅ 执行 | 创建 DevFlow 任务，配置 PPE 环境 |
| 2 | 接口变更 | ✅ 执行 | 在 UserInfo 中新增 age 字段 (i32, optional) |
| 3 | 代码编写 | ✅ 执行 | 实现 GetUserAge 接口，处理 age 字段逻辑 |
| 4 | 提交部署 | ✅ 执行 | Push 到 feat/add-user-age，触发 PPE 部署 |
| 5 | 测试验证 | ✅ 执行 | 测试 GetUserInfo 接口返回 age 字段 |
| 6 | 完成收尾 | ✅ 执行 | 生成报告，发起 MR |

### 预期涉及的关键操作

1. 在 user_info.thrift 中为 UserInfo struct 新增 age 字段
2. 修改 handler.go 和 service.go 实现 age 字段的读写逻辑
3. 调用 bam-api 确认下游 UserService 是否已支持 age 字段

### 潜在风险与注意事项

- 下游 UserService 的 IDL 版本需确认是否已包含 age 字段
- age 字段为 optional，需处理缺省值情况
```

### status.json 更新（检查点确认后）

```json
{
  "current_phase": "info_collection",
  "phases": {
    "info_collection": {
      "status": "completed",
      "completed_at": "2026-02-09T14:32:00+08:00",
      "summary": "参数确认 + 执行计划确认完成 → info/task_config.json, info/execution_plan.md"
    }
  },
  "checkpoints": {
    "execution_plan": {
      "confirmed": true,
      "confirmed_at": "2026-02-09T14:32:00+08:00",
      "iterations": 1,
      "artifact": "info/execution_plan.md"
    }
  },
  "history": [
    { "phase": "info_collection", "action": "wrote_file", "detail": "info/task_config.json", "timestamp": "..." },
    { "phase": "info_collection", "action": "checkpoint_presented", "detail": "execution_plan v1", "timestamp": "..." },
    { "phase": "info_collection", "action": "checkpoint_confirmed", "detail": "execution_plan confirmed by user", "timestamp": "..." },
    { "phase": "info_collection", "action": "wrote_file", "detail": "info/execution_plan.md", "timestamp": "..." }
  ]
}
```

---

## Phase 1: task_setup

### 产出文件 `devflow/task_info.json`

```json
{
  "task_id": 366800,
  "link": "https://devflow.bytedance.net/space/1180/task/366800",
  "psm": "tiktok.xxx.service",
  "branch": "feat/xxx",
  "vregion": ["Singapore-Central", "US-East"],
  "vdc": ["sg1", "maliva"],
  "env": "ppe_xxx",
  "lanes": ["ppe_xxx"],
  "pipeline_links": ["https://devflow.bytedance.net/..."],
  "status": "OPEN",
  "created_at": "2026-02-09T14:35:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "idl_change",
  "phases": {
    "task_setup": {
      "status": "completed",
      "completed_at": "2026-02-09T14:35:00+08:00",
      "summary": "创建任务 366800，分支 feat/xxx，PPE 泳道 ppe_xxx → devflow/task_info.json"
    }
  },
  "context": {
    "psm": "tiktok.xxx.service",
    "branch": "feat/xxx",
    "vregion": ["Singapore-Central", "US-East"],
    "vdc": ["sg1", "maliva"],
    "env": "ppe_xxx",
    "task_id": 366800,
    "task_link": "https://devflow.bytedance.net/space/1180/task/366800",
    "lanes": ["ppe_xxx"],
    "pipeline_links": ["https://..."]
  },
  "history": [
    { "phase": "task_setup", "action": "created_task", "detail": "task_id=366800", "timestamp": "..." },
    { "phase": "task_setup", "action": "started_develop", "detail": "pipeline triggered", "timestamp": "..." },
    { "phase": "task_setup", "action": "wrote_file", "detail": "devflow/task_info.json", "timestamp": "..." }
  ]
}
```

---

## Phase 2: idl_change

> `edit-idl` 是编排指南，实际依次调用 `idl-pull` → 本地编辑 → `idl-commit` → `idl-codegen`。

### 产出文件 `edit-idl/diff_result.json`

```json
{
  "idl_file": "path/to/modified.thrift",
  "changes": "变更摘要：在 UserInfo 添加 age 字段(i32, optional)",
  "branch": "feat/add-user-age",
  "idl_pull": {
    "idl_dir": "/tmp/gdpa-idl/366800",
    "meta_path": "/tmp/gdpa-idl/366800/.gdpa_idl_meta.json",
    "branch_used": "feat/add-user-age",
    "files": ["user_info.thrift"]
  },
  "idl_commit": {
    "commit_id": "abc123def456",
    "commit_url": "https://code.byted.org/idl/xxx/commit/abc123def456",
    "changed_files": ["user_info.thrift"],
    "bam_version": "1.0.1"
  },
  "idl_codegen": {
    "status": "success",
    "decision_mode": "overpass",
    "repositories": ["code.byted.org/xxx/xxx"],
    "mr_links": ["https://code.byted.org/xxx/xxx/merge_requests/1"],
    "go_get_cmds": ["go get code.byted.org/xxx/xxx@feat/add-user-age"]
  },
  "completed_at": "2026-02-09T14:40:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "coding",
  "phases": {
    "idl_change": {
      "status": "completed",
      "summary": "在 UserInfo 添加 age 字段(i32), IDL 提交成功, 代码生成完成 → edit-idl/diff_result.json"
    }
  },
  "history": [
    { "phase": "idl_change", "action": "idl_pull_completed", "detail": "pulled user_info.thrift to /tmp/gdpa-idl/366800", "timestamp": "..." },
    { "phase": "idl_change", "action": "idl_edited", "detail": "added age field to UserInfo", "timestamp": "..." },
    { "phase": "idl_change", "action": "idl_commit_completed", "detail": "commit abc123def456, bam_version 1.0.1", "timestamp": "..." },
    { "phase": "idl_change", "action": "idl_codegen_completed", "detail": "codegen success via overpass", "timestamp": "..." },
    { "phase": "idl_change", "action": "wrote_file", "detail": "edit-idl/diff_result.json", "timestamp": "..." }
  ]
}
```

---

## Phase 3: coding

### ◆ 检查点产出文件 `coding/design_proposal.md`

```markdown
## 🔧 设计方案

### 实现思路
在 UserInfo 结构体中增加 Age 字段，Handler 层新增数据校验，Service 层从下游 UserService 获取 age 数据并填充。

### 修改范围

| 文件 | 修改内容 | 说明 |
|------|---------|------|
| handler.go | 新增 GetUserAge Handler | 处理新接口请求，增加参数校验 |
| service.go | 添加 age 字段处理逻辑 | 调用下游 UserService 获取 age，处理缺省值 |
| model.go | UserInfo 结构体增加 Age 字段 | 数据模型适配，Age 为 *int32 指针类型 |

### 依赖分析
- **下游服务**: UserService.GetUserDetail (已确认支持 age 字段)
- **配置依赖**: TCC enable_age_field 开关（当前值：true）
- **数据依赖**: 无新增数据库变更

### 关键设计决策

| 决策点 | 选择方案 | 理由 |
|--------|---------|------|
| age 字段类型 | *int32 (指针) | optional 字段，需区分"未设置"和"值为 0" |
| 缺省值处理 | 不返回该字段 | 与前端约定，nil 时前端不展示 |
```

### status.json 更新（检查点确认后）

```json
{
  "checkpoints": {
    "design_proposal": {
      "confirmed": true,
      "confirmed_at": "2026-02-09T14:45:00+08:00",
      "iterations": 1,
      "artifact": "coding/design_proposal.md"
    }
  },
  "history": [
    { "phase": "coding", "action": "checkpoint_presented", "detail": "design_proposal v1", "timestamp": "..." },
    { "phase": "coding", "action": "checkpoint_confirmed", "detail": "design_proposal confirmed by user", "timestamp": "..." },
    { "phase": "coding", "action": "wrote_file", "detail": "coding/design_proposal.md", "timestamp": "..." }
  ]
}
```

### 产出文件 `coding/changes.json`

```json
{
  "summary": "实现了 xxx 功能",
  "files_modified": [
    { "path": "handler.go", "action": "modified", "description": "新增 GetUserAge handler" },
    { "path": "service.go", "action": "modified", "description": "添加 age 字段处理逻辑" },
    { "path": "model.go", "action": "modified", "description": "UserInfo 结构体增加 Age 字段" }
  ],
  "skills_used": [
    { "skill": "bam-api", "purpose": "查询下游 UserService 接口定义" },
    { "skill": "tcc-query", "purpose": "确认 enable_age_field 开关状态" }
  ],
  "completed_at": "2026-02-09T15:20:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "deploy",
  "phases": {
    "coding": {
      "status": "completed",
      "summary": "实现了 xxx 功能，修改了 3 个文件 → coding/changes.json"
    }
  },
  "history": [
    { "phase": "coding", "action": "coding_completed", "detail": "3 files modified", "timestamp": "..." },
    { "phase": "coding", "action": "wrote_file", "detail": "coding/changes.json", "timestamp": "..." }
  ]
}
```

---

## Phase 4: deploy

### 产出文件 `deploy/deploy_info.json`

```json
{
  "branch": "feat/xxx",
  "commit_hash": "abc1234",
  "commit_message": "feat: add age field to UserInfo",
  "push_success": true,
  "deploy_env": "ppe_xxx",
  "deploy_status": "triggered",
  "devflow_check": {
    "task_id": 366800,
    "lanes": [
      {
        "name": "ppe_xxx",
        "pipeline_url": "https://devflow.bytedance.net/...",
        "pipeline_id": 123456
      }
    ],
    "checked_at": "2026-02-09T15:30:00+08:00"
  },
  "completed_at": "2026-02-09T15:30:00+08:00"
}
```

### status.json 更新

```json
{
  "current_phase": "testing",
  "phases": {
    "deploy": {
      "status": "completed",
      "summary": "代码已 push 到 feat/xxx (abc1234)，PPE 部署已触发 → deploy/deploy_info.json"
    }
  },
  "history": [
    { "phase": "deploy", "action": "pushed", "detail": "commit abc1234 to feat/xxx", "timestamp": "..." },
    { "phase": "deploy", "action": "deploy_triggered", "detail": "PPE deploy triggered", "timestamp": "..." },
    { "phase": "deploy", "action": "wrote_file", "detail": "deploy/deploy_info.json", "timestamp": "..." }
  ]
}
```

---

## Phase 5: testing

### ◆ 检查点产出文件 `bam-query/test_plan.md`

```markdown
## 🧪 测试方案

### 测试环境
- **Env**: ppe_xxx
- **VRegion**: Singapore-Central, US-East
- **VDC**: sg1, maliva

### 测试用例

| # | 接口/方法 | 类型 | VRegion | VDC | 测试输入 | 预期结果 |
|---|----------|------|---------|-----|---------|---------|
| 1 | GetUserInfo | 读 | Singapore-Central | sg1 | {"user_id": 123} | 返回包含 age 字段 |
| 2 | GetUserInfo | 读 | US-East | maliva | {"user_id": 123} | 同上（跨 Region 验证） |
| 3 | GetUserInfo | 读 | Singapore-Central | sg1 | {"user_id": 0} | 返回参数错误 |

### 日志验证计划
- **搜索关键字**: error, GetUserInfo, panic
- **预期结果**: 无异常错误日志
- **时间范围**: 测试请求前后 5 分钟

### 注意事项
- 所有用例均为读接口，可直接执行
- 需验证 user_id 不存在时的返回是否符合预期
```

### status.json 更新（检查点确认后）

```json
{
  "checkpoints": {
    "test_plan": {
      "confirmed": true,
      "confirmed_at": "2026-02-09T15:45:00+08:00",
      "iterations": 1,
      "artifact": "bam-query/test_plan.md"
    }
  },
  "history": [
    { "phase": "testing", "action": "checkpoint_presented", "detail": "test_plan v1", "timestamp": "..." },
    { "phase": "testing", "action": "checkpoint_confirmed", "detail": "test_plan confirmed by user", "timestamp": "..." },
    { "phase": "testing", "action": "wrote_file", "detail": "bam-query/test_plan.md", "timestamp": "..." }
  ]
}
```

### 产出文件 1 `bam-query/test_result.json`

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
      "env": "ppe_xxx",
      "request": "{\"user_id\": 123}",
      "response_code": 200,
      "response_summary": "返回正常，包含 age 字段",
      "passed": true
    },
    {
      "name": "测试 GetUserInfo 接口 (US-East/maliva)",
      "action": "rpc",
      "psm": "tiktok.xxx.service",
      "func_name": "GetUserInfo",
      "vregion": "US-East",
      "vdc": "maliva",
      "env": "ppe_xxx",
      "request": "{\"user_id\": 123}",
      "response_code": 200,
      "response_summary": "返回正常，包含 age 字段",
      "passed": true
    }
  ],
  "overall_passed": true,
  "tested_at": "2026-02-09T16:00:00+08:00"
}
```

### 产出文件 2 `argos-query/logs_summary.md`

```markdown
# Argos 日志分析摘要

- **查询时间**: 2026-02-09 15:50 ~ 16:00
- **PSM**: tiktok.xxx.service
- **关键字**: error, GetUserInfo
- **结论**: 未发现异常日志，请求正常处理
- **详细日志**: 见 argos-query/logs_raw.log
```

### 测试通过时 status.json 更新

```json
{
  "current_phase": "completion",
  "phases": {
    "testing": {
      "status": "completed",
      "summary": "接口测试通过，日志无异常 → bam-query/test_result.json, argos-query/logs_summary.md"
    }
  },
  "history": [
    { "phase": "testing", "action": "test_passed", "detail": "all test cases passed", "timestamp": "..." },
    { "phase": "testing", "action": "wrote_file", "detail": "bam-query/test_result.json", "timestamp": "..." },
    { "phase": "testing", "action": "wrote_file", "detail": "argos-query/logs_summary.md", "timestamp": "..." }
  ]
}
```

### 测试不通过时回退

```json
{
  "current_phase": "coding",
  "phases": {
    "testing": {
      "status": "failed",
      "summary": "接口返回 500，错误：xxx field not found → bam-query/test_result.json"
    },
    "coding": {
      "status": "in_progress",
      "summary": "从 testing 回退，需修复：xxx field not found"
    }
  },
  "history": [
    { "phase": "testing", "action": "test_failed", "detail": "500: xxx field not found", "timestamp": "..." },
    { "phase": "testing", "action": "wrote_file", "detail": "bam-query/test_result.json", "timestamp": "..." },
    { "phase": "testing", "action": "wrote_file", "detail": "argos-query/logs_summary.md", "timestamp": "..." },
    { "phase": "testing", "action": "rollback_to_coding", "detail": "需修复代码后重新部署测试", "timestamp": "..." }
  ]
}
```

---

## Phase 6: completion

### 产出文件 `summary/report.md` 模板

```markdown
# 研发总结

## 需求描述
{从 status.json 的 requirement 读取}

## 变更内容
- {从 coding/changes.json 的 files_modified 读取，列出每个文件的变更描述}

## IDL 变更
- {从 edit-idl/diff_result.json 读取，如 skipped 则标注"无 IDL 变更"}

## 测试结果
- {从 bam-query/test_result.json 读取测试用例和结果，如 skipped 则标注"未进行自测"}

## 部署信息
- 分支: {context.branch}
- 环境: {context.env}
- VRegion: {context.vregion}
- VDC: {context.vdc}
- DevFlow: {context.task_link}

## 关键决策
- {列出开发过程中的关键技术决策}
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
