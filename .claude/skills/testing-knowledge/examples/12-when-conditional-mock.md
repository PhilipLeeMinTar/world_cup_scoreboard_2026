# Conditional Mock with When

## Purpose
- Return different values under different input conditions using `When` chains.

## Code

```go
// Foo prefixes the input; will be conditionally mocked.
func Foo(in string) string { return "ori:" + in }

func main() {
    // Define multiple conditions; predicates must match the original input signature.
    Mock(Foo).
        When(func(in string) bool { return len(in) == 0 }).Return("EMPTY").
        When(func(in string) bool { return len(in) <= 2 }).Return("SHORT").
        When(func(in string) bool { return len(in) <= 5 }).Return("MEDIUM").
        Build()

    fmt.Println(Foo(""))            // EMPTY
    fmt.Println(Foo("h"))           // SHORT
    fmt.Println(Foo("hello"))       // MEDIUM
    fmt.Println(Foo("hello world")) // ori:hello world
}
```

## Key Points
- Conditions are evaluated in declaration order; the first matching predicate applies.
- If no predicate matches, the original function executes.
