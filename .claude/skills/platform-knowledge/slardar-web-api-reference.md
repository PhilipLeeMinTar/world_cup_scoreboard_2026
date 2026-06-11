# 3. API 参考

本章节详细介绍了 `@slardar/web` SDK 的核心 API，包括初始化、自定义数据上报和上下文信息设置。

**快速索引**
- [核心 API](#核心-api)
  - [`init(options)`](#initoptions)
  - [`start()`](#start)
  - [`setUser(userInfo)`](#setuseruserinfo)
  - [`setContext(context)`](#setcontextcontext)
  - [`addBreadcrumb(breadcrumb)`](#addbreadcrumbbreadcrumb)
  - [`captureException(error, options)`](#captureexceptionerror-options)
  - [`reportEvent(name, metrics, dimensions)`](#reporteventname-metrics-dimensions)
- [高级配置建议](#高级配置建议)
  - [采样率 (sampleRate)](#采样率-samplerate)
  - [环境与版本](#环境与版本)
  - [数据过滤与脱敏](#数据过滤与脱敏)

---

## 核心 API

所有 API 都通过 `browserClient` 函数进行调用，第一个参数是 API 名称，后续参数是该 API 所需的配置。

### `init(options)`

初始化 Slardar SDK。这是**必须调用**的第一个 API。

```typescript
import browserClient from '@slardar/web';

browserClient('init', {
  bid: 'YOUR_BID',
  // ... 其他可选配置
});
```

**核心参数 (`options`)**:

| 参数 | 类型 | 是否必需 | 描述 |
| :--- | :--- | :--- | :--- |
| `bid` | `string` | 是 | 你的应用在 Slardar 平台的唯一标识。 |
| `debug` | `boolean` | 否 | 是否开启 Debug 模式。开启后，数据将在控制台打印而不会真实上报。**严禁用于生产环境**。默认为 `false`。 |
| `region` | `string` | 否 | 指定上报区域，如 `'SG'` (新加坡)。默认为 `'CN'` (中国)。 |
| `sampleRate` | `number` | 否 | 全局采样率，取值范围 `0` 到 `1`。例如 `0.5` 表示 50% 的会话数据会被上报。详见下方“采样率”部分。 |
| `release` | `string` | 否 | 当前应用的版本号，例如 Git commit hash 或版本号字符串。强烈建议设置，便于按版本追溯问题。 |
| `env` | `string` | 否 | 当前环境标识，如 `'development'`, `'staging'`, `'production'`。 |

### `start()`

启动 Slardar 的自动监控和数据上报。在 `init` 之后调用。

```typescript
browserClient('start');
```

此 API 无参数。调用后，SDK 将开始监听全局错误、网络请求等事件。

### `setUser(userInfo)`

设置当前用户信息。这些信息会上报并附加到后续的所有监控数据中，便于你根据用户特征筛选和分析问题。

```typescript
browserClient('setUser', {
  id: 'user-12345',
  name: 'Zhang San',
  email: 'zhangsan@example.com',
});
```

**参数 (`userInfo`)**:

| 字段 | 类型 | 描述 |
| :--- | :--- | :--- |
| `id` | `string` | 用户的唯一标识。 |
| `name` | `string` | 用户名。 |
| `email` | `string` | 用户邮箱。 |
| `...` | `any` | 你可以添加任何自定义字段。 |

> **隐私注意**：请**不要**上报未脱敏的、高度敏感的用户个人信息（如身份证、手机号）。所有上报的用户数据都应遵循公司的隐私合规政策。通常，使用内部系统的用户 ID (`user_id`) 是安全且推荐的做法。

### `setContext(context)`

设置全局的自定义上下文信息。与 `setUser` 类似，但更通用，适用于任何非用户维度的信息，如实验分组、AB 测试标签、业务模块等。

```typescript
browserClient('setContext', {
  feature_flags: {
    new_editor: true,
    dark_mode: false,
  },
  business_module: 'OrderManagement',
});
```

设置的 `context` 会与之后的每一条日志一同上报。你可以随时调用 `setContext` 来更新它，新的值会覆盖旧的值。

### `addBreadcrumb(breadcrumb)`

添加一个用户行为“面包屑”。面包屑是一个记录用户交互路径的日志流，当错误发生时，它会一并上报，帮助你理解用户在遇到问题前执行了哪些操作。

SDK 会自动记录页面跳转、点击等行为。你也可以用此 API 添加自定义面包屑。

```typescript
// 当用户执行一个关键业务操作时
browserClient('addBreadcrumb', {
  category: 'business.action',
  message: 'User clicked "Submit Order" button',
  level: 'info',
  data: {
    orderId: 'temp_order_id_123',
    itemCount: 3,
  },
});
```

### `captureException(error, options)`

主动上报一个被 `try...catch` 捕获的错误或异常。

虽然 Slardar 会自动捕获全局未处理的异常，但在某些情况下，你可能希望主动上报一个被你捕获但仍需关注的错误。

```typescript
try {
  const data = JSON.parse(invalidJsonString);
} catch (e) {
  console.error('Failed to parse user config:', e);

  // 主动将这个错误上报给 Slardar
  browserClient('captureException', e, {
    extra: {
      rawJson: invalidJsonString,
      source: 'UserConfigParsing',
    },
  });
}
```

**参数**:
- `error`: `Error` 对象或任何可以被序列化的值。
- `options.extra`: `object`，附加的额外信息，便于排查问题。

### `reportEvent(name, metrics, dimensions)`

上报一个自定义事件。这是 Slardar 最强大的功能之一，允许你监控任何你关心的业务指标。

- **`name`**: 事件名称，字符串。
- **`metrics`**: 指标集合，`{ [key: string]: number }`，用于记录可聚合的数值，如耗时、数量。
- **`dimensions``**: 维度集合，`{ [key: string]: string | number }`，用于记录事件发生时的分类信息，如状态、类型。

**示例：监控核心功能的耗时和成功率**

```typescript
const startTime = Date.now();

performCriticalTask()
  .then(result => {
    browserClient('reportEvent', 'CriticalTask', {
      // 指标：耗时和成功标记
      duration: Date.now() - startTime,
      success_count: 1,
      failure_count: 0,
    }, {
      // 维度：任务类型
      task_type: result.type,
      status: 'success',
    });
  })
  .catch(error => {
    browserClient('reportEvent', 'CriticalTask', {
      // 指标
      duration: Date.now() - startTime,
      success_count: 0,
      failure_count: 1,
    }, {
      // 维度
      task_type: 'unknown',
      status: 'failure',
    });
  });
```

> **注意**：API 名称（如 `reportEvent`）可能在不同 SDK 版本中存在差异（例如，也可能被称为 `log` 或 `report`）。请以你所使用的 SDK 版本的实际文档为准，但其核心概念（事件名、指标、维度）是通用的。

## 高级配置建议

### 采样率 (sampleRate)

对于流量巨大的应用，全量上报所有监控数据可能会带来不必要的成本和噪音。`sampleRate` 配置允许你只上报一部分用户的会话数据。

-   **`sampleRate: 1`**：上报 100% 的会话数据（默认）。
-   **`sampleRate: 0.1`**：上报 10% 的会话数据。
-   **`sampleRate: 0`**：不上报任何会话数据。

SDK 会在会话开始时（页面加载时）决定是否对当前用户进行采样。一旦决定采样，该用户在本次会话中的所有数据都会被上报。如果未被采样，则本次会话的任何数据都不会上报。

### 环境与版本

强烈建议在 `init` 时配置 `env` 和 `release`：

```typescript
browserClient('init', {
  bid: 'YOUR_BID',
  env: process.env.NODE_ENV, // 'development', 'production', etc.
  release: process.env.GIT_COMMIT_HASH, // 例如，从构建环境中注入
});
```

-   **`env`**: 让你可以在 Slardar 平台上轻松地区分来自开发、测试和生产环境的数据。
-   **`release`**: 将每个错误和性能问题都关联到一个确切的代码版本，极大地简化了问题定位和修复验证的流程。你可以使用 Git 的 commit hash、发布的版本号或任何能够唯一标识代码版本的字符串。

### 数据过滤与脱敏

在某些情况下，你可能需要阻止特定的错误或网络请求被上报，或者对上报数据中的敏感信息进行处理。

Slardar 的 `init` 配置提供了 `beforeSend`、`beforeBreadcrumb` 等钩子函数，允许你在数据发送前进行拦截和修改。

**示例：过滤掉特定的错误，并脱敏用户数据**

```typescript
browserClient('init', {
  bid: 'YOUR_BID',
  
  // 在数据发送前的钩子
  beforeSend: (event) => {
    // 场景1：如果错误信息包含 "ignore this error"，则不发送此事件
    if (event.exception?.values?.[0]?.value?.includes('ignore this error')) {
      return null; // 返回 null 会阻止事件上报
    }

    // 场景2：脱敏面包屑中的敏感信息
    if (event.breadcrumbs) {
      event.breadcrumbs.forEach(b => {
        if (b.category === 'auth.login' && b.data?.password) {
          b.data.password = '[REDACTED]'; // 脱敏密码
        }
      });
    }

    return event; // 返回 event 对象以继续上报
  },
});
```

使用这些钩子可以让你对上报的数据有完全的控制权，确保数据的合规性和有效性。
