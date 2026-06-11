# GDP Update 命令详解

## 命令简介

**作用**: 根据IDL变更生成代码

**核心价值**: GDP 作为脚手架的优势在于设计好了整体工程架构,而 `gdp update` 是实际开发中最常用的命令,用于保持代码与 IDL 定义的同步

## 开发模式

`gdp update` 分为两种模式，通过 `.gdp/rpcmodels.local.yaml` 文件是否存在来判断：

| 模式 | 判断条件 | 说明 |
|------|----------|------|
| **本地模式** | `.gdp/rpcmodels.local.yaml` 存在 | 同步本地IDL变更结果 |
| **DevFlow模式** | `.gdp/rpcmodels.local.yaml` 不存在 | 同步DevFlow的IDL变更结果 |

**检测开发模式**:
```bash
if [ -f ".gdp/rpcmodels.local.yaml" ]; then
    echo "本地模式"
else
    echo "DevFlow模式"
fi
```

## 前置要求

### GDP 工具验证

默认情况下，您应该已经安装了 GDP 工具。如果执行 `gdp update` 命令时提示未找到，请按以下步骤安装：

```bash
# 尝试执行 gdp 命令
gdp -v

# 如果提示未找到命令，再执行安装
bash -c "$(curl -fsSL https://gdp.bytedance.net/open_api/tool/install.sh)"

# 验证安装成功
gdp --version
```

**安装说明**:
- GDP 工具安装后无需重新加载 shell 配置
- 默认假设用户已安装 GDP 工具
- 仅在命令执行失败时尝试安装

## 命令语法

### 基本语法

```bash
# 本地模式：不带参数
gdp update

# DevFlow模式：必须指定分支名
gdp update <devflow-branch-name>
```

### 参数说明

| 参数 | 类型 | 是否必选 | 说明 | 示例 |
|------|------|---------|------|------|
| `[branch]` | 位置参数 | DevFlow模式必选 | DevFlow 任务分支名称 | `feature-20230719143043` 或 `master` |
| `-s, --silence` | bool | 可选 | 跳过交互式提示,静默模式 | `--silence` |
| `-f, --force` | bool | 可选 | 强制覆盖现有文件 | `--force` |
| `--mono` | bool | 可选 | Monorepo 项目模式 | `--mono` |
| `--prefix` | string | 可选 | 服务路径前缀 | `--prefix="/v1"` |
| `--psm` | string | 可选 | 目标服务 PSM | `--psm=tiktok.user.api` |

### 本地模式

**适用场景**: `.gdp/rpcmodels.local.yaml` 存在时

```bash
# 直接执行，无需参数
gdp update
```

**说明**: 本地模式下，IDL路径从 `.gdp/rpcmodels.local.yaml` 读取，支持本地修改IDL后直接生成代码。

### DevFlow模式分支名要求

**适用场景**: `.gdp/rpcmodels.local.yaml` 不存在时

**重要**: DevFlow模式下，分支名是 **强制要求** 的参数，执行 `gdp update` 时必须指定分支名，系统不会假设或使用默认分支。

**要求**:
- **必须提供**: 分支名参数不可省略
- **不得假设**: 系统不会自动选择或假设任何分支
- **用户责任**: 用户必须主动提供正确的 DevFlow 分支名

**如何获取分支名**:
1. 登录 [DevFlow 平台](https://janus.byted.org/devflow/)
2. 查看您的任务列表
3. 复制任务分支名称（通常格式：`task-功能描述` 或 `feature-时间戳`）

**示例**:
```bash
# 正确：指定分支名
gdp update task-add-user-api
gdp update feature-20230719143043

# 错误：DevFlow模式下未指定分支名（系统会报错）
# gdp update  ❌ 缺少必需的参数
```

## 使用场景详解

### 场景 1: 在 DevFlow 任务分支上开发(自动执行)

**流程**:
1. 在 DevFlow 平台创建任务分支(例如 `feature-20230719143043`)
2. 在 DevFlow 修改 IDL 文件
3. DevFlow 自动触发 `gdp-codegen` 流水线节点
4. **GDP 自动执行 `gdp update`**,生成代码变更

**开发者操作**:
```bash
# 拉取 DevFlow 生成的分支
git fetch origin feature-20230719143043
git checkout -b feature-20230719143043 origin/feature-20230719143043

# 在此分支上直接开发业务逻辑,无需手动执行 gdp update
```

**特点**: 无需手动执行,DevFlow 平台自动完成代码生成

---

### 场景 2: 在自定义分支开发(手动执行)

**流程**:
1. 在 DevFlow 分支修改 IDL(例如任务分支 `task-123`)
2. 在本地自定义分支(例如 `my-feature`)开发
3. **手动执行 `gdp update <devflow-branch>`** 同步 DevFlow 分支的变更

**开发者操作**:
```bash
# 创建并切换到自定义分支
git checkout -b my-feature

# 同步 DevFlow 分支 task-123 的 IDL 变更和代码生成结果
gdp update task-123

# 继续在 my-feature 分支上开发业务逻辑
```

**适用情况**:
- 需要在多个 feature 分支并行开发
- 想要保持自己的 Git 分支结构
- 需要在不同 DevFlow 任务之间切换

---

### 场景 3: 更新 DTO 依赖版本(手动执行 go get)

当 IDL 已经合并到主干并发布 DTO 后,需要手动更新本地项目的 DTO 包依赖。

**API 服务**:
```bash
# TikTok API 服务
go get code.byted.org/tiktok/apimodels/p_s_m@latest

# 抖音 API 服务
go get code.byted.org/aweme/apimodels/p_s_m@latest
```

**RPC 服务**:
```bash
# TikTok RPC 服务
go get code.byted.org/tiktok/rpcmodels/p_s_m@latest

# 抖音 RPC 服务
go get code.byted.org/aweme/rpcmodels/p_s_m@latest
```

**注意**: `p_s_m` 需要替换为实际的 PSM(例如 `tiktok_user_api`)

---

## 与 DevFlow 工作流的集成

### DevFlow 任务分支(自动执行)

```
DevFlow 平台修改 IDL
         ↓
触发 gdp-codegen 流水线节点
         ↓
GDP 自动执行 gdp update
         ↓
生成 DTO + Action 骨架 + Router 注册
         ↓
开发者拉取分支,开始业务开发
```

### 本地自定义分支(手动执行)

```
DevFlow 分支修改 IDL (task-123)
         ↓
开发者在自定义分支执行: gdp update task-123
         ↓
同步 IDL 变更和代码生成结果
         ↓
继续在自定义分支开发业务逻辑
```

## 代码生成内容

执行 `gdp update` 会生成或更新以下内容:

### 1. DTO 文件(数据传输对象)

**位置**: 项目根目录下的 DTO 包依赖
- 根据 IDL 定义生成 Request 和 Response 结构体
- 包含字段映射、序列化/反序列化逻辑

### 2. Action 层骨架代码

**位置**: `project_path/action`

**API 服务示例**:
```go
// 自动生成的 Handler 方法
func FooBar(ctx context.Context) (interface{}, af.RespError) {
    var req dto.FooBarRequest
    // TODO: 添加参数校验和业务调用逻辑
    return nil, nil
}
```

**RPC 服务示例**:
```go
// 自动生成的 RPC Handler
func FooBarMethod(ctx context.Context, req *rpc.FooBarRequest) (*rpc.FooBarResponse, error) {
    // TODO: 实现业务逻辑
    return &rpc.FooBarResponse{}, nil
}
```

### 3. Router/Handler 注册代码

**API 服务**: `project_path/router/` 目录
- 自动注册路由规则
- 绑定 HTTP 方法(GET/POST/PUT/DELETE)和 URI

**RPC 服务**: `project_path/handler/` 目录
- 注册 RPC 方法
- 绑定 Thrift/Kitex 接口

**重要**: Router/Handler 代码**完全由框架自动生成和维护**,**请勿手动修改**

## 交互模式示例

### API 服务交互模式

执行 `gdp update` 后,会显示分组确认提示:

```bash
$ gdp update
2023/09/12 11:51:59 ==> 更新 GDP 项目
+----------+--------+------------------------+
|   分组   | 方法   |         URI            |
+----------+--------+------------------------+
|   foo    | GET    | /tiktok/v1/foo/get/    |
+          +--------+------------------------+
|          | POST   | /tiktok/v1/foo/delete/ |
+----------+--------+------------------------+

生成分组 <foo> 代码? (y or n): y
```

**说明**: 可以选择性生成某些分组的代码,便于增量开发

### RPC 服务 GPT 分组

RPC 服务的方法会按照 Thrift 接口定义自动分组,无需交互确认。

## 常见错误排查

### 错误 1: "Branch not found"

**错误信息**:
```
Error: DevFlow branch 'feature-xxx' not found
```

**原因**: 指定的 DevFlow 分支不存在或拼写错误

**解决方案**:
1. 在 [DevFlow 平台](https://janus.byted.org/devflow/) 检查任务分支名称
2. 确认分支是否已创建并完成 IDL 变更
3. 检查分支名拼写是否正确

---

### 错误 2: "Merge conflict in generated code"

**错误信息**:
```
CONFLICT (content): Merge conflict in action/foo.go
```

**原因**: 本地修改与生成代码冲突(通常是手动修改了 Router/Handler 文件)

**解决方案**:
1. **推荐做法**: 保留自动生成的 Router/Handler 代码,将业务逻辑迁移到 `service/domain`
2. **临时做法**: 手动解决冲突,但下次 `gdp update` 仍可能冲突

**预防措施**: 不要手动修改 `router/` 和 `handler/` 目录中的自动生成代码

---

### 错误 3: "DTO version mismatch"

**错误信息**:
```
Error: DTO version mismatch. Expected v1.2.0, got v1.1.0
```

**原因**: 本地 DTO 包版本与 IDL 定义不一致

**解决方案**:
```bash
# API 服务
go get code.byted.org/tiktok/apimodels/p_s_m@latest

# RPC 服务
go get code.byted.org/tiktok/rpcmodels/p_s_m@latest

# 更新 go.mod
go mod tidy
```

---

### 错误 4: "Permission denied" (Monorepo 场景)

**错误信息**:
```
Error: Permission denied to update monorepo
```

**原因**: Monorepo 项目需要特殊权限或配置

**解决方案**:
1. 添加 `--mono` 参数: `gdp update <branch> --mono`
2. 检查 `.gdp/app.yaml` 配置是否正确
3. 如有疑问,发起 Monorepo Oncall 寻求协助

## 最佳实践

### 1. 推荐工作流(自定义分支开发)

```bash
# Step 1: 在 DevFlow 创建任务并修改 IDL (任务分支: task-123)
# Step 2: 在本地创建自定义开发分支
git checkout -b my-feature-branch

# Step 3: 同步 DevFlow 分支的代码生成结果
gdp update task-123

# Step 4: 开发业务逻辑
# 编辑 service/domain、service/dal、service/dao 等文件

# Step 5: IDL 再次变更后,重新同步
gdp update task-123

# Step 6: 提交代码
git add .
git commit -m "feat: implement feature XYZ"
```

### 2. 避免手动修改自动生成的代码

**不要修改**:
- `router/` 目录(API 服务)
- `handler/` 目录(RPC 服务)
- `.gdp/` 目录

**应该修改**:
- `action/` - 可添加参数校验和绑定逻辑
- `service/domain` - 业务逻辑实现
- `service/dal` - 数据服务层
- `service/dao` - 数据模型层

### 3. 及时更新 DTO 版本

当 IDL 合并到主干后,应立即更新 DTO 依赖:

```bash
# 更新 DTO
go get code.byted.org/tiktok/apimodels/p_s_m@latest

# 验证依赖
go mod tidy
go build
```

## 相关文档

- **本地开发流程**: [workflow-local-development.md](../workflow/workflow-local-development.md)
- **代码分层架构概览**: [arch-code-layers-guide.md](../architecture/arch-code-layers-guide.md)
- **GDP Init 命令**: [init-command.md](init-command.md)
