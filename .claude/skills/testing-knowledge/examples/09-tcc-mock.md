# TCC Mock (Unified SDK)

## Purpose
- Demonstrate mocking TCC configuration queries using the unified SDK in tests.

## Code

```go
// Test with table-driven style and TCC mock helpers
func TestTccUsage(t *testing.T) {
    type Fields struct{ TccClient tccclient.Client }
    type Args struct{ Ctx context.Context }
    type test struct {
        Name   string
        Fields Fields
        Args   Args
        Want   string
    }
    tests := []test{
        {
            Name:   "FirstCase",
            Fields: Fields{TccClient: tccmock.GetMockTccClient("toutiao.inf.unit_test", tccclient.NewConfigV2())},
            Args:   Args{context.Background()},
            Want:   "",
        },
    }
    for _, tt := range tests {
        mockey.PatchConvey(tt.Name, t, func() {
            // Tcc Get Method Mock
            tccmock.MockGet(tt.Fields.TccClient, "[\"name1\",\"name2\",\"name3\"]", nil)
            // Tcc GetWithParser Method Mock
            tccmock.MockGetWithParser(tt.Fields.TccClient, Msg{"master"}, nil)
            // ... execute and assert ...
        })
    }
}
```

## Key Points
- Use the unified `tccmock` helpers to control responses without hitting real storage.
- Keep the client obtained via `GetMockTccClient` only in tests.
