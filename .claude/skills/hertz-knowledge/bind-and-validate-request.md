# Binding 参数绑定

## 什么是 Binding?

Binding 是 Hertz 的参数绑定框架,用于自动将 HTTP 请求参数绑定到 Go struct,并进行验证。

基于 [gotagexpr](https://github.com/bytedance/go-tagexpr) 实现,支持:
- 自动参数绑定
- 数据验证
- 类型转换
- 自定义验证规则

## 基本用法

### BindAndValidate

推荐使用的 API,包含绑定和验证。

```go
func handler(c context.Context, ctx *app.RequestContext) {
    var req api.GetUserRequest
    err := ctx.BindAndValidate(&req)
    if err != nil {
        ctx.JSON(400, map[string]string{"error": err.Error()})
        return
    }

    // 使用已绑定和验证的 req
    ctx.JSON(200, req)
}
```

### Bind (仅绑定)

只绑定参数,不进行验证。

```go
func handler(c context.Context, ctx *app.RequestContext) {
    var req api.GetUserRequest
    err := ctx.Bind(&req)
    if err != nil {
        ctx.JSON(400, map[string]string{"error": err.Error()})
        return
    }
    // req 已绑定但未验证
}
```

### Validate (仅验证)

对已填充的 struct 进行验证。

```go
func handler(c context.Context, ctx *app.RequestContext) {
    req := &api.GetUserRequest{ID: 123}
    err := ctx.Validate(req)
    if err != nil {
        ctx.JSON(400, map[string]string{"error": err.Error()})
        return
    }
}
```

## Struct Tag 定义

### query - URL 查询参数

```go
type GetUserRequest struct {
    ID   int64  `query:"id"`
    Name string `query:"name"`
}
```

**HTTP 请求:**
```
GET /api/user?id=123&name=John
```

### path - 路径参数

```go
type GetUserRequest struct {
    ID int64 `path:"id"`
}

// 路由定义
h.GET("/api/user/:id", handler)
```

**HTTP 请求:**
```
GET /api/user/123
```

### form - 表单参数

```go
type LoginRequest struct {
    Username string `form:"username"`
    Password string `form:"password"`
}
```

**HTTP 请求:**
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=123456
```

### json - JSON Body

```go
type CreateUserRequest struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}
```

**HTTP 请求:**
```
POST /api/user
Content-Type: application/json

{
  "name": "John",
  "email": "john@example.com"
}
```

### header - HTTP Header

```go
type Request struct {
    Authorization string `header:"Authorization"`
    UserAgent     string `header:"User-Agent"`
}
```

### cookie - Cookie 值

```go
type Request struct {
    SessionID string `cookie:"session_id"`
}
```

### raw_body - 原始请求体

```go
type UploadRequest struct {
    Content []byte `raw_body:"content"`
}
```

## 验证规则

### vd Tag

使用 `vd` tag 定义验证规则。

```go
type CreateUserRequest struct {
    Name  string `json:"name" vd:"len($)>0 && len($)<50"`
    Email string `json:"email" vd:"email($)"`
    Age   int    `json:"age" vd:"$>0 && $<150"`
}
```

### 常用验证表达式

| 表达式 | 说明 | 示例 |
|--------|------|------|
| `len($)>0` | 必填,长度>0 | 必填字符串 |
| `len($)>=6 && len($)<=20` | 长度范围 | 密码长度 6-20 |
| `$>0` | 大于 0 | 正整数 |
| `$>=1 && $<=100` | 数值范围 | 1-100 的整数 |
| `$>=0.0` | 非负浮点数 | 价格 |
| `email($)` | 邮箱格式 | 邮箱验证 |
| `regexp('^[a-zA-Z0-9]+$')` | 正则匹配 | 字母数字组合 |
| `len($)==11 && regexp('^1[3-9]\\d{9}$')` | 手机号 | 中国手机号 |

### 嵌套结构验证

```go
type Address struct {
    Street string `json:"street" vd:"len($)>0"`
    City   string `json:"city" vd:"len($)>0"`
}

type CreateUserRequest struct {
    Name    string  `json:"name" vd:"len($)>0"`
    Address Address `json:"address"`
}
```

### 切片验证

```go
type BatchRequest struct {
    IDs []int64 `json:"ids" vd:"len($)>0 && len($)<=100"`
}
```

## 类型转换

Binding 自动处理常见类型转换:

```go
type Request struct {
    ID       int64     `query:"id"`        // "123" -> 123
    Price    float64   `query:"price"`     // "19.99" -> 19.99
    Active   bool      `query:"active"`    // "true" -> true
    Tags     []string  `query:"tags"`      // "a,b,c" -> ["a","b","c"]
    CreateAt time.Time `query:"create_at"` // "2023-01-01T00:00:00Z"
}
```

## 默认值

### default Tag

```go
type Request struct {
    Page     int    `query:"page,default=1"`
    PageSize int    `query:"page_size,default=10"`
    Status   string `query:"status,default=active"`
}
```

如果请求中没有提供参数,使用默认值。

## 可选参数

### 使用指针

```go
type Request struct {
    Name  string  `json:"name"`           // 必填
    Email *string `json:"email"`          // 可选
    Age   *int    `json:"age,omitempty"`  // 可选,omitempty 表示零值不序列化
}
```

### 检查可选参数

```go
func handler(c context.Context, ctx *app.RequestContext) {
    var req Request
    ctx.BindAndValidate(&req)

    if req.Email != nil {
        // Email 参数存在
        emailValue := *req.Email
    }
}
```

## 文件上传

### 单文件

```go
type UploadRequest struct {
    File *multipart.FileHeader `form:"file"`
}

func handler(c context.Context, ctx *app.RequestContext) {
    var req UploadRequest
    err := ctx.BindAndValidate(&req)
    if err != nil {
        ctx.JSON(400, map[string]string{"error": err.Error()})
        return
    }

    // 保存文件
    ctx.SaveUploadedFile(req.File, "./uploads/"+req.File.Filename)
    ctx.JSON(200, map[string]string{"message": "uploaded"})
}
```

### 多文件

```go
type UploadRequest struct {
    Files []*multipart.FileHeader `form:"files"`
}

func handler(c context.Context, ctx *app.RequestContext) {
    form, _ := ctx.MultipartForm()
    files := form.File["files"]

    for _, file := range files {
        ctx.SaveUploadedFile(file, "./uploads/"+file.Filename)
    }
    ctx.JSON(200, map[string]string{"message": "uploaded"})
}
```

## 最佳实践

### 1. 使用 BindAndValidate

推荐使用 `BindAndValidate` 而不是分别调用 `Bind` 和 `Validate`。

```go
// 推荐
ctx.BindAndValidate(&req)

// 不推荐
ctx.Bind(&req)
ctx.Validate(&req)
```

### 2. 定义清晰的验证规则

在 struct tag 中明确验证规则,便于维护。

```go
type CreateUserRequest struct {
    Name  string `json:"name" vd:"len($)>=2 && len($)<=50"`
    Email string `json:"email" vd:"email($)"`
    Age   int    `json:"age" vd:"$>=18 && $<=120"`
}
```
