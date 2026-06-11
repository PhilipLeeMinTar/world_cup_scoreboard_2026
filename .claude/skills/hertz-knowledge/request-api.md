# Request API 详解

RequestContext 中与请求相关的功能。

## URI 操作

### Host

获取请求的主机地址。

```go
func (ctx *RequestContext) Host() []byte
```

示例:

```go
// GET http://example.com
h.GET("/", func(c context.Context, ctx *app.RequestContext) {
    host := ctx.Host() // host == []byte("example.com")
})
```

### FullPath

获取匹配的路由完整路径，对于未匹配的路由返回空字符串。

```go
func (ctx *RequestContext) FullPath() string
```

示例:

```go
// GET http://example.com/user/bar
h.GET("/user/:name", func(c context.Context, ctx *app.RequestContext) {
    fpath := ctx.FullPath() // fpath == "/user/:name"
})

// 未匹配路由
h.NoRoute(func(c context.Context, ctx *app.RequestContext) {
    fpath := ctx.FullPath() // fpath == ""
})
```

### Path

获取请求的路径。出现参数路由时 Path 给出命名参数匹配后的路径，而 FullPath 给出原始路径。

```go
func (ctx *RequestContext) Path() []byte
```

示例:

```go
// GET http://example.com/user/bar
h.GET("/user/:name", func(c context.Context, ctx *app.RequestContext) {
    path := ctx.Path() // path == []byte("/user/bar")
})
```

### Param

获取路由参数的值。

```go
func (ctx *RequestContext) Param(key string) string
```

示例:

```go
// GET http://example.com/user/bar
h.GET("/user/:name", func(c context.Context, ctx *app.RequestContext) {
    name := ctx.Param("name") // name == "bar"
    id := ctx.Param("id")     // id == ""
})
```

### Query

获取路由 Query String 参数中指定属性的值，如果没有返回空字符串。

```go
func (ctx *RequestContext) Query(key string) string
```

示例:

```go
// GET http://example.com/user?name=bar
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    name := ctx.Query("name") // name == "bar"
    id := ctx.Query("id")     // id == ""
})
```

### DefaultQuery

获取路由 Query String 参数中指定属性的值，如果没有返回设置的默认值。

```go
func (ctx *RequestContext) DefaultQuery(key, defaultValue string) string
```

示例:

```go
// GET http://example.com/user?name=bar&&age=
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    name := ctx.DefaultQuery("name", "tom") // name == "bar"
    id := ctx.DefaultQuery("id", "123")     // id == "123"
    age := ctx.DefaultQuery("age", "45")    // age == ""（参数存在但为空）
})
```

### GetQuery

获取路由 Query String 参数中指定属性的值以及属性是否存在。

```go
func (ctx *RequestContext) GetQuery(key string) (string, bool)
```

示例:

```go
// GET http://example.com/user?name=bar&&age=
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    name, hasName := ctx.GetQuery("name") // name == "bar", hasName == true
    id, hasId := ctx.GetQuery("id")       // id == "", hasId == false
    age, hasAge := ctx.GetQuery("age")    // age == "", hasAge == true
})
```

### QueryArgs

获取路由 Query String 参数对象。

```go
func (ctx *RequestContext) QueryArgs() *protocol.Args
```

示例:

```go
// GET http://example.com/user?name=bar&age=&pets=dog&pets=cat
h.GET("/user", func(c context.Context, ctx *app.RequestContext) {
    args := ctx.QueryArgs()

    // 获取信息
    s := args.String()           // s == "name=bar&age=&pets=dog&pets=cat"
    name := args.Peek("name")    // name == []byte("bar")
    hasName := args.Has("name")  // hasName == true
    len := args.Len()            // len == 4

    // 遍历所有参数
    args.VisitAll(func(key, value []byte) {
        // 处理每个参数
    })

    // 获取多值参数
    pets := args.PeekAll("pets") // pets == [][]byte{[]byte("dog"), []byte("cat")}

    // 修改参数
    var newArgs protocol.Args
    args.CopyTo(&newArgs)
    newArgs.Set("version", "v1")
    newArgs.Del("age")
    newArgs.Add("name", "foo")
})
```

### URI

返回请求的 URI 对象。

```go
func (ctx *RequestContext) URI() *protocol.URI
```

## Header 操作

### Add

添加或设置键为 key 的 Header。

> 注意：Add 通常用于为同一个 Key 设置多个 Header，若要为同一个 Key 设置单个 Header 请使用 Set。

```go
func (h *RequestHeader) Add(key, value string)
```

示例:

```go
h.GET("/example", func(c context.Context, ctx *app.RequestContext) {
    ctx.Request.Header.Add("hertz1", "value1")
    ctx.Request.Header.Add("hertz1", "value2")
    hertz1 := ctx.Request.Header.GetAll("hertz1") // hertz1 == []string{"value1", "value2"}
})
```

### Set

设置 Header 键值（覆盖已有值）。

```go
func (h *RequestHeader) Set(key, value string)
```

示例:

```go
h.GET("/example", func(c context.Context, ctx *app.RequestContext) {
    ctx.Request.Header.Set("hertz1", "value1")
    ctx.Request.Header.Set("hertz1", "value2")
    hertz1 := ctx.Request.Header.GetAll("hertz1") // hertz1 == []string{"value2"}
})
```

### Header

获取完整的 Header（[]byte 类型）。

```go
func (h *RequestHeader) Header() []byte
```

### String

获取完整的 Header（string 类型）。

```go
func (h *RequestHeader) String() string
```

### VisitAll

遍历所有 Header 的键值并执行 f 函数。

```go
func (h *RequestHeader) VisitAll(f func(key, value []byte))
```

示例:

```go
h.GET("/example", func(c context.Context, ctx *app.RequestContext) {
    ctx.Request.Header.Add("Hertz1", "value1")
    ctx.Request.Header.Add("Hertz1", "value2")

    var hertzString []string
    ctx.Request.Header.VisitAll(func(key, value []byte) {
        if string(key) == "Hertz1" {
            hertzString = append(hertzString, string(value))
        }
    })
    // hertzString == []string{"value1", "value2"}
})
```

### Method

获取请求方法的类型。

```go
func (ctx *RequestContext) Method() []byte
```

示例:

```go
// POST http://example.com/user
h.Any("/user", func(c context.Context, ctx *app.RequestContext) {
    method := ctx.Method() // method == []byte("POST")
})
```

### ContentType

获取请求头 Content-Type 的值。

```go
func (ctx *RequestContext) ContentType() []byte
```

### IfModifiedSince

判断时间是否超过请求头 If-Modified-Since 的值。如果请求头不包含 If-Modified-Since 也返回 true。

```go
func (ctx *RequestContext) IfModifiedSince(lastModified time.Time) bool
```

### Cookie

获取请求头 Cookie 中 key 的值。

```go
func (ctx *RequestContext) Cookie(key string) []byte
```

示例:

```go
// Cookie: foo_cookie=choco; bar_cookie=strawberry
h.Post("/user", func(c context.Context, ctx *app.RequestContext) {
    fCookie := ctx.Cookie("foo_cookie")     // fCookie == []byte("choco")
    bCookie := ctx.Cookie("bar_cookie")     // bCookie == []byte("strawberry")
    noneCookie := ctx.Cookie("none_cookie") // noneCookie == nil
})
```

### UserAgent

获取请求头 User-Agent 的值。

```go
func (ctx *RequestContext) UserAgent() []byte
```

### GetHeader

获取请求头中 key 的值。

```go
func (ctx *RequestContext) GetHeader(key string) []byte
```

示例:

```go
// Say-Hello: hello
h.Post("/user", func(c context.Context, ctx *app.RequestContext) {
    customHeader := ctx.GetHeader("Say-Hello") // customHeader == []byte("hello")
})
```

## Body 操作

### Body

获取请求的 body 数据，如果发生错误返回 error。

```go
func (ctx *RequestContext) Body() ([]byte, error)
```

示例:

```go
// POST http://example.com/pet
// Content-Type: application/json
// {"pet":"cat"}
h.Post("/pet", func(c context.Context, ctx *app.RequestContext) {
    data, err := ctx.Body() // data == []byte("{\"pet\":\"cat\"}"), err == nil
})
```

### RequestBodyStream

获取请求的 BodyStream。

```go
func (ctx *RequestContext) RequestBodyStream() io.Reader
```

示例:

```go
h := server.Default(server.WithStreamBody(true))
h.Post("/user", func(c context.Context, ctx *app.RequestContext) {
    sr := ctx.RequestBodyStream()
    data, _ := io.ReadAll(sr) // data == []byte("abcdefg")
})
```

### MultipartForm

获取 multipart.Form 对象，可用于获取普通值和文件。

```go
func (ctx *RequestContext) MultipartForm() (*multipart.Form, error)
```

示例:

```go
// Content-Type: multipart/form-data;
// Content-Disposition: form-data; name="name"
// tom
h.POST("/user", func(c context.Context, ctx *app.RequestContext) {
    form, err := ctx.MultipartForm()
    name := form.Value["name"][0] // name == "tom"
})
```

### PostForm

按名称检索 multipart.Form.Value，返回给定 name 的第一个值。

> 支持从 application/x-www-form-urlencoded 和 multipart/form-data 获取值，不支持获取文件。

```go
func (ctx *RequestContext) PostForm(key string) string
```

### DefaultPostForm

按名称检索值，如果不存在返回 defaultValue。

```go
func (ctx *RequestContext) DefaultPostForm(key, defaultValue string) string
```

### PostArgs

获取 application/x-www-form-urlencoded 参数对象。

```go
func (ctx *RequestContext) PostArgs() *protocol.Args
```

示例:

```go
// Content-Type: application/x-www-form-urlencoded
// name=tom&pet=cat&pet=dog
h.POST("/user", func(c context.Context, ctx *app.RequestContext) {
    args := ctx.PostArgs()
    name := args.Peek("name") // name == "tom"

    var pets []string
    args.VisitAll(func(key, value []byte) {
        if string(key) == "pet" {
            pets = append(pets, string(value))
        }
    })
    // pets == []string{"cat", "dog"}
})
```

### FormValue

按照以下顺序获取 key 的值：
1. 从 QueryArgs 中获取值
2. 从 PostArgs 中获取值
3. 从 MultipartForm 中获取值

```go
func (ctx *RequestContext) FormValue(key string) []byte
```

## 文件操作

### FormFile

按名称检索上传的文件，返回给定 name 的第一个 multipart.FileHeader。

```go
func (ctx *RequestContext) FormFile(name string) (*multipart.FileHeader, error)
```

示例:

```go
// Content-Disposition: form-data; name="avatar"; filename="abc.jpg"
h.Post("/user", func(c context.Context, ctx *app.RequestContext) {
    avatarFile, err := ctx.FormFile("avatar") // avatarFile.Filename == "abc.jpg"
})
```

### SaveUploadedFile

保存 multipart 文件到磁盘。

```go
func (ctx *RequestContext) SaveUploadedFile(file *multipart.FileHeader, dst string) error
```

示例:

```go
h.Post("/user", func(c context.Context, ctx *app.RequestContext) {
    avatarFile, err := ctx.FormFile("avatar")
    if err != nil {
        ctx.JSON(400, map[string]string{"error": err.Error()})
        return
    }
    // 保存文件
    ctx.SaveUploadedFile(avatarFile, "./uploads/"+avatarFile.Filename)
})
```

## 元数据存储

> 注意：RequestContext 在请求结束后会被回收，元数据会被置为 nil。如需异步使用，请使用 Copy() 方法。

```go
h.POST("/user", func(c context.Context, ctx *app.RequestContext) {
    // 设置元数据
    ctx.Set("version", "v1")
    ctx.Set("user_id", 123)
    ctx.Set("is_admin", true)

    // 获取元数据
    v := ctx.Value("version")            // v == interface{}(string) "v1"
    v, exists := ctx.Get("version")      // v == "v1", exists == true
    vString := ctx.GetString("version")  // vString == "v1"
    vInt := ctx.GetInt("user_id")        // vInt == 123
    vBool := ctx.GetBool("is_admin")     // vBool == true

    // 遍历元数据
    ctx.ForEachKey(func(k string, v interface{}) {
        // 处理每个键值对
    })
})
```

## Handler 控制

### Next

执行下一个 handler，通常用于中间件。

```go
func (ctx *RequestContext) Next(c context.Context)
```

### Abort

终止后续的 handler 执行。

```go
func (ctx *RequestContext) Abort()
```

### IsAborted

获取后续的 handler 执行状态是否被终止。

```go
func (ctx *RequestContext) IsAborted() bool
```

示例:

```go
h.POST("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx.Abort()
    isAborted := ctx.IsAborted() // isAborted == true
}, func(c context.Context, ctx *app.RequestContext) {
    // 不会执行
})
```

## 获取 ClientIP

```go
func (ctx *RequestContext) ClientIP() string
```

示例:

```go
// X-Forwarded-For: 20.20.20.20, 30.30.30.30
// X-Real-IP: 10.10.10.10
h.Use(func(c context.Context, ctx *app.RequestContext) {
    ip := ctx.ClientIP() // 20.20.20.20
})
```

## 并发安全

### Copy

拷贝 RequestContext 副本，提供协程安全的访问方式。

```go
func (ctx *RequestContext) Copy() *RequestContext
```

示例:

```go
h.POST("/user", func(c context.Context, ctx *app.RequestContext) {
    ctx1 := ctx.Copy()
    go func(context *app.RequestContext) {
        // 安全使用副本
        name := context.Query("name")
    }(ctx1)
})
```
