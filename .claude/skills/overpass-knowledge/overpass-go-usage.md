# Overpass Go 代码使用指南

## 概述

本文详细介绍 Overpass 在 Go 语言中的各种使用方式,包括默认封装、自定义 Client、Kitex Option 配置、错误处理等。

---

## 仓库目录结构

Overpass 为每个 PSM 生成的仓库包含以下目录:

```
overpass/P_S_M/
├── kitex_gen/              # Kitex 自动生成的代码
│   └── service_name/       # IDL 对应的 Go 代码
│       ├── service.go      # Service 定义
│       └── ...
├── rpc/                    # RPC 调用封装
│   └── p_s_m/              # 下划线形式的包名
│       ├── client.go       # Client 创建和管理
│       ├── default.go      # 默认封装方法
│       └── ...
├── option/                 # Kitex Option 配置
│   └── option.go           # Option 封装
├── mock/                   # Mock 实现
│   └── mock.go             # RPC Mock
└── go.mod                  # Go 模块定义
```

**目录说明**:
- `kitex_gen/` - 不要手动修改,由 Kitex 自动生成
- `rpc/` - 主要使用的包,包含所有 RPC 调用方法
- `option/` - 提供 Kitex Option 的封装
- `mock/` - 提供 Mock 能力

---

## 调用方式

### 方式 1: 默认封装 (推荐)

**适用场景**: 简单的 RPC 调用,不需要自定义配置

**格式**:
```go
resp, err := P_S_M.Method(ctx, params)
```

**示例**:
```go
import "code.byted.org/overpass/tiktok_user_service/rpc/tiktok_user_service"

// 调用 GetUserInfo
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)

// 调用 BatchGetUserInfo
resp, err := tiktok_user_service.BatchGetUserInfo(ctx, []int64{123, 456})
```

**特点**:
- ✅ 最简洁的调用方式
- ✅ 自动创建 Client (指定 PSM)
- ✅ 自动处理连接池
- ✅ Request 参数简化 (只接受非 optional 字段)
- ❌ 无法自定义 Kitex Option

### 方式 2: 使用 Request 结构体

**适用场景**: 需要传递 optional 字段或复杂参数

**示例**:
```go
import (
    "code.byted.org/overpass/tiktok_user_service/rpc/tiktok_user_service"
    "code.byted.org/tiktok/rpcmodels/user_service"
)

// 使用完整的 Request 结构体
req := &user_service.GetUserInfoRequest{
    UserID: 12345,
    Fields: []string{"nickname", "avatar"},  // optional 字段
}

resp, err := tiktok_user_service.GetUserInfoWithRequest(ctx, req)
```

### 方式 3: 创建自定义 Client

**适用场景**: 需要配置 Kitex Option、创建多个 Client、长连接等

**示例**:
```go
import (
    "code.byted.org/overpass/tiktok_user_service/rpc/tiktok_user_service"
    "github.com/cloudwego/kitex/client"
)

// 创建自定义 Client
cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",  // 下游 PSM
    client.WithTimeout(time.Second * 3),
    client.WithRetryPolicy(retryPolicy),
)
if err != nil {
    return err
}

// 使用 Client 调用
resp, err := cli.GetUserInfo(ctx, userID)
```

**进阶用法**:
```go
// 创建多个 Client 实例
clientA, _ := tiktok_user_service.NewClient("psm.a")
clientB, _ := tiktok_user_service.NewClient("psm.b")

// 使用不同 Client
respA, _ := clientA.GetUserInfo(ctx, userID)
respB, _ := clientB.GetUserInfo(ctx, userID)
```

---

## Kitex Option 配置

### 常用 Option

#### 1. 设置超时时间

```go
import (
    "time"
    "github.com/cloudwego/kitex/client"
)

cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithRPCTimeout(3 * time.Second),      // RPC 超时
    client.WithConnectTimeout(1 * time.Second),  // 连接超时
)
```

#### 2. 配置重试策略

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/retry"
)

// 失败重试策略
retryPolicy := retry.NewFailurePolicy()
retryPolicy.WithMaxRetryTimes(2)
retryPolicy.WithRetryDelay(100 * time.Millisecond)

cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithFailureRetry(retryPolicy),
)
```

#### 3. 配置连接池

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/connpool"
)

cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithLongConnection(
        connpool.IdleConfig{
            MaxIdlePerAddress: 10,
            MaxIdleGlobal:     100,
            MaxIdleTimeout:    time.Minute,
        },
    ),
)
```

#### 4. 配置中间件

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/endpoint"
)

// 自定义中间件
func logMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        start := time.Now()
        err := next(ctx, req, resp)
        duration := time.Since(start)

        log.Infof("RPC call took %v, err: %v", duration, err)
        return err
    }
}

cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithMiddleware(logMiddleware),
)
```

#### 5. 配置服务发现

```go
import (
    "github.com/cloudwego/kitex/client"
    "github.com/cloudwego/kitex/pkg/discovery"
)

// 使用自定义 Resolver
resolver := myCustomResolver{}

cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithResolver(resolver),
)
```

---

## 指定下游 PSM

### 场景说明

在某些情况下,一个 IDL 可能对应多个部署实例 (不同 PSM)。Overpass 允许你指定具体调用哪个 PSM。

### 使用方式

```go
// 默认情况 - 使用 IDL 对应的 PSM
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)

// 指定下游 PSM
cli, err := tiktok_user_service.NewClient("tiktok.user.service.test")  // 测试环境
resp, err := cli.GetUserInfo(ctx, userID)

cli2, err := tiktok_user_service.NewClient("tiktok.user.service.canary")  // 灰度环境
resp2, err := cli2.GetUserInfo(ctx, userID)
```

### 多环境调用

```go
type Environment string

const (
    EnvProd   Environment = "tiktok.user.service"
    EnvTest   Environment = "tiktok.user.service.test"
    EnvCanary Environment = "tiktok.user.service.canary"
)

func getClient(env Environment) (Client, error) {
    return tiktok_user_service.NewClient(string(env))
}

// 使用
prodClient, _ := getClient(EnvProd)
testClient, _ := getClient(EnvTest)
```

---

## 错误处理

### 错误封装结构

Overpass 对所有 RPC 调用（`client.Method`）进行了封装，在 `lib/overpass_auto_generated_client.go` 中统一返回一个封装后的 error，其结构如下：

```go
type RPCError struct {
    PSM              string
    Method           string
    ErrType          RPCErrorType
    OriginalErr      error
    BizStatusCode    int32
    BizStatusMessage string
}
```

### 错误类型

Overpass 返回的 error 共有三种类型：

| 错误类型 | 含义 | 触发条件 |
|---------|------|---------|
| `RPC_FAILED` | RPC 调用失败 | Kitex 返回 `err != nil`，包括 Thrift/Kitex/Mesh 报错、业务 Handler 返回 error（被认为是 Kite 的 [119 RemoteOrNetErrCode] 错误） |
| `RPC_RESP_IS_NIL` | 响应为空 | Kitex 返回的 `resp == nil` |
| `RPC_STATUS_CODE_NOT_ZERO` | 业务状态码非零 | 下游返回的 resp 中包含 `BaseResp`，且 `resp.BaseResp.StatusCode != 0` |

因此，不仅 Kitex 调下游错误时直接返回 err，resp 为 nil 或 StatusCode 不为 0 也会返回一个 err。**在绝大多数情况下，只要 err 是 nil，就可以认为 resp 是没有问题的。**

### 基础用法

```go
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
if err != nil {
    log.Errorf("RPC call failed: %v", err)
    return err
}
```

### 类型断言与错误分类处理

如果需要对错误进行进一步处理（例如取出下游返回的 StatusCode），可以对 Overpass 返回的错误做类型断言，使用 `RPCError` 的方法获取详细信息：

```go
import "code.byted.org/overpass/common/rpc_error"

resp, err := client.Method(ctx, req, callOptions...)
if err != nil {
    rpcErr := err.(*rpc_error.RPCError)
    if rpcErr.Is(rpc_error.RPC_STATUS_CODE_NOT_ZERO) {
        // 下游业务错误，获取业务状态码和消息
        statusCode := rpcErr.GetBizStatusCode()
        statusMsg := rpcErr.GetBizStatusMessage()
        // your code
    } else if rpcErr.Is(rpc_error.RPC_FAILED) {
        // RPC 调用失败（网络、超时等），获取原始错误
        originalErr := rpcErr.GetOriginalErr()
        // your code
    } else {
        // RPC_RESP_IS_NIL
        // your code
    }
}
```

**RPCError 常用方法**：

| 方法 | 说明 |
|------|------|
| `rpcErr.Is(rpc_error.XXX)` | 判断错误类型 |
| `rpcErr.GetBizStatusCode()` | 获取业务状态码 |
| `rpcErr.GetBizStatusMessage()` | 获取业务状态消息 |
| `rpcErr.GetOriginalErr()` | 获取 Kitex 原始错误 |

### 便捷工具函数

`code.byted.org/overpass/common/rpc_error` 包中提供了便捷的错误判断函数。

#### IsBizErrorWithStatusCodes

判断错误是否为业务错误（`BaseResp.StatusCode != 0`），且状态码在指定的错误码列表中：

```go
resp, err := client.Method(ctx, req)
if err != nil {
    if rpc_error.IsBizErrorWithStatusCodes(err, 1001, 1002) {
        // 业务错误码为 1001 或 1002，进行特殊处理
    }
}
```

#### BaseResp 接口

`rpc_error` 包还提供了 `BaseResp` 接口，下游返回的响应如果包含 `BaseResp`，可以直接通过该接口获取状态信息：

```go
type BaseResp interface {
    GetStatusCode() int32
    GetStatusMessage() string
    GetExtra() map[string]string
}
```

### Kitex 原生错误判断

也可以结合 Kitex 原生的错误判断方式：

```go
import (
    "github.com/cloudwego/kitex/pkg/kerrors"
    "github.com/cloudwego/kitex/pkg/remote"
)

resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
if err != nil {
    if kerrors.IsTimeoutError(err) {
        log.Warn("RPC timeout")
        return ErrTimeout
    }
    if remote.IsNetworkError(err) {
        log.Warn("Network error")
        return ErrNetwork
    }
    log.Errorf("Business error: %v", err)
    return err
}
```

### 自定义重试封装

```go
func callWithRetry(ctx context.Context, userID int64, maxRetries int) (*Response, error) {
    var resp *Response
    var err error

    for i := 0; i < maxRetries; i++ {
        resp, err = tiktok_user_service.GetUserInfo(ctx, userID)
        if err == nil {
            return resp, nil
        }

        if kerrors.IsTimeoutError(err) || remote.IsNetworkError(err) {
            log.Warnf("Retry %d/%d: %v", i+1, maxRetries, err)
            time.Sleep(time.Millisecond * 100 * time.Duration(i+1))
            continue
        }

        return nil, err
    }

    return nil, fmt.Errorf("max retries exceeded: %w", err)
}
```

---

## 日志打印

### 使用 Kitex 日志

Overpass 集成了 Kitex 的日志系统。

```go
import "github.com/cloudwego/kitex/pkg/klog"

// 基础日志
klog.Info("Starting RPC call")
klog.Infof("UserID: %d", userID)

// 错误日志
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
if err != nil {
    klog.Errorf("GetUserInfo failed: %v", err)
    return err
}

klog.Infof("GetUserInfo success: %+v", resp)
```

### 结构化日志

```go
import (
    "github.com/cloudwego/kitex/pkg/klog"
    "github.com/bytedance/gopkg/util/logger"
)

// 使用 logger
logger.WithContext(ctx).
    WithField("user_id", userID).
    WithField("method", "GetUserInfo").
    Info("RPC call started")

resp, err := tiktok_user_service.GetUserInfo(ctx, userID)

logger.WithContext(ctx).
    WithField("user_id", userID).
    WithField("duration_ms", duration).
    WithField("error", err).
    Info("RPC call completed")
```

### 日志中间件

```go
func loggingMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        start := time.Now()

        klog.Infof("RPC request: %+v", req)

        err := next(ctx, req, resp)

        duration := time.Since(start)
        if err != nil {
            klog.Errorf("RPC failed: duration=%v, err=%v", duration, err)
        } else {
            klog.Infof("RPC success: duration=%v, resp=%+v", duration, resp)
        }

        return err
    }
}

cli, _ := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithMiddleware(loggingMiddleware),
)
```

---

## 自定义扩展

### Overpass 额外功能设置

Overpass 提供了一些额外的配置选项来扩展功能。

```go
import "code.byted.org/overpass/tiktok_user_service/option"

// 使用 Overpass Option
cli, err := tiktok_user_service.NewClient(
    "tiktok.user.service",
    option.WithCustomOption(...),  // Overpass 自定义选项
)
```

### 自定义 Wrapper

可以在 Overpass 生成的代码基础上添加自己的封装层。

```go
package userclient

import (
    "context"
    "code.byted.org/overpass/tiktok_user_service/rpc/tiktok_user_service"
)

// 自定义 Client 封装
type UserClient struct {
    client tiktok_user_service.Client
}

func NewUserClient() (*UserClient, error) {
    cli, err := tiktok_user_service.NewClient(
        "tiktok.user.service",
        // ... 自定义配置
    )
    if err != nil {
        return nil, err
    }

    return &UserClient{client: cli}, nil
}

// 添加业务逻辑封装
func (c *UserClient) GetUser(ctx context.Context, userID int64) (*User, error) {
    // 参数校验
    if userID <= 0 {
        return nil, ErrInvalidUserID
    }

    // 调用 RPC
    resp, err := c.client.GetUserInfo(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("GetUserInfo failed: %w", err)
    }

    // 业务逻辑处理
    user := convertToUser(resp)

    return user, nil
}
```

---

## Thrift Streaming 支持

Overpass 支持 Thrift Streaming (双向流、客户端流、服务端流)。

### 服务端流示例

```go
import (
    "io"
    "code.byted.org/overpass/tiktok_stream_service/rpc/tiktok_stream_service"
)

// 调用服务端流方法
stream, err := tiktok_stream_service.StreamMessages(ctx, &Request{})
if err != nil {
    return err
}

// 接收流数据
for {
    msg, err := stream.Recv()
    if err == io.EOF {
        break  // 流结束
    }
    if err != nil {
        return err
    }

    // 处理消息
    handleMessage(msg)
}
```

### 客户端流示例

```go
// 创建客户端流
stream, err := tiktok_stream_service.UploadData(ctx)
if err != nil {
    return err
}

// 发送数据
for _, data := range dataList {
    if err := stream.Send(data); err != nil {
        return err
    }
}

// 关闭流并获取响应
resp, err := stream.CloseAndRecv()
```

---

## 最佳实践

### 1. Client 复用

**推荐**: 创建单例 Client,避免频繁创建

```go
var (
    userClient     tiktok_user_service.Client
    userClientOnce sync.Once
)

func GetUserClient() (tiktok_user_service.Client, error) {
    var err error
    userClientOnce.Do(func() {
        userClient, err = tiktok_user_service.NewClient(
            "tiktok.user.service",
            client.WithRPCTimeout(3 * time.Second),
        )
    })
    return userClient, err
}
```

### 2. 统一错误处理

```go
func wrapRPCError(err error, operation string) error {
    if err == nil {
        return nil
    }

    if kerrors.IsTimeoutError(err) {
        return fmt.Errorf("%s timeout: %w", operation, err)
    }

    return fmt.Errorf("%s failed: %w", operation, err)
}

// 使用
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
if err != nil {
    return wrapRPCError(err, "GetUserInfo")
}
```

### 3. Context 传递

```go
import (
    "github.com/cloudwego/kitex/pkg/rpcinfo"
    "github.com/cloudwego/kitex/pkg/transmeta"
)

// 传递 trace ID
ctx = rpcinfo.NewCtxWithCallInfo(ctx, rpcinfo.FromHTTPRequest(req))

// 传递自定义元数据
ctx = transmeta.WithPersistentValue(ctx, "user_id", "12345")

resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
```

### 4. 监控和指标

```go
import (
    "github.com/cloudwego/kitex/pkg/stats"
    "github.com/prometheus/client_golang/prometheus"
)

// 自定义 Tracer
type metricsTracer struct{}

func (m *metricsTracer) Start(ctx context.Context) context.Context {
    return ctx
}

func (m *metricsTracer) Finish(ctx context.Context) {
    // 记录指标
    rpcDuration.Observe(duration.Seconds())
    rpcCounter.Inc()
}

cli, _ := tiktok_user_service.NewClient(
    "tiktok.user.service",
    client.WithTracer(&metricsTracer{}),
)
```

---

## 相关文档

- [Overpass 平台简介](./overpass-introduction.md)
- [Overpass 快速开始](./overpass-quickstart.md)
- [Overpass 平台操作](./overpass-platform-operations.md)
- [客户端配置](./overpass-client-configuration.md)
