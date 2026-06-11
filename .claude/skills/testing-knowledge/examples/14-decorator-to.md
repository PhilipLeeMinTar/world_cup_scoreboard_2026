# Decorator Pattern with Origin + To

## Purpose
- Preserve the original function logic while adding AOP-like behavior in mocks.

## Code

```go
// Foo returns a prefixed string.
func Foo(in string) string { return "ori:" + in }

func main() {
    // Capture original logic in `origin`
    origin := Foo
    // Build decorator around origin
    decorator := func(in string) string {
        fmt.Println("arg is", in)
        out := origin(in)
        fmt.Println("res is", out)
        return out
    }
    // Mock with origin preserved and decorator applied
    Mock(Foo).Origin(&origin).To(decorator).Build()
    fmt.Println(Foo("anything"))
    // Output:
    // arg is anything
    // res is ori:anything
    // ori:anything
}
```

## Key Points
- `Origin(&origin)` captures the pre-mock behavior; `To(decorator)` wraps it.
- Keep decorator signature identical (including receiver if mocking methods).
