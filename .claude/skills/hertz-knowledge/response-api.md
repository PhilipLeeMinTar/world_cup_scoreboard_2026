# Response API 详解

RequestContext 中与响应相关的功能。

## Header 操作

### SetContentType

设置 Content-Type。

```go
func (ctx *RequestContext) SetContentType(contentType string)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.Write([]byte(`{"foo":"bar"}`))
    ctx.SetContentType("application/json; charset=utf-8")
    // Content-Type: application/json; charset=utf-8
})
```

### SetContentTypeBytes

以 []byte 方式设置 Content-Type。

```go
func (ctx *RequestContext) SetContentTypeBytes(contentType []byte)
```

### SetConnectionClose

设置 Connection: close，告知客户端服务器想关闭连接。

```go
func (ctx *RequestContext) SetConnectionClose()
```

### SetStatusCode

设置 Status Code。

```go
func (ctx *RequestContext) SetStatusCode(statusCode int)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.SetStatusCode(consts.StatusOK)
    // Status Code: 200
})
```

### Status

设置 Status Code，SetStatusCode 的别名。

```go
func (ctx *RequestContext) Status(code int)
```

### NotFound

设置 Status Code 为 404。

```go
func (ctx *RequestContext) NotFound()
```

### NotModified

设置 Status Code 为 304。

```go
func (ctx *RequestContext) NotModified()
```

### Redirect

设置 Status Code 以及要跳转的地址。

```go
func (ctx *RequestContext) Redirect(statusCode int, uri []byte)
```

示例:

```go
// 内部重定向
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.Redirect(consts.StatusFound, []byte("/pet"))
})

// 外部重定向
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.Redirect(consts.StatusFound, []byte("http://www.example.com/pet"))
})
```

### Header

设置或删除指定 Header。

```go
func (ctx *RequestContext) Header(key, value string)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.Header("My-Name", "tom")        // 设置 Header
    ctx.Header("My-Name", "")           // 删除 Header
    ctx.Header("X-Custom", "value")     // 设置自定义 Header
})
```

### SetCookie

设置 Cookie。

```go
func (ctx *RequestContext) SetCookie(name, value string, maxAge int, path, domain string, sameSite protocol.CookieSameSite, secure, httpOnly bool)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.SetCookie("user", "hertz", 3600, "/", "localhost", protocol.CookieSameSiteLaxMode, true, true)
    // Set-Cookie: user=hertz; max-age=3600; domain=localhost; path=/; HttpOnly; secure; SameSite=Lax
})
```

### AbortWithStatus

设置 Status Code 并终止后续的 Handler。

```go
func (ctx *RequestContext) AbortWithStatus(code int)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.AbortWithStatus(consts.StatusUnauthorized)
}, func(c context.Context, ctx *app.RequestContext) {
    // 不会执行
})
```

### AbortWithError

设置 Status Code 收集 Error 并终止后续的 Handler，返回 Error。

```go
func (ctx *RequestContext) AbortWithError(code int, err error) *errors.Error
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.AbortWithError(consts.StatusInternalServerError, errors.New("hertz error"))
    err := ctx.Errors.String()
    // err == "Error #01: hertz error"
}, func(c context.Context, ctx *app.RequestContext) {
    // 不会执行
})
```

## 渲染

支持对 JSON、HTML、Protobuf 等的渲染。

### Render

使用自定义渲染器渲染响应。

```go
func (ctx *RequestContext) Render(code int, r render.Render)
```

### String

返回字符串响应。

```go
func (ctx *RequestContext) String(code int, format string, values ...interface{})
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.String(200, "Hello %s", "World")
    // Body: Hello World
})
```

### JSON

返回 JSON 响应。

```go
func (ctx *RequestContext) JSON(code int, obj interface{})
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.JSON(200, map[string]interface{}{
        "code": 0,
        "data": user,
    })
})
```

### PureJSON

返回 JSON 响应，不转义 HTML 字符。

```go
func (ctx *RequestContext) PureJSON(code int, obj interface{})
```

### IndentedJSON

返回格式化的 JSON 响应（带缩进）。

```go
func (ctx *RequestContext) IndentedJSON(code int, obj interface{})
```

### ProtoBuf

返回 Protobuf 响应。

```go
func (ctx *RequestContext) ProtoBuf(code int, obj interface{})
```

### HTML

返回 HTML 响应。

```go
func (ctx *RequestContext) HTML(code int, name string, obj interface{})
```

### Data

返回指定 Content-Type 的数据响应。

```go
func (ctx *RequestContext) Data(code int, contentType string, data []byte)
```

### XML

返回 XML 响应。

```go
func (ctx *RequestContext) XML(code int, obj interface{})
```

## Body 操作

### SetBodyStream

设置 Body Stream 和可选的 Body 大小。用于流式处理场景。

> 注意：bodySize 小于 0 时数据全部写入，大于等于 0 时根据设置的 bodySize 大小写入数据。

```go
func (ctx *RequestContext) SetBodyStream(bodyStream io.Reader, bodySize int)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    data := "hello world"
    r := strings.NewReader(data)
    ctx.SetBodyStream(r, -1) // Body: "hello world"
})

h.GET("/user1", func(c context.Context, ctx *app.RequestContext) {
    data := "hello world"
    r := strings.NewReader(data)
    ctx.SetBodyStream(r, 5) // Body: "hello"
})
```

### SetBodyString

设置 Body。

```go
func (ctx *RequestContext) SetBodyString(body string)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.SetBodyString("hello world") // Body: "hello world"
})
```

### Write

将字节数组添加到 Body 中。

```go
func (ctx *RequestContext) Write(p []byte) (int, error)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.Write([]byte("hello"))
    ctx.Write([]byte(" "))
    ctx.Write([]byte("world"))
    // Body: "hello world"
})
```

### WriteString

设置 Body 并返回大小。

```go
func (ctx *RequestContext) WriteString(s string) (int, error)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    size, _ := ctx.WriteString("hello world")
    // Body: "hello world", size == 11
})
```

### AbortWithMsg

设置 Status Code 和 Body 并终止后续的 Handler。

```go
func (ctx *RequestContext) AbortWithMsg(msg string, statusCode int)
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.AbortWithMsg("abort", consts.StatusOK)
}, func(c context.Context, ctx *app.RequestContext) {
    // 不会执行
})
```

### AbortWithStatusJSON

设置 Status Code 和 JSON 格式 Body 并终止后续的 Handler。

```go
func (ctx *RequestContext) AbortWithStatusJSON(code int, jsonObj interface{})
```

示例:

```go
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.AbortWithStatusJSON(consts.StatusOK, map[string]interface{}{
        "foo":  "bar",
        "html": "<b>",
    })
}, func(c context.Context, ctx *app.RequestContext) {
    // 不会执行
})
```

## 文件操作

### File

将指定文件写入到 Body Stream。

```go
func (ctx *RequestContext) File(filepath string)
```

示例:

```go
h.GET("/download", func(c context.Context, ctx *app.RequestContext) {
    ctx.File("./main.go")
})
```

### FileAttachment

将指定文件写入到 Body Stream 并通过 Content-Disposition 指定为下载。

```go
func (ctx *RequestContext) FileAttachment(filepath, filename string)
```

示例:

```go
h.GET("/download", func(c context.Context, ctx *app.RequestContext) {
    ctx.FileAttachment("./report.xlsx", "2024-report.xlsx")
})
```

### FileFromFS

从文件系统将指定文件写入到 Body Stream。

```go
func (ctx *RequestContext) FileFromFS(filepath string, fs *FS)
```

示例:

```go
h.GET("/download", func(c context.Context, ctx *app.RequestContext) {
    ctx.FileFromFS("./main.go", &app.FS{
        Root:               ".",
        IndexNames:         nil,
        GenerateIndexPages: false,
        AcceptByteRange:    true,
    })
})
```

## 其他

### Flush

把数据刷入被劫持的 Response Writer 中。

```go
func (ctx *RequestContext) Flush() error
```

### GetResponse

获取 Response 对象。

```go
func (ctx *RequestContext) GetResponse() (dst *protocol.Response)
```

## 常用响应模式

### 成功响应

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // JSON 响应
    ctx.JSON(200, map[string]interface{}{
        "code": 0,
        "msg":  "success",
        "data": result,
    })
}
```

### 错误响应

```go
func handler(c context.Context, ctx *app.RequestContext) {
    if err != nil {
        ctx.JSON(500, map[string]interface{}{
            "code": -1,
            "msg":  err.Error(),
        })
        return
    }
}
```

### 重定向

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 临时重定向
    ctx.Redirect(302, []byte("/login"))

    // 永久重定向
    ctx.Redirect(301, []byte("/new-path"))
}
```

### 文件下载

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 直接返回文件内容
    ctx.File("./files/document.pdf")

    // 作为附件下载
    ctx.FileAttachment("./files/report.xlsx", "report-2024.xlsx")
}
```
