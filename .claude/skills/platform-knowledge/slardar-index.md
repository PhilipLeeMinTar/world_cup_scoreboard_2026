# Slardar 前端知识库 - 索引

本套文档旨在为前端工程师提供一个关于 Slardar Web SDK 的全面、易懂的实践指南。无论你是初次接触 Slardar 的新人，还是希望深化理解的资深开发者，都可以在这里找到所需的知识。

**快速索引**
- [如何使用本套文档](#如何使用本套文档)
- [文档导航](#文档导航)
- [核心名词解释](#核心名词解释)

## 如何使用本套文档

我们建议你按照以下顺序阅读：

1.  **从 `简介` 开始**：了解 Slardar 是什么，以及它如何帮助我们提升应用质量。
2.  **阅读 `快速上手`**：跟随教程，在你的项目中完成 Slardar 的基本接入。
3.  **查阅 `API 参考`**：深入了解各个 API 的详细用法和配置选项。
4.  **参考 `React/Vue 集成`**：学习在主流框架中优雅地使用 Slardar。
5.  **遵循 `最佳实践`**：掌握高级技巧，让 Slardar 在你的团队中发挥最大价值。

## 文档导航

-   **[01-slardar-introduction.md](./01-slardar-introduction.md)**
    -   介绍 Slardar 平台及其在前端监控领域的核心价值。
-   **[02-slardar-web-quickstart.md](./02-slardar-web-quickstart.md)**
    -   提供一个完整的、从零开始的接入教程。
-   **[03-slardar-web-api-reference.md](./03-slardar-web-api-reference.md)**
    -   详细解释 `@slardar/web` SDK 提供的所有核心 API。
-   **[04-slardar-web-react-vue-integration.md](./04-slardar-web-react-vue-integration.md)**
    -   针对 React 和 Vue 项目的特定集成方案和代码示例。
-   **[05-slardar-web-best-practices.md](./05-slardar-web-best-practices.md)**
    -   分享在真实业务场景中行之有效的策略和技巧。

## 核心名词解释

在阅读文档时，你可能会遇到以下术语：

-   **APM (Application Performance Monitoring)**
    -   应用性能监控。Slardar 就是一个 APM 平台，它通过采集和分析数据，帮助我们监控和优化应用的性能、稳定性和用户体验。

-   **JS 错误 (JavaScript Error)**
    -   指在代码执行过程中发生的、未被捕获的 JavaScript 异常。这是导致页面功能异常或崩溃的主要原因之一。

-   **白屏 (White Screen)**
    -   指页面在加载或渲染过程中出现长时间的空白状态。这通常是由于资源加载失败、脚本执行错误或渲染阻塞引起的严重用户体验问题。

-   **页面冻结 (Page Freeze)**
    -   指页面长时间无响应，用户无法进行任何交互。这通常是由于主线程被长时间占用的同步计算或死循环导致的。

-   **核心 Web 指标 (Core Web Vitals)**
    -   Google 提出的一组用于衡量网页用户体验的关键性能指标，主要包括：
        -   **LCP (Largest Contentful Paint)**：最大内容绘制，衡量加载性能。
        -   **FID (First Input Delay)** / **INP (Interaction to Next Paint)**：首次输入延迟 / 下次绘制交互，衡量交互性。
        -   **CLS (Cumulative Layout Shift)**：累积布局偏移，衡量视觉稳定性。
