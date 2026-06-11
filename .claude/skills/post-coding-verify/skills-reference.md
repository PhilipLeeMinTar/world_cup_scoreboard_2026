# 可用 Skill 速查与选择指南

> **重要**：在调用任何 Skill 前，**必须先阅读对应的 Skill** 获取完整的参数说明、输入输出格式和使用示例。
> **Workflow Session 约束**：本文件中的所有 `gdpa-cli run` 示例在实际执行时都应显式追加同一个 `--session-id <sid>`。CLI 不再全局强制，但 post-coding-verify 需要依赖它串联 `.gdpa/{session-id}/status.json`、恢复进度和排障信息。

## Skill 速查表

| 阶段 | Skill | 说明 | 典型场景 |
|------|-------|------|---------|
| info_collection | `repotalk` | 代码仓库智能查询 | 语义搜索变更涉及的接口 |
| info_collection | `bam-api` | 查询 API 接口定义 | 获取接口 Schema（方法名、请求/响应结构） |
| deploy | `devflow` | DevFlow 任务生命周期 | 创建任务、启动调试、确认部署状态 |
| api_testing | `bam-query` | BAM 接口测试 | 发送 RPC/HTTP 测试请求 |
| log_verify | `argos-query` | Argos 日志查询 | 按 PSM/关键字/时间范围搜索日志 |

## Skill 选择决策指南

```
需要分析代码变更检测受影响接口？
  └─ repotalk (search_nodes) → 语义搜索变更相关代码

需要获取接口的请求/响应 Schema？
  ├─ 知道 PSM → bam-api (get_api_service_list → get_api_definition_info)
  └─ 不知道 PSM → bam-api (get_api_definition_info_without_psm)

需要创建/管理 DevFlow 任务？
  └─ devflow（create → develop → develop-detail → check）

需要测试接口（发送 RPC/HTTP 请求）？
  └─ bam-query（vregion 用标准值如 Singapore-Central，env 用完整泳道名）

需要查询/分析服务日志？
  └─ argos-query（按 PSM/关键字/时间范围搜索）
```

## 关键阶段 Skill 调用示例

### info_collection 阶段

**repotalk — 语义搜索变更涉及的接口**

```bash
gdpa-cli run repotalk --input '{"action": "search_nodes", "question": "GetUserInfo handler implementation", "repo_names": "tiktok/gdpa-myservice"}'
```

**bam-api — 获取接口定义**

```bash
# 获取服务的接口列表
gdpa-cli run bam-api --input '{"action": "get_api_service_list", "psm": "tiktok.gdpa.myservice"}'

# 获取具体接口定义（含请求/响应 Schema）
gdpa-cli run bam-api --input '{"action": "get_api_definition_info", "psm": "tiktok.gdpa.myservice", "method": "GetUserInfo"}'
```

### deploy 阶段

**devflow — 创建任务并部署**

```bash
# 创建任务
gdpa-cli run devflow --input '{"action": "create", "psm": "tiktok.gdpa.myservice", "branch": "feature/add-user-age", "biz": "Tiktok", "env": "ppe", "region": "i18n"}'

# 启动开发调试
gdpa-cli run devflow --input '{"action": "develop", "task_id": 366800}'

# 获取部署详情（提取 env/vregion/vdc）
gdpa-cli run devflow --input '{"action": "develop-detail", "task_id": 366800}'
```

### api_testing 阶段

**bam-query — 接口测试**

> **重要**：`vregion` 必须使用标准值，`env` 使用完整泳道名。所有参数从 `status.json` 的 `context` 读取。

```bash
# RPC 接口测试
gdpa-cli run bam-query --input '{"action": "rpc", "psm": "tiktok.gdpa.myservice", "func_name": "GetUserInfo", "request": "{\"user_id\": 123}", "vregion": "Singapore-Central", "env": "ppe_20260213", "vdc": "sg1"}'
```

| 参数 | 来源 | 示例值 |
|------|------|--------|
| `vregion` | `context.vregion[i]` | `Singapore-Central`（不是 `sg`） |
| `vdc` | `context.vdc[i]` | `sg1`（不是 `sg`） |
| `env` | `context.env` | `ppe_20260213`（不是 `ppe`） |

### log_verify 阶段

**argos-query — 日志查询**

```bash
gdpa-cli run argos-query --input '{"action": "search", "psm": "tiktok.gdpa.myservice", "keyword": "error", "start_time": "2026-02-13T14:55:00+08:00", "end_time": "2026-02-13T15:05:00+08:00", "vregion": "Singapore-Central"}'
```

> **注意**：Argos 日志可能有 1-5 分钟延迟。首次查询未找到时等待 30-60 秒后重试。
