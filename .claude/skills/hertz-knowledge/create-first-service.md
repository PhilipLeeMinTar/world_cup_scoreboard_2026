# 创建第一个 Hertz 服务

## 前提条件

- 已安装 hertztool v3
- 已配置好 Go 开发环境

## 创建项目骨架

### 1. 创建项目目录

```bash
# 在任意路径下创建项目文件夹 (支持非 GOPATH)
mkdir -p $GOPATH/src/code.byted.org/namespace/repos
cd $GOPATH/src/code.byted.org/namespace/repos
```

### 2. 使用 hertztool 初始化项目

```bash
hertztool new --psm=p.s.m --mod=code.byted.org/namespace/projectName
```

**参数说明:**
- `--psm`: 服务的 PSM 信息 (线上记得替换真实 PSM)
- `--mod`: Go module 名称

### 3. 生成的目录结构

```
.
├── biz
│   ├── handler
│   │   └── ping.go          # 默认 handler
│   └── router
│       └── register.go      # 路由注册
├── build.sh                 # 构建脚本
├── conf
│   └── hertz.config.yaml    # Hertz 配置
├── go.mod
├── main.go                  # 入口文件
├── router.go                # 路由初始化
├── router_gen.go            # 生成的路由代码
└── script
    └── bootstrap.sh         # 启动脚本
```

## 编写业务代码

### 1. 修改 Handler

编辑 `biz/handler/ping.go`:

```go
package handler

import (
    "context"
    "code.byted.org/middleware/hertz/pkg/app"
    "code.byted.org/middleware/hertz/pkg/protocol/consts"
)

// Ping handler
func Ping(ctx context.Context, c *app.RequestContext) {
    c.JSON(consts.StatusOK, map[string]string{
        "message": "pong",
    })
}
```

### 2. 注册路由

编辑 `biz/router/register.go`:

```go
package router

import (
    "code.byted.org/middleware/hertz/byted"
    "code.byted.org/namespace/projectName/biz/handler"
)

func Register(h *byted.Engine) {
    // 注册路由
    h.GET("/ping", handler.Ping)

    // 路由组
    api := h.Group("/api/v1")
    {
        api.GET("/hello", handler.Hello)
        api.POST("/user", handler.CreateUser)
    }
}
```

### 3. 主函数

`main.go` 已由 hertztool 生成:

```go
package main

import (
    "code.byted.org/middleware/hertz/byted"
)

func main() {
    byted.Init() // 重要: 初始化内部组件

    h := byted.Default() // 创建 Hertz 实例 (带标准中间件)

    register(h) // 注册路由

    h.Spin() // 启动服务 (默认 8888 端口)
}
```

## 本地运行服务

### 1. 安装依赖

```bash
go mod tidy
```

### 2. 运行服务

```bash
go run main.go
```

或使用构建脚本:

```bash
sh build.sh
./output/bin/projectName
```

### 3. 测试服务

```bash
curl http://localhost:8888/ping
# 返回: {"message":"pong"}
```

## 使用 IDL 生成代码

### 1. 编写 Thrift IDL

创建 `idl/api.thrift`:

```thrift
namespace go api

struct User {
    1: required i64 id
    2: required string name
    3: optional string email
}

struct GetUserRequest {
    1: required i64 id (api.query="id")
}

struct GetUserResponse {
    1: required User user
}

service UserService {
    GetUserResponse GetUser(1: GetUserRequest req) (api.get="/api/user")
}
```

### 2. 生成代码

```bash
hertztool update -idl idl/api.thrift --mod=code.byted.org/namespace/projectName
```

这将生成:
- Model 定义
- Handler 框架代码
- 路由注册代码
- Binding 标签

### 3. 实现 Handler

在生成的 handler 中补充业务逻辑:

```go
func GetUser(ctx context.Context, c *app.RequestContext) {
    var req api.GetUserRequest
    err := c.BindAndValidate(&req)
    if err != nil {
        c.JSON(400, map[string]string{"error": err.Error()})
        return
    }

    // 业务逻辑
    user := &api.User{
        Id:    req.Id,
        Name:  "John Doe",
        Email: "john@example.com",
    }

    resp := &api.GetUserResponse{User: user}
    c.JSON(200, resp)
}
```

## 配置说明

### hertz.config.yaml

```yaml
Server:
  Address: :8888
  IdleTimeout: 60s
  ReadTimeout: 3s
  WriteTimeout: 3s
```

## 调试技巧

### 1. 查看日志

```bash
# 日志默认在 output/logs/
tail -f output/logs/app.log
```

### 2. 使用 IDE 调试

在 GoLand/VSCode 中设置断点,以 Debug 模式运行 main.go

### 3. 本地关闭 metrics

调试时可临时注释 `byted.Init()` 避免 metrics 报错

## 常见问题

### 1. 端口被占用

修改配置文件或使用环境变量:

```bash
export PORT=9999
go run main.go
```

### 2. 依赖下载失败

检查 GOPROXY 配置:

```bash
go env -w GOPROXY=https://goproxy.byted.org,direct
```

### 3. IDL 生成失败

检查 hertztool 版本和 IDL 语法

## 下一步

- 学习 Server API 详解
- 了解 Binding 使用
- 掌握中间件机制
- 学习 Hertz 1.0 新特性
