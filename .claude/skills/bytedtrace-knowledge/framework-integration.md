# BytedTrace 框架组件集成

> 如果你的框架已集成 BytedTrace，**无需手动初始化 SDK**，框架会自动完成 span 的创建和传递。

## 接入验证

进入 [Argos 链路追踪页面](https://cloud.bytedance.net/argos/trace/retrieve/conditionRetrieve)，切换到你的 PSM，点击"服务配置"，在右侧弹出框中查看是否已接入。

## 服务框架

### Golang

| 框架/组件 | 最低版本 | 备注 |
|-----------|----------|------|
| kitex | >=v1.1.12 | |
| ginex | >=v1.7.0 | v1.7.0 有不兼容变更 |
| hertz | >=v0.5.0 | v1.0 前需从 `hertz.RequestContext.Context()` 获取 ctx；v1.0 后取 `HandlerFunc` 左边的 `context.Context` |
| kite | >=v3.9.25 | |
| kitc | >=v3.10.13 | |
| http-client-trace-wrapper | >=v1.0.6 | 推荐优先使用 hertz-client，无法替换时使用此 wrapper |

### Rust

| 框架 | 最低版本 |
|------|----------|
| lust | >=0.13.1 |

### C++

| 框架 | 最低版本 | 备注 |
|------|----------|------|
| Archon | >=1.50.0 | 开启 mesh 出流量代理会导致没有 clientSpan（mesh client 暂不支持 bytedtrace） |

### Java

| 框架 | 最低版本 |
|------|----------|
| RPC (thrift-lang-core 等) | >=1.0.16-alpha.9.1-SNAPSHOT |
| MVC (mvc-interceptors) | >=1.0.6 |

### Python

| 框架 | 最低版本 | 备注 |
|------|----------|------|
| euler | >=2.1.0 | 低于此版本 `_to_service` 为 "-" |
| bytedunicorn | >=0.6.0 | |
| bytedwsgimiddleware | >=0.7.1 | |

### Node.js

| 框架 | 版本 |
|------|------|
| gulu/gulux | @gulu/runtime-base 5.0.0 |

## 存储/缓存/MQ 基础组件

### MySQL

| 语言 | 组件 | 最低版本 | 备注 |
|------|------|----------|------|
| Go | mysql-driver | >=v1.2.1 | 必须传递 context，如 `gormDB.Context(ctx).Where(...)` |
| Go | bytedmysql | >=v1.1.2 | 同上；开启 mesh 时需升级到 v1.1.19+ |
| Java | java_arch/mysql-group | 1.1.5-8-SNAPSHOT | |
| Node.js | sequelize-creator | @byted-service/sequelize-creator@2.0.0 | 只支持打点，不支持串联 Trace |
| Python | bytedmysql | >=0.3.2 | |

### Redis / ABase

| 语言 | 组件 | 最低版本 | 备注 |
|------|------|----------|------|
| Go | goredis | >=v5.2.0 | 需用 `redisClient.WithContext(ctx).XX` 做串联 |
| Java | springboot2-redis-lang | 2.0.12-SNAPSHOT | |
| Java | java-abase-client | 2.4.4-SNAPSHOT | |
| C++ | cpputil/db2 | 1.3.4-trace | |
| Node.js | gulu/redis / redis-creator | @gulu/redis ^2.0.0 | |
| Python | bytedredis | >=1.3.2 | |

### MQ

| 语言 | 组件 | 最低版本 | 备注 |
|------|------|----------|------|
| Go | rocketmq | >=v1.4.8 | mqmesh 模式暂不支持 |
| Go | sarama | >=v1.4.1 | 使用 `producer.CtxSendMessage(ctx, msg)`；裸用 sarama 默认轻量模式不上报 metrics，需设 `EnableLightMode=false` |
| Go | kafka-client | >=v1.0.9 | 使用 `consumer.TraceMarkOffset()` |
| Go | tmq | >=v1.5.27 | |
| Go | eventbus | >=v1.9.0 | sidecar 模式需 >=v1.12.0 |
| Java | rmq/bmq | — | 无内置 SDK，可参考社区贡献的 Spring 插件 |

### 其他存储

| 类型 | 语言 | 组件 | 最低版本 |
|------|------|------|----------|
| bytegraph | Go | inf/bytegraph_gremlin_go | >=v1.1.22 |
| bytegraph | C++ | inf/bytegraph_gremlin_cpp | v2.0.0 |
| bytegraph | Python | inf/bytegraph_gremlin_python | bytedbytegraph_gremlin 0.0.13a1 |
| bytegraph | Java | lilei.rd/bytegraph-gremlin-java | 1.0.3-SNAPSHOT |
| bytedoc (MongoDB) | Go | bytedoc/mongo-go-driver | >=v1.1.1 |
| bytedoc (MongoDB) | C++ | libmongo_cxxdriver | v1.2.0（默认关闭，需设 `set_use_bytedtrace`） |
| TOS | Go | gopkg/tos | >=v1.3.3 |
| TOS | C++ | storage/tos-cpp-sdk | >=v1.0.3 |
| TOS | Python | pylibs/bytedtos | bytedtos-1.0.0 |
| TOS | Java | storage/tos-java-sdk | >=1.3.12 |
| TOS | Node.js | byted-service/tos | >=3.0.0 |
| bytekv | Go | gopkg/bytekv | >=v1.0.5 |
| bytekv | C++ | bytekv/bytekv4cpp | >=v0.3.0 |
| ByteES | Go | toutiao/elastic | >=v7.0.23（仅用于 ByteES） |
| BES (datapalace) | Go | ad/elastic-go/v7 | >=v7.2.10 |
| bytesql | Go | gopkg/bytesql-go | >=v0.6.0 |

## FaaS

| 语言 | 框架 | 最低版本 | 备注 |
|------|------|----------|------|
| Go | faas-go | >=v1.5.33 | 支持 http & mq request |

> 其他语言的 FaaS 需自行接入 SDK，参考 sdk-usage.md。

## CronJob

CronJob 无统一框架，需开发者手动接入，参考：
- [Cronjob 接入 Trace 示例](https://bytedance.feishu.cn/docs/doccnBcyOIZvefX58XW1spvbiif)
- [[消金-账单] cronjob 接入 byteTrace](https://bytedance.feishu.cn/wiki/L2VlwK9KIid5lrkaGBccn3h2nrd)

## 尚不支持的组件

如需接入不在上述列表中的通用组件：
1. 在用户群（Chat Card: oc_f15caad9a3ebdcb793fba4fa0e76f71d）提 Oncall，寻求 BytedTrace 团队支持
2. 或自行接入 SDK，参考 sdk-usage.md
