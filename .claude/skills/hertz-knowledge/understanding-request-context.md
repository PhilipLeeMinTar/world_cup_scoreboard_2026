# RequestContext 上下文

## Hertz 1.0 双上下文模型

Hertz 1.0 引入了全新的双上下文设计:

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // c: 标准 Go Context (协程安全)
    // ctx: Request Context (非协程安全,高性能)
}
```

### context.Context

**特点:**
- 标准 Go context.Context 接口
- **协程安全**,可以在 goroutine 间传递
- 用于透传元数据、链路追踪信息
- 用于超时控制、取消信号

**使用场景:**
```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 启动 goroutine 处理异步任务
    go func() {
        // 可以安全使用 c
        result := processAsync(c, data)
    }()

    // 调用下游服务,传递 context
    user, err := userClient.GetUser(c, userID)
}
```

### app.RequestContext

**特点:**
- Hertz 专有类型,包含请求和响应信息
- **非协程安全**,不能在并发场景使用
- 高性能,避免不必要的内存分配
- 提供丰富的 HTTP API

**使用场景:**
```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 获取请求参数
    id := ctx.Param("id")
    name := ctx.Query("name")

    // 绑定请求体
    var req Request
    ctx.BindAndValidate(&req)

    // 返回响应
    ctx.JSON(200, response)
}
```

## RequestContext 并发安全

### ❌ 错误用法

**直接在 goroutine 中使用 ctx:**

```go
func handler(c context.Context, ctx *app.RequestContext) {
    go func() {
        // ❌ 错误: ctx 不是协程安全的
        name := ctx.Query("name")  // 可能导致 panic 或数据竞争
        processAsync(name)
    }()
}
```

### ✅ 正确用法 1: 提前读取

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 在 goroutine 外提前读取
    name := ctx.Query("name")

    go func() {
        // 使用提前读取的值
        processAsync(c, name)
    }()
}
```

### ✅ 正确用法 2: 使用 ctx.Copy()

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 创建 RequestContext 的副本
    ctxCopy := ctx.Copy()

    go func() {
        // 使用副本,安全
        name := ctxCopy.Query("name")
        processAsync(c, name)
    }()
}
```

**注意:** `ctx.Copy()` 会复制整个 RequestContext,有性能开销。推荐优先使用"提前读取"方案。

## RequestContext API

### 获取请求参数

#### 路径参数

```go
// 路由: /user/:id
id := ctx.Param("id")
```

#### 查询参数

```go
// URL: /search?keyword=go&page=1
keyword := ctx.Query("keyword")           // 获取参数
page := ctx.DefaultQuery("page", "1")     // 带默认值
```

#### 请求头

```go
userAgent := ctx.GetHeader("User-Agent")
contentType := ctx.ContentType()
```

#### Cookie

```go
sessionID := ctx.Cookie("session_id")
```

#### 请求体

```go
// 绑定 JSON
var req Request
err := ctx.BindAndValidate(&req)

// 原始请求体
body := ctx.Request.Body()
```

### 设置响应

#### JSON 响应

```go
ctx.JSON(200, map[string]interface{}{
    "code": 0,
    "data": user,
})
```

#### String 响应

```go
ctx.String(200, "Hello %s", name)
```

#### HTML 响应

```go
ctx.HTML(200, "<h1>Hello</h1>")
```

#### Redirect

```go
ctx.Redirect(302, "/login")
```

#### 设置响应头

```go
ctx.Header("X-Request-ID", requestID)
ctx.Set("Content-Type", "application/json")
```

#### 设置 Cookie

```go
ctx.SetCookie("session_id", sessionID, 3600, "/", "", false, true)
```

### 元数据操作

#### Set/Get 键值对

```go
// 设置元数据
ctx.Set("user_id", 123)
ctx.Set("user_name", "John")

// 获取元数据
userID := ctx.GetInt64("user_id")
userName := ctx.GetString("user_name")

// 判断是否存在
if value, exists := ctx.Get("user_id"); exists {
    // 存在
}
```

**注意:** 元数据仅在当前请求内有效,用于中间件和 handler 间传递数据。

### 文件操作

#### 文件上传

```go
file, err := ctx.FormFile("file")
if err != nil {
    ctx.JSON(400, map[string]string{"error": err.Error()})
    return
}

// 保存文件
err = ctx.SaveUploadedFile(file, "./uploads/"+file.Filename)
```

#### 文件下载

```go
ctx.File("./files/document.pdf")
```

#### 附件下载

```go
ctx.FileAttachment("./files/report.xlsx", "2024-report.xlsx")
```

### 错误处理

```go
func handler(c context.Context, ctx *app.RequestContext) {
    if err := doSomething(); err != nil {
        // 记录错误
        ctx.Error(err)

        // 返回错误响应
        ctx.JSON(500, map[string]string{
            "error": err.Error(),
        })
        return
    }
}
```

### 中止请求处理

```go
func authMiddleware(c context.Context, ctx *app.RequestContext) {
    token := ctx.GetHeader("Authorization")
    if token == "" {
        ctx.JSON(401, map[string]string{"error": "Unauthorized"})
        ctx.Abort()  // 中止后续 handler 执行
        return
    }
    ctx.Next()  // 继续执行下一个 handler
}
```

## 常见使用场景

### 场景 1: 认证中间件传递用户信息

```go
func AuthMiddleware(c context.Context, ctx *app.RequestContext) {
    token := ctx.GetHeader("Authorization")

    // 验证 token,获取用户信息
    userID, err := validateToken(c, token)
    if err != nil {
        ctx.JSON(401, map[string]string{"error": "Unauthorized"})
        ctx.Abort()
        return
    }

    // 存储到 RequestContext,后续 handler 可用
    ctx.Set("user_id", userID)
    ctx.Next()
}

func GetProfile(c context.Context, ctx *app.RequestContext) {
    // 从 RequestContext 获取用户信息
    userID := ctx.GetInt64("user_id")

    // 业务逻辑
    profile := getUserProfile(c, userID)
    ctx.JSON(200, profile)
}
```

### 场景 2: 异步任务处理

```go
func CreateOrder(c context.Context, ctx *app.RequestContext) {
    var req CreateOrderRequest
    ctx.BindAndValidate(&req)

    // 提前读取需要的数据
    userID := ctx.GetInt64("user_id")
    requestID := ctx.GetHeader("X-Request-ID")

    // 同步创建订单
    order := createOrder(c, &req)

    // 异步发送通知 (使用标准 context,不使用 RequestContext)
    go func() {
        // 使用标准 context,协程安全
        sendNotification(c, userID, order.ID)
        logEvent(c, requestID, "order_created", order.ID)
    }()

    ctx.JSON(200, order)
}
```

## 与 Hertz 0.x 的区别

### Hertz 0.x (单 Context)

```go
// 0.x 版本
func handler(ctx context.Context, c *app.RequestContext) {
    // ctx 和 c 类型相同
}
```

### Hertz 1.x (双 Context)

```go
// 1.x 版本
func handler(c context.Context, ctx *app.RequestContext) {
    // c: 标准 context.Context
    // ctx: *app.RequestContext
}
```

**迁移要点:**
1. 参数顺序变化: `(ctx, c)` → `(c, ctx)`
2. 类型分离: ctx 不再是 context.Context,改用 c
3. 并发安全: 跨 goroutine 使用标准 context c,不使用 RequestContext ctx

## 常见错误

### 错误 1: 在 goroutine 中使用 RequestContext

```go
// ❌ 错误
go func() {
    name := ctx.Query("name")  // panic: 非协程安全
}()

// ✅ 正确
name := ctx.Query("name")
go func() {
    process(c, name)
}()
```

### 错误 2: 混淆 c 和 ctx

```go
// ❌ 错误: 试图用 ctx 做超时控制
ctx.WithTimeout(5 * time.Second)  // RequestContext 没有此方法

// ✅ 正确: 使用标准 context
c, cancel := context.WithTimeout(c, 5*time.Second)
defer cancel()
```

### 错误 3: 在返回后使用 RequestContext

```go
func handler(c context.Context, ctx *app.RequestContext) {
    ctx.JSON(200, data)

    // ❌ 错误: 响应已发送,不应继续使用 ctx
    go func() {
        log := ctx.GetHeader("X-Request-ID")  // 可能已失效
    }()
}
```
