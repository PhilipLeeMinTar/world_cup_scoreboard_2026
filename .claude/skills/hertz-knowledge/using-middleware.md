# 中间件

## 基本用法

### 全局中间件

```go
h.Use(LoggerMiddleware, MetricsMiddleware, AuthMiddleware)
```

### 路由级中间件

```go
h.GET("/admin", AdminMiddleware, AdminHandler)
```

### 路由分组中间件

```go
admin := h.Group("/admin", AdminAuthMiddleware)
{
    admin.GET("/users", GetUsers)
}
```

## 编写中间件

```go
func MyMiddleware(c context.Context, ctx *app.RequestContext) {
    // 前置处理
    startTime := time.Now()
    
    ctx.Next()  // 调用下一个 handler
    
    // 后置处理
    duration := time.Since(startTime)
}
```

### 中止请求

```go
func AuthMiddleware(c context.Context, ctx *app.RequestContext) {
    token := ctx.GetHeader("Authorization")
    if token == "" {
        ctx.JSON(401, map[string]string{"error": "Unauthorized"})
        ctx.Abort()
        return
    }
    ctx.Next()
}
```

## 常用中间件

### Recovery

```go
import "code.byted.org/middleware/hertz/pkg/app/middlewares/server/recovery"
h.Use(recovery.Recovery())
```

### CORS

```go
import "github.com/hertz-contrib/cors"
h.Use(cors.New(cors.Config{
    AllowOrigins: []string{"https://example.com"},
    AllowMethods: []string{"GET", "POST", "PUT", "DELETE"},
}))
```

### Gzip 压缩

```go
import "github.com/hertz-contrib/gzip"
h.Use(gzip.Gzip(gzip.DefaultCompression))
```

参考在线文档获取更多中间件示例。
