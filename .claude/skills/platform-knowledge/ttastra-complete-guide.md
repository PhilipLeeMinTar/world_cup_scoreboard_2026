# TTAstra 完整技术指南

## 框架概述

TTAstra 是基于 EdenX 的 TikTok 业务 CSR 框架，融合了 TikTok 业务最佳实践和国际化多区域部署要求，与 TikTok monorepo 基建深度整合。

### 核心特性
- **多区域部署**：支持 row、eu、us、cn 等区域，自动处理静态资源前缀
- **合规集成**：内置 CSP、MSSDK、Source Map 上传等合规能力
- **通用能力**：i18n、slardar、tea、ByteCloud JWT 等开箱即用
- **微前端支持**：基于 Vmok 的微前端方案
- **Monorepo 集成**：与 Rush 生态深度结合

### 技术栈
- **基础框架**：EdenX 1.68.10
- **UI 框架**：React 18.2.0
- **类型系统**：TypeScript 4.9.5
- **构建工具**：Webpack 5.75.0
- **状态管理**：Zustand 4.5.4

## 项目初始化

### 使用 rush init-project
```bash
rush init-project
# 选择 '[CSR] TTAstra(Based on EdenX)' 模板
```

### 关键配置项
- **packageName**：项目名称，格式：`{VC}_{name}_web`
- **BFF 需求**：按需开启
- **项目类型**：internal（内网）/ external（外网）
- **部署区域**：row、eu、us、cn
- **依赖方式**：workspace（推荐）/ fixed version

## 配置系统

### 配置文件结构
```typescript
// solution.config.ts
import { defineConfig } from '@ttastra/core';

export default defineConfig({
  deploy: {
    isInternalApp: true,           // 项目类型
    vgeos: ['row', 'eu', 'us'],    // 部署区域
    baseUrl: '/my-project',        // 路由前缀
    domains: ['www.tiktok.com'],   // 域名配置
  },
  compliance: {
    hasCSPRequirement: true,       // CSP 合规
    hasLoginBehavior: true,        // 登录行为
    useMSSDK: {                    // MSSDK 配置
      aid: 1000,
      mode: 'login_mode',
    },
  },
  capabilities: {
    i18n: { /* i18n 配置 */ },
    slardar: { bid: 'your-bid' },
    tea: true,
    bytecloudJwt: true,
  },
  router: {
    useConfigBasedRoutes: true,    // 配置式路由
  },
  bff: {
    enableHandleWeb: true,         // BFF 一体化
  },
  vmok: {
    configPath: './vmok.config.json',
  },
});
```

### 核心配置模块

#### 1. 部署配置 (deploy)
```typescript
interface DeployConfig {
  isInternalApp?: boolean;           // 内网/外网项目
  vgeos?: VGeo[];                   // 部署区域：row, eu, us, cn
  baseUrl?: string;                 // 路由前缀
  domains?: string[];               // 域名配置
  deployPlatform?: 'goofy-web' | 'goofy-node' | 'tce';
}
```

#### 2. 合规配置 (compliance)
```typescript
interface ComplianceConfig {
  hasCSPRequirement?: boolean;      // CSP 合规
  hasLoginBehavior?: boolean;       // 登录行为
  uploadSourceMapInTtpScm?: boolean; // Source Map 上传
  useMSSDK?: boolean | MSSDKConfig;  // MSSDK 接入
}
```

#### 3. 通用能力配置 (capabilities)
```typescript
interface CapabilitiesConfig {
  i18n?: I18nConfig;               // 国际化
  slardar?: SlardarConfig;         // 监控
  tea?: boolean;                   // 用户行为
  bytecloudJwt?: boolean | ByteCloudJwtConfig; // 认证
}
```

## 路由系统

### 约定式路由（默认）
```
src/
└── routes/
    ├── layout.tsx          // 根布局
    ├── page.tsx           // 首页
    ├── dashboard/
    │   └── page.tsx       // /dashboard
    └── projects/
        ├── layout.tsx     // /projects 布局
        ├── page.tsx       // /projects
        └── [id]/
            └── page.tsx   // /projects/:id
```

### 配置式路由
```typescript
// solution.config.ts
export default defineConfig({
  router: {
    useConfigBasedRoutes: true,
  },
});

// src/App.tsx
import { AppRouter, Outlet } from '@ttastra/core/runtime/router';

const App = () => {
  return (
    <AppRouter
      routes={[
        {
          path: '/',
          element: <MainLayout><Outlet /></MainLayout>,
          children: [
            { index: true, element: <HomePage /> },
            { path: 'dashboard', element: <Dashboard /> },
            { path: 'projects', element: <Projects /> },
          ],
        },
      ]}
    />
  );
};
```

### 路由组件
```typescript
import { Link, useNavigate, useLocation, useParams } from '@ttastra/core/runtime/router';

// 导航链接
<Link to="/dashboard">前往仪表盘</Link>

// 编程式导航
const navigate = useNavigate();
navigate('/dashboard');

// 获取路由信息
const location = useLocation();
const { id } = useParams();
```

## 运行时系统

### 应用初始化
```typescript
// src/entry.ts
import { initApp, InitAppOptions } from '@ttastra/core/runtime';
import { createRoot } from '@ttastra/core/runtime/react';
import App from './App';

const initOptions: InitAppOptions = {
  plugins: [], // 运行时插件
  slots: {    // 自定义组件
    Loading: LoadingComponent,
    ErrorBoundary: ErrorComponent,
  },
};

const Root = createRoot();
initApp(Root, initOptions);
export default App;
```

### 运行时插件
```typescript
import { LifecyclePlugin } from '@ttastra/core/runtime/plugins';

export class DemoPlugin extends LifecyclePlugin {
  extendPluginContext() {
    return { customData: 'value' };
  }
  
  extendBridge() {
    return { customMethod: () => {} };
  }
  
  async appWillMount(params) {
    console.log('App will mount');
  }
  
  async pageWillMount() {
    console.log('Page will mount');
  }
}
```

### 上下文系统
```typescript
import { useBridge } from '@ttastra/core/runtime';

function MyComponent() {
  const bridge = useBridge();
  // 使用插件提供的上下文和方法
  return <div>{bridge.customData}</div>;
}
```

## 通用能力

### 国际化 (i18n)
```typescript
// 配置
capabilities: {
  i18n: {
    mode: 'extract',
    namespaces: [{
      projectId: '25811',
      spaceId: '94131',
      spaceName: 'i18n_demo',
      apiKey: 'your-api-key',
    }],
  },
}

// 使用
import { i18n } from '@ttastra/core/runtime/i18n';

// 初始化
await i18n.init({ lng: 'en' });

// 使用翻译
const text = i18n.t('hello_world');
```

### 监控 (Slardar)
```typescript
// 配置
capabilities: {
  slardar: {
    bid: 'your-bid',
    perfsee: {
      project: 'your-project',
    },
  },
}

// 使用
import { actualFMP } from '@ttastra/core/runtime/slardar';

// 自定义性能指标
actualFMP('custom-metric', performance.now());
```

### 用户行为 (Tea)
```typescript
// 配置
capabilities: {
  tea: true,
}

// 使用
import { tea } from '@ttastra/core/runtime/tea';

// 上报事件
tea.report('user_click', { button: 'submit' });
```

### 认证 (ByteCloud JWT)
```typescript
// 配置
capabilities: {
  bytecloudJwt: true,
}

// 使用
import { useByteCloudJwt } from '@ttastra/core/runtime/bytecloud-jwt';

function MyComponent() {
  const { isLoggedIn, userInfo, redirectToLogin } = useByteCloudJwt();
  
  if (!isLoggedIn) {
    return <button onClick={redirectToLogin}>登录</button>;
  }
  
  return <div>欢迎，{userInfo.name}</div>;
}
```

## BFF 一体化

### 基础配置
```typescript
// solution.config.ts
export default defineConfig({
  bff: {
    enableHandleWeb: true,    // 处理 Web 请求
    prefix: '/api',           // API 前缀
    proxy: {                  // 代理配置
      '/api': 'https://backend.com',
    },
  },
});
```

### API 路由
```
api/
├── users.ts          // GET /api/users
├── users/
│   └── [id].ts       // GET /api/users/:id
└── auth/
    └── login.ts      // POST /api/auth/login
```

### API 实现
```typescript
// api/users.ts
export default async function handler(req: Request) {
  const users = await fetchUsers();
  return Response.json(users);
}

// api/users/[id].ts
export default async function handler(req: Request, { params }: { params: { id: string } }) {
  const user = await fetchUser(params.id);
  return Response.json(user);
}
```

## 微前端 (Vmok)

### 配置
```typescript
// solution.config.ts
export default defineConfig({
  vmok: {
    configPath: './vmok.config.json',
    dynamicModules: {
      url: 'https://your-goofy-project.com/vmok-config',
    },
  },
  router: {
    useDynamicRoutes: {
      parentPath: '/micro',
    },
  },
});
```

### 模块配置
```json
// vmok.config.json
{
  "modules": [
    {
      "name": "micro-app",
      "entry": "https://micro-app.com/remoteEntry.js",
      "routes": [
        { "path": "/micro/app", "component": "MicroApp" }
      ]
    }
  ]
}
```

### 模块使用
```typescript
import { useRemoteModule } from '@ttastra/core/runtime/vmok';

function MicroApp() {
  const { Module, loading, error } = useRemoteModule('micro-app');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <Module />;
}
```

## 开发工具

### 开发命令
```bash
# 启动开发服务器
rushx dev

# 构建生产版本
rushx build

# 运行测试
rushx test

# 类型检查
rushx _phase:type-check
```

### 开发配置
```typescript
// solution.config.ts
export default defineConfig({
  dev: {
    region: 'row',  // 开发时指定区域
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
});
```

## 部署配置

### 多区域部署
```typescript
export default defineConfig({
  deploy: {
    vgeos: ['row', 'eu', 'us'],
    domains: ['www.tiktok.com'],
    baseUrl: '/my-project',
  },
});
```

### 部署平台
```typescript
export default defineConfig({
  deploy: {
    deployPlatform: 'goofy-web',  // goofy-web | goofy-node | tce
  },
});
```

## 最佳实践

### 1. 项目结构
```
src/
├── routes/              # 页面路由
├── components/          # 通用组件
├── pages/              # 页面组件
├── api/                # BFF API
├── utils/              # 工具函数
├── hooks/              # 自定义 Hooks
├── types/              # 类型定义
└── entry.ts            # 应用入口
```

### 2. 组件开发
```typescript
// 使用 TypeScript 类型
interface ComponentProps {
  title: string;
  children: React.ReactNode;
}

export function MyComponent({ title, children }: ComponentProps) {
  return (
    <div>
      <h1>{title}</h1>
      {children}
    </div>
  );
}
```

### 3. 状态管理
```typescript
import { create } from 'zustand';

interface AppState {
  user: User | null;
  setUser: (user: User) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
```

### 4. 错误处理
```typescript
import { ErrorBoundary } from '@ttastra/core/runtime/components';

function App() {
  return (
    <ErrorBoundary fallback={<ErrorPage />}>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

## 常见问题

### 1. 配置不生效
- 检查配置文件路径是否为 `solution.config.ts`
- 重启开发服务器
- 清理构建缓存

### 2. 路由问题
- 确保路由配置正确
- 检查 basename 设置
- 验证路由组件导入

### 3. 构建失败
- 检查 TypeScript 类型错误
- 验证依赖版本兼容性
- 查看构建日志

### 4. 部署问题
- 确认部署区域配置
- 检查域名和路由配置
- 验证合规要求

## API 参考

### 核心 API
- `defineConfig(config)` - 定义配置
- `initApp(root, options)` - 初始化应用
- `useBridge()` - 获取插件上下文

### 路由 API
- `AppRouter` - 路由容器
- `Link` - 导航链接
- `useNavigate()` - 编程式导航
- `useLocation()` - 获取位置信息
- `useParams()` - 获取路由参数

### 通用能力 API
- `i18n` - 国际化
- `slardar` - 监控
- `tea` - 用户行为
- `useByteCloudJwt()` - 认证

### 微前端 API
- `useRemoteModule(name)` - 使用远程模块
- `loadRemoteModule(name)` - 加载远程模块

## 版本信息

- **当前版本**：1.16.0
- **EdenX 版本**：1.68.10
- **React 版本**：18.2.0
- **TypeScript 版本**：4.9.5

## 相关资源

- [TTAstra 官方文档](https://frontend.byteintl.net/csr-solution/)
- [EdenX 文档](https://edenx.bytedance.net/)
- [React 文档](https://react.dev/)
- [Rush 文档](https://rushjs.io/)
