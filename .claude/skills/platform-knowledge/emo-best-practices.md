# EMO 最佳实践与进阶功能

> 本文档介绍 EMO 的最佳实践、常见问题解决方案和进阶功能

## 一、最佳实践

### 1. 避免幻影依赖 (Phantom Dependency)

**什么是幻影依赖?**

幻影依赖是指代码中使用了某个包,但这个包没有在 `package.json` 中声明,而是通过其他依赖间接安装的。这会导致:
- 代码在某些环境下无法运行
- 依赖升级时意外破坏代码
- 无法准确追踪依赖关系

**EMO 的解决方案:**

1. 使用 pnpm 的严格依赖管理
2. 开启 `externalDependencyCheck`

```json
{
  "config": {
    "workspaceCheck": {
      "externalDependencyCheck": {
        "usedButNotInstalled": true
      }
    }
  }
}
```

3. 手动检查并修复

```bash
emo check --checker externalDependencyCheck
```

### 2. 统一依赖版本

**为什么要统一?**
- 避免包分身问题
- 减少 bundle 大小
- 确保行为一致性

**方法一: 使用 dependencyVersionCheck**

```json
{
  "config": {
    "workspaceCheck": {
      "dependencyVersionCheck": {
        "autofix": true,
        "forceCheck": true,
        "options": {
          "autofixMode": "newerVersion"
        }
      }
    }
  }
}
```

**方法二: 使用 pnpm catalog**

```json
{
  "pnpmWorkspace": {
    "catalog": {
      "react": "18.2.0",
      "react-dom": "18.2.0"
    }
  }
}
```

在子项目中:
```json
{
  "dependencies": {
    "react": "catalog:default",
    "react-dom": "catalog:default"
  }
}
```

### 3. 基于源码开发

**优势:**
- 无需每次构建依赖包
- 修改立即生效
- 提高开发效率

**配置方法:**

在 `package.json` 中使用 `exports` 字段:

```json
{
  "name": "@myorg/shared",
  "main": "./dist/index.js",
  "exports": {
    ".": {
      "source": "./src/index.ts",
      "default": "./dist/index.js"
    }
  }
}
```

配置构建工具支持 `source` 字段(如 webpack):

```javascript
module.exports = {
  resolve: {
    mainFields: ['source', 'module', 'main']
  }
};
```

### 4. 锁定依赖版本

**使用 overrides (pnpm):**

在根目录 `package.json`:

```json
{
  "pnpm": {
    "overrides": {
      "lodash": "^4.17.21",
      "axios@<1.0.0": "^1.0.0"
    }
  }
}
```

**或在 .pnpmfile.cjs:**

```javascript
module.exports = {
  hooks: {
    readPackage(pkg) {
      if (pkg.dependencies?.lodash) {
        pkg.dependencies.lodash = '^4.17.21';
      }
      return pkg;
    }
  }
};
```

### 5. 升级 pnpm 版本

**步骤:**

1. 修改 `eden.monorepo.json`:

```json
{
  "config": {
    "pnpmVersion": "10.12.1"
  }
}
```

2. 清理并重新安装:

```bash
emo clean
emo install
```

**注意事项:**
- 检查 breaking changes
- 更新 CI 配置
- 测试所有项目

### 6. 构建缓存优化

**配置策略:**

```json
{
  "config": {
    "cache": {
      "affectedInput": {
        // 只包含真正影响构建的环境变量
        "env": ["NODE_ENV", "BUILD_ENV"],
        // 包含配置文件
        "file": "default"
      },
      "storedOutput": ["dist", "build"],
      "strategy": "default",
      "operations": {
        "build": {
          "storedOutput": ["dist"]
        },
        "test": {
          "storedOutput": [],
          "strategy": "isolated"
        }
      }
    }
  }
}
```

**最佳实践:**
- 只缓存稳定的产物目录
- 合理设置影响因素
- 本地使用 `isolated`,CI 使用 `default`

## 二、进阶功能

### 1. 插件系统

**创建插件:**

```javascript
// plugins/my-plugin/index.js
module.exports = {
  name: 'my-plugin',
  version: '1.0.0',

  // 插件钩子
  hooks: {
    // 在安装依赖前执行
    beforeInstall(context) {
      console.log('Before install...');
    },

    // 在构建前执行
    beforeBuild(context) {
      console.log('Before build...');
    },

    // 在构建后执行
    afterBuild(context) {
      console.log('After build...');
    }
  },

  // 插件命令
  commands: {
    'my-command': {
      description: 'My custom command',
      handler: async (args) => {
        console.log('Execute my command');
      }
    }
  }
};
```

**注册插件:**

```json
{
  "config": {
    "plugins": [
      "./plugins/my-plugin",
      "@emo/plugin-example"
    ],
    "pluginsDir": "plugins"
  }
}
```

### 2. Workspace Checker

**内置 Checker:**

1. **dependencyVersionCheck** - 依赖版本统一检查
2. **tagRelationCheck** - 标签关系检查
3. **externalDependencyCheck** - 外部依赖检查
4. **cycleDependencyCheck** - 循环依赖检查
5. **projectDependencyCheck** - 项目依赖检查
6. **tsconfigProjectReferenceCheck** - TypeScript 项目引用检查

**自定义 Checker:**

```javascript
// plugins/my-checker/index.js
module.exports = {
  name: 'my-checker',
  check: async (context) => {
    const { workspaces } = context;

    const errors = [];

    for (const workspace of workspaces) {
      // 检查逻辑
      if (!workspace.packageJson.description) {
        errors.push({
          workspace: workspace.name,
          message: 'Missing description'
        });
      }
    }

    return { errors };
  },
  fix: async (context, errors) => {
    // 自动修复逻辑
  }
};
```

### 3. CI 自动化发包

**配置 Changeset:**

```bash
# 初始化 changeset
npx changeset init
```

**CI 配置 (.codebase/pipelines/release.yaml):**

```yaml
name: Release
trigger: push
branches:
  - master

jobs:
  release:
    image: node:18
    steps:
      - name: Install
        commands:
          - npm install -g @ies/eden-monorepo@3.6.1
          - emo install --frozen-lockfile

      - name: Version
        commands:
          - emo version

      - name: Publish
        commands:
          - emo publish
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**工作流:**

1. 开发时添加 changeset:
```bash
emo add-changeset
```

2. 合并到 master 后自动:
   - 更新版本号
   - 生成 CHANGELOG
   - 发布到 npm
   - 发送通知

### 4. 模版生成器 (Generator)

**定义模版:**

```javascript
// templates/react-component/template.js
module.exports = {
  prompts: [
    {
      type: 'input',
      name: 'componentName',
      message: 'Component name:'
    }
  ],

  actions: [
    {
      type: 'add',
      path: 'src/components/{{componentName}}/index.tsx',
      templateFile: './component.hbs'
    },
    {
      type: 'add',
      path: 'src/components/{{componentName}}/style.css',
      templateFile: './style.hbs'
    }
  ]
};
```

**注册模版:**

```json
{
  "config": {
    "generator": [
      {
        "name": "react-component",
        "path": "./templates/react-component"
      }
    ]
  }
}
```

**使用模版:**

```bash
emo generate react-component
```

### 5. MCP Server (AI 集成)

EMO 提供了 MCP Server,帮助 AI 更好地分析和操作项目。

**功能:**
- 分析项目结构
- 查询依赖关系
- 执行 EMO 命令
- 检查项目状态

**配置:**

参考官方文档: https://emo.web.bytedance.net/tutorial/advanced/mcp-server.html

## 三、常见问题

### 1. 依赖安装问题

**问题: 安装失败或 lockfile 损坏**

```bash
# 清理并重新安装
emo clean
emo install

# 或重置
emo reset
```

**问题: 幻影依赖报错**

```bash
# 检查并修复
emo check --checker externalDependencyCheck --autofix
```

### 2. 构建问题

**问题: 缓存未生效**

```bash
# 清除缓存
rm -rf .eden-mono

# 检查缓存配置
cat eden.monorepo.json | grep cache
```

**问题: 构建顺序错误**

使用 `implicitDependencies` 指定依赖关系:

```json
{
  "packages": [
    {
      "name": "@myorg/app",
      "path": "apps/app",
      "implicitDependencies": ["@myorg/shared"]
    }
  ]
}
```

### 3. 版本管理问题

**问题: 版本不一致**

```bash
# 检查版本
emo check --checker dependencyVersionCheck

# 自动修复
emo check --checker dependencyVersionCheck --autofix
```

### 4. CI/CD 问题

**问题: CI 构建慢**

- 开启构建缓存
- 使用 `--frozen-lockfile`
- 只构建变更的项目

```bash
emo pipeline --scene codebase
```

**问题: SCM 构建失败**

检查:
- `eden.mono.pipeline.json` 配置
- `build.sh` 脚本
- 依赖是否安装完整

## 四、性能优化建议

### 1. 依赖安装优化

```json
{
  "config": {
    "pnpmVersion": "10.12.1"  // 使用最新版本
  }
}
```

### 2. 构建优化

- 使用增量构建
- 开启并行构建
- 配置合理的缓存

```bash
# 并行构建
emo run build --parallel
```

### 3. 依赖图优化

```json
{
  "config": {
    "buildProjectGraphFromSourceCode": false,  // 大项目关闭
    "pkgJsonDepsPolicies": "semver"
  }
}
```

### 4. CI 优化

- 使用远程缓存
- 合理配置 affected 构建
- 优化 Docker 镜像

## 五、工程治理建议

### 1. 代码规范

- 统一 ESLint/Prettier 配置
- 配置 Husky + Lint-staged
- 使用 CommitLint

### 2. 依赖管理

- 定期更新依赖
- 统一依赖版本
- 避免幻影依赖
- 使用 catalog 管理版本

### 3. 版本发布

- 使用 Changeset 管理版本
- 自动生成 CHANGELOG
- 配置发布通知
- 遵循语义化版本

### 4. 监控与告警

- 配置构建失败通知
- 监控依赖安全问题
- 追踪构建性能

## 相关文档

- 幻影依赖: https://emo.web.bytedance.net/tutorial/best-practices/phantom-dependency.html
- Pnpm Link 原理: https://emo.web.bytedance.net/tutorial/best-practices/how-pnpm-link.html
- 基于源码开发: https://emo.web.bytedance.net/tutorial/best-practices/source-code-development.html
- 锁定依赖: https://emo.web.bytedance.net/tutorial/best-practices/overrides-lock-version.html
- 升级 pnpm: https://emo.web.bytedance.net/tutorial/best-practices/pnpm-upgrade.html
- 插件系统: https://emo.web.bytedance.net/tutorial/advanced/plugin-system.html
- Workspace Checker: https://emo.web.bytedance.net/tutorial/advanced/workspace-checker.html
