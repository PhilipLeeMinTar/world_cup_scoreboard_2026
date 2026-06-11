# GDP Init 命令详解

## 命令简介

**作用**: 初始化 GDP 项目或生成项目配置文件

**适用场景**:
- 创建新的 API 或 RPC 服务
- 调整代码分组规则(使用 `--cfg-only`)
- 从现有服务迁移到 GDP 框架

**核心价值**: GDP Init 是服务开发的起点,自动生成符合 GDP 规范的项目结构和代码骨架

**使用频率**: 低频命令(一个服务只需执行一次,后续使用 `gdp update`)

## 命令语法

### 基本语法

```bash
gdp init <psm>
```

### 参数说明

| 参数 | 类型 | 是否必选 | 说明 | 示例 |
|------|------|---------|------|------|
| `<psm>` | 位置参数 | 必选 | 服务的 PSM (product.service.type) | `tiktok.user.api` |
| `--cfg-only` | bool | 可选 | 仅生成配置文件 `.gdp/app.yaml` | `--cfg-only` |
| `--branch` | string | 可选 | IDL 源分支 | `--branch feature-xxx` |
| `--mono` | bool | 可选 | Monorepo 项目模式 | `--mono` |
| `--prefix` | string | 可选 | API 路径前缀(用于分组) | `--prefix="/api/v1,/api/v2"` |
| `--prod` | string | 可选 | 产品线 | `--prod=tiktok` 或 `--prod=aweme` |
| `--svc-type` | string | 可选 | 服务类型 | `--svc-type=api` 或 `--svc-type=rpc` |
| `--spec` | string | 可选 | 代码规范 | `--spec=gdp`(默认) 或 `--spec=native` |

## PSM 格式说明

### PSM 结构

**格式**: `<product>.<service>.<type>`

**示例**:
- `tiktok.user.api` - TikTok 用户 API 服务
- `tiktok.payment.rpc` - TikTok 支付 RPC 服务
- `aweme.comment.api` - 抖音评论 API 服务

### 组成部分

**Product (产品线)**:
- `tiktok` - TikTok 国际版
- `aweme` - 抖音
- `tiktok_ic` - TikTok IC
- `tiktok_bric` - TikTok BRIC

**Service (服务名)**:
- 使用有意义的名称
- 小写字母
- 多个单词用下划线连接
- 示例: `user`, `payment`, `order_management`

**Type (服务类型)**:
- `api` - API 服务(HTTP/Restful)
- `rpc` - RPC 服务(Thrift/Kitex)

---

## 使用场景详解

### 场景 1: 完整初始化(默认)

**目的**: 创建新服务的完整项目结构和代码

**命令**:
```bash
# API 服务
gdp init tiktok.user.api

# RPC 服务
gdp init tiktok.payment.rpc
```

**执行流程**:
```
1. 验证 PSM 在 DevFlow 已注册
2. 从 DevFlow 拉取 IDL 定义
3. 生成 .gdp/app.yaml 配置文件
4. 创建目录结构
5. 生成 DTO 引用
6. 生成 Action 层代码
7. 生成 Router/Handler 注册
8. 生成 main.go 和配置文件
9. 初始化 go.mod
```

**生成的项目结构**:
```
your-service/
├── .gdp/                  # GDP 元数据目录
│   └── app.yaml           # 服务配置文件
├── action/                # Action 层 (接入层)
│   ├── user_action.go     # Handler 实现
│   └── ...
├── router/                # 路由注册 (API 服务)
│   └── router.go
├── handler/               # Handler 注册 (RPC 服务)
│   └── handler.go
├── service/               # 业务逻辑目录
│   ├── domain/            # Domain 层 (业务实现层)
│   ├── dal/               # DAL 层 (数据服务层)
│   └── dao/               # DAO 层 (数据模型层)
├── pkg/                   # 服务基础库
│   ├── middleware/        # 中间件
│   └── util/              # 工具函数
├── conf/                  # 配置文件目录
│   ├── conf.yaml          # 主配置文件
│   └── ...
├── main.go                # 服务入口文件
├── build.sh               # 构建脚本
├── go.mod                 # Go 模块定义
└── go.sum                 # Go 依赖锁定
```

---

### 场景 2: 仅生成配置文件

**目的**: 先生成配置文件,手动调整分组规则后再生成代码

**适用情况**:
- 服务有复杂的路由分组需求
- 需要自定义 RPC 方法分组
- 想要在生成代码前预览配置

**步骤 1: 生成配置文件**

```bash
gdp init tiktok.user.api --cfg-only
```

**生成内容**:
```
your-service/
└── .gdp/
    └── app.yaml   # 仅生成配置文件
```

**步骤 2: 编辑配置文件**

打开 `.gdp/app.yaml`,调整配置:

```yaml
# .gdp/app.yaml 示例
psm: tiktok.user.api
service_type: api
product: tiktok

# API 路径分组规则
api_group:
  - name: user
    prefix: /tiktok/v1/user/
    methods:
      - GetUserInfo
      - UpdateUserInfo

  - name: account
    prefix: /tiktok/v1/account/
    methods:
      - Login
      - Logout

# RPC 方法分组规则 (仅 RPC 服务)
rpc_group:
  - name: user_service
    methods:
      - GetUserInfo
      - BatchGetUserInfo
```

**步骤 3: 完整初始化**

配置调整完成后,执行完整初始化:

```bash
gdp init tiktok.user.api
```

GDP 会读取已存在的 `.gdp/app.yaml`,按照自定义的分组规则生成代码。

---

### 场景 3: Monorepo 项目初始化

在 Monorepo 仓库中初始化服务,必须在服务子目录中执行 `gdp init tiktok.user.api --mono`

### 场景 4: 指定 IDL 分支初始化

从特定 IDL 分支生成代码(用于测试): `gdp init tiktok.user.api --branch feature-new-api`

### 场景 5: 自定义路径前缀分组

按 API 路径前缀自动分组: `gdp init tiktok.user.api --prefix="/api/v1,/api/v2"`(不同组生成独立的 Action 和 Router 文件)

---

## 配置文件说明

### .gdp/app.yaml 结构

GDP Init 生成的配置文件示例:

```yaml
# 服务基本信息
psm: tiktok.user.api
service_type: api
product: tiktok

# API 服务分组规则
api_group:
  - name: user                    # 分组名称
    prefix: /tiktok/v1/user/      # 路径前缀
    methods:                      # 包含的方法
      - GetUserInfo
      - UpdateUserInfo
      - DeleteUser

  - name: profile
    prefix: /tiktok/v1/profile/
    methods:
      - GetProfile
      - UpdateProfile

# RPC 服务分组规则 (仅 RPC 服务)
rpc_group:
  - name: user_service
    methods:
      - GetUserInfo
      - BatchGetUserInfo
      - CreateUser

# 代码规范
spec: gdp

# 是否为 Monorepo
mono: false
```

### 关键配置项

**psm**: 服务的唯一标识符
- 必填
- 格式: `product.service.type`

**service_type**: 服务类型
- 可选值: `api`, `rpc`
- 自动从 DevFlow 检测

**api_group / rpc_group**: 方法分组规则
- 控制代码文件的组织方式
- 可以手动调整分组

**spec**: 代码规范
- `gdp`: GDP 标准规范(推荐)
- `native`: 原生 Go 规范

---

## 与一键创建服务平台的关系

### 一键创建服务平台

**平台地址**: https://bits.bytedance.net/app_center/create?tab=service

**功能**: 自动创建 SCM 仓库 + TCE 服务 + DevFlow 集成 + 代码初始化

**流程**:
```
填写服务信息
   ↓
选择 GDP-TikTok 或 GDP-抖音 组件
   ↓
平台自动创建:
  - SCM 代码仓库
  - TCE 服务注册
  - DevFlow 平台集成
   ↓
平台自动执行 gdp init
   ↓
生成完整的项目代码
   ↓
提交 MR 到主干
```

**优势**: 一站式创建所有资源,自动集成 DevFlow 和 TCE,无需手动执行 gdp init,代码直接提交到 SCM

### 手动 gdp init

**适用场景**:
- SCM 仓库已存在
- 从其他框架迁移到 GDP
- 需要自定义初始化流程
- Monorepo 中添加新服务

**流程**:
```
手动创建 SCM 仓库
   ↓
服务在 DevFlow 注册
   ↓
手动执行 gdp init <psm>
   ↓
生成项目代码
   ↓
手动提交到 SCM
```

---

## 项目初始化内容

GDP Init 会创建以下内容:

### 1. 目录结构

完整的 GDP 代码分层目录:
- `action/` - Action 层(接入层)
- `service/domain/` - Domain 层(业务逻辑)
- `service/dal/` - DAL 层(数据服务)
- `service/dao/` - DAO 层(数据模型)
- `pkg/` - 服务基础库

### 2. 代码文件

自动生成的代码文件:
- `main.go` - 服务入口
- `action/*.go` - Handler 实现
- `router/router.go` 或 `handler/handler.go` - 路由/方法注册
- `conf/conf.yaml` - 配置文件

### 3. GDP 元数据

- `.gdp/app.yaml` - 服务配置
- `.gdp/` 目录存放 GDP 框架所需的元数据

### 4. Go 模块

- `go.mod` - Go 模块定义
- `go.sum` - 依赖锁定文件
- 自动添加 GDP 框架和 DTO 依赖

### 5. 构建脚本

- `build.sh` - 服务构建脚本
- 支持本地构建和 CI 集成

---

## 常见问题排查

**问题 1: "PSM not found in DevFlow"** - 服务未在 DevFlow 平台注册。解决方案: 访问 DevFlow 检查服务注册状态,或使用一键创建服务平台

**问题 2: "Directory not empty"** - 目标目录已存在文件。解决方案: 在空目录中执行 `gdp init`,或使用 `--cfg-only` 仅生成配置文件

**问题 3: "IDL not found"** - DevFlow 中没有该服务的 IDL 定义。解决方案: 在 DevFlow 平台创建 IDL 定义,确保 IDL 已提交到 master 分支

**问题 4: "Permission denied"** - 无权限访问该服务的 DevFlow 配置。解决方案: 联系服务 Owner 添加权限

---

## 最佳实践

1. **使用一键创建服务平台**: 对于全新服务,优先使用一键创建平台,自动创建所有资源,避免手动配置错误

2. **先生成配置后调整**: 使用 `--cfg-only` 先生成配置,编辑 `.gdp/app.yaml` 调整分组,然后完整初始化

3. **及时提交到 SCM**: 初始化完成后立即提交代码 (`git add . && git commit && git push`)

4. **验证项目可构建**: 初始化后立即验证 (`go mod tidy && go build && ./build.sh`)

---

## 后续步骤

GDP Init 完成后,您可以:

1. **在 DevFlow 修改 IDL** → 新增或修改接口
2. **执行 gdp update** → 同步 IDL 变更到代码
3. **实现业务逻辑** → 在 `service/domain` 层编写业务代码
4. **本地测试** → 运行单元测试和集成测试
5. **提交代码评审** → 合并到主干并上线

---

## 相关文档

- [update-command.md](update-command.md) - GDP Update 命令
- [arch-code-layers-guide.md](../architecture/arch-code-layers-guide.md) - 代码分层架构指南
- [workflow-local-development.md](../workflow/workflow-local-development.md) - 本地开发流程
