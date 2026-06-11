# 路由管理

## 基本路由

```go
h.GET("/users", getUsers)
h.POST("/users", createUser)
h.PUT("/users/:id", updateUser)
h.DELETE("/users/:id", deleteUser)
```

## 路由分组

```go
api := h.Group("/api/v1")
{
    api.GET("/users", getUsers)
    api.POST("/users", createUser)
}
```

## 路径参数

```go
h.GET("/user/:id", func(c context.Context, ctx *app.RequestContext) {
    id := ctx.Param("id")
})
```

参考: [Hertz Server API示例](https://bytedance.larkoffice.com/wiki/wikcnWyHh0tIeUulzS2IQalFL9f)
