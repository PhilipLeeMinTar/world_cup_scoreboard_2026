# Hertz Client 简介

## 新建 Client

### 创建 Client

```go
import "code.byted.org/middleware/hertz/pkg/app/client"

func main() {
    c, err := client.NewClient()
    if err != nil {
        panic(err)
    }

    status, body, err := c.Get(context.Background(), nil, "http://example.com")
}
```

### 配置 Client

```go
c, err := client.NewClient(
    client.WithMaxConnDuration(10*time.Second),
    client.WithDialTimeout(5*time.Second),
    client.WithMaxIdleConnDuration(90*time.Second),
)
```

## 发送请求

### GET 请求

```go
status, body, err := c.Get(ctx, nil, "http://api.example.com/users")
if err != nil {
    return err
}

// 构建请求
req := &protocol.Request{}
req.SetRequestURI("http://api.example.com/users")
req.URI().QueryArgs().Add("page", "1")
req.URI().QueryArgs().Add("size", "10")

resp := &protocol.Response{}
err = c.Do(ctx, req, resp)
```

### POST 请求

```go
req := &protocol.Request{}
req.SetMethod("POST")
req.SetRequestURI("http://api.example.com/users")
req.Header.SetContentTypeBytes([]byte("application/json"))
req.SetBody([]byte(`{"name":"John","email":"john@example.com"}`))

resp := &protocol.Response{}
err := c.Do(ctx, req, resp)

// 处理响应
if resp.StatusCode() == 200 {
    body := resp.Body()
}
```

### 发起 JSON 请求

```go
type User struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

user := User{Name: "John", Email: "john@example.com"}
body, _ := json.Marshal(user)

req := &protocol.Request{}
req.SetMethod("POST")
req.SetRequestURI("http://api.example.com/users")
req.Header.SetContentTypeBytes([]byte("application/json"))
req.SetBody(body)

resp := &protocol.Response{}
c.Do(ctx, req, resp)
```

## 客户端配置

### 超时配置

```go
c, _ := client.NewClient(
    client.WithClientReadTimeout(30*time.Second),   // 读取response的最长时间
    client.WithDialTimeout(5*time.Second),          // 建立连接超时
)
```

### 重试配置

```go
import "code.byted.org/middleware/hertz/pkg/app/client/retry"

c, _ := client.NewClient()
c.Use(retry.New(
    retry.WithMaxAttemptTimes(3),
    retry.WithInitDelay(time.Second),
    retry.WithMaxDelay(5*time.Second),
))
```

### 连接池配置

```go
c, _ := client.NewClient(
    client.WithMaxConns(100),                       // 最大连接数
    client.WithMaxIdleConnDuration(90*time.Second), // 最大空闲连接时间
    client.WithMaxConnDuration(10*time.Minute),     // 最大连接持续时间
)
```

## 中间件

### 日志中间件

```go
func LoggingMiddleware(next client.Endpoint) client.Endpoint {
    return func(ctx context.Context, req *protocol.Request, resp *protocol.Response) error {
        start := time.Now()
        err := next(ctx, req, resp)
        hlog.CtxInfof(ctx, "request %s took %v", req.URI(), time.Since(start))
        return err
    }
}

c.Use(LoggingMiddleware)
```

### 认证中间件

```go
func AuthMiddleware(token string) client.Middleware {
    return func(next client.Endpoint) client.Endpoint {
        return func(ctx context.Context, req *protocol.Request, resp *protocol.Response) error {
            req.Header.Set("Authorization", "Bearer "+token)
            return next(ctx, req, resp)
        }
    }
}

c.Use(AuthMiddleware("your-token"))
```

## 负载均衡

### 服务发现

```go
import (
    "code.byted.org/middleware/hertz/pkg/app/client"
    "code.byted.org/middleware/hertz/pkg/app/client/loadbalance"
)

resolver := newConsulResolver() // 实现 Resolver

c, _ := client.NewClient(
    client.WithResolver(resolver),
    client.WithLoadBalancer(loadbalance.NewWeightedBalancer()),
)

// 服务发现
status, body, err := c.Get(ctx, nil, "http://user-service/api/users")
```

## 代理设置

```go
c, _ := client.NewClient(
    client.WithDialer(newProxyDialer("http://proxy:8080")),
)
```

## 相关文档

- [Hertz Client API 示例](https://bytedance.larkoffice.com/wiki/wikcnBeXb4AmGmhvjry4W4CguEb)
