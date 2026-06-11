# TCC Golang SDK 使用说明

TCC（动态配置中心）是字节跳动内部的配置管理服务，提供配置的动态下发和实时更新能力。

## SDK 选型指南

TCC 有两个主要的 Golang SDK：

| SDK | 适用范围 | go mod path | 推荐版本 |
|-----|----------|-------------|----------|
| TCC V2 正式版 SDK | 访问 TCC V2/V3 配置 | `code.byted.org/gopkg/tccclient` | >= v1.6.2 |
| TCC V3 正式版 SDK | 访问 TCC V3 配置 | `code.byted.org/gopkg/tccclient/v3` | >= v3.0.0 |

## TCC V2 SDK 使用

### 安装

```shell
go get code.byted.org/gopkg/tccclient
```

> `code.byted.org/gopkg/tccclient` 正式版本（≤ 1.4.19 或 ≥ 1.6.2）的 ClientV2 同时支持读取 TCC V2、TCC V3 配置，是当前读取 TCC V3 配置时最稳定、适用性最佳的版本。

### 基础用法

```go
import (
    "context"
    "code.byted.org/gopkg/tccclient"
)

func main() {
    ctx := context.Background()

    // 创建配置
    config := tccclient.NewConfigV2()
    config.Confspace = "default"

    // 创建客户端
    clientV2, err := tccclient.NewClientV2("your.service.name", config)
    if err != nil {
        panic(err)
    }

    // 读取配置
    value, err := clientV2.GetConfig(ctx, "config_key")
    if err != nil {
        // 处理错误
    }
}
```

### 日志控制

TCC SDK 可能会输出 `context deadline exceeded` 日志，这属于正常行为。如需减少日志数量，请升级到 `>= v1.2.32` 版本，并使用以下方法：

#### 方法一：SetLogMode

```go
config := tccclient.NewConfigV2()
config.Confspace = "default"
config.SetLogMode(tccclient.HighMode)  // 设置日志模式

clientV2, err := tccclient.NewClientV2("your.service.name", config)
```

日志模式说明：

| 参数 | 效果 |
|------|------|
| `tccclient.LowMode` | 60s 时间窗口，前 4 次不打印，后续打印 |
| `tccclient.MediumMode` | 300s 时间窗口，前 4 次不打印，后续打印 |
| `tccclient.HighMode` | 300s 时间窗口，前 2 次不打印，后续打印 |
| `tccclient.AlwaysMode` | 所有错误日志都打印 |
| `tccclient.ForbiddenMode` | 不打印错误日志 |

#### 方法二：SetLogCounter

```go
import "time"

config := tccclient.NewConfigV2()
config.Confspace = "default"
// 在 200s 时间窗口内，前 2 次错误不打印，后续打印
config.SetLogCounter(3, 200*time.Second)

clientV2, err := tccclient.NewClientV2("your.service.name", config)
```

参数说明：

| 参数 | 说明 |
|------|------|
| `triggerLogCount int` | 时间窗口内前 n-1 次错误不打印，后续打印 |
| `triggerLogDuration time.Duration` | 时间窗口大小 |

## TCC V3 SDK 使用

### 安装

```shell
go get code.byted.org/gopkg/tccclient/v3
```

### 基础用法

```go
import (
    "context"
    tccclientv3 "code.byted.org/gopkg/tccclient/v3"
)

func main() {
    ctx := context.Background()

    // 创建 V3 客户端
    clientV3, err := tccclientv3.NewClientV3("your.service.name", nil)
    if err != nil {
        panic(err)
    }

    // 读取配置（需要指定目录和配置名）
    value, err := clientV3.GetConfig(ctx, "dir_name", "config_name")
    if err != nil {
        // 处理错误
    }
}
```

## 升级指南

### 从 alpha/beta 版本升级

如果你使用了以下 alpha/beta 版本，需要升级到正式版：

- `v1.5.0-beta.*`
- `v1.5.0-alpha.*`
- `v1.4.13`（意外泄露版本）

#### 升级方案

根据使用情况选择升级方案：

1. **仅使用 ClientV2**：升级到 TCC V2 正式版 SDK
   ```shell
   go get code.byted.org/gopkg/tccclient
   ```

2. **仅使用 ClientV3**：升级到 TCC V3 正式版 SDK
   ```shell
   go get code.byted.org/gopkg/tccclient/v3
   ```

3. **同时使用 ClientV2 和 ClientV3**：需要同时引入两个 SDK
   ```shell
   go get code.byted.org/gopkg/tccclient
   go get code.byted.org/gopkg/tccclient/v3
   ```

### 破坏性变更说明

#### V3 方法签名变更

从 `1.5.0-beta.xx` 升级到 `v3.0.0` 时，涉及 Key 的方法签名有变化：

```go
// 旧版本（beta）：Key 手动拼接
value, err := clientV3.GetConfig(ctx, "/some/dir/config_name")

// 新版本（v3.0.0）：Dir 和 ConfigName 分开
value, err := clientV3.GetConfig(ctx, "some/dir", "config_name")
```

这个变更是为了支持配置名称中包含 `/` 的场景。

## 缓存机制

TCC SDK 自带缓存功能，默认无过期设置以提升可用性。这可能导致在某些极端情形下缓存长时间未刷新。

如果业务对此敏感，建议主动进行监控配置。

## Getter 接入（Agent 编码参考）

> 本节为补充：Agent 在 Golang 服务中用 `ClientV2` 读结构化配置时遵循。优先对齐仓库既有写法。

### 模型

| 组件 | 职责 |
|------|------|
| `ClientV2` | 连接、拉取、缓存配置字符串 |
| `Getter` / `CastGetter` | 按 key 解析；version 不变时复用解析结果 |

### 编码规则

1. 每个 service + confspace：一个包级 `ClientV2`（`init` 或 init 函数创建）。
2. 每个稳定 key：一个包级 `NewGetter` / `NewCastGetter`。
3. Hot path：只调用 `getter(ctx)` + 类型断言；unmarshal / cast 写在 getter 定义处。
4. 新接入结构化配置：使用 `NewGetter` / `NewCastGetter`（与仓库一致时可沿用 `GetConfig`）。
5. AB / 多 key：每个 key 预建 getter；运行时选择 getter 再调用。
6. getter 返回 map / slice / struct 作只读；修改前拷贝；`NewGetter` 默认值类型与封装函数的类型断言一致（仓库内 struct 多用 `&T{}`，断言 `*T`）。
7. 封装流程：`getter(ctx)` → 类型断言（与 `NewGetter` 默认值同指针/值类型）→ 内容校验 → fallback / log。
8. PPE / BOE：log key、配置内容、error；prod 按需 debug log。
9. 单测：正常读、getter 失败 fallback、AB 选 key、空 / 非法配置。

### 代码模板（`ClientV2`）

**包级 client + getter 初始化**

```go
var tccClient *tccclient.ClientV2
var featureConfigGetter tccclient.Getter

func initTCC() error {
    cfg := tccclient.NewConfigV2()
    cfg.Confspace = "default"
    c, err := tccclient.NewClientV2("your.service.psm", cfg)
    if err != nil {
        return err
    }
    tccClient = c
    featureConfigGetter = tccClient.NewGetter("feature_config", sonic.Unmarshal, &FeatureConfig{})
    return nil
}
```

**请求封装**

```go
func GetFeatureConfig(ctx context.Context) (*FeatureConfig, error) {
    res, err := featureConfigGetter(ctx)
    if err != nil {
        return nil, err
    }
    conf, ok := res.(*FeatureConfig)
    if !ok || conf == nil {
        return nil, fmt.Errorf("tcc feature_config: type cast failed")
    }
    return conf, nil
}
```

**标量：`NewCastGetter`**

```go
thresholdGetter = tccClient.NewCastGetter(
    "threshold_key",
    tccclient.DummyUnmarshal,
    "",
    func(val interface{}) interface{} {
        s, _ := val.(string)
        return conv.Int64Default(s, 0)
    },
)
```

**AB / 多 key**

```go
var ruleGetterV1, ruleGetterV2 tccclient.Getter
// init: 分别为 rule_v1、rule_v2 创建 getter
// runtime: 按条件选 getter，再 getter(ctx)
```

### Bad Case：运行时创建 getter

以下写法均视为 **运行时创建 getter**（Agent 生成代码时禁止出现在 Hot path / 请求函数内）：

| 模式 | 说明 |
|------|------|
| 请求内 `NewGetter` / `NewCastGetter` | 每次请求、每次调用封装函数时新建 getter |
| 请求内 `client.NewGetter(...)(ctx)` | 匿名创建 getter 并立刻调用 |
| AB 分支内按 key 动态 `NewGetter` | 根据 AB 结果拼 key 再 `NewGetter`，而非选用已注册的 getter |
| 循环 / 定时任务内重复 `NewGetter` | 非 init 阶段反复构造 getter |

**正确做法**：`NewGetter` / `NewCastGetter` 仅在包初始化阶段执行一次；运行时只做 `getter(ctx)` 或在多个**已注册**的包级 getter 之间选择。

**与 AB 的边界**：运行时可以选择「用 `ruleGetterV1` 还是 `ruleGetterV2`」；运行时不能 `NewGetter("rule_" + suffix, ...)`。

### 实现后自检

- [ ] `ClientV2`、各 key getter 均为包级单例
- [ ] Hot path / 请求函数内无 `NewGetter` / `NewCastGetter`（无运行时创建 getter，见上节 Bad Case）
- [ ] AB 已预注册各 key 的 getter
- [ ] 封装含断言、内容校验、fallback（`NewGetter` 默认值与 `res.(T)` / `res.(*T)` 一致）

### 排查清单

1. key、confspace、环境配置、AB 选中的 getter
2. getter 是否在包级初始化（非请求内创建）
3. 配置 JSON 与 Go 结构是否一致
4. pprof 反序列化热点：getter 单例、配置对象大小、调用频率

## 已封禁版本

以下版本存在已知 bug，已通过血缘平台封禁，**严禁在生产环境中使用**：

| SDK | 封禁版本 |
|-----|----------|
| `code.byted.org/gopkg/tccclient` | v1.4.18, v1.4.13, v1.5.0-beta.10, v1.5.0-beta.9, v1.5.0-beta.8, v1.5.0-alpha.1 ~ v1.5.0-alpha.19 |

## 参考资料

- [TCC V2 SDK CHANGELOG](https://code.byted.org/gopkg/tccclient/blob/master/CHANGELOG.md)
- [TCC V2 SDK README](https://code.byted.org/gopkg/tccclient/blob/master/README.md)
- [TCC V3 SDK CHANGELOG](https://code.byted.org/gopkg/tccclient/blob/v3/CHANGELOG.md)
- [TCC V3 SDK README](https://code.byted.org/gopkg/tccclient/blob/v3/README.md)
- [TCC V3 服务控制台](https://cloud.bytedance.net/tcc/namespace)
