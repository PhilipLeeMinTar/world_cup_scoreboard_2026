# Rush.js Monorepo 完整技术指南

## 框架概述

Rush.js 是 Microsoft 开发的企业级 Monorepo 管理工具，专为大型代码仓库设计，提供高效的依赖管理、构建优化和开发体验。在 TikTok Web 生态中，Rush.js 作为 Federated Monorepo 的核心工具，支撑着跨地域、跨团队的协作开发。

### 核心特性
- **高效依赖管理**：基于 pnpm 的依赖解析，支持 workspace 依赖
- **增量构建**：智能检测变更，只构建必要的项目
- **并行处理**：支持多项目并行构建和测试
- **插件生态**：丰富的插件系统，支持自定义扩展
- **企业级特性**：支持多环境、多区域部署

### 技术栈
- **包管理器**：pnpm 7.33.5
- **构建工具**：Webpack、Rspack、EdenX
- **CI/CD**：Codebase Pipeline、SCM 构建
- **代码质量**：ESLint、Prettier、TypeScript
- **测试框架**：Jest、Testing Library

## 项目结构

### 标准 Monorepo 结构
```
monorepo/
├── common/                    # 公共配置
│   ├── config/               # Rush 配置
│   │   ├── rush/            # Rush 核心配置
│   │   ├── subspaces/       # 子空间配置
│   │   └── rush-plugins/    # 插件配置
│   ├── temp/                # 临时文件
│   └── autoinstallers/      # 自动安装器
├── subspaces/               # 子空间
│   ├── business-a/          # 业务 A 子空间
│   ├── business-b/          # 业务 B 子空间
│   └── shared/              # 共享子空间
├── packages/                # 包目录
│   ├── apps/               # 应用
│   ├── libs/               # 库
│   └── tools/              # 工具
├── rush.json               # Rush 主配置
├── pnpm-workspace.yaml     # pnpm 工作空间配置
└── .rush/                  # Rush 运行时文件
```

### 子空间 (Subspace) 结构
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

## 核心配置

### rush.json 配置
```json
{
  "rushVersion": "5.122.0",
  "pnpmVersion": "7.33.5",
  "nodeSupportedVersionRange": ">=18.0.0",
  "projects": [
    {
      "packageName": "my-app",
      "projectFolder": "apps/my-app",
      "shouldPublish": false
    },
    {
      "packageName": "my-lib",
      "projectFolder": "libs/my-lib",
      "shouldPublish": true
    }
  ],
  "eventHooks": {
    "preRushInstall": {
      "shellCommand": "echo 'Pre-install hook'"
    }
  }
}
```

### 项目配置 (rush-project.json)
```json
{
  "operationSettings": [
    {
      "operationName": "build",
      "commands": [
        {
          "name": "build",
          "command": "rushx build"
        }
      ]
    }
  ]
}
```

### 命令配置 (command-line.json)
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
    }
  ]
}
```

## 核心命令

### 依赖管理

#### 安装依赖
```bash
# 安装所有依赖
rush install

# 安装特定项目依赖
rush update --to my-app

# 安装特定项目及其依赖
rush update --to my-app --to-except my-app

# 完整更新（包括配置更新）
rush update --full
```

#### 添加/删除依赖
```bash
# 添加依赖
cd my-app
rush add --package lodash

# 删除依赖
cd my-app
rush remove --package lodash

# 添加开发依赖
rush add --package @types/lodash --dev
```

### 构建和测试

#### 构建项目
```bash
# 构建所有项目
rush build

# 构建特定项目及其依赖
rush build --to my-app

# 构建特定项目的依赖（不包括自身）
rush build --to-except my-app

# 构建下游项目
rush build --from my-lib

# 并行构建
rush build --parallelism 4
```

#### 运行脚本
```bash
# 在特定项目中运行脚本
rushx build
rushx test
rushx start

# 在根目录运行脚本
rushx lint
rushx format
```

### 项目选择器

#### --to 选择器
```bash
# 构建 my-app 及其所有依赖
rush build --to my-app
```

#### --to-except 选择器
```bash
# 构建 my-app 的依赖，但不包括 my-app 本身
rush build --to-except my-app
```

#### --from 选择器
```bash
# 构建 my-lib 的下游项目
rush build --from my-lib
```

#### --only 选择器
```bash
# 只构建指定的项目
rush build --only my-app
```

## 子空间 (Subspace) 管理

### 创建子空间
```bash
# 创建新子空间
rush init-subspace --name my-subspace

# 迁移项目到子空间
rush migrate-subspace --target-subspace my-subspace --projects my-app
```

### 子空间配置
```json
// subspaces.json
{
  "subspaces": [
    {
      "subspaceName": "my-subspace",
      "rushJsonFolder": "subspaces/my-subspace"
    }
  ]
}
```

### 子空间操作
```bash
# 在子空间中安装依赖
rush update --subspace my-subspace

# 在子空间中构建
rush build --subspace my-subspace

# 跨子空间依赖
rush build --to my-app --subspace my-subspace
```

## 插件系统

### 内置插件
```json
// rush-plugins.json
{
  "plugins": [
    {
      "packageName": "@rushstack/rush-scm-build-plugin",
      "pluginName": "rush-scm-build-plugin"
    }
  ]
}
```

### 自定义插件
```typescript
// my-plugin.ts
import { RushConfiguration, RushSession } from '@microsoft/rush-lib';

export class MyPlugin {
  public static pluginName: string = 'my-plugin';

  public apply(rushSession: RushSession): void {
    rushSession.hooks.build.tap('my-plugin', (build) => {
      console.log('Custom build hook');
    });
  }
}
```

## CI/CD 集成

### SCM 构建配置
```json
// rush-scm.json
{
  "my-app/scm": "my-app"
}
```

### 构建脚本
```bash
#!/bin/bash
# build.sh

# 设置环境变量
export BUILD_REPO_NAME="my-app/scm"

# 执行 Rush 构建
rush scm-build
```

### 部署配置
```json
// deploy.json
{
  "deploymentProjectNames": [
    "my-app",
    "my-lib"
  ],
  "dependencySettings": [
    {
      "dependencyName": "lodash",
      "dependencyVersionRange": "^4.17.0",
      "patternsToExclude": [
        "node_modules/**"
      ]
    }
  ]
}
```

## 开发工作流

### 日常开发流程
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

### 代码提交流程
```bash
# 1. 创建分支
git checkout -b feature/my-feature

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交代码
git add .
git commit -m "feat: add new feature"

# 4. 推送分支
git push origin feature/my-feature

# 5. 创建 MR
# 在 Codebase 平台创建 Merge Request

# 6. 等待 Code Review 和 CI 检查

# 7. 提交到 Merge Queue
# 点击 "Submit to Merge Queue"
```

## 性能优化

### 构建缓存
```json
// build-cache.json
{
  "buildCacheEnabled": true,
  "cacheProvider": "local-only",
  "localCacheFolder": ".rush/temp/build-cache"
}
```

### 增量构建
```bash
# 启用增量构建
rush build --incremental

# 清理构建缓存
rush purge --unsafe

# 强制重新构建
rush build --force
```

### 并行处理
```bash
# 设置并行度
rush build --parallelism 4

# 限制内存使用
rush build --parallelism 2 --max-old-space-size 4096
```

## 故障排除

### 常见问题

#### 1. 幻影依赖问题
```bash
# 扫描幻影依赖
rush scan --json

# 修复幻影依赖
rush add --package missing-package --to my-app
```

#### 2. 构建失败
```bash
# 查看详细日志
rush build --verbose

# 清理并重新构建
rush purge --unsafe
rush install
rush build
```

#### 3. 依赖冲突
```bash
# 检查依赖冲突
rush check

# 更新依赖版本
rush update --full
```

#### 4. 锁文件冲突
```bash
# 解决锁文件冲突
git checkout --ours common/temp/pnpm-lock.yaml
rush update --to my-app
```

### 调试技巧

#### 启用详细日志
```bash
# 设置日志级别
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

## 最佳实践

### 1. 项目结构设计
```
monorepo/
├── apps/                   # 应用程序
│   ├── web-app/           # Web 应用
│   ├── mobile-app/        # 移动应用
│   └── admin-app/         # 管理应用
├── libs/                   # 共享库
│   ├── ui-components/     # UI 组件库
│   ├── utils/             # 工具库
│   └── types/             # 类型定义
├── tools/                  # 工具和脚本
│   ├── build-tools/       # 构建工具
│   └── dev-tools/         # 开发工具
└── docs/                   # 文档
```

### 2. 依赖管理策略
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

### 3. 构建优化
```json
// rush-project.json
{
  "operationSettings": [
    {
      "operationName": "build",
      "commands": [
        {
          "name": "build",
          "command": "webpack --mode production",
          "incrementalBuildEnabled": true
        }
      ]
    }
  ]
}
```

### 4. 测试策略
```json
// rush-project.json
{
  "operationSettings": [
    {
      "operationName": "test",
      "commands": [
        {
          "name": "test",
          "command": "jest",
          "incrementalBuildEnabled": true
        }
      ]
    }
  ]
}
```

## API 参考

### Rush SDK
```typescript
import { RushConfiguration } from '@microsoft/rush-lib';

// 加载配置
const rushConfiguration = RushConfiguration.loadFromDefaultLocation({
  startingFolder: process.cwd()
});

// 获取项目信息
for (const project of rushConfiguration.projects) {
  console.log(project.packageName);
  console.log(project.projectRelativeFolder);
}

// 修改 package.json
const project = rushConfiguration.findProjectByShorthandName('my-app');
project.packageJsonEditor.addOrUpdateDependency('lodash', '4.17.21', 'dependencies');
project.packageJsonEditor.saveIfModified();
```

### 插件开发
```typescript
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

## 相关资源

### 官方文档
- [Rush.js 官方文档](https://rushjs.io/)
- [Rush.js API 参考](https://rushjs.io/zh-cn/pages/extensibility/api/)
- [Rush.js 最佳实践](https://rushjs.io/pages/maintainer/best_practices/)

### TikTok Web 生态
- [TTFE Monorepo 操作指南](https://bytedance.larkoffice.com/wiki/TTFE-Monorepo-User-Manual)
- [Federated Repo 迁移指南](https://bytedance.larkoffice.com/wiki/Federated-Repo-Migration)
- [Subspace 使用指南](https://bytedance.larkoffice.com/wiki/Subspace-Usage)

### 工具和插件
- [Rush 插件列表](https://rushjs.io/pages/maintainer/using_rush_plugins/)
- [构建缓存插件](https://rushjs.io/pages/advanced/build_cache/)
- [SCM 构建插件](https://rushjs.io/pages/maintainer/deploying/)

## 版本信息

- **Rush 版本**：5.122.0
- **pnpm 版本**：7.33.5
- **Node.js 版本**：>=18.0.0
- **TypeScript 版本**：4.9.5

## 支持渠道

- **Monorepo Oncall 群**：TTFE Monorepo Oncall Group
- **Code Review 群**：TTFE Monorepo Code Review
- **技术文档**：TikTok Web Arch 文档中心
