# Kite/KiteX RPC Mock

## Purpose
- Use `kitex`/`kite` tool with `-mock` to generate client interfaces suitable for mocking in unit tests.

## Steps
- Generate client code with mock support:

```bash
# Example: adjust to your service definitions
kitex -module your.module/path -mock -service abc_service idl/abc_service.thrift
```

## Code

```go
// Update the RPC client
var Client c.ABCServiceClient
Client = c.MustNewClient("a.b.c", kitc.WithMiddleWares(RespCheckMW()))

// In unit tests: replace the client via the generated mock interface
// (Construct and inject a mock implementation as needed)
```

## Key Points
- Passing `-mock` to the generator adds interfaces usable by gomock or custom stubs.
- Keep client replacement scoped to tests; avoid shipping mock bindings in production.
