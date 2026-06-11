# Goroutine Filters for Mock Scope

## Purpose
- Control where a mock is effective: only current goroutine, or all except current.

## Code

```go
// Foo returns the input string; used to demonstrate goroutine-scoped mocks.
func Foo(in string) string { return in }

func main() {
    // Exclude the current goroutine from mock effect
    Mock(Foo).ExcludeCurrentGoRoutine().Return("MOCKED!").Build()
    fmt.Println(Foo("anything")) // anything | mock does not apply here

    go func() {
        fmt.Println(Foo("anything")) // MOCKED! | mock applies in other goroutine
    }()

    time.Sleep(time.Second) // wait for goroutine
}
```

## Key Points
- Prefer `IncludeCurrentGoRoutine` or `ExcludeCurrentGoRoutine`; avoid `FilterGoRoutine` unless you must target exact goroutine IDs.
- Use `GetGoroutineId` if you need to log/debug goroutine identities.
