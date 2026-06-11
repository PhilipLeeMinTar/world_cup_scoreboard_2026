# PIA 前端开发介绍

> **版本**: PIA V3
> **官方文档**: https://pia.bytedance.net/

## 什么是 PIA

**PIA** 是 "**Progressive Instant Web Application**" 的缩写,读作 `/pɪaɪeɪ/`,是一个专注于 **Mobile Web** 的解决方案。

PIA 主要由两部分组成:

1. **PIA Kit** - 提供构建能力的研发框架,解决工程效率问题
2. **PIA SDK** - 增强 Webview 能力的客户端 SDK

> **📝 注意**: 本文档主要面向前端开发者使用 PIA Kit,如果需要查看客户端文档,请移步 [Android](https://pia.bytedance.net/android/getting-started/introduction.html) 和 [iOS](https://pia.bytedance.net/ios/getting-started/introduction.html) 章节。

## 核心特性

### ⚡ 性能优化

通过 PIA SDK 和 PIA Runtime,PIA 提供了大量性能优化能力:

| 功能 | 适用业务场景 | 解决的问题 |
|------|-------------|-----------|
| **Prefetch** (预取) | 首屏渲染依赖请求 | 减少首屏请求时间 |
| **NSR** (Native Side Rendering) | 对时效性不敏感且有前置入口的页面 | 提高页面打开速度,首屏内容"直出" |
| **Snapshot** (快照) | 第二次打开页面与第一次内容差异不大 | 第二次打开直接复用第一次渲染的 HTML |

### 🛠️ 构建能力

PIA Kit 提供专注于 Mobile Web 项目的构建能力:

| 功能 | 解决的问题 |
|------|-----------|
| **基础构建能力** | 提供开箱即用的命令行工具,快速开发移动应用 |
| **客户端能力构建** | 客户端能力驱动的功能开箱即用,无需考虑复杂实现细节 |
| **统一工程设计** | Prefetch / NSR / SSR 实现统一工程设计,功能横向迁移成本低 |
| **插件系统** | 灵活控制构建行为,直接复用现有插件生态 |

### 🐛 开发与调试

PIA 提供了完善的开发调试工具链:

| 工具 | 解决的问题 |
|------|-----------|
| **HDT** | 让 Prefetch/NSR 的 PIA Worker 可以断点调试和查看日志 |
| **PIA Console** | 让 PIA Runtime 和 Webview 的运行时状态更容易查看 |
| **SPM** | 提供 iOS 模拟器包下载、App 快速调用等能力 |
| **pia.dev** | 在 PC 浏览器中调试 in-sdk H5 页面(包括 Prefetch/NSR) |

## 技术栈

### 前端框架
- **React 18.2.0** (主要支持)
- **Preact** (可选)
- 支持 **SSR** (服务端渲染)

### 构建工具
- **Webpack** (默认)
- **Rspack** (可选,更快的构建速度)

### 开发语言
- **TypeScript 5.3.2+**
- 完整的类型支持

## 系统要求

### Node.js
- **Node.js 16.0.0** 或更高版本

### 包管理器
- 推荐使用 **pnpm**
- 也支持 npm 和 yarn

## 快速上手

### 1. 创建项目

**方式一: 在线创建 (推荐)**

使用 [Ship Web 平台](https://pia.bytedance.net/practice/ship/overview.html) 创建项目,提供图形化流程,更方便。

**方式二: 本地 CLI 创建**

```bash
# 创建独立项目
npx -y @byted/create@latest
# 选择 PIA 解决方案

# 或在 EMO Monorepo 中创建子项目
npx -y @byted/create@latest --emo-sub-prj
```

### 2. 安装依赖

```bash
pnpm install
# 或 npm install
# 或 yarn install
```

### 3. 启动开发

```bash
pnpm dev
# 访问 http://localhost:5566/index
```

### 4. 构建部署

```bash
# 构建生产环境
pnpm build

# 构建部署产物
pnpm deploy
```

## 项目结构

```
my-pia-project/
├── src/
│   ├── pages/              # 页面目录
│   │   └── index/          # 首页
│   │       └── index.tsx   # 页面组件
│   ├── common/             # 公共代码
│   └── ...
├── config/                 # 配置目录
│   ├── public/            # 静态资源
│   ├── upload/            # 上传配置
│   └── mock/              # Mock 数据
├── tsconfig.json          # TypeScript 配置
├── package.json
└── ...
```

## 基础配置

### package.json

```json
{
  "scripts": {
    "dev": "pia dev",       // 开发模式
    "build": "pia build",   // 构建
    "deploy": "pia deploy"  // 部署
  },
  "dependencies": {
    "@piajs/kit": "^2",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "@types/node": "16.11.12",
    "@types/react": "18.0.17",
    "@types/react-dom": "18.0.6",
    "typescript": "5.3.2"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@common/*": ["./src/common/*"]
    },
    "esModuleInterop": true,
    "jsx": "preserve",
    "types": ["@piajs/kit/client"]
  },
  "include": ["src"]
}
```

## 核心概念

### 1. PIA Worker
- 运行在独立线程的 JavaScript 环境
- 用于执行 Prefetch 和 NSR 逻辑
- 不阻塞主线程,提升性能

### 2. PIA Runtime
- 客户端运行时环境
- 管理页面生命周期
- 协调 Worker 和 Webview

### 3. Client Mode
- **MPA** (Multi-Page Application) - 多页面应用
- **SPA** (Single-Page Application) - 单页面应用
- 灵活选择适合的模式

## 开发工作流

### 日常开发
```bash
# 1. 启动开发服务器
pnpm dev

# 2. 访问页面
# http://localhost:5566/index

# 3. 编辑代码
# src/pages/index/index.tsx

# 4. 热更新自动刷新
```

### 快速调试
```bash
# 启动开发服务器后
# 在命令行输入: p + Enter
# 自动打开 pia.dev 进行调试
```

### 构建发布
```bash
# 1. 构建生产产物
pnpm build

# 2. 构建部署产物
pnpm deploy

# 3. 部署到 SCM/Goofy
```

## 性能优化特性

### Prefetch (预取)
- 在页面加载前预先请求数据
- 减少首屏渲染时间
- 适用于依赖请求的页面

### NSR (Native Side Rendering)
- 在客户端侧预渲染页面
- 页面打开即可看到内容
- 适用于内容稳定的页面

### Snapshot (快照)
- 保存首次渲染的 HTML
- 第二次打开直接复用
- 大幅提升二次打开速度

### Code Cache (代码缓存)
- 缓存编译后的 JS 代码
- 减少脚本执行时间
- 提升页面加载性能

## 开发调试工具

### pia.dev
- 在 PC 浏览器调试移动页面
- 支持 Prefetch/NSR 调试
- 实时预览和热更新

### PIA Console
- 查看运行时状态
- 监控性能指标
- 调试客户端能力

### HDT
- Worker 断点调试
- 查看日志输出
- 分析执行流程

## 插件系统

PIA 提供了丰富的插件生态:

- **官方插件**: 覆盖常见场景
- **自定义插件**: 灵活扩展功能
- **插件 API**: 完善的开发文档

## 部署方式

### SCM 部署
- 字节内部部署平台
- 支持多环境部署
- 自动化构建流程

### Goofy Deploy
- 前端部署平台
- CDN 加速
- 灰度发布

### Gecko
- 离线包方案
- 提升加载速度
- 减少网络依赖

### ByteCycle
- 持续集成部署
- 自动化测试
- 质量监控

## 迁移指南

PIA 提供了从其他框架迁移的完整指南:

- 从 PIA v1 迁移
- 从 PIA Kit (Speedy) 迁移
- 从 EdenX 迁移
- 从 Eden 2.x / 0.x 迁移
- 从 Jupiter v5 迁移

## 相关资源

- **官方文档**: https://pia.bytedance.net/
- **API 文档**: https://pia.bytedance.net/api/
- **插件文档**: https://pia.bytedance.net/plugin/
- **代码仓库**: https://code.byted.org/pia/pia
- **用户群**: [飞书群组](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=501t9a09-f650-4b10-9140-28d718fc6a2a&qr_code=true)
- **Ship Web**: https://web-infra.bytedance.net/ship

## 适用场景

### ✅ 适合使用 PIA
- 移动端 H5 应用
- 需要高性能优化的页面
- 在字节系 App 内的页面
- 需要客户端能力支持的项目

### ❌ 不适合使用 PIA
- 纯 PC 端应用 (推荐使用 EdenX)
- 独立的 SSR 服务 (推荐使用 PIA SSR)
- 简单的静态页面

## 下一步

- 查看 [核心功能文档](./02-core-features.md) 了解详细特性
- 阅读 [开发指南](./03-development-guide.md) 开始开发
- 参考 [最佳实践](./04-best-practices.md) 优化项目

---

**维护者**: Web Infra Team
**版本**: PIA V3
**最后更新**: 2025-11-25
