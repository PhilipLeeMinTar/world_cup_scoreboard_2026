# Bytedoc (MongoDB) SDK 使用指南 - mongo-go-driver

## 概述

**Bytedoc** 是字节跳动内部基于 **MongoDB** 深度定制的文档数据库服务。它使用 BSON (二进制 JSON) 格式存储灵活的、半结构化的文档，非常适合快速迭代的业务和复杂数据模型的场景。

Go 语言访问 Bytedoc 主要使用内部封装版的 **mongo-go-driver**。该驱动在官方驱动的基础上，集成了字节的服务发现 (Consul)、Token 认证、监控、压测染色等内部生态能力。

**特性**：
- 基于官方 mongo-go-driver 封装
- 集成 Consul 服务发现和 Token 认证
- 支持 BSON 文档存储
- 支持多文档 ACID 事务
- 支持聚合管道和二级索引

**代码包**：
- `code.byted.org/bytedoc/mongo-go-driver/mongo`
- `code.byted.org/bytedoc/mongo-go-driver/bson`
- `code.byted.org/bytedoc/mongo-go-driver/mongo/options`

## 适用场景

- **内容管理**: 存储文章、评论、用户信息等具有复杂或多变结构的数据。
- **产品目录**: 管理商品信息，每个商品的属性可能都不同。
- **配置中心**: 存储服务的动态配置。
- **游戏数据**: 存储玩家档案、装备、游戏状态等。
- **物联网 (IoT)**: 存储来自设备的海量、多样化的数据。

## 定位对比

- 与 **RDS (MySQL)** 相比，Bytedoc 的 Schema-on-Read 模型提供了极大的灵活性，不需要预先定义严格的表结构，但关系查询和强事务能力弱于 RDS。
- 与 **Redis** 相比，Bytedoc 是持久化的文档存储，支持二级索引和复杂的聚合查询，而 Redis 主要用于高性能内存缓存和简单数据结构操作。
- 与 **ABase** 相比，Bytedoc 的文档模型更适合存储自然的、嵌套的 JSON/BSON 对象，而 ABase 的宽列模型更适合大规模、相对扁平的结构化数据。

## 连接与初始化

通过一个特殊的 URI 来配置和初始化 `mongo.Client`，该 URI 封装了服务发现和认证的逻辑。

### 连接 URI

格式通常为 `mongodb+consul+token://{psm}/{dbName}?{options}`：
- `mongodb+consul+token`: 指定了使用 Consul 进行服务发现和 Token 进行认证。
- `{psm}`: Bytedoc 服务的 PSM 标识。
- `{dbName}`: 默认的数据库名。
- `{options}`: 连接参数，如超时时间。

### 客户端单例

`mongo.Client` 是并发安全的，应在服务启动时创建一次，并在整个应用生命周期中复用。客户端内部维护了到集群各节点的连接池。

### 连接池配置

- `SetMinPoolSize`: 最小连接池大小。
- `SetMaxPoolSize`: 最大连接池大小，默认 `100`。
- `SetMaxConnIdleTime`: 连接最大空闲时间。

### 超时配置

- `SetConnectTimeout`: 建立连接的超时时间。
- `SetSocketTimeout`: TCP socket 的读写超时。
- **操作级超时**: 每次操作都应使用 `context.WithTimeout` 来控制其执行时间。

### Read Preference & Write Concern

- **Read Preference**: 控制读操作从哪个节点执行（主节点、从节点等），可实现读写分离。例如 `readpref.SecondaryPreferred()`。
- **Write Concern**: 控制写操作的确认级别，例如 `writeconcern.W(majority)` 保证写入到大多数节点后才返回。

## 生命周期管理

- **启动**: 在服务启动时，调用 `mongo.Connect()` 创建客户端，并用 `client.Ping()` 验证连接。
- **健康检查**: 可以定期调用 `client.Ping()` 来检查与数据库集群的连通性。
- **关闭**: 在服务优雅退出时，调用 `client.Disconnect()` 来关闭所有连接，释放资源。

## 典型代码片段

### 初始化

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "code.byted.org/bytedoc/mongo-go-driver/mongo"
    "code.byted.org/bytedoc/mongo-go-driver/mongo/options"
    "code.byted.org/bytedoc/mongo-go-driver/mongo/readpref"
)

// NewBytedocClient 创建并返回一个 Bytedoc 客户端实例
func NewBytedocClient(psm, dbName string) (*mongo.Client, error) {
    // 内部 URI 格式，集成了服务发现和认证
    uri := fmt.Sprintf("mongodb+consul+token://%s/%s?connectTimeoutMS=5000&socketTimeoutMS=10000", psm, dbName)

    clientOptions := options.Client().
        ApplyURI(uri).
        SetMaxPoolSize(100). // 设置连接池最大连接数
        SetMaxConnIdleTime(10 * time.Minute) // 设置连接最大空闲时间

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    client, err := mongo.Connect(ctx, clientOptions)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to bytedoc: %w", err)
    }

    // Ping a primary node to verify that the connection was successful.
    if err := client.Ping(ctx, readpref.Primary()); err != nil {
        return nil, fmt.Errorf("failed to ping bytedoc: %w", err)
    }

    return client, nil
}

func main() {
    bytedocPSM := "bytedance.bytedoc.your_service"
    dbName := "your_db"

    client, err := NewBytedocClient(bytedocPSM, dbName)
    if err != nil {
        log.Fatalf("bytedoc client initialization failed: %v", err)
    }

    // 在服务退出时断开连接
    // defer client.Disconnect(context.Background())

    fmt.Println("Bytedoc client initialized successfully.")

    // 在这里执行业务逻辑...
}
```

### 基本 CRUD

```go
package repository

import (
    "context"
    "time"

    "code.byted.org/bytedoc/mongo-go-driver/bson"
    "code.byted.org/bytedoc/mongo-go-driver/bson/primitive"
    "code.byted.org/bytedoc/mongo-go-driver/mongo"
    "code.byted.org/bytedoc/mongo-go-driver/mongo/options"
)

// Article 定义了文档模型
type Article struct {
    ID        primitive.ObjectID `bson:"_id,omitempty"`
    Title     string             `bson:"title"`
    Content   string             `bson:"content"`
    AuthorID  int64              `bson:"author_id"`
    Tags      []string           `bson:"tags"`
    CreatedAt time.Time          `bson:"created_at"`
}

type ArticleRepository struct {
    collection *mongo.Collection
}

func NewArticleRepository(db *mongo.Database, collectionName string) *ArticleRepository {
    return &ArticleRepository{collection: db.Collection(collectionName)}
}

// CreateArticle 插入一篇文章
func (r *ArticleRepository) CreateArticle(ctx context.Context, article *Article) (primitive.ObjectID, error) {
    article.ID = primitive.NewObjectID() // 生成新的 ObjectID
    article.CreatedAt = time.Now()
    _, err := r.collection.InsertOne(ctx, article)
    return article.ID, err
}

// FindArticleByID 根据 ID 查询文章
func (r *ArticleRepository) FindArticleByID(ctx context.Context, id primitive.ObjectID) (*Article, error) {
    var article Article
    filter := bson.M{"_id": id}
    err := r.collection.FindOne(ctx, filter).Decode(&article)
    if err == mongo.ErrNoDocuments {
        return nil, nil // 业务上通常将"未找到"作为正常情况处理
    }
    return &article, err
}

// UpdateArticleTitle 更新文章标题
func (r *ArticleRepository) UpdateArticleTitle(ctx context.Context, id primitive.ObjectID, newTitle string) (int64, error) {
    filter := bson.M{"_id": id}
    update := bson.M{"$set": bson.M{"title": newTitle}}

    result, err := r.collection.UpdateOne(ctx, filter, update)
    if err != nil {
        return 0, err
    }
    return result.ModifiedCount, nil
}

// FindArticlesByTag 分页查询包含特定标签的文章
func (r *ArticleRepository) FindArticlesByTag(ctx context.Context, tag string, page, limit int64) ([]*Article, error) {
    var articles []*Article
    filter := bson.M{"tags": tag}

    findOptions := options.Find().
        SetSort(bson.D{{Key: "created_at", Value: -1}}). // 按创建时间降序
        SetSkip((page - 1) * limit).
        SetLimit(limit)

    cursor, err := r.collection.Find(ctx, filter, findOptions)
    if err != nil {
        return nil, err
    }
    defer cursor.Close(ctx)

    if err := cursor.All(ctx, &articles); err != nil {
        return nil, err
    }
    return articles, nil
}
```

### 事务

Bytedoc (MongoDB) 支持多文档 ACID 事务，但需要副本集或分片集群。

```go
func (s *ArticleService) CreateArticleAndIncrAuthorCount(ctx context.Context, article *Article) error {
    // Start a session for the transaction
    session, err := s.client.StartSession()
    if err != nil {
        return err
    }
    defer session.EndSession(ctx)

    // Transaction logic
    callback := func(sessCtx mongo.SessionContext) (interface{}, error) {
        // 1. Insert the article
        if _, err := s.articleRepo.Collection().InsertOne(sessCtx, article); err != nil {
            return nil, err
        }

        // 2. Increment the author's article count in the 'authors' collection
        authorFilter := bson.M{"_id": article.AuthorID}
        authorUpdate := bson.M{"$inc": bson.M{"article_count": 1}}
        if _, err := s.authorRepo.Collection().UpdateOne(sessCtx, authorFilter, authorUpdate); err != nil {
            return nil, err
        }

        return nil, nil
    }

    // Run the transaction
    _, err = session.WithTransaction(ctx, callback)
    return err
}
```

## 常见坑与推荐写法

### Schema 设计

虽然 Bytedoc 是 schema-less 的，但一个好的、相对一致的 schema 设计对性能和可维护性至关重要。避免过度深层的嵌套。

### 索引是关键

- **必须建索引**: 任何用于查询、排序的字段都应该建立索引。没有索引的查询在大数据量下会扫描整个集合，导致性能灾难。
- **复合索引**: 当查询涉及多个字段时，创建复合索引。索引字段的顺序非常重要，应遵循"**等值、排序、范围**"的顺序。
- **覆盖索引**: 如果一个索引包含了查询需要返回的所有字段，那么 MongoDB 可以只从索引中获取数据，而无需访问文档，这被称为覆盖索引，性能极高。

### 分页

避免使用 `skip` 进行深分页，其性能会随着 `skip` 值的增大而线性下降。推荐使用基于范围查询或 seek-method 的分页，例如 `db.collection.find({"_id": {"$gt": lastID}}).limit(pageSize)`。

### BSON 与 Struct 映射

- 使用 `bson` 标签来明确指定 Go struct 字段与 BSON 文档字段的映射关系，如 `bson:"_id,omitempty"`。`omitempty` 表示当字段为零值时，序列化时忽略该字段。
- `_id` 字段推荐使用 `primitive.ObjectID` 类型，它可以自动生成，并天然包含时间戳信息，利于排序。

### 避免大文档

单个 BSON 文档最大为 16MB。应避免设计超大文档，可以将大数组或大块二进制数据拆分到单独的集合或对象存储中。

### 原子操作

善用 `$inc`、`$push`、`$addToSet` 等原子操作符，它们可以避免"读-改-写"模式带来的竞态条件。

## 配置清单

### 连接 URI 参数

`mongodb+consul+token://{psm}/{dbName}?connectTimeoutMS=5000&socketTimeoutMS=10000&maxPoolSize=200`

| 参数               | 推荐区间/示例值     | 说明                                                         |
| ------------------ | ------------------- | ------------------------------------------------------------ |
| `psm`              | `...`               | Bytedoc 服务 PSM。                                           |
| `dbName`           | `...`               | 默认数据库名。                                               |
| `connectTimeoutMS` | `5000`              | 建立连接的超时时间（毫秒）。                                 |
| `socketTimeoutMS`  | `10000`             | Socket 读写超时时间（毫秒）。                                |
| `maxPoolSize`      | `100`-`500`         | 客户端到每个 server 的最大连接数。                           |
| `minPoolSize`      | `0`-`10`            | 最小连接数。                                                 |
| `maxIdleTimeMS`    | `600000` (10分钟)   | 连接在池中保持空闲的最长时间。                               |
| `readPreference`   | `secondaryPreferred`| 读偏好设置，`secondaryPreferred` 可实现读写分离。            |
| `w`                | `majority`          | 写确认级别，`majority` 保证数据写入到大多数节点。            |

### 命名规范

- **数据库/集合名**:
  - 使用小写字母、数字，单词间可用下划线 `_` 分隔。
  - 集合名使用复数形式，如 `articles`。
  - 推荐使用环境前缀，如 `dev_articles`。
- **字段名**:
  - 使用驼峰式命名法 (camelCase) 或下划线法 (snake_case)，并保持项目内统一。例如 `createdAt` 或 `created_at`。

### 序列化

- 驱动程序自动处理 Go `struct` 与 BSON 之间的转换。
- 对性能敏感的场景，可以通过实现 `bson.Marshaler` 和 `bson.Unmarshaler` 接口来自定义序列化逻辑。
- 对于时间类型，确保使用 `time.Time`，驱动会正确地将其序列化为 BSON UTC datetime。

## 示例 Prompt

- "请使用 mongo-go-driver 帮我实现一个功能：查找 `users` 集合中 `age` 大于 30 且拥有 `vip` 标签的所有用户，并按 `registration_date` 倒序排序。"
- "如何为我的 `products` 集合创建一个复合索引来优化对 `category` 和 `price` 字段的查询？请提供 Go 代码示例。"
- "我需要在一个事务中完成两个操作：在 `orders` 集合中插入一个新订单，并更新 `inventory` 集合中对应商品的库存。请展示如何使用 mongo-go-driver 实现。"
- "请解释 MongoDB 中的 '覆盖索引' 是什么，并给出一个能利用覆盖索引的查询示例。"
- "我的 Go 服务连接 Bytedoc 出现性能瓶颈，如何通过配置 `readPreference` 实现读写分离来优化查询性能？"

## 相关文档

- [MongoDB 官方文档](https://www.mongodb.com/docs/)
- [mongo-go-driver 官方文档](https://pkg.go.dev/go.mongodb.org/mongo-driver)
