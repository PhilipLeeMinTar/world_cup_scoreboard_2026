# 协议支持

## TLS/HTTPS

### 启用 TLS

```go
import (
    "crypto/tls"
    "code.byted.org/middleware/hertz/byted"
    "code.byted.org/middleware/hertz/pkg/app/server"
)

func main() {
    // 方式 1: 使用证书文件
    h := byted.Default(
        server.WithHostPorts("0.0.0.0:8443"),
        server.WithTLS(&tls.Config{}),
    )

    h.Spin()
}
```

### TLS 配置选项

```go
tlsConfig := &tls.Config{
    // 最低 TLS 版本
    MinVersion: tls.VersionTLS12,

    // 支持的密码套件
    CipherSuites: []uint16{
        tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
    },

    // 客户端证书验证
    ClientAuth: tls.RequireAndVerifyClientCert,
    ClientCAs: clientCAPool,
}

h := byted.Default(
    server.WithTLS(tlsConfig),
)
```

### 使用证书文件

```go
h := byted.Default()

// 从文件加载证书
h.RunTLS(
    ":8443",
    "path/to/cert.pem",
    "path/to/key.pem",
)
```

### 双向 TLS (mTLS)

```go
// 创建客户端 CA 池
clientCAPool := x509.NewCertPool()
clientCACert, _ := ioutil.ReadFile("client-ca.pem")
clientCAPool.AppendCertsFromPEM(clientCACert)

tlsConfig := &tls.Config{
    ClientAuth: tls.RequireAndVerifyClientCert,
    ClientCAs: clientCAPool,
}

h := byted.Default(server.WithTLS(tlsConfig))
```

## HTTP/2

### 启用 HTTP/2

HTTP/2 在启用 TLS 时自动支持，使用 ALPN 协商。

```go
import (
    "crypto/tls"
    "code.byted.org/middleware/hertz/byted"
    "code.byted.org/middleware/hertz/pkg/app/server"
)

func main() {
    h := byted.Default(
        server.WithTLS(&tls.Config{
            MinVersion: tls.VersionTLS12,
        }),
        server.WithALPN(true),  // 启用 ALPN
    )

    h.Spin()
}
```

### HTTP/2 配置

```go
h := byted.Default(
    server.WithTLS(&tls.Config{}),
    server.WithALPN(true),
    server.WithMaxRequestBodySize(4 * 1024 * 1024),  // 4MB
)
```

### 检测协议版本

```go
func handler(c context.Context, ctx *app.RequestContext) {
    protocol := string(ctx.Request.Header.Protocol())

    if protocol == "HTTP/2.0" {
        // HTTP/2 请求
    } else {
        // HTTP/1.1 请求
    }

    ctx.JSON(200, map[string]string{"protocol": protocol})
}
```

## WebSocket

Hertz 支持 WebSocket 协议，提供双向通信能力。

### 基础使用

```go
import (
    "context"
    "code.byted.org/middleware/hertz/byted"
    "code.byted.org/middleware/hertz/pkg/app"
    "code.byted.org/middleware/hertz/pkg/app/server"
    "github.com/hertz-contrib/websocket"
)

func main() {
    h := byted.Default()

    // WebSocket 升级器
    upgrader := websocket.HertzUpgrader{
        CheckOrigin: func(ctx *app.RequestContext) bool {
            return true  // 允许所有来源
        },
    }

    h.GET("/ws", func(c context.Context, ctx *app.RequestContext) {
        err := upgrader.Upgrade(ctx, func(conn *websocket.Conn) {
            // WebSocket 连接建立后的处理
            for {
                mt, message, err := conn.ReadMessage()
                if err != nil {
                    break
                }

                // 回显消息
                conn.WriteMessage(mt, message)
            }
        })

        if err != nil {
            ctx.String(500, "WebSocket upgrade failed")
        }
    })

    h.Spin()
}
```

### WebSocket 配置

```go
upgrader := websocket.HertzUpgrader{
    // 读缓冲大小
    ReadBufferSize: 1024,

    // 写缓冲大小
    WriteBufferSize: 1024,

    // 检查来源
    CheckOrigin: func(ctx *app.RequestContext) bool {
        origin := string(ctx.Request.Header.Peek("Origin"))
        return origin == "https://example.com"
    },

    // 启用压缩
    EnableCompression: true,
}
```

### WebSocket 消息类型

```go
const (
    TextMessage   = 1  // 文本消息
    BinaryMessage = 2  // 二进制消息
    CloseMessage  = 8  // 关闭连接
    PingMessage   = 9  // Ping
    PongMessage   = 10 // Pong
)

// 发送文本消息
conn.WriteMessage(websocket.TextMessage, []byte("Hello"))

// 发送二进制消息
conn.WriteMessage(websocket.BinaryMessage, data)

// 发送 JSON
conn.WriteJSON(map[string]string{"type": "message"})
```

### WebSocket 心跳

```go
import "time"

func wsHandler(conn *websocket.Conn) {
    // 设置读超时
    conn.SetReadDeadline(time.Now().Add(60 * time.Second))

    // Pong handler
    conn.SetPongHandler(func(string) error {
        conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        return nil
    })

    // 发送心跳
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    go func() {
        for range ticker.C {
            if err := conn.WriteMessage(websocket.PingMessage, nil); err != nil {
                return
            }
        }
    }()

    // 处理消息
    for {
        _, message, err := conn.ReadMessage()
        if err != nil {
            break
        }

        // 处理消息
        handleMessage(message)
    }
}
```

### WebSocket 房间管理

```go
type Room struct {
    clients map[*websocket.Conn]bool
    mu      sync.RWMutex
}

func (r *Room) Join(conn *websocket.Conn) {
    r.mu.Lock()
    r.clients[conn] = true
    r.mu.Unlock()
}

func (r *Room) Leave(conn *websocket.Conn) {
    r.mu.Lock()
    delete(r.clients, conn)
    r.mu.Unlock()
    conn.Close()
}

func (r *Room) Broadcast(message []byte) {
    r.mu.RLock()
    defer r.mu.RUnlock()

    for conn := range r.clients {
        conn.WriteMessage(websocket.TextMessage, message)
    }
}
```

### 完整示例

```go
package main

import (
    "context"
    "log"
    "sync"

    "code.byted.org/middleware/hertz/byted"
    "code.byted.org/middleware/hertz/pkg/app"
    "github.com/hertz-contrib/websocket"
)

type Hub struct {
    clients    map[*websocket.Conn]bool
    broadcast  chan []byte
    register   chan *websocket.Conn
    unregister chan *websocket.Conn
    mu         sync.RWMutex
}

func NewHub() *Hub {
    return &Hub{
        clients:    make(map[*websocket.Conn]bool),
        broadcast:  make(chan []byte),
        register:   make(chan *websocket.Conn),
        unregister: make(chan *websocket.Conn),
    }
}

func (h *Hub) Run() {
    for {
        select {
        case conn := <-h.register:
            h.mu.Lock()
            h.clients[conn] = true
            h.mu.Unlock()

        case conn := <-h.unregister:
            h.mu.Lock()
            if _, ok := h.clients[conn]; ok {
                delete(h.clients, conn)
                conn.Close()
            }
            h.mu.Unlock()

        case message := <-h.broadcast:
            h.mu.RLock()
            for conn := range h.clients {
                err := conn.WriteMessage(websocket.TextMessage, message)
                if err != nil {
                    conn.Close()
                    delete(h.clients, conn)
                }
            }
            h.mu.RUnlock()
        }
    }
}

func main() {
    hub := NewHub()
    go hub.Run()

    h := byted.Default()

    upgrader := websocket.HertzUpgrader{
        CheckOrigin: func(ctx *app.RequestContext) bool {
            return true
        },
    }

    h.GET("/ws", func(c context.Context, ctx *app.RequestContext) {
        err := upgrader.Upgrade(ctx, func(conn *websocket.Conn) {
            hub.register <- conn
            defer func() {
                hub.unregister <- conn
            }()

            for {
                _, message, err := conn.ReadMessage()
                if err != nil {
                    break
                }

                hub.broadcast <- message
            }
        })

        if err != nil {
            log.Println("WebSocket upgrade failed:", err)
        }
    })

    h.Spin()
}
```
