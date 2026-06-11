# ByteTIM Python SDK 使用指南

## 概述

ByteTIM Python SDK 为 Python 服务提供票据生成和校验能力，主要支持 Euler 框架，适用于需要注入或校验 ByteTIM 身份票据的 Python 服务场景。

## 适用场景

**Python SDK 适用场景：**

1. 请求的源头服务是 Python 脚本服务，该服务不承接上游流量
2. Python 服务需要注入业务自定义参数

## 安装要求

- **安装命令**：`pip3 install byted-bytetim`（强烈建议使用最新版本，安装前请确认已配置公司私有源）
- **Python 版本**：由于 Lego SDK 限制，要求 Python 版本 >= 3.6

## 服务角色与初始化

### 票据生成方

```python
# 如果服务角色是票据生成方，使用 init_generator()
from bytetim import client
client.init_generator()
```

### 票据校验方

```python
# 如果服务角色是票据校验方，使用 init_verifier()
from bytetim import client
client.init_verifier()
```

**重要注意事项：**
- 只需要全局初始化一次！
- 初始化过程中的任何错误都会导致服务无法正常启动
- 如果是多进程程序，需要在每个进程中都进行 SDK 初始化

## Euler 框架集成

### Euler 客户端中间件

**适用场景**：服务不承接 RPC 请求流量（例如定时脚本、MQ 消费方等）

```python
import euler
from bytetim import client
from bytetim.bytetim_euler import bytetim_euler_middleware

client.init_generator() # 全局初始化一次
cli = euler.Client()
cli.use(bytetim_euler_middleware)
cli.use(euler.base_compat_middleware.client_middleware)  # Must be registered in the end.
```

### Euler 服务端中间件

**适用场景**：服务是一个 RPC 服务端，承接上游 RPC 请求流量

```python
import euler
from bytetim import client
from bytetim.bytetim_euler import bytetim_euler_middleware

client.init_generator() # 全局初始化一次
svr = euler.Server()
svr.use(euler.base_compat_middleware.server_middleware) # Must be registered in the first.
svr.use(bytetim_euler_middleware)
```

## 票据操作

### 创建票据（基础方式）

对于 Euler 框架，如果不需要注入业务自定义参数，使用 SDK 提供的 `bytetim_euler_middleware` 中间件即可。

### 创建 & 修改票据（注入自定义参数）

业务方可以使用 `upsert_ticket` 方法注入/修改票据字段，需要在控制面设置服务角色为 **票据生成方**。

**参数说明：**
- `extra_map`：可选参数，传入 **tim_ticket.thrift** idl 外的自定义参数，使用前需要事先在平台申请
- `business`：可选参数，早期定义在 **tim_ticket.thrift** idl 内的自定义参数，直接使用即可
- `common_map`：可选参数，目前只支持修改 app/device/user 维度信息

**Euler 框架示例：**

```python
import euler
from bytetim.bytetim_euler import upsert_ticket
from bytetim.tim_ticket.ttypes import Business
from bytetim import client

def upsert_ticket_middleware(ctx, *args, **kwargs):
    try:
        extra = {'BYTETIM_BUSINESS_XXX': 'XXX'}  # idl 外业务自定义参数
        common = {'BYTETIM_APP_APPID': '13'}     # 通用票据参数
        biz = Business(ItemUID=123, ADAccountID=64) # idl 内业务自定义参数
        ctx = upsert_ticket(ctx=ctx, extra_map=extra, common_map=common, business=biz)
    except Exception:
        # 异常处理
    finally:
        return ctx.next(*args, **kwargs)

client.init_generator() # 全局初始化一次
cli = euler.Client()
cli.use(upsert_ticket_middleware)
cli.use(euler.base_compat_middleware.client_middleware)
```

### 校验票据

业务方可以使用 `get_ticket_v2` 方法校验票据，可以在控制面设置票据是否需要可信。

```python
from bytetim.bytetim_euler import get_ticket
from bytetim import client

# 全局初始化一次
client.init_verifier()

def rpc_method1(ctx):
    try:
        t = get_ticket_v2(ctx)
        
        # 获取票据信息
        app_id = t.get_app_info().AppID
        did = t.get_device_info().DID
        item_app_id = t.get_business_info().ItemAppID
        
        # 获取业务自定义字段
        extra = t.get_persist_map()
        biz = extra['BYTETIM_BUSINESS_XX']
    except Exception:
        # 异常处理
```

## HTTP 场景支持

从 1.0.9 版本开始，针对脚本通过 HTTP 调用下游的场景，ByteTIM SDK 提供相关方法注入票据到 header。

### 基础票据注入

```python
import requests
from bytetim import client
from bytetim.bytetim_http import get_or_create_ticket_for_http

client.init_generator() # 全局初始化一次

try:
    headers = {"Content-Type": "application/json"} # 原请求 header 样例
    headers_with_ticket = get_or_create_ticket_for_http(headers) # 注入票据到 header 中
    response = requests.get("https://www.example.com/", headers = headers_with_ticket)
except Exception as e:
    # 异常处理
```

### 带自定义参数的票据注入

```python
import requests
from bytetim import client
from bytetim.bytetim_http import upsert_ticket_for_http

client.init_generator() # 全局初始化一次

try:
    headers = {"Content-Type": "application/json"} # 原请求 header 样例
    extra = {'BYTETIM_BUSINESS_XXX': 'XXX'}  # idl 外业务自定义参数
    common = {'BYTETIM_APP_APPID': '13'}     # 通用票据参数
    biz = Business(ItemUID=123, ADAccountID=64) # idl 内业务自定义参数
    
    headers_with_ticket = upsert_ticket_for_http(header=headers, extra_map=extra, common_map=common, business=biz)
    response = requests.get("https://www.example.com/", headers = headers_with_ticket)
except Exception as e:
    # 异常处理
```

## 资源管理

### 关闭 SDK

如果不再使用 ByteTIM SDK，可以 close SDK 释放资源。

```python
from bytetim import client
client.close()
```

**注意：** 只可以全局 close 一次！init 逻辑比较重，一般来说不需要主动 close。

## 常见问题

### 1. 启动提示 "the token is empty"
由于 ByteTIM SDK 依赖 GDPR/ZTI Token，本地 mac/devbox 需要使用 doas 命令启动才能拿到 token（TCE 无须执行此命令）。

```bash
doas -p xxx.yyy.zzz python3 main.py
```

### 2. 启动提示 "errTimeout"
Lego 和 ByteTIM 启动都需要服务发现，本地 mac 启动请配置好服务发现。

### 3. 多线程情况下提示 "This operation would block forever"
使用 `monkey.patch_all()` 解决。

## 注意事项

1. **框架支持**：目前只支持 Euler 框架，Pie 框架由于早已废弃且不支持传递票据，建议使用 Euler 框架接入
2. **HTTP 服务**：对于 Python 的 HTTP 服务，考虑使用网关方式接入，需要引入支持透传的 Euler middleware
3. **控制面注册**：在使用 SDK 前，需要参考用户文档在 ByteTIM 控制面进行注册
4. **背景知识**：接入前请先阅读 ByteTIM(Themis 3.0)用户文档，了解相关的背景知识

