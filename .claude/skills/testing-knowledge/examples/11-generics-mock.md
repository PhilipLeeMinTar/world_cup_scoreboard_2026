# Generic Functions and Methods

## Purpose
- Mock generic functions/methods using `MockGeneric` (or `Mock` with generics recognition in go1.20+).
- Understand gcshape isolation since v1.3.1.

## Code

```go
// FooGeneric echoes the generic input.
func FooGeneric[T any](t T) T { return t }

type GenericClass[T any] struct{}
func (g *GenericClass[T]) Foo(t T) T { return t }

func main() {
    // mock generic function (string)
    MockGeneric(FooGeneric[string]).Return("MOCKED!").Build()
    fmt.Println(FooGeneric("anything")) // MOCKED!
    fmt.Println(FooGeneric(1))          // 1 | not mocked (type mismatch)

    // mock generic method (string)
    MockGeneric((*GenericClass[string]).Foo).Return("MOCKED!").Build()
    fmt.Println(new(GenericClass[string]).Foo("anything")) // MOCKED!
}
```

```go
// gcshape isolation since v1.3.1
type MyString string
MockGeneric(FooGeneric[string]).Return("MOCKED!").Build()
fmt.Println(FooGeneric("anything"))            // MOCKED!
fmt.Println(FooGeneric[MyString]("anything"))  // anything | no interference
m1 := MockGeneric(FooGeneric[MyString]).Return("MOCKED2!").Build()
fmt.Println(FooGeneric("anything"))            // MOCKED!
fmt.Println(FooGeneric[MyString]("anything"))  // MOCKED2!
m1.UnPatch()
```

## Key Points
- Prefer `MockGeneric` for generic functions/methods; `Mock` with generics recognition is experimental.
- Unpatch in LIFO order when manually releasing multiple mockers.
