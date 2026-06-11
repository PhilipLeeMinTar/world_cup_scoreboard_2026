# py_driver generate/case_code

本文件在需要生成 / 修改 Python 测试文件时读取。

## 1. 文件落点与命名

测试文件必须写入用户指定的 `target_case_dir`。命名优先跟随同目录风格，否则默认 `test_<sanitized_api_or_method>_<case_id>.py`。

## 2. 数据与鉴权组织

当前阶段不要求依赖 `read_test_data_with_data_driven`。允许在测试文件中直接声明：

```python
TEST_DATA = [
    {
        "0": {
            "request": {
                "headers": {...},
                "params": {...},
                "json": {...}
            }
        }
    }
]
```

并使用 `@pytest.mark.parametrize("args", TEST_DATA)`。

`Cookie`、`Authorization`、`Hex-Auth-Key`、`X-Auth-*` 等业务鉴权头必须写入生成的 Python 代码（推荐 `AUTH_HEADERS = {...}` 后复用），不得写入 `.env` 或 config JSON。

## 3. 必备结构

优先遵循 `../../resources/py_test_template.md`，至少包含：必要 imports、`@pytest.mark.caseSource("llm_api_case")`、基于原始 IDC 的 `@pytest.mark.idc("...")`、`@pytest.mark.psm("...")`、测试类、`@allure.title(...)`、`@pytest.mark.parametrize("args", TEST_DATA)`、测试函数。

HTTP 场景优先复用 `target_case_dir/conftest.py` 暴露的 `<psm_sanitized>_client` fixture；仅在目标目录内没有可复用 fixture 且目录允许时，才在测试函数里手动构造 client。

## 4. 断言策略

断言顺序：基础成功断言（HTTP `status_code == 200`；RPC 返回体 / BaseResp / StatusCode）、业务断言、`case.md` 通用断言。

若 `case.md` 给出自然语言或半结构化断言，必须生成可读、可审计的显式 Python `assert`，允许先提取 `resp.json()` / `resp.body` 到局部变量后断言。

## 5. 静态校验

Generate 阶段不执行 pytest，只做静态校验：

1. 生成文件存在且位于用户指定目录。
2. Python 代码可基本语法检查（如 `python3 -m py_compile`）。
3. 导入路径、`conftest.py` / client 路径与仓库结构一致。
4. 配置 JSON 语法合法。
5. 新建 / 修改的 `conftest.py`、client 语法合法且导入一致。
6. 仅修改本轮目标 case、相关 config、必要 `conftest.py` / client。
