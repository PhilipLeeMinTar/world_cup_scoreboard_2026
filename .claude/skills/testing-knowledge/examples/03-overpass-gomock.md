# Overpass RPC Mock with GoMock

## Purpose
- Demonstrate mocking Overpass client and RawCall via gomock-generated code.
- Cover both client method and raw call paths.

## Code

```go
// MockHelloRaw returns a canned response for RawCall.Hello.
func MockHelloRaw(ctx context.Context, req *ma.MyReq, callOptions ...callopt.Option) (*m.MyResp, error) {
    return &m.MyResp{Text: "hello:" + req.Name}, nil
}

// MockHello returns a canned response for client.Hello.
func MockHello(ctx context.Context, name, id string, callOptions ...callopt.Option) (*m.MyResp, error) {
    return &m.MyResp{Text: "hello:" + name}, nil
}

// TestClient shows how to bind gomock-generated Overpass client and raw call.
func TestClient(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    // Bind gomock raw call struct
    rawc := p_s_m.NewMockRawCallStruct(ctrl)
    rawc.EXPECT().Hello(gomock.Any(), gomock.Any(), gomock.Any()).DoAndReturn(MockHelloRaw).AnyTimes()

    // Bind gomock client
    client := p_s_m.NewMockOverpassClient(ctrl)
    client.EXPECT().RawCall().Return(rawc).AnyTimes()
    client.EXPECT().Hello(gomock.Any(), gomock.Any(), gomock.Any(), gomock.Any()).DoAndReturn(MockHello).AnyTimes()

    // Mocked call
    resp, err := client.Hello(context.Background(), "Tom", "123")
    if err == nil { fmt.Println(resp.Text) } else { fmt.Println(err) }

    // Mocked raw call
    resp, err = client.RawCall().Hello(context.Background(), &m.MyReq{Name: "Jerry"})
    if err == nil { fmt.Println(resp.Text) } else { fmt.Println(err) }
}
```

## Key Points
- Use gomock-generated types (`NewMockOverpassClient`, `NewMockRawCallStruct`) from `overpass_gomock.go`.
- Keep expectations broad for tests with `gomock.Any()` and return via `DoAndReturn`.
