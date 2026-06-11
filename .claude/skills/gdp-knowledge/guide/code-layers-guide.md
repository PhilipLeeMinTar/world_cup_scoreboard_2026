# GDP 代码分层架构指南

## 概述

GDP 基于严格的分层原则强制执行标准化的代码结构,分离关注点,提高可维护性,确保所有服务的代码组织一致性。

### 设计原则

**固定目录结构**: 有限且定义明确的目录减少学习曲线,改善跨团队协作

**基于层的组织**: 业务代码分离为不同的层,具有明确的职责和依赖规则

**框架隔离**: 框架代码与业务逻辑分离,最小化耦合

**自动生成**: 核心结构自动生成,确保一致性并减少人为错误

## 标准目录结构

### API 服务结构

```
project_path/
├── .gdp/                  # GDP 元数据(不要修改)
│   └── app.yaml           # GDP配置: psm、svc_type(1=API, 2=RPC)
├── router/                # [gdp update自动生成,禁止修改] 路由注册
│   └── <group>.go
├── action/                # [gdp update自动生成,可添加逻辑] Action 层(接入层)
│   └── <group>/
│       └── <handler>.go
├── service/
│   ├── domain/            # [gdp update自动生成,可编写业务] 业务逻辑层
│   ├── dal/               # [手动创建] 数据服务层
│   └── dao/               # [手动创建] 数据模型层
├── pkg/                   # [手动创建] 服务工具
│   ├── app/
│   ├── conf/
│   └── types/
├── conf/                  # 配置文件
├── main.go
├── build.sh
├── go.mod
└── go.sum
```

**重要说明**:
- `router/`、`action/`、`domain/` 目录下的文件均由 `gdp update` 根据 IDL 自动生成
- **禁止手动创建文件**，只能在已生成的文件中添加业务逻辑
- `router/`: 路由注册，**不要修改**
- `action/`: 接入层，可在已生成的文件中添加参数校验等逻辑
- `domain/`: 业务逻辑层，可在已生成的文件中编写业务代码
- `dal/`、`dao/`、`pkg/`: 需手动创建文件

### RPC 服务结构

```
project_path/
├── .gdp/                  # GDP 元数据(不要修改)
│   ├── app.yaml           # GDP配置: psm、svc_type(1=API, 2=RPC)
│   ├── rpcmodels.yaml     # [可选] rpcmodels生成配置
│   └── rpcmodels.local.yaml  # [可选] 存在此文件则为本地IDL开发模式，用于配置本地IDL路径，否则代表IDL存放远端
├── rpcmodels/               # [gdp update自动生成,禁止修改] IDL的CodeGen生成产物
├── handler/               # [gdp update自动生成,禁止修改] RPC Handler
│   └── <group>.go         # 按 group 平铺
├── action/                # [gdp update自动生成,可添加逻辑] Action 层(接入层)
│   └── <group>/
│       └── <method>.go
├── service/
│   ├── domain/            # [gdp update自动生成,可编写业务] 业务逻辑层
│   ├── dal/               # [手动创建] 数据服务层
│   └── dao/               # [手动创建] 数据模型层
├── pkg/                   # [手动创建] 服务工具
├── conf/                  # 配置文件
├── script/
│   └── bootstrap.sh
├── main.go
├── build.sh
├── go.mod
└── go.sum
```

**重要说明**:
- `handler/`、`action/`、`domain/` 目录下的文件均由 `gdp update` 根据 IDL 自动生成
- **禁止手动创建文件**，只能在已生成的文件中添加业务逻辑
- `rpcmodels/`: 存放 IDL 的 CodeGen 生成产物，**禁止修改**。
- `handler/`: RPC Handler，按 group 平铺为 `<group>.go` 文件，**不要修改**
- `action/`: 接入层，可在已生成的文件中添加参数校验等逻辑
- `domain/`: 业务逻辑层，可在已生成的文件中编写业务代码
- `dal/`、`dao/`、`pkg/`: 需手动创建文件

## 核心层级详解

### Action 层(接入层)

**目录**: `action/` (API 服务和 RPC 服务均使用此目录)

**职责**:
- 接收 HTTP/RPC 请求
- 将请求参数绑定到 DTO 结构
- 执行基本参数验证(类型检查)
- 调用 domain 层业务逻辑
- 格式化并返回响应

**生成方式**: 完全自动生成,可安全添加业务逻辑

**命名约定**:
- **API**: `action/<group>/<path_based_name>.go`
- **RPC**: `action/<group>/<method_name>.go`

**示例**:
```go
// API 服务: action/user/get_user_info.go
func GetUserInfo(ctx context.Context) (interface{}, af.RespError) {
    var req dto.GetUserInfoRequest
    if err := af.Bind(ctx, &req); err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    resp, err := domain.GetUserInfo(ctx, &req)
    if err != nil {
        return nil, errors.WithError(ctx, err)
    }
    return resp, nil
}
```

**注意事项**:
- 保持精简,只做参数绑定和调用 domain 层
- 不要在此层编写业务逻辑
- 可添加参数校验和错误处理

---

### Domain 层(业务逻辑层)

**目录**: `service/domain/`

**职责**:
- 实现核心业务逻辑
- 编排数据服务调用(dal 层)
- 业务规则验证
- 数据聚合和转换
- 返回业务错误码

**调用规则**:
- 只能被 action 层调用
- 可以调用 dal 层
- 不能跨 domain 服务调用
- 不能直接调用 dao 层

**命名约定**: 按业务功能模块组织,如 `domain/user/`, `domain/order/`

**示例**:
```go
// service/domain/user/get_user_info.go
func GetUserInfo(ctx context.Context, req *dto.GetUserInfoRequest) (*dto.GetUserInfoResponse, error) {
    // 1. 参数校验
    if req.GetUserID() <= 0 {
        return nil, errcode.ERR_PARAM_INVALID
    }

    // 2. 调用 dal 层获取数据
    userInfo, err := dal.GetUserByID(ctx, req.GetUserID())
    if err != nil {
        return nil, errcode.ERR_GET_USER_FAILED
    }

    // 3. 业务逻辑处理
    if userInfo.Status != StatusActive {
        return nil, errcode.ERR_USER_NOT_ACTIVE
    }

    // 4. 构造响应
    return &dto.GetUserInfoResponse{
        User: userInfo,
    }, nil
}
```

**注意事项**:
- 这是业务逻辑的核心,重点关注和测试
- 避免在此层直接操作数据库或缓存
- 返回明确的业务错误码

---

### DAL 层(数据服务层)

**目录**: `service/dal/`

**职责**:
- 封装数据相关的业务逻辑
- 调用下游 RPC 服务
- 聚合或裁剪 dao 层返回的数据
- 处理缓存逻辑
- 数据格式转换

**调用规则**:
- 只能被 domain 层调用
- 可以调用 dao 层
- 可以调用下游 RPC
- 返回通用 error(不返回具体业务错误码)

**推荐使用接口**: 便于测试和 mock

**示例**:
```go
// service/dal/user/user_service.go
type UserService interface {
    GetUserByID(ctx context.Context, userID int64) (*User, error)
    BatchGetUsers(ctx context.Context, userIDs []int64) ([]*User, error)
}

type userServiceImpl struct {}

func (s *userServiceImpl) GetUserByID(ctx context.Context, userID int64) (*User, error) {
    // 1. 尝试从缓存获取
    if cached, ok := cache.Get(ctx, userID); ok {
        return cached, nil
    }

    // 2. 从数据库获取
    user, err := dao.QueryUserByID(ctx, userID)
    if err != nil {
        return nil, err
    }

    // 3. 写入缓存
    cache.Set(ctx, userID, user)

    return user, nil
}
```

**注意事项**:
- 推荐使用接口定义,实现依赖注入
- 返回通用 error,不暴露底层实现细节
- 处理缓存、降级、熔断等横切关注点

---

### DAO 层(数据模型层)

**目录**: `service/dao/`

**职责**:
- 提供数据存储实体的原子化 CURD 操作
- 直接操作 MySQL、Redis 等存储
- 执行单表查询和简单关联查询
- 不包含业务逻辑

**调用规则**:
- 只能被 dal 层调用
- 不能调用其他层
- 返回通用 error

**命名约定**: 按数据实体组织,如 `dao/user.go`, `dao/order.go`

**示例**:
```go
// service/dao/user.go
func QueryUserByID(ctx context.Context, userID int64) (*User, error) {
    var user User
    err := db.Where("user_id = ?", userID).First(&user).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

func BatchQueryUsers(ctx context.Context, userIDs []int64) ([]*User, error) {
    var users []*User
    err := db.Where("user_id IN ?", userIDs).Find(&users).Error
    return users, err
}
```

**注意事项**:
- 保持方法原子化,只做单一数据操作
- 不要在此层编写业务逻辑判断
- 使用 ORM 或原生 SQL,避免暴露实现细节

---

### Pkg 层(服务工具层)

**目录**: `pkg/`

**职责**:
- 存放服务内部通用的业务定义
- 工具方法和辅助函数
- 初始化逻辑
- 通用类型定义

**调用规则**:
- 可被所有层调用
- 不能依赖业务层(domain/dal/dao)

**常见子目录**:
- `pkg/app/`: 应用初始化
- `pkg/conf/`: 配置加载
- `pkg/types/`: 通用类型定义
- `pkg/util/`: 工具函数

**注意事项**:
- 不允许直接在 pkg 根目录下创建代码文件
- 必须创建子目录来组织代码
- 避免循环依赖

## 层级依赖关系

```
┌─────────────────────────────────┐
│       Action / Handler          │  接入层(自动生成)
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│          Domain                 │  业务逻辑层(手动编写)
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│           DAL                   │  数据服务层(手动编写)
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│           DAO                   │  数据模型层(手动编写)
└─────────────────────────────────┘

           ┌──────────────┐
           │     Pkg      │  工具层(可被所有层调用)
           └──────────────┘
```

**依赖规则**:
1. 上层可以调用下层,下层不能调用上层
2. 同层服务之间不能相互调用
3. Pkg 可被所有层调用,但不能依赖业务层

## 自动生成与手动编写

| 层级 | 目录 | 生成方式 | 是否可修改 | 能否手动创建文件 |
|------|------|---------|----------|----------------|
| Router | router/ | gdp update 自动生成 | 不可修改 | 禁止 |
| Handler | handler/ | gdp update 自动生成 | 不可修改 | 禁止 |
| Action | action/ | gdp update 自动生成 | 可添加逻辑 | 禁止 |
| Domain | service/domain/ | gdp update 自动生成 | 可编写业务代码 | 禁止 |
| DAL | service/dal/ | 需手动创建 | 手动编写 | 允许 |
| DAO | service/dao/ | 需手动创建 | 手动编写 | 允许 |
| Pkg | pkg/ | 需手动创建 | 手动编写 | 允许 |

**重要提示**:
- `router/`、`handler/`、`action/`、`domain/` 目录下的文件均由 `gdp update` 根据 IDL 自动生成
- **禁止手动创建文件**，只能在已生成的文件中添加业务逻辑
- **不要修改** router/ 和 handler/ 目录中的代码
- **可以修改** action/ 和 domain/ 目录中的代码，添加业务逻辑
- **手动创建** dal/, dao/, pkg/ 目录下的文件

## 最佳实践

1. **单一职责**: 每层只做自己职责范围内的事情,不越界

2. **依赖倒置**: DAL 层使用接口定义,便于测试和 mock

3. **错误处理**: Domain 层返回业务错误码,DAL/DAO 层返回通用 error

4. **代码组织**: 按业务模块组织代码,如 domain/user/, domain/order/

5. **避免循环依赖**: 合理组织包结构,避免循环引用

6. **测试友好**: 为 domain 和 dal 层编写单元测试

## 相关文档

- [action-examples.md](../code-layers/action-examples.md) - Action 层代码示例
- [domain-examples.md](../code-layers/domain-examples.md) - Domain 层代码示例
- [dal-examples.md](../code-layers/dal-examples.md) - DAL 层代码示例
- [dao-examples.md](../code-layers/dao-examples.md) - DAO 层代码示例
- [init-command.md](../commands/init-command.md) - GDP 项目初始化
