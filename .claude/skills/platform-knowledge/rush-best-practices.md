# Rush.js 最佳实践指南

## 项目结构设计

### 1. 目录结构最佳实践

#### 标准 Monorepo 结构
```
monorepo/
├── common/                    # 公共配置
│   ├── config/               # Rush 配置
│   │   ├── rush/            # 核心配置
│   │   ├── subspaces/       # 子空间配置
│   │   └── rush-plugins/    # 插件配置
│   ├── temp/                # 临时文件
│   └── autoinstallers/      # 自动安装器
├── subspaces/               # 子空间
│   ├── business-a/          # 业务 A
│   ├── business-b/          # 业务 B
│   └── shared/              # 共享代码
├── packages/                # 包目录
│   ├── apps/               # 应用程序
│   │   ├── web-app/        # Web 应用
│   │   ├── mobile-app/     # 移动应用
│   │   └── admin-app/      # 管理应用
│   ├── libs/               # 共享库
│   │   ├── ui-components/  # UI 组件
│   │   ├── utils/          # 工具库
│   │   └── types/          # 类型定义
│   └── tools/              # 工具和脚本
│       ├── build-tools/    # 构建工具
│       └── dev-tools/      # 开发工具
├── docs/                   # 文档
├── rush.json              # Rush 主配置
├── pnpm-workspace.yaml    # pnpm 工作空间
└── .rush/                 # Rush 运行时
```

#### 子空间结构设计
```
subspace/
├── common/                  # 子空间公共配置
│   ├── config/             # 子空间配置
│   └── temp/               # 子空间临时文件
├── projects/               # 子空间项目
│   ├── app1/              # 应用 1
│   ├── app2/              # 应用 2
│   └── lib1/              # 库 1
├── rush.json              # 子空间配置
└── pnpm-lock.yaml         # 子空间锁文件
```

### 2. 项目命名规范

#### 包命名规范
```json
{
  "name": "@tiktok/web-app",           // 业务应用
  "name": "@tiktok/ui-components",    // UI 组件库
  "name": "@tiktok/utils",            // 工具库
  "name": "@tiktok/types",            // 类型定义
  "name": "@tiktok/build-tools"       // 构建工具
}
```

#### 目录命名规范
```
packages/
├── apps/                   # 应用程序
│   ├── web-app/          # Web 应用
│   ├── mobile-app/       # 移动应用
│   └── admin-app/        # 管理应用
├── libs/                  # 共享库
│   ├── ui-components/    # UI 组件
│   ├── utils/           # 工具库
│   └── types/           # 类型定义
└── tools/                # 工具和脚本
    ├── build-tools/     # 构建工具
    └── dev-tools/       # 开发工具
```

## 配置管理最佳实践

### 1. rush.json 配置

#### 基础配置
```json
{
  "rushVersion": "5.122.0",
  "pnpmVersion": "7.33.5",
  "nodeSupportedVersionRange": ">=18.0.0",
  "ensureConsistentVersions": true,
  "projects": [
    {
      "packageName": "@tiktok/web-app",
      "projectFolder": "packages/apps/web-app",
      "shouldPublish": false
    },
    {
      "packageName": "@tiktok/ui-components",
      "projectFolder": "packages/libs/ui-components",
      "shouldPublish": true
    }
  ]
}
```

#### 高级配置
```json
{
  "rushVersion": "5.122.0",
  "pnpmVersion": "7.33.5",
  "nodeSupportedVersionRange": ">=18.0.0",
  "ensureConsistentVersions": true,
  "eventHooks": {
    "preRushInstall": {
      "shellCommand": "echo 'Pre-install hook'"
    },
    "postRushInstall": {
      "shellCommand": "echo 'Post-install hook'"
    }
  },
  "telemetry": {
    "enabled": true
  }
}
```

### 2. 项目配置 (rush-project.json)

#### 构建配置
```json
{
  "operationSettings": [
    {
      "operationName": "build",
      "commands": [
        {
          "name": "build",
          "command": "rushx build",
          "incrementalBuildEnabled": true
        }
      ]
    }
  ]
}
```

#### 测试配置
```json
{
  "operationSettings": [
    {
      "operationName": "test",
      "commands": [
        {
          "name": "test",
          "command": "rushx test",
          "incrementalBuildEnabled": true
        }
      ]
    }
  ]
}
```

### 3. 命令配置 (command-line.json)

#### 自定义命令
```json
{
  "commands": [
    {
      "name": "build",
      "commandKind": "bulk",
      "summary": "Build all projects",
      "description": "Build all projects in the monorepo",
      "safeForSimultaneousRushProcesses": true,
      "incrementalBuildEnabled": true
    },
    {
      "name": "test",
      "commandKind": "bulk",
      "summary": "Test all projects",
      "description": "Run tests for all projects",
      "safeForSimultaneousRushProcesses": true,
      "incrementalBuildEnabled": true
    }
  ]
}
```

## 依赖管理最佳实践

### 1. 依赖版本管理

#### 版本策略
```json
// package.json
{
  "dependencies": {
    "react": "18.2.0",           // 精确版本
    "lodash": "^4.17.21"         // 语义化版本
  },
  "devDependencies": {
    "@types/react": "18.2.0",
    "eslint": "^8.0.0"
  }
}
```

#### 公共依赖管理
```json
// common-versions.json
{
  "preferredVersions": {
    "react": "18.2.0",
    "typescript": "4.9.5"
  },
  "allowedAlternativeVersions": {
    "react": ["17.0.0", "18.2.0"]
  }
}
```

### 2. 依赖添加最佳实践

#### 添加生产依赖
```bash
# 进入项目目录
cd packages/apps/web-app

# 添加依赖
rush add --package lodash
rush add --package react
rush add --package @types/lodash --dev
```

#### 添加共享库依赖
```bash
# 添加内部库依赖
rush add --package @tiktok/ui-components
rush add --package @tiktok/utils
```

### 3. 幻影依赖处理

#### 扫描幻影依赖
```bash
# 扫描所有项目
rush scan --phantom-deps

# 扫描特定项目
rush scan --to my-app --phantom-deps
```

#### 修复幻影依赖
```bash
# 添加缺失的依赖
rush add --package missing-package --to my-app

# 检查依赖图
rush list --to my-app
```

## 构建优化最佳实践

### 1. 增量构建配置

#### 启用增量构建
```json
// rush-project.json
{
  "operationSettings": [
    {
      "operationName": "build",
      "commands": [
        {
          "name": "build",
          "command": "rushx build",
          "incrementalBuildEnabled": true
        }
      ]
    }
  ]
}
```

#### 构建缓存配置
```json
// build-cache.json
{
  "buildCacheEnabled": true,
  "cacheProvider": "local-only",
  "localCacheFolder": ".rush/temp/build-cache"
}
```

### 2. 并行构建优化

#### 设置并行度
```bash
# 设置并行度
rush build --parallelism 4

# 根据 CPU 核心数设置
rush build --parallelism $(nproc)
```

#### 内存优化
```bash
# 设置内存限制
export NODE_OPTIONS="--max-old-space-size=4096"
rush build --parallelism 2
```

### 3. 构建脚本优化

#### 优化构建脚本
```json
// package.json
{
  "scripts": {
    "build": "webpack --mode production",
    "build:dev": "webpack --mode development",
    "build:watch": "webpack --mode development --watch"
  }
}
```

#### 使用构建工具
```json
// package.json
{
  "scripts": {
    "build": "edenx build",
    "build:watch": "edenx build --watch",
    "build:analyze": "edenx build --analyze"
  }
}
```

## 开发工作流最佳实践

### 1. 日常开发流程

#### 标准开发流程
```bash
# 1. 同步代码
git fetch origin master
git rebase origin/master

# 2. 安装依赖
rush update --to my-app

# 3. 构建依赖
rush build --to-except my-app

# 4. 启动开发服务器
cd my-app
rushx start

# 5. 运行测试
rushx test

# 6. 构建项目
rushx build
```

#### 快速开发流程
```bash
# 一键设置开发环境
rush update --to my-app && rush build --to-except my-app

# 启动开发服务器
cd my-app && rushx start
```

### 2. 代码提交流程

#### 标准提交流程
```bash
# 1. 创建分支
git checkout -b feature/my-feature

# 2. 开发功能
# ... 编写代码 ...

# 3. 运行检查
rush check
rush build --to my-app
rushx test

# 4. 提交代码
git add .
git commit -m "feat: add new feature"

# 5. 推送分支
git push origin feature/my-feature

# 6. 创建 MR
# 在 Codebase 平台创建 Merge Request
```

#### 代码质量检查
```bash
# 运行所有检查
rush check
rush build --to my-app
rushx lint
rushx test

# 格式化代码
rushx format
```

### 3. 团队协作最佳实践

#### 分支管理策略
```bash
# 主分支
master          # 主分支
develop         # 开发分支

# 功能分支
feature/xxx     # 功能分支
bugfix/xxx      # 修复分支
hotfix/xxx      # 热修复分支
```

#### 代码审查流程
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交代码
git add .
git commit -m "feat: add new feature"

# 4. 推送分支
git push origin feature/new-feature

# 5. 创建 MR
# 在 Codebase 平台创建 Merge Request

# 6. 等待 Code Review
# 等待 Reviewer 审核

# 7. 提交到 Merge Queue
# 点击 "Submit to Merge Queue"
```

## 性能优化最佳实践

### 1. 构建性能优化

#### 并行构建
```bash
# 设置合适的并行度
rush build --parallelism 4

# 根据机器配置调整
rush build --parallelism $(nproc)
```

#### 增量构建
```bash
# 启用增量构建
rush build --incremental

# 强制重新构建
rush build --force
```

#### 构建缓存
```json
// build-cache.json
{
  "buildCacheEnabled": true,
  "cacheProvider": "local-only",
  "localCacheFolder": ".rush/temp/build-cache"
}
```

### 2. 依赖管理优化

#### 依赖分析
```bash
# 分析依赖图
rush list --json > dependencies.json

# 检查依赖冲突
rush check

# 扫描幻影依赖
rush scan --phantom-deps
```

#### 依赖优化
```bash
# 清理未使用的依赖
rush remove --package unused-package

# 更新依赖版本
rush update --full
```

### 3. 内存优化

#### 设置内存限制
```bash
# 设置 Node.js 内存限制
export NODE_OPTIONS="--max-old-space-size=4096"

# 运行构建
rush build --parallelism 2
```

#### 清理缓存
```bash
# 定期清理缓存
rush purge --unsafe

# 清理特定项目
rush purge --to my-app
```

## 子空间管理最佳实践

### 1. 子空间设计原则

#### 子空间划分策略
```
monorepo/
├── subspaces/
│   ├── business-a/          # 业务 A 子空间
│   │   ├── apps/           # 业务 A 应用
│   │   └── libs/           # 业务 A 库
│   ├── business-b/          # 业务 B 子空间
│   │   ├── apps/           # 业务 B 应用
│   │   └── libs/           # 业务 B 库
│   └── shared/              # 共享子空间
│       ├── ui-components/   # 共享 UI 组件
│       └── utils/          # 共享工具
```

#### 子空间配置
```json
// subspaces.json
{
  "subspaces": [
    {
      "subspaceName": "business-a",
      "rushJsonFolder": "subspaces/business-a"
    },
    {
      "subspaceName": "business-b",
      "rushJsonFolder": "subspaces/business-b"
    }
  ]
}
```

### 2. 子空间操作最佳实践

#### 创建子空间
```bash
# 创建新子空间
rush init-subspace --name business-a

# 配置子空间
cd subspaces/business-a
# 编辑 rush.json 配置
```

#### 迁移项目到子空间
```bash
# 迁移项目
rush migrate-subspace --target-subspace business-a --projects my-app

# 生成迁移报告
rush migrate-subspace --report
```

#### 子空间操作
```bash
# 在子空间中安装依赖
rush update --subspace business-a

# 在子空间中构建
rush build --subspace business-a

# 跨子空间依赖
rush build --to my-app --subspace business-a
```

## 插件开发最佳实践

### 1. 插件开发规范

#### 插件结构
```typescript
// my-plugin.ts
import { RushSession, RushConfiguration } from '@microsoft/rush-lib';

export class MyPlugin {
  public static pluginName: string = 'my-plugin';

  public apply(rushSession: RushSession): void {
    // 构建前钩子
    rushSession.hooks.build.tap('my-plugin', (build) => {
      console.log('Before build');
    });

    // 构建后钩子
    rushSession.hooks.build.tapAsync('my-plugin', (build, callback) => {
      console.log('After build');
      callback();
    });
  }
}
```

#### 插件配置
```json
// rush-plugins.json
{
  "plugins": [
    {
      "packageName": "@tiktok/my-plugin",
      "pluginName": "my-plugin"
    }
  ]
}
```

### 2. 插件使用最佳实践

#### 内置插件
```json
// rush-plugins.json
{
  "plugins": [
    {
      "packageName": "@rushstack/rush-scm-build-plugin",
      "pluginName": "rush-scm-build-plugin"
    },
    {
      "packageName": "@rushstack/rush-deploy-plugin",
      "pluginName": "rush-deploy-plugin"
    }
  ]
}
```

#### 自定义插件
```typescript
// custom-plugin.ts
import { RushSession } from '@microsoft/rush-lib';

export class CustomPlugin {
  public static pluginName: string = 'custom-plugin';

  public apply(rushSession: RushSession): void {
    // 自定义逻辑
    rushSession.hooks.build.tap('custom-plugin', (build) => {
      // 执行自定义构建逻辑
    });
  }
}
```

## 故障排除最佳实践

### 1. 常见问题诊断

#### 构建失败诊断
```bash
# 查看详细日志
rush build --verbose

# 检查依赖
rush check

# 扫描问题
rush scan --phantom-deps
```

#### 依赖问题诊断
```bash
# 检查依赖冲突
rush check

# 扫描幻影依赖
rush scan --phantom-deps

# 分析依赖图
rush list --json > dependencies.json
```

### 2. 问题解决流程

#### 标准解决流程
```bash
# 1. 查看错误日志
rush build --verbose

# 2. 检查依赖
rush check

# 3. 清理缓存
rush purge --unsafe

# 4. 重新安装
rush install

# 5. 重新构建
rush build
```

#### 高级解决流程
```bash
# 1. 分析依赖图
rush list --json > dependencies.json

# 2. 检查幻影依赖
rush scan --phantom-deps

# 3. 修复依赖问题
rush add --package missing-package --to my-app

# 4. 更新依赖
rush update --full

# 5. 重新构建
rush build
```

### 3. 预防措施

#### 定期维护
```bash
# 定期检查依赖
rush check

# 定期扫描问题
rush scan --phantom-deps

# 定期清理缓存
rush purge --unsafe
```

#### 监控和告警
```bash
# 设置监控
export RUSH_LOG_LEVEL=verbose

# 运行检查
rush check --verbose
```

## 团队协作最佳实践

### 1. 开发规范

#### 代码规范
```json
// .eslintrc.js
{
  "extends": ["@tiktok/eslint-config"],
  "rules": {
    "no-console": "warn",
    "no-debugger": "error"
  }
}
```

#### 提交规范
```bash
# 提交信息格式
feat: add new feature
fix: fix bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: update dependencies
```

### 2. 协作流程

#### 分支管理
```bash
# 主分支
master          # 主分支
develop         # 开发分支

# 功能分支
feature/xxx     # 功能分支
bugfix/xxx      # 修复分支
hotfix/xxx      # 热修复分支
```

#### 代码审查
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交代码
git add .
git commit -m "feat: add new feature"

# 4. 推送分支
git push origin feature/new-feature

# 5. 创建 MR
# 在 Codebase 平台创建 Merge Request

# 6. 等待 Code Review
# 等待 Reviewer 审核

# 7. 提交到 Merge Queue
# 点击 "Submit to Merge Queue"
```

### 3. 知识分享

#### 文档维护
```bash
# 更新文档
git add docs/
git commit -m "docs: update documentation"

# 推送文档
git push origin feature/docs-update
```

#### 经验分享
```bash
# 分享最佳实践
# 在团队群中分享经验

# 更新文档
# 更新团队文档
```

## 监控和运维最佳实践

### 1. 性能监控

#### 构建性能监控
```bash
# 监控构建时间
time rush build

# 监控内存使用
rush build --parallelism 2
```

#### 依赖监控
```bash
# 监控依赖大小
rush list --json > dependencies.json

# 监控依赖冲突
rush check
```

### 2. 运维最佳实践

#### 定期维护
```bash
# 定期清理缓存
rush purge --unsafe

# 定期更新依赖
rush update --full

# 定期检查问题
rush check
```

#### 监控告警
```bash
# 设置监控
export RUSH_LOG_LEVEL=verbose

# 运行检查
rush check --verbose
```

这些最佳实践涵盖了 Rush.js Monorepo 开发的各个方面，从项目结构到团队协作，为开发者提供了全面的指导。遵循这些实践可以确保代码质量、提高开发效率，并促进团队协作。
