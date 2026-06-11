# EdenX 数据管理与获取

EdenX 提供了一套强大的数据管理方案，其核心是与约定式路由深度集成的数据获取机制——**Data Loader**。这套机制不仅简化了前后端数据交互的流程，还在性能优化、代码组织和开发体验上提供了显著优势。

本文档将详细阐述 EdenX 的数据获取理念、`loader` 函数的使用方法、在不同渲染环境下的行为差异，以及错误处理和缓存策略等高级主题。

## 核心概念：Data Loader

在 EdenX 的约定式路由体系中，每个路由组件（无论是 `page.tsx`、`layout.tsx` 还是 `$.tsx`）都可以拥有一个与之对应的 `.data.ts` 文件。这个文件可以导出一个名为 `loader` 的异步函数，我们称之为 **Data Loader**。

`loader` 函数会在其对应的路由组件**渲染之前**执行，它的核心职责是为该组件准备所需的数据。

**文件结构示例**：

```
.
└── src/
    └── routes/
        └── user/
            ├── profile/
            │   ├── layout.data.ts  # user/profile 布局的数据
            │   ├── layout.tsx
            │   ├── page.data.ts    # user/profile 页面的数据
            │   └── page.tsx
            └── list/
                ├── page.data.ts    # user/list 页面的数据
                └── page.tsx
```

在 `.data.ts` 文件中定义 `loader` 函数：

```ts
// src/routes/user/profile/page.data.ts
export interface UserProfile {
  name: string;
  email: string;
  // ... 其他字段
}

export const loader = async (): Promise<UserProfile> => {
  const response = await fetch('/api/user/profile');
  if (!response.ok) {
    throw new Response('Failed to fetch user profile', { status: 500 });
  }
  const data = await response.json();
  return data;
};
```

在路由组件中，通过 `@edenx/runtime/router` 提供的 `useLoaderData` Hook 来获取 `loader` 函数返回的数据：

```tsx
// src/routes/user/profile/page.tsx
import { useLoaderData } from '@edenx/runtime/router';
import type { UserProfile } from './page.data';

export default function UserProfilePage() {
  const profile = useLoaderData() as UserProfile;

  return (
    <div>
      <h1>{profile.name}</h1>
      <p>邮箱: {profile.email}</p>
    </div>
  );
}
```

> **重要提示**：为了保证类型安全且避免不必要的副作用，当在组件中引入 `.data.ts` 的类型时，**必须**使用 `import type` 语法。

## `loader` 函数详解

`loader` 函数接收一个包含 `params` 和 `request` 的对象作为参数，并期望返回一个可序列化的数据对象或一个标准的 `Response` 实例。

### `params`：动态路由参数

当路由是动态的时（例如 `routes/user/[id]/page.tsx`），URL 中的动态片段会通过 `params` 对象传递给 `loader` 函数。

```ts
// src/routes/user/[id]/page.data.ts
import { LoaderFunctionArgs } from '@edenx/runtime/router';

export const loader = async ({ params }: LoaderFunctionArgs) => {
  const { id } = params; // 访问 /user/123 时, id 的值为 '123'
  const res = await fetch(`/api/users/${id}`);
  return res.json();
};
```

### `request`：请求信息

`request` 参数是一个标准的 Fetch API `Request` 实例。你可以通过它获取到 URL、查询参数、请求头等信息。

```ts
// src/routes/user/list/page.data.ts
import { LoaderFunctionArgs } from '@edenx/runtime/router';

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const url = new URL(request.url);
  const page = url.searchParams.get('page') || '1';
  const pageSize = url.searchParams.get('pageSize') || '10';

  const res = await fetch(`/api/users?page=${page}&pageSize=${pageSize}`);
  return res.json();
};
```

### 返回值

`loader` 函数的返回值必须是以下两种类型之一：

1.  **可序列化的数据**：一个 JavaScript 对象、数组或原始类型。框架会将其序列化为 JSON 进行传输。
2.  **`Response` 实例**：一个标准的 `Response` 对象。这允许你完全自定义响应的状态码、头部和内容类型。

```ts
// 返回自定义 Response
export const loader = async () => {
  const data = { message: 'Success' };
  return new Response(JSON.stringify(data), {
    status: 201,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'X-Custom-Header': 'MyValue',
    },
  });
};
```

## 在不同渲染环境下的行为

`loader` 函数的行为在客户端渲染（CSR）和服务端渲染（SSR）模式下有所不同，但 EdenX 的设计旨在最大化地实现代码同构。

-   **CSR 应用**：所有的 `loader` 函数都在**浏览器端**执行。它们可以直接使用 `window`、`document` 等浏览器环境的 API。

-   **SSR 应用**：所有的 `loader` 函数都**只在服务端**执行。
    -   **首屏加载时**：Node.js 服务直接调用 `loader` 函数，将获取的数据注入到预渲染的 HTML 中。
    -   **客户端导航时**：浏览器会向 SSR 服务器发起一个内部的 `fetch` 请求，触发对应路由的 `loader` 在服务端执行，然后将返回的数据用于客户端的页面更新。

**SSR 模式下 `loader` 只在服务端执行的优势**：

-   **安全性**：可以在 `loader` 中安全地使用数据库连接、私有 API 密钥等敏感信息，这些代码永远不会暴露到客户端。
-   **减少客户端体积**：所有数据获取逻辑及其依赖（例如庞大的 SDK）都只存在于服务端，不会被打包进客户端的 JavaScript 文件中。
-   **性能**：利用服务器的内网环境和更高计算能力，通常能更快地获取数据。

一个显著的性能优势是，当客户端导航到一个嵌套路由时（例如从 `/user/profile` 到 `/user/settings`），EdenX 能够**并行地**请求所有新涉及层级的 `loader` 函数，有效避免了数据请求的瀑布流问题。

## 错误处理

健壮的错误处理是数据管理的重要组成部分。在 `loader` 函数中，你可以通过 `throw` 一个错误或一个 `Response` 对象来触发错误边界。

### 基本用法

当 `loader` 抛出异常时，EdenX 会停止渲染当前组件，并向上寻找最近的 `error.tsx`（错误边界组件）进行渲染。

```ts
// src/routes/product/[id]/page.data.ts
export const loader = async ({ params }) => {
  const res = await fetch(`/api/products/${params.id}`);
  if (!res.ok) {
    // 抛出一个 Response 对象，可以被错误边界捕获
    throw new Response('Product not found', { status: 404 });
  }
  return res.json();
};
```

```tsx
// src/routes/product/error.tsx
import { useRouteError, isRouteErrorResponse } from '@edenx/runtime/router';

export default function ProductError() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
      </div>
    );
  }

  return <h1>An unexpected error occurred.</h1>;
}
```

### 修改 HTTP 状态码

在 SSR 应用中，`throw new Response(...)` 的方式尤其有用，因为它不仅能渲染错误 UI，还能同时**设置整个页面的 HTTP 状态码**。这对 SEO 非常重要，例如可以正确地向搜索引擎返回 `404 Not Found` 或 `500 Internal Server Error`。

## 高级用法

### 获取上层组件的数据

子组件有时需要访问父级布局 `loader` 返回的数据，例如，在一个用户中心的页面里，所有子页面都需要展示当前用户的基本信息。这时可以使用 `useRouteLoaderData` Hook。

**文件结构**:

```
.
└── src/
    └── routes/
        └── user/
            ├── layout.data.ts  # 提供用户基本信息
            ├── layout.tsx
            └── profile/
                └── page.tsx
```

```ts
// src/routes/user/layout.data.ts
export const loader = async () => {
  // 假设这个函数获取当前登录用户的信息
  return { id: '123', name: '张三', email: 'zhangsan@example.com' };
};
```

在子组件中通过 `routeId` 获取数据：

```tsx
// src/routes/user/profile/page.tsx
import { useRouteLoaderData } from '@edenx/runtime/router';

export default function ProfilePage() {
  // `routeId` 是 .data.ts 文件相对于 `src/routes` 的路径
  const userData = useRouteLoaderData('user/layout');

  return (
    <div>
      <h2>个人资料</h2>
      {userData && <p>当前用户: {userData.name}</p>}
      {/* ... 其他个人资料内容 */}
    </div>
  );
}
```

### 数据缓存与重新验证

为了提升性能，EdenX 会自动缓存 `loader` 的数据。当你在路由间导航时，如果某个层级的 `loader` 已经执行过且其 URL 部分未发生变化，框架将不会重新请求数据。

**重新验证（Revalidation）** 会在以下情况自动触发：

1.  当一个**数据写入**操作（Action）成功后，当前页面的所有 `loader` 会自动重新执行。
2.  当 URL 的**查询参数**发生变化时。
3.  用户点击一个指向**当前页面**的链接时。

开发者也可以通过在路由组件中导出 `shouldRevalidate` 函数来手动控制重新验证的行为，实现更精细的缓存策略。

## 常见问题与最佳实践 (FAQ)

**Q1: `loader` 函数和 BFF (Backend for Frontend) 函数有什么区别和联系？**

**A1**:
*   **职责不同**: `loader` 的核心职责是**为页面组件准备数据**，它与路由和渲染生命周期紧密耦合。BFF 函数则是通用的服务端接口，可以被任何客户端（包括 `loader`）调用，用于处理更复杂的业务逻辑、聚合多个下游服务等。
*   **执行环境**: 在 SSR 模式下，`loader` 和 BFF 函数都运行在服务端。你可以认为 `loader` 是一个特殊的、与路由绑定的服务端接口。
*   **推荐用法**:
    *   对于 **GET** 请求，如果只是简单地从下游服务获取数据并直接用于页面渲染，**推荐直接在 `loader` 中实现**，这样可以减少一次网络转发（浏览器 -> BFF -> 下游服务 vs. 浏览器 -> `loader` -> 下游服务）。
    *   对于 **POST/PUT/DELETE** 等写入操作，或者需要被多个不同页面、甚至其他应用复用的复杂查询逻辑，应该封装在 BFF 函数中，然后在需要时从 `loader` 或客户端组件中调用。

**Q2: `loader` 函数中可以返回函数、Date 对象或 Map 实例吗？**

**A2**: **不可以**。`loader` 的返回值必须是**可序列化**的。因为在 SSR 环境下，服务端 `loader` 的返回值需要通过网络以 JSON 格式传输给客户端进行“注水”（hydration）。函数、复杂的类实例（如 Date、Map）等都无法被正确地序列化和反序列化。你应该返回纯粹的 JavaScript 对象、数组和原始值。如果需要传输日期，可以将其格式化为 ISO 字符串（`date.toISOString()`），然后在客户端再转换回来。

**Q3: 我可以直接在我的组件里调用 `loader` 函数吗？**

**A3**: **绝对不行**。`loader` 函数是由 EdenX 框架在路由生命周期的特定阶段自动调度的。你永远不应该手动导入并直接调用它。如果你需要刷新数据，应该依赖框架提供的重新验证机制，或者在极少数情况下通过 `useRevalidator` Hook 手动触发。

**Q4: 如何在 `loader` 中处理加载状态（Loading UI）？**

**A4**: 当数据加载较慢时，提供一个加载指示器对用户体验至关重要。
*   **对于路由切换**：可以在与 `layout.tsx` 同级的目录下创建一个 `loading.tsx` 文件。当子路由的 `loader` 正在执行时，这个 `loading.tsx` 组件会被自动渲染。
*   **对于局部数据**：可以使用 `defer` 和 `<Await>` API 结合 `React.Suspense` 来实现流式加载和更细粒度的加载状态控制。这允许页面主体内容先显示，而将慢数据部分用加载指示器占位。这是提升感知性能的高级技巧。
