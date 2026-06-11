# GuluX 插件体系指南

## 概述

Plugin 是 GuluX 架构的"一等公民"，用于扩展框架能力。插件系统解决两个主要需求：

1. **可复用的框架扩展**：如 redis、tcc 等官方插件
2. **业务逻辑抽象**：将大型项目拆分为逻辑组件

## 插件分类

GuluX 区分两种组织形式：

- **NPM 包插件**：官方插件如 `@gulux/plugin-xx`
- **内联插件**：仅在项目本地使用的自定义插件

两者功能相同，仅配置方式略有不同。

## 使用插件

### 内置框架插件

大多数 `@gulux` 作用域下的插件已集成到 `@gulux/gulux`，可直接激活：

```typescript
// src/config/plugin.default.ts
export default {
  'application-http': { enable: true },
  redis: { enable: true },
  tcc: { enable: true },
  'byted-logger': { enable: true },
  'byted-metrics': { enable: true },
};
```

### 第三方或自定义插件

使用 `package` 或 `path` 属性配置外部包或本地目录：

```typescript
// 使用 npm 包
export default {
  'my-plugin': {
    enable: true,
    package: '@my-scope/my-gulux-plugin',
  },
};

// 使用本地路径
export default {
  'my-local-plugin': {
    enable: true,
    path: './plugins/my-local-plugin',
  },
};
```

## 可用插件列表

### 服务调用类

| 插件          | 说明                    |
| ------------- | ----------------------- |
| `http-client` | HTTP 请求，支持拦截器   |
| `rpc-client`  | RPC 服务调用，支持 mock |

### 存储组件类

| 插件            | 说明                   |
| --------------- | ---------------------- |
| `sequelize`     | RDS/MySQL 关系型数据库 |
| `typegoose`     | MongoDB 对象建模       |
| `redis`         | Redis 缓存，支持集群   |
| `tos`           | 对象存储服务           |
| `elasticsearch` | 搜索和分析引擎         |
| `bytegraph`     | 图数据库               |
| `minio`         | 自托管对象存储         |

### 配置与加密类

| 插件                | 说明               |
| ------------------- | ------------------ |
| `tcc`               | 动态配置管理       |
| `kms-v1` / `kms-v2` | 密钥管理和数据加密 |

### 消息队列类

| 插件                | 说明              |
| ------------------- | ----------------- |
| `kafka-producer`    | Kafka 事件发布    |
| `rocketmq-producer` | RocketMQ 消息发送 |
| `eventbus-producer` | EventBus 事件驱动 |

### 可观测性类

| 插件                                 | 说明       |
| ------------------------------------ | ---------- |
| `byted-logger`                       | 应用日志   |
| `byted-metrics` / `byted-metrics-v2` | 性能指标   |
| `byted-trace`                        | 分布式追踪 |

### 认证登录类

| 插件         | 说明          |
| ------------ | ------------- |
| `cas`        | CAS 认证      |
| `oauth2`     | OAuth2 认证   |
| `passport`   | Passport 认证 |
| `tiktok-sso` | TikTok SSO    |

### HTTP 扩展类

| 插件         | 说明             |
| ------------ | ---------------- |
| `session`    | 会话管理         |
| `security`   | 安全防护         |
| `graphql`    | GraphQL 支持     |
| `views`      | 模板渲染         |
| `static`     | 静态文件服务     |
| `fast-json`  | 快速 JSON 序列化 |
| `http-proxy` | HTTP 代理        |
| `i18n`       | 国际化           |

## 创建自定义插件

### 目录结构

```
my-plugin/
├── src/
│   ├── index.ts          # 插件入口
│   └── ...
├── meta.json             # 插件元数据
└── package.json
```

### meta.json 配置

插件根目录必须包含 `meta.json` 文件：

```json
{
  "name": "my-plugin"
}
```

### 声明插件依赖

```json
{
  "name": "my-plugin",
  "dependencies": [
    { "name": "byted-logger" },
    { "name": "nemo", "optional": true }
  ]
}
```

### 插件入口示例

```typescript
// src/index.ts
import { LifecycleHookUnit, LifecycleHook, Inject, Config } from '@gulux/gulux';

@LifecycleHookUnit()
export default class MyPlugin {
  @Config('myPlugin')
  config: MyPluginConfig;

  @Inject()
  logger: any;

  @LifecycleHook()
  async didLoad() {
    // 插件初始化逻辑
    this.logger?.info?.('MyPlugin loaded with config:', this.config);
  }

  @LifecycleHook()
  async beforeClose() {
    // 插件清理逻辑
    this.logger?.info?.('MyPlugin closing...');
  }
}
```

### 插件配置

```typescript
// config/config.default.ts
export default {
  myPlugin: {
    option1: 'value1',
    option2: 'value2',
  },
};
```

## 依赖管理最佳实践

- **GuluX 框架**：使用 `devDependencies` 和 `peerDependencies`，避免版本冲突
- **仅内部使用的其他插件**：添加到 `package.json` dependencies
- **插件和用户项目都需要的插件**：
  - 从自定义插件重新导出
  - 或在文档中说明用户需自行安装
