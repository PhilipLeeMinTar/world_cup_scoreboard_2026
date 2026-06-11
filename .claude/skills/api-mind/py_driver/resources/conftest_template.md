# Conftest Template for api_test Python LLM Cases

当用户确认的 `target_case_dir` 内找不到可复用的 `conftest.py`，或者该目录内 `conftest.py` 缺少最基本的 config / env / client fixture 时，`api-mind/py_driver` 应使用本模板在 `target_case_dir` 生成**最小可用**的 `conftest.py`。不得向父目录逐级查找或复用父级 `conftest.py`。

## 1. 目标

生成一个最小但符合 api_test 习惯的 `conftest.py`，负责：

- 从同级 `config/` 读取 `{test_env}.json`
- 提供 `llm_config`
- 提供 `test_env`
- 提供 `tag_env`
- 为本次 case 涉及的 PSM 提供 `xxx_client` fixture

> 本模板优先覆盖 HTTP / RPC 单接口场景；更复杂的 account / data-driven / allure hook 逻辑不要求首轮自动补齐。

---

## 2. 目录约定

假设：

- `conftest.py` 位于 `<case_root>/conftest.py`
- 配置目录位于 `<case_root>/config/`
- client 位于 `<case_root>/client/`

优先复用 `config/`；若目录不存在可创建，与 `conftest.py` 内读取路径保持一致。

---

## 3. 最小模板

```python
import os
import pytest
from common.ttat import psm_config
from tests.<domain>.<module>.client.<client_module> import <ClientClass>


@pytest.fixture(scope="session", autouse=True)
def llm_config(test_env, tag_env):
    root_path = os.path.split(os.path.abspath(__file__))[0]

    config_dir = "config"
    if not os.path.isdir(os.path.join(root_path, config_dir)):
        config_dir = "configs"

    config_file = os.path.join(root_path, config_dir, f"{test_env}.json")
    print("fixture config, config_file=", config_file)

    config = psm_config.PsmDynamicClientConfig(filepath=config_file, tag_env=tag_env)
    if tag_env:
        for test_env_key, test_env_config in config.local_config.items():
            if not test_env_config or not isinstance(test_env_config, dict):
                continue
            for psm, psm_conf in test_env_config.items():
                psm_conf["tag_env"] = tag_env
    return config


@pytest.fixture(scope="session", autouse=True)
def test_env():
    value = os.environ.get("TEST_ENV")
    if value is None:
        raise Exception("fixture test_env, TEST_ENV is None")
    return value


@pytest.fixture(scope="session", autouse=True)
def tag_env():
    return os.environ.get("TAG_ENV")


@pytest.fixture(scope="session", autouse=False)
def <client_fixture_name>(llm_config, test_env):
    conf = llm_config[test_env]["<psm>"]
    return <ClientClass>(
        host=conf.get("host", ""),
        idc=conf.get("idc", "sg1"),
        cluster=conf.get("cluster", "default"),
        tag_env=conf.get("tag_env", "prod"),
        use_host=False,
    )
```

---

## 4. 生成规则

### 4.1 导入路径

- `tests.<domain>.<module>.client.<client_module>` 必须对应 api_test 仓库真实路径
- 不允许引用插件仓库文件

### 4.2 配置目录选择

优先顺序：

若同级已有 `config/`，沿用 `config/`；否则创建该文件夹

### 4.3 client fixture 名称

命名建议：

- HTTP: `<psm_sanitized>_client` 或 `<psm_sanitized>_http_client`
- RPC: `<psm_sanitized>_rpc_client`

优先跟随同域已有命名风格。

---

## 5. 可选扩展

仅在明确需要时补充：

- `pytest_runtest_setup` 中的 Allure link
- 额外 client fixtures

原则：**先最小可用，再增量补充**。
