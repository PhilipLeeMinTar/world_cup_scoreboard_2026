# Simple Functions and Methods

## Purpose
- Mock simple functions and methods (value and pointer receivers).

## Code

```go
// Foo returns the input string.
func Foo(in string) string { return in }

type A struct{}
func (a A) Foo(in string) string { return in }   // value receiver

type B struct{}
func (b *B) Foo(in string) string { return in }  // pointer receiver

func main() {
    // mock function
    Mock(Foo).Return("MOCKED!").Build()
    fmt.Println(Foo("anything")) // MOCKED!

    // mock method (value receiver)
    Mock(A.Foo).Return("MOCKED!").Build()
    fmt.Println(A{}.Foo("anything")) // MOCKED!

    // mock method (pointer receiver)
    Mock((*B).Foo).Return("MOCKED!").Build()
    fmt.Println(new(B).Foo("anything")) // MOCKED!
}
```

## Key Points
- Ensure the mock target matches the exact function/method form (type, receiver).
- For methods, use `Type.Method` or `(*Type).Method` depending on receiver kind.
