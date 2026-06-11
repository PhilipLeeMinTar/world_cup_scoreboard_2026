# EdenX 路由系统深度解析

EdenX 框架的路由系统构建于业界知名的 React Router 之上，并在此基础上提供了强大的**约定式路由**能力。这意味着开发者无需手动维护一份庞大的路由配置文件，而是通过合理地组织文件和目录结构，让框架自动生成和管理应用的路由映射。这种方式极大地提升了开发效率，并使得项目结构更加直观和可维护。

本文档将全面介绍 EdenX 的约定式路由机制，包括其核心概念、文件约定、各类路由模式及其在真实场景中的应用。

## 核心概念：嵌套路由

EdenX 约定式路由的核心是**嵌套路由（Nested Routes）**。这是一种将 URL 片段与组件的层级结构深度耦合的设计模式。在这种模式下，URL 的不同部分不仅决定了页面上需要渲染哪些组件，还与其数据依赖紧密相关。

一个典型的嵌套路由场景如下：

```
/user/johnny/profile                  /user/johnny/posts
+------------------+                  +-----------------!
| User             |                  | User            |
| +--------------+ |                  | +-------------+ |
| | Profile      | |  ------------>   | | Posts       | |
| |              | |                  | |             | |
| +--------------+ |                  | +-------------+ |
+------------------+                  +-----------------+
```

在这里，`/user/johnny` 可能对应一个包含用户基本信息和导航的父级布局组件（Layout），而 `profile` 和 `posts` 则作为其子组件，在父布局的指定区域内渲染，分别展示用户的个人资料和文章列表。URL 的变化仅引起子组件的切换，而父布局保持不变，从而实现了高效的页面更新和状态保持。

## 路由文件约定

在 EdenX 项目中，所有约定式路由的相关文件都应放置在 `src/routes` 目录下。框架通过识别该目录下的特定文件名来构建路由树。

### `page.tsx`：页面组件

`page.tsx` 文件定义了路由的**内容组件**，它是一个路由路径的终点。当一个目录下存在 `page.tsx` 文件时，该目录对应的 URL 路径就成为一个可访问的页面。

例如，以下目录结构：

```
.
└── src/
    └── routes/
        ├── page.tsx          # 对应 /
        └── user/
            └── page.tsx      # 对应 /user
```

框架会自动生成两条路由：`/` 和 `/user`。

`page.tsx` 文件内容就是一个标准的 React 组件：

```tsx
// src/routes/page.tsx
export default function HomePage() {
  return <div>这里是首页</div>;
}
```

### `layout.tsx`：布局组件

`layout.tsx` 文件定义了其所在目录及其所有子路由的**布局组件**。它像一个“相框”，包裹着子路由的页面内容。通过在 `layout.tsx` 中使用 `<Outlet />` 组件（由 React Router 提供），可以指定子组件的渲染位置。

```tsx
// src/routes/layout.tsx
import { Outlet } from '@edenx/runtime/router';

export default function RootLayout() {
  return (
    <div className="app-container">
      <header>应用头部</header>
      <main>
        <Outlet /> {/* 子路由内容将在这里渲染 */}
      </main>
      <footer>应用底部</footer>
    </div>
  );
}
```

**嵌套关系示例**：

假设有如下文件结构：

```
.
└── src/
    └── routes/
        ├── layout.tsx
        ├── page.tsx
        └── user/
            ├── layout.tsx
            └── page.tsx
```

- 访问 `/` 时，UI 结构为：
  ```
  <RootLayout>
    <HomePage />
  </RootLayout>
  ```
- 访问 `/user` 时，UI 结构为：
  ```
  <RootLayout>
    <UserLayout>
      <UserPage />
    </UserLayout>
  </RootLayout>
  ```

> **提示**：路由组件文件可以使用 `.ts`、`.js`、`.jsx` 或 `.tsx` 等扩展名。

## 路由模式详解

### 动态路由

通过在目录或文件名中使用方括号 `[]`，可以创建**动态路由**，用于匹配可变的 URL 片段，例如用户 ID、文章 slug 等。

**文件结构**：

```
.
└── src/
    └── routes/
        └── blog/
            └── [slug]/
                └── page.tsx
```

这会生成一个路由 `/blog/:slug`，可以匹配 `/blog/hello-world`、`/blog/my-first-post` 等路径。

在组件内部，可以通过 `@edenx/runtime/router` 提供的 `useParams` Hook 来获取动态参数的值：

```tsx
// src/routes/blog/[slug]/page.tsx
import { useParams } from '@edenx/runtime/router';

export default function BlogPost() {
  const { slug } = useParams(); // 获取名为 'slug' 的参数

  return <div>正在阅读文章：{slug}</div>;
}
```

### 通配路由与 404 页面

**通配路由**用于捕获所有未被其他路由规则匹配的路径，通常用于实现自定义的 404 “未找到”页面。通过创建一个名为 `$.tsx` 的文件来实现。

**重要**：`$.tsx` 必须放置在包含 `layout.tsx` 的目录中才能生效。

**文件结构**：

```
.
└── src/
    └── routes/
        ├── layout.tsx     # 根布局
        ├── page.tsx       # 首页
        └── $.tsx          # 全局 404 页面
```

`$.tsx` 组件内容：

```tsx
// src/routes/$.tsx
import { useRouteError } from '@edenx/runtime/router';

export default function NotFoundPage() {
  const error = useRouteError();
  console.error(error); // 可以在服务端或客户端日志中记录错误

  return (
    <div>
      <h1>404 - 页面未找到</h1>
      <p>抱歉，您访问的页面不存在。</p>
    </div>
  );
}
```

当用户访问如 `/about`、`/products/abc` 等任何未定义的路径时，`$.tsx` 组件就会被渲染在根布局 `<RootLayout>` 的 `<Outlet />` 中。

### 无路径布局（路由分组）

当需要为一组路由应用相同的布局，但又不希望在 URL 中增加一个额外的层级时，可以使用**无路径布局**。只需将目录名以双下划线 `__` 开头即可。

**场景**：假设你需要为“登录”和“注册”页面应用一个统一的认证布局（例如，居中卡片样式），但希望它们的 URL 是 `/login` 和 `/signup`，而不是 `/auth/login`。

**文件结构**：

```
.
└── src/
    └── routes/
        └── __auth/            # 无路径布局目录
            ├── layout.tsx     # 认证专用布局
            ├── login/
            │   └── page.tsx   # 对应 /login
            └── signup/
                └── page.tsx   # 对应 /signup
```

`__auth/layout.tsx` 中的布局会应用于 `login` 和 `signup` 页面，但 `__auth` 这个名字不会出现在最终的 URL 中。

### 无布局路径（点状路由）

对于层级很深但不需要中间布局的路由，为了避免创建过多嵌套目录，EdenX 支持使用点 `.` 来分隔 URL 片段，这被称为**无布局路径**或**点状路由**。

**场景**：你需要一个路径为 `/dashboard/settings/user/profile/edit` 的页面，但中间的 `settings`、`user`、`profile` 都不需要独立的布局组件。

**文件结构**：

```
.
└── src/
    └── routes/
        └── dashboard.settings.user.profile.edit/  # 使用点分隔
            └── page.tsx
```

这会直接生成 `/dashboard/settings/user/profile/edit` 路由，且其内容直接渲染在最近的父级布局（例如根 `layout.tsx`）中，避免了创建 5 层嵌套目录的繁琐。

## 高级功能

### 路由重定向

在某些场景下，需要根据特定条件（如用户登录状态）将用户从一个路由重定向到另一个。

#### 在 `loader` 函数中重定向

推荐的方式是在路由的 `loader` 函数（通常在 `page.data.ts` 文件中定义）中进行重定向。这在服务端渲染（SSR）和客户端渲染（CSR）中都能良好工作。

```ts
// src/routes/dashboard/page.data.ts
import { redirect } from '@edenx/runtime/router';
import { checkAuth } from '../utils/auth';

export const loader = async () => {
  const isLoggedIn = await checkAuth();
  if (!isLoggedIn) {
    // 如果用户未登录，重定向到登录页
    return redirect('/login');
  }
  return { user: { name: 'Admin' } };
};
```

#### 在组件中重定向

也可以在组件的副作用（`useEffect`）中使用 `useNavigate` Hook 进行客户端重定向。

```tsx
// src/routes/dashboard/page.tsx
import { useEffect } from 'react';
import { useNavigate } from '@edenx/runtime/router';
import { useAuth } from '../hooks/useAuth';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { isLoading, isLoggedIn } = useAuth();

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      navigate('/login');
    }
  }, [isLoading, isLoggedIn, navigate]);

  if (isLoading) {
    return <div>加载中...</div>;
  }

  return <div>欢迎来到仪表盘</div>;
}
```

### 错误处理

EdenX 允许在路由的任何层级通过创建 `error.tsx` 文件来定义**错误边界（Error Boundary）**。当该层级及其子路由的组件在渲染过程中抛出错误时，`error.tsx` 定义的组件将被渲染，从而将错误隔离，避免整个应用崩溃。

在 `error.tsx` 中，可以使用 `useRouteError` Hook 来获取错误的详细信息。

```tsx
// src/routes/user/error.tsx
import { useRouteError, isRouteErrorResponse } from '@edenx/runtime/router';

export default function UserError() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
        <p>{error.data}</p>
      </div>
    );
  }

  return <div>处理用户区模块时发生未知错误。</div>;
}
```

## 常见问题与最佳实践 (FAQ)

**Q1: 为什么应该使用 `@edenx/runtime/router` 而不是直接从 `react-router-dom` 导入 API？**

**A1**: EdenX 内部已经集成了特定版本的 `react-router-dom`。为了确保整个应用中只存在一个 React Router 实例，避免版本冲突和不可预知的行为（例如上下文丢失），**必须**总是从 `@edenx/runtime/router` 中导入如 `Link`, `Outlet`, `useParams`, `useNavigate` 等所有路由相关的 API。这保证了你使用的 API 与框架内部的路由系统是完全兼容和一致的。

**Q2: 如何在 `Link` 组件中添加 `active` 状态的样式？**

**A2**: 你应该使用 `NavLink` 组件，而不是 `Link`。`NavLink` 是一个特殊的 `Link`，它可以感知自己是否处于“激活”状态。你可以通过传递一个函数给 `className` 或 `style` prop 来根据激活状态动态应用样式。

```tsx
import { NavLink } from '@edenx/runtime/router';

function AppNav() {
  return (
    <nav>
      <NavLink
        to="/"
        className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
      >
        首页
      </NavLink>
      <NavLink
        to="/about"
        className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
      >
        关于
      </NavLink>
    </nav>
  );
}
```

**Q3: 我想在布局组件中根据当前路由动态显示面包屑导航，该如何实现？**

**A3**: 这是一个典型的路由元信息应用场景。你可以在每个 `page.tsx` 或 `layout.tsx` 的同级目录下创建一个 `page.config.ts` 或 `layout.config.ts` 文件，并在其中导出 `handle` 对象来附加元数据。

*   `src/routes/user/page.config.ts`:
    ```ts
    export const handle = {
      breadcrumb: () => '用户列表'
    };
    ```
*   `src/routes/user/[id]/page.config.ts`:
    ```ts
    export const handle = {
      breadcrumb: (params) => `用户详情 (${params.id})`
    };
    ```

然后在根布局或上层布局中，使用 `useMatches` Hook 来读取这些 `handle` 并生成面包屑。

```tsx
// src/routes/layout.tsx
import { useMatches } from '@edenx/runtime/router';
import { Link } from '@edenx/runtime/router';

function Breadcrumbs() {
  const matches = useMatches();
  const crumbs = matches
    // 首先过滤掉没有 breadcrumb handle 的路由
    .filter((match) => Boolean(match.handle?.breadcrumb))
    // 然后渲染出 breadcrumb
    .map((match) => (
      <Link key={match.id} to={match.pathname}>
        {match.handle.breadcrumb(match.params)}
      </Link>
    ));

  return <nav>{crumbs}</nav>;
}
```

**Q4: 如何实现路由级别的代码分割？**

**A4**: 当你使用 EdenX 的约定式路由时，**路由级别的代码分割是自动完成的**。框架会智能地将每个 `page.tsx` 及其关联的组件打包成独立的 JavaScript chunk。只有当用户导航到特定路由时，相应的 chunk 才会被按需加载。你无需进行任何额外配置。对于组件级别的按需加载，可以使用 `React.lazy` 或 `@loadable/component`。
