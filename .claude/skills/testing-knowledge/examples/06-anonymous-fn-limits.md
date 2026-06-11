# Anonymous Function Mock Limits

## Purpose
- Clarify which anonymous function patterns can be mocked by mockey and which cannot.

## Code

```go
// Can be mocked: function fields and package-level function variables.
type A struct {
    f func()
}
var a = A{f: func() { /* body */ }}
var b = func() { /* body */ }
```

```go
// Cannot be mocked: anonymous function defined only within local scope.
func Foo() {
    c := func() { /* body */ }
    c()
}
```

## Key Points
- Expose function variables or struct fields at package scope to allow mocking.
- Locally constructed anonymous functions are out of reach for runtime patching.
