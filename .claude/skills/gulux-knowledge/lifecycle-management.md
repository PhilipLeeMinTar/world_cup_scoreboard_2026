# GuluX 生命周期管理

GuluX 框架提供了一套完整的生命周期钩子机制，用于框架初始化过程中的各阶段处理。这套机制集成自 Artus 框架的生命周期设计，为开发者提供了精细化的控制能力。

## 核心生命周期钩子

### 继承自 Artus 的 6 个钩子

| 钩子             | 说明                     | 典型用途                 |
| ---------------- | ------------------------ | ------------------------ |
| `configWillLoad` | 配置加载前执行           | 检查环境变量、设置默认值 |
| `configDidLoad`  | 配置加载完成后执行       | 日志记录配置详情         |
| `didLoad`        | 插件实例初始化完成       | 服务初始化               |
| `willReady`      | 协议服务器启动前准备     | 预热缓存、检查依赖       |
| `didReady`       | 应用启动完成、服务就绪后 | 上报指标、开放健康检查等 |
| `beforeClose`    | 应用关闭时清理           | 释放资源、关闭连接       |

### GuluX 自定义的 5 个钩子（协议/服务器）

这 5 个由 GuluX 在 `run()` / `close()` 中触发，主要用于**协议插件**（如 application-http、application-rpc）创建和启停服务器。业务侧一般不需要直接挂这些钩子，但若写协议类插件或需要理解启动顺序，可以关注。

| 钩子                  | 触发时机                                                  | 典型用途                                           | 说明                                                                                                |
| --------------------- | --------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **createServer**      | `run()` 中，在 **willReady 之前**，且仅当「需要服务器」时 | 创建 HTTP/HTTPS Server 实例（不 listen）           | application-http 在此阶段 `new Koa`、`http.createServer()` 等                                       |
| **initServer**        | willReady 之后、beforeStartServer 之前                    | 协议层初始化：注册路由、挂载中间件、body parser 等 | application-http 在此阶段 `routerFactory.create()` 已执行完毕，并执行 `app.init()` 注册路由与中间件 |
| **beforeStartServer** | 服务器 **listen 之前**，最后一处可往应用加中间件的时机    | 在「最后一刻」插入全局中间件（如异常兜底）         | GuluX 在此阶段将 ExceptionFilterMiddleware 插入到索引 0                                             |
| **startServer**       | 协议服务器执行 **listen**                                 | 调用 `server.listen(port)` 等                      | 执行后端口开始监听                                                                                  |
| **stopServer**        | `close()` 时，在 **beforeClose 之后**                     | 停止服务器：`server.close()`                       | 与 beforeClose 一样按 **reverse** 顺序执行                                                          |

**与 Artus 的衔接**：在 GuluX 中，`willReady` 与 `didReady` 之间会依次执行 createServer（若需要）→ willReady → initServer → beforeStartServer → startServer，最后才 `didReady`。因此「willReady」表示「即将启动服务器」，「didReady」表示「已经 listen，对外就绪」。


## 生命周期顺序

### 启动顺序（文字版）

```
应用启动
1. configWillLoad     ← 配置即将加载
2. configDidLoad      ← 配置加载完成（GuluX 注册 @Config handler；HTTP 插件创建 Router）
3. didLoad            ← 加载完成（GuluX 采集插件列表、协议类型等）
4. createServer       ← 创建服务器实例（仅当需要服务器时，如 HTTP 插件）
5. willReady          ← 即将启动服务器（预热、健康检查等）
6. initServer         ← 协议初始化（注册路由、挂中间件）
7. beforeStartServer  ← listen 前最后一处可加中间件（GuluX 插入异常兜底）
8. startServer        ← 执行 listen
9. didReady           ← 应用就绪（GuluX 置 didReady=true，之后不可再 use 中间件）
```

### 关闭顺序（reverse）

```
close() 被调用时：
1. beforeClose  ← 先按 reverse 顺序执行所有 beforeClose 钩子
2. stopServer   ← 再按 reverse 顺序执行所有 stopServer 钩子（如 server.close()）
（若 close(true) 则最后 process.exit(0)）
应用退出
```

在每个生命周期阶段内，GuluX 会按照 Artus 的约定顺序执行钩子：先执行所有 Plugin 的对应生命周期方法，再执行 Application 自身的生命周期方法。这样可以确保插件完成配置与初始化后，应用层才能安全依赖这些能力。

## 使用方式

### 5.1 基本写法

- 使用 **@LifecycleHookUnit()** 装饰一个类，并实现 **ApplicationLifecycle** 接口（或至少实现你关心的钩子方法）。
- 使用 **@LifecycleHook()** 或 **@LifecycleHook('钩子名')** 装饰方法：
  - **方法名与钩子名一致**时，可只写 `@LifecycleHook()`，框架会按方法名识别。
  - 若方法名与钩子名不一致，或要挂到 GuluX 自定义钩子（如 createServer），必须写 `@LifecycleHook('createServer')` 等。

### 5.2 依赖注入

生命周期类支持依赖注入，可 `@Inject()` 注入 `GuluXApplication`、各种 Service 等，在钩子方法里通过 `this.app.config` 读取配置、通过注入的 Service 做预热或清理。

### 5.3 示例一：应用侧常用钩子

```typescript
import {
  LifecycleHookUnit,
  LifecycleHook,
  Inject,
  ApplicationLifecycle,
  GuluXApplication,
} from '@gulux/gulux';

@LifecycleHookUnit()
export default class AppLifecycle implements ApplicationLifecycle {
  @Inject()
  app: GuluXApplication;

  @LifecycleHook()
  async configDidLoad() {
    console.log('Configuration loaded', this.app.config?.name);
    // 例如：校验必填配置
    if (!this.app.config?.someRequiredKey) {
      throw new Error('someRequiredKey is required');
    }
  }

  @LifecycleHook()
  async willReady() {
    // 预热、健康检查（此时尚未 listen）
    await this.cacheService?.warmup?.();
    await this.healthCheck();
  }

  @LifecycleHook()
  async didReady() {
    console.log('Application is ready, server is listening');
    // 例如：上报就绪、打日志
  }

  @LifecycleHook()
  async beforeClose() {
    await this.db?.close?.();
    await this.redis?.quit?.();
  }
}
```

### 5.4 示例二：协议插件侧（如 HTTP）

协议插件需要挂 GuluX 自定义的 createServer、initServer、startServer、stopServer 等，方法名可以与钩子名不同，需显式指定钩子名：

```typescript
@LifecycleHookUnit()
export default class HTTPLifecycle implements ApplicationLifecycle {
  @Inject(GuluXApplication)
  private app: GuluXApplication;

  @Inject()
  private routerFactory: RouterFactory;

  @LifecycleHook()
  public async configWillLoad() {
    this.app.protocolFlag = PROTOCOL_FLAG.HTTP;
  }

  @LifecycleHook()
  public async configDidLoad() {
    this.routerFactory.create(); // 创建 Router，依赖 config 中的 routerPrefix 等
  }

  @LifecycleHook('createServer')
  public async createServer() {
    const protocolApp = this.app.container.get(HTTPProtocolApp);
    protocolApp.createServer(); // 创建 http.Server，未 listen
  }

  @LifecycleHook('initServer')
  public async initServer() {
    const protocolApp = this.app.container.get(HTTPProtocolApp);
    await protocolApp.init(); // 注册路由、挂中间件等
  }

  @LifecycleHook('startServer')
  public async bootstrap() {
    const protocolApp = this.app.container.get(HTTPProtocolApp);
    await protocolApp.listen(); // listen(port)
  }

  @LifecycleHook('stopServer')
  public async stopServer() {
    const protocolApp = this.app.container.get(HTTPProtocolApp);
    await protocolApp.stopServer();
  }
}
```

## 核心装饰器

### @LifecycleHookUnit()

将类注册为生命周期钩子单元：

```typescript
@LifecycleHookUnit()
export default class MyLifecycle implements ApplicationLifecycle {
  // ...
}
```

### @LifecycleHook()

标记方法为生命周期钩子方法：

```typescript
@LifecycleHook()
async configDidLoad() {
  // 钩子逻辑
}
```

## 插件集成规则

### 执行顺序

- **Plugin 钩子** 在 **Application 钩子** 之前执行（同一生命周期阶段内）
- 插件之间的执行顺序由其依赖关系决定

### 各阶段注意事项

#### configWillLoad

- 配置文件加载前执行
- 适合进行基础环境检查、设置默认环境变量等

```typescript
@LifecycleHook()
async configWillLoad() {
  console.log('Before configuration load, current env:', this.app.guluxEnv);
}
```

#### configDidLoad

- 插件合并配置与默认值
- 适合检查和记录配置

```typescript
@LifecycleHook()
async configDidLoad() {
  const config = this.app.config;
  if (!config.database) {
    throw new Error('Database configuration is required');
  }
  console.log('Database config:', config.database);
}
```

#### didLoad

- 插件初始化实例
- 应用应避免使用尚未初始化的插件实例

```typescript
@LifecycleHook()
async didLoad() {
  // 此时插件实例已初始化完成
  await this.initializeServices();
}
```

#### willReady

- 协议服务器即将启动
- 适合进行预热操作

```typescript
@LifecycleHook()
async willReady() {
  // 预热缓存
  await this.cacheService.warmup();

  // 检查外部依赖
  await this.healthCheck();
}
```

#### beforeClose

- 应用即将关闭
- 避免操作可能已销毁的插件实例

```typescript
@LifecycleHook()
async beforeClose() {
  // 关闭数据库连接
  await this.database.close();

  // 清理临时文件
  await this.cleanupTempFiles();

  // 发送关闭通知
  await this.notifyShutdown();
}
```

## 依赖注入

生命周期类支持依赖注入：

```typescript
@LifecycleHookUnit()
export default class AppLifecycle implements ApplicationLifecycle {
  @Inject()
  app: GuluXApplication;

  @Inject()
  cacheService: CacheService;

  @Inject()
  databaseService: DatabaseService;

  @LifecycleHook()
  async willReady() {
    await this.cacheService.warmup();
    await this.databaseService.runMigrations();
  }
}
```

## 实际应用示例

### 数据库迁移

```typescript
@LifecycleHookUnit()
export default class DatabaseLifecycle implements ApplicationLifecycle {
  @Inject()
  sequelize: Sequelize;

  @LifecycleHook()
  async willReady() {
    if (process.env.RUN_MIGRATIONS === 'true') {
      await this.sequelize.sync();
      console.log('Database migrations completed');
    }
  }
}
```

### 健康检查

```typescript
@LifecycleHookUnit()
export default class HealthCheckLifecycle implements ApplicationLifecycle {
  @Inject()
  redis: Redis;

  @Inject()
  database: Database;

  @LifecycleHook()
  async willReady() {
    // 检查 Redis 连接
    await this.redis.ping();
    console.log('Redis connection OK');

    // 检查数据库连接
    await this.database.query('SELECT 1');
    console.log('Database connection OK');
  }
}
```

### 优雅关闭

```typescript
@LifecycleHookUnit()
export default class GracefulShutdownLifecycle implements ApplicationLifecycle {
  @Inject()
  httpServer: HTTPServer;

  @Inject()
  jobQueue: JobQueue;

  @LifecycleHook()
  async beforeClose() {
    // 停止接受新请求
    await this.httpServer.stopAccepting();

    // 等待正在处理的请求完成
    await this.httpServer.waitForPendingRequests(30000);

    // 完成正在执行的任务
    await this.jobQueue.drain();

    console.log('Graceful shutdown completed');
  }
}
```