# Kitex 环境安装

## 前置要求

### Go 版本

- Go 1.16 或更高版本
- 推荐使用 Go 1.19+

验证 Go 版本:
```bash
go version
```

### 环境变量配置

确保以下环境变量正确设置:

```bash
# 查看 GOPATH
go env GOPATH

# 查看 GOBIN
go env GOBIN

# 查看 Go Module 代理
go env GOPROXY
```

## 安装 Kitex 框架

### 添加依赖

在项目中使用 Kitex:

```bash
go get github.com/cloudwego/kitex@latest
```

对于字节内部项目:

```bash
go get code.byted.org/kite/kitex@latest
```

### 初始化 Go Module

如果是新项目:

```bash
mkdir myproject
cd myproject
go mod init myproject
```

## 安装 KiteX Tool (代码生成工具)

KiteX Tool 用于根据 IDL 生成代码。

### 使用 go install

```bash
go install code.byted.org/kite/kitex/tool/cmd/kitex@latest
```

### 验证安装

```bash
kitex -version
# 输出: v1.x.x
```

**注意**: 版本号必须是 `v1.x.x` 格式(公司内部版本)。

## 安装 IDL 编译器

### Thriftgo (Thrift IDL)

如果使用 Thrift IDL:

```bash
go install github.com/cloudwego/thriftgo@latest
```

验证:
```bash
thriftgo --version
```

### Protoc (Protobuf IDL)

如果使用 Protobuf IDL:

#### macOS

```bash
brew install protobuf@3
```

#### Linux

下载预编译文件:

```bash
wget https://github.com/protocolbuffers/protobuf/releases/download/v3.13.0/protoc-3.13.0-linux-x86_64.zip
unzip protoc-3.13.0-linux-x86_64.zip
sudo mv bin/protoc /usr/local/bin/
```

验证:
```bash
protoc --version
# 输出: libprotoc 3.13.0
```

## 配置 Git (字节内部)

### SSH 配置

在 `~/.gitconfig` 中添加:

```ini
[url "git@code.byted.org:"]
    insteadOf = https://code.byted.org/
```

### Go Module 配置

跳过内部库的校验:

```bash
go env -w GOPRIVATE="*.byted.org,*.everphoto.cn,git.smartisan.com"
```

或:

```bash
go env -w GONOSUMDB="*.byted.org,*.everphoto.cn,git.smartisan.com"
```

## 环境验证

创建一个简单的测试项目验证环境:

```bash
# 创建测试目录
mkdir kitex-test
cd kitex-test

# 初始化 Go Module
go mod init kitex-test

# 安装 Kitex
go get github.com/cloudwego/kitex@latest

# 验证成功
go list -m github.com/cloudwego/kitex
```

## 常见问题

### kitex: command not found

**原因**: `$GOPATH/bin` 不在 `$PATH` 中

**解决方案**:

```bash
# 方式1: 添加到 PATH
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
source ~/.bashrc

# 方式2: 使用 GOBIN
export GOBIN=/usr/local/bin
go install code.byted.org/kite/kitex/tool/cmd/kitex@latest
```

### go get 超时

**解决方案**:

```bash
# 配置代理
go env -w GOPROXY=https://goproxy.cn,direct
```

### 权限被拒绝

**解决方案**:

```bash
# 赋予 GOPATH/bin 写权限
sudo chown -R $USER $(go env GOPATH)/bin
```

## 下一步

- 创建第一个 Kitex 服务
- 学习 Thrift IDL 语法
- 了解代码生成工具使用

## 参考

- [Go 官方文档](https://go.dev/doc/)
- [从 IDL 生成代码](./generate-code-from-idl.md)
