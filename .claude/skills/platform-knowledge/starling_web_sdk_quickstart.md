# Starling Web/JS SDK 快速入门

本指南为前端工程师提供一个详细的、可操作的 Starling Web/JS SDK 接入教程。无论你是使用 React、Vue 还是 Next.js，遵循本指南，你将能快速地为你的项目集成 Starling 的国际化能力。

## 目录
- [1. 前置条件](#1-前置条件)
- [2. 安装与初始化](#2-安装与初始化)
  - [2.1. 安装 SDK](#21-安装-sdk)
  - [2.2. 初始化 SDK](#22-初始化-sdk)
- [3. 使用指南](#3-使用指南)
  - [3.1. 基本用法 `t()` 函数](#31-基本用法-t-函数)
  - [3.2. 插值 (Interpolation)](#32-插值-interpolation)
  - [3.3. 复数 (Plurals)](#33-复数-plurals)
  - [3.4. 日期/数字格式化](#34-日期数字格式化)
  - [3.5. Key 命名与目录结构](#35-key-命名与目录结构)
- [4. 框架集成指南](#4-框架集成指南)
  - [4.1. React / Next.js (CSR)](#41-react--nextjs-csr)
  - [4.2. Next.js (SSR)](#42-nextjs-ssr)
  - [4.3. Vue.js (以 Vue 3 为例)](#43-vuejs-以-vue-3-为例)
- [5. 运行时拉取 vs. 构建期注入](#5-运行时拉取-vs-构建期注入)
  - [5.1. 缓存、降级与 Fallback](#51-缓存降级与-fallback)
- [6. CLI / 文案提取](#6-cli--文案提取)
- [7. 调试与测试](#7-调试与测试)
- [8. 常见错误与解决方案](#8-常见错误与解决方案)
- [9. 术语表](#9-术语表)
- [10. 参考链接](#10-参考链接)

---

### 1. 前置条件

在开始之前，请确保你已完成以下准备工作：

*   **平台访问权限**：你拥有 Starling 平台 (`https://starling.bytedance.net/`) 的访问权限。
*   **创建项目和空间**：已在 Starling 平台上创建了你的应用所对应的 **项目 (Project)** 和 **空间 (Namespace)**。[[37]](https://bytedance.larkoffice.com/wiki/wikcnBpiRndVazp1or6rJKclZfb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcncUkM4wkIQ4Kmykbv4BrxAg)
*   **获取认证信息**：
    *   **项目 ID (Project ID)** 和 **空间 ID (Namespace ID)**：进入你的项目空间后，可以直接在浏览器地址栏中找到。例如，URL `https://starling.bytedance.net/project_detail/12345/space/67890` 中，`12345` 是项目 ID，`67890` 是空间 ID。::cite[30, 35]
    *   **API Key**：在项目的 **“设置”** -> **“开发设置”** 页面获取。这是 SDK 在客户端拉取文案时推荐的认证方式。[[37]](https://bytedance.larkoffice.com/wiki/wikcnBpiRndVazp1or6rJKclZfb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcncUkM4wkIQ4Kmykbv4BrxAg)
    *   **AK/SK (Access Key & Secret Key)**：在平台的 **“个人中心”** -> **“AK/SK”** 页面获取。这主要用于 CLI 工具或服务端 API 调用。[[30]](https://bytedance.larkoffice.com/wiki/wikcnanUTPTE83VrbuiMmAkoUKe?from=lark_search_qa&ccm_open_type=lark_search_qa#TeqQd8oYeoSiKkx6gWockml0njh)

### 2. 安装与初始化

#### 2.1. 安装 SDK

Starling 的前端生态主要包含两个核心包：

*   `@ies/starling_intl`：基于 `i18next` 的核心国际化框架，提供翻译能力。[[41]](https://cloud.bytedance.net/developer/docs/edenx/docs/b768ac014742b4e0e62e8c805e6f38d5/d615f8c6dd2305f1185d43a56d97b459)
*   `@ies/starling_client`：用于在浏览器环境（CSR）从 Starling 服务端拉取文案。[[41]](https://cloud.bytedance.net/developer/docs/edenx/docs/b768ac014742b4e0e62e8c805e6f38d5/d615f8c6dd2305f1185d43a56d97b459)

请使用你的项目包管理器进行安装（需要配置公司内部 bnpm registry）：

```bash
# npm
npm install @ies/starling_intl @ies/starling_client --registry=https://bnpm.byted.org

# yarn
yarn add @ies/starling_intl @ies/starling_client --registry=https://bnpm.byted.org

# pnpm
pnpm add @ies/starling_intl @ies/starling_client --registry=https://bnpm.byted.org
```

对于 SSR 或 Node.js 环境，你需要安装 `@ies/starling_node` 替代 `@ies/starling_client`：

```bash
npm install @ies/starling_node --registry=https://bnpm.byted.org
```

#### 2.2. 初始化 SDK

初始化的核心逻辑是：**先拉取文案，再初始化 i18n 实例，最后渲染应用**。这确保了应用在渲染时已经具备了所需的翻译文案，避免了页面抖动或显示原始 Key。[[21]](https://bytedance.larkoffice.com/wiki/wikcnob2KYyFF35ZBQwS4ATcaPc?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnO8AaWai8GS6IWWmWVwm9rf)

创建一个专门的 i18n 初始化文件（例如 `src/i18n.ts`）：

```typescript
// src/i18n.ts
import I18n from '@ies/starling_intl';
import Starling from '@ies/starling_client';

// 从某个地方获取当前语言，例如 localStorage 或 URL 参数
const getCurrentLanguage = () => {
  return localStorage.getItem('language') || 'zh-CN'; // 默认为中文
};

const lang = getCurrentLanguage();

// 1. 配置 Starling Client
const starlingClient = new Starling({
  apiKey: 'YOUR_API_KEY',         // 替换为你的项目 API Key
  projectId: 12345,                // 替换为你的项目 ID
  namespace: 'your_namespace_name',// 替换为你的空间名称
  locale: lang,                    // 当前需要拉取的语言
  // 对于火山引擎外部署，可能需要指定 host
  // zoneHost: 'https://starling.volcengineapi.com',
});

// 2. 封装 i18n 初始化函数
function initializeI18n(resources: object) {
  return new Promise<void>((resolve) => {
    I18n.init({
      resources,
      lng: lang,
      fallbackLng: 'zh-CN', // 兜底语言
      defaultNS: 'translation', // 默认 namespace
      react: {
        useSuspense: false, // 推荐在 Web 端关闭
      },
      interpolation: {
        escapeValue: false, // React/Vue 已内置 XSS 防护
      },
    }, () => resolve());
  });
}

// 3. 导出一个统一的初始化函数
export async function initI18n() {
  try {
    const resources = await starlingClient.load();
    await initializeI18n({ [lang]: { translation: resources } });
    console.log('Starling i18n initialized successfully.');
  } catch (error) {
    console.error('Failed to initialize Starling i18n:', error);
    // 在出错时进行降级，例如加载本地兜底文案
    await initializeI18n({});
  }
}
```

然后在你的应用入口文件（如 `src/main.tsx` 或 `src/main.ts`）中调用它：

```typescript
// src/main.tsx (以 React 为例)
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { initI18n } from './i18n';

async function startApp() {
  await initI18n(); // 等待 i18n 初始化完成

  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

startApp();
```

### 3. 使用指南

初始化完成后，你就可以在项目中使用 `I18n.t()` 方法来获取文案了。

#### 3.1. 基本用法 `t()` 函数

`t` 函数接收一个 Key 作为参数，返回对应的翻译字符串。

```typescript
import I18n from '@ies/starling_intl';

const welcomeMessage = I18n.t('common.welcome'); // -> "欢迎"

// 提供一个默认值作为 Fallback
const buttonText = I18n.t('button.submit', { defaultValue: '提交' });
```

#### 3.2. 插值 (Interpolation)

如果你的文案中包含动态变量，可以使用插值功能。占位符遵循 ICU 语法。[[21]](https://bytedance.larkoffice.com/wiki/wikcnob2KYyFF35ZBQwS4ATcaPc?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnO8AaWai8GS6IWWmWVwm9rf)

*   **Starling 平台文案**:
    *   Key: `greeting.user`
    *   中文: `你好, {name}！`
    *   English: `Hello, {name}!`

*   **代码调用**:

```typescript
const personalizedGreeting = I18n.t('greeting.user', {
  defaultValue: '你好, {name}！',
  name: '张三',
});
// -> "你好, 张三！"
```

#### 3.3. 复数 (Plurals)

ICU 语法支持强大的复数处理能力，以适应不同语言的复数规则。[[21]](https://bytedance.larkoffice.com/wiki/wikcnob2KYyFF35ZBQwS4ATcaPc?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnO8AaWai8GS6IWWmWVwm9rf)

*   **Starling 平台文案**:
    *   Key: `inbox.new_messages`
    *   中文: `你有 {count, plural, =0 {没有新消息} =1 {1 条新消息} other {# 条新消息}}。`
    *   English: `You have {count, plural, =0 {no new messages} =1 {one new message} other {# new messages}}. `

*   **代码调用**:

```typescript
const message1 = I18n.t('inbox.new_messages', { count: 1 });
// -> "你有 1 条新消息。"

const message5 = I18n.t('inbox.new_messages', { count: 5 });
// -> "你有 5 条新消息。"

const messageEn = I18n.t('inbox.new_messages', { count: 5 }); // 假设当前语言为 en
// -> "You have 5 new messages."
```

#### 3.4. 日期/数字格式化

同样利用 ICU 语法，可以实现与 Locale 相关的日期和数字格式化。

*   **Starling 平台文案**:
    *   Key: `common.date`
    *   中文: `今天的日期是 {ts, date, long}`
    *   English: `Today is {ts, date, long}`

*   **代码调用**:

```typescript
const today = I18n.t('common.date', { ts: new Date() });
// 中文环境下 -> "今天的日期是 2025年12月2日"
// 英文环境下 -> "Today is December 2, 2025"
```

#### 3.5. Key 命名与目录结构

*   **Key 命名**：建议采用 `页面/模块.组件.功能` 的分层结构，例如 `login.form.username.placeholder`。这有助于管理和快速定位文案。
*   **目录结构**：建议将拉取或下载的语言文件存放在 `src/locales` 目录下，按语言分子目录，如 `src/locales/zh-CN/translation.json`。

### 4. 框架集成指南

为了更优雅地在框架中使用，推荐结合 `react-i18next` 或 `vue-i18next`。

#### 4.1. React / Next.js (CSR)

安装 `react-i18next`:

```bash
npm install react-i18next
```

在应用根组件包裹 `I18nextProvider`：

```tsx
// src/App.tsx
import React from 'react';
import { I18nextProvider } from 'react-i18next';
import I18n from '@ies/starling_intl';
import MyComponent from './MyComponent';

function App() {
  return (
    <I18nextProvider i18n={I18n.i18nInstance.instance}>
      <MyComponent />
    </I18nextProvider>
  );
}

export default App;
```

在组件中使用 `useTranslation` Hook：

```tsx
// src/MyComponent.tsx
import React from 'react';
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('common.welcome', { defaultValue: '欢迎' })}</h1>
      <p>{t('greeting.user', { name: '访客', defaultValue: '你好, {name}!' })}</p>
    </div>
  );
}

export default MyComponent;
```

#### 4.2. Next.js (SSR)

对于 Next.js 的 SSR 场景，挑战在于如何在服务端获取文案并传递给客户端。

1.  **安装 `@ies/starling_node`**。
2.  **创建服务端 i18n 实例管理器**：

    ```typescript
    // lib/i18n-server.ts
    import Starling from '@ies/starling_node';

    // 缓存 Starling 实例以提高性能
    const starlingInstances = new Map<string, Starling>();

    export function getStarlingInstance(namespace: string) {
      if (!starlingInstances.has(namespace)) {
        const instance = new Starling({
          apiKey: 'YOUR_API_KEY',
          projectId: 12345,
          namespace: namespace,
          // 更多服务端配置，如缓存策略
        });
        starlingInstances.set(namespace, instance);
      }
      return starlingInstances.get(namespace)!;
    }
    ```

3.  **在 `getServerSideProps` 中获取文案**：

    ```tsx
    // pages/index.tsx
    import { GetServerSideProps } from 'next';
    import I18n from '@ies/starling_intl';
    import { getStarlingInstance } from '../lib/i18n-server';
    import MyComponent from '../components/MyComponent';
    import { I18nextProvider } from 'react-i18next';

    export default function HomePage() {
      return (
        <I18nextProvider i18n={I18n.i18nInstance.instance}>
          <MyComponent />
        </I18nextProvider>
      );
    }

    export const getServerSideProps: GetServerSideProps = async (context) => {
      const locale = context.locale || 'zh-CN';
      const starlingInstance = getStarlingInstance('your_namespace_name');

      const { data: resources } = await starlingInstance.getPackage(locale);

      // 在服务端初始化 i18n 实例
      await new Promise<void>(resolve => {
        I18n.init({ 
            resources: { [locale]: { translation: resources } },
            lng: locale,
            /* ...其他配置... */
         }, () => resolve());
      });

      return {
        props: {
          // 将初始化的 i18n 数据传递给客户端
          initialI18nStore: { [locale]: { translation: resources } },
          initialLanguage: locale,
        },
      };
    };
    ```

4.  **客户端使用 props 初始化**：在 `_app.tsx` 中接收 `initialI18nStore` 并初始化，避免客户端再次请求。

> **注意**：以上为简化示例。实际生产中，推荐使用 `next-i18next` 等成熟的 Next.js i18n 库，它们对 SSR 有更好的封装和支持。你可以将 Starling SDK 作为其 `backend` 插件来集成。::cite[6, 10]

#### 4.3. Vue.js (以 Vue 3 为例)

对于 Vue，可以使用 `vue-i18next` 插件。

1.  **安装 `vue-i18next`**:

    ```bash
    npm install vue-i18next
    ```

2.  **创建并配置插件**:

    ```typescript
    // src/plugins/i18n.ts
    import { App } from 'vue';
    import I18n from '@ies/starling_intl';
    import { createI18n } from 'vue-i18next';

    const i18n = createI18n({
      lng: I18n.language,
      resources: I18n.store.data,
    });

    export default {
      install: (app: App) => {
        app.use(i18n);
      },
    };
    ```

3.  **在 `main.ts` 中使用**:

    ```typescript
    // src/main.ts
    import { createApp } from 'vue';
    import App from './App.vue';
    import { initI18n } from './i18n'; // 复用之前的初始化逻辑
    import i18nPlugin from './plugins/i18n';

    async function startApp() {
      await initI18n();
      const app = createApp(App);
      app.use(i18nPlugin);
      app.mount('#app');
    }

    startApp();
    ```

4.  **在组件中使用**:

    ```vue
    <template>
      <div>
        <h1>{{ $t('common.welcome') }}</h1>
        <p>{{ $t('greeting.user', { name: 'Vue 用户' }) }}</p>
      </div>
    </template>

    <script setup lang="ts">
    import { useTranslation } from 'vue-i18next';

    const { t } = useTranslation();

    // 也可以在 <script> 中使用
    const message = t('common.welcome');
    </script>
    ```

### 5. 运行时拉取 vs. 构建期注入

*   **运行时拉取**：即上文示例中的 `starlingClient.load()` 方式，适合绝大多数场景。
*   **构建期注入**：如果希望将文案作为兜底或实现纯静态站点，可以在构建流程中加入 CLI 命令。

    ```bash
    # package.json scripts
    "scripts": {
      "build:locales": "starling download",
      "build": "npm run build:locales && next build"
    }
    ```

    `starling download` 命令会根据 `starling.config.js` 的配置，将文案下载到本地（如 `src/locales`）。[[29]](https://bytedance.feishu.cn/docx/NsWedBwiSoD2Fux1ZHOcrFfMnod)

    然后，在 i18n 初始化时，你可以先加载这些本地文件作为初始数据，再异步去拉取最新文案进行更新。

#### 5.1. 缓存、降级与 Fallback

*   **缓存**：`@ies/starling_client` 默认会将拉取的文案缓存在浏览器的 `localStorage` 中，后续访问会优先使用缓存，并通过版本号检查更新，有效提升加载速度。[[41]](https://cloud.bytedance.net/developer/docs/edenx/docs/b768ac014742b4e0e62e8c805e6f38d5/d615f8c6dd2305f1185d43a56d97b459)
*   **降级 (Fallback)**：当指定语言的翻译不存在时，i18next 会自动降级到 `fallbackLng` 指定的语言。例如，`en-US` 的某个 Key 没翻译，但 `en` 翻译了，会显示 `en` 的版本。
*   **默认值**：作为最后的防线，在 `t` 函数中提供 `defaultValue` 是一个好习惯，确保即时所有翻译和降级都失败，用户也能看到一段可理解的文本，而不是空白或原始 Key。

### 6. CLI / 文案提取

`@ies/starling-cli` 是提升国际化效率的关键工具。[[26]](https://bytedance.feishu.cn/docx/UInpdvubCoo7xtxiTiecTJrhnse)

1.  **初始化配置**：在项目根目录运行 `starling init`，会引导你生成 `starling.config.js` 配置文件，其中包含项目信息、扫描规则等。[[29]](https://bytedance.feishu.cn/docx/NsWedBwiSoD2Fux1ZHOcrFfMnod)
2.  **扫描文案**：`starling scan` 会根据配置扫描你的源代码，找出所有硬编码的中文文案和已使用 `t()` 函数包裹的文案。[[29]](https://bytedance.feishu.cn/docx/NsWedBwiSoD2Fux1ZHOcrFfMnod)
3.  **上传平台**：`starling upload` 将扫描结果上传到 Starling 平台。[[29]](https://bytedance.feishu.cn/docx/NsWedBwiSoD2Fux1ZHOcrFfMnod)
4.  **自动替换**：`starling replace` 会将代码中的硬编码文案替换为 `t('some_key', { defaultValue: '原始文案' })` 的形式。[[29]](https://bytedance.feishu.cn/docx/NsWedBwiSoD2Fux1ZHOcrFfMnod)

一个完整的自动化流程可以通过 `starling pipeline` 命令串联起来，实现从扫描到发布的自动化。[[29]](https://bytedance.feishu.cn/docx/NsWedBwiSoD2Fux1ZHOcrFfMnod)

### 7. 调试与测试

*   **伪本地化 (Pseudo-localization)**：在 i18next 初始化时，可以配置 `debug: true` 和 `saveMissing: true`。对于缺失的 Key，i18next 会自动上报或以 Key 本身作为显示内容，方便快速定位未翻译的文案。
*   **环境切换**：Starling 支持 `test`, `gray`, `production` 等不同环境。`@ies/starling_client` 和 CLI 都可以通过配置参数来拉取不同环境的文案，方便测试。[[31]](https://bytedance.larkoffice.com/docx/R1eGdnPO7o62F6xzfmycAWnnn6f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcn1aOR0VOwiPRmpYNo4iaH3f)
*   **日志与埋点**：SDK 内部集成了日志和监控埋点。在初始化时配置 `handleError` 回调或监听相关事件，可以捕获加载失败等异常情况，并上报到你自己的监控系统。[[41]](https://cloud.bytedance.net/developer/docs/edenx/docs/b768ac014742b4e0e62e8c805e6f38d5/d615f8c6dd2305f1185d43a56d97b459)

> **注意**：关于埋点的具体实现，请以 Starling 官方提供的最新 SDK 文档为准。

### 8. 常见错误与解决方案

*   **动态 Key / 拼接字符串**
    *   **错误**：`t('prefix.' + variable)`
    *   **问题**：CLI 无法静态分析出完整的 Key，导致文案无法被提取和翻译。
    *   **解决**：避免拼接 Key。应使用完整的 Key，将动态部分作为参数传入。例如 `t('prefix.key', { dynamic_part: variable })`。

*   **XSS 风险**
    *   **问题**：将包含用户输入或富文本的变量直接插入到翻译中，可能导致 XSS 攻击。
    *   **解决**：React/Vue 默认会对插值内容进行转义。如果需要渲染 HTML，请使用框架提供的 `dangerouslySetInnerHTML` (React) 或 `v-html` (Vue)，并确保 HTML 内容是可信的或经过严格过滤的。

*   **缺失翻译**
    *   **现象**：页面显示原始 Key 或 `defaultValue`。
    *   **排查**：
        1.  确认该 Key 是否已在 Starling 平台发布到当前环境。
        2.  检查 SDK 初始化时 `locale` 和 `namespace` 是否正确。
        3.  清除浏览器 `localStorage` 缓存后重试。

*   **SSR 与 Hydration 不一致**
    *   **现象**：Next.js 页面在开发模式下报 “Text content does not match server-rendered HTML” 警告。
    *   **原因**：通常是由于服务端和客户端的 i18n 状态不一致导致，例如客户端又重新拉取了一次文案。
    *   **解决**：确保客户端的初始状态完全来自服务端的 props，如 [4.2. Next.js (SSR)](#42-nextjs-ssr) 所示。

### 9. 术语表

| 术语 (Term) | 中文 | 解释 |
| --- | --- | --- |
| SDK | 软件开发工具包 | 指 `@ies/starling_intl`, `@ies/starling_client` 等 npm 包。 |
| CLI | 命令行界面 | 指 `@ies/starling-cli` 工具。 |
| ICU Message Format | - | 一套用于处理复数、性别、插值等的国际化文本格式标准。 |
| Hydration | 激活/注水 | SSR 中客户端 JS 接管静态 DOM 的过程。 |
| Fallback | 降级/兜底 | 获取翻译失败时显示的备用内容。 |

### 10. 参考链接

*   Starling 平台地址: `https://starling.bytedance.net/`
*   `@ies/starling-cli` 完全指南: [飞书文档](https://bytedance.feishu.cn/docx/UInpdvubCoo7xtxiTiecTJrhnse)
*   `react-i18next` 官方文档: [https://react.i18next.com/](https://react.i18next.com/)
*   `i18next` 官方文档: [https://www.i18next.com/](https://www.i18next.com/)
