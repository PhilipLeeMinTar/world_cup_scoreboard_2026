# EdenX 最佳实践配置指南

本文档总结了 EdenX 项目的各种功能配置最佳实践,帮助开发者快速了解如何为项目启用和配置各种功能。

## 目录

- [功能概览](#功能概览)
- [BFF (Backend For Frontend)](#bff-backend-for-frontend)
- [新增页面入口 (Entry)](#新增页面入口-entry)
- [自定义 Web 服务器 (Server)](#自定义-web-服务器-server)
- [监控能力 (Slardar)](#监控能力-slardar)
- [微前端 (MicroFrontend)](#微前端-microfrontend)
- [国际化 (I18n)](#国际化-i18n)
- [静态站点生成 (SSG)](#静态站点生成-ssg)
- [中后台预设 (Admin)](#中后台预设-admin)
- [模板文件](#模板文件)

---

## 功能概览

EdenX v3 框架提供了丰富的功能插件,以下是支持的功能列表:

| 功能 | 参数值 | 说明 | 插件包 |
|------|--------|------|--------|
| BFF | bff | Backend For Frontend | `@edenx/plugin-bff` |
| Entry | entry | 新增页面入口 | - |
| Server | server | 自定义 Web 服务器 | `@edenx/server-runtime` |
| Slardar Web | slardar | 启用 Slardar 监控 | `@edenx/plugin-slardar` |
| MicroFrontend | microfe | 启用微前端支持 | `@edenx/plugin-garfish` |
| I18n | i18n | 启用国际化支持 | `@edenx/plugin-i18n` |
| SSG | ssg | 启用静态站点生成 | `@edenx/plugin-ssg` |
| Admin | admin | 启用中后台预设 | `@edenx/preset-admin` |

---

## BFF (Backend For Frontend)

### 功能说明

BFF 功能允许你在前端项目中创建后端 API 接口,基于 Gulux 框架实现,支持依赖注入、装饰器等特性。

### 前置要求

- ✅ 项目必须是 TypeScript 项目
- ✅ 需要存在 [`tsconfig.json`](tsconfig.json:1) 文件

### 安装依赖

```json
{
  "dependencies": {
    "@edenx/plugin-bff": "^版本号",
    "@edenx/plugin-gulux": "^版本号",
    "@gulux/gulux": "4.0.2"
  }
}
```

> 💡 `@edenx/plugin-bff` 和 `@edenx/plugin-gulux` 版本号应与 `@edenx/app-tools` 保持一致

### 配置步骤

#### 1. 更新 tsconfig.json

```json
{
  "compilerOptions": {
    "moduleResolution": "NodeNext",
    "module": "NodeNext",
    "target": "ES2017",
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "paths": {
      "@api/*": ["./api/lambda/*"]
    }
  }
}
```

#### 2. 配置插件

在 [`edenx.config.ts`](edenx.config.ts:1) 中注册插件:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { bffPlugin } from '@edenx/plugin-bff';
import { guluxPlugin } from '@edenx/plugin-gulux';

export default defineConfig({
  plugins: [
    bffPlugin(),
    guluxPlugin(),
  ],
});
```

#### 3. 项目结构

BFF 功能会创建以下目录结构:

```
api/
├── lambda/          # API 路由处理函数
│   ├── index.ts
│   └── user.ts
├── service/         # 业务逻辑服务
│   └── user.ts
└── config/          # 配置文件
    ├── config.default.ts
    ├── config.dev.ts
    ├── config.prod.ts
    └── plugin.default.ts
```

### 注意事项

- ⚠️ BFF 功能仅支持 TypeScript 项目
- ⚠️ 确保装饰器支持已正确配置
- ⚠️ **禁止在插件注册时添加配置参数**,所有配置应由用户按照文档自行配置

---

## 新增页面入口 (Entry)

### 功能说明

为 EdenX v3 项目添加新的入口点,支持框架模式和构建模式两种方式。

### 项目模式判断

通过 [`package.json`](package.json:1) 中是否存在 `@edenx/runtime` 依赖判断:

- 存在 `@edenx/runtime` → **框架模式** (使用文件路由)
- 不存在 → **构建模式** (使用传统 React 入口)

### 单入口 vs 多入口

**单入口项目标志**:
- 框架模式: 存在 `src/routes/` 目录
- 构建模式: 存在 `src/App.tsx` 或 `src/entry.tsx`

**多入口项目标志**:
- 框架模式: 存在 `src/*/routes/` 目录
- 构建模式: 存在 `src/*/App.tsx` 或 `src/*/entry.tsx`

### 配置步骤

#### 框架模式单入口重构

如果是单入口项目,需要先重构为多入口结构:

```bash
PACKAGE_NAME="main"  # 从 package.json 的 name 字段处理得到
ENTRY_NAME="new-entry"  # 用户输入的新入口名

# 创建现有入口目录并移动文件
mkdir -p "src/${PACKAGE_NAME}"
mv src/routes "src/${PACKAGE_NAME}/routes"
mv src/*.css "src/${PACKAGE_NAME}/"

# 创建新入口目录
mkdir -p "src/${ENTRY_NAME}/routes"
# 复制框架模式模板到新入口
```

#### 构建模式单入口重构

```bash
PACKAGE_NAME="main"
ENTRY_NAME="new-entry"

# 创建现有入口目录并移动文件
mkdir -p "src/${PACKAGE_NAME}"
mv src/App.tsx "src/${PACKAGE_NAME}/"
mv src/entry.tsx "src/${PACKAGE_NAME}/"
mv src/index.css "src/${PACKAGE_NAME}/"

# 创建新入口目录
mkdir -p "src/${ENTRY_NAME}"
# 复制构建模式模板到新入口
```

#### 多入口项目创建新入口

```bash
ENTRY_NAME="new-entry"

# 检查入口是否已存在
if [ -d "src/${ENTRY_NAME}" ] && [ "$(ls -A src/${ENTRY_NAME})" ]; then
  echo "错误: 入口 ${ENTRY_NAME} 已存在"
  exit 1
fi

# 创建新入口(根据项目模式选择对应模板)
```

### 注意事项

- ⚠️ 单入口重构和新入口创建应该一次性完成
- ⚠️ 构建模式入口文件名为 `entry.tsx`,不是 `index.tsx`
- ⚠️ 通过 [`package.json`](package.json:1) 依赖判断模式,无需读取源码文件

---

## 自定义 Web 服务器 (Server)

### 功能说明

为 EdenX v3 项目添加自定义 Web 服务器功能,支持中间件、请求处理等高级特性。

### 安装依赖

```json
{
  "devDependencies": {
    "@edenx/server-runtime": "^版本号",
    "typescript": "^latest",
    "ts-node": "^latest",
    "tsconfig-paths": "^latest"
  }
}
```

### 配置步骤

#### 1. 创建 server 目录

项目根目录下创建 `server/` 目录,包含以下文件:

```
server/
└── edenx.server.ts
```

#### 2. 更新 tsconfig.json

在 [`tsconfig.json`](tsconfig.json:1) 的 `include` 字段中添加 `"server"`:

```json
{
  "include": ["src", "server"]
}
```

### 注意事项

- ⚠️ 如果 server 目录已存在,不要覆盖
- ⚠️ 生成的中间件代码应该符合最佳实践
- ⚠️ 确保所有导入路径正确

---

## 监控能力 (Slardar)

### 功能说明

为 EdenX v3 项目启用 Slardar 监控能力,支持 SourceMap、Web 和 Server 三种类型。

### Slardar 类型

- **SourceMap** (默认): 仅上传 SourceMap,不需要额外依赖
- **Web**: 前端监控,需要安装 `@slardar/web`
- **Server**: 服务端监控,需要安装 `@slardar/base`

### 安装依赖

```json
{
  "dependencies": {
    "@edenx/plugin-slardar": "^版本号",
    // 根据类型选择:
    "@slardar/web": "^latest",        // Web 类型
    "@slardar/base": "^latest"        // Server 类型
  }
}
```

### 配置插件

在 [`edenx.config.ts`](edenx.config.ts:1) 中注册插件:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { slardarPlugin } from '@edenx/plugin-slardar';

export default defineConfig({
  plugins: [
    slardarPlugin(),
  ],
});
```

### 注意事项

- ⚠️ **禁止在插件注册时添加配置参数**
- ⚠️ 所有配置应由用户按照官方文档自行配置

---

## 微前端 (MicroFrontend)

### 功能说明

为 EdenX v3 项目启用微前端能力,基于 Garfish 框架实现。

### 安装依赖

```json
{
  "dependencies": {
    "@edenx/plugin-garfish": "^版本号"
  }
}
```

### 配置插件

在 [`edenx.config.ts`](edenx.config.ts:1) 中注册插件:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { garfishPlugin } from '@edenx/plugin-garfish';

export default defineConfig({
  plugins: [
    garfishPlugin(),
  ],
});
```

### 注意事项

- ⚠️ **禁止在插件注册时添加配置参数**
- ⚠️ 微前端功能是运行时依赖,需要正确配置

---

## 国际化 (I18n)

### 功能说明

为 EdenX v3 项目启用国际化功能,支持 Starling Intl 和 i18next 两种工具。

### I18n 工具类型

- **Starling Intl** (默认): 字节跳动内部国际化工具
- **i18next**: 开源国际化框架

### 安装依赖

```json
{
  "dependencies": {
    "@edenx/plugin-i18n": "^版本号",
    "react-i18next": "^latest",
    // 根据类型选择:
    "@ies/starling_intl": "^latest",  // Starling Intl
    "i18next": "^latest"              // i18next
  }
}
```

### 配置插件

在 [`edenx.config.ts`](edenx.config.ts:1) 中注册插件:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { i18nPlugin } from '@edenx/plugin-i18n';

export default defineConfig({
  plugins: [
    i18nPlugin(),
  ],
});
```

### 后续操作

配置完成后,运行以下命令进行配置:

```bash
npx edenx i18n config
```

### 注意事项

- ⚠️ 无论选择哪种类型,都需要安装 `react-i18next`
- ⚠️ **禁止在插件注册时添加配置参数** (如 `starlingIntl`、`defaultLocale`、`locales` 等)
- ⚠️ 所有配置应由用户通过 `npx edenx i18n config` 命令或按照文档自行配置

---

## 静态站点生成 (SSG)

### 功能说明

为 EdenX v3 项目启用静态站点生成功能,用于生成静态 HTML 页面。

### 安装依赖

```json
{
  "devDependencies": {
    "@edenx/plugin-ssg": "^版本号"
  }
}
```

### 配置插件和 output

在 [`edenx.config.ts`](edenx.config.ts:1) 中注册插件并配置 output:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { ssgPlugin } from '@edenx/plugin-ssg';

export default defineConfig({
  plugins: [
    ssgPlugin(),
  ],
  output: {
    ssg: true,
  },
});
```

### 注意事项

- ⚠️ SSG 是构建时功能,用于生成静态站点
- ⚠️ 需要同时配置插件和 output

---

## 中后台预设 (Admin)

### 功能说明

为 EdenX v3 项目启用中后台应用预设功能,支持 Arco Design 和 Semi Design 两种组件库。

### 组件库选择

- **Arco Design** (默认): 字节跳动开源组件库
- **Semi Design**: 抖音企业级应用设计系统

### 安装依赖

```json
{
  "dependencies": {
    "@edenx/preset-admin": "^版本号",
    // 根据组件库选择:
    "@arco-design/web-react": "^latest",  // Arco Design
    "@douyinfe/semi-ui": "^latest",       // Semi Design
    "@douyinfe/semi-icons": "^latest"     // Semi Design Icons
  }
}
```

### 配置步骤

#### 1. 创建配置文件

在 [`src/admin.config.ts`](src/admin.config.ts:1) 创建配置文件:

```typescript
export default {};
```

#### 2. 配置插件

**Arco Design (无参数)**:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { adminPreset } from '@edenx/preset-admin';

export default defineConfig({
  plugins: [
    adminPreset(),
  ],
});
```

**Semi Design (带参数)**:

```typescript
import { defineConfig } from '@edenx/app-tools';
import { adminPreset } from '@edenx/preset-admin';

export default defineConfig({
  plugins: [
    adminPreset({
      layout: {
        library: 'semi',
      },
    }),
  ],
});
```

### 注意事项

- ⚠️ Semi Design 需要额外的配置参数指定组件库
- ⚠️ 用户需要在 [`src/admin.config.ts`](src/admin.config.ts:1) 中配置中后台相关设置

---

## 模板文件

### 构建模式入口模板

#### App.tsx

```typescript
import "./index.css";

const App = () => {
  return (
    <div className="container-box">
      <h1>Welcome to EdenX</h1>
    </div>
  );
};

export default App;
```

#### entry.tsx

```typescript
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const rootDOM = document.getElementById('root');
if (rootDOM) {
  ReactDOM.createRoot(rootDOM).render(<App />);
}
```

#### index.css

```css
.container-box {
  padding: 20px;
}
```

### 框架模式入口模板

#### routes/layout.tsx

```typescript
import { Outlet } from '@edenx/runtime/router';

const Layout = () => {
  return (
    <div>
      <Outlet />
    </div>
  );
};

export default Layout;
```

#### routes/page.tsx

```typescript
import { Helmet } from "@edenx/runtime/head";
import "./index.css";

const Index = () => {
  return (
    <div className="container-box">
      <Helmet>
        <link rel="icon" type="image/x-icon" href="..." />
      </Helmet>
      <main>
        <h1>Welcome to EdenX</h1>
      </main>
    </div>
  );
};

export default Index;
```

#### routes/index.css

```css
.container-box {
  padding: 20px;
}
```

### Server 模板

#### server/edenx.server.ts

```typescript
import {
  type MiddlewareHandler,
  defineServerConfig
} from '@edenx/server-runtime';

const renderTiming: MiddlewareHandler = async (c, next) => {
  const start = Date.now();
  await next();
  console.log('render-timing', Date.now() - start);
};

const requestTiming: MiddlewareHandler = async (c, next) => {
  const start = Date.now();
  await next();
  console.log('request-timing', Date.now() - start);
};

export default defineServerConfig({
  middlewares: [
    {
      name: 'request-timing',
      handler: requestTiming,
    },
  ],
  renderMiddlewares: [
    {
      name: 'render-timing',
      handler: renderTiming,
    },
  ],
  plugins: [],
});
```

### BFF 模板

#### api/lambda/index.ts

```typescript
import { useReq } from '@edenx/plugin-gulux/runtime';

export default async () => Promise.resolve({
   hello: 'world',
});

export const post = async () => {
   const request = useReq();
   const { header, body: payload } = request;
   // 处理 POST 请求逻辑
   return Promise.resolve({
      hello: 'world',
      payload,
   });
};
```

#### api/lambda/user.ts

```typescript
import { Api, Get, useInject } from '@edenx/plugin-gulux/runtime';
import UserService from '../service/user';

export const getUserInfo = Api(Get('/user'), async () => {
   const userService = useInject(UserService);
   const result = await userService.getInfo();
   return result;
});
```

#### api/service/user.ts

```typescript
import { Injectable } from '@gulux/gulux';

@Injectable()
export default class UserService {
   public async getInfo() {
      return Promise.resolve({
         name: 'edenx',
         email: 'edenx@bytedance.com',
      });
   }
};
```

#### api/config/config.default.ts

```typescript
import type { ApplicationConfig } from '@gulux/gulux';

export default {
  name: 'app',
  psm: 'edenx.http.example',
  applicationHttp: {},
} as ApplicationConfig;
```

#### api/config/config.dev.ts

```typescript
export default {};
```

#### api/config/config.prod.ts

```typescript
export default {};
```

#### api/config/plugin.default.ts

```typescript
export default {
  'application-http': {
    enable: true,
  },
  edenx: {
    enable: true,
    package: '@edenx/plugin-gulux/plugin',
  },
};
```

---

## 通用最佳实践

### 1. 版本管理

- 所有 `@edenx/*` 插件的版本应与 `@edenx/app-tools` 保持一致
- 第三方依赖使用最新稳定版本 (`npm view <package> version`)

### 2. 配置原则

- ✅ 只注册插件,不添加配置参数
- ✅ 配置由用户按照官方文档自行添加
- ✅ 使用工具命令辅助配置 (如 `npx edenx i18n config`)

### 3. 项目结构

- 保持清晰的目录结构
- 单入口项目应先重构为多入口再添加新功能
- 避免目录冲突和文件覆盖

### 4. 类型安全

- 优先使用 TypeScript
- 确保类型定义正确导入
- 配置好装饰器和路径别名

### 5. 错误处理

- 检查功能是否已启用,避免重复配置
- 验证目录和文件是否存在
- 提供清晰的错误提示信息

---

## 总结

EdenX v3 提供了完善的插件体系和最佳实践指南,开发者应:

1. 根据项目需求选择合适的功能
2. 按照文档步骤正确配置
3. 遵循最佳实践原则
4. 保持代码质量和项目结构清晰

更多详细信息请参考 [EdenX 官方文档](https://edenx.bytedance.net)。
