# KiteX Tool 代码生成工具使用指南

## 概述

KiteX Tool 是 Kitex 框架的代码生成工具，用于从 Thrift 或 Protobuf IDL 文件生成 Go 代码。生成的代码包括数据结构定义、序列化代码以及 Client/Server 框架代码。

## 安装

### 方式1：手动安装（推荐）

安装 kitex tool：

```bash
go install code.byted.org/kite/kitex/tool/cmd/kitex@latest

# 指定版本安装
go install code.byted.org/kite/kitex/tool/cmd/kitex@vx.x.x
```

验证安装：

```bash
kitex -version
# 输出应为 v1.x.x 开头的公司内部版本
```

**注意**：版本号必须是 `v1.x.x` 开头才是公司内部版本，否则生成的代码无法接入公司的服务治理。

### 依赖安装

**Thrift 场景**：

```bash
go install github.com/cloudwego/thriftgo@latest
```

**Protobuf 场景**：

需要安装 protoc，下载对应平台的预编译文件：
- Linux: [protoc-3.13.0-linux-x86_64.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.13.0/protoc-3.13.0-linux-x86_64.zip)
- macOS: [protoc-3.13.0-osx-x86_64.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.13.0/protoc-3.13.0-osx-x86_64.zip)

下载后解压，将 `protoc` 放到系统的 `$PATH` 目录下。

### 方式2：直接下载

```bash
# macOS
brew install wget
wget --header="X-Tos-Access: internal" "http://kitex.tos-cn-north.byted.org/self-update/kitex/kitex-darwin-amd64" -O $(go env GOPATH)/bin/kitex && chmod +x $(go env GOPATH)/bin/kitex

# Linux
wget --header="X-Tos-Access: internal" "http://kitex.tos-cn-north.byted.org/self-update/kitex/kitex-linux-amd64" -O $(go env GOPATH)/bin/kitex && chmod a+x $(go env GOPATH)/bin/kitex
```

## 生成代码

### 生成基本代码（Client 使用）

基本语法：`kitex [options] xxx.thrift` 或 `kitex [options] xxx.proto`

**示例 IDL 文件**：

```thrift
// example.thrift
namespace go test
include "base.thrift"

struct MyReq {
    1: required string input
    2: required base.BaseReq baseReq
}

service MyService {
    string Hello(1: required MyReq req)
}

// base.thrift
struct BaseReq {
    1: required string name
}
```

**生成命令**：

```bash
# 在 Go Path 下
kitex example.thrift

# 在 Go Module 项目中（推荐）
kitex -module myproject example.thrift
```

**生成的目录结构**：

```
kitex_gen/
├── base                        # base.thrift 的生成内容
│   ├── base.go                 # thriftgo 生成，包含数据结构定义
│   ├── k-base.go               # kitex 生成，包含序列化优化实现
│   └── k-consts.go             # 占位符文件
└── test                        # example.thrift 的生成内容（使用 go namespace）
    ├── example.go              # thriftgo 生成，包含数据结构定义
    ├── k-consts.go             # 占位符文件
    ├── k-example.go            # kitex 生成，包含序列化优化实现
    └── myservice               # 为 MyService 生成的代码
        ├── client.go           # 提供 NewClient API
        ├── invoker.go          # 提供 Server SDK 化的 API
        ├── myservice.go        # client.go 和 server.go 共用的定义
        └── server.go           # 提供 NewServer API
```

### 生成带脚手架的代码（Server 使用）

使用 `-service` 参数生成完整的服务端框架代码：

```bash
kitex -service mydemoservice -module myproject demo.thrift
```

**生成的目录结构**：

```
├── build.sh                    # 快速构建服务的脚本
├── handler.go                  # Server handler 脚手架
├── kitex_info.yaml             # 元信息，用于与 cwgo 工具集成
├── main.go                     # 快速启动 Server 的主函数
├── script/                     # 构建服务相关脚本
│   └── bootstrap.sh
└── kitex_gen/
    └── ...
```

在 `handler.go` 的接口中填充业务代码后，执行 `main.go` 即可启动 Kitex Server。

## 常用命令行参数

### 基础参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-version` | 查看工具版本 | `kitex -version` |
| `-module` | 指定 Go module 名称 | `kitex -module myproject xxx.thrift` |
| `-service` | 生成 Server 代码，指定服务名（建议使用 PSM） | `kitex -service p.s.m xxx.thrift` |
| `-I path` | 添加 IDL 搜索路径，支持多个 | `kitex -I ./idl -I ./common xxx.thrift` |
| `-gen-path` | 指定生成代码路径（默认 ./kitex_gen） | `kitex -gen-path ./gen xxx.thrift` |
| `-use path` | 使用外部 kitex_gen，配合 -service 使用 | `kitex -service p.s.m -use xxx/public/kitex_gen xxx.thrift` |

### Git 拉取 IDL

从 v1.10.2 版本起，`-I` 参数支持从 Git 仓库拉取 IDL：

```bash
# 拉取默认分支
kitex -I git@code.byted.org:my_namespace/my_repo.git xxx.thrift

# 拉取指定分支
kitex -I git@code.byted.org:my_namespace/my_repo.git@branch xxx.thrift
```

仓库会被拉取到 `~/.kitex/cache/` 目录下。

### Thrift 代码生成选项

通过 `-thrift` 参数传递给 Thriftgo：

| 参数 | 说明 |
|------|------|
| `-thrift ignore_initialisms` | 解决大小写问题（如 Id -> ID） |
| `-thrift compatible_names` | 解决名字多下划线问题 |
| `-thrift template=slim` | 只生成定义，不生成编解码代码（配合 frugal 使用） |
| `-thrift snake_style_json_tag` | 生成下划线分割的 json tag |
| `-thrift frugal_tag=false` | 不生成 frugal tag |
| `-thrift enum_as_int_32` | Enum 类型使用 int32 |
| `-thrift omitempty_for_optional=false` | optional 字段的 json tag 去掉 omitempty |
| `-thrift reserve_comments=true` | 保留 IDL 注释到生成的结构体 |
| `-thrift nil_safe` | 为 Get 方法添加判空代码避免 panic |
| `-thrift json_stringer` | 将 String() 方法输出转为 JSON 格式 |

**示例**：

```bash
kitex -thrift template=slim -service p.s.m idl/api.thrift
```

### 其他参数

| 参数 | 说明 |
|------|------|
| `-combine-service` | 将多个 service 合成为一个 CombineService |
| `-disable-self-update` | 禁用本次执行的自动更新 |

## 使用 Protobuf IDL 注意事项

1. Kitex 仅支持 proto3 语法
2. IDL 里的 `go_package` 是必需的

```protobuf
option go_package = "hello.world"; // 或 hello/world
```

3. 生成的 import path 会是 `${当前目录的 import path}/kitex_gen/hello/world`

4. 如果使用完整导入路径，必须匹配到当前模块的 kitex_gen：
   - ✅ `go_package="${当前模块}/kitex_gen/hello/world";`
   - ❌ `go_package="${当前模块}/hello/world";`
   - ❌ `go_package="other.domain/module/kitex_gen/hello/world";`

## 库依赖

kitex 生成的代码依赖：

- **Thrift IDL**: `github.com/apache/thrift v0.13.0`
- **Protobuf IDL**: `google.golang.org/protobuf v1.26.0`

**重要**：`github.com/apache/thrift` 的 v0.14.0 版本开始 API 不兼容，如果遇到 `not enough arguments in call to iprot.ReadStructBegin` 错误，执行：

```bash
go get github.com/apache/thrift@v0.13.0

# 或使用 replace 指令
go mod edit -replace github.com/apache/thrift=github.com/apache/thrift@v0.13.0
```

## 常见场景示例

### Include 公共库里的 base.thrift

假设 base.thrift 在 `code.byted.org/kitex/test` 仓库的 `common/base.thrift` 路径：

```thrift
// 本地 xxx.thrift
include "common/base.thrift"

struct XXRequest {
    1: required string str,
    255: optional base.Base Base,
}

service XXService {
    XXResponse xxMethod(1: XXRequest req)
}
```

生成命令：

```bash
kitex -I git@code.byted.org:kitex/test.git xxx.thrift
```

### 使用外部 kitex_gen

当已有公共的 kitex_gen 仓库时：

```bash
kitex -service p.s.m -use xxx/public/kitex_gen xxx.thrift
```

此时只生成 main.go、handler.go，不会生成 kitex_gen，且引用会指向指定的公共目录。

## 常见问题

### kitex: command not found

**原因**：安装目录未加入 `$PATH`

**解决方案**：

```bash
# 方案1：将 GOPATH/bin 加到 PATH
export PATH=$PATH:$(go env GOPATH)/bin

# 方案2：指定 GOBIN
GOBIN=/target/dir/ go install code.byted.org/kite/kitex/tool/cmd/kitex@latest
```

### 404 Not Found 或 no such host

**原因**：Go 尝试校验内部库的 checksum

**解决方案**：

```bash
go env -w GOPRIVATE="*.byted.org,*.everphoto.cn,git.smartisan.com"
# 或
go env -w GONOSUMDB="*.byted.org,*.everphoto.cn,git.smartisan.com"
```

### go install 时卡住

**解决方案**：在 `~/.gitconfig` 添加：

```
[url "git@code.byted.org:"]
    insteadOf = https://code.byted.org/
```

### 自动更新失败

**解决方案**：

```bash
# 方案1：安装最新版本避免自更新
go install code.byted.org/kite/kitex/tool/cmd/kitex@latest
go install github.com/cloudwego/thriftgo@latest

# 方案2：禁用自更新
kitex -disable-self-update -module xxx xxx.thrift
```

### IDL 报 undefined type 或 exit status 1

**原因**：include 的 IDL 存在重名

**解决方案**：检查并修改重名的 IDL 文件

### Apache Thrift 不兼容更新问题

如果遇到 `not enough arguments in call to iprot.ReadStructBegin` 等编译错误：

```bash
go get github.com/apache/thrift@v0.13.0
```

## 相关文档

- [安装和配置](./install-and-setup.md)
- [定义 Thrift IDL](./define-thrift-idl.md)
- [创建第一个服务](./create-first-service.md)
- [Kitex 官方文档](https://www.cloudwego.io/zh/docs/kitex/)
