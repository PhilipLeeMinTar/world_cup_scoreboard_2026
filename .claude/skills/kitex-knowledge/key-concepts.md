# Kitex 核心概念速查

本文档提供 Kitex 框架中关键术语和概念的快速参考。

## 框架核心

### Kitex
ByteDance 开源的下一代 Golang 微服务 RPC 框架，具备高性能、强可扩展性的特点，支持 Thrift、Protobuf、gRPC 等协议。

**核心特性**:
- 基于 Netpoll 的高性能网络库
- 丰富的服务治理功能（负载均衡、熔断、限流等）
- 代码生成工具 KiteX Tool
- 可扩展的中间件系统
- 支持 Thrift/Protobuf/gRPC 多协议

### Netpoll
CloudWeGo 开源的高性能网络库，基于 epoll 实现的事件驱动 I/O 模型。

**核心优势**:
- **零拷贝**: 使用 LinkBuffer 减少内存复制
- **事件驱动**: 基于 Epoll 的高效 I/O 多路复用
- **协程友好**: 与 Go 协程模型完美结合
- **连接池管理**: 内置高效的连接池实现

**与标准库对比**:
- 比 net 库性能提升 20-40%
- 降低内存占用
- 更好的大规模并发表现

### kitex_gen
KiteX Tool 根据 IDL 文件自动生成的代码目录，包含客户端、服务端骨架代码以及请求/响应结构体定义。

**目录结构**:
```
kitex_gen/
├── service_name/           # 服务包
│   ├── service_name.go    # 数据结构定义
│   ├── k-service.go       # Kitex 扩展方法
│   ├── client.go          # Client 实现
│   └── server.go          # Server 实现
```

**注意事项**:
- 不要手动修改生成的代码
- IDL 变更后需要重新生成
- 建议加入版本控制

## 中间件系统

### Middleware
拦截器函数，在 RPC 调用前后执行自定义逻辑（如日志、监控、鉴权等）。

**类型签名**:
```go
type Middleware func(endpoint.Endpoint) endpoint.Endpoint
```

**执行模型**:
```
┌─────────────┐
│ Middleware1 │ (前置)
├─────────────┤
│ Middleware2 │ (前置)
├─────────────┤
│   Handler   │
├─────────────┤
│ Middleware2 │ (后置)
├─────────────┤
│ Middleware1 │ (后置)
└─────────────┘
```

**常见用途**:
- 日志记录
- 性能监控
- 请求鉴权
- 错误处理
- 流量控制

### Endpoint
RPC 调用的抽象表示，是中间件的核心接口。

**定义**:
```go
type Endpoint func(ctx context.Context, req, resp interface{}) error
```

**职责**:
- 封装 RPC 调用逻辑
- 作为中间件的包装目标
- 传递请求和响应对象

### RPCInfo
存储 RPC 调用元数据的信息容器，包含调用方、被调用方、方法名等信息。

**获取方式**:
```go
ri := rpcinfo.GetRPCInfo(ctx)
```

**常用信息**:
```go
// 调用方信息
from := ri.From()
fromService := from.ServiceName()
fromAddress := from.Address()

// 被调用方信息
to := ri.To()
toService := to.ServiceName()
method := to.Method()

// 调用配置
config := ri.Config()
timeout := config.RPCTimeout()
```

### KitexArgs / KitexResult
Client 中间件中的请求/响应包装结构。

**KitexArgs**: 包装请求参数
```go
type Args struct {
    Request *YourRequest
}
```

**KitexResult**: 包装响应结果
```go
type Result struct {
    Success *YourResponse
}
```

**在中间件中使用**:
```go
func ClientMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        // 获取请求
        args := req.(*echo.EchoArgs)
        log.Printf("request: %+v", args.Req)
        
        err := next(ctx, req, resp)
        
        // 获取响应
        result := resp.(*echo.EchoResult)
        log.Printf("response: %+v", result.Success)
        
        return err
    }
}
```

## 网络与连接

### 连接多路复用 (Connection Multiplexing)
在单个 TCP 连接上同时处理多个并发请求，复用同一连接减少连接开销。

**工作原理**:
```
Client                Server
  │                     │
  ├──req1─────────────→ │
  ├──req2─────────────→ │  (同一TCP连接)
  ├──req3─────────────→ │
  │                     │
  │ ←─────────────resp1┤
  │ ←─────────────resp2┤
  │ ←─────────────resp3┤
```

**配置方式**:
```go
// Server
server.WithMuxTransport()

// Client
client.WithMuxTransport()
```

**适用场景**:
- ✅ 高并发低流量场景
- ✅ 连接数受限环境
- ✅ 需要减少 TIME_WAIT 连接
- ❌ 大包传输场景（会增加延迟）

### 长连接池 (Connection Pool)
维护一组可复用的 TCP 连接，避免频繁建立/销毁连接的开销。

**核心参数**:
```go
connpool.IdleConfig{
    MaxIdlePerAddress: 10,   // 单地址最大空闲连接
    MaxIdleGlobal:     1000, // 全局最大空闲连接
    MaxIdleTimeout:    60s,  // 空闲超时时间
    MinIdlePerAddress: 2,    // 最小保持连接数
}
```

**连接生命周期**:
```
创建 → 使用 → 归还 → 空闲 → 超时/关闭
```

## 服务治理

### 泛化调用 (Generic Call)
不依赖生成代码，通过动态解析 IDL 或 JSON 直接调用服务。

**类型**:
- **HTTP 泛化**: 通过 HTTP 请求调用 Thrift 服务
- **JSON 泛化**: 使用 JSON 字符串调用服务
- **Map 泛化**: 使用 Map 结构调用服务

**使用场景**:
- API 网关
- 服务测试工具
- 跨语言调用
- 动态服务调用

**示例**:
```go
// JSON 泛化调用
p, _ := generic.NewThriftFileProvider("echo.thrift")
g, _ := generic.JSONThriftGeneric(p)
cli, _ := genericclient.NewClient("echo", g)

resp, err := cli.GenericCall(ctx, "Echo", `{"message":"hello"}`)
```

### Fallback
当 RPC 调用失败时，执行降级逻辑返回默认值或备用方案。

**实现方式**:
```go
func FallbackMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        err := next(ctx, req, resp)
        
        if err != nil {
            // 降级逻辑
            if echoResp, ok := resp.(*echo.EchoResponse); ok {
                echoResp.Message = "fallback response"
            }
            return nil // 吞掉错误
        }
        
        return err
    }
}
```

**常见降级策略**:
- 返回缓存数据
- 返回默认值
- 调用备用服务
- 返回空结果

### Warming Up (服务预热)
服务启动时预先执行一些初始化操作，提升首次请求的性能。

**实现方式**:
```go
import "github.com/cloudwego/kitex/pkg/warmup"

// 预热 handler
warmup.WarmupHandlers(handlers...)

// 自定义预热
func init() {
    // 预加载配置
    loadConfig()
    
    // 预热连接池
    warmupConnectionPool()
    
    // 预编译正则表达式
    compilePatterns()
}
```

**预热内容**:
- JIT 编译优化
- 连接池预建立
- 缓存预加载
- 配置预解析

### Backup Request
当首次请求超过一定时间未返回时，自动发起第二次请求，取最先返回的结果。

**工作原理**:
```
时间线:
t0 ────→ t1 ────→ t2 ────→ t3
│        │        │
req1     req2     resp2 返回 ✓
│                 │
└─────────────────resp1 被丢弃
```

**配置方式**:
```go
bp := retry.NewBackupPolicy(100 * time.Millisecond) // 100ms 后发起备份请求
client.WithBackupRequest(bp)
```

**适用场景**:
- 对延迟敏感的业务
- 下游服务性能不稳定
- 允许请求放大的场景

**注意事项**:
- ⚠️ 会增加下游负载
- ⚠️ 要求接口幂等

### Failure Retry
请求失败后自动重试，提高调用成功率。

**类型**:
- **FailureRetry**: 失败重试
- **BackupRequest**: 备份请求（见上）

**配置方式**:
```go
fp := retry.NewFailurePolicy()
fp.WithMaxRetryTimes(2)                      // 最多重试 2 次
fp.WithRetryDelay(100 * time.Millisecond)    // 重试间隔
fp.WithDDLStop()                             // 超过 deadline 停止重试

client.WithFailureRetry(fp)
```

**重试策略**:
- 固定延迟
- 指数退避
- 随机抖动

**注意事项**:
- ⚠️ 确保接口幂等
- ⚠️ 合理设置重试次数
- ⚠️ 避免重试风暴

### Circuit Breaker (熔断器)
当下游服务异常率过高时，自动切断流量，避免雪崩效应。

**三种状态**:
```
关闭 (Closed) ──────→ 打开 (Open) ──────→ 半开 (Half-Open)
     ↑                                          │
     └──────────────────────────────────────────┘
```

**状态转换**:
- **Closed → Open**: 错误率超过阈值
- **Open → Half-Open**: 冷却时间到达
- **Half-Open → Closed**: 探测成功
- **Half-Open → Open**: 探测失败

**配置方式**:
```go
import "github.com/cloudwego/kitex/pkg/circuitbreak"

cbs := circuitbreak.NewCBSuite(func(ri rpcinfo.RPCInfo) string {
    return ri.To().ServiceName() // Service 级熔断
})

client.WithSuite(cbs)
```

**熔断级别**:
- **Service 级**: 针对整个服务熔断
- **Instance 级**: 针对单个实例熔断
- **Method 级**: 针对特定方法熔断

### Load Balance (负载均衡)
将请求分散到多个服务实例，提高可用性和性能。

**内置策略**:
- **加权随机 (WeightedRandom)**: 根据权重随机选择
- **加权轮询 (WeightedRoundRobin)**: 根据权重轮询
- **一致性哈希 (ConsistentHash)**: 根据请求特征哈希
- **最少连接 (LeastConnection)**: 选择连接数最少的实例

**配置方式**:
```go
import "github.com/cloudwego/kitex/pkg/loadbalance"

// 使用加权随机
client.WithLoadBalancer(loadbalance.NewWeightedRandomBalancer())

// 使用一致性哈希
client.WithLoadBalancer(loadbalance.NewConsistHashBalancer(
    loadbalance.NewConsistentHashOption(func(ctx context.Context, req interface{}) string {
        // 根据 user_id 哈希
        if r, ok := req.(*echo.EchoRequest); ok {
            return r.UserID
        }
        return ""
    }),
))
```

## 错误处理

### BizStatusError
业务级异常，用于表示业务逻辑错误（如参数校验失败、业务规则违反等）。

**创建方式**:
```go
import "github.com/cloudwego/kitex/pkg/kerrors"

// 返回业务错误
return nil, kerrors.NewBizStatusError(40001, "invalid parameter")
```

**判断和处理**:
```go
// Client 端处理
if bizErr, ok := kerrors.FromBizStatusError(err); ok {
    code := bizErr.BizStatusCode()    // 40001
    msg := bizErr.BizMessage()        // "invalid parameter"
    
    // 根据错误码处理
    switch code {
    case 40001:
        // 参数错误处理
    case 50001:
        // 服务错误处理
    }
}
```

**与 BaseResp 的关系**:
```thrift
struct BaseResp {
    1: i32 status_code
    2: string status_message
}

struct Response {
    1: required BaseResp base_resp
    2: optional Data data
}
```

Kitex 会自动将 BizStatusError 转换为 BaseResp。

## 高级特性

### Streaming
支持双向流式通信，客户端和服务端可以持续发送/接收消息。

**类型**:
- **Unary**: 普通请求/响应（非流式）
- **Server Streaming**: 服务端流式返回
- **Client Streaming**: 客户端流式发送
- **Bidirectional Streaming**: 双向流式

**使用场景**:
- 大文件传输
- 实时数据推送
- 长时间运算
- 聊天/消息系统

**示例**:
```go
// Server 端
func (s *StreamServiceImpl) Echo(stream echo.StreamService_EchoServer) error {
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        
        resp := &echo.EchoResponse{Message: req.Message}
        if err := stream.Send(resp); err != nil {
            return err
        }
    }
}

// Client 端
stream, err := client.Echo(ctx)
stream.Send(&echo.EchoRequest{Message: "hello"})
resp, err := stream.Recv()
```

### Suite
高层次的扩展封装，用于批量配置多个 Middleware/Option。

**作用**:
- 组合多个相关配置
- 简化配置代码
- 封装最佳实践

**示例**:
```go
type MySuite struct{}

func (s *MySuite) Options() []server.Option {
    return []server.Option{
        server.WithMiddleware(LogMiddleware),
        server.WithMiddleware(MetricsMiddleware),
        server.WithLimit(&limit.Option{MaxConnections: 1000}),
    }
}

// 使用 Suite
svr := echo.NewServer(
    new(EchoServiceImpl),
    server.WithSuite(new(MySuite)),
)
```

### Validator
自动校验 Thrift 结构体字段的合法性。

**使用方式**:
```thrift
struct User {
    1: required string name (vt.min_size = "1", vt.max_size = "20")
    2: required i32 age (vt.ge = "0", vt.le = "150")
    3: required string email (vt.pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
}
```

**生成校验代码**:
```bash
kitex -thrift with_validator=true your.thrift
```

**自动校验**:
```go
func (s *UserServiceImpl) CreateUser(ctx context.Context, req *user.CreateUserRequest) (*user.CreateUserResponse, error) {
    // Kitex 自动执行校验
    // 如果校验失败，直接返回错误
    
    // 业务逻辑...
    return &user.CreateUserResponse{}, nil
}
```

## 总结

这些核心概念构成了 Kitex 框架的基础，理解它们有助于更好地使用 Kitex 进行微服务开发。

**关键要点**:
- **Netpoll**: 高性能网络库基础
- **Middleware**: 可扩展的拦截器机制
- **连接管理**: 长连接池 + 多路复用
- **服务治理**: 重试、熔断、负载均衡
- **错误处理**: BizStatusError 处理业务错误
- **泛化调用**: 无需生成代码动态调用
- **高级特性**: Streaming、Suite、Validator

更多详细信息，请参考 [Kitex 官方文档](https://www.cloudwego.io/zh/docs/kitex/)。
