# IDL 注解 - 基础

## 注解概览

Hertztool 支持在 Thrift 和 Protobuf IDL 中使用注解来定义 HTTP 路由、参数绑定、验证规则等。

### 注解分类

| 类型 | 注解 | 说明 |
|------|------|------|
| **Field 注解** | api.query | 生成 "query" tag |
| | api.path | 生成 "path" tag |
| | api.header | 生成 "header" tag |
| | api.cookie | 生成 "cookie" tag |
| | api.body | 生成 "json" "form" tag |
| | api.form | 生成 "form" tag |
| | api.raw_body | 生成 "raw_body" tag |
| | api.vd | 生成 "vd" tag（验证） |
| | api.go_tag / go.tag | 透传自定义 go tag |
| **Method 注解** | api.get/post/put/delete/patch/options/head/any | 定义 HTTP 方法及路由 |
| | api.handler_path | 指定 handler 生成路径 |
| **Service 注解** | api.base_domain | 生成 client 代码时访问的域名 |

**注意**：Field 注解中，除了 `api.body`，都会默认生成一个 "json" tag。

## HTTP 方法注解

### api.get

定义 GET 请求路由。

**Thrift:**
```thrift
service UserService {
    GetUserResponse GetUser(1: GetUserRequest req) (api.get="/api/user")
}
```

**Protobuf:**
```protobuf
service UserService {
    rpc GetUser(GetUserRequest) returns (GetUserResponse) {
        option (api.get) = "/api/user";
    }
}
```

### api.post

定义 POST 请求路由。

**Thrift:**
```thrift
service UserService {
    CreateUserResponse CreateUser(1: CreateUserRequest req) (api.post="/api/user")
}
```

**Protobuf:**
```protobuf
service UserService {
    rpc CreateUser(CreateUserRequest) returns (CreateUserResponse) {
        option (api.post) = "/api/user";
    }
}
```

### api.put / api.delete / api.patch

类似 GET/POST,用于其他 HTTP 方法。

```thrift
UpdateUserResponse UpdateUser(1: UpdateUserRequest req) (api.put="/api/user/:id")
DeleteUserResponse DeleteUser(1: DeleteUserRequest req) (api.delete="/api/user/:id")
PatchUserResponse PatchUser(1: PatchUserRequest req) (api.patch="/api/user/:id")
```

### api.options / api.head / api.any

其他 HTTP 方法支持。

**Thrift:**
```thrift
service UserService {
    // OPTIONS 请求
    OptionsResponse Options(1: OptionsRequest req) (api.options="/api/user")
    // HEAD 请求
    HeadResponse Head(1: HeadRequest req) (api.head="/api/user/:id")
    // ANY - 匹配所有 HTTP 方法
    AnyResponse Any(1: AnyRequest req) (api.any="/api/fallback")
}
```

**Protobuf:**
```protobuf
service UserService {
    rpc Options(OptionsRequest) returns (OptionsResponse) {
        option (api.options) = "/api/user";
    }
    rpc Head(HeadRequest) returns (HeadResponse) {
        option (api.head) = "/api/user/:id";
    }
    rpc Any(AnyRequest) returns (AnyResponse) {
        option (api.any) = "/api/fallback";
    }
}
```

### api.handler_path

指定 handler 生成的位置，相对于 handler_dir。

**Thrift:**
```thrift
service Demo {
    Resp Method(1: Req request) (
        api.get="/route",
        api.handler_path="foo/bar"  // handler 生成路径为 biz/handler/foo/bar/*.go
    );
}
```

**Protobuf:**
```protobuf
service Demo {
    rpc Method(Req) returns(Resp) {
        option (api.get) = "/route";
        option (api.handler_path) = "foo/bar";  // handler 生成路径为 biz/handler/foo/bar/*.go
    }
}
```

默认为空字符串，handler 生成在 `biz/handler` 下。

## 参数绑定注解

### api.query

绑定 URL 查询参数 (`?key=value`)。

**Thrift:**
```thrift
struct GetUserRequest {
    1: required i64 id (api.query="id")
    2: optional string name (api.query="name")
}
```

**Protobuf:**
```protobuf
message GetUserRequest {
    int64 id = 1; // @query
    string name = 2; // @query
}
```

**生成的 HTTP 请求:**
```
GET /api/user?id=123&name=John
```

### api.path

绑定路径参数 (`:id`, `:name`)。

**Thrift:**
```thrift
struct GetUserRequest {
    1: required i64 id (api.path="id")
}

service UserService {
    GetUserResponse GetUser(1: GetUserRequest req) (api.get="/api/user/:id")
}
```

**Protobuf:**
```protobuf
message GetUserRequest {
    int64 id = 1; // @path
}
```

**生成的 HTTP 请求:**
```
GET /api/user/123
```

### api.body

绑定请求体 (JSON/Form)。

**Thrift:**
```thrift
struct CreateUserRequest {
    1: required string name (api.body="name")
    2: required string email (api.body="email")
}
```

**Protobuf:**
```protobuf
message CreateUserRequest {
    string name = 1; // @body
    string email = 2; // @body
}
```

**生成的 HTTP 请求:**
```
POST /api/user
Content-Type: application/json

{
  "name": "John",
  "email": "john@example.com"
}
```

### api.form

绑定表单参数 (`application/x-www-form-urlencoded`)。

**Thrift:**
```thrift
struct LoginRequest {
    1: required string username (api.form="username")
    2: required string password (api.form="password")
}
```

**Protobuf:**
```protobuf
message LoginRequest {
    string username = 1; // @form
    string password = 2; // @form
}
```

**生成的 HTTP 请求:**
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=123456
```

### api.header

绑定 HTTP Header。

**Thrift:**
```thrift
struct GetUserRequest {
    1: required string authorization (api.header="Authorization")
    2: optional string user_agent (api.header="User-Agent")
}
```

**Protobuf:**
```protobuf
message GetUserRequest {
    string authorization = 1; // @header=Authorization
    string user_agent = 2; // @header=User-Agent
}
```

### api.cookie

绑定 Cookie 值。

**Thrift:**
```thrift
struct GetUserRequest {
    1: required string session_id (api.cookie="session_id")
}
```

**Protobuf:**
```protobuf
message GetUserRequest {
    string session_id = 1; // @cookie=session_id
}
```

### api.raw_body

绑定原始请求体 (string/[]byte)。

**Thrift:**
```thrift
struct UploadRequest {
    1: required binary content (api.raw_body="content")
}
```

**Protobuf:**
```protobuf
message UploadRequest {
    bytes content = 1; // @raw_body
}
```

### api.go_tag / go.tag

透传自定义 Go tag，会生成 go_tag 里定义的内容。

**Thrift:**
```thrift
struct Demo {
    1: string Demo (api.query="demo", api.path="demo");
    2: string GoTag (go.tag="goTag:\"tag\"")  // Thrift 使用 go.tag
    3: string Vd (api.vd="$!='your string'")
}
```

**Protobuf:**
```protobuf
message Demo {
    string Demo = 1[(api.query)="demo",(api.path)="demo"];
    string GoTag = 2[(api.go_tag)="goTag:\"tag\""];  // Protobuf 使用 api.go_tag
    string Vd = 3[(api.vd)="$!='your string'"];
}
```

**生成的 Go 代码示例:**
```go
type Demo struct {
    Demo  string `query:"demo" path:"demo" json:"Demo"`
    GoTag string `goTag:"tag" json:"GoTag"`
    Vd    string `vd:"$!='your string'" json:"Vd"`
}
```

### api.file_name

绑定文件上传。

**Thrift:**
```thrift
struct UploadRequest {
    1: required binary file (api.form="file", api.file_name="file")
}
```

## 验证注解

### api.vd

使用 validator 进行参数验证。

**Thrift:**
```thrift
struct CreateUserRequest {
    1: required string name (api.vd="len($)>0 && len($)<50")
    2: required string email (api.vd="email($)")
    3: required i32 age (api.vd="$>0 && $<150")
}
```

**Protobuf:**
```protobuf
message CreateUserRequest {
    string name = 1; // @vd="len($)>0 && len($)<50"
    string email = 2; // @vd="email($)"
    int32 age = 3; // @vd="$>0 && $<150"
}
```

### 常用验证表达式

| 表达式 | 说明 | 示例 |
|--------|------|------|
| `len($)>0` | 长度大于 0 | 必填字符串 |
| `len($)>=6 && len($)<=20` | 长度范围 | 密码长度 |
| `$>0` | 大于 0 | 正整数 |
| `$>=1 && $<=100` | 数值范围 | 分数 |
| `$>=0.0` | 非负浮点数 | 价格 |
| `email($)` | 邮箱格式 | 邮箱验证 |
| `regexp('^[a-zA-Z0-9]+$')` | 正则匹配 | 字母数字 |
| `len($)==11 && regexp('^1[3-9]\\d{9}$')` | 中国手机号 | 手机号验证 |
| `in($, ['pending', 'active', 'done'])` | 枚举值 | 状态值验证 |

## 路由注解

### api.base_path

设置路由分组的基础路径。

**Thrift:**
```thrift
service UserService {
    GetUserResponse GetUser(1: GetUserRequest req) (
        api.get="/user/:id",
        api.base_path="/api/v1"
    )
}
```

生成路由: `/api/v1/user/:id`

**生成的路由代码:**
```go
v1 := h.Group("/api/v1")
{
    v1.GET("/user/:id", handler.GetUser)
}
```

### api.serializer

指定序列化器 (默认 JSON)。

**Thrift:**
```thrift
service UserService {
    GetUserResponse GetUser(1: GetUserRequest req) (
        api.get="/api/user",
        api.serializer="json"  // json, thrift, protobuf
    )
}
```

## Service 注解

### api.base_domain

生成 client 代码时要访问的域名。

**Thrift:**
```thrift
service HelloService {
    Resp FormMethod(1: FormReq request) (api.post="/form", api.handler_path="post");
}(
    api.base_domain="http://127.0.0.1:8888";
)
```

**Protobuf:**
```protobuf
service HelloService {
    rpc FormMethod(FormReq) returns(Resp) {
        option (api.post) = "/form";
        option (api.handler_path) = "post";
    }
    option (api.base_domain) = "http://127.0.0.1:8888";
}
```

生成的 client 代码会默认使用这个域名作为请求目标。

## 注意事项

### Thrift 注解语法

1. **使用括号:** `(api.get="/path")`
2. **多个注解用逗号分隔:** `(api.query="id", api.vd="$>0")`
3. **字符串值需要引号:** `api.query="name"`

### Protobuf 注解语法

1. **使用注释:** `// @query` 或 `// @query=name`
2. **使用 option:** `option (api.get) = "/path";`
3. **字段级注解放在注释中:** `int64 id = 1; // @path`

### 路径参数规则

1. **必须在路由中定义:** `api.get="/user/:id"` 且字段有 `api.path="id"`
2. **参数名必须匹配:** 路由中的 `:id` 对应 `api.path="id"`
3. **支持多个参数:** `/user/:uid/post/:pid`

### 验证表达式规则

1. **使用 `$` 表示当前字段值**
2. **逻辑运算符:** `&&` (与), `||` (或), `!` (非)
3. **比较运算符:** `>`, `<`, `>=`, `<=`, `==`, `!=`
4. **函数调用:** `len($)`, `email($)`, `regexp(pattern)`

### 常见错误

**错误 1: 路径参数未定义**
```thrift
// ❌ 错误
struct Request {
    1: required i64 id (api.query="id")  // 应该是 api.path
}
service API {
    Response Get(1: Request req) (api.get="/user/:id")
}
```

**错误 2: 验证表达式语法错误**
```thrift
// ❌ 错误
1: required string name (api.vd="len(name)>0")  // 应该用 $

// ✅ 正确
1: required string name (api.vd="len($)>0")
```
