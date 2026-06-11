# Kitex 错误码参考

> 注意：以下错误码对应的是RPC请求失败的场景，即**对应metric上的_is_error=1**。
> 如果是 toutiao.service.stability.P.S.M.throughput，对应的是label=net_err的错误码。
> 如果不在以下范围的错误码看下是不是_is_error=0或者stability metric的label=net_err，这是业务自定义的状态码。

## THRIFT 错误码

该类别对应 thrift 框架原生的 `Application Exception` 错误，该类错误会被 KiteX 框架包装成 `Remote or network error`。

关于调用端上报的错误码：
- <v1.8.0：调用端上报错误码 119
- >=v1.8.0：上报下面对应的错误码

| 错误码 | 名称 | 含义 | 备注 |
| --- | --- | --- | --- |
| 0 | UnknownApllicationException | 未知错误 | 如果遇到这些status code，可以到 call.log (client) 或者 access.log (server) 捞一下具体的错误信息，比如 code=6 可能是在 server handler 或者 middleware 里遇到了 panic，在日志里可以看到具体的错误信息。 |
| 1 | UnknownMethod | 未知方法 | |
| 2 | InvalidMessageTypeException | 无效的消息类型 | |
| 3 | WrongMethodName | 错误的方法名字 | |
| 4 | BadSequenceID | 错误的包序号 | |
| 5 | MissingResult | 返回结果缺失 | |
| 6 | InternalError | 内部错误 | |
| 7 | ProtocolError | 协议错误 | |

## Kitex / Kite 错误码

该列表对应 byted 所使用的错误码类型。

如果错误码不在下表中，可能是服务端返回了某个支持自定义错误码的 error（如TransError）。

| 错误码 | 名称 | 含义 | 备注 |
| --- | --- | --- | --- |
| 0 | SuccessCode | 请求成功 | |
| -1 | Unknown Error | 未知的错误，具体请看access日志 | 服务端处理异常通常上报-1 |
| 101 | NotAllowedByServiceCBCode | 请求被服务级别的熔断器拒绝 | 当你配置了熔断器, 且服务端错误率过高触发了熔断器；通常是服务端或网络出现了问题 |
| 102 | NotAllowedByInstanceCBCode | 请求被实例级别的熔断器拒绝 | 该熔断器为框架自动打开, 用于屏蔽连接错误过高的服务端实例；通常是网络问题或者服务端出现了问题, 导致连接失败 |
| 103 | RPCTimeoutCode | 调用服务端超时，或业务主动取消（context.cancel） | 可以从错误信息区分（rpc/P.S.M.call.log.xxx） |
| 104 | ForbiddenByDegradationCode | 服务降级 | 请求因服务端的服务降级而被丢弃 |
| 105 | GetDegradationPercentErrorCode | 内部获取降级百分比出错 | |
| 106 | BadConnBalancerCode | 内负载均衡器错误 | |
| 107 | BadConnRetrierCode | 内部连接重试器错误 | |
| 108 | ConnRetryCode | 框架内自动连接重试失败 | 网络环境或者服务端服务实例状态不佳, 导致多次连接重试失败 |
| 109 | BadRPCRetrierCode | （已废弃）内部调用重试器失败 | |
| 110 | RPCRetryCode | 多次RPC重试失败 | |
| 111 | NoExpectedFieldCode | （已废弃）中间件缺少所需要的字段信息 | |
| 112 | GetConnErrorCode | 获取服务端连接失败 | 1. 检查服务端是否有可用实例 2. 如果是因为建连超时（例如跨地域延迟较大），可以尝试调大 ConnectionTimeout |
| 113 | ServiceDiscoverCode | 服务发现错误 | |
| 114 | IDCSelectErrorCode | （已废弃）流量调度时选择机房失败 | |
| 115 | NotAllowedByACLCode | （已废弃）服务访问被拒绝 | Kitex 的 ACL 支持不完备，如依赖该能力，请在 Server 端开启 Mesh Ingress |
| 116 | ReadTimeoutCode | （已废弃）读超时 | |
| 117 | WriteTimeoutCode | （已废弃）写超时 | |
| 118 | ConnResetByPeerCode | （已废弃）连接被远端关闭 | 服务端强行将连接关闭时会发生 |
| 119 | RemoteOrNetErrCode | 网络或者服务端错误 | 此种情况请检查返回的 err 内容, 获取实际的错误信息 |
| 120 | StressBotRejectionCode | 请求属于压测流量，被服务端拒绝 | 此种情况请联系上下游服务的负责人，检查当前上下游服务是否开启了压测开关 |
| 121 | EndpointQPSLimitRejectCode | 请求被限流器拒绝 | |
| 122 | NotAllowedByUserErrCBCode | 请求被用户自定义的熔断器挡住 | 当你配置了熔断器, 且服务端错误率过高触发了熔断器; 通常是服务端服务或网络出现了问题 |
| 123 | ErrCanceledByBusinessCode | 业务代码调用 context cancel | 需要业务主动打开全局开关（Kitex >= v1.11.2 可用） |
| 124 | ErrTimeoutByBusinessCode | 业务代码在 context 设置了 Timeout | |
| 125 | ErrBlockedByAuthSectionCode | 隐私合规管控切面拦截(WIP) | |

## Mesh Proxy RPC 错误码

该类别包含了 service mesh 模式下，mesh proxy 可能返回的错误类型。

### 连接类错误 (11xx)

| 错误码 | 名称 | 含义 | 备注 |
| --- | --- | --- | --- |
| 1111 | GET_CONN_FAILED | 获取连接失败（已废弃） | |
| 1112 | GET_CONN_ERR_NO_HEALTHY_HOST | 连接失败，服务端没有健康节点 | |
| 1113 | GET_CONN_ERR_TLC_NOT_EXIST | 连接失败，获取实例列表失败 | |
| 1114 | GET_CONN_ERR_CONNECTION_POOL_FAILED | 连接失败，从连接池获取连接失败 | |
| 1115 | GET_CONN_ERR_ON_POOL_FAILED | 连接失败，创建连接失败 | |
| 1116 | GET_CONN_ERR_RESOURCE_LIMIT_EXCEEDED | 连接失败，超过链接资源限制 | |
| 1117 | GET_CONN_ERR_NO_AVAILABLE_HOST | 连接失败，没有可用节点 | |
| 1119 | GET_CONN_ERR_ON_EGRESS_POOL_FAILED | Egress 建连失败（目标服务实例重试后仍无法连接），不建议针对该错误码重试 | |

### 超时类错误 (12xx)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1201 | CALL_CONN_TIMEOUT | 连接服务端超时 |
| 1204 | CALL_TOTAL_TIMEOUT | rpc调用超时 |
| 1205 | DDL_TIMEOUT | DDL 调用链超时错误 |

### 协议/序列化错误 (13xx)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1301 | BAD_PROTOCOL_ERR | 序列化错误 |
| 1302 | SERIALIZE_ERR | 序列化错误 |
| 1303 | DESERIALIZE_ERR | 反序列化失败 |

### 传输错误 (14xx)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1401 | PROXY_TRANSPORT_ERR | - |
| 1402 | CALLER_TRANSPORT_ERR | - |
| 1403 | CALLEE_TRANSPORT_ERR | - |

### 服务发现错误 (15xx)

| 错误码 | 名称 | 含义 | 备注 |
| --- | --- | --- | --- |
| 1501 | SERVICE_DISCOVERY_INTERNAL_ERR | 服务发现错误 | 1501 请找 mesh oncall |
| 1502 | SERVICE_DISCOVERY_EMPTY_ERR | 服务发现错误，服务端没有可用节点 | |

### 治理类错误 (16xx)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1601 | NOT_ALLOWED_BY_ACL | ACL拒绝（服务鉴权失败/严格授权失败） |
| 1602 | DEGRADE_DROP | 降级拒绝(比例丢弃) |
| 1603 | OVER_CONNECTION_LIMIT | 限流拒绝 |
| 1604 | OVER_QPS_LIMIT | 限流拒绝 |
| 1605 | CIRCUITBREAKER_OPEN | 熔断拒绝 |
| 1606 | OVERLOAD_PROTECTION_DENY | 过载保护拒绝 |
| 1607 | STRESS_DENY | 拒绝压测流量 |
| 1608 | KIRIN_DENY | kirin鉴权被拒绝，出现这个问题联系服务端加权限 |
| 1609 | CROSS_REGION_DENY | 跨域鉴权被拒绝 |
| 1610 | REQUEST_OVERSIZE_DENY | 请求包过大被拒绝 |
| 1611 | RESPONSE_OVERSIZE_DENY | 响应包过大被拒绝 |

### 连接关闭错误 (17xx)

| 错误码 | 名称 | 含义 | 备注 |
| --- | --- | --- | --- |
| 1701 | UPSTREAM_CLOSE | 被调方链接主动关闭 | 可能原因：服务端 panic 或 fatal error，登到服务端 pod 里查看 /opt/tiger/toutiao/log/app/ 和 /opt/tiger/toutiao/log/run/ |
| 1702 | DOWNSTREAM_CLOSE | 调用方链接主动关闭（只出现在mesh日志中标识作用） | |
| 1704 | DOWNSTREAM_CLOSE (新版) | 调用方链接主动关闭（只出现在mesh日志中标识作用） | |

### ACL/Token 错误 (18xx)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1801 | ACL_TOKEN_PARSE_FAILED | 解析 GDPR token 失败 |
| 1802 | ACL_TOKEN_VERIFY_FAILED | GDPR token 无效 |
| 1803 | ACL_EDGE_PROXY_AUTH_FAILED | 边缘代理 auth 认证失败 |
| 1804 | ACL_EDGE_PROXY_CROSS_REGION_FAILED | 边缘代理跨区域失败 |
| 1805 | ACL_EDGE_PROXY_REVERSE_WHITELIST_CHECK_FAILED | 边缘代理reverse白名单检查失败 |

## DES-RPC 错误码

### IDL Schema 校验错误 (182x-184x)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1822 | DES_NOT_IN_ALLOW_LIST | 不在白名单中（未申请ChannelData & 未Start） |
| 1823 | DES_IDL_SCHEMA_VALIDATE_TIMEOUT | 校验超时 |
| 1824 | DES_IDL_SCHEMA_VALIDATE_SIDECAR_INTERNAL_ERROR | 请求sidecar失败（内部错误） |
| 1825 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNKNOWN | 未知错误 |
| 1826 | DES_IDL_SCHEMA_VALIDATE_ERROR_DECODE_PAYLOAD | Payload 解码错误 |
| 1827 | DES_IDL_SCHEMA_VALIDATE_ERROR_FIELD_TYPE_MISMATCH | 字段类型不匹配 |
| 1828 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNEXPECTED_FIELD | 预期外的字段 |
| 1829 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNEXPECTED_HEADER | 预期外的Header |
| 1830 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNEXPECTED_COOKIE | 预期外的Cookie |
| 1831 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNEXPECTED_QUERY | 预期外的Query |
| 1832 | DES_IDL_SCHEMA_VALIDATE_ERROR_METADATA_MISMATCH | 校验元信息缺失 |
| 1833 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNEXPECTED_METADATA | 预期外的校验元信息 |
| 1834 | DES_IDL_SCHEMA_VALIDATE_ERROR_CONTROL_PLANE_DATA | 控制面数据错误 |
| 1835 | DES_IDL_SCHEMA_VALIDATE_ERROR_EXPR_INVALID_VALUE_TYPE | 校验表达式无效的value类型 |
| 1836 | DES_IDL_SCHEMA_VALIDATE_ERROR_INVALID_BINARY_OP | 校验表达式无效的op |
| 1837 | DES_IDL_SCHEMA_VALIDATE_ERROR_ARGUMENTS_COUNT_NOT_MATCH | 校验错误：聚合数据不匹配 |
| 1838 | DES_IDL_SCHEMA_VALIDATE_ERROR_UNSUPPORTED_FUNCTION | 校验失败：不支持的函数 |
| 1839 | DES_IDL_SCHEMA_VALIDATE_ERROR_EXPR_PARSE_FAILED | 校验失败：表达式解析失败 |
| 1840 | DES_IDL_SCHEMA_VALIDATE_ERROR_EXPR_CHECK_INVALIDATED | 校验失败：校验不通过 |
| 1841 | DES_IDL_SCHEMA_VALIDATE_ERROR_INVALID_UNARY_OP | 校验失败：无效一元操作符 |
| 1842 | DES_IDL_SCHEMA_VALIDATE_ERROR_MISSING_DATA | 校验失败：data缺失 |
| 1843 | DES_CREATOR_VALIDATION_ERROR | Creator 校验失败（用户非creator或校验失败） |

### DES 通信错误 (186x-189x)

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1860 | DES_UPSTREAM_ORIGINAL_PROTOCOL_UNKNOWN | 协议未知（非http，thrift），一般是包有问题导致解析错误 |
| 1861 | DES_REQUEST_INVALID | 非法的请求（缺少字段，字段值非法等） |
| 1862 | DES_UPSTREAM_CLOSE | upstream关闭 |
| 1863 | DES_UPSTREAM_XDS_TIMEOUT | 请求xds超时 |
| 1864 | DES_UPSTREAM_XDS_FAILURE | 请求xds失败 |
| 1865 | DES_HTTP_UPSTREAM_FAILED | 请求upstream失败 |
| 1866 | DES_BAD_INTERNAL_ERROR_CODE | thrift内部错误传递解析失败，一般不会出现 |
| 1867 | DES_GATEWAY_AGENT_RETURNS_ERROR | vpc2中的gateway agent返回了错误，请查看response中的错误信息 |
| 1868 | DES_CLOSE_BY_DOWNSTREAM_BEFORE_RESPONSE | 在回包之前，上游就关闭链接（一般是超时不够用） |
| 1869 | DES_TOKEN_VALIDATION_FAILED | DES-RPC forward 验证GDPR token/zti token失败 |
| 1870 | DES_TOKEN_RE_SIGNING_FAILED | DES-RPC reverse zti token换票失败 |
| 1871 | DES_FORWARD_TO_TLB_COMMUNICATION_ERROR | DES-RPC forward->TLB通讯失败，一般是网络问题导致 |
| 1881 | des_forward_to_tlb_connection_failed | 网络ACL等各种原因导致的连接建立失败 |
| 1883 | des_forward_to_tlb_request_timeout | 网络、链路负载高、甚至是服务端回复慢等原因触发的读写超时 |
| 1885 | des_tlb_to_reverse_request_timeout | 发生 connect/send/read 超时 |
| 1886 | des_tlb_502_error | 后端响应包过大或其他原因 TLB返回 502 |
| 1887 | des_tlb_client_request_oversize | TLB因客户端请求过长返回413 |
| 1888 | des_tlb_client_uri_oversize | TLB因客户端URI过长返回414 |
| 1889 | des_tlb_system_error | 命中了TLB封禁逻辑（Gateway Agent 校验也算 TLB封禁） |
| 1890 | DES_DEST_SERVICE_RETURN_NOT_200 | fp,tlb,rp代理都正常，唯独dst service 不正常 |
| 1891 | des_tlb_unknown_non2xx | 除上述现象外，upsteam status 200但 TLB返回非200 |

## MySQL Mesh 错误码

| 错误码 | 名称 | 含义 |
| --- | --- | --- |
| 1104 | MYSQL_HANDSHAKE_ERR | 握手失败 |
| 2000 | MYSQL_CONN_MISS_TOKEN | 鉴权缺少token |
| 2001 | MYSQL_CONN_AUTH_FAIL | 鉴权失败 |
| 2002 | MYSQL_CONN_UPSTREAM_NOT_FOUND | 发现不了mysql实例 |
| 2003 | MYSQL_CONN_ALL_UPSTREAM_FAILED | 连接不上mysql |
| 2004 | MYSQL_CONN_REFUSE | 连接的时候被mysql拒绝 |
| 2005 | MYSQL_CONN_TIMEOUT | 连接mysql超时 |
| 2021 | MYSQL_REQUEST_TIMEOUT | 请求超时 |
| 2022 | MYSQL_DROP_REQUEST | 请求降级 |
| 2023 | MYSQL_FAULT_INJECTION | 故障注入 |

## FAQ

### 如何判断 Error 是否 Kitex Error（框架内部错误）？

```go
import "github.com/cloudwego/kitex/pkg/kerrors"

kerrors.IsKitexError(err)
```

### 如何从 Kitex Error 中获得内部错误码？

超时是 103, 1204

```go
import "code.byted.org/kite/kitex/byted/berrors"

errCode, ok = berrors.GetErrorCode(err)
```

### 如何判断是否超时错误？

先确认是 Kitex Error，然后使用如下方法：

```go
import "github.com/cloudwego/kitex/pkg/kerrors"

kerrors.IsTimeoutError(err)
```

### 如何从 Overpass Error 获得 Kitex Error？

类型：`rpc_error.RPCError`

参考：https://overpass.arcosite.bytedance.net/5551/v2_err_handler

### 框架如何处理 thrift 框架原生的 Application Exception 错误码？

KiteX 框架包装成 `Remote or network error`，统一包装成 byted 错误码中的 119 (RemoteOrNetErrCode)

### 监控中为什么包含了文档内未列出的错误码？

以上错误码对应的是RPC请求失败的场景，即对应metric上的_is_error=1。

如果是 toutiao.service.stability.P.S.M.throughput，对应的是label=net_err的错误码。

不在以上范围的错误码看下是不是_is_error=0或者stability metric的label=net_err，这是业务自定义的状态码。

## 相关文档

- [错误处理](./handle-errors.md) - 错误类型与处理方式
- [错误处理最佳实践](./error-handling-guide.md) - 错误处理模式
- [超时配置](./configure-timeout.md) - 超时相关配置
- [重试配置](./configure-retry.md) - 重试相关配置

## 参考资料

- [Kitex - 错误码](https://bytedance.larkoffice.com/wiki/wikcnwSA5vc0wZ1gK44JY1pYrAb)
- [ByteMesh RPC问题自查手册--用户篇](https://bytedance.feishu.cn/docs/doccnsy5RwM6rE5V4fXfz9)
