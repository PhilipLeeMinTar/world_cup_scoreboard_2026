# 高级功能与最佳实践

## Mock 功能

confx 提供了完整的 Mock 功能，方便在测试中模拟配置。通过 `mock.NewBuilder` 可以创建 Mock 实例，支持对静态值和动态函数进行 Mock。

**使用示例**：
```go
import "code.byted.org/gopkg/confx/mock"

func TestMyFunction(t *testing.T) {
    conf := &struct {
        A string                  `confx:"env:TEST_A"`
        B func() string           `confx:"tcc:test_b"`
        C func(confx.Key) string  `confx:"tcc"`
        D func() string           `confx:"file:test_d"`
    }{}

    // 创建 Mock
    mocker := mock.NewBuilder(conf).
        MockValue(&conf.A, "mocked_value_a").           // Mock 静态值
        MockValue(&conf.B, "mocked_value_b").           // Mock 动态值
        MockFunc(&conf.C, func(key confx.Key) string {  // Mock 函数
            if key == "special_key" {
                return "special_value"
            }
            return "default_value"
        }).
        MockFunc(&conf.D, func() string {
            return "mocked_file_content"
        }).
        Build()

    // 使用 Mock 的配置
    assert.Equal(t, "mocked_value_a", conf.A)
    assert.Equal(t, "mocked_value_b", conf.B())
    assert.Equal(t, "special_value", conf.C("special_key"))
    assert.Equal(t, "default_value", conf.C("other_key"))
    assert.Equal(t, "mocked_file_content", conf.D())

    // 恢复原始状态
    mocker.Restore()
}
```

## Options 配置

confx 提供了丰富的初始化选项，用于定制配置加载行为。

### 常用 Options

**WithLoaderFactories**：当需要从 tcc、file、env 以外的地方读取配置时使用，比如从 kms、mysql 等地方获取配置。

```go
package main

import "code.byted.org/gopkg/confx/loader/kms"

var conf = &struct{
    UserName string `confx:"kms:user_name"`
}

func init() {
    confx.MustInit(conf, confx.WithLoaderFactories(kms.LoaderFactory()))
}
```

**自定义 LoaderFactory 示例**：
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
                // do some init
            }),
            func(param *loader.Params) loader.Loader {
                // get `myKey` from param.Key
                return loader.NewLoader(
                    func(context.Context) (interface{}, error) {
                        resp, err := DoSomeRPC(param.Key, param.Params["param1"])
                        return resp, err
                    },
                )
            },
        ),
    )
}
```

**WithParserFactories**：当需要自定义解析配置的方法时使用，比如使用了 json/yaml 以外的序列化类型。

```go
import "code.byted.org/gopkg/confx/parser"

func pbUnmarshal(data []byte, v interface{}) error {
    return proto.Unmarshal(data, v)
}

var conf = &struct{
    User UserStruct `confx:"file:./xxx.pb, protobuf"`
}{}

confx.MustInit(
    conf, 
    confx.WithParserFactories(
        parser.NewFactory(
            "protobuf",
            func(params *parser.Params) parser.Parser {
                return parser.NewParser(pbUnmarshal)
            },
        ),
    ),
)
```

**WithDefaultRequired / WithDefaultDeepcopy**：为每个字段默认设置 deepcopy 和 required 关键字的默认值。

```go
confx.MustInit(conf, confx.WithDefaultRequired(true))
```

**WithLoaderKeyMap**：当需要运行期指定 loader 的参数时，预先使用映射 key。

```go
confx.MustInit(
    conf,
    confx.WithLoaderKeyMap(map[string]string{
        "service_conf": fmt.Sprintf("conf/service_config.%s.yml", region),
    }),
)
```

**WithCallback**：设置配置更新后的回调，首次初始化不会回调。

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

**WithRefreshInterval**：设置动态配置的刷新周期，秒级，默认为 10s。

```go
confx.MustInit(
    conf,
    confx.WithRefreshInterval(30), // 30 秒刷新一次
)
```

**WithDebugMode**：启用调试模式，提供更详细的 INFO 日志。

```go
confx.MustInit(
    conf,
    confx.WithDebugMode(), // 启用调试模式
)
```

**WithName**：设置 confx 实例的自定义名称，用于指标和日志记录。

```go
confx.MustInit(
    conf,
    confx.WithName("my-service-config"),
)
```

## 性能优化建议

### 静态配置优化

- 使用 `required` 关键字进行初始化校验，确保配置在启动阶段就正确加载。

### 动态配置优化

- 根据业务需要选择是否使用 `deepcopy`。深拷贝是有性能开销的，配置前要三思。
- 合理设置刷新间隔 `WithRefreshInterval`，避免过于频繁的配置刷新。

### 内存优化

- 大对象配置谨慎使用 `deepcopy`，以避免性能问题。

### 稳定性优化

- 合理配置 TCC 超时和重试参数，保证配置加载的稳定性。

## 错误排查指南

### 配置获取与平台配置不符

如果 confx 获取到的配置与平台配置不符，可以按以下步骤排查：

1. **检查配置类型**：如果现象是服务启动后，配置未随 TCC 变更而更新，需要检查 confx 结构的字段定义是否用了 `func()`，否则会被认定为静态配置。

2. **使用工具检查**：使用 [TccConfChecker 命令行工具](https://bytedance.larkoffice.com/wiki/wikcn4g7HEP7TtNipNAwH0EfxHc) 在机器上获取配置，检查是否符合预期。

3. **如果符合预期而 confx 不符合**：
   - **可能发生了 json.Unmarshal 错误**：导致 fallback 到上次成功解析缓存的配置。排查步骤：
     1. 查服务日志，通过关键词 + TCC 发布时间段查 error 日志，关键词就是 confx
     2. 访问 Grafana，检查是否有失败
     3. 本地写个单测，检查 json.Unmarshal TCC 的配置是否报错
   - **可能业务在读到配置之后修改了配置内容**：由于 confx 默认使用全局变量作为动态配置返回结果，在未配置 deepcopy 的情况下，A goroutine 对配置对象做的改动会影响到 B goroutine 读到的内容。

## 配置监控

confx 提供了内置的监控指标，可以通过 Grafana 查看：

- [监控面板](https://grafana.byted.org/d/dzyWO-3Gk)

监控指标包括：
- **Parse 数**：`gopkg.confx.$PSM.parse.throughput` {name=$Name,field=$FieldName, loader=$LoaderFactory, parser=$ParserFactory, status =ok|error}
- **Load 数**：`gopkg.confx.$PSM.load.throughput` {name=$Name, loader=$LoaderFactory, updated =true|false, status= ok|not_found|error}
- **Load 耗时**：`gopkg.confx.$PSM.load.latency` {name=$Name, loader=$LoaderFactory, updated=true|false, status =ok|not_found|error}

## 设计原则

### 抽象概念

confx 的设计基于以下抽象概念：

![confx 模块依赖关系](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/a948cf8482c5422d9f529e5085ca7693~tplv-tika-image.image)

1. **loader.Factory & loader.Loader**：
   - Loader 不需要关心参数，仅接受 ctx 入参即可
   - 负责从数据源读取数据到字节数组

2. **parser.Factory & parser.Parser**：
   - Parser 不关心参数，有明确的 Parse 行为
   - 负责将字节数组解析为具体的数据结构

3. **Entity**：
   - 代表一个 conf 实体，与一个特定的 loader 和 load 参数绑定
   - 处理动态配置的定期读取、数值变化回调等公共逻辑
   - 同 Loader & 同 Param 的多个不同 Field 可以共享同一个 Entity，避免重复回源

4. **Block**：
   - 代表 Conf 结构体的某个 Field
   - 三种实现：ptrBlock，valueBlock，funcBlock
   - 每个 Block 都对应一个 Entity，多个 Block 允许对应同个 Entity

### 初始化规则

1. **Init 函数行为**：
   - 只有存在 confx tag 的 block 才处理，其他忽略
   - 如果任一个 Block 首次获取配置失败且默认值为空且有 required 标记，则返回 err
   - Parse 失败也会返回 err，此时忽略 required 标记
   - Block 的值 fallback 顺序：正常读到的值 -> func 默认值(如果有) -> 零值
   - 如果存在 confx tag，则一定要有 loader 和 parser，如果没有且没有默认 loader/parser 就报错

2. **关键字处理**：
   - confx 库有关键字的概念，会对关键字做冲突检查
   - 预定义关键字包含：required、callback（block 属性关键字），json、yaml、plain、tcc、file、env（loader/parser 关键字）
   - 用户自定义的 loader 或者 parser 名字会作为自定义关键字存在

## 与其他组件的对比

### confx vs easyswitch

**差异点**：

| Feature               | easyswitch                                  | confx                                              | 差异程度 |
| --------------------- | ------------------------------------------- | -------------------------------------------------- | -------- |
| tcc默认PSM            | 继承自前面的field                           | 默认env.PSM()                                      | 部分支持 |
| 支持主动RefreshValue  | 提供RefreshValue主动刷数据                  | 暂不支持，仅支持定时刷新                           | 部分支持 |
| 支持数组解析          | 数组默认json反序列化，也支持split tag       | 支持json/yaml的数组解析，split需要用户自定义parser | 部分支持 |
| deepcopy特性          | 支持                                        | 已支持                                             | 相同     |
| confspace特性         | WithConfspace(psm string, confspace string) | 支持单个block维度的tcc confspace tag               | 部分支持 |
| tcc v1                | 支持                                        | 不支持                                             | 完全不同 |
| 指针field支持动态更新 | 支持                                        | 考虑到要避免data race，暂不支持                    | 完全不同 |

**相同点**：
- 函数Field入参默认值
- 支持定时刷新
- ajson.Any field（confx 中为 jsonx.Any）
- json/yaml反序列化
- callback特性
- 自定义loader/parser

### confx vs prek/confx

**差异点**：

| Feature              | prek/confx                       | confx                                       | 差异程度 |
| -------------------- | -------------------------------- | ------------------------------------------- | -------- |
| kite/ginex框架配置   | 原生支持                         | 可通过增加loader支持，但不默认集成          | TODO     |
| tcc动态值支持        | 通过confx.TCCLoadInt64等类型支持 | 已支持更方便的func field                    | 完全不同 |
| WithPPEPrefix        | WithPPEPrefix(prefix string)     | 不支持，尽量引导用户使用tcc固有的多环境能力 | 完全不同 |
| 单File支持多环境配置 | WithSingleFileMod(b bool)        | 可通过增加parser支持，但不默认集成          | TODO     |
| field读取失败处理    | Init失败                         | 只有required标记的field失败才导致Init失败   | 部分支持 |

## 常见问题解答

### 怎么通过环境变量加载不同的config文件？

参考最佳实践中的读静态配置，使用 `WithLoaderKeyMap` 动态指定文件路径。

```go
confx.MustInit(
    Config,
    confx.WithLoaderKeyMap(map[string]string{
        "service_conf": fmt.Sprintf("conf/service_config.%s.yml", region),
    }),
)
```

### 想运行期间指定访问哪个key？

参考运行时指定 key 功能，使用 `confx.Key` 参数。

```go
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

### 配置获取与平台配置不符？

按错误排查指南中的步骤进行排查。

