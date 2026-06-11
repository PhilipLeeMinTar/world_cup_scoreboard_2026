# TEA Web SDK - API 参考

本篇文档详细介绍了 TEA Web SDK 的核心 API。所有 API 均以 `Tea.` 或 `window.collectEvent` 的形式调用，具体取决于你的安装方式（NPM 或 CDN）。为了保持一致性，本文档将统一使用 `Tea.` 作为示例。

## 核心 API

### 1. `Tea.init(options)`

初始化 SDK，是所有操作的第一步。每个 SDK 实例只需调用一次。

*   **`options`** `<Object>`: 初始化配置对象。

| 字段 | 类型 | 是否必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `app_id` | `Number` | **是** | - | 你在 TEA 平台申请的应用 ID。 |
| `channel` | `String` | **是** | - | 数据上报的区域。`'cn'` (国内), `'sg'` (新加坡), `'va'` (美东)。 |
| `log` | `Boolean` | 否 | `false` | 是否在浏览器控制台打印详细的调试日志。建议在开发环境中开启。 |
| `autotrack` | `Boolean` | 否 | `false` | 是否开启无埋点（自动采集）功能。开启后可支持圈选和热图。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih) |
| `disable_auto_pv` | `Boolean` | 否 | `false` | 是否禁用 SDK 在 `start()` 时自动上报的首次页面浏览（PV）事件。对于单页应用（SPA），强烈建议设为 `true`，并手动管理 PV 上报。 |
| `enable_stay_duration` | `Boolean` | 否 | `false` | 是否开启页面停留时长统计。 |
| `disable_heartbeat` | `Boolean` | 否 | `false` | 是否关闭心跳事件（`_be_active`）的上报，用于统计活跃用户。 |
| `disable_webid` | `Boolean` | 否 | `false` | 是否禁用网络请求获取 `web_id`，改为本地生成。本地生成的 ID 不保证全局唯一。 |

**示例：**

```javascript
Tea.init({
  app_id: 1234,
  channel: 'cn',
  log: true,
  disable_auto_pv: true,
});
```

### 2. `Tea.config(configs)`

配置 SDK 的公共参数、用户信息和其他动态设置。此方法可以在 `init` 之后、`start` 之前或之后的任何时间点多次调用，新的配置会与旧的配置进行合并（同名属性则覆盖）。

*   **`configs`** `<Object>`: 配置对象。

该对象接受两类属性：**SDK 预设字段**和**业务自定义字段**。

**预设字段（常用）：**

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| `user_unique_id` | `String` | **非常重要**。用户的唯一标识，如用户登录后的 `user_id`。设置后，TEA 会将此 ID 与设备 ID 关联，实现跨端、跨会话的用户行为追踪。 |
| `evtParams` | `Object` | 设置**事件级别**的公共属性。对象中的键值对会被合并到每一个上报事件的 `params` 字段中。 |

**业务自定义字段：**

除了预设字段外，你在 `config` 对象中设置的任何其他顶层键值对，都会被视为**会话级别**的公共属性（或称为“通用属性”），并被添加到每个上报事件的 `header.custom` 对象中。

**示例：**

```javascript
// 在用户登录成功后调用
Tea.config({
  // 设置用户唯一标识
  user_unique_id: 'user-a-12345',

  // 设置会话级别的公共属性
  project_name: 'MyWebApp',
  user_level: 'VIP',

  // 设置事件级别的公共属性
  evtParams: {
    theme: 'dark',
  }
});
```

### 3. `Tea.start()`

启动 SDK 的事件上报队列。这是一个**必须调用**的方法。在 `start()` 被调用之前，所有 `Tea.event()` 的调用都会被缓存在内存中。`start()` 执行后，SDK 会将缓存的事件以及后续的所有事件陆续发送到服务端。

此方法通常在 `init` 和 `config` 之后调用一次。

**示例：**

```javascript
Tea.start();
```

### 4. `Tea.event(eventName, params)`

上报一个自定义事件。这是最核心、最常用的埋点 API。

*   **`eventName`** `<String>`: 事件名称。必须是字符串，建议使用小写字母和下划线的组合，如 `button_click`。
*   **`params`** `<Object>` (可选): 事件的属性。一个包含描述该事件详细信息的键值对对象。属性值应为 `String` 或 `Number` 类型。

**示例：**

```javascript
// 上报一个不带参数的事件
Tea.event('enter_homepage');

// 上报一个带参数的事件
Tea.event('add_to_cart', {
  item_id: 9527,
  item_name: 'TEA SDK T-shirt',
  price: 99.9,
  currency: 'CNY'
});
```

> **注意**：请勿直接将 `Tea.event` 赋值给一个变量后调用，这可能导致 `this` 指向错误。例如，`const myEvent = Tea.event; myEvent('some_event');` 是**错误**的用法。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)

### 5. `Tea.predefinePageView(params)`

手动上报一次页面浏览（Page View）事件。事件名称固定为 `predefine_pageview`。

对于不刷新页面即可切换视图的单页应用（SPA），你必须在路由切换的钩子函数中手动调用此方法，以确保每次页面切换都被记录。

*   **`params`** `<Object>` (可选): 自定义的事件属性。可以用来覆盖或补充 SDK 自动采集的页面信息（如 `url`, `title` 等）。

**示例：**

```javascript
// 在 React Router 或 Vue Router 的路由守卫中调用
Tea.predefinePageView({
  page_name: 'user_profile', // 自定义页面名称
  from_route: '/settings'
});
```

### 6. `Tea.beaconEvent(eventName, params)`

使用浏览器的 `navigator.sendBeacon` API 来上报事件。此方法主要用于在**页面卸载（如关闭、刷新、跳转）前**的短时间内可靠地发送数据。它会立即发送事件，不走常规的事件队列。

*   **`eventName`** `<String>`: 事件名称。
*   **`params`** `<Object>` (可选): 事件属性。

**使用场景：** 统计用户在页面的总停留时长，或记录用户离开页面前的最后一个操作。

**示例：**

```javascript
window.addEventListener('beforeunload', () => {
  Tea.beaconEvent('page_leave', {
    stay_duration: Date.now() - pageOpenTime,
  });
});
```

> **注意**：`sendBeacon` 对上报的数据大小有限制（通常为 64KB），且存在一定的浏览器兼容性，不应作为常规事件上报的主要方式。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)

### 7. `Tea.getToken(callback)`

异步获取 SDK 内部生成的各种 ID。

*   **`callback`** `<Function>`: 获取成功后的回调函数，其参数为一个包含各种 ID 的对象。

**示例：**

```javascript
Tea.getToken((ids) => {
  console.log('Current TEA IDs:', ids);
  // 可能的返回结果：
  // {
  //   web_id: '70...9d',
  //   user_unique_id: 'user-a-12345',
  //   tobid(ssid): '2023...-...'
  // }
});
```

---

### 参考资料

*   [埋点SDK WEB 5.0 版本使用文档](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb)[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)
*   [WEB SDK 使用说明（V4）](https://bytedance.larkoffice.com/wiki/wikcnUGmq3tK9Snq3xCVWqovfQg)[[12]](https://bytedance.larkoffice.com/wiki/wikcnUGmq3tK9Snq3xCVWqovfQg?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnPR0CGl4AgbSsahRrXF3eMh)
