# Kitex 启动配置

## 概述

Kitex Server 启动时需要一些配置信息，诸如监听端口、日志等。本文介绍这些配置的详情及加载方式。

## 配置内容

在 Kitex v1.13.1 版本，启动配置包括：

| 配置名称 | 说明 | 默认值 |
|----------|------|--------|
| AddressConfig | 协议和监听端口，可以指定为 uds 地址 | Network: "tcp"<br>Address: ":8888" |
| ServerTimeoutConfig | 服务端超时配置 | ExitWaitTime: 5s<br>ReadWriteTime: 5s |
| DebugConfig | Debug 配置。开启后不使用 debug 功能不会影响性能 | Enable: true<br>DebugPort: 18888 |
| RuntimeMetricConfig | 是否用 gopkg/stats 采集 Go Runtime 指标 | Enable: true |
| LogConfig | 业务日志、Access Log、Call Log 的配置 | 参见默认配置 |
| RemoteConfigCenter | 治理配置来源<br>"Byted"(或空串)：读取 Neptune 配置<br>"Local"：读取文件配置 | Source: "" |

## 配置加载

### 入口与触发时机

启动配置的加载入口为 `config.Init()`：

- **Kitex Server** 初始化时**会**调用该方法
- **Kitex Client** 初始化时**不会**调用该方法
  - 如果某服务只用到了 Kitex Client，默认不会加载启动配置
  - 可以在 Client 初始化之前主动调用 `config.Init()` 加载配置

### 加载顺序

在 `config.Init()` 里会按照如下顺序分别调用不同的 Initializer，最终得到叠加结果（后执行的优先级更高）：

1. **DefaultInitializer** - 加载默认配置
2. **YamlFileInitializer** - 从 Yaml 文件加载
3. **EnvInitializer** - 从环境变量加载
4. **userDefinedInitializers** - 用户自定义加载

### 默认值：DefaultInitializer

从 `config.defaultConfig` 深拷贝默认配置到全局 config。

### Yaml 文件：YamlFileInitializer

从文件中加载配置到全局 config。

**默认配置文件路径**：`conf/kitex.yml`

可以通过环境变量指定：
- **目录名**：环境变量 `KITEX_CONF_DIR`，默认为 "conf/"
- **文件名**：环境变量 `KITEX_CONF_FILE`，默认为 "kitex.yml"

#### 样例 Yaml 文件

```yaml
Network: "tcp"            # 服务端监听地址的网络类型，只支持 tcp 和 unix
Address: ":8888"          # 服务器监听的地址，tcp端口必须带':'；优先级低于环境变量 TCE_PRIMARY_PORT
ExitWaitTimeout: "5s"     # 服务端退出前的等待时长
ReadWriteTimeout: "3s"    # 服务端读写超时
EnableDebugServer: true   # 开启 debug server；开启后不使用debug功能不影响性能
DebugServerPort: "18888"  # debug server 的端口；优先级低于环境变量 TCE_DEBUG_PORT
EnableRuntimeMetric: true # 开启 gopkg/stats 采集 Go Runtime 指标
RemoteConfigCenter:
  Source: "Byted"         # 读取 Neptune 的服务治理配置（超时、重试等）
Log:                      # 日志配置
  Dir: log                # 日志文件输出的顶层目录
  Loggers:
    - Name: default       # 应用日志
      Level: info         # 日志级别: trace, debug, info, notice, warn, error, fatal
      Outputs:            # 输出流：File（文件）、Console（终端）、Agent（流式日志）
        - File
        - Agent
      # - Console         # WARNING: 仅用于调试，生产环境禁用！
    - Name: rpcAccess     # 服务端访问日志
      Level: trace        # 不建议修改，否则可能影响调用链构建（tracing）
      Outputs:
        - File
        - Agent
    - Name: rpcCall       # 客户端调用日志
      Level: trace        # 不建议修改，否则可能影响调用链构建（tracing）
      Outputs:            # 如果 Outputs 列表为空，则该 logger 不会输出日志
        - File
        - Agent
```

#### 注意事项

1. 如配置文件里缺失 Log 配置，Kitex 会使用默认配置
2. 如想调整某些字段（如给 rpcCall 增加 Console output），需要补充**完整**的 Log 配置

### 环境变量：EnvInitializer

从环境变量中读取以下配置（优先级高于文件配置）：

| 环境变量 | 说明 |
|----------|------|
| `KITEX_LOG_DIR` | 日志目录 |
| `TCE_PRIMARY_PORT` | 监听端口 |
| `TCE_DEBUG_PORT` | Debug 端口 |

由于需要配合 TCE 的管理需求，环境变量优先级高于文件配置（特别是监听端口）。

### 自定义加载：userDefinedInitializers

#### 方式 1：AddInitializer

```go
config.AddInitializer(Initializer)
```

可以添加多个用户自定义的 Initializer，修改任意配置。

#### 方式 2：NewServerWithBytedConfig

在 `NewServerWithBytedConfig(...)` 初始化 Server 时，指定自定义的 `byted.ServerConfig`，会添加一个 userDefinedInitializer，用 ServerConfig 里的下列配置项覆盖全局 config：

- LogConfig: Dir、Loggers
- DebugConfig
- RemoteConfigCenter
- RuntimeMetricConfig

#### 注意

业务代码主动调用 `config.Init()` 会导致 Server 初始化的 userDefinedInitializer 失效（因为 `config.Init()` 使用 sync.Once 保证全局 config 只初始化一次）。

在这种情况下需要：
- 确认 server 未使用方式 2 构造自定义配置
- 或将其改造为方式 1，先 `AddInitializer`，然后再调用 `config.Init()`

## 自定义配置

如需要自定义配置，可在 conf 目录下添加另一个 yaml 文件，并调用 Kitex 提供的 API 加载。

### 示例 1：在默认配置文件里自定义其他配置项

1. 在原配置里新增配置项：

```yaml
Address: ":8888"
EnableDebugServer: true
# ... 其他配置 ...

RedisCluster: "xxx"  # 新增的自定义配置
```

2. 解析 yml 并获取配置项：

```go
import "github.com/cloudwego/kitex/pkg/utils"

conf, err := utils.ReadYamlConfigFile(utils.GetConfFile())
if err != nil {
    fmt.Println("load failed, err =", err)
    return
}
value, exists := conf.Get("RedisCluster")
if exists {
    fmt.Println(value)
} else {
    fmt.Println("(not set)")
}
```

### 示例 2：自定义新配置文件

1. 新增配置文件 `conf/business.yml`：

```yaml
Min: 100
Max: 500
```

**注**：Kitex 的 build.sh 会将 `conf/*` 拷贝到 `output/conf/*`。

2. 获取配置目录并构造完整路径：

```go
import "github.com/cloudwego/kitex/pkg/utils"

confFile := utils.GetConfDir() + "/business.yml"
```

3. 使用工具完成解码：

```go
conf, err := utils.ReadYamlConfigFile(confFile)
if err != nil {
    fmt.Println("load failed, err =", err)
    return
}
value, exists := conf.Get("Min")
if exists {
    fmt.Println(value)
} else {
    fmt.Println("(not set)")
}
```

对于复杂需求（嵌套 map、默认值等），请使用自己实现的加载工具或第三方库。

## 常见问题

### Q: 项目只用了 Kitex Client，如何使用文件配置？

由于 Kitex Client 初始化时不会主动调用 `config.Init()`，因此不会加载文件配置。可以在 Client 初始化之前主动调用该方法：

```go
config.Init()
// 然后初始化 Client
```

### Q: 能支持不同环境加载不同的配置文件吗？

可以通过修改启动脚本实现，或使用环境变量 `KITEX_CONF_FILE` 指定不同的配置文件。

### Q: 默认 debug 端口是 18888 还是 address+10000？

根据环境来定：
- 如果有 `RUNTIME_SERVICE_PORT` 环境变量，则为 `RUNTIME_SERVICE_PORT + 10000`
- 否则默认为 18888

### Q: 配置里的 ReadWriteTimeout 是指什么？

指连接等待读写的最大 idle timeout，传给底层网络库 netpoll 使用，避免异常连接长时间 block goroutine。

### Q: 在 TCE 中运行，Address 端口的配置还会生效吗？

如果存在 `TCE_PRIMARY_PORT` 环境变量，会被该环境变量覆盖（即被 TCE 上设置的 primary 端口覆盖）。

### Q: 日志 Dir 配置项和 KITEX_LOG_DIR 环境变量哪个优先级更高？

环境变量 `KITEX_LOG_DIR` 的优先级更高，可在 bootstrap.sh 中修改。

### Q: 为什么日志没有得到自动清理？

TCE 会自动清理日志，但**只清理** `/opt/tiger/toutiao/log` 目录下的日志。

### Q: 日志的三种 Outputs 分别指什么？

| Output | 说明 |
|--------|------|
| File | 日志写入到文件（异步） |
| Console | 把日志写入到标准输出，在本地/测试环境便于调试 |
| Agent | 把日志写入到日志采集的 Agent，用于 Argos 等日志平台收集和分析日志 |

### Q: 是否可以通过环境变量指定配置目录的绝对路径？

可以，`KITEX_CONF_DIR` 环境变量支持设置绝对路径。

### Q: TCE 容器内服务进程监听的端口号和配置的端口号不一致？

TCE 有端口映射，进程实际监听的是映射后的端口。

### Q: Network 配置项是否支持 kcp？

暂不支持 kcp，只支持 tcp 和 unix。

### Q: 日志报错 open conf/kitex.yml: no such file or directory

检查配置文件是否存在，或通过环境变量 `KITEX_CONF_DIR` 和 `KITEX_CONF_FILE` 指定正确的路径。

### Q: 如何覆盖 TCE 环境变量指定的配置？

- **不建议这么做**，这会打破服务治理约定，可能引起未知问题
- 如果确实有必要，可以使用 userDefinedInitializers，优先级高于 EnvInitializer

## 相关文档

- [超时配置](./configure-timeout.md)
- [服务配置](./configure-service.md)
- [最佳实践](./best-practices.md)
