# apitest — Go 接口自动化运行时

`apitest` 是一个轻量 Go 库，封装了基于 paas-gw 的接口自动化测试主流程：

解析 `<specDir>/.env` + `<specDir>/auth.yaml` → 构造 paas-gw 请求 → 发送 → 解析下游响应 → 跑断言 → 抽取变量 → 写 `<specDir>/api_test_logs/apitest_<case>.log`。

写完的 `*_test.go` 直接 `go test` 跑，无需任何外部 CLI。任何拉到仓库的人只需 `export APITEST_TOKEN=<jwt>` 就能本地复现，**不再需要配置 `APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR`**。

## 1. 何时使用

- 由 `api-mind` skill 自动生成接口自动化测试代码（首选）。
- 手写一个一次性的接口验证 / 联调脚本。

不适合写真正的内嵌 unit test —— 它会真的发 HTTP 到 paas-gw，是 *integration test*。

## 2. 目录约定

每个被测方法一个目录，文件命名 `<method>_test.go`：

```
tests/integration/
├── apitest/                              # 本运行时库
└── <method_snake_case>/
    └── <method_snake_case>_test.go       # 内含 specDir() 助手函数

<feature_dir>/test/                       # 测试输入与运行时配置 (= specDir)
├── .env                                  # 路由字段
├── auth.yaml                             # 业务鉴权 profile
└── api_test_logs/                        # 运行时写入
```

Demo：[`tests/integration/get_all_policy_group_meta/`](../get_all_policy_group_meta/)。

## 3. 最小示例

```go
package my_method_test

import (
    "path/filepath"
    "runtime"
    "testing"

    "<go list -m>/tests/integration/apitest"
)

// specDir 用源码所在目录推算 FEATURE_DIR/test/，整套配置随仓库走，
// 任何人 clone 后无需调整路径即可运行。
func specDir() string {
    _, thisFile, _, _ := runtime.Caller(0)
    return filepath.Join(filepath.Dir(thisFile), "../../../path/to/feature/test")
}

func TestMyMethod(t *testing.T) {
    ctx := apitest.NewContextFromSpec(t, specDir()).WithCaseID("TC-01")

    resp := apitest.CallRPC(ctx, apitest.RPCRequest{
        Method:  "RuntimeGetAllPolicyGroupMeta",
        Headers: ctx.AuthHeaders(),
        Body: apitest.JSON{
            "TenantId": "tiktok-test-automation",
        },
    })

    apitest.Assert(t, resp,
        "$.BaseResp.StatusCode == 0",
        "typeof $.PolicyGroups == 'list'",
        "len($.PolicyGroups) > 0",
    )
}
```

生成代码默认使用 `NewContextFromSpec + ctx.AuthHeaders + CallHTTP/CallRPC + Assert` 的扁平结构，便于 review 和最小化样板代码。

## 4. 配置目录（specDir）

`apitest.NewContextFromSpec(t, specDir())` 把所有运行时配置都收敛到 `specDir` 这一个目录里：

```
<specDir>/
├── .env             # 路由字段（必需）
├── auth.yaml        # 业务鉴权 profile（可选；缺省即视为无业务鉴权）
└── api_test_logs/   # 运行时写入
```

### 4.1 `.env` — 路由专用

```yaml
default_service: main

services:
  main:
    psm: tns.tsop.ms_api
    env: boe_default
    branch: master
    zone: China-BOE
    idc: boe
    cluster: runtime

  dependency:
    psm: tns.tsop.dependency
    env: boe_dependency
    branch: feature/dependency
    zone: China-BOE
    idc: boe
    cluster: runtime
```

单 PSM 老格式仍然兼容，会被 runtime 视为 `services.default`：

```yaml
psm: tns.tsop.ms_api
env: boe_default
branch: master
zone: China-BOE
idc: boe
cluster: runtime
```

`.env` **只放路由字段**：单 PSM 可用 `psm` / `host` / `env` / `branch` / `zone` / `idc` / `cluster`；多 PSM 使用 `default_service` + `services.<service_key>`，并将这些字段绑定在同一个 service 下。生成测试通过 `HTTPRequest.Service` / `RPCRequest.Service` 选择非默认 service；省略 `Service` 时使用 `default_service`。`test_account`、Cookie、Authorization、Hex-Auth-Key、Hex-Login-User-Info 等业务鉴权材料**不得**写入 `.env`。

### 4.2 `auth.yaml` — 业务鉴权 profile

```yaml
version: 1

profiles:
  default:
    headers:
      Cookie: "sessionid=AAA-USER-SESSION; lang=en"
      Hex-Auth-Key: "user-key-9f8e7d6c"

  admin:
    extends: default
    headers:
      Hex-Auth-Key: "admin-key-1234abcd"

case_profiles:
  TC-G02-99: admin       # 该 case 自动用 admin profile
```

生成代码通过两个入口取 headers：

- `ctx.AuthHeaders()` — 默认；按当前 `WithCaseID(...)` 在 `case_profiles` 里查表，命中即用，否则退回 `profiles.default`，再否则返回空 map（无业务鉴权场景兼容）。
- `ctx.AuthHeadersFor("<profile>")` — 显式覆盖，常用于「同一接口跑两个身份对照」（admin vs user、越权场景）。引用未定义的 profile 名是**硬 fatal**。

`extends` 支持一级继承，会在 load 阶段被展平为扁平 map；环检测内置。

业务鉴权值**直接写入 `auth.yaml`** 并随仓库提交，所有协作者共享同一份鉴权材料；**不再**让生成代码内联字面值。

### 4.3 PaaS-GW JWT —`APITEST_TOKEN`

PaaS-GW 外层 JWT 由用户级、有时效的 `APITEST_TOKEN` 环境变量提供（来自 `user_jwt` 工作流步骤或手动 `export`）。**不写入** `.env`、**不写入** `auth.yaml`、**不入** git。运行时未设置该变量时直接 `t.Skip` 并给出可执行提示。

### 4.4 网关选择

由 runtime 的 gateway 层根据当前请求解析出的 service binding 的 `Zone` / `IDC` / `Env` 自动推导，不需要也不支持在 `.env` 中额外配置域名。默认域名遵循 Explorer OpenAPI 控制面表：CN `https://paas-gw.byted.org/api/v1`，BOE `https://paas-gw-boe.byted.org/api/v1`，BOEI18N/BOETTP `https://paas-gw-boei18n.byted.org/api/v1`，I18N 办公网 `https://bc-useastdt-gw.tiktok-row.net/api/v1`，GCP `https://paas-gw-gcp.tiktoke.org/api/v1`，TTP `https://paas-gw-tx.tiktokd.org/api/v1`，SINF `https://paas-gw.sinf.net/api/v1`。

### 4.5 Transport 模式（`APITEST_MODE`）

默认模式是 **gateway**（经 paas-gw 发 HTTP/RPC）：

```bash
export APITEST_TOKEN=<paas-gw-jwt>
GOWORK=off go test -v ./tests/integration/<method_snake>/...
```

**local_rpc** 模式在 `go test` 进程内用 Kitex 客户端直连目标实例，只支持 RPC step：

```bash
export APITEST_MODE=local_rpc
export TARGET_IPPORT=127.0.0.1:8888   # 或 .env host
GOWORK=off go test -v ./tests/integration/<method_snake>/...
```

- `local_rpc` **不需要** `APITEST_TOKEN`。
- skill baseline 自带 `local_rpc_stub.go`；业务仓库需用 **repo overlay** `tests/integration/apitest/local_rpc.go` 实现 `NewLocalRPCTransport`，并在 Workflow §0 同步时保留 overlay、不覆盖。
- overlay 实现应：按 `Step.API` 反射调用 Kitex client；JSON body unmarshal 到 request struct；响应归一化为 JSON-like map；补充 `Base.Extra["user_extra"]` 与 `RpcContext` → `RPC_PERSIST_*` 字段。可通过 `E2E_TENANT`、`E2E_USER`、`E2E_OPEN_ID`、`E2E_HOST`、`TARGET_ENV`、`E2E_RPC_TIMEOUT_SEC` 调整。

## 5. 变量与解析

三层作用域，优先级 高 → 低：

1. 上一步 `Extract` 出来的（per-case 内）
2. `Case.Vars`
3. `Suite.WithGlobalVars(...)`

两套占位符语法：

| 语法 | 用途 | 类型行为 |
| --- | --- | --- |
| `${{var}}` | **保留原类型**：单独占位时返回原始 `int / list / map / bool` | 适合放在 JSON Body 里 |
| `${var}` | **始终字符串化**：内嵌到字符串里做拼接 | 适合 URL / header |

举例：

```go
Body: apitest.JSON{
    "Id":   "${{policy_group_id}}", // 保持 int64
    "Path": "/v1/${tenant_id}/list", // 字符串拼接
}
```

## 6. 断言语法

| 写法 | 含义 |
| --- | --- |
| `status_code == 200` | 网关返回 HTTP 状态码 |
| `$.code == 0` | JSONPath 简写，等同 `jsonpath('$.code') == 0` |
| `$.data.items[0].id != null` | 任意比较 |
| `len($.data.items) > 1` | 长度断言 |
| `typeof $.data.id == 'int'` | 类型断言（int / float / string / boolean / list / dict / null） |
| `'admin' in $.data.roles` | 包含断言 |
| `jsonpath('$.code') == 0` | 显式 `jsonpath()` 调用 |

底层使用内置轻量断言解析器，`$.x.y` 会先被改写为 `jsonpath('$.x.y')` 再求值。

## 7. 抽取语法

```go
Extract: map[string]string{
    "first_id":    "$.data.items[0].id",
    "ticket_id":   "$.data.TicketId",
    "all_ids":     "$.data.items[*].id", // gjson 支持的简单数组通配
}
```

抽出来的值会立即写入 `extracted` 命名空间，下一步可以用 `${{first_id}}` 引用。

## 8. 日志输出

每个 case 写一份 `<specDir>/api_test_logs/apitest_<case_id>.log`，分段格式与 `resources/test_report_guide.md` 兼容：

```
===== Step: RuntimeGetAllPolicyGroupMeta =====
--- Request: Business (Curl) ---
curl --location --request POST 'rpc://tns.tsop.ms_api/RuntimeGetAllPolicyGroupMeta' ...

--- Request: Body ---
{ "TenantId": "tiktok-test-automation" }

--- Response: Business (JSON) ---
{ "PolicyGroups": [ ... ] }

--- Metadata: Business ---
Business.StatusCode: 200
Business.LogID: 20260418yyyy

--- Metadata: Gateway ---
Gateway.URL: https://paas-gw-boe.byted.org/api/v1/rpc_request
Gateway.LogID: 20260418xxxx
Gateway.LatencyMs: 142.3
```

日志目录由 `NewContextFromSpec` 强制为 `<specDir>/api_test_logs/`，不再支持 `APITEST_LOG_DIR` 覆盖。

## 9. 测试组织建议

- **Priority**：仅做信息标注；想强制顺序就把 P0 的 case 放前面，`go test -v` 按声明顺序跑。
- **stop on failure**：用 `t.FailNow()` / `t.Fatal*` 就能在第一个失败处中断；本库的 `runStep` 故意只调 `t.Errorf`，让多个断言失败都能看到。
- **并行**：默认串行，因为大多数接口测试有共享态。需要并行就在你的 Test 里 `t.Parallel()`。

## 10. 依赖

- `github.com/tidwall/gjson`  — JSONPath 抽取

`.env` 与 `auth.yaml` 都由 runtime 内置的极简解析器解析，不依赖完整 YAML 解析库。

均已在 `go.mod` 中显式声明。Library 内部只用 `testing.T.Errorf/Fatalf`，没有强依赖 `testify`，但用户在自己的 `*_test.go` 里可以自由 `import testify`。
