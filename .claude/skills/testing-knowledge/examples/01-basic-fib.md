# Basic Unit Test and TestMain

## Purpose
- Demonstrate a minimal unit test for a pure function.
- Show how to use `TestMain` for package-level setup/teardown.

## Code

```go
// Fib computes the n-th Fibonacci number.
func Fib(n int) int {
    if n < 2 {
        return n
    }
    return Fib(n-1) + Fib(n-2)
}

// TestFib verifies Fib returns the expected value for a given input.
func TestFib(t *testing.T) {
    in := 7
    expected := 13
    actual := Fib(in)
    if actual != expected {
        t.Errorf("Fib(%d) = %d; expected %d", in, actual, expected)
    }
}

// TestMain sets up and tears down shared test fixtures for the package.
func TestMain(m *testing.M) {
    fmt.Println("Do stuff BEFORE the tests!")
    exitVal := m.Run()
    fmt.Println("Do stuff AFTER the tests!")
    os.Exit(exitVal)
}
```

## Key Points
- Keep tests deterministic; avoid randomness and external dependencies.
- Use `TestMain` only once per package to centralize setup/teardown.
