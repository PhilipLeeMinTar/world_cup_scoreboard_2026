# Hertztool 完整示例

## 项目创建与代码生成完整流程

### 1. 创建项目

```bash
# 创建项目目录
mkdir -p $GOPATH/src/code.byted.org/namespace/projectName
cd $GOPATH/src/code.byted.org/namespace/projectName

# 初始化项目
hertztool new --psm=p.s.m --mod=code.byted.org/namespace/projectName
```

### 2. 编写 IDL

创建 `idl/user.thrift`:

```thrift
namespace go user

struct User {
    1: required i64 id (go.tag="json:\"id\"")
    2: required string name (go.tag="json:\"name\"")
    3: optional string email (go.tag="json:\"email,omitempty\"")
}

struct GetUserRequest {
    1: required i64 id (api.path="id")
}

struct GetUserResponse {
    1: required User user
}

struct ListUsersRequest {
    1: optional i32 page (api.query="page", api.vd="$>0")
    2: optional i32 page_size (api.query="page_size", api.vd="$>0 && $<=100")
}

struct ListUsersResponse {
    1: required list<User> users
    2: required i32 total
}

struct CreateUserRequest {
    1: required string name (api.body="name", api.vd="len($)>0 && len($)<50")
    2: required string email (api.body="email", api.vd="email($)")
}

struct CreateUserResponse {
    1: required User user
}

service UserService {
    GetUserResponse GetUser(1: GetUserRequest req) (
        api.get="/user/:id",
        api.base_path="/api/v1"
    )

    ListUsersResponse ListUsers(1: ListUsersRequest req) (
        api.get="/users",
        api.base_path="/api/v1"
    )

    CreateUserResponse CreateUser(1: CreateUserRequest req) (
        api.post="/user",
        api.base_path="/api/v1"
    )
}
```

### 3. 生成代码

```bash
hertztool update -idl idl/user.thrift --mod=code.byted.org/namespace/projectName --insert
```

### 4. 实现业务逻辑

编辑 `biz/handler/user.go`:

```go
func GetUser(ctx context.Context, c *app.RequestContext) {
    var req user.GetUserRequest
    err := c.BindAndValidate(&req)
    if err != nil {
        c.JSON(400, map[string]string{"error": err.Error()})
        return
    }

    // 从数据库获取用户
    u, err := db.GetUserByID(ctx, req.Id)
    if err != nil {
        c.JSON(500, map[string]string{"error": err.Error()})
        return
    }

    resp := &user.GetUserResponse{User: u}
    c.JSON(200, resp)
}
```

### 5. 运行服务

```bash
go run main.go
```

### 6. 测试接口

```bash
# 获取用户
curl http://localhost:8888/api/v1/user/123

# 列出用户
curl "http://localhost:8888/api/v1/users?page=1&page_size=10"

# 创建用户
curl -X POST http://localhost:8888/api/v1/user \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@example.com"}'
```
