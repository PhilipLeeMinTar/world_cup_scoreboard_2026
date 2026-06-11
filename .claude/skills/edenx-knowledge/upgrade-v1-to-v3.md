# EdenX v1 升级到 v3 完整指南

本文档详细说明了如何将 EdenX v1 项目升级到 v3 版本,涵盖所有迁移步骤、配置变更和代码修改。

## 目录

- [升级概览](#升级概览)
- [兼容性检查](#兼容性检查)
- [升级前准备](#升级前准备)
- [升级步骤](#升级步骤)
  - [1. Node.js 版本升级](#1-nodejs-版本升级)
  - [2. 依赖版本升级](#2-依赖版本升级)
  - [3. 类型定义文件](#3-类型定义文件)
  - [4. 配置文件迁移](#4-配置文件迁移)
  - [5. 入口文件迁移](#5-入口文件迁移)
  - [6. 导入路径迁移](#6-导入路径迁移)
  - [7. 插件迁移](#7-插件迁移)
  - [8. 自定义 Server 迁移](#8-自定义-server-迁移)
  - [9. CSS-in-JS 迁移](#9-css-in-js-迁移)
- [常见问题](#常见问题)
- [自动化迁移工具](#自动化迁移工具)

---

## 升级概览

### 主要变更

EdenX v3 带来了以下重大变更:

| 变更项目 | v1 | v3 | 影响范围 |
|---------|----|----|---------|
| **构建工具** | Webpack | Rspack | 所有项目 |
| **Node.js 版本** | >= 14 | >= 20 | 运行环境 |
| **配置文件** | 多处配置 | 集中式配置 | 配置结构 |
| **插件系统** | 自动加载 | 显式注册 | 插件使用 |
| **状态管理** | `@edenx/plugin-state` | 原生 Reduck | 状态相关代码 |
| **运行时配置** | `edenx.config.ts` | `src/edenx.runtime.ts` | 运行时配置 |
| **SSR 模式** | `string` (默认) | `stream` (默认) | SSR 项目 |

### 升级收益

- ✅ **构建提速** - Rspack 编译速度提升 5-10 倍
- ✅ **更好的 TypeScript 支持** - 完善的类型定义
- ✅ **统一的配置管理** - 更清晰的配置层次结构
- ✅ **更灵活的插件系统** - 显式的依赖管理
- ✅ **现代化的开发体验** - 更快的 HMR 和更好的开发工具

---

## 兼容性检查

在开始升级前,需要检查项目是否满足以下条件:

### 不支持迁移的依赖

以下依赖**无法**直接迁移到 v3,需要先移除或替换:

| 依赖包 | 说明 | 替代方案 |
|-------|------|---------|
| `@edenx/plugin-state-legacy` | 旧版状态管理 | 升级到 `@modern-js-reduck` |
| `@edenx/plugin-router-v5` | React Router v5 | 升级到 React Router v6 |
| `@ies/noah` | 旧版监控工具 | 使用 `@edenx/plugin-slardar` |

### React 版本要求

如果项目使用 EdenX 路由功能,React 版本必须 >= 18:

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
```

---

## 升级前准备

### 1. 备份代码

```bash
git add .
git commit -m "chore: 升级前备份"
git checkout -b feat/upgrade-to-v3
```

### 2. 确保项目可运行

```bash
# 安装依赖
npm install

# 确保项目可以正常启动
npm run dev

# 确保项目可以正常构建
npm run build
```

### 3. 记录自定义配置

如果项目有以下自定义配置,建议先记录下来:

- 自定义 Webpack 配置
- 自定义中间件
- 自定义插件配置
- 环境变量配置

---

## 升级步骤

### 1. Node.js 版本升级

EdenX v3 要求 Node.js >= 20。

#### 检查当前版本

```bash
node -v
```

#### 升级方式

**使用 nvm (推荐)**:

```bash
# 安装 Node.js 20
nvm install 20

# 切换到 Node.js 20
nvm use 20
```

**更新项目要求**:

修改 [`package.json`](package.json:1):

```json
{
  "engines": {
    "node": ">=20.0.0"
  }
}
```

更新 [`.nvmrc`](.nvmrc:1) (如果存在):

```
20
```

---

### 2. 依赖版本升级

#### 获取最新版本

```bash
npm view @edenx/app-tools@canary version
```

#### 更新所有 @edenx 依赖

将所有 `@edenx/*` 依赖升级到最新版本(使用精确版本号,不带 `^` 或 `~`):

```json
{
  "dependencies": {
    "@edenx/app-tools": "3.0.0",
    "@edenx/plugin-i18n": "3.0.0",
    "@edenx/plugin-bff": "3.0.0"
  },
  "devDependencies": {
    "@edenx/plugin-ssg": "3.0.0"
  }
}
```

#### 移除废弃依赖

删除以下依赖(如果存在):

```json
{
  "dependencies": {
    "@modern-js/builder-rspack-provider": "删除此行"
  }
}
```

---

### 3. 类型定义文件

#### 删除旧文件

如果存在以下文件,删除它们:

- `src/jupiter-app-end.d.ts` (旧版文件名)
- `api/edenx-server-env.d.ts`

#### 创建新文件

创建或更新 [`src/edenx-app-env.d.ts`](src/edenx-app-env.d.ts:1):

```typescript
/// <reference types='@edenx/app-tools/types' />
```

---

### 4. 配置文件迁移

配置文件迁移是升级过程中最复杂的部分。以下是详细的迁移规则。

#### 4.1 defineConfig 类型参数

移除所有类型参数:

```typescript
// ❌ v1
import { defineConfig } from '@edenx/app-tools';
export default defineConfig<'rspack'>({
  plugins: [/*...*/]
});

// ✅ v3
import { defineConfig } from '@edenx/app-tools';
export default defineConfig({
  plugins: [/*...*/]
});
```

#### 4.2 html 配置迁移

**html.appIcon**

```typescript
// ❌ v1 - 不再支持字符串形式
export default defineConfig({
  html: {
    appIcon: './src/assets/icon.png',
  },
});

// ✅ v3 - 必须使用对象形式
export default defineConfig({
  html: {
    appIcon: {
      icons: [{ src: './src/assets/icon.png', size: 180 }]
    }
  },
});
```

**html.xxxByEntries 迁移为函数**

```typescript
// ❌ v1
export default defineConfig({
  html: {
    metaByEntries: {
      foo: { description: 'TikTok' },
      bar: { description: 'TikTok Admin' }
    },
  },
});

// ✅ v3
export default defineConfig({
  html: {
    meta({ entryName }) {
      switch (entryName) {
        case 'foo':
          return { description: 'TikTok' };
        case 'bar':
          return { description: 'TikTok Admin' };
      }
    },
  },
});
```

**html.disableHtmlFolder**

```typescript
// ❌ v1
export default defineConfig({
  html: {
    disableHtmlFolder: true,
  },
});

// ✅ v3
export default defineConfig({
  html: {
    outputStructure: 'flat',
  },
});
```

#### 4.3 output 配置迁移

**overrideBrowserslist 迁移**

删除配置,创建 [`.browserslistrc`](.browserslistrc:1) 文件:

```
chrome >= 51
edge >= 15
firefox >= 54
safari >= 10
ios_saf >= 10
```

**disable/enable 配置迁移**

```typescript
// ❌ v1
export default defineConfig({
  output: {
    disableCssExtract: true,
    disableFilenameHash: true,
    disableMinimize: true,
    disableSourceMap: true,
    enableInlineScripts: true,
    enableInlineStyles: true,
  },
});

// ✅ v3
export default defineConfig({
  output: {
    injectStyles: true,      // 对应 disableCssExtract
    filenameHash: false,     // 对应 disableFilenameHash
    minify: false,           // 对应 disableMinimize 和 disableSourceMap
    inlineScripts: true,     // 对应 enableInlineScripts
    inlineStyles: true,      // 对应 enableInlineStyles
  },
});
```

**cssModuleLocalIdentName**

```typescript
// ❌ v1
export default defineConfig({
  output: {
    cssModuleLocalIdentName: '[path][name]__[local]-[hash:base64:6]',
  },
});

// ✅ v3
export default defineConfig({
  output: {
    cssModules: {
      localIdentName: '[path][name]__[local]-[hash:base64:6]',
    },
  },
});
```

**enableLatestDecorators**

```typescript
// ❌ v1
export default defineConfig({
  output: {
    enableLatestDecorators: true,
  },
});

// ✅ v3
export default defineConfig({
  source: {
    decorators: {
      version: '2022-03',
    },
  },
});
```

**disableNodePolyfill**

```typescript
// ❌ v1
export default defineConfig({
  output: {
    disableNodePolyfill: false,
  },
});

// ✅ v3
import { pluginNodePolyfill } from "@rsbuild/plugin-node-polyfill";

export default defineConfig({
  builderPlugins: [
    pluginNodePolyfill()
  ]
});
```

#### 4.4 source 配置迁移

```typescript
// ❌ v1
export default defineConfig({
  source: {
    resolveMainFields: ['custom', 'module', 'main'],
    resolveExtensionPrefix: '.web',
    moduleScopes: [/src/],
    enableCustomEntry: true,
  },
});

// ✅ v3
export default defineConfig({
  resolve: {
    mainFields: ['custom', 'module', 'main'],
    extensionPrefix: '.web',
  },
  // moduleScopes 和 enableCustomEntry 已废弃,直接删除
});
```

#### 4.5 tools 配置迁移

**Webpack 到 Rspack 迁移**

```typescript
// ❌ v1 - webpackChain
export default defineConfig({
  tools: {
    webpackChain(chain) {
      chain.devtool(false);
      return chain;
    },
  }
});

// ✅ v3 - bundlerChain (注意:不需要 return)
export default defineConfig({
  tools: {
    bundlerChain(chain) {
      chain.devtool(false);
    },
  }
});
```

```typescript
// ❌ v1 - webpack with ModuleFederationPlugin
export default defineConfig({
  tools: {
    webpack: (config, { webpack, appendPlugins }) => {
      appendPlugins([
        new webpack.container.ModuleFederationPlugin({
          name: 'app',
          filename: 'remoteEntry.js',
          exposes: {
            './Component': './src/Component',
          },
        }),
      ]);
      return config;
    },
  }
});

// ✅ v3 - rspack with ModuleFederationPlugin
export default defineConfig({
  tools: {
    rspack: (config, { rspack, appendPlugins }) => {
      appendPlugins([
        new rspack.container.ModuleFederationPlugin({
          name: 'app',
          filename: 'remoteEntry.js',
          exposes: {
            './Component': './src/Component',
          },
        }),
      ]);
      return config;
    },
  }
});
```

**devServer 配置迁移**

```typescript
// ❌ v1 - tools.devServer
export default defineConfig({
  tools: {
    devServer: {
      hot: true,
      https: true,
      proxy: { '/api': 'http://localhost:3000' },
      compress: true,
      headers: { 'X-Custom-Foo': 'bar' },
    },
  },
});

// ✅ v3 - dev 配置
export default defineConfig({
  dev: {
    hmr: true,              // 注意: hot 改为 hmr
    https: true,
    server: {
      proxy: { '/api': 'http://localhost:3000' },
      compress: true,
      headers: { 'X-Custom-Foo': 'bar' },
    },
  },
});
```

**before/after 中间件迁移**

```typescript
// ❌ v1
export default defineConfig({
  tools: {
    devServer: {
      before: [(req, res, next) => { console.log('before'); next(); }],
      after: [(req, res, next) => { console.log('after'); next(); }],
    },
  },
});

// ✅ v3
export default defineConfig({
  dev: {
    setupMiddlewares: [
      (middlewares, server) => {
        // before 使用 unshift
        middlewares.unshift((req, res, next) => {
          console.log('before');
          next();
        });
        // after 使用 push
        middlewares.push((req, res, next) => {
          console.log('after');
          next();
        });
      },
    ],
  },
});
```

#### 4.6 runtime 和 server 配置迁移

**runtime.router 和 runtime.state**

```typescript
// ❌ v1
export default defineConfig({
  runtime: {
    router: true,  // 直接删除
    state: true,   // 需要迁移到原生 Reduck (见第7步)
  },
});

// ✅ v3
export default defineConfig({
  // runtime.router 不再需要
  // runtime.state 迁移到原生 Reduck
});
```

**server.ssr 模式**

```typescript
// ❌ v1 - 默认为 string 模式
export default defineConfig({
  server: {
    ssr: true,
  },
});

// ✅ v3 - 显式设置 string 模式以保持旧行为
export default defineConfig({
  server: {
    ssr: {
      mode: 'string',
    },
  },
});
```

```typescript
// ❌ v1 - ssrByEntries
export default defineConfig({
  server: {
    ssrByEntries: {
      foo: true,
      bar: { /* 其他配置 */ },
    },
  },
});

// ✅ v3 - 每个 entry 显式设置 mode
export default defineConfig({
  server: {
    ssrByEntries: {
      foo: { mode: 'string' },
      bar: { mode: 'string', /* 其他配置 */ },
    },
  },
});
```

#### 4.7 dev 和 experiments 配置迁移

```typescript
// ❌ v1
export default defineConfig({
  dev: {
    port: 8080,
  },
  experiments: {
    lazyCompilation: true,
  },
});

// ✅ v3
export default defineConfig({
  server: {
    port: process.env.NODE_ENV === 'development' ? 8080 : undefined,
  },
  dev: {
    lazyCompilation: true,
  },
});
```

#### 4.8 插件配置迁移

**autoLoadPlugins**

```typescript
// ❌ v1 - 自动加载插件
export default defineConfig({
  autoLoadPlugins: true,
});

// ✅ v3 - 显式注册插件
import { appTools, defineConfig } from '@edenx/app-tools';
import { i18nPlugin } from '@edenx/plugin-i18n';
import { bffPlugin } from '@edenx/plugin-bff';

export default defineConfig({
  plugins: [
    appTools(),
    i18nPlugin(),
    bffPlugin(),
  ],
});
```

**appTools 插件**

```typescript
// ❌ v1
plugins: [
  appTools({
    bundler: 'rspack'
  })
]

// ✅ v3 - 不需要任何参数
plugins: [
  appTools()
]
```

---

### 5. 入口文件迁移

#### 5.1 构建模式入口迁移

**文件重命名**

将 `src/index.tsx` 重命名为 `src/entry.tsx`(内容保持不变):

```bash
mv src/index.tsx src/entry.tsx
```

#### 5.2 框架模式入口迁移 (Bootstrap 函数)

**迁移前** - [`src/index.tsx`](src/index.tsx:1):

```typescript
export default (App: React.ComponentType, bootstrap: () => void) => {
  initSomething().then(() => {
    bootstrap();
  });
};
```

**迁移后** - [`src/entry.tsx`](src/entry.tsx:1):

```typescript
import { createRoot } from '@edenx/runtime/react';
import { render } from '@edenx/runtime/browser';

const ModernRoot = createRoot();

async function beforeRender() {
  await initSomething();
}

beforeRender().then(() => {
  render(<ModernRoot />);
});
```

#### 5.3 App.config 迁移

将运行时配置提取到 [`src/edenx.runtime.ts`](src/edenx.runtime.ts:1)

**迁移前** - [`src/App.tsx`](src/App.tsx:1):

```typescript
function App() {
  return <div>App</div>;
}

App.config = {
  masterApp: {
    basename: '/',
    apps: [{ name: 'sub-app', entry: 'https://sub-app.example.com' }],
  }
};

export default App;
```

**迁移后**:

[`src/App.tsx`](src/App.tsx:1):
```typescript
function App() {
  return <div>App</div>;
}

export default App;
```

[`src/edenx.runtime.ts`](src/edenx.runtime.ts:1):
```typescript
import { defineRuntimeConfig } from '@edenx/runtime';

export default defineRuntimeConfig({
  masterApp: {
    basename: '/',
    apps: [{ name: 'sub-app', entry: 'https://sub-app.example.com' }],
  }
});
```

#### 5.4 App.init 迁移

将初始化逻辑转换为运行时插件

**迁移前** - [`src/App.tsx`](src/App.tsx:1):

```typescript
App.init = (runtimeContext) => {
  runtimeContext.extra.request = (url) => console.info('request url', url);
};
```

**迁移后** - [`src/edenx.runtime.ts`](src/edenx.runtime.ts:1):

```typescript
import type { RuntimePlugin } from '@edenx/runtime';
import { defineRuntimeConfig } from '@edenx/runtime';

const initRuntimePlugin = (): RuntimePlugin => ({
  name: 'init-runtime-plugin',
  setup: (api) => {
    api.onBeforeRender((runtimeContext) => {
      runtimeContext.extra.request = (url) => console.info('request url', url);
    });
  },
});

export default defineRuntimeConfig({
  plugins: [initRuntimePlugin()]
});
```

#### 5.5 routes/layout.tsx 迁移

如果在 `routes/layout.tsx` 中导出了 `config` 或 `init`，按照上述规则迁移到 [`src/edenx.runtime.ts`](src/edenx.runtime.ts:1)。

---

### 6. 导入路径迁移

#### 6.1 运行时导入路径映射

替换所有源代码文件中的导入路径:

| 旧路径 | 新路径 |
|--------|--------|
| `@edenx/runtime/server` | `@edenx/server-runtime` |
| `@edenx/runtime/gulux` | `@edenx/plugin-gulux/runtime` |
| `@edenx/runtime/gulu` | `@edenx/plugin-gulu/runtime` |
| `@edenx/runtime/garfish` | `@edenx/plugin-garfish/runtime` |
| `@edenx/runtime/i18n` | `@edenx/plugin-i18n/runtime` 或 `react-i18next` |
| `@edenx/runtime/intl` | `@edenx/plugin-i18n/runtime` |
| `@edenx/runtime/slardar` | `@edenx/plugin-slardar/runtime` |
| `@edenx/runtime/admin-config` | `@edenx/preset-admin/admin-config` |
| `@edenx/runtime/axios` | `@edenx/plugin-axios/runtime` |
| `@edenx/runtime/fetch` | `@edenx/plugin-fetch/runtime` |
| `@edenx/runtime/vmok` | `@edenx/plugin-vmok/runtime` |
| `@edenx/runtime/model` | `@modern-js-reduck/react` |

**不需要修改的路径**:
- `@edenx/runtime`
- `@edenx/runtime/router`
- `@edenx/runtime/head`
- `@edenx/runtime/loadable`

#### 6.2 BFF 路径特殊处理

`@edenx/runtime/bff` 需要根据项目依赖判断:

```typescript
// 如果项目使用 @edenx/plugin-gulux
import { useInject } from '@edenx/plugin-gulux/runtime';

// 如果项目使用 @edenx/plugin-gulu
import { useInject } from '@edenx/plugin-gulu/runtime';
```

#### 6.3 批量替换示例

使用编辑器的全局搜索替换功能:

```bash
# 使用 sed 批量替换 (macOS/Linux)
find src -type f \( -name "*.ts" -o -name "*.tsx" \) -exec sed -i '' 's|@edenx/runtime/server|@edenx/server-runtime|g' {} +
```

---

### 7. 插件迁移

#### 7.1 Garfish 微前端配置迁移

**迁移前** - `edenx.config.ts`:

```typescript
export default defineConfig({
  runtime: {
    masterApp: {
      basename: '/',
      apps: [{ name: 'sub-app', entry: 'https://sub-app.example.com' }],
    }
  }
});
```

**迁移后**:

[`edenx.config.ts`](edenx.config.ts:1):
```typescript
import { garfishPlugin } from '@edenx/plugin-garfish';

export default defineConfig({
  plugins: [garfishPlugin()],
  // runtime.masterApp 已移除
});
```

[`src/edenx.runtime.ts`](src/edenx.runtime.ts:1):
```typescript
import { defineRuntimeConfig } from '@edenx/runtime';

export default defineRuntimeConfig({
  masterApp: {
    basename: '/',
    apps: [{ name: 'sub-app', entry: 'https://sub-app.example.com' }],
  },
});
```

#### 7.2 Axios 配置迁移

**迁移前** - [`edenx.config.ts`](edenx.config.ts:1):

```typescript
export default defineConfig({
  runtime: {
    axios: {
      baseURL: 'https://api.example.com',
      timeout: 5000,
    }
  }
});
```

**迁移后** - [`src/edenx.runtime.ts`](src/edenx.runtime.ts:1):

```typescript
import { defineRuntimeConfig } from '@edenx/runtime';

export default defineConfig Runtimeconfig({
  axios: {
    baseURL: 'https://api.example.com',
    timeout: 5000,
  },
});
```

#### 7.3 i18n 插件迁移

i18n 插件迁移是最复杂的迁移之一。

**添加依赖**:

```json
{
  "dependencies": {
    "@edenx/plugin-i18n": "3.0.0",
    "i18next": "^25.6.3",
    "react-i18next": "^15.7.4"
  }
}
```

**迁移前** - 配置可能在两个地方:

[`edenx.config.ts`](edenx.config.ts:1):
```typescript
export default defineConfig({
  plugins: [i18nPlugin()],
  runtime: {
    i18next: {
      mode: 'online',
      starlingProjects: [
        { projectName: 'my-proj', apiKey: 'key', namespace: 'ns' }
      ],
      i18nOptions: {
        fallbackLng: 'en',
        supportedLngs: ['en', 'zh'],
      }
    }
  }
});
```

**迁移后**:

[`edenx.config.ts`](edenx.config.ts:1):
```typescript
import { i18nPlugin } from '@edenx/plugin-i18n';

export default defineConfig({
  plugins: [
    i18nPlugin({
      localeDetection: {
        languages: ['en', 'zh'],
        fallbackLanguage: 'en',
      },
      starling: {
        client: {
          apiKey: 'key',
          namespace: 'ns',
        },
        node: {
          projectName: 'my-proj',
        }
      },
    }),
  ],
});
```

**更新代码中的导入**:

```typescript
// ❌ v1
import { useTranslation } from '@edenx/runtime/i18n';
import runtimeI18n from '@edenx/runtime/i18n';

function Component() {
  const { t } = useTranslation();
  const handleSwitch = () => {
    runtimeI18n.changeLanguage({ locale: 'zh' });
  };
  return <button onClick={handleSwitch}>{t('key')}</button>;
}

// ✅ v3
import { useTranslation } from 'react-i18next';
import { useEdenXI18n } from '@edenx/plugin-i18n/runtime';

function Component() {
  const { t } = useTranslation();
  const { changeLanguage } = useEdenXI18n();
  
  const handleSwitch = () => {
    changeLanguage('zh'); // 直接传入字符串
  };
  return <button onClick={handleSwitch}>{t('key')}</button>;
}
```

#### 7.4 Slardar 监控插件迁移

EdenX v3 将 `@edenx/plugin-slardar-web` 和 `@edenx/plugin-slardar-server` 合并为统一的 `@edenx/plugin-slardar`。

**迁移前** - [`package.json`](package.json:1):

```json
{
  "dependencies": {
    "@edenx/plugin-slardar-web": "1.x",
    "@edenx/plugin-slardar-server": "1.x"
  }
}
```

**迁移后**:

[`package.json`](package.json:1):
```json
{
  "dependencies": {
    "@edenx/plugin-slardar": "3.0.0"
  }
}
```

[`edenx.config.ts`](edenx.config.ts:1):
```typescript
import { slardarPlugin } from '@edenx/plugin-slardar';

export default defineConfig({
  plugins: [
    slardarPlugin(),
  ],
});
```

#### 7.5 plugin-state 迁移到原生 Reduck

**添加依赖**:

```json
{
  "dependencies": {
    "@modern-js-reduck/store": "1.1.13",
    "@modern-js-reduck/react": "1.1.13",
    "@modern-js-reduck/plugin-devtools": "1.1.13",
    "@modern-js-reduck/plugin-effects": "1.1.13",
    "@modern-js-reduck/plugin-immutable": "1.1.13"
  }
}
```

**移除旧依赖和配置**:

```typescript
// ❌ v1 - edenx.config.ts
export default defineConfig({
  runtime: {
    state: {
      immer: true,
      effects: true,
      devtools: true
    }
  }
});
```

**创建 Store** - [`src/store/index.ts`](src/store/index.ts:1):

```typescript
import { createStore } from '@modern-js-reduck/store';
import type { StoreConfig } from '@modern-js-reduck/store';
import immerPlugin from '@modern-js-reduck/plugin-immutable';
import { plugin as effectsPlugin } from '@modern-js-reduck/plugin-effects';
import devtoolsPlugin from '@modern-js-reduck/plugin-devtools';

const isBrowser = typeof window !== 'undefined';

function createStoreConfig(): StoreConfig {
  const config: StoreConfig = {
    plugins: [
      immerPlugin,
      effectsPlugin,
      ...(isBrowser ? [devtoolsPlugin()] : []),
    ],
  };

  // SSR 状态恢复
  if (isBrowser) {
    const ssrData = (window as any)?._SSR_DATA;
    if (ssrData?.data?.storeState) {
      config.initialState = ssrData.data.storeState;
    }
  }

  return config;
}

export const store = createStore(createStoreConfig());
export type AppStore = typeof store;
```

**添加 Provider** - [`src/App.tsx`](src/App.tsx:1) 或 [`src/routes/layout.tsx`](src/routes/layout.tsx:1):

```typescript
import { Provider } from '@modern-js-reduck/react';
import { store } from './store';

export default function App() {
  return (
    <Provider store={store}>
      <YourApp />
    </Provider>
  );
}
```

**更新导入路径**:

```typescript
// ❌ v1
import { model, useModel } from '@edenx/runtime/model';

// ✅ v3
import { model, useModel } from '@modern-js-reduck/react';
```

#### 7.6 Tailwind CSS 插件迁移

**添加 PostCSS 配置** - [`postcss.config.cjs`](postcss.config.cjs:1):

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

**更新 Tailwind 配置** - [`tailwind.config.js`](tailwind.config.js:1):

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

---

### 8. 自定义 Server 迁移

如果项目使用了自定义 Server，需要更新中间件和 Hook 写法。

**迁移前** - [`server/index.ts`](server/index.ts:1):

```typescript
import type { ServerHook } from '@edenx/app-tools';

export const serverHooks: ServerHook = {
  beforeDev: async () => {
    console.log('beforeDev');
  },
  afterDev: async (server) => {
    server.app.use((req, res, next) => {
      console.log('custom middleware');
      next();
    });
  },
};
```

**迁移后** - [`server/edenx.server.ts`](server/edenx.server.ts:1):

```typescript
import {
  type MiddlewareHandler,
  defineServerConfig
} from '@edenx/server-runtime';

const customMiddleware: MiddlewareHandler = async (c, next) => {
  console.log('custom middleware');
  await next();
};

export default defineServerConfig({
  middlewares: [
    {
      name: 'custom-middleware',
      handler: customMiddleware,
    },
  ],
  plugins: [],
});
```

---

### 9. CSS-in-JS 迁移

如果项目使用 styled-components，需要更新配置。

**添加 Builder 插件** - [`edenx.config.ts`](edenx.config.ts:1):

```typescript
import { pluginStyledComponents } from '@rsbuild/plugin-styled-components';

export default defineConfig({
  builderPlugins: [
    pluginStyledComponents({
      ssr: true,
      displayName: true,
    }),
  ],
});
```

**更新依赖** (如果需要):

```json
{
  "dependencies": {
    "styled-components": "^6.0.0"
  },
  "devDependencies": {
    "@rsbuild/plugin-styled-components": "^1.0.0",
    "@types/styled-components": "^5.1.26"
  }
}
```

---

## 常见问题

### Q: 升级后构建报错 "Cannot find module '@edenx/runtime/xxx'"

**A:** 需要更新导入路径,参考 [导入路径迁移](#6-导入路径迁移) 章节。

### Q: TypeScript 报错 "Property 'xxx' does not exist"

**A:** 确保已更新类型定义文件,参考 [类型定义文件](#3-类型定义文件) 章节。

### Q: SSR 项目渲染模式发生变化

**A:** EdenX v3 的 SSR 默认模式从 `string` 改为 `stream`。如需保持旧行为,显式设置 `server.ssr.mode: 'string'`。

### Q: 状态管理不工作

**A:** 确保已完成 plugin-state 到原生 Reduck 的迁移,包括:
1. 创建 Store 配置
2. 添加 Provider 包装
3. 更新导入路径

### Q: 微前端子应用加载失败

**A:** 确保已将 `runtime.masterApp` 配置迁移到 `src/edenx.runtime.ts`。

### Q: 国际化切换不工作

**A:** i18n 插件的 API 发生变化,需要:
1. 更新配置到 `edenx.config.ts`
2. 使用 `react-i18next` 的 Hook
3. 使用 `useEdenXI18n()` 进行语言切换

### Q: Monorepo 项目如何升级?

**A:** 建议逐个子项目升级,每个项目独立迁移配置和依赖。

---

## 自动化迁移工具

EdenX 提供了自动化迁移工具,可以自动完成大部分升级步骤。

### 安装迁移插件

```bash
# 安装 tmates-cli
pnpm add -g @tmates/cli --registry=https://bnpm.byted.org/

# 添加 marketplace
tmates plugin marketplace add git@code.byted.org:webinfra/marketplace.git

# 安装迁移插件
tmates plugin install edenx-migrate-v3@webinfra-plugins
```

### 执行自动迁移

```bash
# 在项目目录运行
tmates

# 输入命令
/edenx-migrate-v3:migrate
```

### 自动化迁移包含的步骤

自动化工具会按顺序执行以下步骤:

1. ✅ 检查项目兼容性
2. ✅ 检测并升级 Node.js 版本要求
3. ✅ 升级所有 @edenx 依赖版本
4. ✅ 更新类型定义文件
5. ✅ 迁移配置文件 (edenx.config.ts)
6. ✅ 迁移入口文件
7. ✅ 迁移导入路径别名
8. ✅ 迁移 Garfish 配置
9. ✅ 迁移 Axios 配置
10. ✅ 迁移 i18n 插件
11. ✅ 迁移 Tailwind CSS 插件
12. ✅ 迁移 Slardar 插件
13. ✅ 迁移 plugin-tea 插件
14. ✅ 迁移 plugin-state 插件
15. ✅ 迁移自定义 Server
16. ✅ 迁移 CSS-in-JS
17. ✅ 格式化代码并提交
18. ✅ 安装依赖

### 断点续传

如果迁移过程中断,重新运行命令时会自动检测进度并继续:

```bash
# 再次运行迁移命令
tmates
/edenx-migrate-v3:migrate

# 工具会自动识别已完成的步骤,从断点继续执行
```

### 手动干预

部分复杂场景可能需要手动确认:

- Monorepo 中的公共配置迁移策略
- 高度自定义的 Web Server
- 复杂的插件配置

---

## 总结

EdenX v1 到 v3 的升级涉及多个方面的变更,主要包括:

### 必须升级的项目

- ✅ Node.js 版本 >= 20
- ✅ 所有 @edenx 依赖升级到 3.0.0
- ✅ 类型定义文件更新

### 配置文件变更

- ✅ defineConfig 类型参数移除
- ✅ html、output、source、tools 配置迁移
- ✅ runtime 配置迁移到 src/edenx.runtime.ts
- ✅ server.ssr 默认模式变更

### 代码变更

- ✅ 入口文件重命名和重构
- ✅ 导入路径更新
- ✅ 插件显式注册
- ✅ 状态管理迁移到原生 Reduck

### 构建工具

- ✅ Webpack → Rspack
- ✅ tools.webpack → tools.rspack
- ✅ tools.webpackChain → tools.bundlerChain

建议使用自动化迁移工具完成大部分升级步骤,仅在必要时进行手动调整。

升级后可获得更快的构建速度、更好的开发体验和更完善的类型支持。

---

**参考文档**:
- [EdenX 官方文档](https://edenx.bytedance.net)
- [Rspack 官方文档](https://rspack.dev)
- [Reduck 官方文档](https://github.com/modern-js-dev/reduck)
