# BITS DevOps 常用流程

## 流水线失败排查流程

当开发任务的流水线失败时，按以下步骤追踪根因：

### 1. 查看任务当前阶段状态

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_stages",
  "dev_task_id": <dev_task_id>}'
```

确认哪个阶段处于 `failed` 状态（如测试阶段 `DevGatekeeperStage`）。

### 2. 获取流水线列表，找到失败的 pipeline_run_id

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_dev_task_pipelines",
  "dev_task_id": <dev_task_id>}'
```

从返回中找到 `status` 为 `FAILED` 的流水线，记下 `pipeline_run_id`。

注意：一个阶段通常有**主流水线**（`is_main_pipeline: true`）和**项目流水线**（关联具体 PSM）。主流水线失败往往是因为子流水线（项目流水线）失败触发的。

### 3. 查看流水线运行详情，定位失败 Job

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_pipeline_run",
  "pipeline_run_id": <pipeline_run_id>}'
```

返回结果中的 `jobs[]` 列出每个 Job 的状态。找到 `job_status` 为失败的 Job，查看其 `fail_reason`。

### 4. 追踪子流水线（如果主流水线因子流水线失败）

如果主流水线的失败 Job 的 `fail_reason` 中包含 `driven_pipeline_run_id`，说明是子流水线失败导致的。用该 ID 继续查询：

```bash
gdpa-cli run bits-devops --session-id <sid> --input '{
  "action": "get_pipeline_run",
  "pipeline_run_id": <driven_pipeline_run_id>}'
```

在子流水线的 Jobs 中找到真正失败的步骤（如 SCM 编译、部署等）和具体错误信息。

### 常见失败原因

| 失败 Job | 常见原因 |
|----------|---------|
| SCM编译 | 代码编译错误（`build version failed`），需检查代码 |
| 部署 BOE/PPE | 部署超时或资源不足 |
| 子流水线状态失败 | 主流水线检测到子流水线失败，需查子流水线详情 |
