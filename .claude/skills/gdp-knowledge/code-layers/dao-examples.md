# DAO 层代码示例

## 概述

DAO 层(数据模型层)提供数据存储实体的原子化 CURD 操作,直接操作 MySQL、Redis 等存储。本文档提供 DAO 层的实际代码示例。

## MySQL 操作示例

### 基础 CRUD 操作

```go
// service/dao/user.go
package dao

import (
    "context"
    "gorm.io/gorm"
)

type User struct {
    UserID    int64  `gorm:"column:user_id;primaryKey"`
    Nickname  string `gorm:"column:nickname"`
    Avatar    string `gorm:"column:avatar"`
    Status    int32  `gorm:"column:status"`
    CreatedAt int64  `gorm:"column:created_at"`
}

func (*User) TableName() string {
    return "users"
}

// QueryUserByID 根据ID查询用户
func QueryUserByID(ctx context.Context, userID int64) (*User, error) {
    var user User
    err := db.WithContext(ctx).
        Where("user_id = ?", userID).
        First(&user).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

// BatchQueryUsers 批量查询用户
func BatchQueryUsers(ctx context.Context, userIDs []int64) ([]*User, error) {
    var users []*User
    err := db.WithContext(ctx).
        Where("user_id IN ?", userIDs).
        Find(&users).Error
    return users, err
}

// InsertUser 插入用户
func InsertUser(ctx context.Context, user *User) error {
    return db.WithContext(ctx).Create(user).Error
}

// UpdateUser 更新用户
func UpdateUser(ctx context.Context, userID int64, updates map[string]interface{}) error {
    return db.WithContext(ctx).
        Model(&User{}).
        Where("user_id = ?", userID).
        Updates(updates).Error
}

// DeleteUser 删除用户(软删除)
func DeleteUser(ctx context.Context, userID int64) error {
    return db.WithContext(ctx).
        Where("user_id = ?", userID).
        Update("status", StatusDeleted).Error
}
```

### 复杂查询

```go
// ListOrders 分页查询订单
func ListOrders(ctx context.Context, userID int64, offset, limit int32, status int32) ([]*Order, int64, error) {
    var orders []*Order
    var total int64

    query := db.WithContext(ctx).Model(&Order{}).Where("user_id = ?", userID)

    // 状态过滤
    if status > 0 {
        query = query.Where("status = ?", status)
    }

    // 查询总数
    if err := query.Count(&total).Error; err != nil {
        return nil, 0, err
    }

    // 分页查询
    err := query.Offset(int(offset)).
        Limit(int(limit)).
        Order("created_at DESC").
        Find(&orders).Error

    return orders, total, err
}
```

## Redis 操作示例

### 基础 Redis 操作

```go
// service/dao/redis.go
package dao

import (
    "context"
    "encoding/json"
    "time"
    "github.com/go-redis/redis/v8"
)

// GetUserCache 从 Redis 获取用户缓存
func GetUserCache(ctx context.Context, userID int64) (*User, error) {
    key := fmt.Sprintf("user:%d", userID)

    val, err := rdb.Get(ctx, key).Result()
    if err == redis.Nil {
        return nil, nil // 缓存未命中
    }
    if err != nil {
        return nil, err
    }

    var user User
    if err := json.Unmarshal([]byte(val), &user); err != nil {
        return nil, err
    }

    return &user, nil
}

// SetUserCache 设置用户缓存
func SetUserCache(ctx context.Context, user *User, expiration time.Duration) error {
    key := fmt.Sprintf("user:%d", user.UserID)

    data, err := json.Marshal(user)
    if err != nil {
        return err
    }

    return rdb.Set(ctx, key, data, expiration).Err()
}

// DeleteUserCache 删除用户缓存
func DeleteUserCache(ctx context.Context, userID int64) error {
    key := fmt.Sprintf("user:%d", userID)
    return rdb.Del(ctx, key).Err()
}
```

## 事务操作示例

```go
// service/dao/transaction.go
package dao

// CreateOrderWithItems 创建订单(事务)
func CreateOrderWithItems(ctx context.Context, order *Order, items []*OrderItem) (int64, error) {
    var orderID int64

    err := db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
        // 1. 创建订单
        if err := tx.Create(order).Error; err != nil {
            return err
        }
        orderID = order.OrderID

        // 2. 创建订单商品
        for _, item := range items {
            item.OrderID = orderID
            if err := tx.Create(item).Error; err != nil {
                return err
            }
        }

        // 3. 扣减库存
        for _, item := range items {
            result := tx.Model(&Product{}).
                Where("product_id = ? AND stock >= ?", item.ProductID, item.Quantity).
                Update("stock", gorm.Expr("stock - ?", item.Quantity))

            if result.Error != nil {
                return result.Error
            }
            if result.RowsAffected == 0 {
                return ErrStockNotEnough
            }
        }

        return nil
    })

    return orderID, err
}
```

## 最佳实践

1. **原子化操作**: 每个方法只做单一数据操作
2. **不含业务逻辑**: 不在 DAO 层进行业务判断
3. **返回通用error**: 使用 error 而非业务错误码
4. **使用ORM**: 推荐使用 GORM,避免 SQL 注入
5. **事务管理**: 复杂操作使用事务确保一致性

## 相关文档

- [arch-code-layers-guide.md](arch-code-layers-guide.md) - 代码分层架构指南
- [arch-dal-layer-examples.md](arch-dal-layer-examples.md) - DAL 层示例
