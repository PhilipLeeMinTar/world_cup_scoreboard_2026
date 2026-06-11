# Vmok 微模块解决方案知识库

> **Vmok** - 基于 Module Federation 2.0 的 Web 微模块解决方案文档

## 📚 文档目录

### [01. Vmok 介绍](./01-introduction.md)
- 什么是 Vmok
- 核心概念 (生产者/消费者、Module Federation、Garfish)
- 架构设计
- 技术栈说明
- 快速上手指南
- 适用场景与对比

### [02. 开发指南](./02-development.md)
- 项目初始化
- 配置详解 (vmok.config.js、package.json)
- 开发流程 (生产者、消费者、应用类型)
- 类型支持
- 运行时 API
- 通信与数据共享
- 调试与性能
- 部署方式

## 🚀 快速开始

### 安装 Vmok CLI

```bash
# 全局安装
npm install -g @vmok/cli

# 验证安装
vmok --version
```

### 创建项目

```bash
# 创建 NPM 类型模块
vmok create my-module --type npm

# 创建应用类型模块
vmok create my-app --type app

# 创建消费者应用
vmok create my-consumer --type consumer
```

### 开发流程

```bash
# 进入项目目录
cd my-module

# 安装依赖
pnpm install

# 启动开发
vmok dev

# 构建生产版本
vmok build
```

## 🎯 核心特性

### ⚡ 运行时能力

| 特性 | 说明 | 优势 |
|------|------|------|
| **动态加载** | 运行时按需加载模块 | 减少初始包体积 |
| **依赖共享** | 避免重复打包相同依赖 | 减少 30-50% 包大小 |
| **版本管理** | 灵活的版本策略 | 支持灰度和回滚 |
| **类型安全** | 完整 TypeScript 支持 | 开发时类型提示 |

### 🛠️ 开发工具

| 工具 | 功能 |
|------|------|
| **Vmok CLI** | 项目创建、开发、构建、部署 |
| **Vmok DevTools** | 依赖图可视化、性能分析 |
| **模块中心** | 模块注册、版本管理、访问统计 |
| **部署平台** | 应用部署、灰度发布、CDN 加速 |

### 🏗️ 架构模式

- **生产者-消费者模式**: 清晰的角色划分
- **NPM 类型**: 适合组件库、工具库
- **应用类型**: 适合独立业务模块
- **Module Federation 2.0**: 运行时模块联邦
- **Garfish 集成**: 子应用生命周期管理

## 📦 两种模块类型

### NPM 类型模块

**特点:**
- 以 npm 包形式发布
- 适合组件库、工具库
- 通过 npm registry 分发
- 版本管理通过 package.json

**典型场景:**
```typescript
// 生产者
export { Button } from './components/Button';
export { Input } from './components/Input';

// 消费者
import { Button } from 'my-components/Button';
```

### 应用类型模块

**特点:**
- 独立完整的应用
- 适合业务模块
- 通过部署平台托管
- 支持独立部署和灰度

**典型场景:**
```typescript
// 消费者通过 Garfish 加载
<GarfishApp name="module-app" entry="http://example.com" />
```

## 💡 核心概念

### 1. 生产者 (Producer)

提供微模块的一方:

```javascript
// vmok.config.js
module.exports = {
  name: 'my-module',
  type: 'npm',
  exposes: {
    './Button': './src/components/Button',
    './Input': './src/components/Input'
  },
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true }
  }
};
```

### 2. 消费者 (Consumer)

使用微模块的一方:

```javascript
// vmok.config.js
module.exports = {
  name: 'my-app',
  type: 'consumer',
  remotes: {
    'my-module': 'my-module@http://localhost:3001/remoteEntry.js'
  },
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true }
  }
};
```

### 3. 依赖共享

```javascript
{
  shared: {
    react: {
      singleton: true,        // 单例模式,全局只有一个实例
      requiredVersion: '^18.0.0',
      strictVersion: false,   // 版本不严格匹配
      eager: false           // 懒加载
    }
  }
}
```

## 🔥 使用示例

### 创建生产者

```typescript
// src/components/Button/index.tsx
import React from 'react';
import './style.css';

export interface ButtonProps {
  type?: 'primary' | 'default';
  onClick?: () => void;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  type = 'default',
  onClick,
  children
}) => {
  return (
    <button
      className={`vmok-button vmok-button-${type}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

export default Button;
```

```typescript
// src/index.ts
export { Button } from './components/Button';
export type { ButtonProps } from './components/Button';
```

### 在消费者中使用

**静态导入:**

```typescript
import React from 'react';
import { Button } from 'my-module/Button';

function App() {
  return (
    <div>
      <h1>消费者应用</h1>
      <Button type="primary" onClick={() => alert('Clicked!')}>
        点击我
      </Button>
    </div>
  );
}
```

**动态导入:**

```typescript
import React, { Suspense, lazy } from 'react';

const RemoteButton = lazy(() => import('my-module/Button'));

function App() {
  return (
    <Suspense fallback={<div>加载中...</div>}>
      <RemoteButton type="primary">点击我</RemoteButton>
    </Suspense>
  );
}
```

**运行时 API:**

```typescript
import { loadRemote } from '@vmok/runtime';

const module = await loadRemote('my-module/Button');
const Button = module.default;
```

## 🌐 运行时 API

### loadRemote - 加载远程模块

```typescript
import { loadRemote } from '@vmok/runtime';

// 基础用法
const module = await loadRemote('my-module/Button');

// 指定版本
const module = await loadRemote('my-module/Button', {
  version: '1.2.0'
});
```

### preloadRemote - 预加载模块

```typescript
import { preloadRemote } from '@vmok/runtime';

// 预加载多个模块
await preloadRemote([
  'my-module/Button',
  'my-module/Input'
]);
```

### registerRemote - 运行时注册

```typescript
import { registerRemote } from '@vmok/runtime';

registerRemote({
  name: 'dynamic-module',
  entry: 'https://cdn.example.com/module/remoteEntry.js'
});
```

## 🔌 通信与共享

### Vmok Bridge - 跨模块通信

```typescript
// 生产者: 提供服务
import { createBridge } from '@vmok/bridge';

const bridge = createBridge('my-service');

bridge.provide('getUser', async (userId: string) => {
  return await fetchUser(userId);
});

// 消费者: 调用服务
import { useBridge } from '@vmok/bridge';

const bridge = useBridge('my-service');
const user = await bridge.call('getUser', 'user-123');
```

### 事件总线

```typescript
import { eventBus } from '@vmok/runtime';

// 发送事件
eventBus.emit('user:login', { userId: '123' });

// 监听事件
eventBus.on('user:login', (data) => {
  console.log('User logged in:', data);
});
```

### 状态共享

```typescript
import { createSharedStore, useSharedStore } from '@vmok/store';

// 创建共享状态
export const userStore = createSharedStore({
  state: {
    user: null,
    isLoggedIn: false
  },
  actions: {
    login(user) {
      this.user = user;
      this.isLoggedIn = true;
    }
  }
});

// 在任意模块中使用
const [state, actions] = useSharedStore(userStore);
```

## 📐 项目结构

### NPM 类型模块

```
my-module/
├── src/
│   ├── components/
│   │   ├── Button/
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   └── Input/
│   │       ├── index.tsx
│   │       └── style.css
│   ├── index.ts
│   └── types.ts
├── dist/                   # 构建产物
├── vmok.config.js         # Vmok 配置
├── package.json
├── tsconfig.json
└── README.md
```

### 应用类型模块

```
my-app/
├── src/
│   ├── pages/
│   ├── components/
│   ├── App.tsx
│   └── index.tsx
├── public/
├── vmok.config.js
├── package.json
└── tsconfig.json
```

### 消费者应用

```
my-consumer/
├── src/
│   ├── pages/
│   ├── components/
│   ├── App.tsx
│   └── index.tsx
├── types/                 # 远程模块类型声明
│   └── remotes.d.ts
├── vmok.config.js
├── package.json
└── tsconfig.json
```

## ⚙️ 配置示例

### 生产者配置

```javascript
// vmok.config.js
module.exports = {
  // 模块名称
  name: 'my-module',

  // 模块类型: npm | app
  type: 'npm',

  // 暴露的模块
  exposes: {
    './Button': './src/components/Button',
    './Input': './src/components/Input',
    './utils': './src/utils'
  },

  // 共享依赖
  shared: {
    react: {
      singleton: true,
      requiredVersion: '^18.0.0'
    },
    'react-dom': {
      singleton: true,
      requiredVersion: '^18.0.0'
    }
  },

  // 构建配置
  build: {
    outputDir: 'dist',
    publicPath: 'auto',
    generateTypes: true,
    minify: true
  }
};
```

### 消费者配置

```javascript
// vmok.config.js
module.exports = {
  name: 'my-consumer',
  type: 'consumer',

  // 远程模块
  remotes: {
    'my-module': 'my-module@http://localhost:3001/remoteEntry.js',
    'other-module': {
      url: 'http://localhost:3002/remoteEntry.js',
      entry: 'other-module'
    }
  },

  // 共享依赖
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true }
  },

  // Garfish 配置 (应用类型)
  garfish: {
    sandbox: true,
    router: { mode: 'browser' },
    preload: ['my-app']
  }
};
```

## 🎨 类型支持

### 自动生成类型

```bash
# 构建时生成类型定义
vmok build --generate-types
```

### 类型声明

```typescript
// types/remotes.d.ts
declare module 'my-module/Button' {
  export interface ButtonProps {
    type?: 'primary' | 'default';
    onClick?: () => void;
    children: React.ReactNode;
  }

  export const Button: React.FC<ButtonProps>;
  export default Button;
}
```

### 使用类型

```typescript
import { Button, ButtonProps } from 'my-module/Button';

// 完整类型支持
const props: ButtonProps = {
  type: 'primary',
  onClick: () => console.log('Clicked')
};
```

## 🚢 部署方式

### NPM 类型部署

```bash
# 构建
vmok build

# 发布到 npm
npm publish

# 发布到内部 registry
npm publish --registry https://npm.byted.org
```

### 应用类型部署

```bash
# 部署到 SCM
vmok deploy --platform scm

# 部署到 Goofy
vmok deploy --platform goofy

# 灰度发布
vmok deploy --gray 10%

# CDN 部署
vmok deploy --cdn
```

## 📊 适用场景

### ✅ 适合使用 Vmok

- **微前端架构**: 多团队独立开发的大型应用
- **组件库共享**: 跨项目共享 UI 组件
- **业务模块解耦**: 独立开发和部署
- **插件系统**: 支持第三方插件扩展
- **逐步迁移**: 老项目逐步迁移到新技术

### 🎯 典型应用场景

1. **大型企业应用**: 多个业务线独立开发
2. **设计系统**: 统一的组件库和设计规范
3. **SaaS 平台**: 支持第三方应用集成
4. **电商平台**: 独立的营销活动模块

### ❌ 不适合使用 Vmok

- 简单的单页应用
- 没有模块共享需求
- 团队规模很小
- 不需要独立部署的项目

## 🔧 开发工具

### Vmok CLI

```bash
vmok --version          # 查看版本
vmok create            # 创建项目
vmok dev              # 启动开发
vmok build            # 构建生产
vmok deploy           # 部署应用
vmok publish          # 发布 npm 包
```

### Vmok DevTools

**浏览器插件:**
- 依赖图可视化
- 性能分析
- 模块加载监控
- 版本管理

**安装:** https://vmok-devtools.bytedance.net/

### 模块中心

**功能:**
- 模块注册和管理
- 版本控制
- 访问统计
- 依赖分析

**访问:** https://vmok-center.bytedance.net/

## 🔗 相关资源

### 官方资源
- **官方文档**: https://vmok.bytedance.net/
- **API 文档**: https://vmok.bytedance.net/api/
- **模块中心**: https://vmok-center.bytedance.net/
- **代码仓库**: https://code.byted.org/vmok/vmok
- **用户群**: [飞书群组](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=xxx)

### 技术文档
- **Module Federation**: https://webpack.js.org/concepts/module-federation/
- **Garfish**: https://www.garfishjs.org/
- **Webpack 5**: https://webpack.js.org/

### 相关框架
- **PIA**: 移动端 H5 解决方案
- **EMO**: Monorepo 解决方案
- **EdenX**: PC 端应用框架

## ❓ 常见问题

### Q: Vmok 和 Module Federation 的区别?
A: Vmok 是基于 Module Federation 2.0 的工程化封装,提供了完整的开发工具链、类型支持、通信机制和部署方案。

### Q: NPM 类型和应用类型如何选择?
A: NPM 类型适合组件库、工具库;应用类型适合完整的业务模块。如果需要独立部署和灰度,选择应用类型。

### Q: 如何处理版本冲突?
A: 使用 `shared` 配置中的 `singleton` 和 `requiredVersion` 来管理依赖版本,确保全局只有一个实例。

### Q: 性能如何优化?
A: 使用预加载、合理配置共享依赖、启用代码分割、使用 CDN 加速。

### Q: 如何调试远程模块?
A: 使用 Vmok DevTools 浏览器插件,或在开发环境启用 source map。

## 📝 更新日志

查看完整更新日志: https://vmok.bytedance.net/changelog.html

## 🤝 贡献与反馈

如果在使用 Vmok 过程中遇到问题或有建议:
- 加入用户群交流
- 提交 Issue: https://code.byted.org/vmok/vmok/issues
- 查阅官方文档

---

**维护者**: Web Infra Team
**版本**: Vmok V2
**文档范围**: 微模块解决方案完整文档
**最后更新**: 2025-11-25
