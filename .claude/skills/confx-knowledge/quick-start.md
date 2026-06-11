# confx 快速入门指南

confx 是字节跳动内部的 Go 多数据源配置加载基础库，提供统一的配置管理能力，让业务代码专注于业务逻辑，无需关心具体的配置加载细节。

## 核心概念

### 静态配置与动态配置
- **静态配置**：初始化时一次性加载，适用于不经常变化的配置
- **动态配置**：支持定期刷新和变化回调，适用于需要实时更新的配置

### 关键组件
- **Loader**：从数据源获取内容的具体实现
- **Parser**：解序列化的具体实现
- **Entity**：代表一个conf实体，与特定的loader和load参数绑定
- **Block**：代表Conf结构体中第一层的成员，每个成员有完整的Loader和Parser及Param描述

## 安装

```shell
go get code.byted.org/gopkg/confx
```

## 基本用法

### 1. 静态配置示例
以下是从本地 yaml 文件加载静态配置的最佳实践：

```go
package main

import (
    "fmt"
    
    "code.byted.org/gopkg/confx"
    "code.byted.org/gopkg/env"
)

var Config = &struct {
    ServiceConfig struct {
        MongoDSN      string `yaml:"MongoDSN"`
        BizA          struct {
            AppID     string `yaml:"AppID"`
        } `yaml:"BizA"`
    } `confx:"file:service_conf"`
}{}

func initConfig() {
    region := env.Region()
    if region == "-" {
        region = env.R_BOE
    }
    // MustInit 没有返回值，发生error即panic
    confx.MustInit(
        Config, 
        confx.WithDefaultRequired(true), 
        confx.WithLoaderKeyMap(map[string]string{
            "service_conf": fmt.Sprintf("conf/service_config.%s.yml", region),
        }),
    )
}
```

### 2. 动态配置示例
以下是从 TCC 加载动态配置的最佳实践：

```go
package main

import (
    "code.byted.org/gopkg/confx"
)

var tccConfig = &struct{
    GetJsonConfig func() struct {
        Foo string `json:"foo"`
        Bar int    `json:"bar"`
    } `confx:"tcc:json_config"`
    
    GetEnableFeatureA func() bool `confx:"tcc:enable_feat_a"`
    GetEnableFeatureB func(defaultValue bool) bool `confx:"tcc:enable_feat_b"`
}{}

func initTCCConfig() {
    confx.MustInit(
        tccConfig,
        confx.WithDefaultDeepcopy(true),
        confx.WithDefaultRequired(true),
    )
    println(tccConfig.GetEnableFeatureA()) // 打印true
    println(tccConfig.GetEnableFeatureB(false)) // 打印false
    println(tccConfig.GetJsonConfig().Bar) // 打印456
}
```

## 配置声明语法

### 结构体标签格式
confx 使用 `confx:"{配置源}:{key}[, {解析器}][:{字段}]"` 的格式描述配置项：

```go
type Conf struct {
    // 外层fields需要通过confx tag描述
    A1 string `confx:"tcc:example_json,json:a"`
    A2 string `confx:"tcc:example_yaml,yaml:a"`
    Plain string `confx:"tcc:example"`
    
    // 支持jsonx.Any类型
    JSONB jsonx.Any `confx:"tcc:example_json, json:b"`
    
    // Struct fields
    JSONStruct struct {
        A string `json:"a"`
    } `confx:"tcc:example_json, json"`
    
    // Pointer fields
    A3 *string `confx:"tcc:example_yaml,yaml:a"`
    
    // Function fields - 动态配置
    A4 func() string `confx:"tcc:example_yaml,yaml:a"`
    
    // 带默认值的函数字段
    A5 func(defaultValue string) string `confx:"tcc:no_this_key,psm:p.s.m,yaml:a"`
}
```

## 初始化选项

confx 提供了丰富的初始化选项来满足不同场景的需求：

```go
confx.MustInit(
    conf,
    // 默认对每个配置项强校验
    confx.WithDefaultRequired(true),
    // 默认每个配置项都完整深拷贝一份
    confx.WithDefaultDeepcopy(true),
    // 设置Loader Key映射
    confx.WithLoaderKeyMap(map[string]string{
        "service_conf": "conf/service_config.yml",
    }),
    // 设置刷新间隔（秒）
    confx.WithRefreshInterval(30),
    // 启用调试模式
    confx.WithDebugMode(),
    // 设置实例名称
    confx.WithName("my-service-config"),
)
```

## 动态配置的三种模式

confx 支持三种动态配置函数模式：

### 1. 无默认值，无error（常用）
如果最近一次读取失败或者解析失败，Fallback路径：上次成功的缓存->空返回值。

```go
AAA func() string `confx:"tcc:aaa"`
```

### 2. 有默认值，无error（常用）
如果最近一次读取失败或者解析失败，Fallback路径：上次成功的缓存->默认值。

```go
AAA func(defaultValue string) string `confx:"tcc:aaa"`
```

### 3. 无默认值，有error（不常用）
对于需要强感知最近配置加载/解析状态的情况，允许增加error返回值。

```go
AAA func() (string, error) `confx:"tcc:aaa"`
```

## 运行时指定key

可以将 `confx.Key` 作为函数参数，在运行时动态指定读取哪个key的配置：

```go
package main

import "code.byted.org/gopkg/confx"

var exampleConfig = &struct {
    GetString func(key confx.Key) string `confx:"tcc"`
    GetIntDefault func(key confx.Key, defaultValue int) int `confx:"tcc"`
}{}

func Foo() {
    confx.MustInit(exampleConfig)
    println(
        exampleConfig.GetString("tcc_key0"), 
        " ",
        exampleConfig.GetIntDefault("tcc_key1", 0)
    )
}
```

## 关键字说明

### required
添加required关键字的配置项，会在初始化阶段完成读取和解析，有一项失败，则整个初始化按失败处理。

### deepcopy
添加deepcopy关键字的动态配置项，会在每次函数返回时，返回一个深拷贝过的value，避免暴露全局缓存，使得value既可读又可写。

### callback
添加callback关键字的配置项，会在配置每次更新时，触发回调。

## 常见使用场景

1. **从本地 yaml/json 文件加载配置**：如数据库 PSM 配置
2. **从 TCC 远程加载动态配置**：如开关状态配置
3. **从 KMS 加载加密配置**：如飞书机器人秘钥
4. **统一管理多环境配置**：通过环境变量区分不同环境的配置文件

## 下一步

掌握了快速入门的基础知识后，您可以进一步了解：
- 各种配置源（TCC、文件、环境变量等）的详细用法
- 动态配置的高级特性和最佳实践
- 如何扩展confx以支持自定义数据源和解析器

