# GuluX 最佳实践指南

## RPC 服务调用

### 推荐方案：IDL 生成的客户端 SDK

对于字节跳动内部服务，推荐使用 BAM 平台生成 SDK：

#### 1. 配置 BAM 平台

1. 导入服务并使用 IDL 格式配置接口（不推荐在线编辑）
2. 选择 Node.js 作为语言/框架
3. 选择 "RPC Client" 作为调用方式
4. 执行手动生成以创建初始版本

#### 2. 安装和使用

```bash
npm i -S @gulux-bam/[service_name]@version
```

```typescript
// config/plugin.default.ts
export default {
  '[service-name]-rpc-client': { enable: true },
};

// 在 Controller 中使用
@Controller({ path: '/api' })
export class APIController {
  @Inject()
  myServiceClient: MyServiceClient;

  @Get('/data')
  async getData() {
    return this.myServiceClient.getData();
  }
}
```

#### 3. 统一管理

可以选择一个 PSM 作为根，在 BAM 统一管理 IDL 更新和代码生成。

### 跨机房调用

- **生产环境**：使用 Neptune 平台的 mesh 调度
- **开发环境**：可通过 `toIdc` 参数临时配置

### 环境/泳道指定

**强烈推荐**：通过调用链传递环境信息，而非在应用代码中硬编码。硬编码在生产环境中风险极高。

## 项目结构

### 推荐目录结构

GuluX 默认会从项目根目录下的 `config/` 目录加载配置文件（可通过应用选项修改 `configDir`）。如果你的项目使用 `src/config` 这类结构，需要在启动应用或应用选项中显式指定 `configDir` 指向对应目录，否则配置不会被正确加载。

```
config/                      # 配置文件（默认位于项目根目录）
├── config.default.ts
├── config.dev.ts
├── config.prod.ts
└── plugin.default.ts
src/
├── controller/              # 控制器
│   └── api/
│       ├── UserController.ts
│       └── BookController.ts
├── service/                 # 服务层
│   ├── UserService.ts
│   └── BookService.ts
├── middleware/              # 中间件
│   ├── AuthMiddleware.ts
│   └── LogMiddleware.ts
├── repository/              # 数据访问层（可选）
│   └── UserRepository.ts
├── model/                   # 数据模型
│   └── User.ts
├── dto/                     # 数据传输对象
│   ├── CreateUserDto.ts
│   └── UpdateUserDto.ts
├── lifecycle/               # 生命周期钩子
│   └── AppLifecycle.ts
└── plugin/                  # 本地插件（如有）
    └── my-plugin/
```

## 分层架构

### Controller → Service → Repository

```typescript
// repository/UserRepository.ts
@Injectable()
export class UserRepository {
  @Inject()
  sequelize: Sequelize;

  async findById(id: number): Promise<User | null> {
    return User.findByPk(id);
  }
}

// service/UserService.ts
@Injectable()
export class UserService {
  @Inject()
  userRepo: UserRepository;

  async getUser(id: number): Promise<User> {
    const user = await this.userRepo.findById(id);
    if (!user) throw new NotFoundException('User not found');
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

## 错误处理

### 统一错误处理中间件

```typescript
@Middleware()
export class ErrorHandlerMiddleware extends GuluXMiddleware {
  public async use(@Req() req: HTTPRequest, @Res() res: HTTPResponse, @Next() next: NextFunction) {
    try {
      await next();
    } catch (error) {
      if (error instanceof BusinessError) {
        res.status = error.statusCode;
        res.body = {
          code: error.code,
          message: error.message,
        };
      } else {
        console.error('Unexpected error:', error);
        res.status = 500;
        res.body = {
          code: 'INTERNAL_ERROR',
          message: 'Internal Server Error',
        };
      }
    }
  }
}
```

### 自定义业务异常

```typescript
export class BusinessError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number = 400,
  ) {
    super(message);
  }
}

export class NotFoundException extends BusinessError {
  constructor(message: string) {
    super('NOT_FOUND', message, 404);
  }
}

export class UnauthorizedException extends BusinessError {
  constructor(message: string = 'Unauthorized') {
    super('UNAUTHORIZED', message, 401);
  }
}
```

## 配置管理

### 环境区分

```typescript
// config/config.default.ts - 所有环境共享
export default {
  port: 3000,
  middleware: [ErrorHandlerMiddleware, LogMiddleware],
};

// config/config.dev.ts - 开发环境
export default {
  port: 3001,
  debug: true,
};

// config/config.prod.ts - 生产环境
export default {
  port: 8080,
  debug: false,
};
```

### 敏感配置

使用 TCC 或 KMS 管理敏感配置：

```typescript
// config/plugin.default.ts
export default {
  tcc: { enable: true },
  'kms-v2': { enable: true },
};
```

## 日志和监控

### 使用 byted-logger

```typescript
// config/plugin.default.ts
export default {
  'byted-logger': { enable: true },
};

// 在代码中使用
@Injectable()
export class UserService {
  @Inject()
  logger: Logger;

  async getUser(id: number) {
    this.logger.info('Getting user', { userId: id });
    // ...
  }
}
```

### 使用 byted-metrics

```typescript
// config/plugin.default.ts
export default {
  'byted-metrics-v2': { enable: true },
};

// 在代码中使用
@Injectable()
export class UserService {
  @Inject()
  metrics: Metrics;

  async getUser(id: number) {
    const timer = this.metrics.startTimer('user_get_duration');
    try {
      const user = await this.doGetUser(id);
      this.metrics.increment('user_get_success');
      return user;
    } catch (error) {
      this.metrics.increment('user_get_error');
      throw error;
    } finally {
      timer.end();
    }
  }
}
```

## 测试

### 单元测试

```typescript
import { Test } from '@gulux/testing';
import { UserService } from '../service/UserService';
import { UserRepository } from '../repository/UserRepository';

describe('UserService', () => {
  let userService: UserService;
  let mockUserRepo: jest.Mocked<UserRepository>;

  beforeEach(async () => {
    mockUserRepo = {
      findById: jest.fn(),
    } as any;

    const module = await Test.createTestingModule({
      providers: [
        UserService,
        { provide: UserRepository, useValue: mockUserRepo },
      ],
    }).compile();

    userService = module.get(UserService);
  });

  it('should return user when found', async () => {
    const mockUser = { id: 1, name: 'Test' };
    mockUserRepo.findById.mockResolvedValue(mockUser);

    const result = await userService.getUser(1);
    expect(result).toEqual(mockUser);
  });

  it('should throw when user not found', async () => {
    mockUserRepo.findById.mockResolvedValue(null);

    await expect(userService.getUser(1)).rejects.toThrow('User not found');
  });
});
```

## 性能优化

### 预构建

GuluX 支持预构建 Manifest，加速启动：

```bash
# 生产构建时生成 manifest
npm run build
```

### 缓存策略

```typescript
@Injectable()
export class UserService {
  @Inject()
  redis: Redis;

  @Inject()
  userRepo: UserRepository;

  async getUser(id: number): Promise<User> {
    const cacheKey = `user:${id}`;

    // 先查缓存
    const cached = await this.redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // 查数据库
    const user = await this.userRepo.findById(id);
    if (user) {
      await this.redis.setex(cacheKey, 3600, JSON.stringify(user));
    }

    return user;
  }
}
```