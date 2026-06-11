# Handler 处理器

## Handler 函数签名

```go
func handler(c context.Context, ctx *app.RequestContext) {
    // 业务逻辑
}
```

## 返回 JSON

```go
ctx.JSON(200, map[string]interface{}{"message": "success"})
```

## 绑定参数

```go
var req Request
ctx.BindAndValidate(&req)
```

参考: [Hertz Server API示例](https://bytedance.larkoffice.com/wiki/wikcnWyHh0tIeUulzS2IQalFL9f)
