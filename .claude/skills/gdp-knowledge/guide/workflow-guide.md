# GDP 本地开发流程
 
## 概述
-本文档说明 GDP服务开发流程指南，涵盖IDL编辑、代码生成、分层实现(action/domain/dal/dao)。当在GDP项目中开发、执行gdp update、编辑IDL或实现业务逻辑时使用。

# GDP开发流程

GDP服务开发完整指南，从IDL定义到代码提交。

## 开发流程概览

```
0. 前置检查 (GDP工具 + 检测开发模式)
   ↓
1. [本地开发模式] 修改本地IDL / [DevFlow模式] 用户自行在DevFlow平台修改IDL
   ↓
2. 生成代码 (gdp update)
   ↓
3. 实现业务逻辑 (domain/dal/dao)
   ↓
4. 编写单元测试
   ↓
5. 本地运行调试
   ↓
6. 提交代码审查
```

## 分步指南

### 步骤0: 前置检查 (GDP工具 + 检测开发模式)

**0.1 验证GDP工具**

```bash
# 先尝试gdp命令
gdp -v
# 如果命令未找到，安装:
bash -c "$(curl -fsSL https://gdp.bytedance.net/open_api/tool/install.sh)"
```

**0.2 了解 .gdp 目录结构**

`.gdp/` 目录包含GDP项目的配置文件:

| 文件 | 说明 |
|------|------|
| `app.yaml` | GDP元数据配置，包含psm(服务标识)、svc_type(服务类型: 1=API服务, 2=RPC服务) |
| `rpcmodels.yaml` | [可选] 本地rpcmodels生成配置，配合 go.work 在本地管理 rpcmodels 产物 |
| `rpcmodels.local.yaml` | [可选] **本地IDL路径配置**，存放本地IDL文件位置，存在此文件则为本地开发模式 |

**rpcmodels.yaml 说明**:

用于配置本地 IDL 产物的 rpcmodels 生成，核心思路是使用 `go.work` 在本地管理 rpcmodels 产物，避免每次都需要发布到远程仓库。

```yaml
# .gdp/rpcmodels.yaml 示例
Models:
    tiktok.gdp.svc_meta:
        BAM: true
        ModPath: code.byted.org/gdp/rpcmodels
GoWork: true
Output: rpcmodels
```

配合 `go.work` 使用：
```go
// go.work
go 1.18

use (
    .
    ./rpcmodels/base
    ./rpcmodels/tiktok_gdp_svc_meta
)
```

**rpcmodels.local.yaml 说明**:

存放本地 IDL 文件位置，存在此文件则为本地开发模式。

```yaml
# .gdp/rpcmodels.local.yaml 示例
Models:
    tiktok.gdp.svc_meta:
        IDLPath: ../service_rpc_idl/service/tiktok_gdp_svc_meta_service.thrift
```

通过读取 `Models` 中各服务的 `IDLPath` 字段，可获取本地 IDL 文件的位置。

**0.3 检测开发模式**

通过检查 `.gdp/rpcmodels.local.yaml` 文件自动检测:

```bash
# 检测是否为本地开发模式
if [ -f ".gdp/rpcmodels.local.yaml" ]; then
    echo "本地开发模式"
else
    echo "DevFlow模式"
fi
```

**开发模式说明:**

| 模式 | 判断条件 | IDL管理方式 | 后续步骤 |
|------|----------|-------------|----------|
| **本地开发模式** | `.gdp/rpcmodels.local.yaml` 存在 | 修改本地IDL，从配置文件读取IDL路径 | 进入步骤1 |
| **DevFlow模式** | `.gdp/rpcmodels.local.yaml` 不存在 | 用户自行在DevFlow平台修改IDL | 跳过步骤1，询问DevFlow分支名，直接进入步骤2 |

### 步骤1: 编辑IDL (仅本地开发模式)

> **如果检测到DevFlow模式则跳过此步骤** - IDL已在DevFlow平台编辑，只需执行 `gdp update <devflow-branch-name>` 同步代码。

**此步骤的前置条件:**
1. 确认检测到本地开发模式 (`.gdp/rpcmodels.local.yaml` 存在)
2. 读取 `.gdp/rpcmodels.local.yaml` 获取IDL路径
3. 使用配置文件中的IDL路径定位并编辑IDL文件

根据用户需求，编辑IDL文件定义API接口。

**重要**:
- 此步骤仅在**本地开发模式**下需要
- 从 `.gdp/rpcmodels.local.yaml` 配置文件读取IDL路径
- 不要假设或猜测IDL位置

**示例 - 定义新API**:
```thrift
// idl/user.thrift
namespace go user

struct CreateUserRequest {
    1: required string nickname
    2: optional string avatar
    3: optional string email
}

struct CreateUserResponse {
    1: required i64 user_id
    2: required string nickname
}

service UserService {
    CreateUserResponse CreateUser(1: CreateUserRequest req)
}
```

**IDL编辑指南**:
- 定义清晰的Request/Response结构
- 使用适当的数据类型 (required/optional)
- 遵循命名规范 (结构体用CamelCase，某些情况下字段用snake_case)
- 为复杂字段添加注释

### 步骤2: 生成代码 (gdp update)

使用 `gdp update` 生成代码。命令根据开发模式不同:

**本地开发模式:**
```bash
# 不带参数执行gdp update (默认行为)
gdp update
```

**DevFlow模式:**
```bash
# 必须指定DevFlow分支名从DevFlow同步代码
gdp update <devflow-branch-name>
```

**DevFlow模式要求**:
- **必需**: DevFlow模式下分支名是必须的
- **禁止假设**: 绝不能假设或猜测分支名
- **询问用户**: 必须在执行gdp update前询问用户"请提供DevFlow分支名"
- **禁止继续**: 用户未提供分支名时，不要执行gdp update命令

**gdp update生成内容**:
- DTO文件 (Request/Response结构体)
- Action层骨架代码 (Handler方法)
- Router/Handler注册代码 (自动维护，禁止修改)

### 步骤3: 实现业务逻辑

遵循分层架构: **action → domain → dal → dao**

**第1步: 检查Action层** (自动生成)
```bash
# 检查生成的Handler骨架
vi action/user/create_user.go
```
Action层: 只添加参数验证和绑定逻辑。核心业务逻辑放在Domain层。

**第2步: Domain层** (业务逻辑)
```bash
touch service/domain/user/create_user.go
vi service/domain/user/create_user.go
```

**第3步: DAL层** (数据服务)
```bash
touch service/dal/user/user_service.go
vi service/dal/user/user_service.go
```

**第4步: DAO层** (数据模型)
```bash
touch service/dao/user.go
vi service/dao/user.go
```

### 步骤4: 编写单元测试

```bash
# Domain层测试
touch service/domain/user/create_user_test.go

# DAL层测试
touch service/dal/user/user_service_test.go
```

**测试示例**:
```go
// service/domain/user/create_user_test.go
package user

import (
    "context"
    "testing"
)

func TestCreateUser(t *testing.T) {
    req := &dto.CreateUserRequest{
        Nickname: "test_user",
    }

    resp, err := CreateUser(context.Background(), req)
    if err != nil {
        t.Errorf("CreateUser failed: %v", err)
    }

    if resp.UserID <= 0 {
        t.Error("UserID should be positive")
    }
}
```

**运行测试**:
```bash
go test ./...                           # 所有测试
go test ./service/domain/user/...       # 特定包
go test -cover ./...                    # 带覆盖率
```

### 步骤5: 本地运行调试

**启动服务**:
```bash
go build -o bin/server && ./bin/server
# 或
./build.sh && ./output/bin/server
```

**测试API**:
```bash
curl -X POST http://localhost:8000/api/v1/user/create \
  -H "Content-Type: application/json" \
  -d '{"nickname": "test_user"}'
```

**查看日志**:
```bash
tail -f logs/server.log
```

### 步骤6: 提交代码

**代码质量检查**:
```bash
go vet ./...
golangci-lint run
go fmt ./...
```

**提交并推送**:
```bash
git add .
git commit -m "feat: add create user API"
git push origin feature/add-user-api
```

## 常用命令

```bash
# ===== GDP代码同步 =====
gdp update                               # 本地开发模式: 默认行为
gdp update <devflow-branch-name>         # DevFlow模式: 从DevFlow分支同步代码

# ===== 依赖管理 =====
go mod tidy                              # 更新依赖
go list -m all                           # 查看模块依赖

# ===== DTO包更新 =====
# API服务
go get code.byted.org/tiktok/apimodels/your_service@latest
# RPC服务
go get code.byted.org/tiktok/rpcmodels/your_service@latest

# ===== 测试 =====
go test ./...                            # 所有测试
go test -run TestCreateUser ./service/domain/user/
go test -coverprofile=coverage.out ./... # 覆盖率报告
go tool cover -html=coverage.out

# ===== 代码质量 =====
go fmt ./...
golangci-lint run
```

## 重要约束

**禁止在以下路径下手动创建子目录:**
- `handler/`
- `action/`
- `service/domain/`

这些目录及其子目录由 `gdp update` 根据IDL定义自动生成。目录结构反映IDL中定义的API分组。

**可以做的:**
- 编辑这些目录中的现有文件
- 向生成的骨架代码添加业务逻辑

**不能做的:**
- 手动创建新子目录
- 直接在这些目录中创建新文件 (使用 `gdp update` 代替)

## 开发技巧

1. **理解分层架构**: 遵循 action → domain → dal → dao，禁止跨层调用
2. **不要修改生成的代码**: Router/Handler目录由框架维护
3. **不要手动创建目录**: 让 `gdp update` 处理 handler/action/service/domain 的目录结构
4. **频繁同步**: IDL变更后运行 `gdp update`
5. **测试驱动**: 先写测试，再实现
6. **及时更新DTO**: IDL合并到main后，使用 `go get` 更新DTO版本

## 相关文档

- [update-command.md](../commands/update-command.md) - GDP Update 命令详解
- [code-layers-guide.md](./code-layers-guide.md) - 代码分层指南
