# Abtest SDK 使用指南

Abtest SDK 是字节跳动内部用于接入 Libra A/B 实验平台的 Golang SDK，封装了与 Libra 分流服务的 RPC 交互、实验参数解析等底层逻辑，为开发者提供简洁的实验参数读取接口。

## 快速接入

### 准备阶段
Libra 已为接入 SDK 的各个 PSM 实现了自动注册配置空间的能力，业务侧对"配置空间"无感知。若业务方与下游存在交互验证，仍需要手动开启配置空间：
1. 为 PSM 对应的配置空间命名（建议和 repo 名称对应）
2. 联系平台完成初始化配置

### SDK 配置（必选）
推荐创建独立的 Client 实例进行配置：

```go
import "code.byted.org/iesarch/abtest/ab"

options := []ab.Option{
    ab.DesignationMode(ab.LibraNamespaceOpti), // 必须！使用 Libra 推荐的 namespace 优化
    ab.EnableNsReveal(), // 开启本地兜底，保障线上业务安全
}
AbClient := ab.MustNewClient(options...)
```

**重要注意事项**：
- SDK 配置应在**进程级别**生效，避免在公共库（common lib）中配置
- 确保实验参数（abparam）的 key 中不包含 "." 字符，或使用自定义分隔符

## 使用场景与接入方式

### 直接与 Libra 交互的服务
场景描述：需要直接请求 vm_framed 分流服务时使用此方式。

**接入步骤**：
1. 参考 Direct Service (Http) 接入 AbTest SDK 文档
2. 初始化 AbTest 对象，管理全部的 AB 数据

### 间接与 Libra 交互的服务
场景描述：不期望直接请求 vm_framed 分流服务，根据上游传递的 AB 结果继续读取实验结果。

**接入步骤**：
1. 使用兼容模式初始化 AbTest 对象
2. 增加 IDL 支持，通过上游传递的 AB 实验结果进行读取

## SDK 核心功能

### 实验参数读取
推荐以**切片形式**传递实验配置参数，避免使用 xxxHelp 方法：

```go
// 读取 int 型实验结果
func (abTest *AbTest) GetIntV(param []string, defaultVal int) int64 {}
```

**依赖 aweme/combo 包的抖音服务**：
- 老方式：调用 combo 包中的 `AbParam().GetAbTestValue()` 函数
- 新方式：调用 combo `AbParamNewAb().GetXxx()` 或 `GetXxxFromClient()` 函数

### 向下游传递 AB 参数
推荐调用 `TransferAbParam()` 函数向下传递 AB 实验结果，对应 IDL 接口。

**兼容方案**：
- 若无法改造 IDL，可参考兼容下游的传递方案
- 依赖 aweme/combo 包可短期/兼容使用 helper 方法

## 高级功能

### 双重验证
SDK 内部针对使用 SDK 接口读取的实验结果做双重校验，校验逻辑对一个实验参数只会执行一次。

**开启条件**：
- 需要当前环境处于 BOE、PPE 或者 online 的 canary
- 版本要求：>= v1.1.11

**验证效果**：
- 搜索 Error 日志关键字 "严重错误" 判断是否存在新老方式不相等的情况
- 在 Metrics 环境检索指标 `bytedance.abtest.sdk.value.not.equal.count`

### 本地安全兜底
SDK 在本地存在 OldAbJson（老数据）的情况下，允许业务侧使用老数据做安全兜底，避免遗漏实验配置参数造成线上问题。

**开启条件**：
- 确保服务处于优化模式：`LibraNamespaceOpti`
- 添加 `EnableNsReveal()` 配置项
- 版本要求：>= v1.1.11

**兜底策略**：
依赖已在配置空间中填写的实验配置参数构建前缀树，当入参 keys 匹配到了前缀树的叶子节点则不兜底，反之则兜底。

### 自动注册实验配置参数
**必要条件**：
- 确保使用了 `EnableNsReveal` option
- SDK 版本 >= v1.3.0

## V1 与 V2 版本选择

### 版本区别
- **V1**：通过返回参数区分实验的分流方式 uid 或 did
- **V2**：支持两种分流方式但不会在返回参数中将它们分开

### 选择建议
1. **全新业务线**：推荐直接使用 V2
2. **老服务迁移**：慎重考虑，AB 实验结果通常需要上游获取并传递给下游，改动可能影响下游服务

### 版本识别
- V1：调用的 RPC 方法名称为 `get_ab_versions` 或 `GetAbVersions`
- V2：调用的 RPC 方法名称为 `get_ab_versions2`
- SDK 中：存在 `UseLibraV2()` 配置则为 V2，否则是 V1

## 配置空间管理
配置空间是某业务/服务下所有相关配置的统一管理单位，概念上等同于顶层命名空间（Namespace）。在一期的功能实现上，配置空间是配置下发的最小单位。

**配置空间基本信息**：
- 名称和描述
- 关联 PSM：关联后配置空间中的配置项将会下发到 PSM 所在的机器上
- 管理员：可以编辑配置空间信息，新增、修改和发布配置
- 通知 Lark 群：绑定后可接收发布通知、报警等消息

## 注意事项

### 重要警告
1. **MS 平台 RPC 超时配置**：Abtest SDK 可能和业务使用的底层 RPC 方法不一致，可能出现 RPC 请求波动报警
2. **模拟命中实验**：老实现中存在 tnc 相关的兼容逻辑实现模拟命中实验，只有极少数业务涉及

### 业务实践建议
- **迁移到 SDK**：SDK 不实现按流量切换新老方案，需要各业务 PSM 自行实现
- **业务正确性保证**：通过双重校验和本地兜底功能辅助验证业务切换前后的正确性
- **流量切换实现**：根据业务复杂度决定是否需要在 PSM 做新老两种方式的兼容代码

## 验证与监控

### 双重校验验证
1. 按照开启步骤完成配置
2. 发送请求到对应机器
3. 在 Pod 上检索日志关键字 "[严重错误] 检测结果发现新老两种方式获取的 value 不相等"
4. 在 Metrics 环境检索指标 `bytedance.abtest.sdk.value.not.equal.count`

### 本地兜底验证
1. 按照开启步骤完成配置
2. 发送请求到对应机器
3. 在 Pod 上检索日志关键字 "发现业务侧未在 libra 配置当前服务期望使用的实验配置参数"
4. 在 Metrics 环境检索指标 `bytedance.abtest.sdk.namespaces.local.reveal`

## 相关资源
- **代码仓库**：[code.byted.org/iesarch/abtest](https://code.byted.org/iesarch/abtest)
- **A/B 实验入门**：[新手基础篇](https://bytedance.feishu.cn/wiki/wikcn90XXkdCCx0BWl9cNaI2q8f)
- **AB 分流服务介绍**：[详细文档](https://bytedance.feishu.cn/wiki/wikcnlbyhQABrskH8HBHHhiLRMe)
- **优化原理**：[完整目录](https://bytedance.feishu.cn/wiki/wikcnSbnmSnucKmu9NIUIL5HQNg)

