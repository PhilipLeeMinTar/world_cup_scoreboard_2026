# Client Template for api_test Python LLM Cases

当目标落点附近找不到可复用 client，且全局 `clients.http_gen.*` / `clients.rpc_gen.*` 也无法直接复用时，`api-mind/py_driver` 应生成本地 `client/<name>.py`。

本模板参考：

- `tests/pipeline_and_release/music_mcs/llm_gen/tiktok_feed_fyp_api/client/tiktok_feed_fyp_api.py`

---

## 1. HTTP Client 模板

```python
from duck import HTTPClient
from duck.decorate import apipath

PSM = "<psm>"


class <ClientClass>(HTTPClient):
    def __init__(
        self,
        host="",
        idc="",
        cluster="default",
        tag_env="prod",
        use_host=True,
        times=1,
        caller_psm="",
        proxy_name="",
        proxy_pw="",
        proxy_host="",
        test_env="",
        enable_row_3pgw=False,
        enable_row_internal=False,
        is_json=False,
    ):
        super().__init__(
            PSM,
            idc,
            cluster,
            tag_env,
            host,
            use_host,
            times,
            caller_psm=caller_psm,
            proxy_name=proxy_name,
            proxy_pw=proxy_pw,
            proxy_host=proxy_host,
            test_env=test_env,
            enable_row_3pgw=enable_row_3pgw,
            enable_row_internal=enable_row_internal,
            is_json=is_json,
        )

    @apipath(psm="<psm>", apipath="<api_path>")
    def <method_name>(self, use_sd=True, **kwargs):
        method_name = self.<method_name>.__name__
        apipath_value = kwargs.get("apipath") or "<api_path>"
        return self.call_api(
            api=method_name,
            apipath=apipath_value,
            method="<http_method>",
            use_sd=use_sd,
            **kwargs,
        )
```

### HTTP 调用参数说明

生成测试代码时，HTTP client 的调用参数需要区分 client 基类来源：

1. **若 client 继承的是 `HTTPGenericClient`**
   - 调用时通常需要显式传入：
     - `serialization=duck.Serialization.JSON`
   - Example:

```python
resp = client.{func_name}(
    headers=args['0']['request']['headers'],
    query_params=args['0']['request']['params'],
    json=args['0']['request']['json'],
    serialization=duck.Serialization.JSON,
)
```

2. **若 client 继承的是 `duck.HTTPClient`**
   - **不需要**额外传 `serialization=duck.Serialization.JSON`
   - Example:

```python
resp = client.{func_name}(
    headers=args['0']['request']['headers'],
    query_params=args['0']['request']['params'],
    json=args['0']['request']['json'],
)
```

约束：

- agent 在生成测试代码前，必须先判断目标 client 实际继承的是 `HTTPGenericClient` 还是 `HTTPClient`
- 不要把 `serialization=duck.Serialization.JSON` 无差别加到所有 HTTP client 调用上
- 若目标目录已有既有调用风格，优先跟随既有风格，再结合基类类型判断是否需要 `serialization`

### 生成要求

1. 文件名使用 snake_case，例如：`tiktok_feed_fyp_api.py`
2. 类名使用 PascalCase，例如：`TiktokFeedFypApiClient`
3. 每个接口方法应尽量一一对应 case 所需 API
4. `@apipath` 中的 `psm` 与 path 必须准确，不可凭空捏造
5. 若同 case 文件涉及多个 HTTP API，可在同一 client 类里生成多个方法

---

## 2. RPC Client 处理策略

RPC 优先级：

1. 优先复用全局 `clients.rpc_gen.*`
2. 其次复用同业务目录已有的 RPC generic client
3. 只有在明确需要且仓库里没有现成 generic client 时，才允许生成本地包装层

推荐的本地 RPC 包装模板：

```python
from clients.rpc_gen.<rpc_module> import <GenericClientClass>


class <ClientClass>(<GenericClientClass>):
    pass
```

说明：

- 除非用户目录已有明确的本地包装习惯，否则不要手写复杂 RPC transport 逻辑
- `api-mind/py_driver` 的首选是**复用**现有 rpc_gen client，而不是重新发明一套 RPC client

---

## 3. 方法名生成建议

### HTTP

优先顺序：

1. 复用已有业务目录 client 的命名风格
2. 若无既有风格，可使用：
   - `get_<sanitized_path>` for GET
   - `post_<sanitized_path>` for POST
   - `put_<sanitized_path>` for PUT
   - `delete_<sanitized_path>` for DELETE

例如：

- `/aweme/v1/feed/` -> `get_aweme_v1_feed`
- `/tiktok/feed/for_us/v2` -> `get_tiktok_feed_for_us_v2`

### RPC

直接使用 IDL / generic client 中的原始方法名，例如：

- `AIExcaliburModerate`
- `SearchArtistOneID`

---

## 4. 生成前校验

在生成 client 前，先检查：

1. 目标路径附近是否已有可复用 client
2. 全局 `clients.http_gen.*` / `clients.rpc_gen.*` 是否已有对应实现
3. case 里涉及的是 HTTP 还是 RPC
4. path / method / psm 信息是否来自 `case.md` / `spec.md` / 已知契约，而非猜测

---

## 5. 生成后校验

1. client 文件可被 Python 语法检查
2. 类名、方法名与测试文件导入一致
3. conftest fixture 返回的 client 类与该文件一致
4. 只生成本次 case 真正需要的方法，不顺手批量生成整个 service 的所有接口
