# VikingDB SDK 使用指南 - viking_go_client

## 概述

**viking_go_client** 是字节跳动内部VikingDB向量数据库的Go语言客户端SDK，提供向量数据的写入、检索和管理能力。VikingDB是新一代向量化检索产品，采用存储与计算分离的架构，提供一站式的ANN（近似最近邻）/KNN（K最近邻）向量索引构建与检索服务。

**特性**：
- 支持向量相似度检索（文本、图片、视频、音频等多模态）
- 支持混合向量检索（稠密向量和稀疏向量）
- 支持结构化信息联合查询（ANN+DSL Filter）
- 提供多模态检索能力，整合文本、图片等多种数据类型

**代码包**：
- `code.byted.org/lagrange/viking_go_client`

## 适用场景

- **推荐、搜索、广告系统**：通过向量相似度检索实现个性化推荐和精准搜索
- **图片/音视频等多模态检索**：支持图像、音频、视频等非结构化数据的向量化检索
- **RAG（检索增强生成）应用**：为生成式AI提供相关文档检索能力
- **向量相似度搜索**：文本相似度、语义搜索等场景

## 定位对比

- **VikingDB vs 传统数据库**：VikingDB专注于向量数据的近似最近邻检索，而传统数据库擅长结构化数据的关系查询
- **VikingDB vs 其他向量数据库**：VikingDB采用存储与计算分离架构，支持大规模数据量和多模态检索

## 连接与初始化

### 配置项

VikingDB客户端初始化需要以下参数：
- `vikingdb_name`：向量库全名
- `token`：访问令牌
- `region`：区域（CN, CE, BOE, VA, SG, TTP, EU, JP等）

### 服务发现

VikingDB支持通过HTTP/RPC方式访问，也可通过VikingProxy进行RPC调用。

## 典型代码片段

### 初始化

```go
package vikingdb_go_example

import (
    VikingClient "code.byted.org/lagrange/viking_go_client"
)

var (
    VikingDbClient     *VikingClient.VikingDbClient
    VikingDbHerzClient *VikingClient.VikingDbHerzClient
)

// 使用向量库公共VikingDB server
func InitClient() *VikingClient.VikingDbClient {
    token := "29a29718af6cf6136fb7dab644741303"
    vikingdb_name := "tce_test_1713766902__example_for_sdk"
    vikingdb_client := VikingDbClient(vikingdb_name=vikingdb_name, token=token, region="CN")
    return vikingdb_client
}
```

### 数据写入

```go
func TestAdd(t *testing.T) {
    dataList := make([]*VikingDbData, 0)
    fvector := make([]float64, 64)
    for i := 0; i < 64; i++ {
        fvector[i] = 0.0
    }
    context := []string{"default"}
    dslInfo := make(map[string]interface{})
    dslInfo["test_bool"] = 0
    dslInfo["test_int64"] = 1
    dslInfo["test_float"] = 1.2
    dslInfo["test_string"] = "a"
    dslInfo["test_list_int64"] = []int{1, 2, 3}
    dslInfo["test_list_string"] = []string{"a", "b", "c"}
    
    data := NewVikingDbData(1000000000,
                            context,
                            fvector, 
                            WithLabelUppert(0), 
                            WithBias(0.0), 
                            WithAttrs("ok"), 
                            WithDslInfo(dslInfo), 
                            WithTtl(1000000000)) //ttl单位：秒； -1：不过期； 若不设置，则采用平台设置的默认ttl
    dataList = append(dataList, data)
    
    client := NewVikingDbWriterClient("tce_test_1661240600__wwk_test123", "e38bab2fceb3830a4500806aa61ae147", Region_CN)
    rowkeys, logID, err := client.AddData(dataList)
    assert.Equal(t, err, nil)
    fmt.Println("add_label:: ", rowkeys)
    fmt.Println("logID: ", logID)
    time.Sleep(3 * time.Second) //async write need wait
}
```

### 数据检索

```go
func TestGet(t *testing.T) {
    // This API is only for test and debug,
    // Donnot use in high frequency.
    client := NewVikingDbWriterClient("tce_test_1661240600__wwk_test123", "e38bab2fceb3830a4500806aa61ae147", Region_CN)
    labs := make([]*LabelLowerAndUpper, 0)
    lab := &LabelLowerAndUpper{
        LabelLower64: 1000000000,
        LabelUpper64: 0,
    }
    labs = append(labs, lab)
    dataInfo, err := client.GetData(labs)
    assert.Equal(t, err, nil)
    fmt.Println("data_info: ", dataInfo)
}
```

### 多模态检索

VikingDB支持多模态检索，可以同时处理文本和图片输入：

```go
client := NewVikingDbClient("tce_test_1753857620__test_multimodal_v4", "6227b536572d158fe9c4a70951e04d80", Region_CN)
// using raw embedding to get embedding
data := map[string]interface{}{
    "multimodal" : map[string]interface{} {
        "text": "Hello world",
        "image_url":"https://public-vikingdb-bucket-v2.tos-cn-north.byted.org/Fruit1.jpg",
        // "image_access_key":"xxx",
    },
}
rawData := NewRawData(data)
rawDatas := []*RawData{rawData}
embeddings, _, err := client.RawEmbedding(rawDatas)
assert.Equal(t, err, nil)

req := &RecallRequest{
    Embedding:        embeddings[0],
    Index:            "v1", //模型详情页对应的version字段值
    SubIndex:         "default",
    TopK:             10,
}
rsp, _, err := client.Recall(req)
assert.Equal(t, err, nil)
```

### 数据删除

```go
func TestDelete(t *testing.T) {
    client := NewVikingDbWriterClient("tce_test_1661240600__wwk_test123", "e38bab2fceb3830a4500806aa61ae147", Region_CN)
    labs := make([]*LabelLowerAndUpper, 0)
    lab := &LabelLowerAndUpper{
        LabelLower64: 1000000000,
        LabelUpper64: 0,
    }
    labs = append(labs, lab)
    rowkeys, logID, err := client.DeleteData(labs)
    assert.Equal(t, err, nil)
    fmt.Println("del_label:", rowkeys)
    fmt.Println("logid: ", logID)
}
```

## 向量化方法

VikingDB支持多种向量化方法，适用于不同场景：

### 文本向量化
- **base-bge-large-zh-v1.5-query-prefix**：中文向量化模型SOTA，兼容英文，自动为query文本添加前缀提升召回精度
- **doubao-embedding**：字节跳动研发的语义向量化模型，中英双语，支持最长4K上下文长度
- **doubao-embedding-0915**：doubao-embedding-large的text-240915版本

### 多模态向量化
- **doubao-embedding-vision_250615**：支持图片、文本多模态检索

## 常见坑与推荐写法

### 向量维度匹配
- 确保写入的向量维度与索引配置的维度一致
- 不同向量化方法产生的向量维度不同，需对应使用

### 异步写入等待
- VikingDB的写入是异步的，写入后需要等待几秒才能检索到数据
- 如示例中的`time.Sleep(3 * time.Second)`等待异步写入完成

### TTL设置
- TTL单位为秒，-1表示永不过期
- 若不设置TTL，则采用平台设置的默认TTL

### 高吞吐需求
- 如果业务方有高吞吐需求（QPS≥20），需要自行私有化部署向量化方法
- 低吞吐需求（QPS<20）可直接使用内置的向量化方法

## 相关文档

- [VikingDB User Manual | 向量数据库用户指南](https://bytedance.larkoffice.com/wiki/ZXadwaQnFi3z0fkkMjPcf7XSndg)
- [VikingDB 多模态检索文档](https://bytedance.larkoffice.com/docx/YtDqdAYQFoARvAxeWEbc1OU0nD8)
- [SDK 使用指南 | SDK User Guide](https://bytedance.larkoffice.com/wiki/S0HBwVwz8ie0NQkwhdTcsGvPnNb)
- [索引上线和在线请求接口 | Index Online Interface](https://bytedance.larkoffice.com/wiki/HRetw8w5NiDqDWkiVlIcwR6Kn3c)
- [在线服务如何请求 Viking/VikingProxy](https://bytedance.larkoffice.com/wiki/wikcnLzVU4eO5Egu9y6ofIhXped)
