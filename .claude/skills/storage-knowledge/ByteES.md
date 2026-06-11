# ByteES SDK 使用指南 - Golang Client SDK

## 概述

**ByteES Golang Client SDK** 是字节跳动内部基于 [Golang Olivere Elastic Client](https://github.com/olivere/elastic) 封装实现的 Elasticsearch 客户端，增加了服务发现、GDPR、HTTPS、全链路追踪、请求日志、Metric 打点、IPv4/IPv6 支持等功能，并完全兼容原有接口。

**特性**：
- 支持访问 v5, v6, v7 版本的 ES 集群（ByteES 平台主要使用 v7.1.1/v7.6.2/v7.10.2 版本）
- 支持 OpenSearch v2 版本（ByteES 平台主要使用 v2.9.0）
- 内置服务发现机制
- 全链路追踪支持
- 请求日志和监控指标打点

**代码包**：
- `code.byted.org/toutiao/elastic/v7@latest`（针对 OpenSearch 2.x 或 ES 7.x）
- `code.byted.org/toutiao/elastic/v6@latest`（针对 ES 6.x）
- `code.byted.org/toutiao/elastic/v5@latest`（针对 ES 5.x）

## 适用场景

- **全文检索类应用**：支持复杂的全文搜索需求，如商品搜索、内容搜索等
- **结构化查询需求**：支持精确查询、范围查询、聚合分析等结构化数据查询
- **时序（日志）类数据存储与分析**：适用于日志分析、监控数据存储等场景
- **POI类地理位置检索**：支持地理位置查询和空间分析
- **向量检索类应用**：支持向量相似度搜索
- **高安全性场景需求**：支持安全等级不同的集群访问

## 定位对比

- **与开源 Elasticsearch 对比**：ByteES 是基于开源的 Elasticsearch 进行改进开发的，所有 API 都与 Elasticsearch 相同。如果想知道 ByteES 是否支持某些操作，可以直接参考 Elasticsearch 的官方文档
- **与其他存储服务对比**：ByteES 专注于搜索和分析场景，与 RDS（关系型数据）、Redis（缓存）、TOS（对象存储）等形成互补

## 连接与初始化

ByteES Golang Client SDK 的初始化需要根据集群版本选择合适的 SDK 版本。

### 版本选择

根据要访问的集群版本选择对应的 Golang Client SDK（建议使用 go mod 编译）：

| 集群版本                 | 安装语句                                               |
| ------------------------ | ------------------------------------------------------ |
| OpenSearch 2.x 或 ES 7.x | `go get -v "code.byted.org/toutiao/elastic/v7@latest"` |
| ES 6.x                   | `go get -v "code.byted.org/toutiao/elastic/v6@latest"` |
| ES 5.x                   | `go get -v "code.byted.org/toutiao/elastic/v5@latest"` |

**重要说明**：针对 OpenSearch 2.x 或者 ES 7.x，请使用 v7.0.42及其以上版本。

### 集群安全等级识别

进入集群详情页，单击**基本信息**页签查看集群安全等级：
![集群安全等级查看](https://p9-arcosite.byteimg.com/tos-cn-i-goo7wpa0wc/560ec418e08241a8b31babba0f79335b~tplv-goo7wpa0wc-image.image)

## 典型代码片段

### 初始化

```go
package main

import (
    "context"
    "code.byted.org/toutiao/elastic/v7"
)

// NewByteESClient 创建并返回一个 ByteES Client 实例
func NewByteESClient() (*elastic.Client, error) {
    // 初始化客户端
    client, err := elastic.NewClient(
        elastic.SetURL("http://your-bytees-endpoint:9200"),
        elastic.SetSniff(false), // ByteES 环境下建议关闭 sniff
        elastic.SetHealthcheck(false),
    )
    if err != nil {
        return nil, err
    }
    
    return client, nil
}
```

### 基本查询操作

```go
package search

import (
    "context"
    "fmt"
    "code.byted.org/toutiao/elastic/v7"
)

type ProductSearch struct {
    client *elastic.Client
}

func NewProductSearch(client *elastic.Client) *ProductSearch {
    return &ProductSearch{client: client}
}

// SearchProducts 搜索产品信息
func (s *ProductSearch) SearchProducts(ctx context.Context, keyword string, from, size int) ([]map[string]interface{}, error) {
    // 构建查询
    query := elastic.NewMatchQuery("name", keyword)
    
    searchResult, err := s.client.Search().
        Index("products").
        Query(query).
        From(from).
        Size(size).
        Do(ctx)
    
    if err != nil {
        return nil, err
    }
    
    var results []map[string]interface{}
    for _, hit := range searchResult.Hits.Hits {
        var product map[string]interface{}
        if err := hit.Unmarshal(&product); err != nil {
            continue
        }
        results = append(results, product)
    }
    
    return results, nil
}
```

### 带 search_pipeline 的查询

根据 [Golang SDK使用教程](https://cloud.bytedance.net/docs/ses/docs/6614e634c6a2250303cdeb04/661c9697ead05d031b5e411c?x-resource-account=public&x-bc-region-id=bytedance) 创建 client：

```go
// cli为初始化的客户端

// query为查询DSL
query := `{"_source":"content","query":{"remote_neural":{"content_knn":{"query_text":"What is the capital of US?","k":10}}}}`

options := elastic.PerformRequestOptions{
    Method: "GET",
    Path:   "/<your_index_name>/_search",
    // Params中为search_pipeline
    Params: url.Values{
       "search_pipeline": []string{"<your_search_pipeline_id>"},
    },
    Body: query,
}

response, err := cli.PerformRequest(context.Background(), options)
if err != nil {
    // 错误处理
}
```

### 聚合查询示例

```go
// AggregateProductSales 聚合产品销售额
func (s *ProductSearch) AggregateProductSales(ctx context.Context, startTime, endTime string) (map[string]float64, error) {
    // 时间范围查询
    rangeQuery := elastic.NewRangeQuery("sale_time").
        Gte(startTime).
        Lte(endTime)
    
    // 按产品类别聚合
    aggregation := elastic.NewTermsAggregation().Field("category")
    salesAgg := elastic.NewSumAggregation().Field("sales_amount")
    aggregation.SubAggregation("total_sales", salesAgg)
    
    searchResult, err := s.client.Search().
        Index("sales_records").
        Query(rangeQuery).
        Aggregation("categories", aggregation).
        Size(0). // 不需要返回具体文档
        Do(ctx)
    
    if err != nil {
        return nil, err
    }
    
    agg, found := searchResult.Aggregations.Terms("categories")
    if !found {
        return nil, fmt.Errorf("aggregation not found")
    }
    
    result := make(map[string]float64)
    for _, bucket := range agg.Buckets {
        salesAgg, found := bucket.Aggregations.Sum("total_sales")
        if found && salesAgg.Value != nil {
            result[bucket.Key.(string)] = *salesAgg.Value
        }
    }
    
    return result, nil
}
```

## 常见坑与推荐写法

### SDK 版本管控

**重要提醒**：升级 SDK 建议业务方一定要做好测试验证和灰度的工作。针对早期 SDK 版本（<= v7.0.37），即使下游无实例情况下，初始化 client 不会抛出异常；后续版本（>v7.0.37，除了 v7.0.54）会检查下游是否存在实例，不存在则返回 err。

### 查询性能优化

- **避免使用 `_id` 字段排序或聚合查询**：内置 `_id` 字段缺少 docvalue 索引，针对 `_id` 字段的排序或者聚合查询时，ES 需要在内存中构建全局序数，并且占用集群内存不释放，存在实例 OOM 风险，影响集群稳定性
- **谨慎使用 Script 查询**：Script 查询无法利用提前构建的索引结构，需要运行时判断是否满足查询，如果 Script 查询命中候选集很大，执行效率较低且耗 CPU
- **Scroll 查询限制**：默认情况下，Scroll 查询上下文数量上限为 500

### 集群访问规范

- **不要通过 `_cat/nodes` api 获取 es 节点**
- **查询速度受多种因素影响**：集群索引多少、查询目标索引大小、分片数大小、并发/请求的多少、网络抖动等因素都会影响查询速度。一般简单查询在 1s 以内，复杂查询很难评估

### 错误处理

```go
// 推荐写法：详细的错误处理和重试机制
func (s *ProductSearch) SafeSearch(ctx context.Context, query elastic.Query) (*elastic.SearchResult, error) {
    var lastErr error
    
    // 重试机制
    for i := 0; i < 3; i++ {
        result, err := s.client.Search().
            Index("products").
            Query(query).
            Do(ctx)
        
        if err == nil {
            return result, nil
        }
        
        lastErr = err
        
        // 根据错误类型决定是否重试
        if isRetryableError(err) {
            time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
            continue
        }
        
        // 非重试错误直接返回
        return nil, err
    }
    
    return nil, fmt.Errorf("search failed after retries: %v", lastErr)
}
```

## 相关文档

- [Golang Client SDK 使用教程](https://cloud.bytedance.net/docs/ses/docs/6614e634c6a2250303cdeb04/661c9697ead05d031b5e411c?x-resource-account=public&x-bc-region-id=bytedance)
- [ByteES GO SDK v7版本管控升级](https://bytedance.larkoffice.com/docx/Z4A1dVFbLoWkfxxE7MUcLgjFnce)
- [Golang Client SDK 发布记录](https://cloud.bytedance.net/docs/ses/docs/6614e634c6a2250303cdeb04/668f494f99cc6202f1be2497?x-resource-account=public)
- [ByteES 使用规约](https://bytedance.larkoffice.com/wiki/BJiLwNmkBivGvXkr3V1cvHDPn96)
- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Olivere Elastic Client GitHub](https://github.com/olivere/elastic)

**重要提示**：因社区 ES Client SDK 以及依赖的公司内部上下游组件的快速迭代发展，以及各语言版本众多，加之 ByteES 人力异常紧张，可能会没法及时同步和验证社区和上下游组件的一些更新，故而强烈建议业务方一定要做好测试验证和灰度的工作。
