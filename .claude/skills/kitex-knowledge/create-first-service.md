# 创建第一个 Kitex 服务

本文档将引导你从零开始创建一个简单的 Kitex 服务,包括 Server 和 Client。

## 项目初始化

### 1. 创建项目目录

```bash
mkdir hello-kitex
cd hello-kitex
go mod init hello-kitex
```

### 2. 安装依赖

```bash
go get github.com/cloudwego/kitex@latest
```

## 定义 IDL

创建 `echo.thrift` 文件:

```thrift
namespace go echo

struct EchoRequest {
    1: required string message
}

struct EchoResponse {
    1: required string message
}

service EchoService {
    EchoResponse Echo(1: EchoRequest req)
}
```

**说明**:
- `namespace go echo`: 指定生成的 Go 包名为 echo
- `struct`: 定义数据结构
- `service`: 定义服务接口
- `1:`: 字段编号,用于序列化

## 生成代码

### 生成 Server 端代码

```bash
kitex -module hello-kitex -service echo.service echo.thrift
```

**参数说明**:
- `-module`: 指定 Go module 名称
- `-service`: 指定服务名称,会生成完整的 Server 代码

### 生成的目录结构

```
hello-kitex/
├── echo.thrift
├── go.mod
├── go.sum
├── kitex_gen/           # 生成的代码
│   └── echo/
│       ├── echo.go
│       ├── echoservice/
│       │   ├── client.go
│       │   ├── server.go
│       │   └── ...
│       └── ...
├── handler.go           # 业务逻辑实现
├── main.go              # Server 入口
└── build.sh             # 构建脚本
```

## 实现业务逻辑

编辑 `handler.go`:

```go
package main

import (
    "context"
    "fmt"

    "hello-kitex/kitex_gen/echo"
)

// EchoServiceImpl implements the last service interface defined in the IDL.
type EchoServiceImpl struct{}

// Echo implements the EchoServiceImpl interface.
func (s *EchoServiceImpl) Echo(ctx context.Context, req *echo.EchoRequest) (resp *echo.EchoResponse, err error) {
    // 实现业务逻辑
    message := fmt.Sprintf("Server received: %s", req.Message)

    resp = &echo.EchoResponse{
        Message: message,
    }

    return resp, nil
}
```

## 启动 Server

### 查看默认 main.go

生成的 `main.go` 已经包含了基本的 Server 启动代码:

```go
package main

import (
    "log"

    "hello-kitex/kitex_gen/echo/echoservice"
    "github.com/cloudwego/kitex/server"
)

func main() {
    svr := echoservice.NewServer(new(EchoServiceImpl))

    err := svr.Run()
    if err != nil {
        log.Println(err.Error())
    }
}
```

### 启动服务

```bash
go run .
```

输出:
```
[INFO] server listen at addr=[::]:8888
```

Server 默认监听 8888 端口。

## 创建 Client

### 创建 Client 代码

新建 `client/main.go`:

```go
package main

import (
    "context"
    "log"

    "hello-kitex/kitex_gen/echo"
    "hello-kitex/kitex_gen/echo/echoservice"
    "github.com/cloudwego/kitex/client"
)

func main() {
    // 创建 Client
    c, err := echoservice.NewClient(
        "echo.service",
        client.WithHostPorts("127.0.0.1:8888"),
    )
    if err != nil {
        log.Fatal(err)
    }

    // 构造请求
    req := &echo.EchoRequest{
        Message: "Hello Kitex!",
    }

    // 发起调用
    resp, err := c.Echo(context.Background(), req)
    if err != nil {
        log.Fatal(err)
    }

    // 打印响应
    log.Printf("Response: %s", resp.Message)
}
```

### 运行 Client

在新终端中:

```bash
go run client/main.go
```

输出:
```
Response: Server received: Hello Kitex!
```

## 完整流程总结

1. **定义 IDL**: 描述服务接口和数据结构
2. **生成代码**: 使用 `kitex` 命令生成框架代码
3. **实现 Handler**: 在 `handler.go` 中实现业务逻辑
4. **启动 Server**: 运行 `main.go` 启动服务
5. **创建 Client**: 编写客户端代码调用服务
6. **测试**: 验证服务正常工作

## 自定义配置

### 修改监听端口

在 `main.go` 中:

```go
import "github.com/cloudwego/kitex/server"

func main() {
    svr := echoservice.NewServer(
        new(EchoServiceImpl),
        server.WithServiceAddr(&net.TCPAddr{Port: 9999}),
    )

    err := svr.Run()
    //...
}
```

### 添加日志

```go
import "github.com/cloudwego/kitex/pkg/klog"

func (s *EchoServiceImpl) Echo(ctx context.Context, req *echo.EchoRequest) (resp *echo.EchoResponse, err error) {
    klog.Infof("Received request: %s", req.Message)

    resp = &echo.EchoResponse{
        Message: fmt.Sprintf("Echo: %s", req.Message),
    }

    return resp, nil
}
```

## 常见问题

### 端口已被占用

**错误**: `bind: address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8888

# 杀死进程或更改端口
```

### 连接被拒绝

**错误**: `connection refused`

**原因**: Server 未启动或地址不正确

**解决方案**:
1. 确认 Server 已启动
2. 检查 Client 中的地址和端口

### 导入路径错误

**错误**: `cannot find module`

**解决方案**:
```bash
# 更新依赖
go mod tidy

# 如果是 module 名称问题,修改 go.mod
```

## 下一步

- 学习《服务治理 - 超时配置》
- 了解《服务治理 - 重试策略》
- 学习《中间件开发》
- 探索《高级特性》

## 完整项目示例

完整的示例代码可以在字节内部 GitLab 查看:
- [kitex-examples](https://code.byted.org/kite/kitex-examples)
