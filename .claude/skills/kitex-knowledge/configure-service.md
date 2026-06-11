# Kitex 配置文件使用

## 概述

Kitex 支持多种配置方式，包括代码配置、配置文件和配置中心。

## 配置文件格式

### YAML 配置

推荐使用 YAML 格式配置文件：

```yaml
# config.yaml
server:
  service_name: "my.service"
  address: ":8888"

client:
  my_service:
    address: "127.0.0.1:8888"
    timeout: 1000  # 毫秒
    retry:
      max_retry_times: 2

  another_service:
    address: "127.0.0.1:9999"
    timeout: 2000
```

### JSON 配置

```json
{
  "server": {
    "service_name": "my.service",
    "address": ":8888"
  },
  "client": {
    "my_service": {
      "address": "127.0.0.1:8888",
      "timeout": 1000
    }
  }
}
```

## 读取配置文件

### 使用 viper 读取

```go
import (
    "github.com/spf13/viper"
    "github.com/cloudwego/kitex/server"
    "github.com/cloudwego/kitex/client"
)

func main() {
    // 读取配置文件
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath(".")
    viper.AddConfigPath("./conf")

    if err := viper.ReadInConfig(); err != nil {
        panic(err)
    }

    // 创建 Server
    addr := viper.GetString("server.address")
    svr := myservice.NewServer(
        new(MyServiceImpl),
        server.WithServiceAddr(&net.TCPAddr{
            Port: parsePort(addr),
        }),
    )

    // 创建 Client
    timeout := viper.GetInt("client.my_service.timeout")
    cli, err := downstream.NewClient(
        "downstream.service",
        client.WithRPCTimeout(time.Duration(timeout) * time.Millisecond),
    )
}
```

### 使用自定义配置结构

```go
type Config struct {
    Server ServerConfig `yaml:"server"`
    Client map[string]ClientConfig `yaml:"client"`
}

type ServerConfig struct {
    ServiceName string `yaml:"service_name"`
    Address     string `yaml:"address"`
}

type ClientConfig struct {
    Address string `yaml:"address"`
    Timeout int    `yaml:"timeout"`
    Retry   RetryConfig `yaml:"retry"`
}

type RetryConfig struct {
    MaxRetryTimes int `yaml:"max_retry_times"`
}

func LoadConfig(path string) (*Config, error) {
    data, err := ioutil.ReadFile(path)
    if err != nil {
        return nil, err
    }

    var config Config
    if err := yaml.Unmarshal(data, &config); err != nil {
        return nil, err
    }

    return &config, nil
}
```

## 多环境配置

### 按环境分离配置文件

```
conf/
├── config.yaml          # 默认配置
├── config.dev.yaml      # 开发环境
├── config.test.yaml     # 测试环境
└── config.prod.yaml     # 生产环境
```

### 加载环境配置

```go
func LoadEnvConfig() (*Config, error) {
    env := os.Getenv("ENV")
    if env == "" {
        env = "dev"
    }

    configFile := fmt.Sprintf("conf/config.%s.yaml", env)
    return LoadConfig(configFile)
}
```

### 配置合并

```go
func MergeConfig(base, override *Config) *Config {
    // 基础配置 + 环境配置
    merged := *base

    if override.Server.Address != "" {
        merged.Server.Address = override.Server.Address
    }

    for name, cfg := range override.Client {
        merged.Client[name] = cfg
    }

    return &merged
}
```

## 配置热更新

### 监听配置文件变化

```go
import (
    "github.com/fsnotify/fsnotify"
)

func WatchConfig(configPath string, onChange func(*Config)) {
    viper.WatchConfig()
    viper.OnConfigChange(func(e fsnotify.Event) {
        log.Println("Config file changed:", e.Name)

        var newConfig Config
        if err := viper.Unmarshal(&newConfig); err != nil {
            log.Println("Failed to unmarshal config:", err)
            return
        }

        onChange(&newConfig)
    })
}
```

### 应用配置更新

```go
func main() {
    config := LoadConfig("config.yaml")

    // 创建可更新的 Client
    var cli myservice.Client
    updateClient := func(cfg *Config) {
        newCli, err := myservice.NewClient(
            "my.service",
            client.WithRPCTimeout(time.Duration(cfg.Client["my_service"].Timeout) * time.Millisecond),
        )
        if err != nil {
            log.Println("Failed to create client:", err)
            return
        }
        cli = newCli
    }

    updateClient(config)

    // 监听配置变化
    WatchConfig("config.yaml", updateClient)
}
```

## 配置中心集成

### 使用配置中心

```go
import (
    "code.byted.org/kite/kitex-contrib/configcenter"
)

func main() {
    // 连接配置中心
    cc := configcenter.NewClient(configcenter.Options{
        ConfigCenterAddr: "config-center.example.com:8080",
        ServiceName:      "my.service",
    })

    // 订阅配置
    cc.Subscribe(func(key string, value interface{}) {
        log.Printf("Config updated: %s = %v", key, value)

        // 动态更新配置
        switch key {
        case "timeout":
            newTimeout := value.(int)
            // 更新 client timeout
        case "retry_times":
            newRetryTimes := value.(int)
            // 更新重试次数
        }
    })
}
```

## 常用配置项

### Server 配置

```yaml
server:
  service_name: "my.service"
  address: ":8888"

  # 连接限制
  max_connections: 10000

  # 读写超时
  read_timeout: 5000   # 毫秒
  write_timeout: 5000

  # 优雅关闭
  exit_wait_time: 5000
```

### Client 配置

```yaml
client:
  my_service:
    address: "127.0.0.1:8888"

    # 超时配置
    timeout: 1000
    connect_timeout: 100

    # 重试配置
    retry:
      max_retry_times: 2
      enable_backup_request: true
      backup_delay: 20

    # 连接池配置
    connection_pool:
      max_idle_per_address: 10
      max_idle_global: 1000
      max_idle_timeout: 60000
      min_idle_per_address: 2

    # 负载均衡
    load_balance: "weighted_random"

    # 熔断配置
    circuit_breaker:
      error_rate_threshold: 0.5
      min_sample: 100
```

## 配置验证

### 添加配置验证

```go
func ValidateConfig(config *Config) error {
    if config.Server.Address == "" {
        return errors.New("server address is required")
    }

    if config.Server.ServiceName == "" {
        return errors.New("service name is required")
    }

    for name, cli := range config.Client {
        if cli.Timeout <= 0 {
            return fmt.Errorf("invalid timeout for client %s", name)
        }
        if cli.Address == "" {
            return fmt.Errorf("address is required for client %s", name)
        }
    }

    return nil
}
```

## 最佳实践

### 1. 敏感信息处理

```yaml
# 使用环境变量
database:
  password: ${DB_PASSWORD}

# 或使用密钥管理服务
api:
  secret_key: ${SECRET_KEY}
```

```go
func ExpandEnvVars(s string) string {
    return os.ExpandEnv(s)
}

password := ExpandEnvVars(config.Database.Password)
```

### 2. 配置分层

```
conf/
├── default.yaml       # 默认值
├── base.yaml         # 基础配置
├── dev.yaml          # 开发环境覆盖
└── prod.yaml         # 生产环境覆盖
```

### 3. 配置文档化

```yaml
# config.yaml

# Server 配置
server:
  # 服务名称，用于服务发现和监控
  service_name: "my.service"

  # 监听地址，格式: [host]:port
  address: ":8888"

  # 最大连接数，0 表示不限制
  max_connections: 10000
```

### 4. 配置校验规则

```go
type Config struct {
    Server ServerConfig `yaml:"server" validate:"required"`
    Client map[string]ClientConfig `yaml:"client" validate:"required"`
}

type ServerConfig struct {
    ServiceName string `yaml:"service_name" validate:"required"`
    Address     string `yaml:"address" validate:"required,hostname_port"`
}

func ValidateWithTags(config *Config) error {
    validate := validator.New()
    return validate.Struct(config)
}
```

## 相关文档

- [使用 Call Options](./using-call-options.md)
- [重试配置](./configure-retry.md)
- [超时配置](./configure-timeout.md)
