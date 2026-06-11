# Kitex Streaming

## 概述

Streaming 支持双向流式通信,适用于:
- 大文件传输
- 实时数据推送
- 长时间连接

## 基本用法

### IDL 定义

```thrift
service StreamService {
    // 服务端流式
    stream<Response> ServerStream(1: Request req)

    // 客户端流式
    Response ClientStream(1: stream<Request> reqs)

    // 双向流式
    stream<Response> BidiStream(1: stream<Request> reqs)
}
```

### Server 端实现

```go
func (s *StreamServiceImpl) ServerStream(req *Request, stream StreamService_ServerStreamServer) error {
    for i := 0; i < 10; i++ {
        resp := &Response{Data: fmt.Sprintf("message %d", i)}
        if err := stream.Send(resp); err != nil {
            return err
        }
    }
    return nil
}
```

### Client 端调用

```go
stream, err := cli.ServerStream(ctx, req)
if err != nil {
    return err
}

for {
    resp, err := stream.Recv()
    if err == io.EOF {
        break
    }
    if err != nil {
        return err
    }
    log.Println(resp.Data)
}
```

## 双向流式

```go
stream, err := cli.BidiStream(ctx)

// 发送
go func() {
    for i := 0; i < 5; i++ {
        req := &Request{Data: fmt.Sprintf("req %d", i)}
        stream.Send(req)
    }
    stream.CloseSend()
}()

// 接收
for {
    resp, err := stream.Recv()
    if err == io.EOF {
        break
    }
    log.Println(resp.Data)
}
```

## 注意事项

- 记得关闭流: `stream.Close()`
- 处理 EOF 错误
- 注意goroutine泄漏

## 相关文档

- [连接池调优](./tune-connection-pool.md)
- [超时配置](./configure-timeout.md)
