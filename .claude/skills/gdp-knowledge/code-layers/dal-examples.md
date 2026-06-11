# DAL 层代码示例

## 概述

DAL 层(数据服务层)封装数据相关的业务逻辑,调用下游 RPC 服务,聚合 DAO 层数据,处理缓存逻辑。本文档提供 DAL 层的实际代码示例。

## 接口定义模式

### 基础接口定义

```go
// service/dal/user/interface.go
package user

import "context"

type UserService interface {
    GetUserByID(ctx context.Context, userID int64) (*User, error)
    BatchGetUsers(ctx context.Context, userIDs []int64) ([]*User, error)
    UpdateUserProfile(ctx context.Context, userID int64, profile *ProfileUpdate) error
}

type userServiceImpl struct {
    cache Cache
    dao   DAO
}

func NewUserService(cache Cache, dao DAO) UserService {
    return &userServiceImpl{
        cache: cache,
        dao:   dao,
    }
}
```

## 缓存处理模式

### 单条查询with缓存

```go
// service/dal/user/get_user.go
package user

func (s *userServiceImpl) GetUserByID(ctx context.Context, userID int64) (*User, error) {
    // 1. 尝试从缓存获取
    cacheKey := fmt.Sprintf("user:%d", userID)
    if cached, ok := s.cache.Get(ctx, cacheKey); ok {
        return cached.(*User), nil
    }

    // 2. 从数据库获取
    user, err := s.dao.QueryUserByID(ctx, userID)
    if err != nil {
        return nil, err
    }

    // 3. 写入缓存
    s.cache.Set(ctx, cacheKey, user, 300) // 5分钟过期

    return user, nil
}
```

### 批量查询with缓存

```go
func (s *userServiceImpl) BatchGetUsers(ctx context.Context, userIDs []int64) ([]*User, error) {
    result := make([]*User, 0, len(userIDs))
    missIDs := make([]int64, 0)

    // 1. 批量从缓存获取
    for _, userID := range userIDs {
        cacheKey := fmt.Sprintf("user:%d", userID)
        if cached, ok := s.cache.Get(ctx, cacheKey); ok {
            result = append(result, cached.(*User))
        } else {
            missIDs = append(missIDs, userID)
        }
    }

    // 2. 查询缓存未命中的数据
    if len(missIDs) > 0 {
        users, err := s.dao.BatchQueryUsers(ctx, missIDs)
        if err != nil {
            return nil, err
        }

        // 3. 写入缓存并添加到结果
        for _, user := range users {
            cacheKey := fmt.Sprintf("user:%d", user.UserID)
            s.cache.Set(ctx, cacheKey, user, 300)
            result = append(result, user)
        }
    }

    return result, nil
}
```

## RPC 调用模式

### 下游服务调用

```go
// service/dal/payment/payment_service.go
package payment

type PaymentService interface {
    CreatePayment(ctx context.Context, orderID int64, amount int64) (*Payment, error)
    GetPaymentStatus(ctx context.Context, paymentID string) (PaymentStatus, error)
}

type paymentServiceImpl struct {
    rpcClient PaymentRPCClient
}

func (s *paymentServiceImpl) CreatePayment(ctx context.Context, orderID int64, amount int64) (*Payment, error) {
    // 调用下游 RPC 服务
    resp, err := s.rpcClient.CreatePayment(ctx, &payment_rpc.CreatePaymentRequest{
        OrderID: orderID,
        Amount:  amount,
    })
    if err != nil {
        return nil, err
    }

    return &Payment{
        PaymentID: resp.GetPaymentID(),
        Status:    resp.GetStatus(),
    }, nil
}
```

## 数据聚合模式

### 多数据源聚合

```go
// service/dal/order/get_order_detail.go
package order

func (s *orderServiceImpl) GetOrderWithItems(ctx context.Context, orderID int64) (*OrderDetail, error) {
    // 1. 获取订单基础信息
    order, err := s.dao.QueryOrderByID(ctx, orderID)
    if err != nil {
        return nil, err
    }

    // 2. 获取订单商品
    items, err := s.dao.QueryOrderItems(ctx, orderID)
    if err != nil {
        return nil, err
    }

    // 3. 聚合返回
    return &OrderDetail{
        Order: order,
        Items: items,
    }, nil
}
```

## 事务处理模式

```go
// service/dal/order/create_order.go
package order

func (s *orderServiceImpl) CreateOrderWithItems(ctx context.Context, req *OrderCreate) (int64, error) {
    // 开启事务
    tx, err := s.dao.BeginTx(ctx)
    if err != nil {
        return 0, err
    }
    defer tx.Rollback()

    // 1. 创建订单
    orderID, err := tx.InsertOrder(ctx, req)
    if err != nil {
        return 0, err
    }

    // 2. 创建订单商品
    for _, item := range req.Items {
        err = tx.InsertOrderItem(ctx, orderID, item)
        if err != nil {
            return 0, err
        }
    }

    // 3. 扣减库存
    for _, item := range req.Items {
        err = tx.DeductStock(ctx, item.ProductID, item.Quantity)
        if err != nil {
            return 0, err
        }
    }

    // 提交事务
    if err := tx.Commit(); err != nil {
        return 0, err
    }

    return orderID, nil
}
```

## 最佳实践

1. **使用接口定义**: 便于测试和 mock
2. **合理使用缓存**: 提高查询性能
3. **返回通用error**: 不暴露底层实现细节
4. **处理降级熔断**: RPC 调用需要容错处理
5. **事务管理**: 确保数据一致性

## 相关文档

- [arch-code-layers-guide.md](arch-code-layers-guide.md) - 代码分层架构指南
- [arch-dao-layer-examples.md](arch-dao-layer-examples.md) - DAO 层示例
