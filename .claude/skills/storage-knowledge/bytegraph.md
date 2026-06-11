# ByteGraph SDK 使用指南 - bytegraph_gremlin_go

## 概述

**bytegraph_gremlin_go** 是字节跳动内部使用的 ByteGraph 图数据库 Go 客户端 SDK，它提供了对 ByteGraph 分布式图数据存储系统的访问能力，支持 Gremlin 图查询语言，集成了服务发现、监控、鉴权等内部特性。

**特性**：
- 支持 Gremlin 图查询语言，图灵完备的查询能力
- 支持参数绑定模式，提高查询性能和安全性
- 集成公司内部鉴权机制（GDPR/ZTI）
- 支持多种数据类型的绑定和映射

**代码包**：
- `code.byted.org/inf/bytegraph_gremlin_go/driver`
- `code.byted.org/inf/bytegraph_gremlin_go/structure`

## 适用场景

- **图结构数据存储和查询**：适用于需要存储和查询复杂关系数据的场景
- **多跳关系查询需求**：支持一度和多度的图查询，适合社交网络、推荐系统等场景
- **知识图谱构建**：适用于构建和查询知识图谱、实体关系图等应用
- **实时推荐系统**：支持实时图计算和关系分析

## 定位对比

- **与传统关系数据库对比**：ByteGraph 专门为图结构数据设计，在多跳查询、关系分析方面性能更优
- **与其他图数据库对比**：ByteGraph 是字节自研的分布式图数据库，与公司内部基础设施深度集成

## 连接与初始化

ByteGraph SDK 的初始化需要指定服务 PSM 和默认表名，并支持超时设置等配置选项。

### 配置项

- **PSM**：ByteGraph 服务的唯一标识，格式为 `bytegraph.{subsystem}.{module}`
- **DefaultTable**：默认查询的表名
- **Timeout**：查询超时时间设置

### 服务发现

ByteGraph SDK 通过 PSM 自动进行服务发现，无需手动配置服务地址。

### 鉴权配置

访问开启鉴权的 ByteGraph 集群时，需要配置鉴权。ByteGraph 支持 GDPR 或 ZTI 鉴权环境，TCE 类环境会自动注入 GDPR Token，无需手动处理。

## 典型代码片段

### 初始化

```go
package main

import (
    "context"
    "fmt"
    "time"
    "code.byted.org/inf/bytegraph_gremlin_go/driver"
    "code.byted.org/inf/bytegraph_gremlin_go/structure"
)

func main() {
    // 连接服务psm，创建一个线程安全GraphTraversal
    conn, err := driver.NewClient("bytegraph.gremlin.test",
            driver.WithDefaultTable("online"),
            driver.WithTimeout(time.Second*30))
    if err != nil {
        panic(err)
    }
    defer conn.Close()
    
    // 创建图遍历生成器
    g := driver.NewGraphTraversal()
}
```

### 基本查询操作

```go
// 参数绑定模式查询示例
func queryWithParameterBinding(ctx context.Context, conn *driver.Client) {
    // 创建参数绑定占位符
    ph := driver.NewPlaceHolder
    
    // 构建参数化查询模板
    query := g.V().Has("type", ph("type")).Has("id", ph("id"))
    
    // 绑定参数并执行查询
    params := map[string]interface{}{
        "type": 1,
        "id":   1113,
    }
    
    result, err := conn.Submit(ctx, query, params)
    if err != nil {
        panic(err)
    }
    
    // 处理查询结果
    var vertices []structure.Vertex
    if err := result.Read(&vertices); err != nil {
        panic(err)
    }
}
```

### 多跳关系查询

```go
// 查询某个人的认识的人（的属性）
func queryOneHopRelations(ctx context.Context, conn *driver.Client) {
    query := g.V().Has('id', 1).Has('type', 1).Out('knows').Project('fri').By(properties())
    
    result, err := conn.Submit(ctx, query, nil)
    if err != nil {
        panic(err)
    }
    
    // 结果类型为 List<Map>
    var results []map[string][]structure.Property
    if err := result.Read(&results); err != nil {
        panic(err)
    }
}
```

### 复杂查询示例

```go
// 查询某个人的姓名、认识的人、开发的软件以及认识的人数
func complexQueryExample(ctx context.Context, conn *driver.Client) {
    query := g.V().Has("type", 1).Has("id", 1).
        Project("my_name", "person", "software", "knows_count").
        By(__.Values("name")).
        By(__.Out("knows").Local(__.Properties().Fold())).
        By(__.Out("created").Properties()).
        By(__.Out("knows").Count())
    
    result, err := conn.Submit(ctx, query, nil)
    if err != nil {
        panic(err)
    }
    
    // 结果类型为 List<Map>
    var results []map[string]interface{}
    if err := result.Read(&results); err != nil {
        panic(err)
    }
}
```

## 常见坑与推荐写法

### 鉴权配置顺序

**重要**：操作顺序很关键，首先要将要访问数据库的 client 都添加授权，然后再开启鉴权。先开启鉴权会导致所有请求都挂掉。

### SDK 版本兼容性

- 使用 Gremlin 访问时，建议将 SDK 升级到最新版本
- Go SDK 需要 v1.1.73 及以上版本支持完整功能
- 某些高级功能（如 group step）需要特定版本支持

### 查询性能优化

- 使用参数绑定模式可以提高查询性能和安全性
- 避免在查询中硬编码值，使用参数绑定
- 合理设计图数据模型，避免过度复杂的查询

### 错误处理

```go
func safeQuery(ctx context.Context, conn *driver.Client, query string) (interface{}, error) {
    result, err := conn.Submit(ctx, query, nil)
    if err != nil {
        // 记录错误日志
        log.Printf("ByteGraph query failed: %v", err)
        return nil, err
    }
    
    // 设置合理的超时时间
    ctxWithTimeout, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    // 处理结果
    var data interface{}
    if err := result.ReadWithContext(ctxWithTimeout, &data); err != nil {
        return nil, err
    }
    
    return data, nil
}
```

## 相关文档

- [ByteGraph 平台](https://cloud.bytedance.net/bytegraph/clusters) - ByteGraph 管理控制台
- [Gremlin 快速入门](https://cloud.bytedance.net/docs/bytegraph/docs/63d76a4dbd6ec6022478cafd/63d9dba4bd6ec602247e18c0) - Gremlin 查询语言入门指南
- [配置 ByteGraph 鉴权](https://cloud.bytedance.net/docs/bytegraph/docs/63d76a4dbd6ec6022478cafd/63d9e0197df7d2021d0155ec) - 鉴权配置详细指南
- [ByteGraph Oncall](https://oncall.bytedance.net/chats/user/dialog?tenant=281) - 技术支持联系方式
