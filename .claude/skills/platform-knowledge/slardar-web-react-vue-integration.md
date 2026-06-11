# 4. React & Vue 集成实践

在单页面应用 (SPA) 框架如 React 和 Vue 中使用 Slardar，除基本接入外，还需要一些额外的集成工作来更好地捕获框架特定的错误和路由变化。

**快速索引**
- [React 集成](#react-集成)
  - [使用 Error Boundary 捕获渲染错误](#使用-error-boundary-捕获渲染错误)
  - [采集路由变更](#采集-路由变更)
  - [在函数组件和 Hook 中上报](#在函数组件和-hook-中上报)
- [Vue 集成](#vue-集成)
  - [使用全局错误处理器](#使用全局错误处理器)
  - [采集路由变更](#采集路由变更-1)
  - [在组件内部上报](#在组件内部上报)
- [关于 SPA 与 SSR 的建议](#关于-spa-与-ssr-的建议)

---

## React 集成

### 使用 Error Boundary 捕获渲染错误

React 的 `ErrorBoundary` (错误边界) 是一种可以捕获其子组件树中 JavaScript 错误的组件。这是捕获 React 渲染阶段错误的标准方式。我们可以创建一个自定义的 `ErrorBoundary`，在捕获到错误时，将其主动上报给 Slardar。

**示例：`SlardarErrorBoundary.tsx`**

```tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import browserClient from '@slardar/web';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

class SlardarErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): State {
    // 更新 state，以便下一次渲染可以显示降级后的 UI
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 将错误信息上报给 Slardar
    browserClient('captureException', error, {
      extra: {
        componentStack: errorInfo.componentStack,
      },
    });
  }

  render() {
    if (this.state.hasError) {
      // 你可以渲染任何自定义的降级 UI
      return <h1>抱歉，页面出错了。我们正在紧急修复。</h1>;
    }

    return this.props.children;
  }
}

export default SlardarErrorBoundary;
```

**如何使用**:

在你的应用根组件或者关键业务模块外层包裹这个 `SlardarErrorBoundary`。

```tsx
// App.tsx
import SlardarErrorBoundary from './SlardarErrorBoundary';
import MyRoutes from './MyRoutes';

function App() {
  return (
    <SlardarErrorBoundary>
      <MyRoutes />
    </SlardarErrorBoundary>
  );
}
```

### 采集路由变更

对于 SPA 应用，页面的切换不会导致浏览器刷新，因此需要手动监听路由变化并上报，以便 Slardar 能够正确地记录页面浏览轨迹 (PV) 和关联错误发生的页面。

如果你使用 `react-router-dom`，可以在 `useEffect` 中监听 `location` 对象的变化。

**示例：使用 `useLocation` 钩子**

```tsx
// 在你的路由组件或顶层组件中
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import browserClient from '@slardar/web';

function RouteChangeTracker() {
  const location = useLocation();

  useEffect(() => {
    // 每当 location.pathname 变化时，就认为是一次页面跳转
    // Slardar SDK 会自动处理，我们只需要调用 setContext 即可触发
    browserClient('setContext', {
      // Slardar 会识别 page 字段的变化并自动上报 PV
      page: location.pathname, 
    });
  }, [location]);

  return null;
}

// 然后在你的 Router 中使用这个组件
// <BrowserRouter>
//   <RouteChangeTracker />
//   <App />
// </BrowserRouter>
```

### 在函数组件和 Hook 中上报

在任何函数组件或自定义 Hook 中，你都可以直接导入 `browserClient` 并调用其 API。

```tsx
import { useState } from 'react';
import browserClient from '@slardar/web';

function UserProfile() {
  const [loading, setLoading] = useState(false);

  const handleUpdateProfile = async () => {
    setLoading(true);
    const startTime = Date.now();
    try {
      // ... 更新用户信息的逻辑 ...
      browserClient('reportEvent', 'UpdateProfile', {
        duration: Date.now() - startTime,
        success_count: 1,
      }, { status: 'success' });
    } catch (error) {
      browserClient('captureException', error);
      browserClient('reportEvent', 'UpdateProfile', {
        duration: Date.now() - startTime,
        failure_count: 1,
      }, { status: 'failure' });
    } finally {
      setLoading(false);
    }
  };

  return <button onClick={handleUpdateProfile} disabled={loading}>Update</button>;
}
```

---

## Vue 集成

### 使用全局错误处理器

Vue 提供了 `app.config.errorHandler`，这是一个全局钩子，用于捕获所有组件渲染和生命周期函数中未被捕获的错误。这是集成 Slardar 的理想位置。

**示例：在 `main.ts` 中配置**

```typescript
// main.ts
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import browserClient from '@slardar/web';

// --- Slardar 初始化 ---
browserClient('init', { bid: 'YOUR_BID' });
browserClient('start');
// --------------------

const app = createApp(App);

// 设置 Vue 全局错误处理器
app.config.errorHandler = (err, instance, info) => {
  // err: 错误对象
  // instance: 发生错误的组件实例
  // info: Vue 特定的错误信息，比如错误所在的生命周期钩子
  
  console.error('Caught by Vue errorHandler:', err);

  browserClient('captureException', err, {
    extra: {
      vue_info: info,
      component_name: instance?.$options.name || 'AnonymousComponent',
    },
  });
};

app.use(router);
app.mount('#app');
```

### 采集路由变更

如果你使用 `vue-router`，可以利用其提供的导航守卫 `router.afterEach` 来监听路由变化。

**示例：在 `router/index.ts` 或 `main.ts` 中配置**

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import browserClient from '@slardar/web';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ... 你的路由配置
  ],
});

router.afterEach((to, from) => {
  // to: 目标路由对象
  // from: 来源路由对象
  
  // 通过 setContext 更新当前页面路径
  browserClient('setContext', {
    page: to.path,
  });
});

export default router;
```

### 在组件内部上报

在 Vue 的组合式 API (`setup`) 或选项式 API (methods, created, etc.) 中，同样可以直接导入 `browserClient` 来进行自定义上报。

**示例：在 `<script setup>` 中使用**

```vue
<script setup lang="ts">
import { ref } from 'vue';
import browserClient from '@slardar/web';

const isLoading = ref(false);

async function submitForm() {
  isLoading.value = true;
  try {
    // ... 提交逻辑 ...
    browserClient('addBreadcrumb', {
      category: 'form.submission',
      message: 'User submitted the contact form',
      level: 'info',
    });
  } catch (error) {
    browserClient('captureException', error);
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <form @submit.prevent="submitForm">
    <!-- ... 表单内容 ... -->
    <button type="submit" :disabled="isLoading">提交</button>
  </form>
</template>
```

## 关于 SPA 与 SSR 的建议

-   **SPA (单页面应用)**
    -   **初始化位置**：务必在应用的最顶层、最早执行的脚本中进行 `init` 和 `start`。
    -   **路由采集**：必须手动集成路由变更的监听，这是确保 PV 数据和页面归因准确的关键。

-   **SSR (服务器端渲染)**
    -   **双端初始化**：在 SSR 架构中，代码会在服务器和客户端两端执行。Slardar SDK (`@slardar/web`) 是**纯客户端**的，它依赖 `window` 等浏览器环境的 API。
    -   **避免在服务端执行**：你必须确保 Slardar 的 `import` 和调用只在客户端环境中发生。通常可以通过判断 `typeof window !== 'undefined'` 来实现。

    ```typescript
    // 一个在 SSR 环境中安全初始化 Slardar 的例子
    if (typeof window !== 'undefined') {
      // 仅在浏览器环境中执行
      import('@slardar/web').then(({ default: browserClient }) => {
        browserClient('init', { bid: 'YOUR_BID' });
        browserClient('start');
        
        // 在这里可以继续设置 Vue/React 的客户端特定逻辑
      });
    }
    ```
    -   对于 Node.js 端的异常和性能监控，需要使用 Slardar 提供的 **Node.js SDK**，它与前端的 `@slardar/web` 是不同的包，用法也不同。
