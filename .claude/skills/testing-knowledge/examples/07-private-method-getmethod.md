# GetMethod / GetPrivateMethod for Special Cases

## Purpose
- Mock methods via instances, unexported types/methods, or nested struct methods when direct mocking is not effective.

## Code

```go
// Example: instance method via GetMethod
type A struct{}
func (a A) Foo(in string) string { return in }

func main() {
    a := new(A)
    Mock(GetMethod(a, "Foo")).Return("MOCKED!").Build()
    fmt.Println(a.Foo("anything")) // MOCKED!
}
```

```go
// Example: unexported type method (sha256.digest.Sum)
Mock(GetMethod(sha256.New(), "Sum")).Return([]byte{0}).Build()
fmt.Println(sha256.New().Sum([]byte("anything"))) // [0]
```

```go
// Example: unexported method (bytes.Buffer.empty) with OptUnexportedTargetType
var targetType func() bool // signature without receiver
target := GetMethod(new(bytes.Buffer), "empty", OptUnexportedTargetType(targetType))
Mock(target).Return(true).Build()
buf := bytes.NewBuffer([]byte{1, 2, 3, 4})
b, err := buf.ReadByte()
fmt.Println(b, err) // 0 EOF
```

```go
// Example: nested struct methods (Wrapper.inner.Foo)
type Wrapper struct { inner }
type inner struct{}
func (i inner) Foo(in string) string { return in }
Mock(GetMethod(Wrapper{}, "Foo")).Return("MOCKED!").Build()
fmt.Println(Wrapper{}.Foo("anything")) // MOCKED!
```

## Key Points
- Ensure the instance passed to `GetMethod` is non-nil.
- For erased type info on unexported methods, specify `OptUnexportedTargetType`.
