# GuluX 快速入门指南

本文档提供GuluX框架的快速入门指导，帮助开发者快速上手基于GuluX的Node.js服务端应用开发。

## 环境要求

在开始之前，请确保满足以下环境要求：

- **Node.js版本**：GuluX要求Node.js >= 14版本
- **包管理器**：推荐使用npm或yarn
- **TypeScript**：GuluX基于TypeScript开发，需要TypeScript环境支持

## 项目初始化

### 使用CLI创建项目

通过GuluX CLI快速初始化项目结构：

```bash
npm init @gulux/gulux-app --registry=https://bnpm.byted.org
```

或者使用npx方式：

```bash
npx -p @gulux/cli gulux init
```

![GuluX CLI初始化界面](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/cd1d6a14a16947ada07c8b0f59a5445f~tplv-tika-image.image) 

### 项目目录结构

初始化完成后，您将得到以下标准的项目结构：

```bash
.
├── config                      # 配置文件存放目录
│   ├── config.default.ts      # 默认配置
│   ├── config.dev.ts          # dev环境配置
│   ├── config.prod.ts         # prod环境配置
│   ├── config.test.ts         # test环境配置
│   └── plugin.default.ts      # 插件配置
├── controller                  # Controller文件存放目录
│   └── home.ts
├── service                     # Service文件存放目录
│   └── user.ts
├── middleware                  # 中间件文件存放目录
│   └── demo.ts
├── package.json
├── test
│   └── index.test.ts
├── README.md
├── build.sh                    # 构建脚本，SCM构建必须，请勿修改
├── jest.config.js
└── tsconfig.json
```

## 基础开发流程

### 1. 配置管理

#### 插件配置
在`config/plugin.default.ts`中配置需要启用的插件：

```typescript
export default {
  'application-http': {
    enable: true, // 开启HTTP服务插件
  },
};
```

#### 应用配置
在`config/config.default.ts`中配置应用基础信息：

```typescript
import { ApplicationConfig } from '@gulux/gulux';

export default {
  name: 'app',
  applicationHttp: {
    port: Number(process.env.PORT) || 3000,
    routerPrefix: '/api', // 全局路由前缀
  },
} as ApplicationConfig;
```

### 2. 控制器开发

创建控制器处理HTTP请求：

```typescript
// controller/book.ts
import { Controller, Get } from '@gulux/gulux/application-http';

@Controller({ path: '/book' })
export default class BookController {
    @Get('/list')
    public async getBookList() {
        return {
            code: 0,
            data: [],
            message: 'success'
        };
    }
    
    @Get('/:id')
    public async getBookById() {
        // 获取图书详情逻辑
    }
}
```

### 3. 服务层开发

创建服务类封装业务逻辑：

```typescript
// service/user.ts
import { Injectable } from '@gulux/gulux';

@Injectable()
export default class UserService {
    public async getInfo() {
        return {
            name: 'example',
            email: 'example@bytedance.com',
        };
    }
}
```

### 4. 中间件开发

创建中间件处理通用逻辑：

```typescript
// middleware/global_exception.ts
import { Middleware, Next, GuluXMiddleware, NextFunction} from '@gulux/gulux';
import { Res, Response } from '@gulux/gulux/application-http';

@Middleware()
export default class GlobalExceptionMiddleware extends GuluXMiddleware {
  public async use(@Res() res: Response, @Next() next: NextFunction) {
    try {
      await next();
    } catch (err) {
      res.body = {
        code: err.code || 9999,
        message: err.message || '网络异常，请稍后重试',
      };
    }
  }
}
```

## 启动与测试

### 本地开发启动

使用以下命令启动本地开发服务器：

```bash
npm run dev
```

![本地开发启动日志](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/1d49d28ffc254e6ab3cd0a76c4cd87be~tplv-tika-image.image) 

### 接口测试

应用启动后，可以通过curl命令测试接口：

```bash
# 获取图书列表
curl http://127.0.0.1:3000/api/book/list

# 获取图书详情
curl http://127.0.0.1:3000/api/book/1
```

### 示例项目接口

GuluX示例项目提供了完整的HTTP服务接口示例：

```bash
# 获取图书列表
curl --location --request GET 'http://127.0.0.1:3000/api/book/list'

# 获取图书详情
curl --location --request GET 'http://127.0.0.1:3000/api/book/1'

# 新增图书
curl --location --request POST 'http://127.0.0.1:3000/api/book' \
--header 'Content-Type: application/json' \
--data-raw '{
    "isbn": "9787208171336",
    "title": "海边的房间",
    "description": "无常往往最平常，老灵魂的世情书写，温热冷艳，拨动平凡市井里的人心与天机，失意人的情欲与哀伤，我们日常的困顿与孤独。"
}'

# 更新图书
curl --location --request PUT 'http://127.0.0.1:3000/api/book/1' \
--header 'Content-Type: application/json' \
--data-raw '{
    "id": 2,
    "title": "更新后的标题"
}'
```

## 生产环境部署

### 构建应用

在部署到生产环境前，需要先构建应用：

```bash
gulux build
```

### 启动应用

**重要提示**：`gulux start`命令一般只在线上环境使用，不要在本地开发环境使用！

```bash
# 进入构建输出目录
cd output

# 启动应用
gulux start
```

![生产环境启动日志](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/3cc5bb893d14d5385d7bc2e3135831f~tplv-tika-image.image) 

### 启动选项

`gulux start`支持多种启动选项：

```bash
# 以daemon方式启动
gulux start --daemon

# 开启auto env能力
gulux start --auto-env

# 设置应用启动worker数量
gulux start --instances=2

# 简化版Node启动方式（Goofy Deploy或Stack环境使用）
gulux start --direct
```

## 常见问题

### 1. 启动报错：app xxx exists

如果多次重复执行`gulux start`会报错"app xxx exists, use restart command instead"，此时应使用restart命令：

```bash
gulux restart
```

### 2. 启动报错：必须在output目录执行

如果没有进入编译后目录output直接执行`gulux start`，会报错"The 'start' command only supports execution in the 'output' directory"：

![output目录错误提示](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/edd0bde50a9d410ebdba5f5f048f4a08~tplv-tika-image.image) 

正确做法：

```bash
gulux build
cd output
gulux start
```

### 3. 传递Node命令行选项

根据部署平台不同，传递Node命令行选项的方式也不同：

- **TCE平台**（通过node.js cluster模式启动）：
  ```bash
  gulux start --node-args '--max-http-header-size 65536'
  ```

- **Goofy Deploy平台**（单进程模式启动）：
  ```bash
  NODE_OPTIONS='--max-http-header-size=65536' gulux start
  ```

## 下一步

完成快速入门后，建议继续学习：

1. **控制器与路由**：深入学习HTTP控制器和路由的定义与使用
2. **服务与依赖注入**：掌握服务层的开发和依赖注入机制
3. **中间件开发**：了解中间件的编写和应用场景
4. **插件体系**：探索GuluX的插件扩展机制

## 参考资源

- [GuluX官方文档站](https://gulux.bytedance.net/guide/getting-started.html)
- [GuluX使用手册](https://bytedance.feishu.cn/wiki/wikcnD568NVBT7d95DAu3dunZdc)
- [示例项目地址](https://code.byted.org/nodejs/tutorial_gulux_http_server)
