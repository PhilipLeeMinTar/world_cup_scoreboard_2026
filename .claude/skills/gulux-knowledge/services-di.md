# 服务与依赖注入

## 服务（Service）概述

在GuluX框架中，服务（Service）是用于抽象业务逻辑的核心单元，将复杂的业务逻辑从控制器中分离出来，实现代码的解耦和复用。

## 基本用法

Service 通常放在 `src/service/` 目录下，使用 `@Injectable()` 装饰器：

```typescript
import { Injectable } from '@gulux/gulux';

@Injectable()
export class UserService {
  async getUser(id: number): Promise<User> {
    return { id, name: 'Noah', department: { id: 1, name: 'EngProd' } };
  }

  async createUser(data: CreateUserDto): Promise<User> {
    // 业务逻辑实现
    return { id: 1, ...data };
  }

  async updateUser(id: number, data: UpdateUserDto): Promise<User> {
    // 业务逻辑实现
    return { id, ...data };
  }

  async deleteUser(id: number): Promise<boolean> {
    // 业务逻辑实现
    return true;
  }
}
```

## 依赖注入

### 在 Controller 中注入 Service

```typescript
import { Inject } from '@gulux/gulux';
import { Controller, Get, Query } from '@gulux/gulux/application-http';
import { UserService } from '../service/UserService';

@Controller({ path: '/api/user' })
export class UserController {
  @Inject()
  userService: UserService;

  @Get('/')
  async getUser(@Query('id') uid: number) {
    const user = await this.userService.getUser(uid);
    return { user };
  }
}
```

### Service 之间相互注入

```typescript
import { Injectable, Inject } from '@gulux/gulux';
import { LogService } from './LogService';
import { CacheService } from './CacheService';

@Injectable()
export class UserService {
  @Inject()
  logService: LogService;

  @Inject()
  cacheService: CacheService;

  async getUser(id: number): Promise<User> {
    // 先从缓存获取
    const cached = await this.cacheService.get(`user:${id}`);
    if (cached) {
      this.logService.log(`Cache hit for user ${id}`);
      return cached;
    }

    // 从数据库获取
    const user = await this.fetchUserFromDB(id);
    await this.cacheService.set(`user:${id}`, user);
    return user;
  }

  private async fetchUserFromDB(id: number): Promise<User> {
    // 数据库查询逻辑
    return { id, name: 'User' };
  }
}
```

## 核心装饰器

### @Injectable()

将类注册到 IoC 容器，使其可被自动实例化和注入：

```typescript
import { Injectable } from '@gulux/gulux';

@Injectable()
export class MyService {
  // 服务实现
}
```

### @Inject()

从容器中获取已注册的实例并注入到类属性：

```typescript
import { Inject } from '@gulux/gulux';

@Injectable()
export class MyService {
  @Inject()
  otherService: OtherService;
}
```

**注意**：`@Inject()` 需要对应的类使用 `@Injectable()` 装饰器注册。

## 配置注入

Service 中也可以注入配置：

```typescript
import { Injectable, Config } from '@gulux/gulux';

interface ApiConfig {
  baseUrl: string;
  timeout: number;
}

@Injectable()
export class ApiService {
  @Config('api')
  api: ApiConfig;

  async request(path: string) {
    // 使用配置的 baseUrl 和 timeout
    return fetch(`${this.api.baseUrl}${path}`, {
      timeout: this.api.timeout,
    });
  }
}
```

> 注意：`@Config('api')` 会从合并后的配置中读取 `config.api` 对象。如果使用 `'api.baseUrl'` 这类点号路径，则会查找 `config['api.baseUrl']` 这个扁平键，而不会从 `config.api.baseUrl` 中取值。

## 设计模式

### 分层架构

```
Controller (HTTP 处理)
    ↓
Service (业务逻辑)
    ↓
Repository (数据访问)
```

### 示例

```typescript
// repository/UserRepository.ts
@Injectable()
export class UserRepository {
  async findById(id: number): Promise<User | null> {
    // 数据库查询
    return { id, name: 'User' };
  }

  async save(user: User): Promise<User> {
    // 数据库保存
    return user;
  }
}

// service/UserService.ts
@Injectable()
export class UserService {
  @Inject()
  userRepo: UserRepository;

  async getUser(id: number): Promise<User> {
    const user = await this.userRepo.findById(id);
    if (!user) {
      throw new Error('User not found');
    }
    return user;
  }
}

// controller/UserController.ts
@Controller({ path: '/api/user' })
export class UserController {
  @Inject()
  userService: UserService;

  @Get('/:id')
  async getUser(@Param('id') id: number) {
    return this.userService.getUser(id);
  }
}
```

## 最佳实践

1. **单一职责**：每个 Service 只负责一个领域的业务逻辑
2. **依赖抽象**：通过接口定义依赖，便于测试和替换
3. **避免循环依赖**：合理划分 Service 边界，避免 A 依赖 B，B 又依赖 A
4. **异步处理**：使用 async/await 处理异步操作
5. **错误处理**：在 Service 层统一处理业务异常

## 相关资源
- [GuluX官方文档 - 服务](https://gulux.bytedance.net/guide/basic/service.html)
- [GuluX官方文档 - 依赖注入](https://gulux.bytedance.net/guide/advanced/di.html)
