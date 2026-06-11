# Rush.js 命令参考手册

## 核心命令概览

### 依赖管理命令
- `rush install` - 安装依赖
- `rush update` - 更新依赖和配置
- `rush add` - 添加依赖
- `rush remove` - 删除依赖

### 构建和测试命令
- `rush build` - 构建项目
- `rush rebuild` - 强制重新构建
- `rushx <script>` - 运行项目脚本

### 项目管理命令
- `rush list` - 列出项目
- `rush scan` - 扫描项目
- `rush check` - 检查依赖

### 工具命令
- `rush purge` - 清理缓存
- `rush setup` - 环境设置
- `rush tab-complete` - 自动补全设置

## 详细命令说明

### 依赖管理

#### rush install
安装所有依赖，不修改任何文件。

```bash
# 基本用法
rush install

# 指定项目
rush install --to my-app

# 排除项目
rush install --to-except my-app

# 完整安装
rush install --full
```

**参数说明：**
- `--to <project>` - 安装指定项目及其依赖
- `--to-except <project>` - 安装指定项目的依赖，不包括自身
- `--from <project>` - 安装指定项目的下游项目
- `--only <project>` - 只安装指定项目
- `--full` - 完整安装，包括配置更新

#### rush update
更新依赖和配置文件。

```bash
# 基本用法
rush update

# 更新特定项目
rush update --to my-app

# 完整更新
rush update --full

# 更新到特定版本
rush update --to my-app --to tiktok_web_monorepo
```

**参数说明：**
- `--to <project>` - 更新指定项目
- `--full` - 完整更新，包括配置
- `--recheck` - 重新检查依赖

#### rush add
添加新依赖。

```bash
# 添加生产依赖
rush add --package lodash

# 添加开发依赖
rush add --package @types/lodash --dev

# 添加可选依赖
rush add --package lodash --optional

# 指定版本
rush add --package lodash@4.17.21

# 添加到特定项目
cd my-app
rush add --package lodash
```

**参数说明：**
- `--package <name>` - 包名
- `--dev` - 开发依赖
- `--optional` - 可选依赖
- `--version <version>` - 指定版本

#### rush remove
删除依赖。

```bash
# 删除依赖
rush remove --package lodash

# 删除开发依赖
rush remove --package @types/lodash --dev
```

**参数说明：**
- `--package <name>` - 包名
- `--dev` - 开发依赖

### 构建和测试

#### rush build
构建项目。

```bash
# 构建所有项目
rush build

# 构建特定项目及其依赖
rush build --to my-app

# 构建特定项目的依赖
rush build --to-except my-app

# 构建下游项目
rush build --from my-lib

# 并行构建
rush build --parallelism 4

# 增量构建
rush build --incremental

# 强制重新构建
rush build --force
```

**参数说明：**
- `--to <project>` - 构建指定项目及其依赖
- `--to-except <project>` - 构建指定项目的依赖
- `--from <project>` - 构建指定项目的下游
- `--only <project>` - 只构建指定项目
- `--parallelism <number>` - 并行度
- `--incremental` - 增量构建
- `--force` - 强制重新构建
- `--verbose` - 详细输出

#### rush rebuild
强制重新构建所有项目。

```bash
# 重新构建所有项目
rush rebuild

# 重新构建特定项目
rush rebuild --to my-app
```

#### rushx
在项目目录中运行脚本。

```bash
# 在项目目录中运行脚本
cd my-app
rushx build
rushx test
rushx start

# 从根目录运行项目脚本
rushx build my-app
rushx test my-app
```

### 项目管理

#### rush list
列出项目信息。

```bash
# 列出所有项目
rush list

# 列出特定项目
rush list --to my-app

# JSON 格式输出
rush list --json

# 详细输出
rush list --verbose
```

**参数说明：**
- `--to <project>` - 指定项目
- `--json` - JSON 格式输出
- `--verbose` - 详细输出

#### rush scan
扫描项目依赖。

```bash
# 扫描所有项目
rush scan

# 扫描特定项目
rush scan --to my-app

# JSON 格式输出
rush scan --json

# 检查幻影依赖
rush scan --phantom-deps
```

**参数说明：**
- `--to <project>` - 指定项目
- `--json` - JSON 格式输出
- `--phantom-deps` - 检查幻影依赖

#### rush check
检查依赖冲突。

```bash
# 检查所有项目
rush check

# 检查特定项目
rush check --to my-app

# 详细输出
rush check --verbose
```

### 工具命令

#### rush purge
清理缓存和临时文件。

```bash
# 清理缓存
rush purge

# 强制清理
rush purge --unsafe

# 清理特定项目
rush purge --to my-app
```

**参数说明：**
- `--unsafe` - 强制清理
- `--to <project>` - 指定项目

#### rush setup
设置开发环境。

```bash
# 设置环境
rush setup

# 检查环境
rush setup --check
```

#### rush tab-complete
设置命令自动补全。

```bash
# 设置自动补全
rush tab-complete

# 检查补全状态
rush tab-complete --check
```

### 子空间命令

#### rush init-subspace
创建新子空间。

```bash
# 创建子空间
rush init-subspace --name my-subspace

# 指定路径
rush init-subspace --name my-subspace --path subspaces/my-subspace
```

#### rush migrate-subspace
迁移项目到子空间。

```bash
# 迁移项目
rush migrate-subspace --target-subspace my-subspace --projects my-app

# 生成报告
rush migrate-subspace --report
```

### SCM 构建命令

#### rush scm-build
SCM 环境构建。

```bash
# SCM 构建
rush scm-build

# 指定项目
rush scm-build --to my-app
```

### 部署命令

#### rush deploy
部署项目。

```bash
# 部署项目
rush deploy --project my-app --target-folder output

# 使用特定配置
rush deploy --project my-app --target-folder output -s gulux
```

**参数说明：**
- `--project <name>` - 项目名
- `--target-folder <path>` - 目标文件夹
- `-s <config>` - 配置名称

## 项目选择器详解

### --to 选择器
构建指定项目及其所有依赖。

```bash
# 构建 my-app 及其依赖
rush build --to my-app

# 安装 my-app 及其依赖
rush install --to my-app
```

**使用场景：**
- 开发特定项目时
- 需要构建项目及其依赖时

### --to-except 选择器
构建指定项目的依赖，但不包括自身。

```bash
# 构建 my-app 的依赖，不包括 my-app
rush build --to-except my-app

# 安装 my-app 的依赖
rush install --to-except my-app
```

**使用场景：**
- 启动开发服务器前
- 构建依赖但不构建自身时

### --from 选择器
构建指定项目的下游项目。

```bash
# 构建 my-lib 的下游项目
rush build --from my-lib

# 安装 my-lib 的下游项目
rush install --from my-lib
```

**使用场景：**
- 修改库后需要构建使用该库的项目
- 检查下游项目是否受影响

### --only 选择器
只操作指定的项目。

```bash
# 只构建 my-app
rush build --only my-app

# 只安装 my-app
rush install --only my-app
```

**使用场景：**
- 只操作特定项目时
- 避免影响其他项目时

## 常用命令组合

### 开发环境设置
```bash
# 1. 克隆仓库
git clone <repository-url>
cd monorepo

# 2. 安装依赖
rush install --to tiktok_web_monorepo

# 3. 构建依赖
rush build --to-except tiktok_web_monorepo

# 4. 启动开发服务器
cd my-app
rushx start
```

### 添加新依赖
```bash
# 1. 进入项目目录
cd my-app

# 2. 添加依赖
rush add --package lodash

# 3. 更新依赖
rush update --to my-app

# 4. 构建项目
rush build --to my-app
```

### 修改共享库
```bash
# 1. 修改库代码
# ... 编辑 lib/my-lib 代码 ...

# 2. 构建库
rush build --to my-lib

# 3. 构建使用该库的项目
rush build --from my-lib
```

### 清理和重建
```bash
# 1. 清理缓存
rush purge --unsafe

# 2. 重新安装依赖
rush install

# 3. 重新构建
rush build
```

## 环境变量

### 常用环境变量
```bash
# 设置日志级别
export RUSH_LOG_LEVEL=verbose

# 设置并行度
export RUSH_PARALLELISM=4

# 设置内存限制
export NODE_OPTIONS="--max-old-space-size=4096"

# 设置构建缓存
export RUSH_BUILD_CACHE_ENABLED=true
```

### 开发环境变量
```bash
# 开发模式
export NODE_ENV=development

# 调试模式
export DEBUG=rush:*

# 详细输出
export RUSH_VERBOSE=true
```

## 故障排除

### 常见错误

#### 1. 幻影依赖错误
```bash
# 错误信息
Error: Phantom dependency detected

# 解决方案
rush scan --phantom-deps
rush add --package missing-package --to my-app
```

#### 2. 构建失败
```bash
# 错误信息
Error: Build failed

# 解决方案
rush build --verbose
rush purge --unsafe
rush install
rush build
```

#### 3. 依赖冲突
```bash
# 错误信息
Error: Dependency conflict

# 解决方案
rush check
rush update --full
```

#### 4. 锁文件冲突
```bash
# 错误信息
Error: Lockfile conflict

# 解决方案
git checkout --ours common/temp/pnpm-lock.yaml
rush update --to my-app
```

### 调试技巧

#### 启用详细日志
```bash
# 设置详细日志
export RUSH_LOG_LEVEL=verbose

# 运行命令
rush build --verbose
```

#### 分析依赖图
```bash
# 生成依赖图
rush list --json > dependencies.json

# 查看项目依赖
rush list --to my-app
```

#### 检查构建缓存
```bash
# 清理构建缓存
rush purge --unsafe

# 检查缓存状态
rush build --incremental
```

## 最佳实践

### 1. 命令使用原则
- 优先使用 `rush update` 而不是 `rush install`
- 使用项目选择器精确控制操作范围
- 定期运行 `rush check` 检查依赖冲突

### 2. 性能优化
- 使用 `--parallelism` 控制并行度
- 启用增量构建 `--incremental`
- 合理使用构建缓存

### 3. 错误处理
- 遇到错误时先查看详细日志
- 使用 `rush scan` 检查幻影依赖
- 定期清理缓存避免累积问题

### 4. 团队协作
- 统一使用相同的 Rush 版本
- 遵循项目选择器使用规范
- 及时同步依赖更新
