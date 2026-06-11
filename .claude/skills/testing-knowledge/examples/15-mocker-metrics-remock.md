# Mocker Metrics and Re-Mock

## Purpose
- Use `Mocker` to inspect counts and reconfigure mocks; release to restore originals.

## Code

```go
// Foo echoes input; will be conditionally mocked.
func Foo(in string) string { return in }

func main() {
    mocker := Mock(Foo).When(func(in string) bool { return len(in) > 5 }).Return("MOCKED!").Build()
    fmt.Println(Foo("any"))      // any
    fmt.Println(Foo("anything")) // MOCKED!

    // Inspect counts
    fmt.Println(mocker.MockTimes()) // number of times mock was applied
    fmt.Println(mocker.Times())     // total calls to Foo

    // Re-mock return value
    mocker.Return("MOCKED2!")
    fmt.Println(Foo("anything"))    // MOCKED2!

    // Release the mock
    mocker.Release()
    fmt.Println(Foo("anything"))    // anything
}
```

## Key Points
- Counts reset when re-mocking or releasing.
- Keep reconfiguration local to tests; avoid global side effects.
