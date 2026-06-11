# Overpass Non-Intrusive Mock API

## Purpose
- Demonstrate Overpass's non-intrusive RPC mock API to replace real Kitex calls during tests.
- Comply with project rules: avoid explicit `init()` in `_test.go`; use `Init()` + `sync.Once` and wire from `TestMain`.

## Code

```go
// Init sets Overpass client mocks. Prefer calling this from TestMain via sync.Once.
var initOnce sync.Once
func Init() { // do NOT use explicit init() in *_test.go
    initOnce.Do(func() {
        // Mock the global default Overpass client
        hotsoon_func_data.SetMock.GetUserFunc(func(ctx context.Context, req *data.GetKaelUsedPsmsReq) (*data.GetKaelUsedPsmsResp, error) {
            return &data.GetUserResp{Name: "Tom"}, nil
        })
        // Mock a specific Overpass client
        opClient.MockClient().GetUserFunc = func(ctx context.Context, req *data.GetKaelUsedPsmsReq) (*data.GetKaelUsedPsmsResp, error) {
            return &data.GetUserResp{Name: "Tom"}, nil
        }
    })
}

// TestMain wires the explicit Init() once for the package tests.
func TestMain(m *testing.M) {
    Init()
    os.Exit(m.Run())
}
```

## Key Points
- Keep mocks in test files or test-only helpers; never ship these into production builds.
- Use `sync.Once` to prevent double initialization across multiple tests.
