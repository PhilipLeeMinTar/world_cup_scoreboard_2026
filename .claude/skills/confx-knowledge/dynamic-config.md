# 动态配置特性详解

confx 的动态配置以函数字段形式声明，支持多种调用模式和丰富的特性，让业务能够轻松实现配置的热更新和实时监控。

## 函数声明模式

confx 支持三种动态配置函数模式，满足不同业务场景的需求：

### 1. 无默认值，无 error（常用）
如果最近一次读取失败或者解析失败，Fallback路径：上次成功的缓存 → 空返回值。

```go
AAA func() string `confx:"tcc:aaa"`
```

### 2. 有默认值，无 error（常用）
如果最近一次读取失败或者解析失败，Fallback路径：上次成功的缓存 → 默认值。默认值类型需要与返回值相同，在初始化阶段会做校验。

```go
AAA func(defaultValue string) string `confx:"tcc:aaa"`
```

### 3. 无默认值，有 error（不常用）
对于需要强感知最近配置加载/解析状态的情况，允许增加 error 返回值，这种情况下没有 Fallback 逻辑。

```go
AAA func() (string, error) `confx:"tcc:aaa"`
```

## 运行时指定 Key

支持在运行时动态指定配置 Key，可以将 `confx.Key` 作为函数参数（如果 default 参数存在则置于 default 之前），此时不能在 tag 标明 key。

```go
// confx.Key 实际上就是 string，为了与 string 默认值做区分，这里必须用 confx.Key 这个别名
AAA func(key confx.Key) string `confx:"tcc"`
```

**示例代码**：
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
    // 打印的结果可能是："hello world 123"
}
```

## 核心特性

### 深拷贝保护（deepcopy）
添加 `deepcopy` 关键字的动态配置项，会在每次函数返回时，返回一个深拷贝过的 value，避免暴露全局缓存，使得 value 既可读又可写。

**使用场景**：
- 防御型配置项，能防御类似修改全局变量的事故
- 业务在读到配置之后需要修改配置内容的场景

**注意事项**：
- 深拷贝有性能开销，大对象配置需谨慎使用
- 配置前要三思，根据业务需要选择是否使用

### 变化回调（callback）
添加 `callback` 关键字的配置项，会在配置每次更新时，触发回调。

**配置方式**：
```go
func updateMyValue(newValue int) {
    fmt.Println("Config value updated:", newValue)
}

confx.MustInit(
    conf, 
    confx.WithCallback(map[string]interface{}{
        "my_tcc_key": updateMyValue,
    })
)
```

### 初始化校验（required）
添加 `required` 关键字的配置项，会在初始化阶段完成读取和解析，有一项失败，则整个初始化按失败处理。

**使用场景**：
- 希望初始化阶段检查每个配置项都是已配置的状态
- 确保配置在服务启动时就解析就绪

## 刷新机制

### 默认刷新间隔
confx 默认每 10 秒刷新一次动态配置。

### 自定义刷新间隔
可以通过 `WithRefreshInterval` 选项设置自定义的刷新周期：

```go
confx.MustInit(
    conf,
    confx.WithRefreshInterval(30), // 30 秒刷新一次
)
```

### Fallback 逻辑
动态配置的 Fallback 顺序为：
1. 正常读到的值
2. 函数默认值（如果有）
3. 零值（如空字符串或 0）

## 性能优化建议

### 内存优化
- **大对象配置**：谨慎使用 `deepcopy`，避免不必要的性能开销
- **只读场景**：如果能确保配置只读，可不加 `deepcopy` 以减少内存拷贝

### 稳定性优化
- **TCC 参数**：合理配置 TCC 超时和重试参数保证稳定性
- **刷新间隔**：根据业务实际需求设置合理的刷新间隔，避免频繁刷新

## 错误排查

当 confx 获取到的配置与平台配置不符时，可按以下步骤排查：

1. **检查字段定义**：确认是否使用了 `func()` 声明，否则会被认定为静态配置
2. **使用工具检查**：使用 [TccConfChecker 命令行工具](https://bytedance.larkoffice.com/wiki/wikcn4g7HEP7TtNipNAwH0EfxHc) 在机器上获取配置，检查是否符合预期
3. **日志分析**：
   - 查服务日志，通过关键词 + TCC 发布时间段查 error 日志，关键词就是 confx
   - 访问 Grafana，检查是否有失败
4. **本地测试**：写个单测，检查 json.Unmarshal TCC 的配置是否报错
5. **配置修改检查**：确认业务是否在读到配置之后修改了配置内容，在未配置 `deepcopy` 的情况下，A goroutine 对配置对象做的改动会影响到 B goroutine 读到的内容

## 监控指标

confx 提供了内置的监控指标，可以通过 Grafana 查看：
- [监控面板](https://grafana.byted.org/d/dzyWO-3Gk)

**主要监控指标**：
- **Parse 数**：`gopkg.confx.$PSM.parse.throughput`
- **Load 数**：`gopkg.confx.$PSM.load.throughput`
- **Load 耗时**：`gopkg.confx.$PSM.load.latency`

## 最佳实践示例

```go
package main

import (
    "code.byted.org/gopkg/confx"
)

var tccConfig = &struct{
    // tcc 默认使用 json 解析，基础类型或者 json 结构体可省略解析器声明
    GetJsonConfig func() struct {
        Foo string `json:"foo"`
        Bar int    `json:"bar"`
    } `confx:"tcc:json_config"`
    
    GetEnableFeatureA func() bool `confx:"tcc:enable_feat_a"`
    // 配置读取失败或者解析失败情况下，允许使用用户填写的默认值作为返回值
    GetEnableFeatureB func(defaultValue bool) bool `confx:"tcc:enable_feat_b"`
}{}

func initTCCConfig() {
    confx.MustInit(
        tccConfig,
        // 默认每个配置项在获取时都完整深拷贝一份，这样得到的结果是可读可写的
        // 带来的性能开销取决于结构大小，如果能确保配置只读，可不加
        confx.WithDefaultDeepcopy(true),
        // 默认每个配置项都是已配置的状态，且在初始化阶段正常解析完毕
        confx.WithDefaultRequired(true),
    )
    println(tccConfig.GetEnableFeatureA()) // 打印 true
    println(tccConfig.GetEnableFeatureB(false)) // 打印 false
    println(tccConfig.GetJsonConfig().Bar) // 打印 456
}
```

## 与其他组件的对比

### 与 easyswitch 的差异
- **动态配置获取**：confx 支持更丰富的函数模式，包括带 error 返回值的模式
- **深拷贝特性**：confx 支持 `deepcopy` 关键字，避免数据竞争问题
- **刷新机制**：confx 提供更灵活的刷新间隔配置

### 与 prek/confx 的差异
- **动态值支持**：confx 通过 func field 提供更方便的动态配置支持，相比 prek/confx 的 TCCLoadInt64 等类型更加灵活
- **协议支持**：confx 支持 json、yaml 等多种协议，而 prek/confx 仅支持 yaml