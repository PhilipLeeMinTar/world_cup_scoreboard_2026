# 中间件开发指南

## 概述

Middleware 抽象通用的请求处理逻辑，如登录验证、错误处理、请求日志等，使用洋葱模型（Onion Model）架构。
注意：仅应用自身 config 可配置 middleware，插件 config 不能写 middleware 实现。

## 编写中间件

中间件必须是实现 `use` 方法的类：

```typescript
import { Middleware, GuluXMiddleware } from '@gulux/gulux';
import { Req, HTTPRequest, Next, NextFunction } from '@gulux/gulux/application-http';

@Middleware()
export default class RequestLogMiddleware extends GuluXMiddleware {
  public async use(@Req() req: HTTPRequest, @Next() next: NextFunction) {
    const start = Date.now();
    console.log(`[Request] ${req.method} ${req.url}`);

    await next();

    const duration = Date.now() - start;
    console.log(`[Response] ${req.method} ${req.url} - ${duration}ms`);
  }
}
```

## 核心装饰器

### @Middleware()

将类注册到 IoC 容器作为中间件：

```typescript
@Middleware()
export class AuthMiddleware extends GuluXMiddleware {
  // ...
}
```

### 参数装饰器

| 装饰器         | 说明                 |
| -------------- | -------------------- |
| `@Req()`       | 注入请求对象         |
| `@Res()`       | 注入响应对象         |
| `@Next()`      | 注入下一个中间件函数 |
| `@Config(key)` | 注入配置值           |
| `@Inject()`    | 注入依赖服务         |

## 使用中间件

### 方法一：配置文件（全局）

在配置文件中声明全局中间件：

```typescript
// config/config.default.ts
import { RequestLogMiddleware } from '../middleware/RequestLogMiddleware';
import { ErrorHandlerMiddleware } from '../middleware/ErrorHandlerMiddleware';
import { AuthMiddleware } from '../middleware/AuthMiddleware';

export default {
  middleware: [RequestLogMiddleware, ErrorHandlerMiddleware, AuthMiddleware],
};
```

**注意**：插件不能在其配置文件中配置中间件。

### 方法二：生命周期钩子（全局）

在应用生命周期钩子中动态添加中间件：

```typescript
import { LifecycleHookUnit, LifecycleHook, Inject } from '@gulux/gulux';
import { GuluXApplication, ApplicationLifecycle } from '@gulux/gulux';

@LifecycleHookUnit()
export default class AppLifecycle implements ApplicationLifecycle {
  @Inject()
  app: GuluXApplication;

  @LifecycleHook()
  async willReady() {
    this.app.use(MyDynamicMiddleware);
  }
}
```

### 方法三：Controller 装饰器（局部）

在 Controller 或方法级别应用中间件：

```typescript
import { Controller, Get } from '@gulux/gulux/application-http';
import { AuthMiddleware } from '../middleware/AuthMiddleware';
import { RateLimitMiddleware } from '../middleware/RateLimitMiddleware';

// Controller 级别中间件
@Controller({ path: '/api/user', middlewares: [AuthMiddleware] })
export default class UserController {
  // 方法级别中间件
  @Get('/profile', { middlewares: [RateLimitMiddleware] })
  async getProfile() {
    return { profile: {} };
  }
}
```

## 执行顺序

### 优先级层次

1. **Plugin 中间件**（按插件依赖顺序）
2. **Project 中间件**（按配置声明顺序）
3. **Controller 中间件**
4. **Method 中间件**

### 插件依赖示例

如果 plugin1 依赖 plugin3，plugin2 独立：
- 执行顺序：`plugin3 → plugin1 → plugin2`

### 洋葱模型

```
Request → Middleware1 → Middleware2 → Middleware3 → Controller
                                                        ↓
Response ← Middleware1 ← Middleware2 ← Middleware3 ← Response
```

## 常见中间件示例

### 认证中间件

```typescript
@Middleware()
export class AuthMiddleware extends GuluXMiddleware {
  public async use(@Req() req: HTTPRequest, @Res() res: HTTPResponse, @Next() next: NextFunction) {
    const token = req.headers.authorization;

    if (!token) {
      res.status = 401;
      res.body = { error: 'Unauthorized' };
      return;
    }

    try {
      const user = await this.verifyToken(token);
      req.user = user;
      await next();
    } catch (error) {
      res.status = 401;
      res.body = { error: 'Invalid token' };
    }
  }

  private async verifyToken(token: string) {
    // 验证逻辑
  }
}
```

### 错误处理中间件

```typescript
@Middleware()
export class ErrorHandlerMiddleware extends GuluXMiddleware {
  public async use(@Req() req: HTTPRequest, @Res() res: HTTPResponse, @Next() next: NextFunction) {
    try {
      await next();
    } catch (error) {
      console.error(`[Error] ${req.method} ${req.url}:`, error);
      res.status = 500;
      res.body = {
        error: 'Internal Server Error',
        message: error.message,
      };
    }
  }
}
```

### 请求格式化中间件

```typescript
interface AppConfig {
  requestIdHeader: string;
}

@Middleware()
export class RequestFormatMiddleware extends GuluXMiddleware {
  @Config('app')
  app: AppConfig;

  public async use(@Req() req: HTTPRequest, @Next() next: NextFunction) {
    req.requestId = req.headers[this.app.requestIdHeader] || this.generateRequestId();
    await next();
  }

  private generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

## 依赖注入

中间件支持依赖注入，与 Controller 方法类似：

```typescript
@Middleware()
export class AuthMiddleware extends GuluXMiddleware {
  @Inject()
  userService: UserService;

  @Inject()
  logService: LogService;

  public async use(@Req() req: HTTPRequest, @Next() next: NextFunction) {
    const user = await this.userService.verifyToken(req.headers.authorization);
    this.logService.log(`User ${user.id} authenticated`);
    req.user = user;
    await next();
  }
}
```