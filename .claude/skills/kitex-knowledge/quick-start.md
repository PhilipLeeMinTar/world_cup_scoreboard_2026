# Kitex 快速入门

本文档面向有经验的开发者，快速上手 Kitex 框架。

## 代码生成工具安装

获取 kitex 代码生成工具：

```bash
go install code.byted.org/kite/kitex/tool/cmd/kitex@latest
```

验证安装：

```bash
$ kitex -h
Usage: kitex [flags] IDL
flags:
  -module string
        Specify the Go module name to generate go.mod.
  -service string
        Specify the service name to generate server side codes.
  -v
  -verbose
        Turn on verbose mode.
```

**注意**：
- kitex 只在当前目录生成代码，需要先切换到目标项目目录
- 如果当前目录不在 `GOPATH` 下，需要通过 `-module` 指定模块名

## 示例 IDL

假设我们的 IDL 文件 `toutiao_kitex_demo.thrift` 内容如下：

```thrift
namespace py toutiao.kitex.demo
namespace go toutiao.kitex.demo
include "base.thrift"

struct DemoRequest {
    1: required string Message,
    255: optional base.Base Base;
}

struct DemoResponse {
    1: required string Message,
    255: optional base.BaseResp BaseResp;
}

service DemoService {
    DemoResponse Greet(1: DemoRequest request);
}
```

## 生成代码

### 生成客户端代码

直接指定 IDL 文件，生成可用于创建客户端的代码：

```bash
kitex toutiao_kitex_demo.thrift
```

生成的目录结构：

```
.
└── kitex_gen
    ├── base
    │   ├── base-consts.go
    │   ├── base.go
    │   └── GoUnusedProtection__.go
    └── toutiao
        └── kitex
            └── demo
                ├── demoservice
                │   ├── client.go    # NewClient & MustNewClient
                │   ├── kClient.go
                │   └── server.go
                ├── toutiao_kitex_demo-consts.go
                └── toutiao_kitex_demo.go
```

### 生成服务端代码

使用 `-service` 参数生成完整的服务端代码骨架：

```bash
kitex -service toutiao.kitex.demo toutiao_kitex_demo.thrift
```

生成的目录结构：

```
.
├── build.sh          # 构建脚本
├── conf
│   └── kitex.yml     # 默认配置文件
├── handler.go        # 业务逻辑实现
├── kitex_gen
│   ├── base
│   │   ├── base-consts.go
│   │   └── base.go
│   └── toutiao
│       └── kitex
│           └── demo
│               ├── demoservice
│               │   ├── client.go
│               │   ├── kClient.go
│               │   └── server.go
│               ├── toutiao_kitex_demo-consts.go
│               └── toutiao_kitex_demo.go
├── main.go           # Server 创建和启动入口
└── script
    ├── bootstrap.sh
    └── settings.py
```

## 代码示例

### 客户端代码

在项目目录新建 `app/main.go`：

```go
package main

import (
    "context"
    "fmt"

    "code.byted.org/kite/kitex/client/callopt"
    "code.byted.org/kite/tests/demo/kitex_gen/toutiao/kitex/demo"
    "code.byted.org/kite/tests/demo/kitex_gen/toutiao/kitex/demo/demoservice"
)

func main() {
    // 创建客户端，参数为目标服务的 PSM
    client := demoservice.MustNewClient("toutiao.kitex.demo")

    ctx := context.Background()
    req := &demo.DemoRequest{
        Message: "Hello",
    }

    // 发起 RPC 调用
    resp, err := client.Greet(ctx, req, callopt.WithHostPort("localhost:8888"))
    if err != nil {
        fmt.Printf("failed: %s\n", err.Error())
    } else {
        fmt.Printf("OK: %s\n", resp.Message)
    }
}
```

### 服务端代码

修改生成的 `handler.go` 添加业务逻辑：

```go
package main

import (
    "context"

    "code.byted.org/kite/tests/kitex_gen/toutiao/kitex/demo"
)

// DemoServiceImpl implements the last service interface defined in the IDL.
type DemoServiceImpl struct{}

// Greet implements the DemoServiceImpl interface.
func (s *DemoServiceImpl) Greet(ctx context.Context, request *demo.DemoRequest) (resp *demo.DemoResponse, err error) {
    // TODO: Your code here...
    println("Received:", request.Message)
    resp = &demo.DemoResponse{
        Message: "你好",
    }
    return resp, nil
}
```

## 运行服务

### 启动服务端

```bash
./build.sh && ./output/bootstrap.sh
```

**注意**：如果遇到 thrift 接口问题，请执行：

```bash
go mod edit -replace=github.com/apache/thrift=github.com/apache/thrift@v0.13.0
```

### 运行客户端

```bash
go run app/main.go
```

### 输出结果

服务端输出：

```
Info 2019-11-21 16:44:05,706 v1(6) server.go:114 10.227.7.116 - - default - server listen at: :8888
Info 2019-11-21 16:44:05,707 v1(6) once.go:66 10.227.7.116 - - default - starting debug server
Received: Hello
```

客户端输出：

```
OK: 你好
```

## 常见问题

### Q: kitex: command not found

**原因**：没有把 `$GOPATH/bin` 加入到 `$PATH` 中

**解决方案**：

```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

### Q: 代码生成工具安装失败

**解决方案**：
1. 检查 Go 代理配置
2. 检查 Git 配置
3. 确保已配置 `GOPRIVATE` 环境变量

```bash
go env -w GOPRIVATE="*.byted.org"
```

### Q: thrift 接口兼容性问题

如果遇到 `not enough arguments in call to iprot.ReadStructBegin` 等编译错误：

```bash
go mod edit -replace=github.com/apache/thrift=github.com/apache/thrift@v0.13.0
```

## 下一步

- [定义 Thrift IDL](./define-thrift-idl.md) - 学习 IDL 定义规范
- [从 IDL 生成代码](./generate-code-from-idl.md) - 了解更多代码生成选项
- [服务配置](./configure-service.md) - 配置客户端和服务端
- [启动配置](./startup-configuration.md) - Server 启动配置详解

## 相关文档

- [安装和配置](./install-and-setup.md)
- [创建第一个服务](./create-first-service.md)
- [Kitex 框架概览](./what-is-kitex.md)
