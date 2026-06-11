# Overpass Core Concepts

## Overview

Overpass is TikTok's unified RPC calling solution built on top of the Kitex framework. It automates code generation and provides a streamlined API for making RPC calls across microservices.

## Architecture

### Repository Generation Model

Overpass automatically creates a dedicated code repository for each PSM (Product Service Module):
- Auto-generates `kitex_gen` code
- Creates Client initialization code
- Provides common capability encapsulation
- Automatically updates when IDL changes

### White-list Mechanism

Due to the large number of RPC services, Overpass uses a white-list approach:
1. Visit https://overpass.arcosite.bytedance.com (or overpass.bytedance.net)
2. Search for your target PSM in "IDL Information Query"
3. Click "Generate Overpass Repository"
4. Wait for repository creation (typically a few seconds)

### Repository Structure

```
code.byted.org/overpass/p_s_m/
├── go.mod
├── go.sum
├── kitex_gen/           # Kitex generated files
├── overpass/            # Build check files
│   └── build_check/
└── rpc/                 # RPC encapsulation
    └── p_s_m/
        ├── overpass_client.go      # Core Overpass Client
        ├── overpass_default.go     # Global client & methods
        ├── overpass_extends.go     # Extension interfaces
        └── overpass_gomock.go      # Go Mock support
```

## Core Components

### Overpass Client

The `OverpassClient` is the primary abstraction that wraps Kitex Client with additional capabilities:
- Error handling and logging
- Default method encapsulation
- Raw call support
- Mock integration

### Method Call Patterns

#### 1. Default Method (Simplified)
Automatically flattens non-optional request fields into function parameters:

```go
// IDL definition
struct MyReq {
    1: required string name,
    2: string id
    3: optional string address
}

// Generated method signature
func Hello(ctx context.Context, Name string, Id string, callOptions ...interface{}) (*MyResp, error)

// Usage
resp, err := p_s_m.Hello(ctx, "Tom", "123", opts...)
```

#### 2. Raw Call Method (Original)
Uses the original request structure:

```go
req := &MyRequest{
    Name: "Tom",
    Id: "123",
    Address: "xxx",
}
resp, err := p_s_m.RawCall.Hello(ctx, req, opts...)
```

#### 3. Direct Kitex Client Access
For direct framework access:

```go
kitexClient := opClient.KitexClient()
resp, err := kitexClient.Hello(context.Background(), req, opts)
```

## Client Creation

### Global Auto-created Client

Overpass automatically creates a default client on startup:

```go
// Direct usage
resp, err := p_s_m.Hello(ctx, "Tom", "123")

// Equivalent to
opClient := p_s_m.DefaultClient()
resp, err := opClient.Hello(ctx, "Tom", "123")
```

Disable auto-creation with environment variable:
```bash
export OVERPASS_DO_NOT_NEW_CLIENT_WHEN_INIT=1
```

### Manual Client Creation

For more complex scenarios:

```go
// Method 1: PSM + Kitex options
opClient, err := p_s_m.NewClient("p.s.m",
    client.WithHostPorts(hostport),
    client.WithCluster("cluster"))

// Method 2: PSM + BytedConfig + Kitex options
opClient, err := p_s_m.NewClientWithBytedConfig("p.s.m",
    bytedConfig,
    client.WithHostPorts(hostport))
```

## IDL Information Sources

### Main IDL Path Priority
1. CN region (if PSM exists in both CN and I18n)
2. I18n region (if PSM not in CN)
3. Configuration at: https://bytedance.larkoffice.com/wiki/B1zmwRKqxiNfXzkGgIRcOL8Bndc

### PSM Discovery
- Source: TCE API (lists all deployed PSMs)
- Limitation: Services not on TCE (e.g., ByteOS physical machines) must be manually white-listed

### Update Timing
- New service detected from TCE: 5 seconds
- IDL path update on MS: 3 minutes
- IDL file modification: 4 minutes
- Repository update after IDL change: 30 seconds

**Force Update**: Use web interface buttons for immediate synchronization

## Key Design Principles

### 1. PSM as Dimensionality
- One repository per PSM (not per IDL file)
- Ensures proper dependency management
- Simplifies code discovery

### 2. Kitex Framework Basis
- Built on top of Kitex API
- Inherits all Kitex capabilities
- Adds scaffolding and automation

### 3. Compilation Guarantee
- All generated code passes compilation
- Failed builds are not merged
- Users always get working dependencies

### 4. Automatic Updates
- IDL changes trigger auto-updates
- Exponential backoff on failures
- Manual force-update available

## Common Patterns

### Adding Dependency

```bash
# From web interface "Quick Commands"
go get code.byted.org/overpass/toutiao_location_location
```

### Simple RPC Call

```go
import (
    "context"
    "code.byted.org/overpass/toutiao_location_location/rpc/toutiao_location_location"
)

func main() {
    ctx := context.Background()
    resp, err := toutiao_location_location.MultiGetIPInfo(ctx, []string{"8.8.8.8"})
    // Handle response
}
```

### Updating Dependencies

```bash
# Update all Overpass dependencies
go get code.byted.org/overpass/...

# Update specific repository
go get code.byted.org/overpass/specific_psm
```

## Environment Support

### Supported Environments
- Production (default)
- PPE (pre-production)
- BOE (business operation environment)
- Devbox (development)

### Traffic Routing
Use context to specify environment:

```go
ctx = kitutil.NewCtxWithEnv(ctx, "ppe_xxx")
resp, err := p_s_m.RawCall().Method(ctx, req)
```

## Best Practices

1. **Use Default Client for Simple Cases**: When calling a single PSM with minimal configuration
2. **Create Manual Clients for Complex Cases**: When needing specific options or multiple downstream PSMs
3. **Avoid WithPSM Pattern**: Deprecated; use multiple manual clients instead
4. **Keep Dependencies Updated**: Use `go get code.byted.org/overpass/...` regularly
5. **Check Compilation Status**: Overpass guarantees compilation; conflicts indicate local dependency issues

## Related Documentation

- Kitex Framework: Internal Kitex documentation
- MS Platform: Service management configuration
- TCE: Service deployment platform
