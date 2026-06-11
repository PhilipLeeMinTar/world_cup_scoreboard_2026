# py_driver generate/config_client

本文件在需要同步 runtime config、复用 / 补齐 `conftest.py` 或 client 时读取。

## 1. conftest 检查范围

只允许检查用户确认的 `<target_case_dir>/conftest.py`：

- 存在时，将 `target_case_dir` 记为 `conftest_root`，并在 `<target_case_dir>/config/` 使用或创建配置文件。
- 不存在时，不得向父目录逐级查找，也不得使用 `**/conftest.py` 搜索其他目录；按 `../../resources/conftest_template.md` 在 `target_case_dir` 内最小生成。

不得默认 `Read` 完整 conftest。优先用 `Grep` 确认：`llm_config`、`test_env`、`tag_env`、`*_client` / `*_http_client`、`get_account` 等。只有 Grep 不足以判断时，才读取前 50 行。

## 2. runtime config 同步规则

只从当前 spec `.env` 读取与本次 case 所属 PSM 匹配的项；同一 PSM 多组环境都应同步，以便生成多个 `@pytest.mark.idc(...)`。

统一按 **runtime_config → TEST_ENV alias** 处理。常见 alias：`my_prod`、`va_prod`、`boei18n_prod`、`ttp_prod`、`ttp2_prod`、`my2_prod`、`my3_prod`、`sg_prod`。

对每条匹配项：

- `config_key = TEST_ENV`
- 配置文件名：`<config_dir>/<config_key>.json`
- JSON 顶层 key：`<config_key>`
- 本地执行时传入：`TEST_ENV=<config_key>`

配置文件名 stem、JSON 顶层 key、运行时 `TEST_ENV`、`llm_config[test_env]` 中的 `test_env` 必须一致。找不到 alias 时，先复用目标目录现有配置别名；仍无法确定则回退 `{idc}_{env}`；多候选时必须提示用户确认。

`@pytest.mark.idc(...)` 始终使用 `.env.idc` 原始值，与 `TEST_ENV` alias 解耦。

字段映射：`idc ← .env.idc`、`cluster ← .env.cluster`（缺省 `default`）、`tag_env ← .env.env`、`host ← .env.host`。不得将 `test_account` / `cookie` / `Authorization` / `Hex-Auth-Key` 写入 `.env` 或 config JSON。

更新策略：不存在则新建；缺当前 PSM 则增量加入；已有当前 PSM 且路由字段不同则仅更新当前 PSM 字段，不能清空或重写其他 PSM。

## 3. HTTP 鉴权来源与落点

非公开 HTTP API 必须显式处理 auth。优先级：

1. `case.md` 显式 headers / cookie → 写入 `TEST_DATA[*].request.headers`
2. 当前 spec `.env` 中该环境项的 `test_account` / `cookie` → 合并进 headers；冲突时以 `case.md` 为准
3. 目标目录附近 sibling case 的 auth 形态 → 仅作为候选补全，不能覆盖显式值；使用时记录 warning：`auth inferred from sibling case`

若最终 auth 仍缺失，而接口明显属于非公开 HTTP API，generate 输出 warning；execute(local) 前再次提示可能出现 `401` / `403`。

## 4. conftest / client 复用约定

1. fixture：复用 `llm_config`、`test_env`、`tag_env`、已有 `xxx_client` / `xxx_http_client` / `xxx_rpc_client`。fixture 通过测试函数参数注入，不默认显式 import `conftest.py`。
2. client：优先同业务目录 `client/`，其次全局 `clients.http_gen.*` / `clients.rpc_gen.*`。
3. 导入路径必须跟随 api_test 包路径，严禁写入本插件仓库路径。
4. 不强行改造已可用的 `conftest.py`；缺少少量 fixture 时做最小补丁。
5. 配置加载能力缺失时，按 `../../resources/conftest_template.md` 最小补齐。
6. client 缺失时，按 `../../resources/client_template.md` 最小补齐：HTTP 优先生成本地 `client/<psm_sanitized>.py`；RPC 优先复用 `clients.rpc_gen.*`；命名跟随同域风格。
