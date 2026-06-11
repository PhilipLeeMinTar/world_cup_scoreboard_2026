# 自定义 Resolver

## 概述

Resolver 负责服务发现，将服务名解析为实例列表。Kitex 支持自定义 Resolver 实现。

## Resolver 接口

```go
type Resolver interface {
    // Target 返回要解析的目标描述
    Target(ctx context.Context, target rpcinfo.EndpointInfo) string

    // Resolve 执行解析，返回发现结果
    Resolve(ctx context.Context, key string) (Result, error)

    // Diff 比较两次解析结果的差异
    Diff(key string, prev, next Result) (Change, bool)

    // Name 返回 Resolver 名称
    Name() string
}
```

## 实现自定义 Resolver

### 静态 IP 列表

```go
type StaticResolver struct {
    instances map[string][]discovery.Instance
}

func NewStaticResolver(config map[string][]string) *StaticResolver {
    instances := make(map[string][]discovery.Instance)

    for serviceName, addrs := range config {
        var insts []discovery.Instance
        for _, addr := range addrs {
            insts = append(insts, discovery.NewInstance(
                "tcp",
                addr,
                10,  // weight
                nil, // tags
            ))
        }
        instances[serviceName] = insts
    }

    return &StaticResolver{instances: instances}
}

func (r *StaticResolver) Target(ctx context.Context, target rpcinfo.EndpointInfo) string {
    return target.ServiceName()
}

func (r *StaticResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    instances, ok := r.instances[key]
    if !ok {
        return discovery.Result{}, fmt.Errorf("service %s not found", key)
    }

    return discovery.Result{
        Cacheable: true,
        CacheKey:  key,
        Instances: instances,
    }, nil
}

func (r *StaticResolver) Diff(key string, prev, next discovery.Result) (discovery.Change, bool) {
    return discovery.Change{
        Result: next,
    }, true
}

func (r *StaticResolver) Name() string {
    return "static"
}
```

### 使用自定义 Resolver

```go
resolver := NewStaticResolver(map[string][]string{
    "my.service": {
        "192.168.1.1:8888",
        "192.168.1.2:8888",
        "192.168.1.3:8888",
    },
})

cli, err := myservice.NewClient(
    "my.service",
    client.WithResolver(resolver),
)
```

## 高级示例

### 配置文件 Resolver

```go
type FileResolver struct {
    configPath string
    instances  sync.Map  // serviceName -> []Instance
    watcher    *fsnotify.Watcher
}

func NewFileResolver(configPath string) (*FileResolver, error) {
    r := &FileResolver{
        configPath: configPath,
    }

    // 初始加载
    if err := r.loadConfig(); err != nil {
        return nil, err
    }

    // 监听文件变化
    watcher, err := fsnotify.NewWatcher()
    if err != nil {
        return nil, err
    }

    r.watcher = watcher
    go r.watchConfig()

    return r, nil
}

func (r *FileResolver) loadConfig() error {
    data, err := ioutil.ReadFile(r.configPath)
    if err != nil {
        return err
    }

    var config map[string][]struct {
        Address string `json:"address"`
        Weight  int    `json:"weight"`
    }

    if err := json.Unmarshal(data, &config); err != nil {
        return err
    }

    for serviceName, addrs := range config {
        var instances []discovery.Instance
        for _, addr := range addrs {
            instances = append(instances, discovery.NewInstance(
                "tcp",
                addr.Address,
                addr.Weight,
                nil,
            ))
        }
        r.instances.Store(serviceName, instances)
    }

    return nil
}

func (r *FileResolver) watchConfig() {
    r.watcher.Add(r.configPath)

    for {
        select {
        case event := <-r.watcher.Events:
            if event.Op&fsnotify.Write == fsnotify.Write {
                log.Println("Config file changed, reloading...")
                r.loadConfig()
            }
        case err := <-r.watcher.Errors:
            log.Println("Watcher error:", err)
        }
    }
}

func (r *FileResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    instances, ok := r.instances.Load(key)
    if !ok {
        return discovery.Result{}, fmt.Errorf("service %s not found", key)
    }

    return discovery.Result{
        Cacheable: false,  // 不缓存，始终从文件读取
        Instances: instances.([]discovery.Instance),
    }, nil
}
```

### HTTP API Resolver

```go
type HTTPResolver struct {
    apiEndpoint string
    client      *http.Client
    cache       sync.Map
}

func NewHTTPResolver(endpoint string) *HTTPResolver {
    return &HTTPResolver{
        apiEndpoint: endpoint,
        client:      &http.Client{Timeout: 5 * time.Second},
    }
}

func (r *HTTPResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    // 先查缓存
    if cached, ok := r.cache.Load(key); ok {
        return cached.(discovery.Result), nil
    }

    // 调用 API 获取实例列表
    url := fmt.Sprintf("%s/services/%s/instances", r.apiEndpoint, key)
    resp, err := r.client.Get(url)
    if err != nil {
        return discovery.Result{}, err
    }
    defer resp.Body.Close()

    var apiResp struct {
        Instances []struct {
            Address string            `json:"address"`
            Weight  int               `json:"weight"`
            Tags    map[string]string `json:"tags"`
        } `json:"instances"`
    }

    if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
        return discovery.Result{}, err
    }

    // 转换为 Kitex Instance
    var instances []discovery.Instance
    for _, inst := range apiResp.Instances {
        instances = append(instances, discovery.NewInstance(
            "tcp",
            inst.Address,
            inst.Weight,
            inst.Tags,
        ))
    }

    result := discovery.Result{
        Cacheable: true,
        CacheKey:  key,
        Instances: instances,
    }

    // 缓存结果
    r.cache.Store(key, result)

    return result, nil
}
```

## 结合服务发现中间件

### Consul Resolver

```go
import (
    "github.com/hashicorp/consul/api"
)

type ConsulResolver struct {
    client *api.Client
}

func NewConsulResolver(addr string) (*ConsulResolver, error) {
    config := api.DefaultConfig()
    config.Address = addr

    client, err := api.NewClient(config)
    if err != nil {
        return nil, err
    }

    return &ConsulResolver{client: client}, nil
}

func (r *ConsulResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    // 查询 Consul 服务
    services, _, err := r.client.Health().Service(key, "", true, nil)
    if err != nil {
        return discovery.Result{}, err
    }

    var instances []discovery.Instance
    for _, service := range services {
        addr := fmt.Sprintf("%s:%d", service.Service.Address, service.Service.Port)
        instances = append(instances, discovery.NewInstance(
            "tcp",
            addr,
            service.Service.Weights.Passing,
            service.Service.Tags,
        ))
    }

    return discovery.Result{
        Cacheable: true,
        CacheKey:  key,
        Instances: instances,
    }, nil
}
```

## 最佳实践

### 1. 实现缓存机制

```go
type CachedResolver struct {
    resolver discovery.Resolver
    cache    *cache.Cache
    ttl      time.Duration
}

func (r *CachedResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    // 检查缓存
    if cached, found := r.cache.Get(key); found {
        return cached.(discovery.Result), nil
    }

    // 调用底层 Resolver
    result, err := r.resolver.Resolve(ctx, key)
    if err != nil {
        return result, err
    }

    // 缓存结果
    r.cache.Set(key, result, r.ttl)

    return result, nil
}
```

### 2. 健康检查

```go
func (r *MyResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    allInstances := r.getAllInstances(key)

    // 过滤健康实例
    var healthyInstances []discovery.Instance
    for _, inst := range allInstances {
        if r.isHealthy(inst) {
            healthyInstances = append(healthyInstances, inst)
        }
    }

    return discovery.Result{
        Instances: healthyInstances,
    }, nil
}

func (r *MyResolver) isHealthy(inst discovery.Instance) bool {
    // 实现健康检查逻辑
    conn, err := net.DialTimeout("tcp", inst.Address().String(), 3*time.Second)
    if err != nil {
        return false
    }
    conn.Close()
    return true
}
```

### 3. 错误处理和降级

```go
func (r *MyResolver) Resolve(ctx context.Context, key string) (discovery.Result, error) {
    result, err := r.fetchInstances(ctx, key)
    if err != nil {
        // 使用缓存的旧数据
        if cached, ok := r.cache.Load(key); ok {
            log.Warnf("Using cached instances for %s due to error: %v", key, err)
            return cached.(discovery.Result), nil
        }
        return result, err
    }

    // 更新缓存
    r.cache.Store(key, result)

    return result, nil
}
```

## 相关文档

- [负载均衡配置](./configure-loadbalance.md)
- [自定义 LoadBalancer](./implement-custom-loadbalancer.md)
- [重试配置](./configure-retry.md)
