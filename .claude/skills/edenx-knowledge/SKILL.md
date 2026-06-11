---
name: edenx-knowledge
description: 当在 React 项目中使用 EdenX 框架开发、使用 @edenx/app-tools 创建项目、配置 Builder/Runtime/Server、使用 Rspack 构建、开发 SSR/BFF 应用、或集成 Garfish/Vmok 时使用。
user-invocable: false
---

# EdenX 知识库

EdenX 是字节跳动内部基于 React 的渐进式现代 Web 开发框架,由 Web Infra 团队推出。它融合了内部两大框架 Eden 和 Jupiter 的优势,提供了从开发到生产的一体化解决方案。框架内置了强大的构建工具(支持 Rspack)、完善的运行时方案和统一的服务端支持,覆盖了从开发、调试到部署的全流程。

## 框架介绍

EdenX 框架的核心概念和设计理念,帮助开发者全面理解框架架构:

- **核心组件**:构建器(Builder)、运行时(Runtime)、服务端(Server)三大核心
- **设计原则**:渐进式、一体化、开箱即用、强大的生态
- **架构设计**:基于 Rspack/Webpack 的高性能构建,插件化运行时,统一的 Web Server
- **框架定位**:从小型项目到大型复杂应用的全场景覆盖

**使用场景**:
- 了解 EdenX 框架的整体架构
- 理解渐进式开发理念
- 选择合适的技术栈和开发模式
- 企业级 React 应用开发入门

[edenx-introduction.md](./edenx-introduction.md) - EdenX 框架介绍与核心组件

## 核心原理

EdenX 的核心技术架构和实现原理,深入理解框架的工作机制:

- **构建器原理**:双引擎驱动(Webpack/Rspack)、插件化扩展、配置抹平
- **运行时机制**:路由管理、状态管理、数据请求、生命周期管理
- **服务端架构**:统一的开发和生产环境 Web Server、BFF 层、SSR 支持
- **渐进式设计**:从纯构建工具到一体化全栈开发的灵活使用

**使用场景**:
- 理解 EdenX 的技术架构
- 深入掌握构建和运行时原理
- 进行框架层面的扩展和定制
- 解决复杂的技术问题

[edenx-principles.md](./edenx-principles.md) - EdenX 核心原理与技术架构

## 功能特性

EdenX 提供的强大功能和特性,提升开发效率和应用性能:

- **高性能构建**:Rspack 构建引擎、SWC/esbuild 支持、Rsbuild 升级
- **渐进式与一体化**:灵活的功能启用、统一的开发体验、CSR/SSR 同构
- **开箱即用**:零配置启动、内置工具链、多种路由模式
- **插件系统**:CLI/Server/Runtime 三层插件机制
- **EdenX Module**:专业的 npm 包开发工具,双模式构建
- **生态集成**:微前端/微模块、Monorepo、状态管理、UI 库

**使用场景**:
- 选择合适的构建工具和配置
- 启用和配置各项功能特性
- 开发 npm 包和组件库
- 集成公司内外优秀解决方案

[edenx-features.md](./edenx-features.md) - EdenX 功能特性详解

## 配置管理

EdenX 的配置系统和配置方法,实现项目的个性化定制:

- **配置文件类型**:编译时配置(edenx.config.ts)、运行时配置、服务端配置
- **编译时配置**:defineConfig 使用、Rspack 切换、插件注册
- **底层工具配置**:webpack/rspack、babel、postcss、less/sass 等配置
- **配置迁移**:从 Eden v2/Jupiter 迁移的配置映射关系

**使用场景**:
- 配置项目构建和编译选项
- 自定义路由、状态管理等运行时行为
- 配置 BFF 和 SSR 服务端逻辑
- 从旧版本框架迁移配置

[edenx-configuration.md](./edenx-configuration.md) - EdenX 配置管理指南

## 生态系统

EdenX 的周边工具和生态解决方案,构建完整的开发体系:

- **核心生态工具**:Rslib(npm 包开发)、EdenX Doc(文档站)、Rsbuild(跨框架构建)
- **大型项目架构**:Garfish(微前端)、Vmok(微模块)
- **工程与效率**:EMO(Monorepo)、Rsdoctor(构建分析)
- **插件与集成**:国际化、中后台、监控、遥测等

**使用场景**:
- 开发和发布 npm 包
- 搭建项目文档站点
- 实现微前端或微模块架构
- 管理 Monorepo 项目
- 分析和优化构建性能

[edenx-ecosystem.md](./edenx-ecosystem.md) - EdenX 生态系统

## 应用场景

EdenX 的典型应用场景和解决方案,满足不同项目需求:

- **中后台管理系统**:@edenx/preset-admin 插件集、Arco Design 集成、开发效率提升
- **SSR 应用**:一体化 SSR、数据获取、SEO 优化、首屏性能
- **微前端架构**:Garfish 集成、主应用与子应用开发、团队协作
- **NPM 包开发**:EdenX Module、双模式构建、Storybook 集成

**使用场景**:
- 开发企业内部运营平台
- 构建对 SEO 友好的 C 端应用
- 实现大型应用的微前端拆分
- 开发和发布组件库

[edenx-use-cases.md](./edenx-use-cases.md) - EdenX 常见应用场景

## 最佳实践

EdenX 项目的各种功能配置最佳实践,快速启用和配置功能:

- **BFF 开发**:Backend For Frontend 接口开发、Gulux 框架集成
- **入口管理**:单入口与多入口项目、框架模式与构建模式
- **自定义 Server**:Web 服务器中间件、请求处理、生命周期
- **监控能力**:Slardar 集成、SourceMap 上传、前端和服务端监控
- **微前端**:Garfish 配置、主子应用开发
- **国际化**:Starling Intl 和 i18next 支持
- **静态站点生成**:SSG 配置和使用
- **中后台预设**:Admin 插件集、Arco/Semi Design 选择

**使用场景**:
- 为项目启用各种功能特性
- 配置开发和生产环境
- 集成监控和埋点
- 快速搭建中后台应用
- 实现国际化和 SEO 优化

[best-practices.md](./best-practices.md) - EdenX 最佳实践配置指南

## 版本升级

EdenX v1 到 v3 的完整升级迁移指南,涵盖所有配置和代码变更:

- **升级概览**:主要变更、升级收益、构建工具切换到 Rspack
- **兼容性检查**:不支持迁移的依赖、React 版本要求
- **升级步骤**:Node.js 升级、依赖升级、配置文件迁移、入口文件迁移
- **配置迁移**:html/output/source/tools/runtime/server 配置映射
- **插件迁移**:Garfish、Axios、i18n、Slardar、State、Tailwind 等插件迁移
- **导入路径迁移**:运行时导入路径更新映射表
- **自定义 Server 迁移**:中间件和 Hook 写法更新
- **自动化工具**:tmates-cli 自动迁移工具使用方法

**使用场景**:
- 将 EdenX v1 项目升级到 v3
- 迁移配置和代码到新版本
- 理解版本间的破坏性变更
- 使用自动化工具快速升级

[upgrade-v1-to-v3.md](./upgrade-v1-to-v3.md) - EdenX v1 到 v3 完整升级指南

## 路由系统

EdenX 基于文件约定的路由系统深度解析,掌握框架路由的核心能力:

- **嵌套路由**:URL 片段与组件层级的深度耦合设计模式
- **文件约定**:page.tsx、layout.tsx、loading.tsx、error.tsx 等路由文件规范
- **动态路由**:通过 `[id]` 目录命名实现动态参数匹配
- **通配路由**:使用 `$.tsx` 捕获所有未匹配的路径
- **无路径布局**:使用 `__` 前缀实现不影响 URL 的布局分组
- **路由重定向与错误处理**:高级路由控制能力

**使用场景**:
- 设计和组织项目的路由结构
- 实现嵌套布局和动态页面
- 配置路由重定向和 404 处理
- 理解约定式路由的工作原理

[edenx-routes.md](./edenx-routes.md) - EdenX 路由系统深度解析

## 数据管理与获取

EdenX 与约定式路由深度集成的 Data Loader 数据获取机制:

- **Data Loader 机制**:通过 `.data.ts` 文件为路由组件准备数据
- **loader 函数**:在组件渲染前执行的异步数据获取函数
- **参数传递**:通过 `params` 和 `request` 获取路由参数和请求信息
- **不同渲染环境**:CSR 和 SSR 下 loader 的行为差异
- **错误处理**:数据加载失败的优雅降级方案
- **缓存与重新验证**:数据缓存策略和更新机制

**使用场景**:
- 为页面组件获取和准备数据
- 实现 SSR 场景下的数据预取
- 处理数据加载错误和异常
- 优化数据获取的性能和体验

[edenx-data-management.md](./edenx-data-management.md) - EdenX 数据管理与获取

## BFF 一体化开发

EdenX 的 BFF（Backend for Frontend）解决方案,实现前后端一体化开发:

- **BFF 价值**:消除胶水代码、类型安全、数据聚合
- **启用方式**:Aiden CLI 快捷启用、手动配置集成 Gulux 或 Hono
- **函数定义**:在 `api/` 目录下编写 TypeScript 函数作为服务端接口
- **路由约定**:BFF 函数的文件路径与 API 路由的映射规则
- **参数传递**:前端调用 BFF 函数的参数序列化和类型推断
- **Gulux 集成**:与公司内部 Gulux 框架的深度集成方案

**使用场景**:
- 开发前后端一体化的 API 接口
- 实现类型安全的前后端数据交互
- 聚合多个微服务的数据
- 集成 Gulux 框架进行 BFF 开发

[edenx-bff.md](./edenx-bff.md) - EdenX BFF 一体化开发实践

## 渲染模式

EdenX 支持的多种渲染模式对比与选型指南:

- **CSR（客户端渲染）**:浏览器端动态生成 DOM,适合交互密集型应用
- **SSR（服务端渲染）**:服务器预渲染完整 HTML,提升首屏和 SEO
- **Streaming SSR（流式 SSR）**:边渲染边传输,EdenX 中 SSR 的默认模式
- **SSG（静态站点生成）**:构建时生成静态 HTML,追求极致加载速度
- **RSC（React Server Components）**:组件在服务端运行,大幅减少客户端 JS 体积
- **渲染模式选型**:不同业务场景下的决策指南

**使用场景**:
- 选择适合项目的渲染策略
- 配置和切换 CSR/SSR/SSG 模式
- 启用流式 SSR 提升首屏性能
- 评估和使用 React Server Components

[edenx-rendering.md](./edenx-rendering.md) - EdenX 渲染模式深度解析

## 性能优化

EdenX 中的前端性能优化策略,构建高性能 Web 应用:

- **约定式路由自动分割**:框架自动为每个路由页面创建独立代码块
- **动态 import()**:按需加载非首屏必须的组件和库
- **React.lazy**:React 组件级别的懒加载和 Suspense 集成
- **静态资源内联**:将小体积资源直接内联到 HTML/JS 中减少请求
- **Chunk 优化**:代码块的拆分和合并策略
- **性能分析**:使用 Rsdoctor 等工具分析和优化构建产物

**使用场景**:
- 优化应用首屏加载速度
- 实现组件和模块的按需加载
- 配置静态资源的内联策略
- 分析和减小打包产物体积

[edenx-performance.md](./edenx-performance.md) - EdenX 性能优化策略

## 国际化 (i18n)

EdenX 基于 i18next 和 Starling 平台的国际化解决方案:

- **核心技术栈**:i18next + react-i18next + Starling 平台
- **本地化开发**:启用 i18n 插件、配置语言资源文件、useTranslation Hook
- **命名空间**:翻译资源的拆分和按需加载
- **Starling 集成**:与公司翻译平台的对接工作流,实现文案与代码分离
- **React 最佳实践**:useTranslation Hook、Trans 组件、插值和复数处理
- **语言切换**:运行时动态切换语言的实现方案

**使用场景**:
- 为应用添加多语言支持
- 集成 Starling 翻译平台管理文案
- 实现语言的动态切换
- 组织和优化翻译资源的加载

[edenx-i18n.md](./edenx-i18n.md) - EdenX 国际化 (i18n) 解决方案