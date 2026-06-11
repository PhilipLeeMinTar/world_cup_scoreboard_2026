# IDL 注解 - 高级用法

## Go Tag 注解

### go.tag

透传 Go struct tag。

**Thrift:**
```thrift
struct User {
    1: required i64 id (go.tag="json:\"id\" bson:\"_id,omitempty\"")
    2: required string name (go.tag="json:\"name\" validate:\"required,min=2,max=50\"")
    3: optional string email (go.tag="json:\"email,omitempty\" validate:\"email\"")
}
```

**生成的 Go 代码:**
```go
type User struct {
    ID    int64  `thrift:"id,1,required" json:"id" bson:"_id,omitempty"`
    Name  string `thrift:"name,2,required" json:"name" validate:"required,min=2,max=50"`
    Email string `thrift:"email,3,optional" json:"email,omitempty" validate:"email"`
}
```

**Protobuf:**
```protobuf
message User {
    int64 id = 1; // @gotag: json:"id" bson:"_id,omitempty"
    string name = 2; // @gotag: json:"name" validate:"required,min=2,max=50"
    string email = 3; // @gotag: json:"email,omitempty" validate:"email"
}
```

### 常用 Go Tag

**JSON 标签:**
```thrift
1: required string name (go.tag="json:\"name,omitempty\"")  // 零值时省略
```

**BSON 标签 (MongoDB):**
```thrift
1: required i64 id (go.tag="bson:\"_id\"")
```

**Validate 标签:**
```thrift
1: required string email (go.tag="validate:\"required,email\"")
```

**组合使用:**
```thrift
1: required string name (go.tag="json:\"name\" bson:\"name\" validate:\"required,min=2\"")
```

**注意事项:**
```thrift
// ❌ 错误: 引号冲突
1: required string name (go.tag="json:"name"")

// ✅ 正确: 转义引号
1: required string name (go.tag="json:\"name\"")
```

## 文件级注解

### go_package (Protobuf)

指定生成 Go 代码的包路径。

```protobuf
syntax = "proto3";

package api;

option go_package = "code.byted.org/namespace/projectName/biz/model/api";
```

### namespace (Thrift)

指定命名空间 (Go 包名)。

```thrift
namespace go api
namespace java com.example.api
namespace py api
```

## 复杂验证示例

### 数组长度验证

```thrift
struct BatchRequest {
    1: required list<i64> ids (api.vd="len($)>0 && len($)<=100")
}
```

### 嵌套字段验证

```thrift
struct Address {
    1: required string street (api.vd="len($)>0")
    2: required string city (api.vd="len($)>0")
}

struct CreateUserRequest {
    1: required string name (api.vd="len($)>0")
    2: required Address address
}
```

### 条件验证

```thrift
struct UpdateUserRequest {
    1: required i64 id (api.vd="$>0")
    2: optional string email (api.vd="len($)==0 || email($)")  // 空或有效邮箱
}
```

## 完整示例

### RESTful CRUD API

```thrift
namespace go api

struct User {
    1: required i64 id (go.tag="json:\"id\"")
    2: required string name (go.tag="json:\"name\" validate:\"required,min=2\"")
    3: required string email (go.tag="json:\"email\" validate:\"required,email\"")
    4: optional i32 age (go.tag="json:\"age,omitempty\" validate:\"gte=0,lte=150\"")
    5: optional string avatar (go.tag="json:\"avatar,omitempty\"")
}

struct GetUserRequest {
    1: required i64 id (api.path="id", api.vd="$>0")
}

struct GetUserResponse {
    1: required User user
}

struct ListUsersRequest {
    1: optional i32 page (api.query="page", api.vd="$>0")
    2: optional i32 page_size (api.query="page_size", api.vd="$>0 && $<=100")
    3: optional string keyword (api.query="keyword")
}

struct ListUsersResponse {
    1: required list<User> users
    2: required i32 total
    3: required i32 page
    4: required i32 page_size
}

struct CreateUserRequest {
    1: required string name (api.body="name", api.vd="len($)>0 && len($)<50")
    2: required string email (api.body="email", api.vd="email($)")
    3: optional i32 age (api.body="age", api.vd="$>=0 && $<=150")
}

struct CreateUserResponse {
    1: required User user
}

struct UpdateUserRequest {
    1: required i64 id (api.path="id", api.vd="$>0")
    2: optional string name (api.body="name", api.vd="len($)==0 || (len($)>0 && len($)<50)")
    3: optional string email (api.body="email", api.vd="len($)==0 || email($)")
    4: optional i32 age (api.body="age", api.vd="$>=0 && $<=150")
}

struct UpdateUserResponse {
    1: required User user
}

struct DeleteUserRequest {
    1: required i64 id (api.path="id", api.vd="$>0")
}

struct DeleteUserResponse {
    1: required bool success
}

service UserService {
    // 获取单个用户
    GetUserResponse GetUser(1: GetUserRequest req) (
        api.get="/user/:id",
        api.base_path="/api/v1"
    )

    // 列出用户
    ListUsersResponse ListUsers(1: ListUsersRequest req) (
        api.get="/users",
        api.base_path="/api/v1"
    )

    // 创建用户
    CreateUserResponse CreateUser(1: CreateUserRequest req) (
        api.post="/user",
        api.base_path="/api/v1"
    )

    // 更新用户
    UpdateUserResponse UpdateUser(1: UpdateUserRequest req) (
        api.put="/user/:id",
        api.base_path="/api/v1"
    )

    // 删除用户
    DeleteUserResponse DeleteUser(1: DeleteUserRequest req) (
        api.delete="/user/:id",
        api.base_path="/api/v1"
    )
}
```

### 文件上传示例

```thrift
struct UploadRequest {
    1: required binary file (api.form="file", api.file_name="file")
    2: optional string description (api.form="description")
}

struct UploadResponse {
    1: required string file_url
    2: required i64 file_size
}

service FileService {
    UploadResponse Upload(1: UploadRequest req) (
        api.post="/upload",
        api.base_path="/api/v1"
    )
}
```

### 认证头示例

```thrift
struct AuthRequest {
    1: required string token (api.header="Authorization", api.vd="len($)>0")
    2: required i64 user_id (api.path="user_id", api.vd="$>0")
}

struct GetProfileResponse {
    1: required User user
}

service UserService {
    GetProfileResponse GetProfile(1: AuthRequest req) (
        api.get="/user/:user_id/profile",
        api.base_path="/api/v1"
    )
}
```

### 复杂查询示例

```thrift
struct SearchRequest {
    1: optional string keyword (api.query="keyword")
    2: optional string category (api.query="category")
    3: optional i64 min_price (api.query="min_price", api.vd="$>=0")
    4: optional i64 max_price (api.query="max_price", api.vd="$>=0")
    5: optional string sort_by (api.query="sort_by", api.vd="in($, ['price', 'name', 'date'])")
    6: optional string order (api.query="order", api.vd="in($, ['asc', 'desc'])")
    7: optional i32 page (api.query="page", api.vd="$>0")
    8: optional i32 page_size (api.query="page_size", api.vd="$>0 && $<=100")
}

struct SearchResponse {
    1: required list<Product> products
    2: required i32 total
}

service ProductService {
    SearchResponse Search(1: SearchRequest req) (
        api.get="/search",
        api.base_path="/api/v1"
    )
}
```
