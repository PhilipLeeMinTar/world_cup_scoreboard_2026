---
name: gulux-knowledge
description: 当在 Node.js 服务中使用 GuluX 框架开发、使用 @gulux/gulux 或 @gulux/cli 创建项目、实现 Controller/Service/Middleware、配置 Plugin、或使用 IoC 依赖注入时使用。
user-invocable: false
---

# GuluX 知识库

GuluX是字节跳动内部的新一代Node.js服务端应用开发框架，以TypeScript为基础，采用IoC（控制反转）的开发模式，为业务开发带来一套具有静态语言开发体验的业务框架。该框架提供了丰富的插件生态来增强框架功能，方便业务开发适配公司内的基建，提高开发效率，并采用预构建机制带来超快的启动体验。

## 快速入门

GuluX框架的基础概念和入门指南，帮助开发者快速上手服务端应用开发：

- **框架概览**：了解GuluX的核心特性和架构设计
- **环境准备**：配置Node.js开发环境和相关工具
- **项目创建**：使用CLI工具初始化GuluX应用
- **基础开发**：编写控制器、服务和中间件
- **本地调试**：启动开发服务器进行本地测试

**使用场景**：
- 新建GuluX项目
- 了解Node.js服务框架基础
- 企业级应用开发入门

[quick-start.md](./quick-start.md) - 快速入门指南
[idl-usage.md](./idl-usage.md) - 通过 Thrift IDL 编写 HTTP Server
[best-practices.md](./best-practices.md) - 最佳实践指南

## 控制器与路由

HTTP控制器和路由的定义与使用：

- **控制器定义**：使用@Controller装饰器声明控制器类
- **路由映射**：通过@Get、@Post等装饰器定义HTTP方法路由
- **参数提取**：使用@Query、@Body、@Param等参数装饰器
- **请求处理**：控制器作为请求处理的第一站，进行校验和预加工

**使用场景**：
- 定义RESTful API接口
- 处理HTTP请求和响应
- 实现业务逻辑入口

[controllers-routing.md](./controllers-routing.md) - 控制器与路由开发

## 应用生命周期

GuluX框架的生命周期管理机制，用于在服务启动和关闭过程中执行自定义逻辑：

- **生命周期阶段**：包括configWillLoad、configDidLoad、didLoad、willReady、didReady、beforeClose六个核心阶段
- **钩子函数**：使用@LifecycleHook装饰器声明生命周期回调函数
- **执行时机**：插件生命周期钩子先于应用执行，插件间按依赖关系顺序执行
- **应用场景**：客户端初始化、日志记录、实例属性修改、资源清理等一次性操作

**使用场景**：
- 服务启动时的初始化逻辑
- 客户端实例的创建和配置
- 应用关闭前的资源清理
- 插件和应用的协同启动

[lifecycle-management.md](./lifecycle-management.md) - 应用生命周期管理


## 中间件开发

中间件的编写和应用，用于抽象处理请求流程中的通用逻辑：

- **中间件定义**：必须是一个class且实现use方法
- **洋葱模型**：基于洋葱模型的请求处理流程
- **全局与局部**：支持全局中间件和按接口配置的中间件
- **执行顺序**：插件中间件优先于用户中间件执行

**使用场景**：
- 登录校验和权限控制
- 错误处理和日志记录
- 请求格式化和响应处理

[middleware-development.md](./middleware-development.md) - 中间件开发指南

## 插件体系

GuluX的插件扩展机制，通过可插拔形式对框架进行功能扩展：

- **插件分类**：npm包形式插件和项目内联插件
- **官方插件**：@gulux/plugin-redis、@gulux/plugin-sequelize等
- **协议插件**：HTTP和RPC协议插件提供API服务能力
- **插件配置**：在plugin.default.ts中配置插件启用状态

**使用场景**：
- 集成公司内部基建服务
- 扩展框架通用能力
- 抽象通用业务逻辑

[plugin-system.md](./plugin-system.md) - 插件体系详解

## 服务与依赖注入

服务层的开发和使用，实现业务逻辑的封装和复用：

- **服务定义**：使用@Injectable装饰器声明服务类
- **依赖注入**：通过@Inject装饰器注入依赖服务
- **业务逻辑**：在服务层实现核心业务逻辑
- **代码组织**：合理的分层架构设计

**使用场景**：
- 业务逻辑封装和复用
- 服务层代码组织
- 依赖管理和解耦

[services-di.md](./services-di.md) - 服务与依赖注入

## 配置管理

应用配置的管理和使用，支持不同环境的配置切换：

- **配置文件**：config目录下的配置文件结构
- **环境配置**：支持development、production等环境
- **插件配置**：插件相关的配置项管理
- **运行时配置**：通过@Config装饰器获取配置数据

**使用场景**：
- 多环境配置管理
- 敏感信息配置
- 运行时配置获取

[configuration-management.md](./configuration-management.md) - 配置管理指南


