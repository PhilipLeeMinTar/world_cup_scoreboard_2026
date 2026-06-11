# 请求上下文 RequestContext

请求上下文 `RequestContext` 是用于保存 HTTP 请求和设置 HTTP 响应的上下文，它提供了许多方便的 API 接口帮助用户开发。

Hertz 在 `HandlerFunc` 设计上，同时提供了一个标准 `context.Context` 和一个 `RequestContext` 作为函数的入参：

```go
type HandlerFunc func(c context.Context, ctx *RequestContext)
```

## 上下文传递与并发安全

### 元数据存储

`context.Context` 与 `RequestContext` 都有存储值的能力，具体选择使用哪一个上下文有个简单依据：所储存值的生命周期和所选择的上下文要匹配。

| 上下文 | 生命周期 | 查询效率 | 协程安全 | 实现接口 |
|--------|----------|----------|----------|----------|
| `RequestContext` | 请求级别 | 高（底层是 map） | 否 | 无 |
| `context.Context` | 可跨请求 | 较低 | 是 | context.Context |

- **RequestContext** 主要用来存储请求级别的变量，请求结束就回收了，特点是查询效率高（底层是 `map`），协程不安全，且未实现 `context.Context` 接口。
- **context.Context** 作为上下文在中间件/handler 之间传递，协程安全。所有需要 `context.Context` 接口作为入参的地方，直接传递 `c` 即可。

### 协程安全

如果存在异步传递 `ctx` 或并发使用 `ctx` 的场景，hertz 提供了 `ctx.Copy()` 接口，方便业务能够获取到一个协程安全的副本。

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 创建副本用于异步场景
    ctxCopy := ctx.Copy()

    go func() {
        // 在 goroutine 中安全使用副本
        name := ctxCopy.Query("name")
        processAsync(c, name)
    }()

    ctx.JSON(200, map[string]string{"status": "processing"})
}
```

## 使用指南

### Request 相关操作

详细的请求处理 API 请参考 [Request API 详解](./request-api.md)，包括：

- **URI 操作**：Host、Path、Query、Param 等
- **Header 操作**：获取/设置请求头
- **Body 操作**：获取请求体、表单数据
- **文件操作**：文件上传处理

### Response 相关操作

详细的响应处理 API 请参考 [Response API 详解](./response-api.md)，包括：

- **Header 操作**：设置响应头、Cookie
- **渲染操作**：JSON、HTML、Protobuf 等
- **Body 操作**：设置响应体、流式响应
- **文件操作**：文件下载

## 快速示例

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 获取请求参数
    id := ctx.Param("id")           // 路径参数
    name := ctx.Query("name")       // Query 参数
    token := ctx.GetHeader("Authorization")  // 请求头

    // 绑定请求体
    var req CreateUserRequest
    if err := ctx.BindAndValidate(&req); err != nil {
        ctx.JSON(400, map[string]string{"error": err.Error()})
        return
    }

    // 设置响应
    ctx.Header("X-Request-ID", "xxx")
    ctx.JSON(200, map[string]interface{}{
        "id":   id,
        "name": name,
        "data": req,
    })
}
```
