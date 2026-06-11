# Sequence Returns

## Purpose
- Return different values across multiple calls using `Sequence` chaining.

## Code

```go
// Foo echoes input; will be overridden by sequence returns.
func Foo(in string) string { return in }

func main() {
    Mock(Foo).Return(Sequence("Alice").Then("Bob").Times(2).Then("Tom")).Build()
    fmt.Println(Foo("anything")) // Alice
    fmt.Println(Foo("anything")) // Bob
    fmt.Println(Foo("anything")) // Bob
    fmt.Println(Foo("anything")) // Tom
}
```

## Key Points
- Use `Times(n)` to repeat a value, and `Then(next)` to move to the next value.
- After the sequence is exhausted, behavior falls back to the original function.
