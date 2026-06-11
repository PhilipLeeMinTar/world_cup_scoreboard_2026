# 配置源支持

confx 支持多种配置数据源，包括默认集成的 TCC、文件、环境变量，以及可通过扩展引入的 KMS、Byteconf 等。每种数据源都有特定的参数和用法，满足不同场景的需求。

## 默认集成的数据源

confx 默认集成了以下三种数据源：

1. **TCC** - 字节跳动内部的配置中心服务
2. **File** - 本地文件配置
3. **Env** - 环境变量配置

## TCC 配置源

TCC 是字节跳动内部的配置中心服务，confx 提供了完整的 TCC 支持，包括 TCC V2 和 V3 版本。

### 基本用法

TCC 配置源的基本用法如下：

```go
var tccConfig = &struct{
    GetJsonConfig func() struct {
        Foo string `json:"foo"`
        Bar int    `json:"bar"`
    } `confx:"tcc:json_config"`
    
    GetEnableFeatureA func() bool `confx:"tcc:enable_feat_a"`
    GetEnableFeatureB func(defaultValue bool) bool `confx:"tcc:enable_feat_b"`
}{}
```

### 参数说明

TCC 配置源支持以下参数：

1. **psm** - 指定读取某个 PSM 下的 TCC 配置。如果当前进程所在的 TCE PSM 与待读取的 TCC PSM 相同，可省略此参数。

```go
var tccConfig = &struct {
    EnableFeatureA func() bool `confx:"tcc:enable_feat_a, psm:demo.a.b"`
}
```

2. **confspace** - 指定读取某个 confspace 下的配置（仅供 TCC V2 使用），默认值为 `default`。

```go
var tccConfig = &struct {
    EnableFeatureA func() bool `confx:"tcc:enable_feat_a, confspace:abc"`
}
```

3. **path** - 指定某个 path 下的配置（**仅供 TCC V3 使用**），默认值为 `/default`。这个 path 是到目录级别。

![TCC V3 路径示例](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/43b646b27a1a413795c4ff39497da249~tplv-tika-image.image)

```go
var tccConfig = &struct {
    EnableFeatureA func() bool `confx:"tcc:sub_dir_config, path:/custom/sub_dir"`
}
```

4. **cli_version** - 显式指定使用 TCC V3 客户端。

```go
var tccConfig = &struct {
    EnableFeatureA func() bool `confx:"tcc:enable_feat_a, cli_version:v3"`
}{}
```

### 自动版本检测

confx 支持 TCC 版本自动检测：

- 如果配置了 `path` 参数，或者全局配置了 `WithTCCV3()` Option，系统会自动使用 TCC V3 客户端，无需显式指定 `cli_version:v3`。
- 如果以上三者均未配置，confx 会用 tccclient V2 的兼容模式读配置，此时配置无论是在 V2 还是 V3 的 `/default` 目录，都能读到。

### TCC 全局配置选项

confx 提供了以下 TCC 相关的全局配置选项：

1. **WithTCCV3()** - 全局启用 TCC V3。

```go
confx.MustInit(
    tccConfig,
    confx.WithTCCV3(), // 全局启用 TCC V3
)
```

2. **WithTCCDefaultPSM(psm)** - 设置默认 PSM。

```go
confx.MustInit(
    tccConfig,
    confx.WithTCCDefaultPSM("my.service.psm"), // 设置默认 PSM
)
```

3. **WithTCCInitConfig(config)** - 配置 TCC 初始化参数。

```go
confx.MustInit(
    tccConfig,
    confx.WithTCCInitConfig(confx.TCCInitConfig{
        FirstTimeoutSecond: 15, // 首次获取超时时间（秒）
        FirstRetryTimes:    3,  // 首次获取重试次数
    }),
)
```

## 文件配置源

文件配置源支持从本地文件加载配置，支持 JSON、YAML 等格式。

### 基本用法

```go
var Config = &struct {
    ServiceConfig struct {
        MongoDSN string `yaml:"MongoDSN"`
        BizA struct {
            AppID string `yaml:"AppID"`
        } `yaml:"BizA"`
    } `confx:"file:service_conf"`
}{}
```

### 文件路径映射

可以使用 `WithLoaderKeyMap` 动态指定文件路径，特别适用于多环境配置场景。

```go
confx.MustInit(
    Config,
    confx.WithLoaderKeyMap(map[string]string{
        "service_conf": fmt.Sprintf("conf/service_config.%s.yml", region),
    }),
)
```

## 环境变量配置源

环境变量配置源支持从系统环境变量读取配置。

### 基本用法

```go
var conf = &struct{
    FieldA1 string `confx:"env:fieldA"`
}
```

## Byteconf 配置源

Byteconf 配置源需要 confx 版本 >= v0.8.0，并需要额外引入。

### 引入方式

```go
import "code.byted.org/gopkg/confx/loader/byteconf"

var byteconfConfig = &struct {
    UserName  func() string `confx:"byteconf:user_name, namespace:my_namespace, path:/user"`
    UserEmail func() string `confx:"byteconf:user_email, namespace:my_namespace, path:/user"`
    // 支持决策树场景
    Decision  func(byteconf.Decision) *DecisionModel `confx:"byteconf:decision_key, namespace:my_namespace, path:/"`
}{}
```

### 参数说明

- **namespace** - 必填，指定命名空间
- **path** - 可选，指定路径，默认为根路径 "/"

## KMS 配置源

KMS 配置源需要通过 `WithLoaderFactories` 引入。

### 引入方式

```go
import "code.byted.org/gopkg/confx/loader/kms"

var conf = &struct{
    UserName string `confx:"kms:user_name"`
}

func init() {
    confx.MustInit(conf, confx.WithLoaderFactories(kms.LoaderFactory()))
}
```

## 自定义配置源

confx 支持通过 `WithLoaderFactories` 引入自定义配置源。

### 自定义 LoaderFactory 示例

```go
package main

import (
    "code.byted.org/gopkg/confx"
    "code.byted.org/gopkg/confx/loader"
)

var conf = &struct{
    Foo func() string `confx:"myLoader:myKey, param1:value1"`
}{}

func Init() {
    confx.MustInit(
        conf,
        confx.WithLoaderFactories(
            loader.NewFactory(
                "myLoader",
                func() error {
                    // 初始化逻辑
                    return nil
                },
                func(param *loader.Params) loader.Loader {
                    // 根据参数创建 Loader
                    return loader.NewLoader(
                        func(context.Context) (interface{}, error) {
                            resp, err := DoSomeRPC(param.Key, param.Params["param1"])
                            return resp, err
                        },
                    )
                },
            ),
        ),
    )
}
```

## 配置源选择规则

1. **数据源唯一性** - 每个字段只能指定一个数据源（file、env、flag、tcc、kms 五选一）
2. **嵌套一致性** - 嵌套结构体的情况下，内外数据源必须一致
3. **协议一致性** - 嵌套结构体的情况下，内外协议必须一致

## 使用场景建议

- **TCC** - 适用于需要动态更新、多环境管理的配置场景
- **File** - 适用于静态配置、本地开发环境
- **Env** - 适用于容器化部署、环境变量注入场景
- **Byteconf** - 适用于需要决策树等高级配置功能的场景
- **KMS** - 适用于需要加密存储的敏感配置（如秘钥、凭证等）

## 注意事项

1. **TCC 参数顺序** - 在 struct tag 定义中，配置源参数列表必须紧跟配置源信息之后。即：`confx:"tcc:{key}, psm:{psm}"` 而不是 `confx:"psm:{psm}, tcc:{key}"`
2. **默认 PSM** - 如果不配置 PSM 参数，默认使用 `env.PSM()`
3. **文件后缀推断** - 对于文件配置源，如果文件后缀名是 `.yml` 或 `.yaml`，会自动推断使用 YAML 解析器，除非后缀名与 format 方法不符，才需要显式指定

