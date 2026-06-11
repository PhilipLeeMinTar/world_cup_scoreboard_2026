# Hertz 最佳实践

## 版本选择

✅ **使用 Hertz v1.x 版本以获得更好的性能和安全性**

Hertz 1.0 引入了全新的双上下文模型,修复了 0.x 的多个已知问题。

## Context 使用

✅ **RequestContext 不能并发使用,需要通过 ctx.Copy() 创建副本**

```go
// ❌ 错误
go func() {
    name := ctx.Query("name")  // 不安全
}()

// ✅ 正确
name := ctx.Query("name")
go func() {
    process(c, name)
}()
```

## 代码生成

✅ **优先使用 Hertztool v3 进行代码生成**

Hertztool v3 解决了 v2 的历史问题,推荐使用。

```bash
go install code.byted.org/middleware/hertztool/v3@latest
```

## 资源管理

✅ **合理配置连接池和超时参数以避免内存泄漏**

```go
// Server 端
h := byted.Default(
    server.WithIdleTimeout(60*time.Second),
    server.WithReadTimeout(3*time.Second),
)

// Client 端
c, _ := client.NewClient(
    client.WithMaxConns(100),
    client.WithMaxIdleConnDuration(90*time.Second),
)
```

## 错误处理

✅ **使用中间件进行统一的错误处理和日志记录**

```go
func ErrorHandlerMiddleware(c context.Context, ctx *app.RequestContext) {
    ctx.Next()
    if len(ctx.Errors) > 0 {
        err := ctx.Errors.Last()
        ctx.JSON(500, map[string]string{"error": err.Error()})
    }
}
```

## 安全性

✅ **在生产环境启用 TLS 和 HTTP/2 以提升安全性和性能**

```go
h := byted.Default(
    server.WithTLS(&tls.Config{MinVersion: tls.VersionTLS12}),
    server.WithALPN(true),
)
```

## 日志管理

✅ **定期清理日志文件避免磁盘空间不足**

配置日志轮转策略,定期归档或删除旧日志。

## 参数验证

✅ **使用 Binding 框架进行参数验证,避免手动解析**

```go
var req Request
if err := ctx.BindAndValidate(&req); err != nil {
    ctx.JSON(400, map[string]string{"error": err.Error()})
    return
}
```

## Session 管理

✅ **合理使用 Localsession 避免在不同请求间共享数据**

Hertz 1.0 正确隔离了 Localsession,每个请求独立。

## 版本追踪

✅ **关注 Release Notes 及时了解版本更新和不兼容变更**

定期查看 [Hertz 1.0 Release Notes](https://bytedance.larkoffice.com/wiki/wikcnha0l5W96pYXowvu95Dgr3e)

## 性能优化

### 1. 连接池优化

```go
// Client 端
c, _ := client.NewClient(
    client.WithMaxConns(100),
    client.WithMaxIdleConnDuration(90*time.Second),
    client.WithDialTimeout(5*time.Second),
)
```

### 2. 避免不必要的 Copy

```go
// ❌ 不推荐
ctxCopy := ctx.Copy()
name := ctxCopy.Query("name")

// ✅ 推荐
name := ctx.Query("name")
```

### 3. 使用 Buffer Pool

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}
```

### 4. 启用压缩

```go
import "github.com/hertz-contrib/gzip"
h.Use(gzip.Gzip(gzip.BestSpeed))
```

## 测试实践

### 使用 Hertztest

```go
func TestHandler(t *testing.T) {
    c := mock.NewContext()
    Handler(context.Background(), c)
    assert.Equal(t, 200, c.Response.StatusCode())
}
```

## 迁移指南

### Hertz 0.x → 1.0

**主要变更:**
1. Handler 参数顺序: `(ctx, c)` → `(c, ctx)`
2. Context 分离: 标准 context.Context 和 RequestContext
3. 并发安全: RequestContext 不再协程安全

**迁移步骤:**
1. 调整所有 handler 函数签名
2. 修复并发使用 RequestContext 的代码
3. 运行测试验证

参考 [Hertz 1.0 Release Notes](https://bytedance.larkoffice.com/wiki/wikcnha0l5W96pYXowvu95Dgr3e) 获取完整迁移指南。
