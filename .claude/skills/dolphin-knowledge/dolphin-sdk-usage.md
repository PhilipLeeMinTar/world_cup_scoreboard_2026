# Dolphin SDK使用指南

## 概述

Dolphin SDK提供Go和Rust两种语言的接入方式，支持动态规则决策和业务逻辑配置。SDK基于高性能规则执行引擎实现，通过RPC异步获取规则和配置，规则在本地执行，提供低延迟的决策能力。

## Go SDK接入（V3版本）

### 为什么建议接入最新版本？

- **性能优化**：新版本有更好的性能、更低的资源开销；线上测试，CPU优化30%+
- **问题修复**：新版本进行了一些历史问题的修复和异常表现的修正
- **引擎升级**：底层引擎切换，支持更强大的语法和脚本能力

### 依赖引入

```shell
go get code.byted.org/dolphin/go-dolphin/v3

# 如果需要特定版本或者使用 alpha & beta 版本的话 需要额外指定版本号 e.g.
go get code.byted.org/dolphin/go-dolphin/v3@v3.2.0-beta.1
```

### 经典版接入示例

```go
package example

import (
    goDolphinV3 "code.byted.org/dolphin/go-dolphin/v3"
    "code.byted.org/dolphin/go-dolphin/v3/config"
    "code.byted.org/gopkg/logs"
    "context"
    "time"
)

var (
    // DolphinCli Dolphin Client, 建议作为全局变量使用
    DolphinCli *goDolphinV3.DolphinClient
)

// InitDolphin 初始化Dolphin Client
func InitDolphin() error {
    // 确定需要初始化的业务线和事件列表
    dolCfg := config.NewDefaultDolphinConfig("test", []string{"test"})
    
    // 初始化一个 Option
    option := config.NewDolphinOption()
    option.SetLogLevel(logs.LevelWarn) // 设置日志的等级
    
    // 定义Dolphin Client
    DolphinCli, err = goDolphinV3.NewDolphinClient(dolCfg, option)
    if err != nil {
        logs.Error("NewDolphinClient failed. err=%v", err)
        return err
    }

    // init dolphin client
    err = DolphinCli.Init()
    if err != nil {
        logs.Error("Init DolphinClient failed. err=%v", err)
        return err
    }

    return nil
}

// GetDecisionDemo 执行示例
func GetDecisionDemo(ctx context.Context) {
    // execute BasicJudge with dolphin client
    req := &goDolphinV3.BasicJudgeRequest{
        Bizline:    "test",
        Event:      "test",
        EventTime:  time.Now().Unix(),
        ParamsJSON: `{"name":"jack"}`,
    }

    // 直接获取决策结果
    resp, err := DolphinCli.BasicJudge(ctx, req)
    if err != nil {
        logs.CtxError(ctx, "BasicJudge failed. err=%v", err)
    } else {
        logs.CtxInfo(ctx, "resp=%v", resp)
    }
}
```

### 响应结构

```go
type BasicJudgeResponse struct {
    ResultJson       map[string]interface{} `json:"ResultJSON"`       // 所有节点的输出合并
    FinalResult      map[string]interface{} `json:"FinalResult"`      // 指向结束的节点输出合并
    HitMap           map[int64]*RuleStatus  `json:"HitMap"`           // 规则命中信息
    LatestVersion    int64                  `json:"LatestVersion"`    // 最新的版本号
    DeleteTargetKeys []string               `json:"DeleteTargetKeys"` // 删除目标键
    ExecDetail       *ExecDetail            `json:"ExecDetail"`       // 执行细节
}
```

### Lite版接入

关于lite和经典版的区别以及选择，参考 [关于Dolphin-lite](https://bytedance.larkoffice.com/wiki/W86ZwzZ9IiTYjLkc7jNcz7ZHnnh)

```go
// InitDolphin 初始化Dolphin Client
func InitDolphin() error {
    // 确定需要初始化的业务线
    dolCfg := config.NewLiteDolphinConfig("test_lite")
    
    // 如果需要按照策略标签加载规则
    // dolCfg := config.NewLiteDolphinConfigWithTags("test_lite", []string{"tagA"})
    
    // 初始化一个 Option
    option := config.NewDolphinOption()
    option.SetLogLevel(logs.LevelWarn)
    
    // 定义Dolphin Client
    DolphinCli, err = goDolphinV3.NewDolphinClient(dolCfg, option)
    if err != nil {
        logs.Error("NewDolphinClient failed. err=%v", err)
        return err
    }

    // init dolphin client
    err = DolphinCli.Init()
    if err != nil {
        logs.Error("Init DolphinClient failed. err=%v", err)
        return err
    }

    return nil
}
```

## Rust SDK接入

### 依赖引入

```json
// 建议使用最新版本，可以自行锁定版本比如： version = "0.1"
rust-dolphin = { version = "*", registry = "crates-byted"}
```

### 示例代码

```rust
use faststr::FastStr;
use rust_dolphin::client::{BasicJudgeRequest, ClientBuilder, DolphinClient};
use std::time::{SystemTime, UNIX_EPOCH};

struct Service {
    // dolphin client
    dolphin_cli: DolphinClient,
}

impl Service {
    pub async fn new() -> Self {
        // build client
        let client = ClientBuilder::new(FastStr::new("test"), vec![FastStr::new("test_rs")], None)
            .with_rule_execute_log_sample(10)
            .build_client()
            .expect("Build client failed");

        // init client
        client.init_async().await.expect("Init client failed");

        Self {
            dolphin_cli: client,
        }
    }

    pub fn get_dolphin_client(&self) -> &DolphinClient {
        &self.dolphin_cli
    }
}

#[tokio::main]
async fn main() {
    let service = Service::new().await;

    let request = BasicJudgeRequest {
        bizline: FastStr::new("test"),
        event: FastStr::new("test_rs"),
        event_time: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("Failed to get timestamp")
            .as_secs(),
        params: FastStr::new(r#"{"uid": 123, "did": 456}"#),
        env: None,
        options: None,
    };

    match service.get_dolphin_client().basic_judge(request).await {
        Ok(res) => {
            println!("Invoke Dolphin Get {:?}", res.result)
        }
        Err(err) => {
            println!("Invoke Dolphin Failed:{}", err)
        }
    };
}
```

### 开发问题

**编译报错**
```
error: could not find native static library `rule_engine_aarch64_macos`, perhaps an -L flag is missing?
```

可以临时在最外层项目的Cargo.toml中增加：

```rust
[patch.crates-byted]
uren = {git = "https://code.byted.org/risk_control/uren", branch ="release" }
```

## 性能测试

Rust引擎性能测试结果：

![rust引擎性能测试](https://p-tika-sg.tiktok-row.net/tos-alisg-i-tika-sg/2829a1f285314576a1d586daf54fb40a~tplv-tika-image.image)

## Options配置说明

Go SDK提供了丰富的配置选项：

```go
// EnableEngineUpgradeContrast 升级引擎需要采集数据
func (opt *Options) EnableEngineUpgradeContrast()

// SetRuleRefreshInterval 设置规则刷新时间, 默认20s
func (opt *Options) SetRuleRefreshInterval(t time.Duration) 

// SetDolphinDBCacheOption 设置加载规则RPC选项
func (opt *Options) SetDolphinDBCacheOption(idc, cluster string, timeout time.Duration) 

// EnableHttpLoad 设置加载规则Http选项
func (opt *Options) EnableHttpLoad(host string, timeout time.Duration)

// SetLogLevel 配置log级别
func (opt *Options) SetLogLevel(level int) 

// EnableAutoLoadBackupFile 开启自动加载容灾文件
func (opt *Options) EnableAutoLoadBackupFile()
```

## 使用建议

1. **初始化时机**：建议在服务框架初始化之前初始化Dolphin client
2. **全局变量**：Dolphin Client建议作为全局变量使用
3. **错误处理**：初始化失败时应记录详细日志并返回错误
4. **性能监控**：建议开启日志记录和性能监控
5. **容灾配置**：生产环境建议配置容灾方案，确保服务可用性

## 参考文档

- [Dolphin 引擎切换兼容性说明](https://bytedance.larkoffice.com/wiki/DXTAwUy4Uiu1Y7kXM88cPoBRnef)
- [Dolphin SDK 引擎升级操作手册（用户版）](https://bytedance.larkoffice.com/wiki/KKL4w4D4eivP0kkfkXYcvYPUntO)
- [关于Dolphin-lite](https://bytedance.larkoffice.com/wiki/W86ZwzZ9IiTYjLkc7jNcz7ZHnnh)
- [SDK 容灾降级](https://bytedance.larkoffice.com/wiki/Nl23wlTq7iYga1kCoNqcAPfOnGd)

