# Kitex 最佳实践

## IDL 设计规范

### 命名规范
- **使用有意义的命名**: Service/Method/Field 都应清晰表达业务语义
- **一致的命名风格**: 统一使用驼峰命名或下划线命名  
- **避免缩写**: 除非是业内公认的缩写(如 ID、URL)

### 结构设计  
- **避免过度嵌套**: 结构体嵌套层级建议不超过3层
- **合理使用 optional**: 只对真正可选的字段使用 optional
- **字段编号规划**:
  - Base 字段: 255
  - 关键字段: 1-20  
  - 普通字段: 21+
  - 预留扩展空间

### 版本兼容性
- **只新增字段不删除**: 保持向后兼容
- **使用 @deprecated 标记废弃字段**: 而不是直接删除
- **Required vs Optional**: 新增字段建议使用 optional

## 代码生成最佳实践

### 工具配置
```bash
# 使用 go mod 管理依赖
kitex -module github.com/your-org/your-service your.thrift

# 公共 IDL 通过 git 引用
kitex -I git@code.byted.org:your-team/idl.git your.thrift

# 生产环境固定版本  
kitex -disable-self-update -module xxx your.thrift
```

### 版本管理
- **生成代码版本追踪**: 在代码第一行注释查看生成时的 KiteX Tool 版本
- **依赖版本锁定**: `go get github.com/apache/thrift@v0.13.0`
- **go.mod replace**: `replace github.com/apache/thrift => github.com/apache/thrift@v0.13.0`

### 代码组织
- **使用 -service 参数**: 指定服务名避免目录混乱
- **分离 handler 逻辑**: 不要在生成的 handler_stub.go 中直接编写业务逻辑
- **IDL 单独仓库管理**: 推荐将 IDL 文件单独管理以便复用

## 服务端开发最佳实践

### 初始化配置
```go
svr := echo.NewServer(
    server.WithServiceAddr(&net.TCPAddr{IP: net.IPv4zero, Port: 8888}),
    server.WithMiddleware(CommonMiddleware),
    server.WithSuite(tracing.NewServerSuite()),
    server.WithServerBasicInfo(&rpcinfo.EndpointBasicInfo{ServiceName: "echo"}),
)
```

### 关键配置项
- **WithServiceAddr**: 监听地址和端口
- **WithMiddleware**: 注册中间件
- **WithSuite**: 使用 Suite 批量配置扩展
- **WithLimit**: 限流配置
- **WithMuxTransport**: 连接多路复用
- **WithExitWaitTime**: 优雅退出等待时间

### 优雅关闭
```go
// 监听系统信号
go func() {
    sig := <-signals
    svr.Stop() // 触发优雅关闭
}()

if err := svr.Run(); err != nil {
    log.Fatal(err)
}
```

## 客户端开发最佳实践

### Client 初始化
```go
client, err := echo.NewClient(
    "echo",
    client.WithHostPorts("127.0.0.1:8888"),
    client.WithMiddleware(CommonMiddleware),
    client.WithSuite(tracing.NewClientSuite()),
    client.WithRPCTimeout(3*time.Second),
)
```

### 长连接池配置
```go
client.WithLongConnection(
    connpool.IdleConfig{
        MaxIdlePerAddress: 10,
        MaxIdleGlobal:     100,
        MaxIdleTimeout:    60 * time.Second,
    },
)
```

### 重试配置
```go
fp := retry.NewFailurePolicy()
fp.WithMaxRetryTimes(2)
fp.WithRetryDelay(100 * time.Millisecond)
client.WithFailureRetry(fp)
```

### 熔断配置
```go
cbs := circuitbreak.NewCBSuite(func(ri rpcinfo.RPCInfo) string {
    return ri.To().ServiceName()
})
client.WithSuite(cbs)
```

## 中间件开发最佳实践

### Server 中间件
```go
func ServerMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) (err error) {
        // 前置处理
        start := time.Now()
        
        // 调用下一个中间件或 Handler
        err = next(ctx, req, resp)
        
        // 后置处理
        cost := time.Since(start)
        log.Printf("cost=%v", cost)
        
        return err
    }
}
```

### Client 中间件
```go
func ClientMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) (err error) {
        // 获取 RPCInfo
        ri := rpcinfo.GetRPCInfo(ctx)
        
        // 前置处理
        log.Printf("calling %s", ri.To().Method())
        
        err = next(ctx, req, resp)
        
        // 后置处理
        if err != nil {
            log.Printf("call failed: %v", err)
        }
        
        return err
    }
}
```

### 获取 Request/Response
```go
func LogMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        // 获取请求
        if echoReq, ok := req.(*echo.EchoRequest); ok {
            log.Printf("request: %+v", echoReq)
        }
        
        err := next(ctx, req, resp)
        
        // 获取响应
        if echoResp, ok := resp.(*echo.EchoResponse); ok {
            log.Printf("response: %+v", echoResp)
        }
        
        return err
    }
}
```

## 性能优化最佳实践

### 连接多路复用
```go
// Server 端开启
server.WithMuxTransport()

// Client 端开启
client.WithMuxTransport()
```

**适用场景**: 
- 高并发低流量场景
- 连接数受限场景
- 减少 TIME_WAIT 连接

### 连接池优化
```go
client.WithLongConnection(
    connpool.IdleConfig{
        MaxIdlePerAddress: 10,  // 单个地址最大空闲连接
        MaxIdleGlobal:     1000, // 全局最大空闲连接
        MaxIdleTimeout:    60 * time.Second,
        MinIdlePerAddress: 2,    // 最小保持连接数
    },
)
```

### Netpoll 使用
Kitex 默认使用 Netpoll 作为网络库:
- **基于 Epoll**: 高性能事件驱动
- **零拷贝**: 减少内存复制
- **LinkBuffer**: 高效的内存管理

**注意**: 如果使用标准库 net，需要显式指定:
```go
server.WithTransHandlerFactory(netpoll.NewSvrTransHandlerFactory())
```

### 预热优化
```go
import "github.com/cloudwego/kitex/pkg/warmup"

// 服务启动时预热
warmup.WarmupHandlers(handlers...)
```

## 错误处理最佳实践

### 业务错误使用 BizStatusError
```go
import "github.com/cloudwego/kitex/pkg/kerrors"

func (s *EchoServiceImpl) Echo(ctx context.Context, req *echo.EchoRequest) (*echo.EchoResponse, error) {
    if req.Message == "" {
        return nil, kerrors.NewBizStatusError(400, "message is empty")
    }
    
    return &echo.EchoResponse{Message: req.Message}, nil
}
```

### 框架错误处理
```go
// Client 端
resp, err := client.Echo(ctx, req)
if err != nil {
    // 区分错误类型
    if kerrors.IsTimeoutError(err) {
        log.Printf("timeout: %v", err)
    } else if bizErr, ok := kerrors.FromBizStatusError(err); ok {
        log.Printf("biz error: code=%d, msg=%s", bizErr.BizStatusCode(), bizErr.BizMessage())
    } else {
        log.Printf("unknown error: %v", err)
    }
}
```

### 中间件错误处理
```go
func ErrorHandlerMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        err := next(ctx, req, resp)
        
        if err != nil {
            // 记录错误
            ri := rpcinfo.GetRPCInfo(ctx)
            log.Printf("[ERROR] service=%s method=%s err=%v", 
                ri.To().ServiceName(), ri.To().Method(), err)
            
            // 上报监控
            metrics.EmitCounter("rpc.error", 1, 
                "service", ri.To().ServiceName(),
                "method", ri.To().Method())
        }
        
        return err
    }
}
```

## 配置管理最佳实践

### 使用配置文件
```yaml
# kitex.yml
server:
  address: :8888
  service_name: echo
  read_timeout: 5s
  write_timeout: 5s

client:
  echo:
    address: 127.0.0.1:8888
    rpc_timeout: 3s
    conn_timeout: 1s
```

### 配置热更新
```go
import "github.com/cloudwego/kitex/pkg/remote/codec/thrift"

// 实现配置更新接口
type ConfigReloader interface {
    OnConfigChange(config *Config)
}

// 监听配置变化
watcher.Watch(func(config *Config) {
    // 更新配置
    reloader.OnConfigChange(config)
})
```

### 多环境配置
```bash
# 开发环境
kitex -config dev/kitex.yml

# 测试环境
kitex -config test/kitex.yml

# 生产环境
kitex -config prod/kitex.yml
```

## 测试最佳实践

### 单元测试
```go
func TestEchoService(t *testing.T) {
    // 创建 mock client
    mockClient := mock.NewMockEchoService(t)
    
    // 设置期望
    mockClient.EXPECT().Echo(
        gomock.Any(),
        &echo.EchoRequest{Message: "hello"},
    ).Return(&echo.EchoResponse{Message: "hello"}, nil)
    
    // 测试
    resp, err := mockClient.Echo(context.Background(), &echo.EchoRequest{Message: "hello"})
    assert.NoError(t, err)
    assert.Equal(t, "hello", resp.Message)
}
```

### 集成测试
```go
func TestEchoIntegration(t *testing.T) {
    // 启动测试服务
    svr := echo.NewServer(new(EchoServiceImpl), server.WithServiceAddr(&net.TCPAddr{Port: 8888}))
    go svr.Run()
    defer svr.Stop()
    
    // 创建客户端
    client, _ := echo.NewClient("echo", client.WithHostPorts("127.0.0.1:8888"))
    
    // 测试调用
    resp, err := client.Echo(context.Background(), &echo.EchoRequest{Message: "test"})
    assert.NoError(t, err)
    assert.Equal(t, "test", resp.Message)
}
```

### 压测
```bash
# 使用 hey 工具压测
hey -n 10000 -c 100 -m POST -H "Content-Type: application/json" \
    -d '{"message":"hello"}' http://localhost:8888/echo
```

## 监控和日志最佳实践

### 日志规范
```go
import "github.com/cloudwego/kitex/pkg/klog"

// 使用 klog
klog.Infof("service started on %s", addr)
klog.Errorf("failed to call service: %v", err)

// 设置日志级别
klog.SetLevel(klog.LevelInfo)

// 自定义 logger
klog.SetLogger(yourLogger)
```

### 监控指标
推荐监控的关键指标:
- **QPS**: 每秒请求数
- **延迟**: P50/P95/P99 延迟
- **错误率**: 错误请求比例
- **连接数**: 活跃连接数
- **超时率**: 超时请求比例
- **重试率**: 重试请求比例

### Tracing 集成
```go
import "github.com/kitex-contrib/tracer-opentracing"

// Server 端
svr := echo.NewServer(
    new(EchoServiceImpl),
    server.WithSuite(tracing.NewServerSuite()),
)

// Client 端
client, _ := echo.NewClient(
    "echo",
    client.WithSuite(tracing.NewClientSuite()),
)
```
