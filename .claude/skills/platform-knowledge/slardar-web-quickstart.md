# 2. 快速上手 Slardar Web SDK

本章节将引导你一步步在前端项目中安装并启动 Slardar，整个过程通常只需要几分钟。

**快速索引**
- [第一步：安装 SDK](#第一步安装-sdk)
- [第二步：初始化与启动](#第二步初始化与启动)
- [第三步：验证上报](#第三步验证上报)
- [开箱即用的能力](#开箱即用的能力)
- [常见问题排查](#常见问题排查)

## 第一步：安装 SDK

首先，你需要使用项目的包管理器安装 `@slardar/web`。它兼容 npm、yarn、pnpm 等主流工具。

```bash
# 使用 npm
npm install @slardar/web

# 使用 yarn
yarn add @slardar/web

# 使用 pnpm
pnpm add @slardar/web
```

## 第二步：初始化与启动

安装完成后，在你的应用入口文件（例如 `main.ts`, `app.tsx` 或类似的启动脚本）中，尽早地执行初始化和启动逻辑。

**“尽早”** 是关键，因为这能确保 Slardar 尽可能多地捕获到应用在启动阶段可能发生的异常和性能问题。

```typescript
// main.ts 或你的应用入口文件

import browserClient from '@slardar/web';

// 1. 初始化 Slardar 实例
browserClient('init', {
  // 将 'YOUR_BID' 替换为你在 Slardar 平台申请到的真实 bid
  bid: 'YOUR_BID',
  // [可选] 默认是国内（CN）区域，如果你的应用部署在海外，需要指定区域
  // region: 'SG', // 例如，新加坡区域
});

// 2. 启动 Slardar，开始数据采集和上报
browserClient('start');

// --- 你的应用原始启动逻辑 ---
// 例如:
// import { createApp } from 'vue';
// import App from './App.vue';
//
// const app = createApp(App);
// app.mount('#app');
```

**代码解释**：

1.  `import browserClient from '@slardar/web';`
    -   默认导入的是中国 (CN) 区域的 SDK 实例。如果你的业务服务于海外用户，需要从特定子路径导入，例如：
        -   `import browserClient from '@slardar/web/sg';` // 新加坡
        -   `import browserClient from '@slardar/web/maliva';` // 美东
    -   请根据你的业务部署区域选择正确的入口。

2.  `browserClient('init', { bid: 'YOUR_BID' });`
    -   这是初始化函数，它告诉 SDK 你的应用是谁。`bid` 是**唯一且必需**的参数。
    -   `init` 只应被调用一次。重复调用会产生警告，并可能导致配置混乱。建议将初始化逻辑放在应用生命周期中只执行一次的地方。

3.  `browserClient('start');`
    -   这个函数会启动所有的自动监控功能，如 JS 错误、网络请求、性能指标等的采集。在调用 `start` 之前，SDK 不会进行任何数据上报。

## 第三步：验证上报

将代码部署到你的测试环境后，如何确认 Slardar 是否工作正常？

1.  **打开浏览器开发者工具**：进入“网络 (Network)”面板。
2.  **筛选上报请求**：在筛选框中输入 `slardar` 或上报接口的部分路径（通常包含 `monitor_web` 字样）。
3.  **观察数据包**：刷新页面或在页面上进行一些操作（如点击按钮、触发一个 API 请求），你应该能看到有数据被发送到 Slardar 的服务器。这些请求通常是 `POST` 请求，并且其 `payload` 中包含了加密后的监控数据。

或者，你也可以在开发环境中通过一个特殊的 `debug` 配置来查看原始上报数据：

```typescript
browserClient('init', {
  bid: 'YOUR_BID',
  debug: true, // 开启 Debug 模式
});
browserClient('start');
```

开启 `debug: true` 后，Slardar 不会真实上报数据，而是会在浏览器的控制台 (Console) 中打印出它采集到的所有原始日志。这对于开发阶段的验证非常有用。

> **注意**：`debug: true` **严禁**在生产环境中使用，因为它会暴露敏感信息并可能影响性能。

## 开箱即用的能力

一旦你完成了 `init` 和 `start`，Slardar 就已经开始在后台默默工作了。它会自动为你采集以下数据，无需任何额外配置：

-   **JS 错误**：任何未被 `try...catch` 的代码异常。
-   **资源加载错误**：如 `<img>`, `<script>`, `<link>` 加载失败。
-   **未捕获的 Promise 拒绝**。
-   **网络请求**：`fetch` 和 `XMLHttpRequest` 的状态和耗时。
-   **核心 Web 指标**：LCP, CLS, INP 等。
-   **白屏和页面冻结**。
-   **用户行为面包屑**：记录页面跳转、用户点击等，用于辅助错误排查。

你可以稍等几分钟，然后登录 Slardar 平台，在你的应用看板上应该就能看到这些数据的报表了。

## 常见问题排查

-   **控制台没有任何 Slardar 相关的输出或报错**
    -   **检查**：是否正确 `import` 了 `browserClient`？`init` 和 `start` 是否被成功调用？
    -   **尝试**：在 `init` 调用前后添加 `console.log` 来确认代码是否执行。

-   **Slardar 平台没有收到数据**
    -   **检查**：`bid` 是否正确填写？网络策略（CSP）是否阻止了上报请求？
    -   **检查**：浏览器开发者工具的网络面板中，是否有发往 Slardar 服务器的请求？如果请求状态是 `blocked` 或 `failed`，请查看失败原因。
    -   **确认**：是否在 `init` 后调用了 `start`？

-   **控制台出现 "Slardar has been initialized" 的警告**
    -   **原因**：`browserClient('init', ...)` 在应用中被执行了多次。
    -   **解决**：检查你的代码，确保初始化逻辑只在应用生命周期的最开始执行一次。例如，在 React/Vue 的根组件挂载前，或在一个单例模块中。
