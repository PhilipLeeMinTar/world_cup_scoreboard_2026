# Vmok 开发指南

> 本文档详细介绍如何使用 Vmok 进行微模块开发

## 一、项目初始化

### 1. 安装 Vmok CLI

```bash
# 全局安装
npm install -g @vmok/cli

# 或使用 pnpm
pnpm add -g @vmok/cli

# 验证安装
vmok --version
```

### 2. 创建生产者项目

#### NPM 类型模块

```bash
# 创建 NPM 类型模块
vmok create my-components --type npm

cd my-components
pnpm install
```

**项目结构:**
```
my-components/
├── src/
│   ├── components/
│   │   ├── Button/
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   └── Input/
│   │       ├── index.tsx
│   │       └── style.css
│   ├── index.ts
│   └── types.ts
├── vmok.config.js
├── package.json
├── tsconfig.json
└── webpack.config.js
```

#### 应用类型模块

```bash
# 创建应用类型模块
vmok create my-module-app --type app

cd my-module-app
pnpm install
```

**项目结构:**
```
my-module-app/
├── src/
│   ├── pages/
│   ├── components/
│   ├── App.tsx
│   └── index.tsx
├── public/
├── vmok.config.js
├── package.json
└── tsconfig.json
```

### 3. 创建消费者项目

```bash
# 创建消费者应用
vmok create my-consumer --type consumer

cd my-consumer
pnpm install
```

## 二、配置详解

### 1. vmok.config.js (生产者)

#### 基础配置

```javascript
// vmok.config.js
module.exports = {
  // 模块名称 (必填)
  name: 'my-module',

  // 模块类型: npm | app (必填)
  type: 'npm',

  // 暴露的模块 (必填)
  exposes: {
    './Button': './src/components/Button',
    './Input': './src/components/Input',
    './utils': './src/utils'
  },

  // 共享依赖
  shared: {
    react: {
      singleton: true,
      requiredVersion: '^18.0.0'
    },
    'react-dom': {
      singleton: true,
      requiredVersion: '^18.0.0'
    }
  },

  // 构建配置
  build: {
    // 输出目录
    outputDir: 'dist',

    // 公共路径
    publicPath: 'auto',

    // 是否生成类型定义
    generateTypes: true,

    // 是否压缩代码
    minify: true
  }
};
```

#### 高级配置

```javascript
module.exports = {
  name: 'advanced-module',
  type: 'npm',

  // 暴露配置
  exposes: {
    './Button': {
      import: './src/components/Button',
      name: 'Button'
    },
    './hooks': {
      import: './src/hooks',
      name: 'hooks'
    }
  },

  // 共享依赖高级配置
  shared: {
    react: {
      // 单例模式
      singleton: true,
      // 必需版本
      requiredVersion: '^18.0.0',
      // 严格版本
      strictVersion: false,
      // 立即加载
      eager: false,
      // 共享作用域
      shareScope: 'default'
    },
    lodash: {
      singleton: false,
      requiredVersion: '^4.17.0'
    }
  },

  // Webpack 配置扩展
  configureWebpack: (config) => {
    config.optimization = {
      ...config.optimization,
      splitChunks: {
        chunks: 'all'
      }
    };
    return config;
  },

  // 插件配置
  plugins: [
    '@vmok/plugin-react',
    ['@vmok/plugin-typescript', { configFile: './tsconfig.json' }]
  ]
};
```

### 2. vmok.config.js (消费者)

```javascript
// vmok.config.js
module.exports = {
  name: 'my-consumer',
  type: 'consumer',

  // 远程模块配置
  remotes: {
    // NPM 类型模块
    'my-components': 'my-components@http://localhost:3001/remoteEntry.js',

    // 应用类型模块
    'module-app': {
      url: 'http://localhost:3002/remoteEntry.js',
      entry: 'module-app'
    },

    // 动态 URL
    'dynamic-module': {
      url: () => {
        const env = process.env.NODE_ENV;
        return env === 'production'
          ? 'https://cdn.example.com/module/remoteEntry.js'
          : 'http://localhost:3003/remoteEntry.js';
      },
      entry: 'dynamic-module'
    }
  },

  // 共享依赖
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true }
  },

  // Garfish 配置 (应用类型模块)
  garfish: {
    // 是否启用沙箱
    sandbox: true,

    // 路由配置
    router: {
      mode: 'browser'
    },

    // 预加载配置
    preload: ['module-app']
  }
};
```

### 3. package.json 配置

#### 生产者 (NPM 类型)

```json
{
  "name": "@myorg/my-module",
  "version": "1.0.0",
  "main": "./dist/index.js",
  "module": "./dist/index.esm.js",
  "types": "./dist/index.d.ts",

  "exports": {
    ".": {
      "import": "./dist/index.esm.js",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./Button": {
      "import": "./dist/Button.esm.js",
      "require": "./dist/Button.js",
      "types": "./dist/Button.d.ts"
    }
  },

  "files": [
    "dist",
    "package.json",
    "README.md"
  ],

  "scripts": {
    "dev": "vmok dev",
    "build": "vmok build",
    "publish": "vmok publish"
  },

  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
```

## 三、开发流程

### 1. 开发生产者模块

#### 创建组件

```typescript
// src/components/Button/index.tsx
import React from 'react';
import './style.css';

export interface ButtonProps {
  type?: 'primary' | 'default';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  type = 'default',
  size = 'medium',
  onClick,
  children
}) => {
  return (
    <button
      className={`vmok-button vmok-button-${type} vmok-button-${size}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

export default Button;
```

#### 导出模块

```typescript
// src/index.ts
export { Button } from './components/Button';
export type { ButtonProps } from './components/Button';

export { Input } from './components/Input';
export type { InputProps } from './components/Input';

// 导出工具函数
export * from './utils';
```

#### 启动开发

```bash
# 启动开发服务器
vmok dev

# 访问 http://localhost:3001
```

#### 构建模块

```bash
# 构建生产版本
vmok build

# 生成类型定义
vmok build --generate-types

# 分析包大小
vmok build --analyze
```

### 2. 开发消费者应用

#### 使用远程模块

**方式一: 静态导入**

```typescript
// src/App.tsx
import React from 'react';
import { Button } from 'my-components/Button';

function App() {
  return (
    <div>
      <h1>消费者应用</h1>
      <Button type="primary" onClick={() => alert('Clicked!')}>
        点击我
      </Button>
    </div>
  );
}

export default App;
```

**方式二: 动态导入**

```typescript
// src/App.tsx
import React, { Suspense, lazy } from 'react';

// 懒加载远程组件
const RemoteButton = lazy(() => import('my-components/Button'));

function App() {
  return (
    <div>
      <h1>消费者应用</h1>
      <Suspense fallback={<div>加载中...</div>}>
        <RemoteButton type="primary">点击我</RemoteButton>
      </Suspense>
    </div>
  );
}

export default App;
```

**方式三: 使用运行时 API**

```typescript
// src/App.tsx
import React, { useEffect, useState } from 'react';
import { loadRemote } from '@vmok/runtime';

function App() {
  const [Button, setButton] = useState(null);

  useEffect(() => {
    loadRemote('my-components/Button').then((module) => {
      setButton(() => module.default);
    });
  }, []);

  if (!Button) return <div>加载中...</div>;

  return (
    <div>
      <h1>消费者应用</h1>
      <Button type="primary">点击我</Button>
    </div>
  );
}

export default App;
```

### 3. 应用类型模块集成

#### 加载应用模块

```typescript
// src/App.tsx
import React from 'react';
import { GarfishProvider, GarfishApp } from '@vmok/garfish-react';

function App() {
  return (
    <GarfishProvider
      apps={[
        {
          name: 'module-app',
          entry: 'http://localhost:3002',
          activeWhen: '/module-app'
        }
      ]}
    >
      <div>
        <nav>
          <a href="/module-app">模块应用</a>
        </nav>

        {/* 渲染子应用 */}
        <GarfishApp name="module-app" />
      </div>
    </GarfishProvider>
  );
}

export default App;
```

## 四、类型支持

### 1. 自动生成类型定义

```bash
# 生成类型定义
vmok build --generate-types
```

**生成结果:**
```
dist/
├── index.js
├── index.d.ts
├── Button.js
├── Button.d.ts
└── types/
    └── ...
```

### 2. 类型声明文件

```typescript
// types/remotes.d.ts
declare module 'my-components/Button' {
  export interface ButtonProps {
    type?: 'primary' | 'default';
    size?: 'small' | 'medium' | 'large';
    onClick?: () => void;
    children: React.ReactNode;
  }

  export const Button: React.FC<ButtonProps>;
  export default Button;
}

declare module 'my-components/Input' {
  export interface InputProps {
    value?: string;
    onChange?: (value: string) => void;
    placeholder?: string;
  }

  export const Input: React.FC<InputProps>;
  export default Input;
}
```

### 3. 在消费者中使用类型

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "types": ["@vmok/types"],
    "paths": {
      "my-components/*": ["./types/my-components/*"]
    }
  }
}
```

```typescript
// src/App.tsx
import React from 'react';
import { Button, ButtonProps } from 'my-components/Button';

// 完整类型支持
const props: ButtonProps = {
  type: 'primary',
  size: 'medium',
  onClick: () => console.log('Clicked')
};

function App() {
  return <Button {...props}>点击我</Button>;
}
```

## 五、运行时 API

### 1. loadRemote

动态加载远程模块:

```typescript
import { loadRemote } from '@vmok/runtime';

// 基础用法
const module = await loadRemote('my-components/Button');
const Button = module.default;

// 带选项
const module = await loadRemote('my-components/Button', {
  from: 'runtime',  // 加载来源
  version: '1.2.0', // 指定版本
  bustCache: false  // 是否清除缓存
});
```

### 2. preloadRemote

预加载远程模块:

```typescript
import { preloadRemote } from '@vmok/runtime';

// 预加载模块
await preloadRemote(['my-components/Button', 'my-components/Input']);

// 在组件中使用
import { Button } from 'my-components/Button'; // 已预加载,立即可用
```

### 3. getRemoteInfo

获取远程模块信息:

```typescript
import { getRemoteInfo } from '@vmok/runtime';

const info = getRemoteInfo('my-components');
console.log(info);
// {
//   name: 'my-components',
//   version: '1.0.0',
//   entry: 'http://localhost:3001/remoteEntry.js',
//   loaded: true
// }
```

### 4. registerRemote

运行时注册远程模块:

```typescript
import { registerRemote } from '@vmok/runtime';

registerRemote({
  name: 'dynamic-module',
  entry: 'https://cdn.example.com/module/remoteEntry.js'
});

// 之后可以加载
const module = await loadRemote('dynamic-module/Component');
```

## 六、通信与数据共享

### 1. Vmok Bridge

跨模块通信:

```typescript
// 生产者: 提供服务
import { createBridge } from '@vmok/bridge';

const bridge = createBridge('my-service');

bridge.provide('getUser', async (userId: string) => {
  const response = await fetch(`/api/user/${userId}`);
  return response.json();
});

bridge.provide('updateUser', async (userId: string, data: any) => {
  const response = await fetch(`/api/user/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
  return response.json();
});
```

```typescript
// 消费者: 调用服务
import { useBridge } from '@vmok/bridge';

function UserProfile() {
  const bridge = useBridge('my-service');

  useEffect(() => {
    const loadUser = async () => {
      const user = await bridge.call('getUser', 'user-123');
      console.log(user);
    };
    loadUser();
  }, []);

  const handleUpdate = async () => {
    await bridge.call('updateUser', 'user-123', { name: 'New Name' });
  };

  return <button onClick={handleUpdate}>更新用户</button>;
}
```

### 2. 事件总线

```typescript
// 发送事件
import { eventBus } from '@vmok/runtime';

eventBus.emit('user:login', { userId: '123', username: 'John' });

// 监听事件
eventBus.on('user:login', (data) => {
  console.log('User logged in:', data);
});

// 取消监听
eventBus.off('user:login', handler);
```

### 3. 状态共享

```typescript
// 创建共享状态
import { createSharedStore } from '@vmok/store';

export const userStore = createSharedStore({
  state: {
    user: null,
    isLoggedIn: false
  },
  actions: {
    login(user) {
      this.user = user;
      this.isLoggedIn = true;
    },
    logout() {
      this.user = null;
      this.isLoggedIn = false;
    }
  }
});

// 在任意模块中使用
import { useSharedStore } from '@vmok/store';
import { userStore } from './stores/user';

function Header() {
  const [state, actions] = useSharedStore(userStore);

  return (
    <div>
      {state.isLoggedIn ? (
        <span>{state.user.name}</span>
      ) : (
        <button onClick={actions.login}>登录</button>
      )}
    </div>
  );
}
```

## 七、调试与性能

### 1. Vmok DevTools

**安装浏览器插件:**
- Chrome: https://vmok-devtools.bytedance.net/
- 提供模块依赖图、性能分析等功能

**使用:**
```typescript
// 在代码中启用 DevTools
if (process.env.NODE_ENV === 'development') {
  import('@vmok/devtools').then((devtools) => {
    devtools.init();
  });
}
```

### 2. 性能监控

```typescript
// vmok.config.js
module.exports = {
  name: 'my-module',

  // 性能监控配置
  performance: {
    // 启用性能监控
    enabled: true,

    // 上报地址
    reportUrl: '/api/performance',

    // 采样率
    sampleRate: 0.1
  }
};
```

### 3. 构建分析

```bash
# 分析包大小
vmok build --analyze

# 生成依赖图
vmok build --graph

# 性能报告
vmok build --profile
```

## 八、部署

### 1. NPM 类型部署

```bash
# 构建
vmok build

# 发布到 npm
npm publish

# 或发布到内部 registry
npm publish --registry https://npm.byted.org
```

### 2. 应用类型部署

```bash
# 构建
vmok build

# 部署到 SCM
vmok deploy --platform scm

# 部署到 Goofy
vmok deploy --platform goofy

# 灰度发布
vmok deploy --gray 10%
```

### 3. CDN 部署

```javascript
// vmok.config.js
module.exports = {
  name: 'my-module',

  build: {
    publicPath: 'https://cdn.example.com/my-module/1.0.0/'
  },

  // CDN 配置
  cdn: {
    enabled: true,
    domain: 'cdn.example.com',
    path: '/my-module'
  }
};
```

## 相关文档

- Vmok 介绍: ./01-introduction.md
- 最佳实践: ./03-best-practices.md
- API 文档: https://vmok.bytedance.net/api/
- Module Federation 文档: https://webpack.js.org/concepts/module-federation/
