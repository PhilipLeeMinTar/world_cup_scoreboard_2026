# API Mind CLI

`api-mind` is a command-line interface tool for interacting with internal ByteDance HTTP and RPC services via a gateway. It supports structured logging, automatic retries, and permission handling.

## Installation

```bash
bash scripts/install.sh
```

## Commands

### `api-mind generate-param`

The `generate-param` command allows you to generate example parameters for HTTP or RPC requests using Bits AI.

#### Common Options

- `--psm`: Target service PSM (Required).
- `--type`: Protocol type: `http` or `rpc` (Required).
- `--token`: JWT token for api-mind tool authentication (Required).
- `--idl-version`: IDL version branch (default: `master`).
- `--query`: Query parameters as JSON string.
- `--request` / `--request-body`: Request body content.
- `--headers`: Request headers as JSON string.
- `--cookies`: Cookies as JSON string.

#### HTTP Options

- `--path`: HTTP path (Required).
- `--method`: HTTP method (Required).

#### RPC Options

- `--func-name`: RPC function name (Required).

#### Examples

**HTTP Example:**
```bash
api-mind generate-param \
  --psm "my.service.psm" \
  --type http \
  --path "/api/v1/users" \
  --method GET \
  --token "your-jwt-token" \
  --idl-version "feat/get_user_info"
```

**RPC Example:**
```bash
api-mind generate-param \
  --psm "my.service.psm" \
  --type rpc \
  --func-name "GetUserInfo" \
  --token "your-jwt-token" \
  --idl-version "feat/get_user_info"
```

### `api-mind test-exec`

The `test-exec` command executes automated test suites defined in YAML or Markdown files. It supports HTTP and RPC testing with assertions, variable extraction, and multi-step workflows.

#### Usage

```bash
api-mind test-exec <FILE> [OPTIONS]
```

#### Arguments

- `FILE`: Path to test suite file (YAML `.yaml`).

#### Options

- `--token`: JWT token for api-mind tool authentication (or set `API_MIND_TOKEN` env var).
- `--env-file`: Path to environment file (default: `./.env`).
- `--env`: Override environment (e.g., `ppe_feat_user`).
- `--log-dir`: Directory to save execution logs (default: current directory).
- `--stop-on-failure`: Stop execution on first failure (default: continue).
- `--dry-run`: Parse only, do not execute tests.
- `--verbose`, `-v`: Verbose output.

#### Test Suite File Format

Test suites can be defined in following format:

**Format 1: Pure YAML File (`.yaml`)**

```yaml
test_suite:
  name: "API Test Suite for My Service"
  test_cases:
    - id: "TC_001"
      name: "Verify basic API response"
      priority: "P0"
      description: "Validates that the /v1/api endpoint returns the correct status code and business code."
      steps:
        - name: "Call /v1/api endpoint"
          request:
            type: "HTTP"
            api: "/v1/api"
            method: "POST"
            headers:
              Content-Type: "application/json"
            params:
              key: "value"
            body:
              id: "123"
          extract: {} # Not needed for a single API test without data chaining
          asserts:
            - expression: "status_code == 200"
              description: "HTTP status code should be 200"
            - expression: "jsonpath('$.code') == 0"
              description: "Business code in the response body should be 0"
```


#### Test Suite Structure

**Env File Section**

```yaml
- host: "https://api.example.com"      # Base URL for HTTP requests
  psm: "my.service.psm"             # PSM for RPC/HTTP calls
  env: "prod"                       # Environment: prod, boe, etc.
  cluster: "default"                # Cluster name
  idc: ""                            # IDC
  token: ""                          # JWT token for api-mind tool authentication (or use --token option)
  zone: ""                           # Zone 
  branch: ""                         # Branch
```

**Test Case Definition**

```yaml
test_cases:
  - id: "test_001"                  # Unique test case ID
    name: "Test Case Name"          # Descriptive name
    priority: "P0"                  # Priority: P0, P1, P2
    description: "Verify basic API response"
    global_variables:                # Case-level variables
      user_id: "123"
    steps:                          # Test steps
      - name: "Step Name"
        request:
          type: "HTTP"              # Type: HTTP or RPC
          api: "/api/path/${{user_id}}"
          method: "POST"
          headers:
            Content-Type: "application/json"
          params:
            key: "value"
          body:
            key: "value"
        extract:                   # Variable extraction
          var_name: "$.data.field"
        asserts:                    # Assertions
          - expression: "status_code == 200"
            description: "HTTP status code should be 200"
          - expression: "jsonpath('$.code') == 0"
            description: "Business code in the response body should be 0"
```

#### Variable System

**Variable Precedence** (highest to lowest):
1. **Extracted variables** - From `extract` in previous steps
2. **Case variables** - Defined in `global_variables` section

**Usage in Steps**:
```yaml
steps:
  - request:
      api: "/api/user/${{user_id}}"    # Use variable in path
      body:
        name: "${{user_name}}"          # Use variable in body
```

#### Assertion Syntax

Supported assertions:
```yaml
asserts:
  - expression: "status_code == 200"         # Status code check
    description: "HTTP status code should be 200"
  - expression: "jsonpath('$.code') == 0"    # JSONPath expression
    description: "Business code in the response body should be 0"              
  - expression: "$.data.name == 'John'"      # String comparison
    description: "name should be John"
  - expression: "typeof $.data.id == 'int'"  # Type checking
    description: "ID type should be int"
  - expression: "len($.data.items) > 1"      # Length check
    description: "number of items should be more than 1"
```

#### Examples

**Example 1: Basic HTTP Test**:
```bash
api-mind test-exec tests/test_suite.yaml \
  --token "your-jwt-token" \
```

**Example 2: With Environment Override**:
```bash
api-mind test-exec tests/test_suite.yaml \
  --token "your-jwt-token" \
  --env boe \
  --verbose
```

**Example 3: Dry Run (Parse Only)**:
```bash
api-mind test-exec tests/test_suite.yaml \
  --dry-run
```

**Example 4: Stop on First Failure**:
```bash
api-mind test-exec tests/test_suite.yaml \
  --token "your-jwt-token" \
  --stop-on-failure
```

#### Environment Variables

- `API_MIND_TOKEN`: Default JWT token if `--token` not provided

#### Hidden Parameters (Using Defaults)
The following parameters are not exposed in the CLI but use default values internally:
- `serialization`: `json`
- `request_timeout`: `10000` ms
- `connect_timeout`: `10000` ms
- `retry`: `3`
- `retry_delay`: `5` seconds
- `bam_psm_cluster`: `2` (I18N)
- `idl_source`: `1` (Codebase)
- `branch`: ``
#### Logging
Logs are saved in the directory specified by `--log-dir`. The filename format is `api_mind_{case_id}.log`.
**Log Format**
The log file is organized into the following sections, separated by `---` delimiters:
**Structure**:
```
--- Request: Business (Curl) ---
curl --location --request GET 'http://psm.service/api/v1/endpoint' \
  --header 'Authorization: Bearer ...' \
  --header 'Content-Type: application/json' \
  --data-raw '{...}'

--- Response: Business (JSON) ---
{
  "code": 0,
  "message": "success",
  "data": { ... }
}

--- Response: Business Headers (JSON) ---
{
  "Content-Type": "application/json; charset=utf-8",
  "X-Tt-Logid": "20260330..."
}

--- Metadata: Business ---
Business.StatusCode: 200
Business.LogID: 20260330...

--- Metadata: Gateway ---
Gateway.Timestamp: 2026-03-30T17:25:05.097059
Gateway.HTTPStatusCode: 200
Gateway.LatencyMs: 1784.58
Gateway.RetryConfig: 3
Gateway.HasPermission: True
Gateway.ErrorCode: 0
Gateway.LogID: 20260330...

--- Runtime: Gateway Request (Curl) ---
curl --location --request POST https://gateway.example.com/api/v1/http_request \
  --header 'Content-Type: application/json' \
  --data-raw '{...}'

--- Runtime: Gateway Response ---
{
  "has_permission": true,
  "error_code": 0,
  "data": "{...}",
  "status_code": 200,
  "resp_headers": { ... },
  "log_id": "20260330..."
}
```
**Section Descriptions**:
- `Request: Business (Curl)`: The business-level curl command for reproducing the request.
- `Response: Business (JSON)`: The parsed business response body (data source for `jsonpath()` assertions).
- `Response: Business Headers (JSON)`: The response headers from the business service.
- `Metadata: Business`: Business-level metadata including `StatusCode` and `LogID`.
- `Metadata: Gateway`: Gateway-level metadata including `HTTPStatusCode`, `HasPermission`, `ErrorCode`, etc.
- `Runtime: Gateway Request/Response`: Raw gateway request and response details for debugging. **Not used for assertions.**
**URL Construction**
The Business Curl URL is constructed based on available parameters:
1. If `--host` is provided: `https://{host}{path}` (or `http://` if specified)
2. If `--host` is empty but `--psm` is provided: `http://{psm}{path}`
3. If both are empty: `{path}` (relative path)
For RPC requests, the URL format is: `rpc://{psm}/{func_name}`
