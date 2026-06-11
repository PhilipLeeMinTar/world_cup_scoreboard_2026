## 2. EdenX 功能特性

EdenX 作为一个现代化的 Web 开发框架，提供了一系列强大的功能特性，旨在提升开发效率、优化应用性能和改善开发体验。::cite[3]

### 2.1. 高性能构建

*   **Rust 构建引擎:** EdenX 深度集成了基于 Rust 的构建工具 Rspack，可以轻松切换，实现飞一般的编译速度。相比传统的 Webpack + Babel 构建，使用 Rspack 模式能带来数倍的性能提升。::cite[4] 例如，在 Rspack + SWC 模式下，构建速度比原 Eden 框架快 400%。::cite[4]
*   **SWC/esbuild 支持:** 除了 Rspack，EdenX 还支持使用 SWC 和 esbuild 进行代码转译和压缩，进一步提升构建效率。::cite[27]
*   **Rsbuild 升级:** EdenX 的底层构建工具已从 Modern.js Builder 升级为 Rsbuild，这是 EdenX 团队基于 Rspack 开发的构建工具，能够更好地支持 Rspack，并与社区保持同步发展。::cite[5]

### 2.2. 渐进式与一体化

*   **渐进式开发:** 允许开发者从一个最精简的项目模板开始，通过代码生成器逐步启用所需的功能插件，如路由、状态管理等，灵活定制解决方案。::cite[6]
*   **一体化开发体验:** 提供了开发与生产环境统一的 Web Server，支持客户端渲染 (CSR) 和服务器端渲染 (SSR) 的同构开发。同时，内置的 BFF (服务于前端的后端) 能力，让开发者可以通过函数即接口的形式快速开发 API 服务。::cite[6]

### 2.3. 开箱即用

*   **零配置启动:** 无需任何手动配置，即可获得对 TypeScript、JSX、CSS 的内置支持。::cite[2]
*   **内置工具链:** 集成了 ESLint、调试工具、自动化测试等，提供了全功能的开发体验。::cite[6]
*   **多种路由模式:** 支持自控路由和基于文件系统的约定式路由（包括嵌套路由），满足不同项目的需求。::cite[6]

### 2.4. 强大的插件系统

EdenX 拥有一个灵活且强大的插件系统，允许开发者在不同层面扩展框架能力：::cite[4]

*   **CLI 插件:** 可以处理 CLI 命令、自定义打包构建流程，例如修改 Rspack 或 PostCSS 的配置。
*   **Server 插件:** 可以处理服务端的生命周期和客户端请求，例如自定义 Node.js 服务器框架。
*   **Runtime 插件:** 可以处理 React 组件的渲染逻辑，例如修改运行时需要渲染的组件。

### 2.5. EdenX Module：专业的 npm 包开发工具

EdenX Module 是为开发 npm 包（如 React 组件库、工具库）而设计的专业工具。::cite[2]

*   **双模式构建:** 同时支持 `bundleless` (transform) 和 `bundle` 两种构建模式，仅需一套配置即可生成适用于不同场景的产物。::cite[2]
*   **极致性能:** 基于 esbuild 打造，无论是 `bundleless` 还是 `bundle` 模式，性能都远超传统的 Babel/Rollup 方案。::cite[2]
*   **组件调试与文档:** 集成了 Storybook 用于组件调试，并可以结合 EdenX Doc 自动生成文档。::cite[2]

### 2.6. 丰富的生态集成

EdenX 不仅自身功能强大，还与公司内外的优秀解决方案深度集成，形成了一个完整的生态系统。::cite[7]

*   **微前端/微模块:** 开箱即用支持 Garfish (微前端) 和 Vmok (微模块) 方案。::cite[7]
*   **Monorepo:** 推荐使用 EMO 进行 Monorepo 仓库管理。::cite[7]
*   **状态管理:** 兼容 Redux、Jotai、Zustand 等社区主流状态管理库。::cite[27]
*   **UI 库:** 完美支持 Arco Design 等组件库。::cite[40]

下面是一个展示 EdenX 功能亮点的图示：

```mermaid
graph LR
    subgraph EdenX 核心功能
        A[🚀 高性能构建<br>(Rspack/Rsbuild)] --> B{渐进式与一体化};
        B --> C[📦 开箱即用<br>(TS/ESLint/路由)];
        C --> D[🔌 强大的插件系统];
    end

    subgraph 周边工具与生态
        E[EdenX Module<br>(NPM包开发)]
        F[丰富生态<br>(Garfish/Vmok/EMO)]
    end

    D --> E;
    D --> F;

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#ccf,stroke:#333,stroke-width:2px
    style C fill:#cfc,stroke:#333,stroke-width:2px
    style D fill:#fcf,stroke:#333,stroke-width:2px
```
