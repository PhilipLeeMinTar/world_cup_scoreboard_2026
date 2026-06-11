# 通过 Thrift IDL 编写 HTTP Server

## 背景与适用场景

在 GuluX 项目中，当整个服务的 HTTP 接口都采用 IDL（接口定义语言）进行统一管理时，我们可以利用 GuluX CLI 的能力，从 IDL 文件一键生成 Controller 的模板代码。这种做法极大地提升了开发效率，并确保了代码实现与接口定义的一致性。

该功能尤其适用于遵循统一 `controller` 目录结构（而非 DDD 等分层架构）的项目。它与多文件 IDL 模式无缝集成，支持将分散在不同 `.thrift` 文件中的 Service 定义，统一生成到对应的 Controller 文件中。

## 前置条件

在开始之前，请确保你的开发环境和项目结构满足以下要求：

- **@gulux/cli 版本**: 必须 `> =1.9.0`。
- **IDL 目录 (idl-root)**: 项目中应有一个存放所有 Thrift IDL 文件的根目录，例如 `./idl`。
- **入口 IDL (main-idl)**: 需要一个主 IDL 文件（如 `main.thrift`），它通过 `include` 和 `extends` 汇总了项目所需的所有 Service 定义。
- **项目结构**: 推荐一个清晰的目录结构，以便管理 IDL、生成的代码和业务逻辑。

## CLI 指令详解

核心操作依赖 `gulux cg` (code generation) 命令。

### 基础代码生成

首先，生成基础的类型定义和辅助代码是必需的。此命令会解析 IDL 并在默认的 `gulux_gen/` 目录下生成 TypeScript 类型、常量等。

```bash
npx gulux cg --type http-server --idl-root ./idl --main-idl main.thrift
```

- `--type http-server`: 指定生成用于 HTTP 服务的代码。
- `--idl-root ./idl`: 指定 IDL 文件所在的根目录。
- `--main-idl main.thrift`: 指定包含所有 Service 定义的入口 IDL 文件。

`gulux_gen` 目录是自动生成代码的存放处，可以根据团队协作模式选择将其提交至代码库，或在 CI/CD 流程中动态生成。

### 自动生成 Controller

在基础命令之上，增加 `--gen-controller` 标志即可激活 Controller 代码的自动生成。

```bash
npx gulux cg --type http-server --idl-root ./idl --main-idl main.thrift --gen-controller
```

默认情况下，Controller 文件会被生成在项目根目录下的 `controller/` 文件夹内。你也可以通过在 `--gen-controller` 后跟随路径参数来指定生成位置：

```bash
npx gulux cg --type http-server --idl-root ./idl --main-idl main.thrift --gen-controller app/my_controller
```

一个典型的项目在执行生成命令后，其目录结构可能如下所示：

```plaintext
.
├── controller
│   ├── api
│   │   └── v1
│   │       ├── internal.ts
│   │       └── open.ts
│   └── home.ts
├── gulux_gen
│   ├── constant.ts
│   ├── index.ts
│   ├── middleware.ts
│   ├── types.ts
│   └── typings
│       ├── api
│       │   └── v1
│       │       ├── internal.ts
│       │       └── open.ts
│       └── main.ts
├── idl
│   ├── api
│   │   └── v1
│   │       ├── internal.thrift
│   │       └── open.thrift
│   └── main.thrift
└── package.json
```

**重要提示**：此生成命令是幂等的。当 IDL 接口签名更新后，可重复执行该命令。它只会更新方法签名和类型定义，而不会删除或覆盖你已经编写的业务逻辑代码。

## Controller 模板与填充

生成器会根据 IDL 中的 `service` 定义创建对应的 Controller 文件。例如，`open.thrift` 中的 `DemoOpenService` 会生成 `open.ts` 文件。

在填充业务逻辑时，请注意以下几点：

- **保留装饰器**: `@UseIdl()` 和 `@IdlArg('req')` 是连接 IDL 和业务逻辑的关键，请勿修改或删除它们。`@UseIdl` 负责将 HTTP 请求路由到正确的方法，`@IdlArg` 则用于注入经过校验和转换的请求参数。
- **方法签名**: 方法名（如 `GetRecord`）与 IDL 中的方法名保持一致。参数（如 `req: GetRecordRequest`）则直接使用从 `gulux_gen` 导入的类型。
- **返回 Response 实例**: 强烈建议在方法末尾返回对应 Response 类型（如 `GetRecordResponse`）的实例。这样做可以充分利用 GuluX 的能力，自动处理 `StatusCode`、`Header` 等映射。IDL 中未定义的字段将被自动过滤，确保响应的规范性。
- **添加业务逻辑**: 在 `// ...biz code` 注释处，你可以自由地注入依赖、调用其他服务、操作数据库，并最终构建 Response 对象返回。

```typescript
// controller/api/v1/open.ts
import { Controller } from '@gulux/gulux/application-http';
import { UseIdl, IdlArg } from '../../../gulux_gen/index'; // 路径根据实际情况调整
import {
  GetRecordRequest,
  GetRecordResponse,
  RecordItem, // 假设 RecordItem 也被导出
} from '../../../gulux_gen/typings/api/v1/open';

@Controller()
export default class DemoOpenController {
  @UseIdl()
  public async GetRecord(@IdlArg('req') req: GetRecordRequest) {
    // 示例：在这里添加你的业务逻辑
    console.log(`Fetching record with ID: ${req.Id}`);
    
    // 模拟数据查询
    const mockData: RecordItem[] = [
      { Name: 'gulux-user', Email: 'gulux@example.com' },
    ];

    // 返回 Response 类的实例
    return new GetRecordResponse({
      Data: mockData,
    });
  }
}
```

目前可以使用三种手段在 Controller 中获取参数：
```
// 1. 使用 IdlArg 装饰器获取特定参数（推荐）
public async index(@IdlArg('req') req: EmptyStruct, @IdlArg('otherArg') otherArg: OtherArgStruct) {
    console.log(req); // EmptyStruct
    console.log(otherArg); // OtherArgStruct
}
// 2. 使用 IdlArg 装饰器获取所有参数
public async index(@IdlArg() args: { req: EmptyStruct, otherArg: OtherArgStruct }) {
    console.log(args); // { req: EmptyStruct, otherArg: OtherArgStruct }
    console.log(args.req); // EmptyStruct
    console.log(args.otherArg); // OtherArgStruct
}
// 3. 从 Request 上取值（备用方案，不建议）
public async index(@Req() req: HTTPRequest<{ req: EmptyStruct, otherArg: OtherArgStruct }>) {
    console.log(req.args); // { req: EmptyStruct, otherArg: OtherArgStruct }
    console.log(req.args.req); // EmptyStruct
    console.log(req.args.otherArg); // OtherArgStruct
}
```

## 多文件模式

当项目接口复杂时，通常会将接口定义拆分到多个 `.thrift` 文件中。通过一个 `main.thrift` 入口文件 `include` 并 `extends` 这些 Service，可以实现模块化管理。

```thrift
// idl/main.thrift
include 'api/v1/open.thrift'
include 'api/v1/internal.thrift'

// 将不同文件中的 Service 继承到当前作用域
service DemoOpenService extends open.DemoOpenService {}
service DemoInternalService extends internal.DemoInternalService {}
```

运行 `--gen-controller` 命令后，GuluX 会为 `DemoOpenService` 和 `DemoInternalService` 分别在 `controller/api/v1/` 目录下生成 `open.ts` 和 `internal.ts`。我们建议 Controller 的目录结构与 IDL 的目录结构保持一致，以增强项目的可维护性。

## 复杂类型的 CLI 参数映射

Thrift IDL 中的某些类型（如 `i64`、`map`、`set`）在 TypeScript 中有多种表示方式。`gulux cg` 命令提供了参数来进行转换，以适应不同场景的需求：

- `--int64-as-string`: 将 `i64` 类型映射为 `string`。
- `--int64-as-number`: 将 `i64` 类型映射为 `number` (注意 JavaScript 的精度问题)。
- `--map-as-object`: 将 `map` 类型映射为 `object` (键值对)。
- `--set-as-array`: 将 `set` 类型映射为 `Array`。

在需要处理大整数或特定数据结构时，合理使用这些参数可以简化代码。

## 约束与注意事项

- **方法名唯一性**: 所有被合并到入口 IDL 的 Service 中，其方法名（Method Name）必须全局唯一。
- **Service 定义**: 建议在单个 IDL 文件（非入口文件）中只定义一个 Service，并且避免进行二次 `extends`，以防出现预料之外的行为。
- **代码风格**: 自动生成的代码可能与你的项目风格不符。可以在生成命令后，执行 `eslint --fix` 等 linting 工具来统一代码风格。
- **自定义生成路径**: 默认情况下，Controller 文件名与 IDL 文件名一致。你可以在 Service 定义上通过 `api.group` 注解来指定生成的文件路径。例如 `(api.group='common/health')` 会将该 Service 的 Controller 生成在 `controller/common/health.ts`。
- **路由前缀**: Thrift IDL 规范要求路径必须是全路径。GuluX 配置中的 `routerPrefix` 对 IDL 生成的路由无效。请在 IDL 的 `api.get/post` 等注解中提供完整的路由路径。

## 调试与验证

完成 Controller 代码填充后，你可以启动服务，并使用 `curl` 或其他 HTTP 客户端进行测试。

```bash
curl -X GET 'http://127.0.0.1:3000/api/v1/record?id=123'
```

- **GET 请求与复杂参数**: GuluX 遵循 HTTP 规范，不建议在 GET 请求的 QueryString 中传递复杂的嵌套对象或数组，因为这可能引发 HPP (HTTP Parameter Pollution) 攻击，且多数请求库对其处理方式不一。对于复杂查询，应优先使用 POST 请求和 JSON Body。

## 参考链接

- [ByteAPI IDL 规范](https://bytedance.feishu.cn/wiki/wikcn5e97r02eH8mLedtM8DaUkh)
- [GuluX 官方文档：通过 Thrift IDL 编写 HTTP Server](https://gulux.bytedance.net/best-practice/thrift-idl-http-server.html)
