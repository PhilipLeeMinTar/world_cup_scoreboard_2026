# 控制器与路由开发指南

## 控制器定义与职责

在GuluX框架中，控制器是请求处理的第一站，主要负责对请求进行校验、判断、预加工，然后转交给下一站处理或直接返回给客户端。

### 控制器定义方式
控制器通过`@Controller`装饰器进行定义，示例如下：

```typescript
// controller/user.ts
@Controller('/user')
export default class UserController {
  @Inject()
  public usrSvr: UserService; 
  
  @Get('/userlist')
  public async getUserList() {
    // 校验、判断、预加工...
    const result = await this.usrSvr.getUserList();
    // 对结果进行进一步处理
    return result;
  }
}
```

控制器包含四个主要部分：
1. 一个普通的class：如`UserController`
2. 属性方法：如`getUserList`、`getUserList2`
3. class装饰器：使用`@Controller`装饰器装饰class
4. 属性方法装饰器：使用`@Get`、`@Post`等装饰器装饰属性方法

### 控制器文件位置
GuluX对模块文件位置没有严格要求，用户只需要对某个class加上`@Controller`装饰器，框架就能自动识别。

## 请求参数提取

GuluX通过参数装饰器从请求中提取信息，使用格式为：
```typescript
function(@name([key]) pName: [type], ...){}
```

### 内置参数装饰器
GuluX HTTP模块提供了丰富的内置参数装饰器：

| 装饰器      | 用途                 | 示例                                    |
| ----------- | -------------------- | --------------------------------------- |
| `@Req()`    | 获取request对象      | `@Req() req: HTTPRequest`               |
| `@Res()`    | 获取response对象     | `@Res() res: HttpResponse`              |
| `@Next()`   | 声明中间件的next形参 | `@Next() next: NextFunction`            |
| `@Body()`   | 获取POST body对象    | `@Body('name') name: string`            |
| `@Query()`  | 获取query参数        | `@Query('id') id: string`               |
| `@Param()`  | 获取路由参数         | `@Param('userId') userId: string`       |
| `@Header()` | 获取headers          | `@Header('Authorization') auth: string` |
| `@Files()`  | 获取上传的文件       | `@Files() files: File[]`                |

### 参数提取示例
```typescript
@Get('/booklist')
async getBookList(@Query('storeId') storeId: string, @Req() req: HTTPRequest) {
    this.logger.info('getBookList|storeId|extract by Query', storeId);
    this.logger.info('getBookList|cityId|extract by Req', req.query.cityId);
    // ...
}
```

## 服务调用与依赖注入

控制器通过依赖注入调用服务层：

```typescript
// controller/user.ts
import UserService from './service/user';

@Controller('/user')
export default class UserController {
  // 注入UserService实例
  @Inject()
  public usrSvr: UserService; 
  
  @Get('/userlist')
  public async getUserList() {
    const result = await this.usrSvr.getUserList();
    return result;
  }
}
```

服务层定义：
```typescript
import { Injectable } from '@gulux/gulux';

@Injectable()
export default class UserService {
  public async getUserList() {
    return {
      code: 0,
      message: 'succ'
    };
  }
}
```

## 响应处理

### 设置响应体
GuluX简化了响应返回，用户只需在controller函数中返回结果：

```typescript
@Get('/userlist')
public async getUserList() {
  return {data: [...]}
}
```

### 设置响应头
通过`@Res()`装饰器获取response对象设置响应头：

```typescript
@Get('/userlist')
public async getUserList(@Res() res: HttpResponse) {
  const result = await this.usrSvr.getUserList();
  res.set('Content-Type', 'application/json');
  return result;
}
```

### 设置状态码
```typescript
@Get('/userlist')
public async getUserList(@Res() res: HttpResponse) {
  const result = await this.usrSvr.getUserList();
  res.status = 204;
  return result;
}
```

### 重定向
```typescript
@Get('/userlist2')
async getUserList(@Res() res: HTTPResponse) {
  if(...){
    res.redirect('/');
  }
}
```

## 路由定义与匹配

### 路由机制
GuluX采用装饰器声明路由，与控制器定义在一起：

```typescript
import { Inject } from '@gulux/gulux';
import { Controller, Get } from '@gulux/gulux/application-http';

@Controller('/user')
export default class UserController {
  @Inject()
  usrSvr: UserService;

  @Get('/userlist')
  async getUserList() {
    return await this.usrSvr.getUserList();
  }
}
```

### 路径组成
GuluX路径由三部分组成：
- 全局路由前缀：`routerPrefix`
- `@Controller`声明的path：`controllerPath`
- `@Get`声明的path：`methodPath`

最终路径：`${globalPrefix || ''}${controllerPath}${methodPath}`

### 路径格式支持
GuluX支持四种路由格式，匹配优先级从高到低：

1. **静态格式**
```typescript
@Get('/user/list')
```

2. **带参数的路径**
```typescript
@Get('/user/info/:id') // 匹配 /user/info/12
```

3. **通配符形式**
```typescript
@All('/views/*')
```

4. **带参数并用正则表达式修饰**
```typescript
@Get('/user/info/:id(^\\d+)')
```

### 全局路由前缀配置
```typescript
// config/config.default.ts
export default {
    applicationHttp: {
        routerPrefix: '/api/v1'
    }
}
```

## 路由中间件

GuluX支持在class层级和属性层级添加中间件：

```typescript
import { Controller, Get } from '@gulux/gulux/application-http';
import { middlewareA, middlewareB, middlewareC } from './middlewares/index';

@Controller({
  path: '/user',
  middlewares: [middlewareA, middlewareB]
})
export default class UserController {

  @Get('/userlist', {
    middlewares: [middlewareC]
  })
  async getUserList() {...}

  @Get('/userlist2')
  async getUserList2() {...}
}
```

中间件执行顺序：
- 访问`/user/userlist`：`[...全局中间件] -> middlewareA -> middlewareB -> middlewareC`
- 访问`/user/userlist2`：`[...全局中间件] -> middlewareA -> middlewareB`

## 错误处理

GuluX提供三种错误处理方式：

1. **用户自定义处理**：主动在业务代码外包try-catch
```typescript
@Get('/userlist')
public async getUserList() {
  try {
    let res;
    // ...
    return res;
  } catch (err) {
    return {data: []}
  }
}
```

2. **抛出指定异常**：业务代码抛出错误，由exception filter自动捕获

3. **AOP方式**：通过`afterThrow`处理错误

## HTTP方法装饰器

GuluX支持所有标准HTTP方法的装饰器：

| 装饰器       | HTTP方法 | 用途               |
| ------------ | -------- | ------------------ |
| `@Get()`     | GET      | 获取资源           |
| `@Post()`    | POST     | 创建资源           |
| `@Put()`     | PUT      | 更新资源           |
| `@Delete()`  | DELETE   | 删除资源           |
| `@Patch()`   | PATCH    | 部分更新资源       |
| `@Options()` | OPTIONS  | 获取支持的HTTP方法 |
| `@Head()`    | HEAD     | 获取响应头         |
| `@All()`     | 所有方法 | 匹配所有HTTP方法   |

## 最佳实践

### 控制器设计原则
1. **单一职责**：每个控制器专注于特定业务领域
2. **简洁明了**：控制器方法应保持简洁，复杂逻辑委托给服务层
3. **错误处理**：合理使用异常处理机制
4. **依赖注入**：通过依赖注入解耦业务逻辑

### 路由设计建议
1. **RESTful风格**：遵循RESTful API设计原则
2. **版本控制**：通过全局路由前缀实现API版本管理
3. **中间件分层**：合理使用全局、控制器级、方法级中间件
4. **路径规范**：使用清晰、一致的路径命名

### 性能优化
1. **路由匹配**：优先使用静态路由格式
2. **参数验证**：在控制器层进行参数验证
3. **缓存策略**：合理使用缓存减少重复计算
4. **异步处理**：充分利用异步编程特性

