# Python Test Template for api_test

本模板用于 `api-mind/py_driver` 在 api_test 仓库内生成 Python 测试用例文件。

## 1. 适用范围

适用于以下场景：

- 当前目标目录已有可复用 `conftest.py`
- 当前目标目录已有可复用 client，或可复用全局 `clients.http_gen.*` / `clients.rpc_gen.*`
- generate 阶段只负责**产出代码并推送或本地静态校验**，**不在模板内假设立即执行 pytest**

如果 `conftest.py` / client 缺失，请先按：

- `resources/conftest_template.md`
- `resources/client_template.md`

补齐基础设施，再生成测试文件。

---

## 2. 强制约束

1. 测试文件必须落在用户指定的 `target_case_dir`
2. 命名优先跟随同目录已有风格；若无，使用 `test_<sanitized_api_or_method>_<case_id>.py`
3. 默认使用**硬编码 `TEST_DATA`**；本轮不要强依赖 `read_test_data_with_data_driven`
4. 优先复用 `<target_case_dir>/conftest.py` 提供的：
   - `llm_config`
   - `test_env`
   - `tag_env`
   - `xxx_client` fixture
5. **不要默认显式 import `conftest.py`**
   - fixture 应通过测试函数参数自动注入
   - 只有确实存在 helper 函数，且目标目录已有显式 import helper 的既有风格时，才允许导入非 fixture helper
6. 导入路径必须是 api_test 仓库内的 Python 包路径
7. 至少保留：
   - `@pytest.mark.caseSource("llm_api_case")`
   - 一个或多个 `@pytest.mark.idc("...")`
   - `@pytest.mark.psm("...")`
   - `@allure.title(...)`
   - `@pytest.mark.parametrize("args", TEST_DATA)`
8. 断言必须生成显式 `assert` 语句

---

## 3. HTTP 模板（优先版：复用 client fixture）

当 `target_case_dir/conftest.py` 已提供可用的 `<psm_sanitized>_client` / `<psm_sanitized>_http_client` fixture 时，优先使用下面的风格。

```python
import allure
import pytest

AUTH_HEADERS = {
    # Generated from case.md / task.md / user-provided test-account data when auth is required.
    # Do not move Cookie / Authorization / Hex-Auth-Key into .env or config/*.json.
}

TEST_DATA = [
    {
        "0": {
            "request": {
                "headers": {
                    # 这里放 case.md 明确给出的 headers / cookie，
                    # 并在 generate 阶段合并 .env.test_account 中可用的 auth headers
                },
                "params": {},
                "json": {},
            },
        }
    }
]


@pytest.mark.caseSource("llm_api_case")
@pytest.mark.idc("sg1")
@pytest.mark.idc("maliva")
@pytest.mark.psm("tiktok.feed.fyp_api")
class TestAwemeV1Feed184683:

    @allure.title("aweme_v1_feed")
    @pytest.mark.parametrize("args", TEST_DATA)
    def test_aweme_v1_feed_184683(self, args, tiktok_feed_fyp_api_client):
        with allure.step("[action] send request"):
            req = args["0"]["request"]
            resp = tiktok_feed_fyp_api_client.get_aweme_v1_feed(
                headers=req.get("headers", {}),
                query_params=req.get("params", {}),
                json=req.get("json"),
                use_sd=True,
            )

        with allure.step("[assert] basic checks"):
            assert resp.status_code == 200

        with allure.step("[assert] business checks"):
            resp_body = resp.json()
            assert isinstance(resp_body, dict)
            assert resp_body["status_code"] == 0
            assert "data" in resp_body
```

### 优先版说明

- 测试函数应优先通过 fixture 拿 client，而不是在测试函数里重新 new client
- fixture 名称要跟随目标目录现有风格：如 `<psm_sanitized>_client`、`<psm_sanitized>_http_client`
- `@pytest.mark.idc("...")` 使用原始 IDC（如 `sg1` / `maliva`）
- `test_env` / `TEST_ENV` 使用配置别名（如 `sg_prod` / `va_prod`）

---

## 4. HTTP 模板（兜底版：仅在无 fixture 且目录允许时手动 new client）

只有在以下条件同时满足时，才允许使用本模板：

1. `<target_case_dir>/conftest.py` 没有可复用的 client fixture
2. 当前目录已有“测试函数内手动构造 client”的既有风格，或本轮新增的最小 `conftest.py` 仅提供 `llm_config` / `test_env`
3. 当前目录没有更合适的 client fixture 约定可复用

```python
import allure
import duck
import pytest
from tests.<domain>.<module>.client.<client_module> import <ClientClass>

TEST_DATA = [
    {
        "0": {
            "request": {
                "headers": {
                    # case.md headers / cookie
                    # + generate 阶段从 .env.test_account 合并得到的 auth headers
                },
                "params": {},
                "json": {},
            },
        }
    }
]


@pytest.mark.caseSource("llm_api_case")
@pytest.mark.idc("sg1")
@pytest.mark.psm("tiktok.feed.fyp_api")
class TestAwemeV1Feed184683:

    @allure.title("aweme_v1_feed")
    @pytest.mark.parametrize("args", TEST_DATA)
    def test_aweme_v1_feed_184683(self, args, llm_config, test_env):
        psm = "tiktok.feed.fyp_api"
        conf = llm_config[test_env][psm]

        client = <ClientClass>(
            host=conf.get("host", ""),
            idc=conf.get("idc", "sg1"),
            cluster=conf.get("cluster", "default"),
            tag_env=conf.get("tag_env", "prod"),
            use_host=False,
        )

        with allure.step("[action] send request"):
            req = args["0"]["request"]
            resp = client.get_aweme_v1_feed(
                headers=req.get("headers", {}),
                query_params=req.get("params", {}),
                json=req.get("json"),
                serialization=duck.Serialization.JSON,
                use_sd=True,
            )

        with allure.step("[assert] basic checks"):
            assert resp.status_code == 200

        with allure.step("[assert] business checks"):
            resp_body = resp.json()
            assert isinstance(resp_body, dict)
            assert resp_body["status_code"] == 0
```

### 兜底版说明

- 这是**兜底方案**，不是默认方案
- 若历史目录风格使用 `params=` 而非 `query_params=`，跟随已有目录风格
- 若返回值是 `(status_code, body)` 而非 response object，需按实际 client 约定改写断言
- 若 case 需要 Cookie / Authorization / Hex-Auth-Key / X-Auth-* 等业务鉴权头，必须写入生成的 Python 代码（推荐模块级 `AUTH_HEADERS`，也可内联到 `TEST_DATA`），不得写入 `.env` 或 api_test `config/*.json`。

---

## 5. RPC 模板

```python
import allure
import pytest

TEST_DATA = [
    {
        "0": {
            "request": {
                "field_a": "value",
                "field_b": 1,
            },
        }
    }
]


@pytest.mark.caseSource("llm_api_case")
@pytest.mark.idc("sg1")
@pytest.mark.idc("maliva")
@pytest.mark.psm("tns.demo.rpc")
class TestDemoRpc177001:

    @allure.title("tns.demo.rpc - DemoMethod")
    @pytest.mark.parametrize("args", TEST_DATA)
    def test_demo_method_177001(self, demo_rpc_client, args):
        with allure.step("[action] send request"):
            req_body = args["0"]["request"]
            resp = demo_rpc_client.DemoMethod(req_body)

        with allure.step("[assert] basic checks"):
            assert isinstance(resp.body, dict)
            assert resp.body["BaseResp"]["StatusCode"] == 0

        with allure.step("[assert] business checks"):
            assert "Data" in resp.body
            assert resp.body["Data"]["field_a"] == req_body["field_a"]
```

---

## 6. 鉴权来源与落点

对需要鉴权的 HTTP API，生成时应按下面的优先级构造 `TEST_DATA[*].request.headers`：

1. `case.md` 中明确给出的 headers / cookie
2. 当前 spec `.env` 中该 PSM 对应环境项里的 `test_account` / `cookie`
3. 目标目录附近 sibling case 中可复用的 auth 形态

规则：

- sibling case 推断只允许作为**候选补全**，不能覆盖 case.md 或 `.env` 的显式值
- 如果 auth 来源于 sibling case，必须在 generate 结果中记录 warning，说明其为 inferred auth
- 如果最终仍缺少关键 auth，应在 generate 结果中输出 warning，并在 execute 前再次提示用户可能出现 401 / 403

---

## 7. 生成时需要自动替换的占位符

- `<domain>.<module>`: 目标目录对应的 api_test 包路径
- `<client_module>`: client 文件名（snake_case）
- `<ClientClass>`: client 类名（PascalCase）
- `TestAwemeV1Feed184683`: 依据 API / method / case_id 生成
- `test_aweme_v1_feed_184683`: 依据 API / method / case_id 生成
- `tiktok.feed.fyp_api`: 当前 case 的 PSM
- `get_aweme_v1_feed`: 目标 client 方法名
- IDC marks: 根据同步后的 config 环境列表生成

---

## 8. 断言策略

建议顺序：

1. 传输层成功
   - HTTP: `status_code == 200`
   - RPC: `resp.body['BaseResp']['StatusCode'] == 0`
2. case.md 中明确的业务断言
3. 若 case.md 中存在半结构化断言，必须在生成阶段把它们展开为普通 Python `assert` 语句

---

## 9. 生成后静态检查

生成后至少检查：

1. Python 语法合法
2. imports 在当前仓库结构下可解析
3. fixture 名称与 `conftest.py` 保持一致
4. client 类名 / 方法名与实际生成或复用的 client 对齐
5. `@pytest.mark.idc(...)` 与 config 文件覆盖的环境一致
6. 未默认 import `conftest.py`；若存在 helper import，必须能说明其必要性并符合目标目录既有风格
