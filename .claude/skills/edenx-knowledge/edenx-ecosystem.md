## 5. EdenX 生态系统

EdenX 不仅仅是一个独立的框架，它还拥有一个强大且不断发展的生态系统。这个生态系统由一系列官方和社区的工具、库和解决方案组成，旨在解决 Web 开发中的各种垂直领域问题，与 EdenX 框架本身形成了强大的协同效应。::cite[7]

### 5.1. 核心生态工具

EdenX 团队为不同的开发场景提供了专门的解决方案，这些工具与 EdenX 框架无缝集成，共同构成了现代 Web 工程体系。::cite[11]

*   **Rslib:** 如果你需要开发一个 npm 包（如组件、工具函数），Rslib 是推荐的解决方案。它与 EdenX Module 一脉相承，专注于库的构建和发布。::cite[7]
*   **EdenX Doc:** 用于快速搭建文档站点。它基于 Rspress，内置了默认的文档主题，支持 Markdown 和 MDX，并且构建性能极高。EdenX 自身的官方文档就是使用它构建的。::cite[7, 36]
*   **Rsbuild:** 作为 EdenX 的底层构建工具，Rsbuild 也可以独立用于开发 Vue、Solid 或 Svelte 应用，体现了其跨框架的通用能力。::cite[7]

### 5.2. 大型项目架构方案

对于大型、复杂的应用，EdenX 提供了成熟的微前端和微模块解决方案。

*   **Garfish (微前端):** 当你需要将多个独立的应用整合成一个大型单体应用时，推荐使用 Garfish。EdenX 对 Garfish 提供了开箱即用的支持，可以轻松实现微前端架构。::cite[7]
*   **Vmok (微模块):** Vmok 是一种更轻量级的代码组织方案，适用于在同一个应用内实现模块级别的拆分和独立开发。它解决了大型项目分而治之的问题。::cite[7, 33]

### 5.3. Monorepo 与构建分析

*   **EMO (Eden Monorepo):** 对于需要管理多个相关联项目的场景，EMO 是官方推荐的 Monorepo 解决方案。它可以帮助统一依赖管理、简化代码共享和规范化开发流程。::cite[7]
*   **Rsdoctor:** 这是一个用于深入分析构建过程和产物的工具。当遇到构建性能问题或需要优化打包结果时，Rsdoctor 可以提供详细的可视化报告，帮助开发者快速定位问题。::cite[7]

### 5.4. 生态关系图

下图清晰地展示了 EdenX 与其生态系统各个组件之间的关系：

```mermaid
graph TD
    subgraph A[EdenX 核心框架]
        direction LR
        A1[Web 应用开发]
    end

    subgraph B[核心生态工具]
        direction TB
        B1[Rslib<br>(npm 包开发)]
        B2[EdenX Doc<br>(文档站)]
        B3[Rsbuild<br>(Vue/Svelte应用)]
    end

    subgraph C[大型项目架构]
        direction TB
        C1[Garfish<br>(微前端)]
        C2[Vmok<br>(微模块)]
    end

    subgraph D[工程与效率]
        direction TB
        D1[EMO<br>(Monorepo)]
        D2[Rsdoctor<br>(构建分析)]
    end

    A -- 扩展场景 --> B
    A -- 应对复杂性 --> C
    A -- 提升工程效率 --> D

    style A fill:#f9f,stroke:#333,stroke-width:2px
```

### 5.5. 插件与集成

除了上述核心工具，EdenX 的生态还包括大量的官方插件和第三方集成，覆盖了国际化 (i18n)、中后台快速开发、数据监控 (Slardar)、遥测 (Tea) 等多个方面，极大地扩展了 EdenX 的能力边界。::cite[33, 34]
