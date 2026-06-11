# PIA 前端开发知识库

> **PIA V3** - 移动 Web 解决方案文档 (仅前端部分)

## 📚 文档目录

### [01. PIA 介绍](./01-introduction.md)
- 什么是 PIA
- 核心特性与优势
- 技术栈说明
- 快速上手指南
- 项目结构与配置

### [02. 核心功能](./02-core-features.md)
- 性能优化功能 (Prefetch, NSR, Snapshot等)
- 构建功能 (Webpack/Rspack, 代码分割等)
- 工程化功能 (路由, 资源处理, HMR等)
- 调试工具 (pia.dev, PIA Console, HDT等)
- 插件系统

## 🚀 快速开始

### 创建项目

```bash
# 使用 CLI 创建
npx -y @byted/create@latest
# 选择 PIA 解决方案

# 或在 EMO Monorepo 中创建
npx -y @byted/create@latest --emo-sub-prj
```

### 开发流程

```bash
# 安装依赖
pnpm install

# 启动开发
pnpm dev

# 访问页面
# http://localhost:5566/index

# 快速调试 (输入 p + Enter)
# 自动打开 pia.dev
```

### 构建部署

```bash
# 构建生产环境
pnpm build

# 构建部署产物
pnpm deploy
```

## 🎯 核心特性

### ⚡ 性能优化

| 功能 | 说明 | 性能提升 |
|------|------|----------|
| **Prefetch** | 数据预取 | FCP 提升 30-50% |
| **NSR** | 客户端预渲染 | 页面秒开 |
| **Snapshot** | HTML 快照 | 二次打开提升 50-80% |
| **Code Cache** | 代码缓存 | 执行时间减少 30-50% |

### 🛠️ 开发工具

| 工具 | 功能 |
|------|------|
| **pia.dev** | PC 浏览器调试移动页面 |
| **PIA Console** | 运行时状态监控 |
| **HDT** | Worker 断点调试 |
| **Slardar** | 性能监控与错误上报 |

### 🏗️ 构建能力

- **多构建器**: Webpack / Rspack
- **TypeScript**: 完整支持
- **CSS方案**: CSS Modules / Less / Sass
- **代码分割**: 自动+手动分割
- **HMR**: 热更新
- **插件系统**: 灵活扩展

## 📦 技术栈

### 前端框架
- React 18.2.0 (主要)
- Preact (可选)

### 构建工具
- Webpack (默认)
- Rspack (更快)

### 开发语言
- TypeScript 5.3.2+

### 包管理器
- pnpm (推荐)
- npm / yarn

## 💡 核心概念

### PIA Worker
运行在独立线程的 JavaScript 环境,执行 Prefetch 和 NSR 逻辑,不阻塞主线程。

### PIA Runtime
客户端运行时环境,管理页面生命周期,协调 Worker 和 Webview。

### Client Mode
- **MPA** - 多页面应用
- **SPA** - 单页面应用

## 📋 项目结构

```
my-pia-project/
├── src/
│   ├── pages/              # 页面目录 (约定式路由)
│   │   ├── index/          # 首页
│   │   │   ├── index.tsx   # 页面组件
│   │   │   ├── worker.ts   # Worker 逻辑 (Prefetch/NSR)
│   │   │   └── index.module.css
│   │   └── detail/         # 详情页
│   ├── components/         # 公共组件
│   ├── utils/             # 工具函数
│   └── common/            # 公共代码
├── config/                 # 配置目录
│   ├── public/            # 静态资源
│   ├── upload/            # 上传配置
│   └── mock/              # Mock 数据
├── pia.config.js          # PIA 配置
├── tsconfig.json          # TS 配置
└── package.json
```

## ⚙️ 基础配置

### package.json

```json
{
  "scripts": {
    "dev": "pia dev",
    "build": "pia build",
    "deploy": "pia deploy"
  },
  "dependencies": {
    "@piajs/kit": "^2",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "jsx": "preserve",
    "types": ["@piajs/kit/client"],
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### pia.config.js

```javascript
module.exports = {
  builder: 'rspack',  // 或 'webpack'
  alias: {
    '@': './src'
  },
  proxy: {
    '/api': 'https://api.example.com'
  }
};
```

## 🔥 核心功能示例

### Prefetch (数据预取)

```typescript
// src/pages/index/worker.ts
export async function prefetch(context) {
  const data = await fetch('/api/data').then(res => res.json());
  return { data };
}

// src/pages/index/index.tsx
function Index({ prefetchData }) {
  return <div>{prefetchData.data}</div>;
}
```

### NSR (客户端预渲染)

```typescript
// src/pages/index/worker.ts
export async function nsr(context) {
  const data = await fetch('/api/data').then(res => res.json());
  return {
    props: { data }
  };
}
```

### CSS Modules

```typescript
// index.module.css
.container {
  padding: 20px;
}

// index.tsx
import styles from './index.module.css';

function App() {
  return <div className={styles.container}>Hello</div>;
}
```

## 🎨 样式方案

### 支持的方案
- **CSS Modules** (推荐)
- **Less**
- **Sass/Scss**
- **PostCSS**
- **Styled Components**

### REM 适配

```javascript
// pia.config.js
module.exports = {
  rem: {
    enabled: true,
    rootValue: 75
  }
};
```

## 🔌 插件系统

### 使用官方插件

```javascript
// pia.config.js
module.exports = {
  plugins: [
    '@piajs/plugin-less',
    '@piajs/plugin-sass'
  ]
};
```

### 自定义插件

```javascript
// my-plugin.js
module.exports = {
  name: 'my-plugin',
  setup(api) {
    api.onBuildStart(() => {
      console.log('Build started');
    });
  }
};
```

## 🚢 部署方式

### SCM 部署
字节内部部署平台,支持多环境部署。

### Goofy Deploy
前端部署平台,CDN 加速,灰度发布。

### Gecko
离线包方案,提升加载速度。

### ByteCycle
持续集成部署,自动化测试。

## 🐛 调试技巧

### 快速打开 pia.dev
```bash
pnpm dev
# 在命令行输入: p + Enter
```

### Worker 调试
使用 HDT 进行 Prefetch/NSR Worker 的断点调试。

### 性能分析
```bash
# 使用 Rsdoctor 分析构建性能
RSDOCTOR=true pnpm build
```

## 📊 性能优化建议

### 1. 选择合适的优化策略
- 首屏依赖请求 → 使用 Prefetch
- 内容相对稳定 → 使用 NSR
- 二次打开场景多 → 使用 Snapshot

### 2. 代码优化
- 使用代码分割
- 懒加载非首屏组件
- 优化图片资源

### 3. 构建优化
- 使用 Rspack 替代 Webpack
- 开启 Code Cache
- 合理配置 chunk splitting

## 🔗 相关资源

### 官方资源
- **官方文档**: https://pia.bytedance.net/
- **FE 文档**: https://pia.bytedance.net/guide/
- **API 文档**: https://pia.bytedance.net/api/
- **插件文档**: https://pia.bytedance.net/plugin/
- **实践案例**: https://pia.bytedance.net/practice/

### 调试工具
- **pia.dev**: https://dev.pia.bytedance.net/
- **Ship Web**: https://web-infra.bytedance.net/ship

### 社区
- **代码仓库**: https://code.byted.org/pia/pia
- **用户群**: [飞书群组](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=501t9a09-f650-4b10-9140-28d718fc6a2a&qr_code=true)

## ❓ 常见问题

### Q: PIA 和 EdenX 有什么区别?
A: PIA 专注于移动端 H5,EdenX 专注于 PC 端。PIA 提供了更多移动端性能优化能力。

### Q: 如何选择 Webpack 还是 Rspack?
A: Rspack 构建速度更快,推荐新项目使用。老项目如果有 Webpack 特定插件依赖,继续使用 Webpack。

### Q: Prefetch 和 NSR 可以同时使用吗?
A: 不建议。根据场景选择一种即可,NSR 的性能优化效果更好但适用场景有限制。

### Q: 如何调试 Worker 中的代码?
A: 使用 HDT 工具,可以对 Worker 进行断点调试和日志查看。

## 📝 更新日志

查看完整更新日志: https://pia.bytedance.net/guide/changelog.html

## 🤝 贡献与反馈

如果在使用 PIA 过程中遇到问题或有建议:
- 加入用户群交流
- 提交 Issue
- 查阅官方文档

---

**维护者**: Web Infra Team
**版本**: PIA V3
**文档范围**: 仅前端部分
**最后更新**: 2025-11-25
