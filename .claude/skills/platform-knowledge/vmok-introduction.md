# Vmok 微模块解决方案介绍

> **Vmok** - 基于 Module Federation 2.0 的 Web 微模块解决方案

## 什么是 Vmok

**Vmok** 是一个面向 Web 开发场景的**微模块解决方案**,由字节跳动前端基础设施团队开发。

Vmok 提供了一套完整的微前端架构方案,主要特点:

- 基于 **Module Federation 2.0** 和 **Garfish** 技术
- 支持**运行时动态注入**和**依赖共享**
- 提供**模块中心**和**部署平台**
- 统一的**生产者-消费者**架构模式

## 核心概念

### 1. 生产者 (Producer)

生产者是提供微模块的一方,负责开发、构建和发布模块。

**两种类型:**

#### NPM 类型 (NPM Type)
- 以 npm 包的形式发布
- 通过 npm registry 分发
- 适合组件库、工具库等场景
- 版本管理通过 package.json

#### 应用类型 (Application Type)
- 以独立应用的形式发布
- 通过部署平台托管
- 适合独立业务模块
- 支持独立部署和灰度

### 2. 消费者 (Consumer)

消费者是使用微模块的一方,负责加载和运行模块。

**特点:**
- 动态加载生产者模块
- 管理模块生命周期
- 提供依赖共享能力
- 支持模块隔离和通信

### 3. Module Federation 2.0

Vmok 基于 Webpack Module Federation 2.0 技术:

**优势:**
- **运行时加载**: 无需提前打包,按需加载
- **依赖共享**: 避免重复加载相同依赖
- **版本管理**: 灵活的版本策略
- **类型安全**: 完整的 TypeScript 支持

**与 Module Federation 的关系:**
```
Vmok = Module Federation 2.0 + Garfish + 工程化封装
```

### 4. Garfish 集成

Vmok 集成了 **Garfish** 微前端框架:

**功能:**
- 子应用生命周期管理
- JS/CSS 沙箱隔离
- 应用间通信
- 路由管理

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────┐
│           消费者应用 (Consumer)           │
│  ┌──────────────────────────────────┐  │
│  │     Vmok Runtime (运行时)         │  │
│  │  ┌────────┐  ┌────────┐          │  │
│  │  │ 模块A  │  │ 模块B  │          │  │
│  │  └────────┘  └────────┘          │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
              ↓ 加载
┌─────────────────────────────────────────┐
│          模块中心 (Module Center)         │
│  ┌──────────┐       ┌──────────┐        │
│  │ NPM 模块 │       │ App 模块 │        │
│  └──────────┘       └──────────┘        │
└─────────────────────────────────────────┘
              ↑ 发布
┌─────────────────────────────────────────┐
│         生产者应用 (Producer)            │
│  ┌──────────────────────────────────┐  │
│  │    Vmok Build Plugin (构建)       │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 模块中心 (Module Center)

**功能:**
- 模块注册和管理
- 版本控制
- 依赖分析
- 访问统计

**访问地址:** https://vmok-center.bytedance.net/

### 部署平台

**功能:**
- 应用类型模块的部署
- 灰度发布
- 回滚管理
- CDN 加速

## 技术栈

### 核心技术
- **Webpack 5** - 构建工具
- **Module Federation 2.0** - 模块联邦
- **Garfish** - 微前端框架
- **TypeScript** - 类型支持

### 支持框架
- **React** 16.8+, 17.x, 18.x
- **Vue** 2.x, 3.x (通过插件)
- 其他框架正在支持中

## 快速上手

### 安装

```bash
# 安装 Vmok CLI
npm install -g @vmok/cli

# 或使用 pnpm
pnpm add -g @vmok/cli
```

### 创建生产者项目

```bash
# 创建 NPM 类型模块
vmok create my-module --type npm

# 创建应用类型模块
vmok create my-app --type app
```

### 创建消费者项目

```bash
# 创建消费者应用
vmok create my-consumer --type consumer
```

### 基础使用

#### 1. 配置生产者 (NPM 类型)

```javascript
// vmok.config.js
module.exports = {
  name: 'my-module',
  type: 'npm',
  exposes: {
    './Button': './src/components/Button',
    './utils': './src/utils'
  },
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true }
  }
};
```

#### 2. 配置消费者

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

#### 3. 使用远程模块

```typescript
// src/App.tsx
import React from 'react';

// 动态导入远程模块
const RemoteButton = React.lazy(() => import('my-module/Button'));

function App() {
  return (
    <div>
      <h1>消费者应用</h1>
      <React.Suspense fallback="Loading...">
        <RemoteButton />
      </React.Suspense>
    </div>
  );
}

export default App;
```

## 核心特性

### 1. 运行时动态加载

**特点:**
- 按需加载模块
- 无需重新构建主应用
- 支持版本热更新

**示例:**

```typescript
// 运行时动态加载
import { loadRemote } from '@vmok/runtime';

const module = await loadRemote('my-module/Button');
```

### 2. 依赖共享

**特点:**
- 避免重复打包
- 减少包体积
- 统一依赖版本

**配置示例:**

```javascript
{
  shared: {
    react: {
      singleton: true,        // 单例模式
      requiredVersion: '^18.0.0',
      strictVersion: false,    // 版本不严格
      eager: false            // 懒加载
    }
  }
}
```

### 3. 类型安全

**功能:**
- 自动生成类型定义
- TypeScript 完整支持
- IDE 智能提示

**使用:**

```typescript
// 生成类型
vmok build --generate-types

// 使用时自动提示
import { Button } from 'my-module/Button'; // 有完整类型
```

### 4. 版本管理

**策略:**
- Semantic Versioning
- 灰度发布
- 版本回滚

### 5. 开发调试

**工具:**
- Vmok DevTools
- 模块依赖图可视化
- 性能分析

## 适用场景

### ✅ 适合使用 Vmok

- **微前端架构**: 多个团队独立开发的大型应用
- **组件库共享**: 跨项目共享 UI 组件
- **业务模块解耦**: 独立开发和部署业务模块
- **逐步迁移**: 老项目逐步迁移到新技术栈

### 🎯 典型场景

1. **多团队协作**: 不同团队维护不同模块
2. **组件库**: 统一的设计系统和组件库
3. **插件系统**: 支持第三方插件
4. **AB 测试**: 不同版本的功能测试

### ❌ 不适合使用 Vmok

- 简单的单页应用
- 没有模块共享需求
- 团队规模很小
- 不需要独立部署

## 与其他方案对比

### Vmok vs 传统 Monorepo

| 对比项 | Vmok | Monorepo |
|--------|------|----------|
| 构建方式 | 独立构建 | 统一构建 |
| 部署方式 | 独立部署 | 统一部署 |
| 版本管理 | 独立版本 | 统一版本 |
| 团队协作 | 完全独立 | 代码共享 |
| 适用场景 | 大型分布式 | 中小型集中式 |

### Vmok vs iframe

| 对比项 | Vmok | iframe |
|--------|------|--------|
| 性能 | 高(共享依赖) | 低(重复加载) |
| 通信 | 简单 | 复杂(postMessage) |
| 样式隔离 | 可选 | 完全隔离 |
| SEO | 支持 | 不友好 |

## 相关资源

### 官方资源
- **官方文档**: https://vmok.bytedance.net/
- **API 文档**: https://vmok.bytedance.net/api/
- **模块中心**: https://vmok-center.bytedance.net/
- **代码仓库**: https://code.byted.org/vmok/vmok

### 社区
- **用户群**: [飞书群组](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=xxx)
- **问题反馈**: https://code.byted.org/vmok/vmok/issues

### 学习资源
- Module Federation 官方文档: https://webpack.js.org/concepts/module-federation/
- Garfish 文档: https://www.garfishjs.org/

## 系统要求

### Node.js
- Node.js 16.0.0 或更高版本

### 包管理器
- npm 7+
- pnpm 7+ (推荐)
- yarn 2+

### 浏览器支持
- Chrome 90+
- Edge 90+
- Firefox 88+
- Safari 14+

## 下一步

- 查看 [开发指南](./02-development.md) 了解详细开发流程
- 访问 [模块中心](https://vmok-center.bytedance.net/) 查看可用模块
- 阅读 [最佳实践](./03-best-practices.md) 优化项目架构

---

**维护者**: Web Infra Team
**版本**: Vmok V2
**最后更新**: 2025-11-25
