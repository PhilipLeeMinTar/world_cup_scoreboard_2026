# Environment & Auth Configuration Template

This document defines the **two configuration files** that live next to every generated Go test:

```
FEATURE_DIR/
└── test/
    ├── .env         # routing fields only — flat psm/... or services.<name> bindings
    └── auth.yaml    # business auth headers, organized as named profiles
```

Generated Go test files resolve this directory purely from `runtime.Caller(0)` + a relative path baked in at generation time — **no path env vars (`APITEST_ENV` / `APITEST_AUTH` / `APITEST_LOG_DIR`) are read.** The only env var honored at run time is `APITEST_TOKEN` (paas-gw JWT).

The full three-layer separation policy (routing `.env` / business `auth.yaml` / per-user `APITEST_TOKEN`) and its hard rules are defined in `SKILL.md §3`. This document only specifies the schema and value-sourcing rules for `.env` and `auth.yaml`.

---

## Part A — `.env` (routing only)

### Multi-service Field Definitions

| Field | Type | Required | Description | Default |
| --- | --- | --- | --- | --- |
| `default_service` | String | Required when `services` has 2+ entries | Default service key used when `HTTPRequest.Service` / `RPCRequest.Service` is omitted. | sole service key when only one service exists |
| `services.<name>.psm` | String | Yes | Service identifier, e.g. `tiktok.demo.<service_name>`. Ask the user if missing. | |
| `services.<name>.host` | String | No | Hostname for this service endpoint. Sourced from the matching service `Host` field in `FEATURE_DIR/test/task.md`. | |
| `services.<name>.env` | String | No | PPE/BOE environment name bound to this PSM. Sourced from the matching service `Env` field in `FEATURE_DIR/test/task.md`. | `prod` |
| `services.<name>.branch` | String | No | IDL branch bound to this PSM. Sourced from `IDL_Branch` (preferred) or `Branch` for this service. | `master` |
| `services.<name>.zone` | String | No | Mapped geographical region code for this service. Derived from `VRegion` via `zone_mapping.md`. | |
| `services.<name>.idc` | String | No | IDC (Internet Data Center) for this service. | |
| `services.<name>.cluster` | String | No | Cluster name within the IDC for this service. | `default` |

> Removed fields: `test_account`, `cookie`, `auth_*`, `headers`, JWT — these now live in `auth.yaml`. If you see them in `.env`, migrate them to `auth.yaml` and remove from `.env`.

### Template

```yaml
# <specDir>/.env
default_service: [SERVICE_KEY]  # Required when services has 2+ entries.

services:
  [SERVICE_KEY]:
    psm: [PSM]          # format: tiktok.demo.psm1
    host: [HOST]        # Source: matching `Host` in `FEATURE_DIR/test/task.md`
    env: [ENV]          # Source: matching `PPE Environment Name`; defaults to "prod"
    branch: [BRANCH]    # Source: matching `Branch`; defaults to "master"
    zone: [ZONE]        # Source: matching `VRegion`, map via `zone_mapping.md`
    idc: [IDC]          # Source: matching `IDC`
    cluster: [CLUSTER]  # Source: matching `Cluster`; defaults to "default"
# DO NOT add test_account / cookie / Hex-Auth-Key / Authorization here. Use auth.yaml.
```

### Worked Example

```yaml
default_service: main

services:
  main:
    psm: tiktok.demo.psm1
    host: ppe.demo-service1.tiktok.com
    env: ppe-music-service-us
    branch: feature/new-recommendation-flow
    zone: us-east-1
    idc: va6
    cluster: default

  dependency:
    psm: tiktok.demo.dependency
    host: ppe.demo-dependency.tiktok.com
    env: ppe-dependency-us
    branch: feature/dependency-flow
    zone: us-east-1
    idc: va6
    cluster: default
```

### Legacy Flat Format

Single-PSM `.env` files may still use the legacy flat shape. The runtime treats it as `services.default`, so existing generated tests keep working:

```yaml
psm: tiktok.demo.psm1
host: ppe.demo-service1.tiktok.com
env: ppe-music-service-us
branch: feature/new-recommendation-flow
zone: us-east-1
idc: va6
cluster: default
```

When a generated test calls a non-default downstream service, set `Service: "<service_key>"` in `apitest.HTTPRequest` / `apitest.RPCRequest`. Never inline `psm` / `host` / `env` / `branch` in Go code.

---

## Part B — `auth.yaml` (business auth headers, per profile)

`auth.yaml` is loaded by `apitest.NewContextFromSpec(t, specDir())` and exposed via `ctx.AuthHeaders()` (default / per-case mapped profile) and `ctx.AuthHeadersFor("<profile>")` (explicit override). When the file is absent, the runtime returns an empty header map — endpoints without business auth still work.

### Schema

```yaml
version: 1                        # schema version, currently 1
profiles:                         # named groups of HTTP headers
  <profile_name>:
    extends: <base_profile_name>  # optional, single string; resolved into a flat map at load time
    headers:                      # required when this profile contributes any header
      <Header-Name>: "<value>"    # values are strings; quoting is optional but recommended
case_profiles:                    # optional: map case_id → profile_name
  <case_id>: <profile_name>
```

### Resolution rules

The runtime picks headers for each call in this order:

1. **Explicit profile** — `ctx.AuthHeadersFor("admin")` returns `profiles.admin` (typo = hard fatal at run time).
2. **Per-case mapping** — `ctx.AuthHeaders()` first looks up the current `WithCaseID(...)` value in `case_profiles`.
3. **`default` profile fallback** — otherwise returns `profiles.default`.
4. **Empty map** — if `auth.yaml` is missing or no profile matches.

### `extends` inheritance

- The base profile's headers are merged in first; the current profile's `headers` block overrides on collision.
- Cycles are detected and rejected at load time.
- `extends` accepts a single profile name; chains (`A → B → C`) are resolved recursively.

### Template

```yaml
# <specDir>/auth.yaml
version: 1

profiles:
  default:
    headers:
      Hex-Auth-Key: "<key>"
      Cookie: "sessionid=<value>"
      Hex-Login-User-Info: "<base64-or-jwt>"

  admin:
    extends: default               # inherits default's Cookie + Hex-Login-User-Info
    headers:
      Hex-Auth-Key: "<admin_key>"  # overrides only the key

  no_auth:
    headers: {}                    # explicit empty profile for negative tests

case_profiles:
  TC-G02-01: admin                 # this specific case runs as admin
  TC-G02-50: no_auth               # this case sends no auth header on purpose
```

With this file:

- `ctx.AuthHeaders()` for an unmapped case returns the **default** profile.
- `ctx.AuthHeaders()` for `TC-G02-01` returns the **admin** profile (per `case_profiles`).
- `ctx.AuthHeadersFor("admin")` always returns the **admin** profile, regardless of `caseID`.
- `ctx.AuthHeadersFor("ghost")` is a hard fatal because no `ghost` profile is defined.

### Layering non-auth headers

Non-sensitive HTTP headers (`Content-Type`, `X-Trace-Id`, ...) are added per request without polluting the auth file:

```go
h := ctx.AuthHeaders()
h["Content-Type"] = "application/json"
h["X-Trace-Id"] = traceID
req.Headers = h
```

---

## Usage Notes

- **Sourcing values.** `.env` routing values come from `FEATURE_DIR/test/task.md`; `auth.yaml` profile values come from `case.md → Request Parameters → Headers` plus the user's test-account credentials. Required auth missing → stop or skip with a clear reason; never issue unauthenticated requests.
- **Gateway selection.** Inferred from `zone` / `idc` / `env` by the runtime. Domain table lives in `runtime/README.md §4.4`.
- **Defaults.** `cluster` defaults to `default` when unset.
- **Path autonomy.** Generated Go computes `<specDir>` via `runtime.Caller(0) + "{{SPEC_DIR_REL}}"`; clone-and-run users only need `export APITEST_TOKEN=<jwt>` and `go test ./...`. Logs land in `<specDir>/api_test_logs/`.
