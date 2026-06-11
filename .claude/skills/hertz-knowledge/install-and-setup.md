# Hertz 环境安装

## 前置要求

在开始使用 Hertz 之前,请确保满足以下条件:

### 操作系统

- macOS 系统
- Linux/*nix 系统
- Windows (通过 WSL)

### Go 环境

- **Golang 版本要求**: >= 1.15 (推荐 1.19+)
- 已按照规范安装配置好 Golang 开发环境
- 配置好 GOPATH 和 GO111MODULE

### 内网配置 (字节跳动员工)

1. **Go Module Proxy 配置**
   ```bash
   # 配置内网 go module proxy
   export GOPROXY=https://goproxy.byted.org,direct
   ```

2. **Git 配置**
   - 完成公司内网 git 相关配置
   - 配置 SSH Key 或 HTTPS 认证

### Protobuf 支持 (可选)

如果项目需要使用 Protobuf,需要安装:

#### 1. 安装 protoc (3.0+ 版本)

**macOS:**
```bash
# 官方镜像安装
wget https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-osx-x86_64.zip
unzip protoc-3.19.4-osx-x86_64.zip
cp bin/protoc /usr/local/bin/protoc

# 确保 include/google 放入 /usr/local/include 下
cp -r include/google /usr/local/include/google
```

**Linux:**
```bash
wget https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-linux-x86_64.zip
unzip protoc-3.19.4-linux-x86_64.zip
sudo cp bin/protoc /usr/local/bin/protoc
sudo cp -r include/google /usr/local/include/google
```

#### 2. 安装 protoc-gen-go

```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
```

验证安装:
```bash
protoc --version  # 应显示 libprotoc 3.x.x
```

## Hertztool 工具安装

### 推荐: 安装 Hertztool v3

Hertztool v3 是最新版本,解决了 v2 的多种历史问题,推荐使用。

```bash
# 方式 1: go get
GO111MODULE=on go get -v code.byted.org/middleware/hertztool/v3

# 方式 2: go install (推荐)
go install code.byted.org/middleware/hertztool/v3@latest
```

### 验证安装

```bash
hertztool -v
```

预期输出:
```
hertztool version v3.1.5
```

如果提示 "command not found",需要将 `$GOPATH/bin/` 添加到系统 PATH:

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PATH=$PATH:$GOPATH/bin

# 或者如果使用 go modules
export PATH=$PATH:$(go env GOPATH)/bin

# 使配置生效
source ~/.bashrc  # 或 source ~/.zshrc
```

## 常见问题

### 1. protoc 版本太低

**错误信息:**
```
invalid protoc version libprotoc 2.x, need protoc 3.x
```

**解决方案:**
卸载旧版本,按照上述步骤安装 protoc 3.x 版本。

### 2. protoc-gen-go 找不到

**错误信息:**
```
Protoc-gen-go: program not found or is not executable
```

**解决方案:**
```bash
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
# 确保 $GOPATH/bin 在 PATH 中
```

### 3. hertztool 安装失败

**可能原因:**
- 网络问题
- GOPROXY 配置不正确

**解决方案:**
```bash
# 检查 GOPROXY 配置
go env GOPROXY

# 如果在字节跳动内网
export GOPROXY=https://goproxy.byted.org,direct

# 重新安装
go install code.byted.org/middleware/hertztool/v3@latest
```

## 开发环境建议

### IDE 推荐

- **GoLand**: JetBrains 出品,功能强大
- **VSCode**: 轻量级,配合 Go 扩展使用
- **Vim/Neovim**: 配合 vim-go 插件

### 必备工具

```bash
# 安装 gofmt 代码格式化
go install golang.org/x/tools/cmd/gofmt@latest

# 安装 golint 代码检查
go install golang.org/x/lint/golint@latest

# 安装 goimports 自动 import 管理
go install golang.org/x/tools/cmd/goimports@latest
```

## 下一步

环境准备就绪后,可以开始:

1. 阅读《创建第一个 Hertz 项目》
2. 了解《Hertztool v3 使用手册》
3. 查看《Server API 示例》

## 参考链接

- [Go 官方安装指南](https://go.dev/doc/install)
- [Hertztool v3 使用手册](https://bytedance.larkoffice.com/wiki/wikcnXFjRCCtuGV7U44X0aUCuCf)
- [Protobuf 官方文档](https://developers.google.com/protocol-buffers)
