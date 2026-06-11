# Kitex 泛化调用

## 什么是泛化调用?

泛化调用允许在没有 IDL 的情况下调用 RPC 服务,适用于:
- API 网关
- 调试工具
- 跨语言调用

## HTTP 泛化调用

### Server 端

```go
import (
    "github.com/cloudwego/kitex/pkg/generic"
    "github.com/cloudwego/kitex/server/genericserver"
)

// 加载 IDL
p, err := generic.NewThriftFileProvider("example.thrift")
g, err := generic.HTTPThriftGeneric(p)

// 创建 Generic Server
svr := genericserver.NewServer(
    &GenericServiceImpl{},
    g,
    server.WithServiceAddr(&net.TCPAddr{Port: 8888}),
)
```

### Client 端

```go
// 加载 IDL
p, err := generic.NewThriftFileProvider("example.thrift")
g, err := generic.HTTPThriftGeneric(p)

// 创建 Generic Client
cli, err := genericclient.NewClient(
    "myservice",
    g,
    client.WithHostPorts("127.0.0.1:8888"),
)

// 调用
req := `{"method":"GetUser","uid":123}`
resp, err := cli.GenericCall(ctx, "GetUser", req)
```

## JSON 泛化调用

```go
p, err := generic.NewThriftFileProvider("example.thrift")
g, err := generic.JSONThriftGeneric(p)

cli, err := genericclient.NewClient("myservice", g)

req := `{"uid":123,"name":"test"}`
resp, err := cli.GenericCall(ctx, "GetUser", req)
```

## Map 泛化调用

```go
g, err := generic.MapThriftGeneric(p)

req := map[string]interface{}{
    "uid":  123,
    "name": "test",
}

resp, err := cli.GenericCall(ctx, "GetUser", req)
```

## 使用场景

### API 网关

无需生成代码即可转发请求。

### 调试工具

方便调试和测试 RPC 服务。

### 跨语言调用

不同语言间通过 JSON 交互。

## 注意事项

- 性能略低于普通调用
- 需要提供 IDL 文件
- 类型检查在运行时

## 相关文档

- [创建第一个服务](./create-first-service.md)
- [定义 Thrift IDL](./define-thrift-idl.md)
