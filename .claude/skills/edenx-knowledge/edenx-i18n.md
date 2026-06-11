# EdenX 国际化 (i18n) 解决方案

国际化（Internationalization，缩写为 i18n）是让应用能够适应不同语言、地区和文化需求的关键工程实践。EdenX 提供了一套完整且强大的国际化解决方案，它深度集成了业界主流的 `i18next` 框架和公司内部的 `Starling` 翻译平台，帮助开发者高效地构建多语言应用。

本文档将介绍 EdenX i18n 的核心概念、基础用法、与 Starling 平台的集成，以及实现多语言支持的最佳实践。

## 核心概念

在深入实践之前，了解几个核心概念至关重要。

-   **`i18next`**: 一个功能强大的 JavaScript 国际化框架。它提供了语言检测、资源管理、插值、复数处理等所有你需要的功能。EdenX 的 i18n 能力正是构建于其上。

-   **`react-i18next`**: `i18next` 的官方 React 绑定库。它提供了 `useTranslation` Hook 和 `Trans` 组件，使得在 React 组件中使用 i18n 功能变得极其简单和自然。

-   **`Starling` 平台**: 公司内部的智能国际化翻译平台。它提供在线的文案管理、机器翻译、专业翻译等服务，能够实现**文案与代码的分离**，让非开发人员（如产品经理、运营）也能直接修改和发布文案，无需前端重新部署。

-   **命名空间 (Namespace)**: 用于组织和拆分翻译资源文件的方式。例如，你可以将公共的文案（如“确定”、“取消”）放在一个 `common` 命名空间下，而将特定页面的文案放在 `dashboard` 命名空间下。这有助于按需加载，减小首屏资源体积。

-   **语言代码**: 用于标识语言的字符串，遵循 ISO 639-1 标准（如 `en` 表示英语，`zh` 表示中文），有时也包含地区码（如 `en-US`, `zh-CN`）。

## 快速上手：本地化开发

首先，我们来看如何在不依赖外部平台的情况下，仅通过本地资源文件实现国际化。

### 1. 启用 i18n 插件

在 `edenx.config.ts` 中，引入并配置 `@edenx/plugin-i18n`。

```ts
// edenx.config.ts
import { defineConfig } from '@edenx/app-tools';
import { i18nPlugin } from '@edenx/plugin-i18n';

export default defineConfig({
  plugins: [
    /* ...其他插件 */
    i18nPlugin({
      // 开启语言检测功能
      localeDetection: true, 
    }),
  ],
});
```

### 2. 创建资源文件

在项目根目录下创建 `locales` 目录，并按照 `locales/<语言代码>/<命名空间>.json` 的结构组织翻译文件。

```
locales/
├── en/
│   └── translation.json
└── zh/
    └── translation.json
```

-   **`locales/en/translation.json`**:
    ```json
    {
      "welcome": "Welcome to EdenX",
      "greeting": "Hello, {{name}}!"
    }
    ```

-   **`locales/zh/translation.json`**:
    ```json
    {
      "welcome": "欢迎使用 EdenX",
      "greeting": "你好, {{name}}！"
    }
    ```

### 3. 配置运行时

在 `src/edenx.runtime.ts`（如果没有则创建）中，配置 i18n 的运行时选项，如支持的语言和默认语言。

```ts
// src/edenx.runtime.ts
import { defineRuntimeConfig } from '@edenx/runtime';

export default defineRuntimeConfig({
  i18n: {
    // i18next 的初始化选项
    initOptions: {
      lng: 'zh', // 默认语言
      fallbackLng: 'en', // 当某个 key 在当前语言中找不到时，回退到英语
      supportedLngs: ['zh', 'en'], // 支持的语言列表
      // 对于 React，必须设置此项以避免不必要的 HTML 转义
      interpolation: { escapeValue: false }, 
    },
  },
});
```

### 4. 在组件中使用

通过 `react-i18next` 提供的 `useTranslation` Hook 获取 `t` 函数，用它来翻译文本。

```tsx
import { useTranslation } from 'react-i18next';

function App() {
  const { t, i18n } = useTranslation();

  const switchLanguage = (lang) => {
    i18n.changeLanguage(lang);
  };

  return (
    <div>
      <h1>{t('welcome')}</h1>
      <p>{t('greeting', { name: '开发者' })}</p>

      <button onClick={() => switchLanguage('zh')}>中文</button>
      <button onClick={() => switchLanguage('en')}>English</button>
    </div>
  );
}
```

现在，你的应用就已经具备了基本的多语言切换能力。

## 高级功能

### 插值与格式化

`t` 函数的第二个参数可以传入一个对象，用于**插值**（即动态替换文案中的变量）。

-   **文案**: `"你有 {{count}} 条未读消息。"`
-   **调用**: `t('unreadMessages', { count: 5 })`
-   **结果**: `"你有 5 条未读消息。"`

`i18next` 还支持**格式化**，允许你对数字、日期、货币等进行特定于语言的格式化。

### 复数 (Plurals)

不同语言对复数的处理规则不同。`i18next` 能自动处理这些差异。你只需按照其约定的 key 后缀来提供不同数量的文案即可。

-   **`locales/en/translation.json`**:
    ```json
    {
      "apple": "one apple",
      "apple_plural": "{{count}} apples"
    }
    ```
-   **调用**: `t('apple', { count: 1 })` -> `"one apple"`, `t('apple', { count: 5 })` -> `"5 apples"`

中文通常没有复数形式，但你可以提供 `_0` 后缀来处理数量为零的特殊情况。

## 集成 Starling 平台

为了实现文案与代码的解耦和更专业的翻译流程，推荐使用 Starling 平台。EdenX i18n 插件提供了与 Starling 的无缝集成。

### 启用 Starling 集成

在 `edenx.config.ts` 的插件配置中，开启 Starling 集成并提供项目信息。

```ts
// edenx.config.ts
import { i18nPlugin } from '@edenx/plugin-i18n';

export default {
  plugins: [
    i18nPlugin({
      // ...其他配置
      starling: {
        // 在 Starling 平台申请的项目 ID
        projectId: 'YOUR_STARLING_PROJECT_ID',
        // 是否在本地开发时也从 Starling 拉取最新文案
        dev: true,
        // 是否在生产构建时将 Starling 文案打包进去
        prod: true,
      },
    }),
  ],
};
```

### 工作流变化

启用 Starling 集成后，开发工作流变为：

1.  **文案提取**: 使用 Starling 官方提供的 `@ies/starling-cli` 工具扫描项目代码，自动提取硬编码的中文文案。
2.  **上传至平台**: CLI 会将提取的文案上传到 Starling 平台，并自动生成唯一的翻译键（key）。
3.  **翻译与管理**: 在 Starling 平台上，可以对文案进行翻译、审核和版本管理。
4.  **自动拉取**: EdenX 应用在本地开发或生产构建时，会自动从 Starling 平台拉取最新的、已发布的文案资源。本地的 `locales` 目录可以作为开发初期的占位或回退方案，但最终线上的文案来源是 Starling。

## 常见问题与最佳实践 (FAQ)

**Q1: 如何处理带 HTML 标签的复杂文案？**

**A1**: 对于包含 `<a>`、`<strong>` 等 HTML 标签的文案，不应将整个 HTML 字符串放在翻译资源中，这会带来 XSS 安全风险。正确的做法是使用 `react-i18next` 提供的 `Trans` 组件。

-   **`translation.json`**:
    ```json
    {
      "terms": "请阅读并同意我们的<1>服务条款</1>。"
    }
    ```
-   **组件代码**:
    ```tsx
    import { Trans } from 'react-i18next';

    function Terms() {
      return (
        <p>
          <Trans i18nKey="terms">
            请阅读并同意我们的<a href="/terms">服务条款</a>。
          </Trans>
        </p>
      );
    }
    ```
    `Trans` 组件会智能地将翻译文本中的 `<1>` 等占位符替换为子组件中的对应元素，既保证了翻译的灵活性，又确保了代码的安全性。

**Q2: 语言的检测顺序是怎样的？如何自定义？**

**A2**: EdenX i18n 插件默认的语言检测顺序是：URL 路径 (`/en/home`) -> Cookie -> `Accept-Language` 请求头 -> 默认语言。你可以通过 `localeDetection.order` 配置项自定义这个顺序。
```ts
// edenx.config.ts
i18nPlugin({
  localeDetection: {
    order: ['cookie', 'path', 'header'],
  },
}),
```

**Q3: 在 SSR 环境下，如何确保服务端和客户端的语言一致？**

**A3**: 这是 SSR i18n 的一个关键问题。EdenX 的解决方案是：
1.  **服务端检测**: 在服务端接收到请求时，根据检测顺序（如从 Cookie 或请求头中）确定当前请求的语言。
2.  **数据注入**: 服务端使用该语言渲染页面，并将该语言代码和所需的翻译资源注入到 HTML 的 `window` 对象下的一个特殊变量中。
3.  **客户端同步**: 客户端的 i18n 实例在初始化时，会首先从 `window` 对象中读取服务端的语言和资源，从而确保初始状态的无缝衔接，避免了客户端重新检测语言可能导致的闪烁或内容不匹配问题。这一切都是框架自动完成的。

**Q4: 我应该如何组织我的命名空间 (namespaces)？**

**A4**: 良好的命名空间组织是大型项目可维护性的关键。
-   **`common`**: 创建一个 `common` 命名空间，用于存放所有页面都可能用到的通用文案，如按钮文本（保存、取消）、表单校验提示、全局通知等。
-   **按页面/功能划分**: 为每个主要功能模块或复杂页面创建独立的命名空间，如 `dashboard`, `userProfile`, `settings`。
-   **按需加载**: 在组件中，只加载当前需要的命名空间，而不是一次性加载所有。
    ```tsx
    // 只加载 'dashboard' 和 'common' 命名空间的文案
    const { t } = useTranslation(['dashboard', 'common']);
    ```
    这能有效减少初始加载的资源量，提升性能。
