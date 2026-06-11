# Action 层代码示例

## 概述

Action 层是 GDP 框架与业务逻辑之间的桥梁,负责接收请求、参数绑定、调用业务逻辑和返回响应。本文档提供 Action 层的实际代码示例和最佳实践。

## API 服务示例

### 基础 Handler 示例

```go
// action/user/get_user_info.go
package user

import (
    "context"
    "code.byted.org/gdp/af"
    "code.byted.org/tiktok/apimodels/user_service/dto"
    "code.byted.org/tiktok/compkg/errors"
    errcode "code.byted.org/ies/errcode_i18n"
    "your_service/service/domain"
)

// GetUserInfo 获取用户信息
func GetUserInfo(ctx context.Context) (interface{}, af.RespError) {
    var req dto.GetUserInfoRequest

    // 1. 参数绑定
    if err := af.Bind(ctx, &req); err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    // 2. 调用业务逻辑
    resp, err := domain.GetUserInfo(ctx, &req)
    if err != nil {
        return nil, errors.WithError(ctx, err)
    }

    return resp, nil
}
```

### 带参数校验的 Handler

```go
// action/user/update_user_profile.go
package user

func UpdateUserProfile(ctx context.Context) (interface{}, af.RespError) {
    var req dto.UpdateUserProfileRequest

    // 参数绑定
    if err := af.Bind(ctx, &req); err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    // 参数校验
    if req.GetUserID() <= 0 {
        return nil, errors.WithError(ctx, errcode.ERR_PARAM_INVALID)
    }
    if len(req.GetNickname()) == 0 || len(req.GetNickname()) > 50 {
        return nil, errors.WithError(ctx, errcode.ERR_PARAM_INVALID)
    }

    // 调用业务逻辑
    resp, err := domain.UpdateUserProfile(ctx, &req)
    if err != nil {
        return nil, errors.WithError(ctx, err)
    }

    return resp, nil
}
```

### 路由选项配置

```go
// action/user/options.go
package user

import (
    "code.byted.org/gdp/af"
    "code.byted.org/tiktok/compkg/options"
)

// GetUserInfoOpts 配置路由选项
func GetUserInfoOpts() []af.RouterOption {
    dp := options.DefaultAPIOptionalParam()

    // 关闭强制登录校验(允许未登录用户访问)
    dp.CheckUser = false

    return []af.RouterOption{
        options.WithAPIOption(dp, GetUserInfo),
    }
}

// CreateOrderOpts 需要登录的接口
func CreateOrderOpts() []af.RouterOption {
    dp := options.DefaultAPIOptionalParam()

    // 开启强制登录校验(默认)
    dp.CheckUser = true

    // 拦截 FTC 用户
    dp.BlockFTC = true

    return []af.RouterOption{
        options.WithAPIOption(dp, CreateOrder),
    }
}
```

## RPC 服务示例

### 基础 Handler 示例

```go
// handler/user/get_user_info.go
package user

import (
    "context"
    "code.byted.org/tiktok/rpcmodels/user_service"
    "your_service/service/domain"
)

// GetUserInfo RPC 方法实现
func GetUserInfo(ctx context.Context, req *user_service.GetUserInfoRequest) (*user_service.GetUserInfoResponse, error) {
    // 参数校验
    if req.GetUserID() <= 0 {
        return nil, errcode.ERR_PARAM_INVALID
    }

    // 调用业务逻辑
    resp, err := domain.GetUserInfo(ctx, req)
    if err != nil {
        return nil, err
    }

    return resp, nil
}
```

### 批量查询示例

```go
// handler/user/batch_get_users.go
package user

func BatchGetUsers(ctx context.Context, req *user_service.BatchGetUsersRequest) (*user_service.BatchGetUsersResponse, error) {
    // 参数校验
    if len(req.GetUserIDs()) == 0 {
        return nil, errcode.ERR_PARAM_INVALID
    }

    // 限制批量查询数量
    if len(req.GetUserIDs()) > 100 {
        return nil, errcode.ERR_PARAM_TOO_MANY
    }

    // 调用业务逻辑
    users, err := domain.BatchGetUsers(ctx, req.GetUserIDs())
    if err != nil {
        return nil, err
    }

    return &user_service.BatchGetUsersResponse{
        Users: users,
    }, nil
}
```

## 常见模式

### 分页查询

```go
func ListOrders(ctx context.Context) (interface{}, af.RespError) {
    var req dto.ListOrdersRequest

    if err := af.Bind(ctx, &req); err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    // 分页参数校验和默认值
    page := req.GetPage()
    if page <= 0 {
        page = 1
    }

    pageSize := req.GetPageSize()
    if pageSize <= 0 {
        pageSize = 20
    }
    if pageSize > 100 {
        pageSize = 100
    }

    resp, err := domain.ListOrders(ctx, page, pageSize, req.GetStatus())
    if err != nil {
        return nil, errors.WithError(ctx, err)
    }

    return resp, nil
}
```

### 文件上传

```go
func UploadAvatar(ctx context.Context) (interface{}, af.RespError) {
    // 获取上传的文件
    file, err := af.FormFile(ctx, "avatar")
    if err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    // 文件大小校验
    if file.Size > 5*1024*1024 { // 5MB
        return nil, errors.WithError(ctx, errcode.ERR_FILE_TOO_LARGE)
    }

    // 文件类型校验
    if !isImageFile(file.Filename) {
        return nil, errors.WithError(ctx, errcode.ERR_FILE_TYPE_INVALID)
    }

    // 调用业务逻辑上传
    resp, err := domain.UploadAvatar(ctx, file)
    if err != nil {
        return nil, errors.WithError(ctx, err)
    }

    return resp, nil
}
```

### 响应格式定制

```go
// 返回 Protobuf 格式
func GetUserInfoProtobufOpts() []af.RouterOption {
    dp := options.DefaultAPIOptionalParam()
    return []af.RouterOption{
        options.WithAPIOption(dp, GetUserInfo,
            options.WithRespProtoBuf(),
        ),
    }
}

// 返回图片格式
func GetQRCodeOpts() []af.RouterOption {
    dp := options.DefaultAPIOptionalParam()
    return []af.RouterOption{
        options.WithAPIOption(dp, GetQRCode,
            options.WithRespImage(),
        ),
    }
}
```

## 错误处理

### 标准错误处理

```go
func CreateOrder(ctx context.Context) (interface{}, af.RespError) {
    var req dto.CreateOrderRequest

    if err := af.Bind(ctx, &req); err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    resp, err := domain.CreateOrder(ctx, &req)
    if err != nil {
        // 业务错误码直接返回
        return nil, errors.WithError(ctx, err)
    }

    return resp, nil
}
```

### 自定义错误响应

```go
func DeleteUser(ctx context.Context) (interface{}, af.RespError) {
    var req dto.DeleteUserRequest

    if err := af.Bind(ctx, &req); err != nil {
        return nil, errors.WithError(ctx, errcode.ERR_INVALID_PARAM)
    }

    err := domain.DeleteUser(ctx, req.GetUserID())
    if err != nil {
        // 根据错误类型返回不同错误码
        if err == domain.ErrUserNotFound {
            return nil, errors.WithError(ctx, errcode.ERR_USER_NOT_FOUND)
        }
        if err == domain.ErrPermissionDenied {
            return nil, errors.WithError(ctx, errcode.ERR_PERMISSION_DENIED)
        }
        return nil, errors.WithError(ctx, errcode.ERR_INTERNAL)
    }

    return &dto.DeleteUserResponse{
        Success: true,
    }, nil
}
```

## 最佳实践

1. **保持精简**: Action 层只做参数绑定、基本校验、调用 domain 层
2. **参数校验**: 在 Action 层进行基本参数校验,复杂业务校验在 domain 层
3. **错误处理**: 使用 compkg/errors 统一包装错误码
4. **路由选项**: 合理配置登录校验、FTC 拦截等选项
5. **不写业务逻辑**: 所有业务逻辑必须在 domain 层实现

## 相关文档

- [arch-code-layers-guide.md](arch-code-layers-guide.md) - 代码分层架构指南
- [arch-domain-layer-examples.md](arch-domain-layer-examples.md) - Domain 层示例
- [init-command.md](../commands/init-command.md) - GDP 项目初始化
