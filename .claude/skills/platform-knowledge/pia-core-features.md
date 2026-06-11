# PIA 核心功能

> 本文档详细介绍 PIA 的核心功能和性能优化特性

## 一、性能优化功能

### 1. Prefetch (数据预取)

**功能描述**:
在页面加载前预先请求数据,减少首屏渲染时间。

**适用场景**:
- 首屏渲染依赖于 API 请求
- 数据加载时间较长的页面
- 需要优化 FCP/LCP 的场景

**使用方式**:

```typescript
// src/pages/index/worker.ts
export async function prefetch(context) {
  // 预取数据
  const data = await fetch('/api/data').then(res => res.json());

  return {
    data
  };
}
```

**工作流程**:
1. 用户点击入口时,客户端触发 prefetch
2. PIA Worker 在后台执行数据请求
3. 页面打开时,数据已经ready,直接渲染

**性能收益**:
- 减少首屏请求等待时间
- FCP 提升 30-50%
- 用户体验更流畅

### 2. NSR (Native Side Rendering)

**功能描述**:
在客户端侧预渲染页面,实现页面内容"直出"。

**适用场景**:
- 内容对时效性不敏感
- 有明确的前置入口
- 需要极致首屏体验

**使用方式**:

```typescript
// src/pages/index/worker.ts
export async function nsr(context) {
  // 获取数据
  const data = await fetch('/api/data').then(res => res.json());

  // 返回渲染所需数据
  return {
    props: { data }
  };
}
```

**工作流程**:
1. 用户在前置页面时,触发 NSR
2. PIA Worker 获取数据并渲染 HTML
3. 用户打开页面时,直接展示预渲染的 HTML
4. 完成 hydration 后页面可交互

**性能收益**:
- 页面秒开,FCP 接近 0
- 大幅提升用户感知性能
- 降低服务端压力

**与 SSR 的区别**:
| 对比项 | NSR | SSR |
|--------|-----|-----|
| 渲染位置 | 客户端 | 服务端 |
| 触发时机 | 前置页面 | 页面请求时 |
| 服务器压力 | 低 | 高 |
| SEO | 不支持 | 支持 |

### 3. Streaming NSR

**功能描述**:
流式渲染优化,边获取数据边渲染,进一步提升性能。

**适用场景**:
- 页面内容较多
- 有多个独立数据源
- 需要渐进式渲染

**使用方式**:

```typescript
export async function nsr(context) {
  // 返回 stream
  return {
    stream: true,
    render: async function* () {
      // 先渲染骨架屏
      yield { skeleton: true };

      // 获取数据并渲染
      const data = await fetchData();
      yield { props: { data } };
    }
  };
}
```

### 4. Snapshot (快照)

**功能描述**:
保存首次渲染的 HTML,第二次打开直接复用。

**适用场景**:
- 页面内容相对稳定
- 二次打开场景较多
- 需要优化二跳体验

**工作原理**:
1. 首次打开页面,正常渲染
2. 渲染完成后,保存 HTML 快照
3. 第二次打开时,直接使用快照
4. 后台异步更新快照

**性能收益**:
- 二次打开速度提升 50-80%
- 减少重复渲染开销
- 降低服务器请求

### 5. HTML Preload (HTML 预加载)

**功能描述**:
预加载页面 HTML 模板,加速首屏渲染。

**使用配置**:

```javascript
// pia.config.js
module.exports = {
  htmlPreload: {
    enabled: true,
    pages: ['index', 'detail']
  }
};
```

### 6. Prefetch Segmenting (预取分段)

**功能描述**:
将预取过程分段执行,优化内存使用。

**适用场景**:
- 预取数据量较大
- 多个独立数据源
- 需要控制并发

**配置示例**:

```typescript
export async function prefetch(context) {
  return {
    segments: [
      { key: 'user', fetch: () => fetchUser() },
      { key: 'posts', fetch: () => fetchPosts() }
    ]
  };
}
```

### 7. Resources Warmup (资源预热)

**功能描述**:
预热静态资源,提升加载速度。

**包括**:
- JS 文件预加载
- CSS 文件预加载
- 图片资源预热
- 字体文件预热

### 8. Resource Preload (资源预加载)

**功能描述**:
使用 link preload 优化资源加载优先级。

**配置方式**:

```javascript
// pia.config.js
module.exports = {
  performance: {
    preload: {
      js: true,
      css: true,
      fonts: ['main.woff2']
    }
  }
};
```

### 9. Code Cache (代码缓存)

**功能描述**:
缓存编译后的 JavaScript 代码,减少解析时间。

**性能收益**:
- 减少 30-50% 的脚本执行时间
- 降低 CPU 使用率
- 提升页面加载速度

**启用方式**:

```javascript
// pia.config.js
module.exports = {
  codeCache: {
    enabled: true
  }
};
```

### 10. Dynamic Hydration (动态注水)

**功能描述**:
按需注水,减少初始 JavaScript 执行时间。

**适用场景**:
- 页面组件较多
- 部分组件首屏不可见
- 需要优化 TTI

**使用方式**:

```typescript
import { lazy } from 'react';

// 懒加载组件
const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <div>
      <Header />  {/* 立即注水 */}
      <Suspense fallback={<Loading />}>
        <HeavyComponent />  {/* 延迟注水 */}
      </Suspense>
    </div>
  );
}
```

## 二、构建功能

### 1. 基础构建

**支持的功能**:
- TypeScript 编译
- JSX/TSX 转换
- CSS 处理
- 静态资源处理
- 代码压缩
- Tree Shaking

### 2. Builder (构建器)

**支持的构建器**:
- **Webpack** (默认)
- **Rspack** (更快的构建速度)

**切换构建器**:

```javascript
// pia.config.js
module.exports = {
  builder: 'rspack'  // 或 'webpack'
};
```

### 3. 代码分割

**自动代码分割**:
- 页面级别自动分割
- 路由懒加载
- 动态 import

**自定义分割策略**:

```javascript
// pia.config.js
module.exports = {
  optimization: {
    splitChunks: {
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    }
  }
};
```

### 4. CSS 解决方案

**支持的方案**:
- **CSS Modules** (推荐)
- **Less**
- **Sass/Scss**
- **PostCSS**
- **Styled Components**

**CSS Modules 使用**:

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

### 5. TypeScript 支持

**完整的 TypeScript 支持**:
- 类型检查
- 自动补全
- 类型声明生成
- TSX 语法支持

**推荐配置**:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "node",
    "jsx": "preserve",
    "strict": true,
    "esModuleInterop": true,
    "types": ["@piajs/kit/client"]
  }
}
```

### 6. 环境变量

**使用环境变量**:

```javascript
// .env.development
REACT_APP_API_URL=https://dev-api.example.com

// .env.production
REACT_APP_API_URL=https://api.example.com
```

**代码中使用**:

```typescript
const apiUrl = process.env.REACT_APP_API_URL;
```

### 7. Alias (别名)

**配置路径别名**:

```javascript
// pia.config.js
module.exports = {
  alias: {
    '@': './src',
    '@components': './src/components',
    '@utils': './src/utils'
  }
};
```

### 8. Proxy (代理)

**开发环境代理**:

```javascript
// pia.config.js
module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'https://dev-api.example.com',
        changeOrigin: true
      }
    }
  }
};
```

### 9. Mock 数据

**Mock 配置**:

```javascript
// config/mock/api.js
module.exports = {
  'GET /api/user': {
    name: 'John Doe',
    age: 30
  },
  'POST /api/login': (req, res) => {
    res.json({ token: 'mock-token' });
  }
};
```

## 三、工程化功能

### 1. 约定式路由

**目录结构即路由**:
```
src/pages/
  ├── index/          → /index
  ├── about/          → /about
  └── user/
      ├── [id]/       → /user/:id
      └── profile/    → /user/profile
```

### 2. 静态资源处理

**支持的资源类型**:
- 图片: png, jpg, gif, svg, webp
- 字体: woff, woff2, ttf
- 其他: json, txt

**导入方式**:

```typescript
import logo from './logo.png';
import icon from './icon.svg?component';  // SVG 作为组件
```

### 3. SVG 处理

**多种导入方式**:

```typescript
// 作为 URL
import iconUrl from './icon.svg';

// 作为 React 组件
import { ReactComponent as Icon } from './icon.svg';

// 或使用查询参数
import Icon from './icon.svg?component';
```

### 4. HMR (热更新)

**自动启用**:
- 代码修改后自动刷新
- 保持组件状态
- 快速反馈

### 5. REM 适配

**移动端适配**:

```javascript
// pia.config.js
module.exports = {
  rem: {
    enabled: true,
    rootValue: 75,
    unitPrecision: 5,
    propList: ['*']
  }
};
```

### 6. Browserslist

**浏览器兼容配置**:

```javascript
// package.json
{
  "browserslist": [
    "> 1%",
    "last 2 versions",
    "not dead",
    "iOS >= 9",
    "Android >= 5"
  ]
}
```

## 四、调试工具

### 1. pia.dev

**功能**:
- PC 浏览器调试移动页面
- 支持 Prefetch/NSR 调试
- 实时预览
- 网络请求查看

**使用方式**:
1. 启动开发服务器: `pnpm dev`
2. 命令行输入: `p` + Enter
3. 自动打开 pia.dev

### 2. PIA Console

**功能**:
- 查看运行时状态
- 监控性能指标
- 查看 Worker 日志
- 调试客户端能力

### 3. HDT (Hybrid Debug Tool)

**功能**:
- Worker 断点调试
- 日志查看
- 网络请求监控
- 性能分析

### 4. Slardar (监控)

**功能**:
- 性能监控
- 错误上报
- 用户行为追踪
- 自定义埋点

**集成方式**:

```javascript
// pia.config.js
module.exports = {
  slardar: {
    bid: 'your-bid',
    enabled: true
  }
};
```

### 5. Rsdoctor (构建分析)

**功能**:
- 构建性能分析
- 包大小分析
- 依赖关系可视化
- 优化建议

**启用方式**:

```bash
RSDOCTOR=true pnpm build
```

## 五、插件系统

### 官方插件

- **@piajs/plugin-react** - React 支持
- **@piajs/plugin-preact** - Preact 支持
- **@piajs/plugin-typescript** - TypeScript 支持
- **@piajs/plugin-less** - Less 支持
- **@piajs/plugin-sass** - Sass 支持

### 自定义插件

**创建插件**:

```javascript
// my-plugin.js
module.exports = {
  name: 'my-plugin',
  setup(api) {
    // 监听构建事件
    api.onBuildStart(() => {
      console.log('Build started');
    });

    // 修改配置
    api.modifyConfig((config) => {
      return {
        ...config,
        // 自定义配置
      };
    });
  }
};
```

**使用插件**:

```javascript
// pia.config.js
module.exports = {
  plugins: [
    './my-plugin.js',
    ['some-plugin', { option: 'value' }]
  ]
};
```

## 相关文档

- 官方性能优化文档: https://pia.bytedance.net/guide/advanced-features/
- 构建配置文档: https://pia.bytedance.net/guide/compilation/
- 插件开发文档: https://pia.bytedance.net/plugin/
- API 文档: https://pia.bytedance.net/api/
