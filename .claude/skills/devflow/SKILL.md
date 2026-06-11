---
name: devflow
description: Use when creating, querying, starting, closing, or managing IDL path bindings for DevFlow tasks.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# DevFlow 任务管理工具

DevFlow 是 ByteDance 的开发流程管理平台。gdpa-cli 提供了完整的 DevFlow 任务生命周期管理命令。

## 快速开始

### 前置条件

所有 DevFlow 命令需要先登录 ByteCloud 获取认证凭证：

```bash
# 登录（默认同时登录 cn 和 i18n）
gdpa-cli login

# 或指定区域
gdpa-cli login cn      # 仅登录 cn
gdpa-cli login i18n    # 仅登录 i18n
```

## 命令概览

| 命令 | 别名 | 功能 | 示例 |
|------|------|------|------|
| `list` | `ls` | 列出任务 | `devflow list --psm xxx` |
| `info` | - | 查看详情 | `devflow info 366792` |
| `create` | - | 创建任务 | `devflow create --title "..." --psm xxx --branch xxx` |
| `develop-start` | `start`, `dev-start` | 启动开发调试 | `devflow start 366792` |
| `develop-detail` | - | 查看开发部署详情 | `devflow develop-detail 366792` |
| `close` | - | 关闭任务 | `devflow close 366792` |
| `idl-repo` | - | 查询 IDL 仓库和 Service 文件 | `devflow idl-repo --psm xxx` |
| `bind-path` | - | 绑定任务的 IDL 路径和 PSM | `devflow bind-path 366792 --psm xxx --path xxx` |
| `unbind-path` | - | 解绑任务的 IDL 路径 PSM | `devflow unbind-path 366792 --psm xxx` |

---

## 1. 创建任务 (create)

创建一个新的 DevFlow 任务。

### 基本用法

```bash
gdpa-cli run devflow create \
  --title "任务标题" \
  --psm "tiktok.service.xxx" \
  --branch "feature-xxx"
```

### 完整参数

| 参数 | 简写 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--title` | `-t` | ✅ | - | 任务标题 |
| `--psm` | `-p` | ✅ | - | PSM 名称 |
| `--branch` | `-b` | ✅ | - | 源分支名称 |
| `--target` | - | ❌ | `master` | 目标分支 |
| `--region` | - | ❌ | `i18n` | 区域（cn 或 i18n） |
| `--env` | - | ❌ | `ppe` | 环境（ppe、boe 或 ppe+boe） |
| `--dc` | - | ❌ | `LF` | 数据中心 |
| `--has-idl` | - | ❌ | `true` | 是否有 IDL |
| `--biz` | - | ❌ | `tiktok` | 业务线（支持名称或 ID，例如 tiktok/devflow/aweme/tikcast/7743；也支持平台枚举名如 TikTok Shop） |
| `--meego` | - | ❌ | - | 关联 Meego 工单 URL（可多次指定，格式：`https://meego.larkoffice.com/{project}/{type}/detail/{id}`） |

### `--biz` 支持业务线

`--biz` 支持传入业务线名称或业务线 ID（数字字符串），当前支持：

| ID | 名称 |
|----|------|
| `0` | 抖音 |
| `1` | 火山 |
| `2` | 抖音-工具线 |
| `3` | DevFlow |
| `4` | DevFlow Demo |
| `8` | TikTok-UserCore |
| `10` | 抖音系增长 |
| `11` | 抖音IM |
| `13` | Janus Portal |
| `14` | TikTok IM |
| `15` | Yumme |
| `17` | TikTok Studio (Client) |
| `22` | Ecom |
| `23` | OEC |
| `24` | 小说 |
| `25` | Music |
| `27` | 西瓜 |
| `30` | 抖音-搜索 |
| `31` | 用户中台 |
| `32` | 公共 |
| `33` | 豆包 |
| `34` | paladin |
| `35` | 直播互动 |
| `1180` | TikTok |
| `1728` | Global live |
| `7743` | TikTok Shop |
| `112889` | 抖音工具线-模板业务 |
| `325528` | 西西里 |

### 高级特性

#### 1. 关联 Meego 工单

创建任务时可通过 `--meego` 参数关联 Meego 工单，支持传入工单 URL（可多次指定关联多个工单）：

```bash
# 关联单个 Meego 工单
gdpa-cli run devflow create \
  --title "修复登录问题" \
  --psm "tiktok.service.xxx" \
  --branch "feature-fix-login" \
  --meego "https://meego.larkoffice.com/ttarch/story/detail/6874274119"

# 关联多个 Meego 工单
gdpa-cli run devflow create \
  --title "重构用户模块" \
  --psm "tiktok.service.xxx" \
  --branch "feature-refactor-user" \
  --meego "https://meego.larkoffice.com/ttarch/story/detail/111" \
  --meego "https://meego.larkoffice.com/ttarch/bug/detail/222"
```

支持两种 URL 格式：
- `https://meego.larkoffice.com/{simple_name}/{type}/detail/{id}` — 常用格式，自动解析 simple_name 为 project_key
- `https://meego.feishu.cn/{project_key}/{type}/detail/{id}` — 直接使用 project_key

`{type}` 可以是 `story`、`bug`、`task` 等。

#### 2. 多环境支持

支持同时创建多个环境的泳道（使用 `+` 分隔）：

```bash
# 同时创建 PPE 和 BOE 泳道
gdpa-cli run devflow create \
  --title "多环境测试" \
  --psm "tiktok.service.xxx" \
  --branch "feature-20260206173200" \
  --env ppe+boe \
  --region i18n
```

#### 3. 泳道命名规则

泳道名称自动从分支名称提取后缀：

- 分支：`feature-20260206173200`
- 泳道：`ppe_20260206173200`、`boe_20260206173200`

#### 4. 区域配置

**I18N 区域**：（默认）
```bash
gdpa-cli run devflow create \
  --title "I18N 任务" \
  --psm "tiktok.service.xxx" \
  --branch "feature-xxx" \
  --region i18n
```

**CN 区域**：
```bash
gdpa-cli run devflow create \
  --title "CN 任务" \
  --psm "tiktok.service.xxx" \
  --branch "feature-xxx" \
  --region cn
``


### 输出示例

```
ID:   366792
Link: https://devflow.bytedance.net/space/1180/task/366792
```

---

## IDL 路径绑定 (bind-path / unbind-path)

为已有 DevFlow 任务维护 IDL 提交侧的路径绑定。

### 绑定路径

```bash
gdpa-cli run devflow bind-path 366792 \
  --psm "tiktok.service.xxx" \
  --path "idl/path/to/service"
```

如果未传 `--path`，CLI 默认使用 `--psm` 的值作为路径。

### 解绑路径

```bash
gdpa-cli run devflow unbind-path 366792 \
  --psm "tiktok.service.xxx"
```

`unbind-path` 支持重复传入 `--psm` 一次解绑多个 PSM。

---

## 2. 列出任务 (list)

查询指定 PSM 的 DevFlow 任务列表。

### 基本用法

```bash
# 列出所有任务
gdpa-cli run devflow list --psm "tiktok.service.xxx"

# 使用别名
gdpa-cli run devflow ls --psm "tiktok.service.xxx"
```

### 参数说明

| 参数 | 简写 | 必填 | 说明 |
|------|------|------|------|
| `--psm` | `-p` | ✅ | PSM 名称 |
| `--branch` | `-b` | ❌ | 按分支过滤 |
| `--user` | `-u` | ❌ | 按用户过滤 |
| `--all` | `-a` | ❌ | 显示所有任务（忽略用户/分支过滤） |
| `--biz` | - | ❌ | 按业务线过滤（默认 tiktok；支持名称或 ID） |

### 使用示例

```bash
# 查询特定分支的任务
gdpa-cli run devflow list \
  --psm "tiktok.service.xxx" \
  --branch "feature-xxx"

# 查询特定用户的任务
gdpa-cli run devflow list \
  --psm "tiktok.service.xxx" \
  --user "username"

# 查询所有任务（不过滤）
gdpa-cli run devflow list \
  --psm "tiktok.service.xxx" \
  --all
```

### 输出示例

```
=== DevFlow Task Information ===
Title                           Branch              Creator         Status    
--------------------------------------------------------------------------------
test pipeline link              feature-xxx         yuehongwei      OPEN      
--------------------------------------------------------------------------------
For more information: https://devflow.bytedance.net
```

### 特殊行为

在 macOS 上，如果指定了分支且有结果，会自动在浏览器中打开第一个任务的网页。

---

## 3. 查看任务详情 (info)

显示指定任务的详细信息，包括 DTO 生成状态和命令。

### 基本用法

```bash
gdpa-cli run devflow info <task_id>
```

### 示例

```bash
gdpa-cli run devflow info 366792
```

### 输出示例

```
=== Task Detail ===
ID:          366792
Title:       test pipeline link
Status:      OPEN
Creator:     yuehongwei.harvey
Branch:      feature-20260206173200
Link:        https://devflow.bytedance.net/space/1180/task/366792

=== DTO Generation Info ===
Platform:    tiktok.ug_incentive.open
Resource:    GDP RPC
Branch:      master
Status:      SUCCESS
Time:        2026-02-06 16:30:21
Commands:
  - 更新 Dto 依赖
    go get code.byted.org/tiktok/rpcmodels/tiktok_ug_incentive_open@latest

Platform:    tiktok.ug_incentive.open
Resource:    KiteX
Branch:      feature-20260206161847
Status:      SUCCESS
Time:        2026-02-06 16:24:45
Commands:
  - Tiktok_ug_incentive_open仓库下载
    git clone -b feature-20260206161847 git@code.byted.org:overpass/tiktok_ug_incentive_open.git
  - 分支切换
    git fetch origin feature-20260206161847 && git checkout -b feature-20260206161847 origin/feature-20260206161847
  - Tiktok_ug_incentive_open依赖更新
    go get code.byted.org/overpass/tiktok_ug_incentive_open@feature-20260206161847

Platform:    tiktok.ug_incentive.open
Resource:    Overpass Client
Branch:      master
Status:      SUCCESS
Time:        2026-02-06 16:26:42
Commands:
  - 依赖更新
    go get code.byted.org/overpass/tiktok_ug_incentive_open@master
  - Import路径
    code.byted.org/overpass/tiktok_ug_incentive_open/rpc/tiktok_ug_incentive_open

Platform:    tiktok.ug_incentive.open
Resource:    Overpass Model
Branch:      master
Status:      SUCCESS
Time:        2026-02-06 16:26:42
Commands:
  - 主结构体Import路径
    go get code.byted.org/overpass/tiktok_ug_incentive_open/kitex_gen/tiktok/ug_incentive/open@master
  - Import路径
    code.byted.org/overpass/tiktok_ug_incentive_open/rpc/tiktok_ug_incentive_open
```

### DTO 生成信息说明

`info` 命令会自动查询任务的 DTO 代码生成状态，包括：

- **Platform**: 生成的平台类型（GDP RPC、KiteX、Overpass Client、Overpass Model 等）
- **Resource**: 资源标识（PSM 或平台名称）
- **Branch**: 生成代码的分支
- **Status**: 生成状态（SUCCESS、RUNNING、ERROR、SKIPPED）
- **Time**: 生成时间
- **Commands**: 可执行的更新命令列表
  - 包含命令说明和实际命令
  - 可直接复制执行来更新依赖

常见的生成资源类型：
- **GDP RPC**: RPC 模型依赖（通常在 `rpcmodels` 仓库）
- **KiteX**: KiteX 服务代码（Overpass 仓库）
- **Overpass Client**: Overpass 客户端代码
- **Overpass Model**: Overpass 数据模型

---

## 4. 启动开发调试 (develop-start)

启动任务的开发调试流水线。这会触发选中环境的部署流水线，开始开发和调试流程。

### 基本用法

```bash
# 完整命令
gdpa-cli run devflow develop-start <task_id>

# 使用别名（推荐）
gdpa-cli run devflow start <task_id>
gdpa-cli run devflow dev-start <task_id>
```

### 示例

```bash
# 启动任务 366792 的开发调试
gdpa-cli run devflow start 366792
```

### 输出示例

**单环境任务**：
```
Task ID: 366780

Pipeline [ppe_20260206172100]:
https://devflow.bytedance.net/space/1180/task/366780/develop?lane_name=ppe_20260206172100&meegoId=&meegoProjectKey=&region=i18n&tabKey=Develop&title=%5BPPE_I18N%5D+tiktok.gdpa.test_rpc
```

**多环境任务（ppe+boe）**：
```
Task ID: 366792

Pipeline [ppe_20260206173200]:
https://devflow.bytedance.net/space/1180/task/366792/develop?lane_name=ppe_20260206173200&meegoId=&meegoProjectKey=&region=i18n&tabKey=Develop&title=%5BPPE_I18N%5D+tiktok.gdpa.test_rpc

Pipeline [boe_20260206173200]:
https://devflow.bytedance.net/space/1180/task/366792/develop?lane_name=boe_20260206173200&meegoId=&meegoProjectKey=&region=i18n&tabKey=Develop&title=%5BBOE_I18N%5D+tiktok.gdpa.test_rpc
```

### 返回内容说明

- **Task ID**: 任务 ID
- **Pipeline 链接**: 直接跳转到对应泳道的流水线页面
  - 包含泳道名称（lane_name）
  - 包含区域信息（region）
  - 包含标题（自动格式化为 `[ENV_REGION] PSM`）
  - 多环境任务会为每个泳道生成独立的链接

---

## 5. 查看开发部署详情 (develop-detail)

查看任务的开发部署详情，包括泳道信息、流水线 URL 和流水线 ID。

### 基本用法

```bash
gdpa-cli run devflow develop-detail <task_id>
```

### 示例

```bash
gdpa-cli run devflow develop-detail 366792
```

### 输出示例

```
=== Develop Detail ===
Task ID: 366792

Lane:         ppe_20260206173200
Status:       READY
Region:       i18n
Env:          ppe
DC:           LF
Clusters:     default
PSM:          tiktok.gdpa.test_rpc
Provider:     TCE
Branch:       feature-20260206173200
CanDebug:     true
EnvURL:       https://tce.bytedance.net/...
PipelineURL:  https://devflow.bytedance.net/...
PipelineID:   123456
BytesuiteID:  abc123
Repo:         tiktok/gdpa-test-rpc
GitURL:       git@code.byted.org:tiktok/gdpa-test-rpc.git

---

Lane:         boe_20260206173200
Status:       RUNNING
Region:       i18n
Env:          boe
DC:           LF, SG
Clusters:     default, sg1
PSM:          tiktok.gdpa.test_rpc
Provider:     TCE
Branch:       feature-20260206173200
NeedDeploy:   true
EnvURL:       https://tce.bytedance.net/...
PipelineURL:  https://devflow.bytedance.net/...
PipelineID:   123457

=== Pipeline Status ===
  [SUCCESS] 编译构建
    [SUCCESS] 编译
           https://...
  [RUNNING] 部署
    [RUNNING] 部署到 PPE
           https://...
  [PENDING] 验证
```

### 返回内容说明

**泳道部署信息**：

- **Lane**: 泳道名称（以 `ppe_` 或 `boe_` 开头）
- **Status**: 部署状态（PENDING/RUNNING/READY/FAILED/DEBUGGING/NOT_RECYCLED）
- **Region**: 控制面区域（cn 或 i18n），即 VRegion
- **Env**: 环境类型（ppe、boe 或 prod）
- **DC**: 部署机房列表，即 VDC（支持多机房，如 `LF, SG`）
- **Clusters**: 集群列表（支持多集群）
- **PSM**: 服务 PSM 名称
- **Provider**: 服务类型（TCE、ByteFaaS 等）
- **Branch**: 开发分支
- **NeedDeploy**: 是否需要部署服务
- **CanDebug**: 是否可以 debug
- **IsDebugging**: 是否正在 debug
- **DebugTips**: Debug 提示信息（如有）
- **EnvURL**: 环境页面链接（可跳转查看实例详情，含 IP/Port 等）
- **PipelineURL**: 流水线页面链接
- **PipelineID**: 流水线 ID
- **BytesuiteID**: ByteSuite 实例 ID
- **Repo**: 代码仓库名
- **GitURL**: Git 仓库地址

**流水线状态**（Pipeline Status）：

- 展示流水线各节点的执行状态（CREATED/RUNNING/SUCCESS/FAILED/PENDING/CANCELED）
- 每个节点下的子任务包含名称、状态、链接和错误信息

> **注意**：如需查看实例级别的 IP/Port/启动状态等详细信息，可通过 EnvURL 链接跳转到 TCE 环境页面查看，或使用 `tce_pod_list` 工具传入 PSM 和 env 参数查询。

---

## 6. 关闭任务 (close)

关闭或放弃一个 DevFlow 任务。

### 基本用法

```bash
gdpa-cli run devflow close <task_id>
```

### 示例

```bash
gdpa-cli run devflow close 366792
```

### 输出示例

```
Task 366792 closed successfully
```

---

## 7. 查询 IDL 仓库信息 (idl-repo)

通过 PSM 查询对应的 IDL 仓库和 Service 文件路径。底层使用 BAM 平台的 GetRepoInfo 接口。

### 基本用法

```bash
gdpa-cli run devflow idl-repo --psm "tiktok.gdpa.test_rpc"

# 使用别名
gdpa-cli run devflow repo-info --psm "tiktok.gdpa.test_rpc"
```

### 参数说明

| 参数 | 简写 | 必填 | 说明 |
|------|------|------|------|
| `--psm` | `-p` | ✅ | PSM 名称（三段式，如 tiktok.gdpa.test_rpc） |
| `--json` | - | ❌ | 以 JSON 格式输出 |

### 输出示例

**默认格式**：
```
=== IDL Repo Info ===
PSM:            tiktok.gdpa.test_rpc
Repo:           
Service File:   tiktok/tiktok_gdpa_test_rpc_service.thrift
Branch:         master
Repo Namespace: tiktok/service_rpc_idl
Repo Type:      gitlab
```

**JSON 格式**（`--json`）：
```json
{
  "psm": "tiktok.gdpa.test_rpc",
  "repo": "",
  "path": "tiktok/tiktok_gdpa_test_rpc_service.thrift",
  "branch": "master",
  "proto_path": "",
  "repo_namespace": "tiktok/service_rpc_idl",
  "repo_type": "gitlab"
}
```

### 返回字段说明

- **PSM**: 服务的 PSM 名称
- **Repo**: IDL 仓库地址
- **Service File**: IDL Service 文件路径（主文件）
- **Branch**: 默认分支
- **Proto Path**: Proto 路径（proto 类型 IDL 时使用）
- **Repo Namespace**: 仓库命名空间
- **Repo Type**: 仓库类型（gitlab 或 gerrit）

---

## 完整工作流示例

### 场景 1：创建单环境 PPE 任务并启动

```bash
# 1. 登录
gdpa-cli login

# 2. 创建任务
gdpa-cli run devflow create \
  --title "修复用户登录问题" \
  --psm "tiktok.user.service" \
  --branch "feature-fix-login-20260206" \
  --region i18n \
  --env ppe

# 输出：ID: 366800

# 3. 启动开发调试
gdpa-cli run devflow start 366800

# 4. 查看任务状态
gdpa-cli run devflow info 366800

# 5. 完成后关闭任务
gdpa-cli run devflow close 366800
```

### 场景 2：创建多环境任务并分别启动

```bash
# 1. 创建 PPE+BOE 多环境任务
gdpa-cli run devflow create \
  --title "性能优化测试" \
  --psm "tiktok.api.gateway" \
  --branch "feature-perf-opt-20260206" \
  --region i18n \
  --env ppe+boe

# 输出：ID: 366801

# 2. 启动开发调试（会同时显示两个泳道的链接）
gdpa-cli run devflow start 366801

# 输出：
# Pipeline [ppe_perf-opt-20260206]: https://...
# Pipeline [boe_perf-opt-20260206]: https://...
```

### 场景 3：查询和管理任务

```bash
# 1. 查看某个 PSM 的所有任务
gdpa-cli run devflow list --psm "tiktok.user.service"

# 2. 查看特定分支的任务
gdpa-cli run devflow list \
  --psm "tiktok.user.service" \
  --branch "feature-fix-login-20260206"

# 3. 查看任务详情
gdpa-cli run devflow info 366800

# 4. 关闭不需要的任务
gdpa-cli run devflow close 366800
```

---

## 常见问题

### Q: 如何关联 Meego 工单？

A: 使用 `--meego` 参数传入 Meego 工单 URL（直接从浏览器地址栏复制即可）。可多次使用 `--meego` 关联多个工单。支持 `meego.larkoffice.com`（自动解析项目 slug）和 `meego.feishu.cn`（直接使用 project_key）两种格式。

### Q: 如何创建多环境任务？

A: 使用 `--env ppe+boe` 参数即可同时创建 PPE 和 BOE 两个泳道。

### Q: 泳道名称是如何生成的？

A: 泳道名称格式为 `{env}_{branch_suffix}`。例如分支 `feature-20260206173200` 会生成泳道 `ppe_20260206173200`。

### Q: develop-start 命令的链接为什么这么长？

A: 链接包含了所有必要的查询参数，可以直接跳转到对应泳道的流水线页面，方便查看部署进度。

### Q: 如何在多个泳道之间切换？

A: `develop-start` 命令会为每个泳道生成独立的链接，直接点击对应的链接即可。

---

## 注意事项

1. **认证凭证**: 所有命令需要先通过 `gdpa-cli login` 登录
2. **任务命名**: 建议使用清晰的分支名称后缀（如时间戳），便于识别泳道
3. **环境选择**: 开发调试通常使用 PPE，正式测试使用 BOE
4. **区域选择**: 根据服务的部署区域选择 cn 或 i18n
5. **多环境**: 如需同时测试多个环境，使用 `ppe+boe` 一次性创建

---

## 相关链接

- DevFlow 平台: https://devflow.bytedance.net
- 文档首页: https://devflow.bytedance.net/docs
