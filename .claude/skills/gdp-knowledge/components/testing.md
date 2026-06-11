# GDP 单测套件

## 概述

GDP 单测套件提供了完整的单元测试解决方案，可以在不依赖任何第三方组件的前提下，在单元测试中模拟线上请求。通过构建与线上完全一致的 `Context`，开发者可以编写高质量且易维护的单元测试代码。

**代码包**：code.byted.org/gdp/mocks

## 主要特性

- **Context 模拟**：构建与线上一致的请求上下文
- **零依赖**：不依赖任何第三方组件
- **API/RPC 支持**：同时支持 API 服务和 RPC 服务测试
- **自动 Mock 管理**：自动释放 RAL、config、mockey 组件的 mock 数据
- **框架集成**：与 GDP 框架深度集成
- **代码生成**：支持自动生成测试框架代码

## 快速上手

### GDP 项目结构

GDP 项目有固定的代码结构，业务代码集中于 `pkg`、`domain`、`dal`、`dao`：

```
service/domain/foo/
├── example_test.go          // mock 模板和工具函数
├── foo_bar.go               // 业务逻辑
└── foo_bar_test.go          // 业务逻辑单元测试
```

### 基础业务逻辑示例

一个简单的业务服务层 `domain` 的代码：

```go
// foo_bar.go
func FooBar(ctx context.Context, req *dto.FooRequest) (*dto.FooResponse, errcode) {
   var resp dto.FooResponse
   if req.Str == "" {
       return nil, errcode.ERR_PARAM_INVALID
   }

   resp.Str = req.Str
   return &resp, nil
}
```

### API 服务单测

```go
// foo_bar_test.go
func TestFooBar(t *testing.T) {
    mocks.Run("call foo bar success", t, func(t *testing.T) {
        as := assert.New(t)

        // 创建 HTTP 请求
        r := NewRequest()
        r.PostForm.Set("device_id", "123456")
        r.PostForm.Set("str", "x")

        // 创建 Context
        ctx := NewMockContext(r)
        req := dto.FooRequest{
            Str: af.GetParam("str"),
        }

        resp, err := FooBar(ctx, &req)
        as.Equal("x", resp.GetStr())
        as.Nil(err)
    })

    mocks.Run("call foo bar failed", t, func(t *testing.T) {
        as := assert.New(t)

        // 创建 HTTP 请求
        r := NewRequest()
        r.PostForm.Set("str", "")

        // 创建 Context
        ctx := NewMockContext(r)
        req := dto.FooRequest{
            Str: af.GetParam("str"),
        }

        resp, err := FooBar(ctx, &req)
        as.Nil(resp)
        as.Equal(errcode.ERR_PARAM_INVALID, err)
    })
}
```

### RPC 服务单测

```go
// foo_bar_test.go
func TestFooBar(t *testing.T) {
    mocks.Run("call foo bar success", t, func(t *testing.T) {
        as := assert.New(t)

        // 创建请求
        req := dto.FooRequest{
            Str: "x",
        }

        // 创建 Context
        ctx := NewMockContext(req)

        resp, err := FooBar(ctx, &req)
        as.Equal("x", resp.GetStr())
        as.Nil(errCode)
    })

    mocks.Run("call foo bar failed", t, func(t *testing.T) {
        as := assert.New(t)

        // 创建请求
        req := dto.FooRequest{
            Str: "",
        }

        // 创建 Context
        ctx := NewMockContext(req)

        resp, err := FooBar(ctx, &req)
        as.Nil(resp)
        as.Equal(errcode.ERR_PARAM_INVALID, err)
    })
}
```

## 高级功能

### 使用 mocks.Run 组织测试

`mocks.Run` 提供了便利的能力：

```go
func TestBusinessLogic(t *testing.T) {
    mocks.Run("test case name", t, func(ctx context.Context) {
        as := assert.New(t)

        // mock 资源，测试结束后自动释放
        // RAL 资源
        redis.Mock().Get().WithResponse("ok").Build()
        abase.Mock().MGet().WithAbaseNil().Build()
        db.Mock().WithModel(&Data{}).Build()

        // GDP 配置 mock
        config.Mock().WithKey("abc").WithValue("bcd").Build()

        // mockey 打桩
        mocks.Mock(some_func).Return(nil).Build()

        // 执行业务逻辑测试
        result, err := BusinessLogic(ctx, req)
        as.NotNil(result)
        as.Nil(err)
    })
}
```

### 批量 Mock 资源

```go
func TestWithBatchMocks(t *testing.T) {
    as := assert.New(t)

    // 批量 mock 资源
    defer redis.Mock().Get().WithResponse("ok").Build()
    defer mocks.MockBatch(
        abase.Mock().MGet().WithAbaseNil().Build(),
        db.Mock().WithModel(&Data{}).Build(),
        mocks.Mock(some_func).Return(nil).Build(),
    ).Unpatch()

    // 测试逻辑
    result, err := BusinessLogic(ctx, req)
    as.NotNil(result)
    as.Nil(err)
}
```

### 测试 HTTP 响应头

```go
func TestHTTPHeaders(t *testing.T) {
    as := assert.New(t)

    // 业务逻辑设置响应头
    func SetResponse(ctx context.Context) {
        af.SetHeader(ctx, "Access-Control-Allow-Methods", "POST")
        af.SetHeader(ctx, "X-Custom-Header", "value")
    }

    // 测试验证
    req := mocks.NewRawRequest(rawReq)
    ctx := mocks.NewMockContext(req)

    SetResponse(ctx)

    resp := mocks.GetMockResponse(ctx)
    as.Equal("POST", resp.Header.Get("Access-Control-Allow-Methods"))
    as.Equal("value", resp.Header.Get("X-Custom-Header"))
}
```

### 使用 af.Bind 绑定参数

```go
func TestWithBind(t *testing.T) {
    as := assert.New(t)

    // 创建请求
    request := NewRequest()
    request.PostForm.Set("aid", "1180")
    request.PostForm.Set("iid", "0")

    ctx := mocks.NewMockContext(request)

    var req dto.FooRequest

    // 直接设置参数
    req.ParamX = "X"

    // 使用 af.Bind 绑定（需要设置 Content-Type）
    _ = af.Bind(ctx, &req)

    // 验证绑定结果
    as.Equal("1180", req.Aid)
    as.Equal("0", req.Iid)
}
```

## 常见问题

### gdp/mocks 能在非单测代码中使用吗？

**不能**。`import code.byted.org/gdp/mocks` 只能出现在 `_test.go` 文件中，否则会导致服务无法启动。

### 如何编写可复用的测试工具函数？

1. **包内使用**：直接写在 package 下的任意 `_test.go` 文件中
2. **全局使用**：使用 build tag

```go
//go:build unittest
// +build unittest

package unittest

import (
    "context"
    "code.byted.org/gdp/mocks"
)

func CreateTestContext() context.Context {
    return mocks.NewMockContext(NewRequest())
}
```

### 什么时候需要使用 gdp/mocks 创建 Context？

只要有透传 `Context` 的场景，都需要通过 `gdp/mocks` 创建对应的 `Context`：

- **业务服务层 (domain)**：所有需要透传 `Context` 的单测场景
- **使用 GDP 组件**：如使用了 `gdp/config` 的单测场景
- **RAL 资源访问**：需要模拟远程资源调用的场景

### 可以不再使用 mockey/mockito 吗？

可以，`gdp/mocks` 封装了常用的 mock 方法：

| **原库** | **gdp/mocks 替代** |
| --- | --- |
| `mockey.Mock` | `mocks.Mock` |
| `mockey.PatchConvey` | `mocks.Run` |
| `mockey.GetMethod` | `mocks.GetMethod` |

### example_test.go 文件的作用？

代码生成时自动创建，包含：

- **API 服务**：`NewRequest()` 和 `NewMockContext()` 函数
- **RPC 服务**：`NewMockContext()` 函数

**建议保留**，这些是测试的基础工具函数。

## 相关文档
- [RAL概述](../ral/overview.md) - RAL组件总体介绍
- [RPC资源](../ral/rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](../ral/abase_redis.md) - 缓存资源配置和使用
- [Database资源](../ral/database.md) - 数据库资源配置和使用
- [Eventbus资源](../ral/eventbus.md) - 消息队列资源配置和使用