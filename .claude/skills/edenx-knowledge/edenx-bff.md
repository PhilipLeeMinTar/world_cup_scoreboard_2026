# EdenX BFF 一体化开发实践

EdenX 框架提供了一套强大的 **BFF（Backend for Frontend，服务于前端的后端）** 解决方案，其核心特性是**一体化调用**。这使得前端开发者可以在同一个项目中无缝编写和调用服务端逻辑，极大地简化了前后端协作，并天然地保证了类型安全。

本文档将详细介绍如何在 EdenX项目中启用和使用 BFF 功能，包括 BFF 函数的定义、路由约定、参数传递规则，以及与公司内部基建（如 Gulux）的集成方案。

## BFF 的价值

传统的开发模式中，前端需要通过 HTTP 客户端（如 `fetch` 或 `axios`）调用后端 API。这带来了几个痛点：
- **胶水代码**：需要手动编写大量请求封装、URL 管理、参数序列化和错误处理的代码。
- **类型安全缺失**：前后端接口的类型定义通常是分离的，容易因一方变更而导致另一方出错，且难以在编译期发现。
- **数据聚合困难**：当前端页面需要来自多个不同微服务的数据时，不得不在客户端发起多次请求，增加了网络开销和页面加载复杂度。

EdenX 的 BFF 方案旨在解决这些问题。它允许开发者在项目 `api/` 目录下编写 TypeScript 函数作为服务端接口，然后在前端 `src/` 目录中像调用本地模块一样直接调用这些函数，框架会自动将其转换为标准的 HTTP 请求。
## 启用 BFF

在 EdenX 项目中启用 BFF 功能，我们强烈推荐使用内部的 `Aiden` 插件，它可以一键完成所有配置。如果希望手动配置，也支持标准（集成 Gulux）和轻量（基于 Hono）两种方案。


### 方式一：手动配置（标准 BFF，集成 Gulux）

对于需要与公司内部 RPC、服务治理、监控等基建深度整合的复杂应用，推荐使用集成了 `Gulux` 框架的标准 BFF 方案。

1.  **安装依赖**：
    确保 `@edenx/plugin-bff` 和 `@edenx/plugin-gulux` 的版本与项目中的 `@edenx/app-tools` 保持一致。
    ```bash
    # 查看当前版本
    pnpm list @edenx/app-tools

    # 安装相同版本的插件和 gulux
    pnpm add @edenx/plugin-bff@<版本号> @edenx/plugin-gulux@<版本号> @gulux/gulux@^4.0.2
    ```

2.  **修改 `edenx.config.ts`**：
    注册 BFF 和 Gulux 插件。
    ```ts
    import { defineConfig, appTools } from '@edenx/app-tools';
    import { bffPlugin } from '@edenx/plugin-bff';
    import { guluxPlugin } from '@edenx/plugin-gulux';

    export default defineConfig({
      plugins: [appTools(), bffPlugin(), guluxPlugin()],
    });
    ```

3.  **修改 `tsconfig.json`**：
    添加 BFF 相关的路径别名和编译选项。
    ```json
    {
      "compilerOptions": {
        // ... 其他配置
        "moduleResolution": "NodeNext",
        "module": "NodeNext",
        "target": "ES2017",
        "emitDecoratorMetadata": true,
        "experimentalDecorators": true,
        "strictPropertyInitialization": false,
        "paths": {
          "@api/*": ["./api/lambda/*"],
          // ... 其他 paths
        }
      },
      "include": [
        "src",
        "api" // 确保 api 目录被 ts 编译器包含
        // ... 其他 include
      ]
    }
    ```

4.  **创建 BFF 源码目录和文件**：
    建议的目录结构如下，它将接口定义 (`lambda`)、业务逻辑服务 (`service`) 和配置 (`config`) 分离开。
    ```
    api/
    ├── lambda/     # BFF 函数（控制器层）
    │   ├── index.ts
    │   └── user.ts
    ├── service/    # 业务逻辑层
    │   └── user.ts
    └── config/     # Gulux 配置
        ├── config.default.ts
        ├── plugin.default.ts
        └── ...
    ```

## 编写第一个 BFF 函数

BFF 函数是遵循特定规则的、可被一体化调用的服务端函数。

1.  **创建文件**：
    在 `api/lambda/` 目录下创建一个新文件，例如 `hello.ts`。

2.  **编写函数**：
    导出一个与 HTTP Method 同名的异步函数。`export default` 默认对应 `GET` 请求。

    ```ts
    // api/lambda/hello.ts

    // 处理 GET /api/hello
    export default async () => {
      return {
        message: 'Hello from EdenX BFF!',
        timestamp: new Date().toISOString(),
      };
    };

    // 处理 POST /api/hello
    export const post = async () => {
      return { status: 'success' };
    };
    ```

3.  **在前端调用**：
    在任何 `src/` 目录下的组件中，直接通过 `@api` 别名导入并调用该函数。

    ```tsx
    // src/components/Greeting.tsx
    import { useState, useEffect } from 'react';
    import helloBFF from '@api/hello'; // 导入默认导出的 GET 函数

    export function Greeting() {
      const [greeting, setGreeting] = useState('');

      useEffect(() => {
        // 直接调用，框架会自动转换为 fetch 请求
        helloBFF().then(data => {
          setGreeting(data.message);
        });
      }, []);

      return <div>{greeting}</div>;
    }
    ```

当组件渲染时，你会在浏览器的网络面板中看到一个发往 `/api/hello` 的 `GET` 请求，而代码层面则完全是类型安全的函数调用。

## BFF 路由约定

EdenX BFF 的路由系统同样基于文件约定，`api/lambda/` 目录下的文件结构直接映射为 API 路由。所有路由默认带有一个前缀，通常是 `/api`，可以通过 `bff.prefix` 配置项修改。

-   **文件名映射**：
    `api/lambda/user/list.ts` -> `/api/user/list`

-   **`index.ts` 文件**：
    `api/lambda/user/index.ts` -> `/api/user`

-   **动态路由**：
    使用方括号 `[]` 来定义动态路由片段。
    `api/lambda/user/[id].ts` -> `/api/user/:id`

-   **忽略规则**：
    以下划线 `_` 开头的文件或目录、测试文件（`.test.ts`）、类型定义文件（`.d.ts`）等会被自动忽略，不会被解析为 BFF 路由。

## 函数签名与参数传递

BFF 函数的参数设计遵循 RESTful API 的标准，分为**路径参数**和**请求选项**。

### 路径参数 (Dynamic Path)

动态路由的片段会按顺序作为函数的前几个参数传入。

```ts
// api/lambda/repo/[owner]/[name].ts
export default async (owner: string, name: string) => {
  // 当请求 /api/repo/bytedance/edenx 时
  // owner => 'bytedance'
  // name => 'edenx'
  return { owner, name };
};
```

**前端调用**：

```ts
import getRepoInfo from '@api/repo/[owner]/[name]';

getRepoInfo('bytedance', 'edenx').then(info => console.log(info));
```

### 请求选项 (RequestOption)

路径参数之后是一个可选的 `RequestOption` 对象，用于接收 `query` 参数和请求体 `data`。

```ts
// api/lambda/user.ts
import type { RequestOption } from '@edenx/server-runtime';

interface UserQuery {
  page?: number;
  pageSize?: number;
}

interface UserData {
  name: string;
  email: string;
}

// 处理 POST /api/user?page=1
export const post = async ({ query, data }: RequestOption<UserQuery, UserData>) => {
  console.log('Query:', query); // { page: 1 }
  console.log('Data:', data);   // { name: '...', email: '...' }
  // ... 创建用户的逻辑
  return { id: 'new-user-id', ...data };
};
```

**前端调用**：

```ts
import { post as createUser } from '@api/user';

createUser({
  query: { page: 1 },
  data: { name: 'New User', email: 'test@example.com' },
}).then(newUser => {
  console.log('Created user:', newUser);
});
```

对于 `GET` 请求，由于没有请求体，`RequestOption` 中只有 `query` 字段。

## 常见问题与最佳实践 (FAQ)

**Q1: 如何在 BFF 函数中获取原始的 HTTP 请求对象（如 `Request` 或 `Response`）？**

**A1**: 当使用**标准 BFF (Gulux)** 方案时，可以通过 `@edenx/plugin-gulux/runtime` 提供的 Hooks 来访问上下文。
```ts
import { useReq, useRes } from '@edenx/plugin-gulux/runtime';

export const post = async () => {
  const request = useReq(); // 获取请求对象
  const response = useRes(); // 获取响应对象

  const userAgent = request.header('user-agent');
  response.set('X-Powered-By', 'EdenX');

  // ... 业务逻辑
  return { userAgent };
};
```
对于**轻量 BFF (Hono)**，上下文会作为参数直接注入到处理器函数中，具体用法请参考 Hono 的文档。

**Q2: 如何在 BFF 函数中处理文件上传？**

**A2**: 文件上传通常通过 `multipart/form-data` 格式的请求实现。在使用 Gulux 时，你需要借助 `@midwayjs/upload` 等中间件来处理。在 `config/plugin.default.ts` 中启用它，然后在 BFF 函数中通过 `@File()` 装饰器注入文件流。详细配置请参考 [EdenX 文件上传文档](/guides/advanced-features/bff/upload.html)。

**Q3: 前端和 BFF 之间如何共享代码，比如类型定义？**

**A3**: EdenX 提供了 `shared` 目录的约定。在项目根目录下创建一个 `shared` 目录，放置在这里的任何代码（例如 `shared/types/user.ts`）可以被 `src/` 和 `api/` 两个目录安全地引用。这是实现前后端类型共享和代码复用的推荐方式。

```
my-project/
├── api/
├── src/
└── shared/
    └── types/
        └── index.ts  # 可被前后端同时 import
```

**Q4: BFF 函数的日志在哪里查看？如何进行调试？**

**A4**:
*   **本地开发**：当你运行 `pnpm run dev` 时，BFF 函数的 `console.log` 输出会直接显示在启动服务的**终端**中。
*   **调试**：你可以使用标准的 Node.js 调试方法。在 `package.json` 的 `dev` 命令中添加 `--inspect-brk` 标志，然后使用 VS Code 或 Chrome DevTools 连接到 Node.js 进程进行断点调试。
*   **线上环境**：BFF 函数的日志会根据你部署环境的配置（例如 Gulux 的日志配置）被收集到相应的日志服务中，如 Argos。你需要在部署配置文件中正确设置日志级别和输出目标。
