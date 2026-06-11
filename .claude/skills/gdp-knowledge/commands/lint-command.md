# Lint 工具使用指南

## 概述

GDP 项目使用 Lint 工具进行代码质量检查,确保代码符合编码规范和最佳实践。

## 工具安装

### golangci-lint

**安装**:
```bash
# macOS
brew install golangci-lint

# Linux
curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin

# 验证安装
golangci-lint --version
```

### 其他工具

```bash
# go vet (Go 自带)
go vet ./...

# gofmt (Go 自带)
gofmt -l -w .

# goimports (推荐)
go install golang.org/x/tools/cmd/goimports@latest
```

## 使用方法

### 基础检查

```bash
# 运行所有检查
golangci-lint run

# 检查特定目录
golangci-lint run ./service/...

# 检查特定文件
golangci-lint run service/domain/user/create_user.go

# 查看所有可用的 linter
golangci-lint linters
```

### CI 集成

在 CI/CD 流水线中自动运行 Lint:

**.gitlab-ci.yml** 示例:
```yaml
lint:
  stage: test
  script:
    - golangci-lint run --timeout 5m
  only:
    - merge_requests
```

**Makefile** 示例:
```makefile
.PHONY: lint
lint:
	@echo "Running lint checks..."
	@golangci-lint run ./...
	@go vet ./...
	@gofmt -l -w .

.PHONY: lint-fix
lint-fix:
	@echo "Auto-fixing lint issues..."
	@golangci-lint run --fix ./...
```

## 配置文件

在项目根目录创建 `.golangci.yml`:

```yaml
run:
  timeout: 5m
  tests: true

linters:
  enable:
    - gofmt      # 格式化检查
    - goimports  # import 排序
    - govet      # Go vet 检查
    - errcheck   # 错误检查
    - staticcheck # 静态分析
    - unused     # 未使用代码
    - gosimple   # 简化建议
    - ineffassign # 无效赋值
    - misspell   # 拼写检查

  disable:
    - lll        # 行长度限制(可选)
    - gocyclo    # 复杂度检查(可选)

linters-settings:
  errcheck:
    check-blank: true  # 检查 _ = 赋值
  gofmt:
    simplify: true     # 简化代码
  govet:
    check-shadowing: true  # 检查变量遮蔽

issues:
  exclude-rules:
    # 排除测试文件的某些检查
    - path: _test\.go
      linters:
        - errcheck
```

## 常见问题修复

### 未使用的变量

```go
// 错误
func example() {
    unused := "value"  // unused: ineffassign
}

// 修复
func example() {
    _ = "value"  // 明确忽略
}
```

### 错误未检查

```go
// 错误
func example() {
    file.Close()  // errcheck: error return value not checked
}

// 修复
func example() {
    if err := file.Close(); err != nil {
        logs.Error(ctx, "Failed to close file", err)
    }
}
```

### Import 排序

```go
// 错误
import (
    "your_service/pkg/types"
    "context"
    "code.byted.org/gdp/af"
)

// 修复(标准库 → 第三方 → 本地包)
import (
    "context"

    "code.byted.org/gdp/af"

    "your_service/pkg/types"
)
```

### 代码格式化

```bash
# 自动格式化
gofmt -w .
goimports -w .

# 或使用 golangci-lint 自动修复
golangci-lint run --fix
```

## 最佳实践

1. **提交前检查**: 提交代码前运行 `make lint` 检查
2. **自动修复**: 使用 `golangci-lint run --fix` 自动修复简单问题
3. **CI 强制**: 在 CI 中强制运行 Lint,不通过则无法合并
4. **增量检查**: 只检查变更的文件,提高效率
5. **配置统一**: 团队使用统一的 `.golangci.yml` 配置

## IDE 集成

### VSCode

安装 `golang.go` 插件,在 `settings.json` 中配置:

```json
{
    "go.lintTool": "golangci-lint",
    "go.lintOnSave": "workspace",
    "editor.formatOnSave": true
}
```

### GoLand

Settings → Tools → File Watchers → 添加 golangci-lint

## 常用命令

```bash
# 快速检查
golangci-lint run --fast

# 显示所有问题
golangci-lint run --max-issues-per-linter 0 --max-same-issues 0

# 只运行特定 linter
golangci-lint run --disable-all --enable=errcheck

# 生成配置文件模板
golangci-lint config path

# 查看帮助
golangci-lint help
```

## 相关文档

- [arch-code-layers-guide.md](../architecture/arch-code-layers-guide.md) - 代码分层架构指南
- [workflow-local-development.md](../workflow/workflow-local-development.md) - 本地开发流程
