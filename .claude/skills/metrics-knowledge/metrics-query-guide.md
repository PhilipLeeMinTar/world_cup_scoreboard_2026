# Metrics Golang SDK 查询数据指南

Metrics 提供了 Golang SDK 来通过调用 Metrics API 查询数据。本文档基于 [代码仓库](https://code.byted.org/inf/metrics-query) 的 README.md 文件示例，简要介绍如何查询数据。

## 前置条件

在使用 SDK 之前，请完成以下准备工作：

1. **设置 Golang 编译环境**：当前 SDK 版本与 Go 1.20 存在部分不兼容，建议选择兼容版本。
2. **熟悉 Metrics API 基本用法**：了解 Metrics 查询的基本概念和接口。
3. **申请目标环境配额**：详细操作请参考 [Metrics OpenAPI 用户指南](https://cloud.bytedance.net/docs/metrics/docs/63bbbb1ec6b537022a6000c7/63e4973d3d23a3021dfb5b4c)。

## 使用步骤

### 1. 初始化客户端

首先需要初始化查询客户端，指定应用名称和密钥：

```go
import "code.byted.org/inf/metrics-query/mq"

client, err := mq.NewClient("your_app_name", "your_secret")
if err != nil {
    // 处理错误
    panic(err.Error())
}
```

### 2. 构建查询指标

使用 SDK 提供的查询构建器创建查询：

```go
// 创建 QPS 查询
qpsQuery := mq.NewQuery(mq.AggregatorSum, "inf.bytetsd.queryproxy.request")

// 创建延迟查询  
latencyQuery := mq.NewQuery(mq.AggregatorAvg, "inf.bytetsd.queryproxy.request.cost.avg")
```

### 3. 执行查询

构建查询请求并执行：

```go
// 创建查询请求
result := client.NewRequest(mq.RegionBOE)
    .SetIntervalAgo(2 * time.Minute)
    .AddQueries(qpsQuery, latencyQuery)
    .DoWithContext(context.Background())

// 检查错误
if err := result.Err(); err != nil {
    // 处理查询错误
    log.Printf("查询失败: %v", err)
    return
}

// 处理查询结果
curves := result.All()
for _, curve := range curves {
    // 处理每个指标的数据
    fmt.Printf("指标: %s, 数据点数量: %d\n", curve.Name(), len(curve.Points()))
}
```

## SDK 架构原理

Metrics 查询 SDK 的整体架构如下图所示：

![Metrics 查询 SDK 整体结构图](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/d0a35bc9437c42c39f6fc8bf953ead24~tplv-tika-image.image)

### 核心组件

* **Config**：维护 Metrics 查询相关的各种元数据，提供具有扩展性的选项配置接口。
* **Query**：统一 Metrics 查询协议/语法，提供便于构建请求的枚举和方法。
* **HTTPClient**：根据 Config 做好准备，接收 Query 执行 HTTP 查询请求，并将返回数据统一转换为 CurveSet。
* **Cache**：缓存 HTTPClient 历史查询结果，加速重复请求的结果返回。
* **CurveSet**：作为 Client 的输出，为用户提供结构化的原始数据。
* **TimeSeries**：把 CurveSet 进一步转换为表格结构，在 DataAnalysis 中提供插值补点、复合指标运算和统计量计算。

## 配额管理

**重要提示**：Go SDK 默认一个指标一个请求，多个指标会占用多个配额。

```go
qpsQuery := mq.NewQuery(mq.AggregatorSum, "inf.bytetsd.queryproxy.request")
latencyQuery := mq.NewQuery(mq.AggregatorAvg, "inf.bytetsd.queryproxy.request.cost.avg")
// 实际会分别并发发起2次查询，占用2个查询配额
result := client.NewRequest(mq.RegionBOE).SetIntervalAgo(2*time.Minute).AddQueries(qpsQuery, latencyQuery).DoWithContext(context.Background())
```

## 常见问题

### 查询报 401 Authorization failure: token missing

**根本原因**：访问 QueryProxy 获取 token 失败。

**疑似原因**：查询**真实路由**的区域没有创建应用 APP_NAME。

### 报错 region inaccessible

错误信息示例：
```
_msg=Failed to query metrics 22, error=[DoWithContext] create request failed: [NewRequest] region "China-North" is inaccessible or unsupported due to its cluster "cn" is not configured
```

**原因分析**：查询使用控制面和 Region 不匹配。更多信息，见 [config.go](https://code.byted.org/inf/metrics-query/blob/master/internal/enum/config.go)。

### 使用 SDK 查询无数据

**排查方法**：SDK 打开 DEBUG，查看日志中真实的查询域名，使用 OpenAPI 测试域名。

## 高级配置

### 指定域名查询

例如，为本地调试指定办公网域名：

```go
client, err := mq.NewClient("your app_name", "your secret",
   WithEntry(mq.ClusterEUTTP, "http://openapi-metrics-euttp.tiktok-eu.org"),
   WithDebug(nil))
if err != nil {
   // 处理错误
   panic(err.Error())
}
```

## 项目地址

* 主仓库：https://code.byted.org/inf/metrics-query
* Rust SDK（个人封装）：https://crates.byted.org/crates/metrics-query

**说明**：更多语言的 SDK Metrics 团队正在开发中，支持后会及时进行更新说明。
