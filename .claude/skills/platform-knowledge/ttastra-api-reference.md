# TTAstra API 参考

## 配置 API

### defineConfig
定义 TTAstra 配置的主函数。

```typescript
import { defineConfig } from '@ttastra/core';

export default defineConfig({
  // 配置选项
});
```

**参数：**
- `config: SolutionConfig` - 配置对象

**返回值：**
- `UserConfigExport<UserConfig<AppTools<'webpack'>>>` - EdenX 配置

### defineNonTTConfig
定义非 TikTok 项目的配置。

```typescript
import { defineNonTTConfig } from '@ttastra/core';

export default defineNonTTConfig({
  // 非 TikTok 配置
});
```

## 运行时 API

### initApp
初始化 TTAstra 应用。

```typescript
import { initApp, InitAppOptions } from '@ttastra/core/runtime';

const initOptions: InitAppOptions = {
  plugins: [],           // 运行时插件
  slots: {              // 自定义组件槽
    Loading: LoadingComponent,
    ErrorBoundary: ErrorComponent,
  },
};

initApp(Root, initOptions);
```

**参数：**
- `root: ReactRoot` - React 根节点
- `options: InitAppOptions` - 初始化选项

### useBridge
获取插件上下文桥接对象。

```typescript
import { useBridge } from '@ttastra/core/runtime';

function MyComponent() {
  const bridge = useBridge();
  // 使用插件提供的上下文和方法
  return <div>{bridge.customData}</div>;
}
```

**返回值：**
- `Bridge` - 桥接对象，包含插件提供的上下文和方法

## 路由 API

### AppRouter
配置式路由容器组件。

```typescript
import { AppRouter, Outlet } from '@ttastra/core/runtime/router';

<AppRouter
  routes={[
    {
      path: '/',
      element: <Layout><Outlet /></Layout>,
      children: [
        { index: true, element: <Home /> },
        { path: 'about', element: <About /> },
      ],
    },
  ]}
/>
```

**Props：**
- `routes: RouteObject[]` - 路由配置数组

### Link
导航链接组件。

```typescript
import { Link } from '@ttastra/core/runtime/router';

<Link to="/dashboard">前往仪表盘</Link>
<Link to="/projects" className="nav-link">项目管理</Link>
```

**Props：**
- `to: string` - 目标路径
- `className?: string` - CSS 类名
- `children: React.ReactNode` - 子元素

### useNavigate
编程式导航 Hook。

```typescript
import { useNavigate } from '@ttastra/core/runtime/router';

function MyComponent() {
  const navigate = useNavigate();
  
  const handleClick = () => {
    navigate('/dashboard');           // 导航到指定路径
    navigate('/projects?status=active'); // 带查询参数
    navigate(-1);                    // 返回上一页
    navigate(1);                     // 前进一页
  };
}
```

**返回值：**
- `(to: string | number, options?: NavigateOptions) => void` - 导航函数

### useLocation
获取当前路由位置信息。

```typescript
import { useLocation } from '@ttastra/core/runtime/router';

function MyComponent() {
  const location = useLocation();
  
  console.log(location.pathname); // '/dashboard'
  console.log(location.search);    // '?status=active'
  console.log(location.hash);      // '#section1'
}
```

**返回值：**
- `Location` - 位置对象，包含 pathname、search、hash 等

### useParams
获取路由参数。

```typescript
import { useParams } from '@ttastra/core/runtime/router';

// 路由配置：{ path: 'projects/:id', element: <ProjectDetail /> }
function ProjectDetail() {
  const { id } = useParams();
  return <div>Project ID: {id}</div>;
}
```

**返回值：**
- `Params` - 参数对象

### Outlet
子路由渲染组件。

```typescript
import { Outlet } from '@ttastra/core/runtime/router';

function Layout() {
  return (
    <div>
      <nav>导航栏</nav>
      <Outlet /> {/* 子路由将在这里渲染 */}
    </div>
  );
}
```

## 国际化 API

### i18n
国际化实例。

```typescript
import { i18n } from '@ttastra/core/runtime/i18n';

// 初始化
await i18n.init({
  lng: 'en',              // 当前语言
  fallbackLng: 'en',      // 回退语言
});

// 使用翻译
const text = i18n.t('hello_world');
const withParams = i18n.t('welcome_user', { name: 'John' });
```

**方法：**
- `init(options: I18nInitOptions): Promise<void>` - 初始化
- `t(key: string, options?: any): string` - 翻译文本

## 监控 API

### actualFMP
自定义性能指标上报。

```typescript
import { actualFMP } from '@ttastra/core/runtime/slardar';

// 上报自定义指标
actualFMP('custom-metric', performance.now());

// 带标签的指标
actualFMP('api-response-time', 150, {
  endpoint: '/api/users',
  method: 'GET',
});
```

**参数：**
- `name: string` - 指标名称
- `value: number` - 指标值
- `tags?: Record<string, string>` - 标签

## 用户行为 API

### tea
用户行为上报实例。

```typescript
import { tea } from '@ttastra/core/runtime/tea';

// 上报事件
tea.report('user_click', {
  button: 'submit',
  page: 'login',
});

// 带用户信息的事件
tea.report('user_action', {
  action: 'purchase',
  amount: 99.99,
}, {
  userId: '12345',
  sessionId: 'abc123',
});
```

**方法：**
- `report(event: string, data: any, userInfo?: any): void` - 上报事件

## 认证 API

### useByteCloudJwt
ByteCloud JWT 认证 Hook。

```typescript
import { useByteCloudJwt } from '@ttastra/core/runtime/bytecloud-jwt';

function MyComponent() {
  const {
    isByteCloudJwtLoading,    // 是否正在加载
    isLoggedIn,               // 是否已登录
    userInfo,                 // 用户信息
    error,                    // 错误信息
    redirectToLogin,          // 跳转登录
    redirectToLogout,         // 跳转登出
    getJwt,                   // 获取 JWT
  } = useByteCloudJwt();
  
  if (isByteCloudJwtLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isLoggedIn) {
    return <button onClick={redirectToLogin}>登录</button>;
  }
  
  return <div>欢迎，{userInfo.name}</div>;
}
```

**返回值：**
- `ByteCloudJwtState` - 认证状态对象

### getJwt
获取 JWT 令牌。

```typescript
import { getJwt } from '@ttastra/core/runtime';

const jwt = await getJwt();
```

**返回值：**
- `Promise<string | null>` - JWT 令牌

### getJwtUserInfo
获取用户信息。

```typescript
import { getJwtUserInfo } from '@ttastra/core/runtime';

const userInfo = await getJwtUserInfo();
```

**返回值：**
- `Promise<UserInfo | null>` - 用户信息

## 微前端 API

### useRemoteModule
使用远程模块 Hook。

```typescript
import { useRemoteModule } from '@ttastra/core/runtime/vmok';

function MicroApp() {
  const { Module, loading, error } = useRemoteModule('micro-app');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <Module />;
}
```

**参数：**
- `name: string` - 模块名称

**返回值：**
- `RemoteModuleState` - 远程模块状态

### loadRemoteModule
加载远程模块。

```typescript
import { loadRemoteModule } from '@ttastra/core/runtime/vmok';

const module = await loadRemoteModule('micro-app');
```

**参数：**
- `name: string` - 模块名称

**返回值：**
- `Promise<RemoteModule>` - 远程模块

## 区域 API

### getVGeo
获取虚拟地理区域。

```typescript
import { getVGeo } from '@ttastra/core/runtime/regions';

const vgeo = getVGeo();
console.log(vgeo); // 'row' | 'eu' | 'us' | 'cn'
```

**返回值：**
- `VGeo` - 虚拟地理区域

### getVRegion
获取虚拟区域。

```typescript
import { getVRegion } from '@ttastra/core/runtime/regions';

const vregion = getVRegion();
console.log(vregion); // 'row' | 'eu' | 'us' | 'cn' | 'unknown'
```

**返回值：**
- `VRegion | 'unknown'` - 虚拟区域

### getPublicPath
获取公共路径。

```typescript
import { getPublicPath } from '@ttastra/core/runtime/regions';

const publicPath = getPublicPath();
console.log(publicPath); // '/static/'
```

**返回值：**
- `string` - 公共路径

## 插件 API

### BasePlugin
基础插件类。

```typescript
import { BasePlugin } from '@ttastra/core/runtime/plugins';

export class MyPlugin extends BasePlugin {
  name = 'my-plugin';
  
  setup() {
    // 插件设置逻辑
  }
}
```

### LifecyclePlugin
生命周期插件类。

```typescript
import { LifecyclePlugin } from '@ttastra/core/runtime/plugins';

export class MyLifecyclePlugin extends LifecyclePlugin {
  extendPluginContext() {
    return { customData: 'value' };
  }
  
  extendBridge() {
    return { customMethod: () => {} };
  }
  
  async appWillMount(params: AppLifecycleHookParams) {
    console.log('App will mount');
  }
  
  async pageWillMount() {
    console.log('Page will mount');
  }
  
  async layoutWillMount() {
    console.log('Layout will mount');
  }
}
```

## 组件 API

### ErrorBoundary
错误边界组件。

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

**Props：**
- `fallback: React.ComponentType` - 错误时显示的组件
- `children: React.ReactNode` - 子组件

### Loading
加载组件。

```typescript
import { Loading } from '@ttastra/core/runtime/components';

function App() {
  return <Loading />;
}
```

## 类型定义

### SolutionConfig
解决方案配置类型。

```typescript
interface SolutionConfig {
  deploy?: DeployConfig;
  compliance?: ComplianceConfig;
  capabilities?: CapabilitiesConfig;
  router?: RouterConfig;
  bff?: BFFConfig;
  vmok?: VmokConfig;
  plugins?: CliPlugin[];
  builderPlugins?: RsbuildPlugin[];
  edenx?: EdenXUserConfig;
}
```

### InitAppOptions
应用初始化选项。

```typescript
interface InitAppOptions {
  plugins?: LifecyclePlugin[];
  slots?: SlotsConfig;
}
```

### RouteObject
路由对象类型。

```typescript
interface RouteObject {
  path?: string;
  index?: boolean;
  element?: React.ReactNode;
  children?: RouteObject[];
  caseSensitive?: boolean;
}
```

### Bridge
桥接对象类型。

```typescript
interface Bridge {
  [key: string]: any;
}
```

## 配置类型

### DeployConfig
部署配置类型。

```typescript
interface DeployConfig {
  isInternalApp?: boolean;
  vgeos?: VGeo[];
  baseUrl?: string;
  domains?: string[] | DomainsConfig;
  enableMonorepoRecoverDeps?: boolean;
  deployPlatform?: 'goofy-web' | 'goofy-node' | 'tce';
}
```

### ComplianceConfig
合规配置类型。

```typescript
interface ComplianceConfig {
  hasCSPRequirement?: boolean;
  hasLoginBehavior?: boolean;
  uploadSourceMapInTtpScm?: boolean;
  replaceTuxFontUrlInTtpScm?: boolean | ReplaceTuxFontUrlOptions;
  useMSSDK?: boolean | MSSDKConfig;
}
```

### CapabilitiesConfig
通用能力配置类型。

```typescript
interface CapabilitiesConfig {
  i18n?: I18nConfig;
  slardar?: SlardarConfig;
  tea?: boolean;
  bytecloudJwt?: boolean | ByteCloudJwtConfig;
}
```

### RouterConfig
路由配置类型。

```typescript
interface RouterConfig {
  useConfigBasedRoutes?: boolean;
  useDynamicRoutes?: boolean | { parentPath: string };
  isMPA?: boolean;
}
```

### BFFConfig
BFF 配置类型。

```typescript
interface BFFConfig {
  enableHandleWeb?: boolean;
  prefix?: string;
  proxy?: Record<string, string | ProxyOptions>;
  separateMode?: boolean;
  timeout?: number;
}
```

### VmokConfig
微前端配置类型。

```typescript
interface VmokConfig {
  configPath: string;
  dynamicModules?: {
    url: string;
  };
}
```

## 错误处理

### 常见错误类型

```typescript
// 配置错误
class ConfigError extends Error {
  constructor(message: string) {
    super(`[TTAstra Config Error] ${message}`);
  }
}

// 运行时错误
class RuntimeError extends Error {
  constructor(message: string) {
    super(`[TTAstra Runtime Error] ${message}`);
  }
}

// 插件错误
class PluginError extends Error {
  constructor(message: string) {
    super(`[TTAstra Plugin Error] ${message}`);
  }
}
```

### 错误处理最佳实践

```typescript
// 使用错误边界
function App() {
  return (
    <ErrorBoundary fallback={({ error, resetError }) => (
      <div>
        <h2>Something went wrong:</h2>
        <pre>{error.message}</pre>
        <button onClick={resetError}>Try again</button>
      </div>
    )}>
      <MyComponent />
    </ErrorBoundary>
  );
}

// 异步错误处理
async function loadData() {
  try {
    const data = await fetchData();
    return data;
  } catch (error) {
    console.error('Failed to load data:', error);
    throw new Error('数据加载失败');
  }
}
```
