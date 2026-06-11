# Overpass Client Configuration

## Client Creation Methods

### Global Auto-created Client (Recommended for Simple Cases)

The simplest approach - Overpass automatically creates a default client:

```go
package main

import (
    "context"
    "code.byted.org/overpass/p_s_m/rpc/p_s_m"
)

func main() {
    // Direct usage - auto-created client
    resp, err := p_s_m.Hello(ctx, "Tom", "123")

    // Explicit access to default client
    opClient := p_s_m.DefaultClient()
    resp, err = opClient.Hello(ctx, "Jerry", "321")
}
```

**When to use**:
- Single downstream PSM
- No special configuration needed
- Simple RPC call scenarios

**Disable auto-creation**:
```bash
export OVERPASS_DO_NOT_NEW_CLIENT_WHEN_INIT=1
```

### Manual Client Creation (Recommended for Complex Cases)

Create explicit clients with custom configuration:

```go
// Method 1: Basic creation with PSM and options
opClient, err := p_s_m.NewClient("p.s.m",
    client.WithHostPorts("127.0.0.1:8888"),
    client.WithMiddleware(MyKitexMW()),
    client.WithIDC("idc"),
    client.WithCluster("cluster"))

// Method 2: With BytedConfig
opClient, err := p_s_m.NewClientWithBytedConfig("p.s.m",
    bytedConfig,
    client.WithHostPorts(hostport))
```

**When to use**:
- Multiple downstream PSMs
- Need specific Kitex options
- Complex configuration requirements
- Avoiding dependency override issues

## Kitex Options

### Client Options (Initialization Time)

Applied when creating the client:

```go
import "github.com/cloudwego/kitex/client"

opClient, err := p_s_m.NewClient("p.s.m",
    // Network
    client.WithHostPorts("hostport"),

    // Transport
    client.WithTransportProtocol(transport.Framed),
    client.WithPayloadCodec(thrift.NewThriftCodecWithConfig(
        thrift.FrugalRead|thrift.FrugalWrite)),

    // Service discovery
    client.WithIDC("idc"),
    client.WithCluster("cluster"),

    // Middleware
    client.WithMiddleware(MyKitexMW()),

    // Additional options...
)
```

### Call Options (Per-Request)

Applied at RPC call time:

```go
import "github.com/cloudwego/kitex/client/callopt"

// Default method style
resp, err := opClient.Hello(ctx, req.param1, req.param2,
    callopt.WithIDC("idc"),
    callopt.WithCluster("cluster"),
    callopt.WithRPCTimeout(100*time.Millisecond))

// Raw call style
resp, err := p_s_m.RawCall.GetMessages(ctx, req,
    callopt.WithIDC("idc"),
    callopt.WithCluster("cluster"))
```

### Common Options

#### Specify Transport Protocol (for Data/C++ services)

Data C++ services typically use Framed protocol instead of default Buffered:

```go
func init() {
    p_s_m.InitDefaultClientOptions(
        clientoption.WithTransportProtocol(transport.Framed))
}
```

#### Cluster Selection

```go
// At client creation
opClient, err := p_s_m.NewClient("p.s.m",
    client.WithCluster("my-cluster"))

// At call time
resp, err := opClient.Hello(ctx, param1, param2,
    callopt.WithCluster("my-cluster"))
```

#### Timeout Configuration

```go
// Connection timeout
client.WithConnectTimeout(100 * time.Millisecond)

// RPC timeout (call option)
callopt.WithRPCTimeout(200 * time.Millisecond)
```

## Overpass-Specific Configuration

### Configuration Structure

```go
type Conf struct {
    EnableErrHandler  bool
    ErrHandler        handler.Handler
    EnableReqRespLog  bool
    ReqRespLogHandler handler.Handler
}
```

### Accessing Configuration

```go
// For explicit client
opClient.Conf().EnableReqRespLog = true
opClient.Conf().EnableErrHandler = false

// For global default client
p_s_m.DefaultClient().Conf().EnableReqRespLog = true
p_s_m.DefaultClient().Conf().ErrHandler.NoLog = true
```

### Sharing Configuration Across Clients

```go
// Create shared configuration
conf := kos.NewConf()
conf.EnableReqRespLog = true
conf.EnableErrHandler = false

// Apply to multiple clients
opClient1.SetConf(conf)
opClient2.SetConf(conf)
opClient3.SetConf(conf)
```

## Error Handling Configuration

### Default Behavior

Overpass wraps all errors in `RPCError` structure:

```go
type RPCError struct {
    PSM              string
    Method           string
    ErrType          RPCErrorType
    OriginalErr      error
    BizStatusCode    int32
    BizStatusMessage string
}
```

### Error Types

1. **RPC_FAILED**: Kitex error, network error, or business handler error
2. **RPC_RESP_IS_NIL**: Response is nil
3. **RPC_STATUS_CODE_NOT_ZERO**: Business status code != 0

### Error Handling Example

```go
resp, err := client.Method(ctx, req)
if err != nil {
    rpcErr := err.(*rpc_error.RPCError)

    if rpcErr.Is(rpc_error.RPC_STATUS_CODE_NOT_ZERO) {
        code := rpcErr.GetBizStatusCode()
        msg := rpcErr.GetBizStatusMessage()
        // Handle business error
    } else {
        origErr := rpcErr.GetOriginalErr()
        // Handle RPC/network error
    }
}
```

### Disabling Error Handler

```go
// Globally for client
opClient.Conf().EnableErrHandler = false

// For specific call
resp, err := p_s_m.Hello(ctx, param1, param2,
    calloption.WithoutOverpassErrHandler())

// Via environment variable
// export OVERPASS_FORBIDDEN_ERROR_HANDLER=1
```

## Logging Configuration

### Default Behavior

Overpass automatically logs request/response in certain environments:
- **BOE**: Enabled by default
- **PPE/Production**: Disabled by default (for compliance)
- **Load Testing**: Disabled automatically

### Enabling/Disabling Logs

```go
// Enable for specific client
opClient.Conf().EnableReqRespLog = true

// Enable for specific call
resp, err := p_s_m.RawCall.Method(ctx, req,
    calloption.WithReqRespLogsInfo())

// Via environment variable
// export OVERPASS_OPTION_PRINT_REQ_RESP_LOG=1  # Enable
// export OVERPASS_OPTION_PRINT_REQ_RESP_LOG=0  # Disable
```

### Decision Flow

```
Request → Is Load Test? → Yes → No Log
           ↓ No
       Code Specified? → Yes → Use Code Setting
           ↓ No
       Env Variable Set? → Yes → Use Env Setting
           ↓ No
       Is BOE? → Yes → Log
           ↓ No
       No Log
```

### Custom Logging

For advanced logging control (whitelist/blacklist methods, custom log function):

```go
import "code.byted.org/kite/kitex-overpass-suite/handler"

// Replace default logger with custom logger
p_s_m.DefaultClient().Conf().ReqRespLogHandler =
    handler.NewCustomLogger(myPrintFunc, methodList, isWhitelistMode)

// myPrintFunc signature:
// func(ctx context.Context, psm, method, rip string,
//      request, response interface{}) error
```

## Advanced Configuration

### Custom Handlers

Implement custom pre/post RPC hooks:

```go
type MyHandler struct {}

func (h *MyHandler) PreFunc(method, psm string, ctx context.Context,
                            args ...interface{}) (context.Context, []callopt.Option) {
    // Pre-RPC logic
    // Can add additional call options dynamically
    return ctx, nil
}

func (h *MyHandler) PostFunc(method, psm string, ctx context.Context,
                             response interface{}, err error,
                             args ...interface{}) error {
    // Post-RPC logic
    return err
}

// Apply custom handler
opClient.Conf.ErrHandler = &MyHandler{}

// Chain multiple handlers
handlers := []handler.Handler{&MyHandler1{}, &MyHandler2{}}
opClient.Conf.OverpassHandlerChain = handlers
```

### Environment-Specific Routing

```go
import "code.byted.org/gopkg/kitutil"

// Route to specific PPE lane
ctx = kitutil.NewCtxWithEnv(ctx, "ppe_xxx")
resp, err := p_s_m.RawCall().Method(ctx, req)
```

### IPv6 Configuration

```go
// Enable degraded IPv6 (environment variable)
// export OVERPASS_USE_DEGRADED_IPV6=1

// This automatically configures:
// bytedConfig.IPPolicy = IPV6Priority
```

## Migration from Old Template

### Option Type Changes

Old template used Overpass-specific options. New template uses Kitex options directly:

```go
// OLD (deprecated)
import "code.byted.org/overpass/common/option/clientoption"
clientoption.WithHostPorts(xxx)

// NEW (recommended)
import "github.com/cloudwego/kitex/client"
client.WithHostPorts(xxx)
```

### Interface{} Type for Options

New template uses `interface{}` for compatibility:

```go
// If you previously used:
opts := []calloption.Option{xxx}
psm.Hello(req, opts...)

// Change to either:
opts := []interface{}{xxx}  // Option 1
psm.Hello(req, opts...)

// Or remove the spread:
psm.Hello(req, opts)  // Option 2 (recommended)
```

### Deprecated InitDefaultClientOptions

Old approach (not recommended):
```go
p_s_m.InitDefaultClientOptions(clientoption.WithCluster("xxx"))
```

This causes global pollution. Use manual client creation instead:
```go
opClient, err := p_s_m.NewClient("p.s.m", client.WithCluster("xxx"))
```

## Troubleshooting

### Option Type Invalid Error

```
panic: [Overpass Init] Client Option Type invalid at the position of 1
```

**Solution**: Check that you're passing correct option types:
- Client Options at initialization
- Call Options during RPC call
- Not mixing option types
- Not passing request parameters as options

### JSON Serialization Panic

If logging causes panic in `json.Marshal`:

**Cause**: Concurrent modification of request/response during serialization

**Solutions**:
1. Disable logging (immediate fix)
2. Fix concurrent access with `-race` detection (proper fix)

## Best Practices

1. **Choose the Right Creation Method**:
   - Simple cases: Use global auto-created client
   - Complex cases: Manual creation with explicit options

2. **Avoid Deprecated Patterns**:
   - Don't use `WithPSM` call option
   - Don't use `InitDefaultClientOptions`
   - Use Kitex options directly, not Overpass wrappers

3. **Configuration Management**:
   - Share `Conf` objects for consistent behavior
   - Document your client creation choices
   - Keep option usage close to client creation

4. **Error Handling**:
   - Always check for nil errors
   - Use type assertion for `RPCError` when needed
   - Don't silence errors unless intentional

5. **Logging**:
   - Be careful with high-volume production logging
   - Use custom loggers for fine-grained control
   - Disable in load tests automatically (built-in)
