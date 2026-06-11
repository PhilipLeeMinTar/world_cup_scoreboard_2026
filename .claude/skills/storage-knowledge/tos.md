# TOS (Object Storage) SDK 使用指南

## 概述

**TOS (Tinder Object Storage)** 是字节跳动内部的对象存储服务，提供海量、安全、低成本、高可靠的云存储服务。TOS Go SDK 提供了对 TOS 服务的访问能力。

**SDK 地址**：`code.byted.org/gopkg/tos`

## 适用场景

- **海量非结构化数据存储**: 图片、音视频、日志文件等。
- **数据备份与归档**: 长期保存的历史数据。
- **大数据分析**: 作为大数据平台的底层存储。
- **静态网站托管**: 托管静态网页资源。

## 定位对比

- 与 **RDS (MySQL)** 相比，TOS 适合存储大文件和非结构化数据，不支持复杂的 SQL 查询和事务。
- 与 **Redis** 相比，TOS 提供低成本的持久化存储，读写延迟高于内存数据库，不适合高频小 IO 访问。
- 与 **HDFS** 相比，TOS 提供 HTTP RESTful 接口，更适合互联网应用访问。

## 安装

需要 Golang 1.16 及以上版本。

```bash
go get -u code.byted.org/gopkg/tos
```

## 连接与初始化

初始化 TOS Client 是使用服务的第一步。**强烈建议优先通过服务发现方式创建 Client**，以避免内网域名的带宽限制（默认 5MB/s）。

### 关键配置

- **WithBucket (必选)**: 指定要访问的存储桶名称。
- **WithCredentials (必选)**: 配置鉴权信息（AccessKey/SecretKey）。
- **WithServiceName (可选)**: 服务发现名称，默认为 `toutiao.tos.tosapi`。
- **WithRemotePSM (可选)**: 调用方的 PSM，用于鉴权和统计。

### 初始化示例 (推荐：服务发现)

```go
package main

import (
    "fmt"
    "os"
    "code.byted.org/gopkg/tos"
)

func main() {
    // 初始化 TOS Client
    // 注意：CN 的 BOE 环境需使用"个人密钥"；其他环境使用 Bucket Key
    client, err := tos.NewTos(
        // 1. 指定 Bucket 名称 (必选)
        tos.WithBucket("your-bucket-name"),
        
        // 2. 配置鉴权信息 (必选)
        tos.WithCredentials(&tos.BucketAccessKeyCredentials{
            BucketName: "your-bucket-name",
            AccessKey:  "your-access-key",
            // SecretKey: "your-secret-key", // BOE 环境或使用个人密钥时必填
        }),
        
        // 3. 配置调用方 PSM (可选，推荐)
        tos.WithRemotePSM("your.caller.psm"),
        
        // 4. 服务发现配置 (可选，使用默认值通常即可)
        // tos.WithServiceName("toutiao.tos.tosapi"), 
    )

    if err != nil {
        fmt.Println("Error:", err)
        os.Exit(-1)
    }
    
    fmt.Printf("Create TOS client success: %+v\n", client)
}
```

## 常见坑与最佳实践

### 1. 超时设置 (Context 复用问题)

**严禁复用旧的 Context**。
TOS SDK 的请求默认超时时间为 10s。业务侧应为每个请求创建一个新的 `context.WithTimeout`。

- **错误**: 多个请求复用同一个 `context`，导致后续请求的剩余超时时间极短。
- **正确**:
  ```go
  ctx := context.Background()
  // 为每个操作设置独立的超时
  ctx, cancel := context.WithTimeout(ctx, 60*time.Second)
  defer cancel()
  
  // 调用接口
  // client.PutObjectV2(ctx, ...)
  ```

### 2. 内网限速

- **现象**: 通过 Endpoint (域名) 方式访问 TOS，速度被限制在 5MB/s。
- **原因**: TOS 内网域名默认有 5MB/s 的访问限速，且不可调大。
- **解决**: **优先使用服务发现** (`tos.NewTos` 时不指定 `WithEndpoint`，或显式指定 `WithServiceName`)，服务发现的限流阈值跟随 Bucket 的配置。

### 3. 鉴权配置

- **线上环境**: 推荐使用 Bucket 专用密钥 (只需 AccessKey)。
- **BOE 环境**: 必须使用个人密钥 (需 AccessKey 和 SecretKey)。

## 常用接口

- **上传对象**: `PutObject` / `PutObjectV2`
- **下载对象**: `GetObject` / `GetObjectV2`
- **拷贝对象**: `CopyObject`
- **列举对象**: `ListObjects`
- **删除对象**: `DeleteObject`

详细接口定义请参考官方文档或代码注释。

## 配置清单

| 参数 | 说明 | 示例 |
| :--- | :--- | :--- |
| `WithBucket` | **必选**。访问的桶名。 | `tostest` |
| `WithCredentials` | **必选**。鉴权凭证。 | `&tos.BucketAccessKeyCredentials{...}` |
| `WithServiceName` | 可选。服务发现名称。 | `toutiao.tos.tosapi` (默认) |
| `WithRegion` | 可选。地域信息。 | `bj` |
| `WithEndpoint` | 可选。直接指定域名（不推荐，有内网限速）。 | `tos-cn-north.byted.org` |
| `WithEnableCRC` | 可选。开启 CRC 校验。 | `true` (默认) |

## 相关文档

- [TOS Go SDK 用户手册](https://cloud.bytedance.net/docs/tos/docs/64db3bc855f10602a14c81dc/64e5e57faf85cf029a2fe0b7)
- [TOS 产品文档](https://cloud.bytedance.net/product/tos)
