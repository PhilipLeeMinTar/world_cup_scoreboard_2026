# Hertz Server 基础

## 创建 Server 实例

### 方式1: 使用标准中间件 (推荐)

```go
import "code.byted.org/middleware/hertz/byted"

func main() {
    byted.Init() // 初始化内部组件
    h := byted.Default() // 带标准中间件
    h.Spin()
}
```

包含的标准中间件:
- 日志中间件
- Metrics 监控
- 链路追踪
- Recovery (panic 恢复)

### 方式2: 纯净实例

```go
import "code.byted.org/middleware/hertz/pkg/app/server"

func main() {
    h := server.New() // 不带任何中间件
    h.Spin()
}
```

## Server 配置

### 基本配置

```go
h := byted.Default(
    server.WithHostPorts(":8080"),              // 监听端口
    server.WithReadTimeout(3*time.Second),      // 读超时
    server.WithWriteTimeout(3*time.Second),     // 写超时
    server.WithIdleTimeout(60*time.Second),     // 空闲超时
    server.WithMaxRequestBodySize(20<<20),      // 20MB
)
```

### 通过配置文件

`conf/hertz.config.yaml`:

```yaml
Server:
  Address: :8888
  IdleTimeout: 60s
  ReadTimeout: 3s
  WriteTimeout: 3s
  MaxRequestBodySize: 20971520  # 20MB
```

## 路由注册

### HTTP 方法

```go
h.GET("/get", handler)
h.POST("/post", handler)
h.PUT("/put", handler)
h.DELETE("/delete", handler)
h.PATCH("/patch", handler)
h.HEAD("/head", handler)
h.OPTIONS("/options", handler)
h.ANY("/any", handler)  // 匹配所有方法
```

### 路由分组

```go
v1 := h.Group("/api/v1")
{
    v1.GET("/users", getUsers)
    v1.POST("/users", createUser)

    user := v1.Group("/user/:id")
    {
        user.GET("", getUser)
        user.PUT("", updateUser)
        user.DELETE("", deleteUser)
    }
}
```

### 路由参数

```go
// 路径参数
h.GET("/user/:id", func(ctx context.Context, c *app.RequestContext) {
    id := c.Param("id")
    c.String(200, "User ID: "+id)
})

// 通配符
h.GET("/files/*filepath", func(ctx context.Context, c *app.RequestContext) {
    path := c.Param("filepath")
    c.String(200, "File: "+path)
})
```

## Handler 函数

### 函数签名

```go
type HandlerFunc func(c context.Context, ctx *app.RequestContext)
```

**注意:** Hertz 1.0 使用双 context:
- `c context.Context`: 标准 Context,协程安全,用于透传
- `ctx *app.RequestContext`: 请求 Context,非协程安全

### 基本用法

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 获取请求参数
    name := ctx.Query("name")

    // 返回 JSON
    ctx.JSON(200, map[string]string{
        "message": "Hello " + name,
    })
}
```

## 启动与停止

### 启动服务

```go
h.Spin()  // 阻塞直到收到停止信号
```

### 优雅退出

Server 会自动处理 SIGTERM 信号,优雅退出流程:
1. 停止接受新请求
2. 等待已有请求处理完成
3. 关闭资源连接
4. 退出进程

### 自定义退出逻辑

```go
h.OnShutdown = append(h.OnShutdown, func(ctx context.Context) {
    // 清理资源
    log.Println("Shutting down...")
})
```

## 中间件

### 全局中间件

```go
h.Use(middleware1, middleware2, middleware3)
```

### 路由级中间件

```go
h.GET("/admin", adminMiddleware, adminHandler)
```

### 分组中间件

```go
admin := h.Group("/admin", authMiddleware)
{
    admin.GET("/users", getUsers)
}
```

## 静态文件

### 提供静态文件

```go
h.Static("/static", "./public")
h.StaticFile("/favicon.ico", "./resources/favicon.ico")
h.StaticFS("/assets", &app.FS{Root: "./assets"})
```

## 错误处理

```go
func handler(c context.Context, ctx *app.RequestContext) {
    if err := doSomething(); err != nil {
        ctx.Error(err)  // 记录错误
        ctx.JSON(500, map[string]string{"error": err.Error()})
        return
    }
    ctx.JSON(200, map[string]string{"status": "ok"})
}
```

## 参考资料

- Server API 示例文档
- 路由注册详解
- 请求上下文详解
