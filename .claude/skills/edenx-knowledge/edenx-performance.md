# EdenX 性能优化策略

Web 应用的性能直接关系到用户体验和业务转化率。一个加载迅速、响应流畅的应用能更好地留住用户。EdenX 框架内置了多种开箱即用的性能优化能力，并提供了灵活的配置选项，帮助开发者轻松构建高性能应用。

本文档将聚焦于 EdenX 中的前端性能优化，主要涵盖两个核心领域：**代码分割**和**静态资源内联**。

## 代码分割 (Code Splitting)

代码分割是将庞大的 JavaScript 包（Bundle）拆分成多个小块（Chunk）的技术。这些小块可以按需加载或并行加载，从而减少应用首次加载时需要下载和解析的 JavaScript 体积，显著加快首屏渲染速度。

EdenX 提供了三种主流的代码分割方式。

### 1. 约定式路由自动分割

这是 EdenX 中最重要且最便捷的代码分割方式。当你使用框架推荐的**约定式路由**时（即通过 `src/routes/` 目录结构定义页面），**框架会自动为每个路由（页面）创建一个独立的代码块**。

**工作原理**：用户首次访问应用时，只需加载公共代码和当前访问页面的代码。当用户导航到新页面时，框架会自动加载新页面对应的代码块。这一切都是全自动的，开发者无需任何额外配置。

> **提示**：正因如此，我们强烈推荐在 EdenX 项目中采用约定式路由，以享受开箱即用的最佳性能实践。

### 2. 动态 `import()`

动态 `import()` 是 ECMAScript 标准提供的语法，允许你在代码的任何地方按需加载一个模块。这对于加载非首屏必须的、体积较大的组件或库非常有用。

**适用场景**：
- 点击后才显示的大型弹窗组件（如复杂的表单、图表）。
- 用户执行特定操作后才需要的功能模块（如导出 Excel 的库）。
- 基于用户权限或 A/B 测试加载的不同组件。

**用法**：
`import()` 函数返回一个 Promise，该 Promise resolve 为一个包含模块所有导出的对象。

```tsx
import { useState } from 'react';

function MyComponent() {
  const [Chart, setChart] = useState(null);

  const showChart = async () => {
    // 当点击按钮时，才去加载 ChartComponent 模块
    const chartModule = await import('./ChartComponent');
    setChart(chartModule.default);
  };

  return (
    <div>
      <button onClick={showChart}>显示图表</button>
      {Chart && <Chart />}
    </div>
  );
}
```

### 3. `React.lazy` 与 `Suspense`

`React.lazy` 是 React 官方提供的、与动态 `import()` 结合使用的 API，专门用于延迟加载 React 组件。它使得代码分割在组件层面的应用更加优雅和简单。

`React.lazy` 必须与 `React.Suspense` 组件配合使用。`Suspense` 允许你指定一个加载指示器（如一个 loading spinner），在懒加载组件的代码块下载和解析完成前显示。

**重要提示**：`React.lazy` 和 `Suspense` 的组合在传统的字符串 SSR 模式下不起作用。但是，它们在 **CSR（客户端渲染）** 和 **Streaming SSR（流式服务端渲染）**（React 18+）模式下能完美工作。

**用法**：

```tsx
import React, { Suspense, useState } from 'react';

// 使用 React.lazy 包装动态导入的组件
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));

function App() {
  const [show, setShow] = useState(false);

  return (
    <div>
      <button onClick={() => setShow(true)}>加载重型组件</button>
      {/* Suspense 包裹懒加载组件，并提供 fallback UI */}
      {show && (
        <Suspense fallback={<div>正在加载中...</div>}>
          <HeavyComponent />
        </Suspense>
      )}
    </div>
  );
}
```

## 静态资源内联 (Asset Inlining)

静态资源内联是将小的 CSS、JS 或图片等文件直接嵌入到 HTML 文件中，而不是通过外部链接（如 `<link>` 或 `<script>`）引用的技术。

**优势**：
- **减少 HTTP 请求数**：对于非常小的文件，内联可以避免一次独立的网络请求，从而减少网络延迟，加快页面渲染。

**劣势**：
- **增加 HTML 体积**：内联会使主 HTML 文档变大。
- **无法利用浏览器缓存**：内联的资源无法被浏览器或 CDN 单独缓存。如果多个页面都内联了同一个资源，用户每次访问都需要重新下载。

因此，资源内联是一种权衡。它**只适用于体积非常小且不常变化的资源**。

### 在 EdenX 中配置内联

EdenX 允许你通过 `output.inline` 配置来精细地控制哪些资源应该被内联。

**配置示例** (`edenx.config.ts`):

```ts
export default {
  output: {
    // 内联小于 10KB 的 JS 文件
    inlineScripts: true,

    // 内联小于 10KB 的 CSS 文件
    inlineStyles: true,
  },
  // 可以通过 performance.dataURI.limit 进一步自定义图片等资源的内联阈值
  performance: {
    // 小于 5KB 的图片、字体等资源将被转换为 Base64 格式内联
    dataURI: {
      limit: 5 * 1024, // 单位：字节
    },
  },
};
```

**默认行为**：
- `inlineScripts`: 默认开启。构建时会生成一个很小的运行时脚本并内联到 HTML 中。
- `inlineStyles`: 默认关闭。

## 常见问题与最佳实践 (FAQ)

**Q1: 我应该手动进行代码分割，还是完全依赖约定式路由？**

**A1**: 对于页面级别的分割，你应该 **100% 依赖约定式路由**的自动分割能力，这是最简单、最高效的方式。手动分割主要用于**页面内部的组件级别优化**。当你发现某个页面因为包含了一个非首屏必须的、体积巨大的组件（如一个复杂的第三方图表库）而导致加载缓慢时，就应该对这个组件使用 `React.lazy` 或动态 `import()` 进行手动分割。

**Q2: 资源内联的阈值应该设置多大比较合适？**

**A2**: 这没有一个绝对的“最佳值”，但一般建议保持一个较小的值。
-   **CSS/JS**: EdenX 默认的内联脚本阈值为 `10KB`，这是一个比较合理的起点。对于业务项目，可以根据实际情况调整。如果一个脚本或样式表在多个页面间共享，即使它很小，也可能不适合内联，因为外部引用可以更好地利用缓存。
-   **图片/字体**: `5KB` 到 `10KB` 是一个常见的阈值。太大的图片内联会导致 HTML 急剧膨胀，得不偿失。只对那些几乎每个页面都会用到的小图标（如 logo、小的装饰性图标）考虑内联。

**Q3: 如何分析我的应用打包产物，找到可以优化的点？**

**A3**: EdenX 集成了强大的构建分析工具 **Rsdoctor**。你可以在构建命令后添加 `--analyze` 标志，或者在 `edenx.config.ts` 中进行配置，来启动构建分析。
```bash
pnpm run build --analyze
```
构建完成后，Rsdoctor 会启动一个 web 服务，通过可视化的图表（如矩形树图）清晰地展示你的包体构成、模块依赖关系、重复引用的库等信息。通过分析这个报告，你可以轻松地找到体积过大的模块，或者被错误地打包进来的依赖，从而有针对性地进行代码分割或其他优化。

**Q4: 除了代码分割和资源内联，EdenX 还有哪些性能优化手段？**

**A4**: EdenX 的性能优化是一个体系，还包括：
-   **构建性能优化**：底层使用基于 Rust 的 **Rspack** 作为打包工具，相比 Webpack 有数量级的速度提升。
-   **Tree Shaking**：自动移除代码中未被使用的部分，减小打包体积。
-   **资源压缩**：自动对 JS、CSS、图片等资源进行压缩。
-   **预加载/预获取**：通过在 `<link>` 标签上添加 `rel="preload"` 或 `rel="prefetch"`，可以告诉浏览器提前加载未来可能需要的资源。EdenX 的路由系统也支持在用户悬停在链接上时就进行预加载。
-   **渲染模式优化**：如前文所述，选择合适的渲染模式（SSR, SSG, RSC）是更高维度的性能优化。
