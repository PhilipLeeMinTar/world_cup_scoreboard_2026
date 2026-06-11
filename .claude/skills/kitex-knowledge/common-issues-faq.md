# Kitex 常见问题 FAQ

## 中间件使用问题

### Q1: 如何在中间件中获取 Request/Response？

**问题**: 在中间件中需要访问请求和响应的具体字段

**解决方案**:
```go
func LogMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        // 方法1: 使用类型断言
        if echoReq, ok := req.(*echo.EchoRequest); ok {
            log.Printf("request message: %s", echoReq.Message)
        }
        
        err := next(ctx, req, resp)
        
        // 方法2: 使用反射（不推荐，性能较差）
        reqValue := reflect.ValueOf(req)
        if reqValue.Kind() == reflect.Ptr {
            reqValue = reqValue.Elem()
        }
        
        return err
    }
}
```

**注意事项**:
- 推荐使用类型断言而不是反射
- Client 中间件 req/resp 是 XXXArgs/XXXResult 类型
- Server 中间件 req/resp 是业务 Request/Response 类型

### Q2: 如何获取 BaseResp？

**问题**: Thrift IDL 中定义了 BaseResp 但无法直接访问

**解决方案**:
```go
func BaseRespMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        err := next(ctx, req, resp)
        
        // 使用 GetOrSetBaseResp 获取 BaseResp
        if baseResp := base.GetOrSetBaseResp(resp); baseResp != nil {
            log.Printf("status_code=%d, status_msg=%s", 
                baseResp.StatusCode, baseResp.StatusMessage)
        }
        
        return err
    }
}
```

### Q3: 中间件执行顺序是什么？

**回答**: 
- **注册顺序**: WithMiddleware(mw1, mw2, mw3)
- **执行顺序**: mw1(前) → mw2(前) → mw3(前) → Handler → mw3(后) → mw2(后) → mw1(后)

**示例**:
```go
server.WithMiddleware(
    LogMiddleware,    // 最外层
    MetricsMiddleware, // 中间层
    AuthMiddleware,    // 最内层
)

// 执行顺序:
// Log(前) → Metrics(前) → Auth(前) → Handler → Auth(后) → Metrics(后) → Log(后)
```

## 安装和工具问题

### Q4: `go install` 安装 kitex 失败

**问题**: 执行 `go install github.com/cloudwego/kitex/tool/cmd/kitex@latest` 失败

**常见原因和解决方案**:

1. **Go 版本过低**
   ```bash
   # 检查 Go 版本
   go version
   
   # Kitex 要求 Go 1.16+
   # 升级 Go 到最新版本
   ```

2. **网络问题**
   ```bash
   # 设置 GOPROXY
   go env -w GOPROXY=https://goproxy.cn,direct
   
   # 或使用其他代理
   go env -w GOPROXY=https://goproxy.io,direct
   ```

3. **GOPATH/GOBIN 未设置**
   ```bash
   # 设置 GOBIN
   export GOBIN=$GOPATH/bin
   
   # 或添加到 PATH
   export PATH=$PATH:$(go env GOPATH)/bin
   ```

### Q5: `kitex: command not found`

**问题**: 安装成功但无法执行 kitex 命令

**解决方案**:
```bash
# 1. 检查 kitex 是否安装成功
ls $(go env GOPATH)/bin/kitex

# 2. 将 GOPATH/bin 添加到 PATH
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
source ~/.bashrc

# 3. 或使用完整路径
$(go env GOPATH)/bin/kitex -version
```

### Q6: KiteX Tool 自动更新失败

**问题**: 工具启动时提示 "new version available" 但更新失败

**解决方案**:
```bash
# 1. 禁用自动更新
kitex -disable-self-update your.thrift

# 2. 手动更新
go install github.com/cloudwego/kitex/tool/cmd/kitex@latest

# 3. 固定版本（生产环境推荐）
go install github.com/cloudwego/kitex/tool/cmd/kitex@v0.8.0
```

## 连接和网络问题

### Q7: 连接多路复用如何配置？

**问题**: 想使用连接多路复用减少连接数

**Server 端配置**:
```go
import "github.com/cloudwego/kitex/pkg/remote"

svr := echo.NewServer(
    new(EchoServiceImpl),
    server.WithMuxTransport(),
)
```

**Client 端配置**:
```go
client, err := echo.NewClient(
    "echo",
    client.WithHostPorts("127.0.0.1:8888"),
    client.WithMuxTransport(),
)
```

**注意事项**:
- 需要 Server 和 Client 同时开启
- 适用于高并发低流量场景
- 不适用于大包场景（会增加延迟）

### Q8: 如何配置连接超时和 RPC 超时？

**问题**: 需要单独配置连接建立超时和 RPC 调用超时

**解决方案**:
```go
client, err := echo.NewClient(
    "echo",
    // 连接超时（建立连接的超时时间）
    client.WithConnectTimeout(1 * time.Second),
    
    // RPC 超时（整个 RPC 调用的超时时间）
    client.WithRPCTimeout(3 * time.Second),
)

// CallOption 动态覆盖
resp, err := client.Echo(
    ctx,
    req,
    callopt.WithRPCTimeout(5 * time.Second),
)
```

**超时优先级**: CallOption > Client Option > 默认值

### Q9: 长连接池配置建议

**问题**: 不知道如何配置连接池参数

**推荐配置**:
```go
client.WithLongConnection(
    connpool.IdleConfig{
        MaxIdlePerAddress: 10,   // 单地址最大空闲连接（根据 QPS 调整）
        MaxIdleGlobal:     1000, // 全局最大空闲连接
        MaxIdleTimeout:    60 * time.Second, // 空闲超时
        MinIdlePerAddress: 2,    // 最小保持连接（预热）
    },
)
```

**参数调优**:
- **高 QPS**: MaxIdlePerAddress 设置为 10-20
- **低 QPS**: MaxIdlePerAddress 设置为 2-5
- **多下游**: 增大 MaxIdleGlobal
- **长时间空闲**: 减小 MaxIdleTimeout

## 版本兼容问题

### Q10: Thrift 版本不兼容

**问题**: 生成代码后编译报错，提示 Thrift 版本不匹配

**解决方案**:
```bash
# 1. 查看当前 Thrift 版本
go list -m github.com/apache/thrift

# 2. 锁定推荐版本
go get github.com/apache/thrift@v0.13.0

# 3. 使用 go.mod replace
# go.mod
replace github.com/apache/thrift => github.com/apache/thrift v0.13.0
```

**版本兼容表**:
- Kitex v0.4.0+ 推荐 Thrift v0.13.0
- Kitex v0.5.0+ 推荐 Thrift v0.14.1
- Kitex v0.8.0+ 推荐 Thrift v0.17.0

### Q11: Kitex 版本升级注意事项

**问题**: 升级 Kitex 版本后出现兼容性问题

**升级步骤**:
```bash
# 1. 查看当前版本
go list -m github.com/cloudwego/kitex

# 2. 升级到指定版本
go get github.com/cloudwego/kitex@v0.8.0

# 3. 重新生成代码
kitex -module xxx your.thrift

# 4. 运行测试
go test ./...
```

**注意事项**:
- **大版本升级**: 可能有 Breaking Changes，查看 CHANGELOG
- **重新生成代码**: 升级后务必重新生成代码
- **测试验证**: 升级前在测试环境验证

## 错误处理问题

### Q12: Panic 如何恢复？

**问题**: Handler 中发生 panic 导致服务崩溃

**解决方案**:
```go
func RecoveryMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) (err error) {
        defer func() {
            if r := recover(); r != nil {
                // 记录 panic 信息
                log.Errorf("panic recovered: %v\nstack: %s", r, debug.Stack())
                
                // 返回错误
                err = kerrors.NewBizStatusError(500, "internal server error")
            }
        }()
        
        return next(ctx, req, resp)
    }
}

// 注册中间件
server.WithMiddleware(RecoveryMiddleware)
```

**Kitex 内置 Panic 恢复**: Kitex 框架默认会捕获 panic，但建议自定义中间件记录详细日志

### Q13: 如何区分超时错误和业务错误？

**问题**: 需要根据错误类型做不同处理

**解决方案**:
```go
resp, err := client.Echo(ctx, req)
if err != nil {
    // 1. 超时错误
    if kerrors.IsTimeoutError(err) {
        log.Errorf("timeout: %v", err)
        return nil, err
    }
    
    // 2. 业务错误
    if bizErr, ok := kerrors.FromBizStatusError(err); ok {
        log.Errorf("biz error: code=%d, msg=%s", 
            bizErr.BizStatusCode(), bizErr.BizMessage())
        return nil, err
    }
    
    // 3. 其他框架错误
    log.Errorf("kitex error: %v", err)
    return nil, err
}
```

## 泛化调用问题

### Q14: HTTP 泛化调用如何使用？

**问题**: 想通过 HTTP 调用 Thrift 服务

**解决方案**:
```go
import (
    "github.com/cloudwego/kitex/pkg/generic"
    "github.com/cloudwego/kitex/client/genericclient"
)

// 1. 创建泛化调用 client
p, err := generic.NewThriftFileProvider("echo.thrift")
g, err := generic.HTTPThriftGeneric(p)
cli, err := genericclient.NewClient("echo", g, client.WithHostPorts("127.0.0.1:8888"))

// 2. 构造 HTTP 请求
body := map[string]interface{}{
    "message": "hello",
}
req, err := http.NewRequest("POST", "http://example.com/Echo", nil)
customReq, err := generic.FromHTTPRequest(req)

// 3. 发起调用
resp, err := cli.GenericCall(ctx, "Echo", customReq, callopt.WithRPCTimeout(3*time.Second))
```

## 性能问题

### Q15: QPS 上不去怎么办？

**问题**: 压测时 QPS 达不到预期

**排查步骤**:

1. **检查连接数配置**
   ```go
   // 增大连接池
   client.WithLongConnection(
       connpool.IdleConfig{
           MaxIdlePerAddress: 20,
           MaxIdleGlobal:     2000,
       },
   )
   ```

2. **开启连接多路复用**
   ```go
   server.WithMuxTransport()
   client.WithMuxTransport()
   ```

3. **调整 Netpoll 参数**
   ```go
   import "github.com/cloudwego/netpoll"
   
   // 增大读写缓冲区
   server.WithReadBufferSize(8192)
   server.WithWriteBufferSize(8192)
   ```

4. **检查业务逻辑**
   - 避免阻塞操作（数据库查询、HTTP 调用等）
   - 使用 pprof 分析性能瓶颈

### Q16: 内存占用过高

**问题**: 服务运行一段时间后内存持续增长

**排查步骤**:

1. **检查连接泄漏**
   ```bash
   # 查看连接数
   netstat -an | grep ESTABLISHED | wc -l
   
   # 监控 goroutine 数量
   curl http://localhost:9091/debug/pprof/goroutine?debug=1
   ```

2. **检查对象池**
   ```go
   // Kitex 使用 sync.Pool 优化对象分配
   // 如果自定义对象，记得放回池中
   ```

3. **使用 pprof 分析内存**
   ```bash
   # 采集内存 profile
   go tool pprof http://localhost:9091/debug/pprof/heap
   
   # 分析内存分配
   top 10
   list functionName
   ```

## 其他问题

### Q17: 如何实现基于 Method 的处理逻辑？

**问题**: 想对不同的 Method 执行不同的逻辑

**解决方案**:
```go
func MethodBasedMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        ri := rpcinfo.GetRPCInfo(ctx)
        method := ri.To().Method()
        
        switch method {
        case "Echo":
            // Echo 方法特殊处理
            log.Printf("calling Echo")
        case "Ping":
            // Ping 方法特殊处理
            log.Printf("calling Ping")
        }
        
        return next(ctx, req, resp)
    }
}
```

### Q18: 如何动态修改下游地址？

**问题**: 根据请求内容路由到不同的下游实例

**解决方案**:
```go
// 使用 CallOption 动态指定地址
resp, err := client.Echo(
    ctx,
    req,
    callopt.WithHostPort("192.168.1.100:8888"),
)

// 或在中间件中修改
func DynamicRouteMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        // 从请求中提取路由信息
        if echoReq, ok := req.(*echo.EchoRequest); ok {
            if echoReq.RouteKey == "cluster-a" {
                ctx = callopt.WithHostPort("cluster-a.example.com:8888")(ctx)
            }
        }
        
        return next(ctx, req, resp)
    }
}
```

### Q19: 服务注册发现如何配置？

**问题**: 想使用服务注册中心（如 Consul、Etcd）

**解决方案**:
```go
import (
    consul "github.com/kitex-contrib/registry-consul"
)

// Server 端注册
r, err := consul.NewConsulRegister("127.0.0.1:8500")
svr := echo.NewServer(
    new(EchoServiceImpl),
    server.WithRegistry(r),
    server.WithServerBasicInfo(&rpcinfo.EndpointBasicInfo{
        ServiceName: "echo",
    }),
)

// Client 端发现
r, err := consul.NewConsulResolver("127.0.0.1:8500")
client, err := echo.NewClient(
    "echo",
    client.WithResolver(r),
)
```

### Q20: 如何实现灰度发布？

**问题**: 想对部分流量使用新版本服务

**解决方案**:
```go
// 1. 使用 Tag 区分版本
server.WithServerBasicInfo(&rpcinfo.EndpointBasicInfo{
    ServiceName: "echo",
    Tags: map[string]string{
        "version": "v2",
    },
})

// 2. Client 端根据条件路由
func GrayMiddleware(next endpoint.Endpoint) endpoint.Endpoint {
    return func(ctx context.Context, req, resp interface{}) error {
        // 10% 流量到 v2
        if rand.Intn(100) < 10 {
            ctx = metainfo.WithValue(ctx, "version", "v2")
        }
        
        return next(ctx, req, resp)
    }
}
```
