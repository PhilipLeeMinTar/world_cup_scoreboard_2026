# API Test Case Template

## 1. Overview

This document provides the standard template and guide for defining API and RPC test cases in YAML format. The purpose is to establish a unified, clear, and maintainable structure for automated testing. It covers single-API tests, multi-step chained API scenarios, variable extraction, and comprehensive assertions.

## 2. Schema Definition

The following sections define the structure and fields for a test suite file.

### 2.1. Top-Level Structure: `test_suite`

The root object of a test case file.

| Field | Required | Type | Description |
|---|---|---|---|
| `name` | Yes | String | A descriptive name for the entire test suite, e.g., "API Test Suite for User Service". |
| `test_cases`| Yes | List | A list containing one or more `test_case` objects. |

### 2.2. Test Case Object: `test_case`

Defines a single, self-contained test scenario.

| Field | Required | Type | Description |
|---|---|---|---|
| `id` | Yes | String | A unique identifier for the test case, e.g., "TC_001". |
| `name` | Yes | String | A short, descriptive name for the test case's objective. |
| `priority` | Yes | String | The execution priority of the test case. See Best Practices for allowed values. |
| `description`| No | String | A more detailed explanation of the test case's purpose and scope. |
| `global_variables` | No | Map | A key-value map of variables that are shared across all steps within this test case. |
| `steps` | Yes | List | An ordered list of `step` objects to be executed sequentially. |

### 2.3. Step Object: `step`

Represents a single action or API call within a test case.

| Field | Required | Type | Description |
|---|---|---|---|
| `name` | Yes | String | A concise name describing the purpose of the step, e.g., "Call login API". |
| `purpose` | No | String | Provides additional context for the step, explaining why it is being executed. |
| `request` | Yes | Object | An object defining the API or RPC request to be made. |
| `extract` | No | Map | A key-value map for extracting data from the response body and storing it as variables for subsequent steps. |
| `asserts` | Yes | List | A list of `assert` objects to validate the response. |

### 2.4. Request Object: `request`

Details of the outbound request.

| Field | Required | Type | Description |
|---|---|---|---|
| `type` | Yes | String | The request protocol type. Allowed values: `"HTTP"`, `"RPC"`. |
| `api` | Yes | String | The target API endpoint. For `HTTP`, this is the URL path (e.g., `/v1/users`). For `RPC`, this is the exact function name from the IDL. (e.g., `GetUserList`) |
| `method` | Yes (for HTTP) | String | The HTTP method (e.g., `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`). |
| `headers` | No | Map | A key-value map of request headers. |
| `params` | No | Map | A key-value map of URL query parameters. |
| `body` | No | JSON/Object | The request payload for `POST` or `PUT` requests, or the RPC request body. |

### 2.5. Extract Object: `extract`

Used for response data extraction.

The `extract` field is a key-value map where:
- **key**: The name of the variable to store the extracted value.
- **value**: A [JSONPath](#32-jsonpath-for-data-extraction-and-assertion) expression to locate the data within the response JSON body.

### 2.6. Assert Object: `assert`

Defines a single validation rule.

| Field | Required | Type | Description |
|---|---|---|---|
| `expression`| Yes | String | A boolean expression that evaluates the response. If it returns `true`, the assertion passes. |
| `description`| Yes | String | A human-readable description of what the assertion is verifying. |

## 3. Variables and Expressions

### 3.1. Variable Interpolation

Variables allow you to create dynamic and chained test cases. Variables can be defined in the `global_variables` block of a test case or extracted from a response using the `extract` block.

To use a variable, wrap its name in `${{...}}`.

- **Syntax**: `${{variable_name}}`
- **Scope**:
    - `global_variables`: Available in all steps of the test case.
    - `extract` variables: Available in all subsequent steps after they are defined.

### 3.2. JSONPath for Data Extraction and Assertion

JSONPath is used to query data from JSON response bodies.
- In the `extract` block, the JSONPath string is the value.
- In `asserts` expressions, the `jsonpath()` function is used to retrieve a value for comparison.

**Common `jsonpath()` Usage:**
- `jsonpath('$.data.items[0].id')`: Selects the `id` of the first item in the `items` array under the `data` object.
- `jsonpath('$.code')`: Selects the value of the `code` field at the root level.

**Available fields in Assertion Expressions:**
- `status_code`: The HTTP status code of the response.
- `jsonpath('...')`: A function to query the JSON body.
- `typeof(...)`: A function to check the data type of a value. Its return value is one of: `'int'`, `'str'`, `'array'`, `'object'`, `'float'`, `'bool'`, `'null'`.

## 4. Examples

### 4.1. Example 1: Single API Test Case

This example shows a basic test case that calls a single API and validates its response.

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

### 4.2. Example 2: Chained API Test Case

This example demonstrates a more complex scenario where data extracted from the first API call is used in the second.

```yaml
test_suite:
  name: "API Test Suite for User Management"
  test_cases:
    - id: "TC_002"
      name: "Get user details from user list"
      priority: "P1"
      description: "First, fetch the user list, then use the first user's ID to fetch their details."
      global_variables:
        common_param: "value" # A common parameter available in all steps of this test case
      steps:
        - name: "Find a valid user ID"
          purpose: "Get an available user_id from the user list for use in subsequent steps."
          request:
            type: "HTTP"
            api: "/v2/get_user_list"
            method: "GET"
            headers:
              Content-Type: "application/json"
            params:
              key: "value"
              common_param: "${{common_param}}" # Reference a global variable
          extract:
            extracted_id: "$.data.user_list[0].id" # Extract the user ID using a JSONPath expression
          asserts:
            - expression: "status_code == 200"
              description: "User list API should return 200"
            - expression: "jsonpath('$.code') == 0"
              description: "User list API business code should be 0"
            - expression: "typeof(jsonpath('$.status')) == 'str'"
              description: "The 'status' field should be of type string ('str')"

        - name: "Get user info"
          purpose: "Get user details based on the extracted_id from the previous step."
          request:
            type: "HTTP"
            api: "/v2/user/info"
            method: "GET"
            headers:
              Content-Type: "application/json"
            params:
              common_param: "${{common_param}}" # Reuse the global variable
              user_id: "${{extracted_id}}" # Reference the variable extracted from the previous step
          extract: {} # Can be used to extract more variables if needed
          asserts:
            - expression: "status_code == 200"
              description: "User info API should return 200"
            - expression: "jsonpath('$.code') == 0"
              description: "User info API business code should be 0"
            - expression: "jsonpath('$.data.name') != null"
              description: "User name should not be null"
            - expression: "jsonpath('$.data.status') in ['active', 'inactive']"
              description: "User status should be one of the allowed values"
            - expression: "exists(jsonpath('$.data.email')) == true"
              description: "Response should contain the email field"
            - expression: "len(jsonpath('$.data.name')) > 0 and typeof(jsonpath('$.data.name')) == 'str'"
              description: "User name should be a non-empty string"
```

## 5. Best Practices

- **Priorities**: Use a simple priority system to categorize test cases.
    - `P0`: Critical-path tests. A failure indicates a major service outage. Must always pass.
    - `P1`: Core feature tests. A failure indicates a significant functional defect.
    - `P2`: Non-critical tests, edge cases, or less important features.

- **Naming Conventions**:
    - `id`: Use a consistent prefix and numbering system (e.g., `TC_AUTH_001`, `TC_USER_002`).
    - `name`: Write clear, concise descriptions of the test's goal.

- **Assertions**:
    - Be specific. Prefer `jsonpath('$.code') == 0` over a less precise check.
    - Add a `description` for every assertion to explain its intent.
    - Validate both HTTP status codes and business-level codes/data in the payload.
    - Add type checks (`typeof(...)`) to ensure data integrity.

## 6. Assertion Syntax & Type Rules

In `asserts`, each item must use an expression string. The following operators and helper functions are supported.

### 6.1. Basic Comparison Operators

Supported operators: `==`, `!=`, `>`, `>=`, `<`, `<=`.

- **Examples**:
  ```
  "status_code == 200"
  "status_code != 500"
  "jsonpath('$.data.total') > 0"
  "jsonpath('$.data.total') >= 1"
  "jsonpath('$.data.score') < 100"
  "jsonpath('$.data.score') <= 99.5"
  ```

### 6.2. Collection / Containment Checks

- **`in`**: Checks if the left operand is a member of the right-hand collection (list/array).
  ```
  "jsonpath('$.code') in [0, 2000]"
  "jsonpath('$.status') in ['active', 'pending']"
  ```
- **`not in`**: The negation of `in`. Checks that the left operand is NOT a member of the right-hand collection.
  ```
  "jsonpath('$.code') not in [1001, 1002, 1003]"
  ```
- **`contains`**: Checks if the left operand (string or array) contains the right operand.
  ```
  "jsonpath('$.message') contains 'success'"
  "jsonpath('$.roles') contains 'admin'"
  ```
- **`not contains`**: The negation of `contains`. Checks that the left operand does NOT contain the right operand.
  ```
  "jsonpath('$.message') not contains 'error'"
  "jsonpath('$.tags') not contains 'deprecated'"
  ```

### 6.3. String Matching

- **`startswith`**: Checks if a string value starts with the given prefix.
  ```
  "jsonpath('$.request_id') startswith 'req-'"
  "jsonpath('$.url') startswith 'https://'"
  ```
- **`endswith`**: Checks if a string value ends with the given suffix.
  ```
  "jsonpath('$.filename') endswith '.json'"
  "jsonpath('$.email') endswith '@example.com'"
  ```

### 6.4. Null and Boolean Checks

- **Null comparison**: Use `null` to check whether a field's value is null.
  ```
  "jsonpath('$.data.error') == null"
  "jsonpath('$.data.deleted_at') != null"
  ```
  **Important**: `== null` only matches fields that **exist** with a `null` value. If the field does not exist in the response at all, the assertion will **FAIL** (not pass). To check whether a field exists, use `exists()` from section 6.5 instead.
- **Boolean comparison**: Use `true` / `false` (without quotes) to compare boolean values.
  ```
  "jsonpath('$.data.is_active') == true"
  "jsonpath('$.data.is_deleted') == false"
  ```

### 6.5. Existence Checks

Use the `exists()` function to check whether a field exists in the response JSON body. Returns `true` if the field is present (even if its value is `null`), `false` otherwise.

- **Examples**:
  ```
  "exists(jsonpath('$.data.user_id')) == true"
  "exists(jsonpath('$.data.deprecated_field')) == false"
  ```

### 6.6. Length Checks

Use the `len()` function to get the length of an array, string, or object. It can be combined with any comparison operator.

- **Examples**:
  ```
  "len(jsonpath('$.data.user_list')) > 0"
  "len(jsonpath('$.data.user_list')) >= 1"
  "len(jsonpath('$.errors')) == 0"
  "len(jsonpath('$.data.name')) <= 50"
  ```

### 6.7. Type Checks

Use the `typeof()` function to get the data type of a field. The return value must be one of the following strings: `'int'`, `'str'`, `'array'`, `'object'`, `'float'`, `'bool'`, `'null'`.

**Number type rule**: A JSON number without a decimal point is `'int'` (e.g., `10`), a number with a decimal point is `'float'` (e.g., `10.0`, `9.99`).

- **Examples**:
  ```
  "typeof(jsonpath('$.data.count')) == 'int'"
  "typeof(jsonpath('$.data.score')) == 'float'"
  "typeof(jsonpath('$.status')) == 'str'"
  "typeof(jsonpath('$.data.is_valid')) == 'bool'"
  "typeof(jsonpath('$.data')) == 'object'"
  "typeof(jsonpath('$.data.user_list')) == 'array'"
  "typeof(jsonpath('$.data.deleted_at')) == 'null'"
  ```

### 6.8. Logical Operators

Use `and` and `or` to combine multiple conditions in a single expression.

- **`and`**: Both conditions must be true.
  ```
  "jsonpath('$.code') == 0 and jsonpath('$.data.total') > 0"
  "status_code == 200 and jsonpath('$.message') contains 'ok'"
  ```
- **`or`**: At least one condition must be true.
  ```
  "jsonpath('$.code') == 0 or jsonpath('$.code') == 2000"
  "jsonpath('$.status') == 'active' or jsonpath('$.status') == 'pending'"
  ```

### 6.9. JSONPath Conventions

Always use the `jsonpath('$.path.to.field')` function to access fields in the JSON response body. If the JSONPath expression returns an array, you can access its elements by index (e.g., `$.data.list[0].id`) or use the `len()` function to check its size.