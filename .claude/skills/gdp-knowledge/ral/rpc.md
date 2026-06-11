# RPC资源配置和使用

## 概述

RPC（Remote Procedure Call）是RAL框架中最常用的资源类型之一，用于访问远程服务。基于`KiteX`封装，需要基于代码生成使用。目前已同时支持`tiktok/rpcmodels`与`overpass`两种模式。

## 主要特性

- **双模式支持**：同时支持`tiktok/rpcmodels`与`overpass`两种RPC框架
- **代码生成**：基于IDL自动生成客户端代码，无需手动编写
- **服务发现**：自动集成服务发现机制，支持动态服务寻址
- **负载均衡**：内置多种负载均衡策略，提高服务可用性
- **超时控制**：支持连接超时、读超时、写超时等多级超时配置
- **重试机制**：提供可配置的重试策略，增强服务调用可靠性
- **监控打点**：自动集成监控指标，支持调用链追踪

## 代码生成位置

对应生成的代码位置如下：

- `rpcmodels` => `code.byted.org/tiktok/rpcmodels/p_s_m/cli`
- `overpass (RAL)` => `code.byted.org/overpass/p_s_m/gdp/rpc/p_s_m`

### 包路径说明

> **重点注意**：通过包路径中是否包含 `/gdp/` 来区分使用 RAL 还是原生 overpass。如果是原生 overpass，请参考 overpass 技术栈文档。

| 包路径 | 说明 | 是否需要 RAL 配置 |
|--------|------|------------------|
| `code.byted.org/overpass/p_s_m/gdp/rpc/p_s_m` | RAL client 包，带 `/gdp/` 路径 | **需要** |
| `code.byted.org/overpass/p_s_m/rpc/p_s_m` | 原生 overpass 包，不带 `/gdp/` 路径 | **不需要** |

**注意**：
- 带 `/gdp/` 路径 → RAL 封装的 client，需要在 `rpc.yaml` 中配置资源
- 不带 `/gdp/` 路径 → 原生 overpass client，直接使用即可，无需 RAL 配置

## 资源配置

RPC 的资源配置非常简单，在配置时需要注意以下细节：

- 协议标识：`rpc`
- 超时配置只支持`ConnTimeout`、`ReqTimeout`，**不支持**`WriteTimeout`、`ReadTimeout`
- 超时配置在文件中的优先级比 neptune 高，即**只要在配置中指定了相关超时，neptune 的配置将不会生效**
- **没有默认集群选项**，不支持`ExtensionCfg.IsDefault`

### 配置示例

一个完整的 RPC 资源配置示例（标记为必填字段）如下：

```yaml
ugc_center:
  PSM: tiktok.ugc.center
  Protocol: rpc
  Retry: 1
  ConnTimeout: 120ms
  ReqTimeout:
    default: 500ms
    ENV_singapore-central: 300ms
  ExtensionCfg:
    TargetVDC:
      default: my1
      ENV_useast2a: maliva
    TargetCluster: auth
    ReqRespLog: true
```

### 多机房配置

可以通过yaml 空值～声明在某个机房不访问某个资源。例如：

```yaml
ugc_center:
  PSM:
      default: tiktok.ugc.center
      ENV_singapore-central: ~ // 在singapore-central忽略此资源的初始化
  Protocol: rpc
```

### 扩展配置字段

`ExtensionCfg`支持配置的字段如下：

| **字段名** | **`ENV_tag`** | **含义** |
| --- | --- | --- |
| `TargetVDC` | `支持` | • 访问资源的目标机房 VDC |
| `TargetCluster` | `支持` | • 访问资源的目标** TCE 集群**标识 |
| `ReqRespLog` | 不支持 | • 将所有请求的 Request 和 Response，添加到日志 |

## 使用客户端

使用方式非常简单，直接调用`rpcmodels`或者`overpass`代码仓库中的客户端代码即可：

### rpcmodels模式

```go
import (
    "context"

    tiktok_ugc_center "code.byted.org/tiktok/rpcmodels/tiktok_ugc_center/cli"
    "code.byted.org/tiktok/rpcmodels/tiktok_ugc_center/dto"
)

func Invoke(ctx context.Context) {
    req := &dto.PostRequest{}

    resp, err := tiktok_ugc_center.Post(ctx, req) // call rpc
    // ...
}
```

### overpass模式

```go
import (
    "context"

    "code.byted.org/overpass/tiktok_ugc_center/gdp/rpc/tiktok_ugc_center"
    dto "code.byted.org/overpass/tiktok_guc_center/kitex_gen/tiktok/ugc/center"
)

func Invoke(ctx context.Context) {
    req := &dto.PostRequest{}

    // **Note**: 不再需要添加 RawCall
    resp, err := tiktok_ugc_center.Post(ctx, req) // call rpc

    // ...
}
```

## 请求选项

支持代码方式设置`KiteX`提供的请求选项：

| **选项** | **说明** |
| --- | --- |
| `WithRetry` | 设置单次请求的`Retry` |
| `WithConnTimeout` | 设置单次请求的连接超时 |
| `WithRPCTimeout` | 设置单次请求的超时 |
| `WithIDC` | 设置单次请求的目标 IDC |
| `WithVRegion` | 设置单次请求的目标 VRegion |
| `WithCluster` | 设置单次请求的目标** TCE 集群** |
| `WithoutExtractBizError` | 设置为**不解析****`业务错误`****信息**，默认会从`BaseResp`中解析出业务错误，并将此类型错误也转换成`error`并抛出。 |

## 请求日志

```
Notice invokehandler.go:92 10.78.204.49 p.s.m - default - 0 span=[0.3] req_start_time=[1716366741.835819] req_name=[svc_meta] psm=[tiktok.gdp.svc_meta] req_type=[rpc] conn_timeout=[20ms] req_timeout=[5s] req_method=[GetAPIMetaInfo] inline_combine=[-] transport_protocol=[TTHeader] mesh_mode=[1] target_vdc=[boe] target_cluster=[default] stress_tag=[-] remote_addr=[[2605:340:cd50:2000:c7c3:3b7:abea:b93b]:9356] send_size=[307] recv_size=[158] sd=[0.034ms] conn=[6.502ms] write=[0.033ms] read=[9.553ms] total=[16.276ms] errno=[0] errmsg=[ok]
```

请求日志中特有字段的说明：

|   | **字段名** | **字段解析** |
| --- | --- | --- |
| 基本信息 | `req_method`<br />`inline_combine`<br />`transport_protocol`<br />`mesh_mode` | • 请求 RPC 方法名<br />• 是否是合并部署状态<br />• 请求传输协议<br />• 请求是否通过 Mesh 完成 |
| 请求信息 | `target_vdc`<br />`target_cluster`<br />`send_size`、`recv_size` | • 目标 VDC<br />• 目标集群<br />• 请求发送、接收字节数 |

## 相关文档

- [RAL概述](../overview.md) - RAL组件总体介绍
- [Abase/Redis资源](abase_redis.md) - 缓存资源配置和使用
- [Database资源](database.md) - 数据库资源配置和使用
- [Eventbus资源](eventbus.md) - 消息队列资源配置和使用
- [单元测试](testing.md) - RAL组件单元测试指南