# GDP 配置组件

## 概述

GDP 配置组件提供了统一的配置管理解决方案，支持文件配置和 TCC（远程配置中心）配置获取。通过统一的接口，开发者可以在多机房环境下方便地获取配置信息，同时支持配置的版本管理、环境隔离和单元测试 Mock。

**代码包**：code.byted.org/gdp/config

## 主要特性

- **统一接口**：通过 `Get` 方法统一获取文件配置和 TCC 配置
- **多环境支持**：支持基于环境变量的配置覆盖机制
- **类型安全**：支持结构体配置绑定，自动解析 YAML/JSON
- **配置 Mock**：单元测试场景下支持配置 Mock
- **优先级管理**：清晰的配置优先级规则
- **多机房适配**：适配字节跳动多机房部署架构

## 快速上手

### 获取文件配置

文件配置支持 YAML 格式，支持多环境覆盖：

```go
import "code.byted.org/gdp/config"

type AppConfig struct {
    DatabaseURL string `yaml:"database_url"`
    MaxRetries  int    `yaml:"max_retries"`
    Features    []string `yaml:"features"`
}

func LoadConfig(ctx context.Context) (*AppConfig, error) {
    var cfg AppConfig
    if err := config.Get(ctx, "app/config", &cfg); err != nil {
        return nil, err
    }
    return &cfg, nil
}
```

**配置文件结构：**
```yaml
# app/config.yaml
database_url: "mysql://localhost:3306/mydb"
max_retries: 3
features:
  - feature1
  - feature2

# app/config.boei18n.yaml (环境特定配置)
database_url: "mysql://boe-db:3306/mydb"
# max_retries 继承基础配置
```

### 获取 TCC 配置

TCC 配置支持 JSON 格式，支持命名空间和分组：

```go
import "code.byted.org/gdp/config"

func LoadTCCConfig(ctx context.Context) error {
    // 获取简单配置
    var apiKey string
    if err := config.Get(ctx, "api_key", &apiKey); err != nil {
        return err
    }

    // 获取复杂配置
    var featureFlags []string
    if err := config.Get(ctx, "feature_flags", &featureFlags); err != nil {
        return err
    }

    // 指定命名空间和分组
    var testConfig string
    if err := config.Get(ctx, "test_key", &testConfig,
        config.WithNamespace("other.service"),
        config.WithGroup("test"),
    ); err != nil {
        return err
    }

    return nil
}
```

### 配置默认值和自定义解析

```go
import "code.byted.org/gdp/config"

func LoadConfigWithDefaults(ctx context.Context) error {
    // 带默认值的配置
    var timeout int
    if err := config.Get(ctx, "timeout", &timeout,
        config.WithDefault(30),
    ); err != nil {
        return err
    }

    // 自定义解析器
    var allowedIPs []string
    if err := config.Get(ctx, "allowed_ips", &allowedIPs,
        config.WithParser(func(raw string) (interface{}, error) {
            return strings.Split(raw, ","), nil
        }),
    ); err != nil {
        return err
    }

    return nil
}
```

## 配置 Mock

在单元测试场景下，可以通过 `Mock` 接口实现对配置的模拟：

```go
import "code.byted.org/gdp/config"

func TestConfig(t *testing.T) {
    // Mock 文件配置
    config.Mock("app/config", map[string]interface{}{
        "database_url": "mock://test-db",
        "max_retries":  5,
    })

    // Mock TCC 配置
    config.Mock("api_key", "mock-api-key")

    // 测试代码
    var cfg AppConfig
    err := config.Get(ctx, "app/config", &cfg)
    // cfg.DatabaseURL == "mock://test-db"
}
```

## 配置优先级

GDP 配置组件遵循以下优先级规则（从高到低）：

1. **Mock 配置**（单元测试场景）
2. **环境特定配置**（如 `.boei18n.yaml`）
3. **默认配置文件**（如 `.yaml`）
4. **TCC 远程配置**
5. **默认值**（通过 `WithDefault` 设置）

## 最佳实践

### 配置结构设计
- 使用清晰的层级结构，避免过深的嵌套
- 为不同环境创建专门的配置文件
- 使用有意义的键名，遵循命名规范
- 为配置项添加合适的 YAML 标签

### 配置使用
- 优先使用文件配置管理静态配置
- 使用 TCC 配置管理动态配置和业务参数
- 在代码中始终处理配置获取错误
- 为关键配置设置合理的默认值
- 避免在热点代码中频繁获取配置

### 多环境支持
- 利用 GDP 的多环境配置机制
- 为每个环境创建对应的配置文件
- 使用 `WithNamespace` 和 `WithGroup` 管理 TCC 配置
- 理解配置继承和覆盖规则

## 相关文档
- [RAL概述](../ral/overview.md) - RAL组件总体介绍
- [RPC资源](../ral/rpc.md) - 远程过程调用配置和使用
- [Abase/Redis资源](../ral/abase_redis.md) - 缓存资源配置和使用
- [Database资源](../ral/database.md) - 数据库资源配置和使用
- [Eventbus资源](../ral/eventbus.md) - 消息队列资源配置和使用