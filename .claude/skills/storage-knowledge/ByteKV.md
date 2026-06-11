# ByteKV SDK 使用指南 - Go

## 概述

**ByteKV** 是字节跳动内部自研的分布式事务性键值数据库，提供强一致性保证。Go SDK 在官方 `bytekv` 包的基础上进行了封装，集成了服务发现 (Consul)、监控、熔断等内部特性，为业务提供了开箱即用的强一致性存储访问能力。

**特性**：
- **强一致性**：通过自研的 ByteRaft 实现可容错的多副本强一致性
- **全局有序**：基于 range 分区，支持有序扫描和前缀扫描
- **高可用**：数据多副本，只要多数派副本可用，系统即可正常读写
- **高可扩展**：基于 range 分区实现平滑扩容，TPS 和 QPS 随扩容线性扩展
- **低延迟**：单机房读写 PCT99 延时为毫秒级，跨机房为十毫秒级
- **大容量**：单集群支持 TB～PB 级别存储容量，1000 万 TPS

**代码包**：
- `code.byted.org/gopkg/bytekv`

## 适用场景

- **金融数据管理**：如抖音红包等需要强一致性的金融业务
- **元数据管理**：文件目录、文件元信息等元数据存储
- **高数据一致性要求的场景**：需要保证数据强一致性的业务场景
- **需要多Key更新原子性的场景**：需要保证多个Key同时更新要么全部成功要么全部失败的场景

## 定位对比

- **vs Redis**：ByteKV 提供强一致性保证，适合对数据一致性要求高的场景；Redis 适合缓存和最终一致性场景
- **vs MySQL**：ByteKV 是分布式键值存储，适合简单KV模型；MySQL 是关系型数据库，适合复杂查询和事务
- **vs 其他KV存储**：ByteKV 支持分布式事务和强一致性，适合在线业务场景

## 连接与初始化

ByteKV 的初始化通常在服务启动时完成，并保持一个全局单例的客户端实例。

### 配置项

```go
type Config struct {
    ServiceName string // 服务发现名称，格式：bytedance.bytekv.${module_name}
    ClusterName string // 集群名称
    Namespace   string // 命名空间
    Logf        func(format string, args ...interface{}) // 自定义日志函数
}
```

### 服务发现

ByteKV 使用 Consul 进行服务发现。ServiceName 的格式为 `bytedance.bytekv.${module_name}`，其中 `${module_name}` 是将用户的 `cluster_name` 中的 `'.'` 转换为 `'_'` 之后的字符串。

### 超时与重试

SDK 内置了连接超时和请求超时机制，可以通过配置项进行设置。

## 典型代码片段

### 初始化

```go
package main

import (
    "context"
    "fmt"
    "code.byted.org/gopkg/bytekv"
)

// NewByteKVClient 创建并返回一个 ByteKV Client 实例
func NewByteKVClient() (*bytekv.Client, error) {
    conf := &bytekv.Config{
        ServiceName: "bytedance.bytekv.my_test_cluster",
        ClusterName: "my_test_cluster",
        Namespace:   "test_namespace",
    }
    
    // 可选：自定义日志函数
    conf.Logf = func(format string, args ...interface{}) {
        fmt.Printf("[ByteKV] "+format, args...)
    }
    
    client, err := bytekv.New(conf)
    if err != nil {
        return nil, fmt.Errorf("failed to create ByteKV client: %v", err)
    }
    
    return client, nil
}
```

### 基本 CRUD (Put/Get/Delete)

```go
package storage

import (
    "context"
    "fmt"
    "code.byted.org/gopkg/bytekv"
)

type MetadataStore struct {
    client *bytekv.Client
}

func NewMetadataStore(client *bytekv.Client) *MetadataStore {
    return &MetadataStore{client: client}
}

// PutMetadata 存储元数据
func (s *MetadataStore) PutMetadata(ctx context.Context, table, key, value string) error {
    resp := s.client.Put(ctx, table, []byte(key), []byte(value))
    if resp.Err != nil {
        return fmt.Errorf("failed to put metadata: %v", resp.Err)
    }
    return nil
}

// PutMetadataWithTTL 存储带过期时间的元数据
func (s *MetadataStore) PutMetadataWithTTL(ctx context.Context, table, key, value string, ttlSeconds int) error {
    resp := s.client.Put(ctx, table, []byte(key), []byte(value), bytekv.WithTtlSeconds(ttlSeconds))
    if resp.Err != nil {
        return fmt.Errorf("failed to put metadata with TTL: %v", resp.Err)
    }
    return nil
}

// GetMetadata 获取元数据
func (s *MetadataStore) GetMetadata(ctx context.Context, table, key string) (string, error) {
    resp := s.client.Get(ctx, table, []byte(key))
    if resp.Err != nil {
        return "", fmt.Errorf("failed to get metadata: %v", resp.Err)
    }
    return string(resp.Value), nil
}

// DeleteMetadata 删除元数据
func (s *MetadataStore) DeleteMetadata(ctx context.Context, table, key string) error {
    resp := s.client.Delete(ctx, table, []byte(key))
    if resp.Err != nil {
        return fmt.Errorf("failed to delete metadata: %v", resp.Err)
    }
    return nil
}
```

### 事务操作 (WriteBatch)

```go
// BatchUpdateMetadata 批量更新元数据（原子性保证）
func (s *MetadataStore) BatchUpdateMetadata(ctx context.Context, table string, updates map[string]string) error {
    wb := s.client.BeginWriteBatch()
    
    for key, value := range updates {
        wb.Put(table, []byte(key), []byte(value))
    }
    
    resp := wb.Commit(ctx)
    if resp.Err != nil {
        return fmt.Errorf("failed to commit write batch: %v", resp.Err)
    }
    return nil
}
```

### 批量操作 (MultiGet/MultiWrite)

```go
// BatchGetMetadata 批量获取元数据（一致性快照读）
func (s *MetadataStore) BatchGetMetadata(ctx context.Context, table string, keys []string) (map[string]string, error) {
    mg := s.client.BeginMultiGet()
    
    for _, key := range keys {
        mg.Get(table, []byte(key))
    }
    
    resp := mg.Commit(ctx)
    if resp.Err != nil {
        return nil, fmt.Errorf("failed to commit multi get: %v", resp.Err)
    }
    
    result := make(map[string]string)
    for i, key := range keys {
        if i < len(resp.Values) && resp.Values[i] != nil {
            result[key] = string(resp.Values[i])
        }
    }
    
    return result, nil
}

// BatchWriteMetadata 批量写入元数据（非事务性）
func (s *MetadataStore) BatchWriteMetadata(ctx context.Context, table string, kvs map[string]string) error {
    mw := s.client.BeginMultiWrite()
    
    for key, value := range kvs {
        mw.Put(table, []byte(key), []byte(value))
    }
    
    resp := mw.Commit(ctx)
    if resp.Err != nil {
        return fmt.Errorf("failed to commit multi write: %v", resp.Err)
    }
    return nil
}
```

### 扫描操作 (Scan)

```go
// ScanMetadata 扫描元数据
func (s *MetadataStore) ScanMetadata(ctx context.Context, table, startKey string, limit int) ([]string, error) {
    it, err := s.client.Scan(ctx, table, []byte(startKey), bytekv.WithLimit(limit))
    if err != nil {
        return nil, fmt.Errorf("failed to start scan: %v", err)
    }
    defer it.Close()
    
    var results []string
    for {
        err = it.Next(ctx)
        if err != nil {
            break
        }
        key := string(it.Key())
        value := string(it.Value())
        version := it.Version()
        
        results = append(results, fmt.Sprintf("key=%s, value=%s, version=%d", key, value, version))
    }
    
    if err != nil && err != bytekv.ErrIteratorEnd {
        return nil, fmt.Errorf("scan error: %v", err)
    }
    
    return results, nil
}

// ScanByPrefix 按前缀扫描
func (s *MetadataStore) ScanByPrefix(ctx context.Context, table, prefix string) (map[string]string, error) {
    // 使用前缀作为startKey，扫描所有以该前缀开头的key
    it, err := s.client.Scan(ctx, table, []byte(prefix))
    if err != nil {
        return nil, fmt.Errorf("failed to start prefix scan: %v", err)
    }
    defer it.Close()
    
    result := make(map[string]string)
    for {
        err = it.Next(ctx)
        if err != nil {
            break
        }
        
        key := string(it.Key())
        // 检查是否仍然以prefix开头（Scan可能返回超过prefix范围的数据）
        if len(key) >= len(prefix) && key[:len(prefix)] == prefix {
            result[key] = string(it.Value())
        } else {
            // 已经超出前缀范围，可以提前结束
            break
        }
    }
    
    if err != nil && err != bytekv.ErrIteratorEnd {
        return nil, fmt.Errorf("prefix scan error: %v", err)
    }
    
    return result, nil
}
```

### CAS 操作

```go
// UpdateMetadataCAS 使用CAS更新元数据
func (s *MetadataStore) UpdateMetadataCAS(ctx context.Context, table, key, newValue string, expectedVersion uint64) error {
    resp := s.client.Put(ctx, table, []byte(key), []byte(newValue), bytekv.WithExpectedVersion(expectedVersion))
    
    if resp.Err == bytekv.ErrCasFailed {
        // CAS失败，需要重新获取当前版本并重试
        return fmt.Errorf("CAS failed: version mismatch")
    }
    
    if resp.Err == bytekv.ErrTimeout {
        // 超时情况，无法确定操作是否成功
        // 需要在value中编码unique-request-id，通过比较当前值来判断是否成功
        return fmt.Errorf("CAS timeout: cannot determine if operation succeeded")
    }
    
    if resp.Err != nil {
        return fmt.Errorf("CAS operation failed: %v", resp.Err)
    }
    
    return nil
}
```

## 常见坑与推荐写法

### 大 Key/热 Key

**限制**：
- **最佳使用**：单个 KV 的大小在 10KB 以内有比较好的性能
- **使用要求**：单个 KV 的大小不超过 100KB，否则无稳定性保证
- **直接拒绝**：单个 KV 的大小超过 1MB 时，写入会直接返回失败

**推荐写法**：
```go
// 避免存储大Value
func (s *MetadataStore) StoreLargeData(ctx context.Context, table, key string, largeData []byte) error {
    if len(largeData) > 100*1024 { // 100KB
        return fmt.Errorf("data too large: %d bytes, max 100KB", len(largeData))
    }
    
    // 如果数据确实很大，考虑分片存储
    if len(largeData) > 10*1024 { // 10KB
        return s.storeChunkedData(ctx, table, key, largeData)
    }
    
    return s.PutMetadata(ctx, table, key, string(largeData))
}

func (s *MetadataStore) storeChunkedData(ctx context.Context, table, key string, data []byte) error {
    chunkSize := 8 * 1024 // 8KB per chunk
    chunkCount := (len(data) + chunkSize - 1) / chunkSize
    
    wb := s.client.BeginWriteBatch()
    
    // 存储分片信息
    wb.Put(table, []byte(key+"_info"), []byte(fmt.Sprintf(`{"chunks":%d}`, chunkCount)))
    
    // 存储各个分片
    for i := 0; i < chunkCount; i++ {
        start := i * chunkSize
        end := start + chunkSize
        if end > len(data) {
            end = len(data)
        }
        chunkKey := fmt.Sprintf("%s_chunk_%d", key, i)
        wb.Put(table, []byte(chunkKey), data[start:end])
    }
    
    resp := wb.Commit(ctx)
    return resp.Err
}
```

### 键名与序列化规范

**限制**：
- **最佳使用**：避免 key 过长，以便得到更好的存储效率
- **使用要求**：key 长度不超过 1024 字节
- **重要提示**：ByteKV 不接受空 key，并且不对空 key 的访问返回结果做任何保证

**推荐写法**：
```go
// 使用有意义的键名结构
func buildUserKey(userID string) string {
    return fmt.Sprintf("user:%s:profile", userID)
}

func buildSessionKey(sessionID string) string {
    return fmt.Sprintf("session:%s", sessionID)
}

// 使用JSON序列化复杂结构
type UserProfile struct {
    ID        string `json:"id"`
    Name      string `json:"name"`
    Email     string `json:"email"`
    CreatedAt int64  `json:"created_at"`
}

func (s *MetadataStore) StoreUserProfile(ctx context.Context, userID string, profile *UserProfile) error {
    data, err := json.Marshal(profile)
    if err != nil {
        return fmt.Errorf("failed to marshal profile: %v", err)
    }
    
    key := buildUserKey(userID)
    return s.PutMetadata(ctx, "user_profiles", key, string(data))
}
```

### 批量操作限制

**限制**：
- **最佳使用**：单个 WriteBatch/MultiWrite/MultiGet 请求的 key 数量在 10 个以内有比较好的性能
- **使用要求**：单个 WriteBatch/MultiWrite/MultiGet 请求的 key 数量不超过 100 个，否则无稳定性保证
- **直接拒绝**：单个 WriteBatch/MultiWrite/MultiGet 请求的 key 数量超过 1000 个时，会直接返回失败

**推荐写法**：
```go
// 分批处理大量key
func (s *MetadataStore) BatchGetLargeDataset(ctx context.Context, table string, keys []string, batchSize int) (map[string]string, error) {
    result := make(map[string]string)
    
    for i := 0; i < len(keys); i += batchSize {
        end := i + batchSize
        if end > len(keys) {
            end = len(keys)
        }
        
        batchKeys := keys[i:end]
        batchResult, err := s.BatchGetMetadata(ctx, table, batchKeys)
        if err != nil {
            return nil, fmt.Errorf("batch get failed at batch %d: %v", i/batchSize, err)
        }
        
        for k, v := range batchResult {
            result[k] = v
        }
    }
    
    return result, nil
}
```

### QPS 限制

**限制**：
- **最佳使用**：各类型请求的 QPS 都不超过工单中对应的 QPS
- **归一化算法**：
  - 1 MultiGet = key_num Get
  - 1 Delete = 1 Put
  - 1 WriteBatch = (key_num * 2 + 3) Put
  - 1 MultiWrite = key_num Put

**推荐写法**：
```go
// 实现QPS监控和限流
type RateLimitedStore struct {
    store      *MetadataStore
    qpsLimiter *rate.Limiter
}

func NewRateLimitedStore(store *MetadataStore, qps int) *RateLimitedStore {
    return &RateLimitedStore{
        store:      store,
        qpsLimiter: rate.NewLimiter(rate.Limit(qps), qps),
    }
}

func (r *RateLimitedStore) GetMetadataWithRateLimit(ctx context.Context, table, key string) (string, error) {
    if err := r.qpsLimiter.Wait(ctx); err != nil {
        return "", fmt.Errorf("rate limit exceeded: %v", err)
    }
    return r.store.GetMetadata(ctx, table, key)
}
```

## 相关文档

- [ByteKV 官方文档](https://cloud.bytedance.net/docs/product/bytekv?from=cloud)
- [ByteKV 使用限制](https://bytedance.larkoffice.com/docx/OBNFdipOvo1ennxnsLOcKlMinze)
- [Go SDK API Reference](https://code.byted.org/godoc/code.byted.org/gopkg/bytekv)
- [ByteKV 最佳实践](https://cloud.bytedance.net/docs/bytekv/docs/6412809fb08fc5022949da0b/654a2dc6b1398002ebf4bc20)