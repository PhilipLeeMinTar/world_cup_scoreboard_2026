# Domain 层代码示例

## 概述

Domain 层(业务逻辑层)是 GDP 应用的核心,负责实现业务逻辑、编排数据服务调用、业务规则验证和数据聚合转换。本文档提供 Domain 层的实际代码示例。

## 基础业务逻辑示例

### 单一实体查询

```go
// service/domain/user/get_user_info.go
package user

import (
    "context"
    "your_service/service/dal"
    "your_service/pkg/types"
    errcode "code.byted.org/ies/errcode_i18n"
)

func GetUserInfo(ctx context.Context, req *dto.GetUserInfoRequest) (*dto.GetUserInfoResponse, error) {
    // 1. 参数校验
    if req.GetUserID() <= 0 {
        return nil, errcode.ERR_PARAM_INVALID
    }

    // 2. 从 DAL 层获取数据
    user, err := dal.GetUserByID(ctx, req.GetUserID())
    if err != nil {
        return nil, errcode.ERR_GET_USER_FAILED
    }

    // 3. 业务规则校验
    if user.Status != types.StatusActive {
        return nil, errcode.ERR_USER_NOT_ACTIVE
    }

    // 4. 构造响应
    return &dto.GetUserInfoResponse{
        User: convertToDTO(user),
    }, nil
}

func convertToDTO(user *dal.User) *dto.UserInfo {
    return &dto.UserInfo{
        UserID:   user.UserID,
        Nickname: user.Nickname,
        Avatar:   user.Avatar,
    }
}
```

### 批量查询与聚合

```go
// service/domain/user/batch_get_users.go
package user

func BatchGetUsers(ctx context.Context, userIDs []int64) ([]*dto.UserInfo, error) {
    // 参数校验
    if len(userIDs) == 0 {
        return []*dto.UserInfo{}, nil
    }

    // 批量查询
    users, err := dal.BatchGetUsers(ctx, userIDs)
    if err != nil {
        return nil, errcode.ERR_GET_USERS_FAILED
    }

    // 数据转换
    result := make([]*dto.UserInfo, 0, len(users))
    for _, user := range users {
        result = append(result, convertToDTO(user))
    }

    return result, nil
}
```

## 复杂业务逻辑示例

### 数据聚合与编排

```go
// service/domain/order/get_order_detail.go
package order

func GetOrderDetail(ctx context.Context, orderID int64) (*dto.OrderDetail, error) {
    // 1. 获取订单基础信息
    order, err := dal.GetOrderByID(ctx, orderID)
    if err != nil {
        return nil, errcode.ERR_GET_ORDER_FAILED
    }

    // 2. 获取订单商品列表
    items, err := dal.GetOrderItems(ctx, orderID)
    if err != nil {
        return nil, errcode.ERR_GET_ORDER_ITEMS_FAILED
    }

    // 3. 获取用户信息(并行调用)
    userCh := make(chan *dal.User, 1)
    go func() {
        user, _ := dal.GetUserByID(ctx, order.UserID)
        userCh <- user
    }()

    // 4. 获取支付信息
    payment, err := dal.GetPaymentByOrderID(ctx, orderID)
    if err != nil {
        return nil, errcode.ERR_GET_PAYMENT_FAILED
    }

    user := <-userCh

    // 5. 聚合数据
    return &dto.OrderDetail{
        Order:   convertOrderToDTO(order),
        Items:   convertItemsToDTO(items),
        User:    convertUserToDTO(user),
        Payment: convertPaymentToDTO(payment),
    }, nil
}
```

### 创建操作与事务

```go
// service/domain/order/create_order.go
package order

func CreateOrder(ctx context.Context, req *dto.CreateOrderRequest) (*dto.CreateOrderResponse, error) {
    // 1. 参数校验
    if len(req.GetItems()) == 0 {
        return nil, errcode.ERR_ORDER_ITEMS_EMPTY
    }

    // 2. 业务规则校验
    totalAmount := calculateTotalAmount(req.GetItems())
    if totalAmount <= 0 {
        return nil, errcode.ERR_ORDER_AMOUNT_INVALID
    }

    // 3. 库存检查
    for _, item := range req.GetItems() {
        available, err := dal.CheckStock(ctx, item.GetProductID(), item.GetQuantity())
        if err != nil {
            return nil, errcode.ERR_CHECK_STOCK_FAILED
        }
        if !available {
            return nil, errcode.ERR_STOCK_NOT_ENOUGH
        }
    }

    // 4. 创建订单(调用 DAL 层的事务方法)
    orderID, err := dal.CreateOrderWithItems(ctx, &dal.OrderCreate{
        UserID:      req.GetUserID(),
        TotalAmount: totalAmount,
        Items:       convertItemsFromDTO(req.GetItems()),
    })
    if err != nil {
        return nil, errcode.ERR_CREATE_ORDER_FAILED
    }

    return &dto.CreateOrderResponse{
        OrderID: orderID,
    }, nil
}
```

### 状态机与业务流程

```go
// service/domain/order/cancel_order.go
package order

func CancelOrder(ctx context.Context, orderID, userID int64) error {
    // 1. 获取订单
    order, err := dal.GetOrderByID(ctx, orderID)
    if err != nil {
        return errcode.ERR_GET_ORDER_FAILED
    }

    // 2. 权限校验
    if order.UserID != userID {
        return errcode.ERR_PERMISSION_DENIED
    }

    // 3. 状态机校验
    if !canCancelOrder(order.Status) {
        return errcode.ERR_ORDER_CANNOT_CANCEL
    }

    // 4. 执行取消操作
    err = dal.UpdateOrderStatus(ctx, orderID, types.OrderStatusCancelled)
    if err != nil {
        return errcode.ERR_UPDATE_ORDER_FAILED
    }

    // 5. 退还库存
    items, _ := dal.GetOrderItems(ctx, orderID)
    for _, item := range items {
        dal.ReturnStock(ctx, item.ProductID, item.Quantity)
    }

    // 6. 退款(如已支付)
    if order.PaymentStatus == types.PaymentStatusPaid {
        dal.CreateRefund(ctx, orderID, order.TotalAmount)
    }

    return nil
}

func canCancelOrder(status int32) bool {
    return status == types.OrderStatusPending ||
           status == types.OrderStatusPaid
}
```

## 错误处理模式

### 业务错误码返回

```go
func UpdateUserProfile(ctx context.Context, req *dto.UpdateUserProfileRequest) error {
    // 参数校验
    if req.GetUserID() <= 0 {
        return errcode.ERR_PARAM_INVALID
    }

    // 获取用户
    user, err := dal.GetUserByID(ctx, req.GetUserID())
    if err != nil {
        return errcode.ERR_USER_NOT_FOUND
    }

    // 业务规则校验
    if user.Status == types.StatusBanned {
        return errcode.ERR_USER_BANNED
    }

    // 更新操作
    err = dal.UpdateUserProfile(ctx, req.GetUserID(), &dal.ProfileUpdate{
        Nickname: req.GetNickname(),
        Avatar:   req.GetAvatar(),
    })
    if err != nil {
        return errcode.ERR_UPDATE_PROFILE_FAILED
    }

    return nil
}
```

## 分页查询模式

```go
// service/domain/order/list_orders.go
package order

func ListOrders(ctx context.Context, userID int64, page, pageSize int32, status int32) (*dto.ListOrdersResponse, error) {
    // 参数校验
    if page <= 0 {
        page = 1
    }
    if pageSize <= 0 || pageSize > 100 {
        pageSize = 20
    }

    // 计算偏移量
    offset := (page - 1) * pageSize

    // 查询订单列表
    orders, total, err := dal.ListOrdersByUser(ctx, userID, offset, pageSize, status)
    if err != nil {
        return nil, errcode.ERR_LIST_ORDERS_FAILED
    }

    // 转换为 DTO
    orderDTOs := make([]*dto.OrderInfo, 0, len(orders))
    for _, order := range orders {
        orderDTOs = append(orderDTOs, convertOrderToDTO(order))
    }

    return &dto.ListOrdersResponse{
        Orders:     orderDTOs,
        Total:      total,
        Page:       page,
        PageSize:   pageSize,
        TotalPages: (total + int64(pageSize) - 1) / int64(pageSize),
    }, nil
}
```

## 最佳实践

1. **单一职责**: 每个函数只做一件事,保持函数精简
2. **业务规则集中**: 所有业务逻辑和规则校验都在 domain 层
3. **错误码明确**: 返回明确的业务错误码,便于调用方理解
4. **数据转换**: 统一进行 DAL 实体到 DTO 的转换
5. **避免直接依赖 DAO**: 通过 DAL 层访问数据,不跨层调用
6. **测试覆盖**: 为 domain 层编写完整的单元测试

## 相关文档

- [arch-code-layers-guide.md](arch-code-layers-guide.md) - 代码分层架构指南
- [arch-action-layer-examples.md](arch-action-layer-examples.md) - Action 层示例
- [arch-dal-layer-examples.md](arch-dal-layer-examples.md) - DAL 层示例
