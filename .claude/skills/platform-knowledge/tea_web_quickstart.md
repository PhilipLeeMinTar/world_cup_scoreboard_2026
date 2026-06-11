# Web 前端快速上手指南

本指南将引导你如何为 Web 应用快速接入 TEA（Toutiao Event Analysis）的 JavaScript SDK，并上报你的第一个事件。我们提供了两种主流的安装方式：NPM 和 CDN，以及在原生 JS、React 和 Vue 项目中的具体实践示例。

## 1. 安装 SDK

你可以根据项目类型选择最适合的安装方式。

### 方式一：使用 NPM/Yarn（推荐）

对于使用 Webpack、Vite 等构建工具的现代化前端项目，推荐使用 NPM 进行安装和管理。

```bash
# 使用 npm 安装
npm install byted-tea-sdk

# 或者使用 yarn 安装
yarn add byted-tea-sdk
```

安装完成后，你可以在项目的代码中直接 `import` SDK。[[10]](https://bytedance.larkoffice.com/wiki/wikcnZXhLbCcWqGzPdRUD7j66cb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcngDes7MByAdNyYF4haqxQof)

```javascript
import Tea from 'byted-tea-sdk';
```

### 方式二：使用 CDN

对于传统项目或希望快速体验的场景，可以直接在 HTML 文件中通过 `<script>` 标签引入 SDK。

1.  **添加引导代码**
    将以下代码片段复制到 HTML 文件的 `<head>` 标签内，并确保它在所有其他脚本之前加载。这段代码会创建一个全局的 `collectEvent` 函数队列，用于在 SDK 完全加载前缓存所有 API 调用。

    ```html
    <script>
      (function(win, export_obj) {
        win['LogAnalyticsObject'] = export_obj; // V5 版本及以后推荐使用 LogAnalyticsObject
        if (!win[export_obj]) {
          function _collect() {
            _collect.q.push(arguments);
          }
          _collect.q = _collect.q || [];
          win[export_obj] = _collect;
        }
        win[export_obj].l = +new Date();
      })(window, 'collectEvent');
    </script>
    ```

2.  **引入 SDK 主文件**
    在引导代码之后，通过 `async` 脚本引入 SDK 的主文件。推荐使用最新 V5 版本的 CDN 地址：

    ```html
    <!-- 基础版本 -->
    <script async src="https://lf-static.applogcdn.com/obj/applog-sdk-static/log-sdk/collect/5/collect-base.js"></script>

    <!-- 完整版本（包含无埋点、A/B测试等功能） -->
    <script async src="https://lf-static.applogcdn.com/obj/applog-sdk-static/log-sdk/collect/5/collect.js"></script>
    ```

引入后，你可以通过全局的 `window.collectEvent` 函数来调用 SDK 的所有 API。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)

## 2. 初始化与配置

无论使用何种方式安装，SDK 的初始化流程都是相似的，遵循 **`init` -> `config` -> `start`** 的顺序。

```javascript
// 1. 初始化 SDK
Tea.init({
  app_id: 1234, // 【必填】替换为你的产品在 TEA 平台申请的 App ID (数字类型)
  channel: 'cn', // 【必填】上报渠道，'cn' 为国内，'sg' 为新加坡，'va' 为美东
  log: true, // 建议开发环境下开启，会在控制台打印详细的日志信息，方便调试
  disable_auto_pv: false, // 是否禁用 SDK 自动上报的页面浏览（PV）事件，默认为 false。对于 SPA 应用，建议设置为 true，并手动上报
});

// 2. 配置公共参数和用户信息
Tea.config({
  // 设置用户唯一标识，在用户登录后调用，用于精准识别用户
  user_unique_id: 'YOUR_USER_ID', // 替换为业务中的实际用户 ID

  // 设置所有事件都会携带的公共属性 (custom dimensions)
  // 这些属性会挂载在 header.custom 下
  page_type: 'article_detail',
  from_page: 'homepage',

  // 也可以通过 evtParams 设置事件级别的公共属性
  // 这些属性会合并到每个事件的 params 对象中
  evtParams: {
    platform: 'web',
    version: '1.2.0',
  }
});

// 3. 启动上报
// 这个方法必须被调用！调用后，SDK 才会真正开始向服务器发送事件数据。
Tea.start();
```

## 3. 上报事件

完成初始化后，你就可以在代码的任何地方上报自定义事件了。

### 上报页面浏览 (PV) 事件

对于单页应用（SPA），由于路由切换不会刷新页面，SDK 无法自动捕获页面变化。你需要在路由监听器中手动调用 `predefinePageView` 方法。

```javascript
// 当路由发生变化时调用
Tea.predefinePageView({
  // 你可以传入自定义属性来覆盖或补充 SDK 自动采集的页面信息
  page_title: '新的页面标题',
});
```

### 上报自定义事件

使用 `event` 方法上报业务逻辑中的关键行为。

```javascript
// 上报一个简单的点击事件，不带参数
Tea.event('button_click');

// 上报一个带参数的搜索事件
Tea.event('search_action', {
  keyword: 'TEA SDK',
  search_type: 'article',
});
```

## 4. 框架集成示例

### React 示例 (Hooks)

在 React 项目中，通常会将 TEA 的初始化逻辑封装在一个高阶组件（HOC）或一个自定义 Hook 中，并在应用根组件（如 `App.js`）中执行一次。

```jsx
// src/utils/tea.js
import Tea from 'byted-tea-sdk';

let isTeaInitialized = false;

export const initTea = () => {
  if (isTeaInitialized) return;

  Tea.init({
    app_id: 1234, // 替换为你的 App ID
    log: process.env.NODE_ENV === 'development',
    disable_auto_pv: true, // React 项目通常是 SPA，推荐手动上报 PV
  });

  Tea.config({
    // 初始的公共属性
    platform: 'web-react',
  });

  Tea.start();
  isTeaInitialized = true;
  console.log('TEA SDK Initialized.');
};

export const tea = Tea; // 导出 Tea 实例，方便在其他地方调用

// src/App.js
import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { initTea, tea } from './utils/tea';

function App() {
  const location = useLocation();

  useEffect(() => {
    // 应用加载时初始化 TEA
    initTea();
  }, []);

  useEffect(() => {
    // 监听路由变化，手动上报 PV 事件
    tea.predefinePageView();
    console.log(`TEA PV event sent for path: ${location.pathname}`);
  }, [location]);

  const handleButtonClick = () => {
    // 上报自定义事件
    tea.event('hero_button_click', { from_component: 'App' });
    alert('Event sent!');
  };

  return (
    <div>
      <h1>React TEA Example</h1>
      <button onClick={handleButtonClick}>Send Custom Event</button>
    </div>
  );
}

export default App;
```

### Vue 示例 (Vue 3)

在 Vue 项目中，可以将 TEA 实例挂载到全局属性，或通过插件（Plugin）的方式注入，方便在各个组件中调用。

```javascript
// src/plugins/tea.js
import Tea from 'byted-tea-sdk';

export default {
  install: (app) => {
    Tea.init({
      app_id: 5678, // 替换为你的 App ID
      log: import.meta.env.DEV,
      disable_auto_pv: true, // Vue 项目通常是 SPA，推荐手动上报 PV
    });

    Tea.config({
      platform: 'web-vue',
    });

    Tea.start();
    console.log('TEA SDK Initialized.');

    // 将 Tea 实例挂载到全局
    app.config.globalProperties.$tea = Tea;
  },
};

// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import teaPlugin from './plugins/tea';

const app = createApp(App);

app.use(router);
app.use(teaPlugin);

app.mount('#app');

// 监听路由变化
router.afterEach((to, from) => {
  // 使用 nextTick 确保 DOM 更新后再上报
  app.config.globalProperties.$nextTick(() => {
    app.config.globalProperties.$tea.predefinePageView();
    console.log(`TEA PV event sent for path: ${to.path}`);
  });
});

// src/components/MyButton.vue
<template>
  <button @click="sendEvent">Send Event from Vue</button>
</template>

<script>
export default {
  methods: {
    sendEvent() {
      this.$tea.event('vue_button_click', { component_name: 'MyButton' });
      alert('Event sent!');
    },
  },
};
</script>
```

---

### 参考资料

*   [Tea前端接入指南](https://bytedance.larkoffice.com/wiki/wikcnZXhLbCcWqGzPdRUD7j66cb)[[10]](https://bytedance.larkoffice.com/wiki/wikcnZXhLbCcWqGzPdRUD7j66cb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcngDes7MByAdNyYF4haqxQof)
*   [埋点SDK WEB 5.0 版本使用文档](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb)[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)
