# Mocking Variables and Function Variables

## Purpose
- Replace values of ordinary variables and function variables during tests.

## Code

```go
// Ordinary variable
var GlobalAnswer = 42

// Function variable
var Compute = func(x int) int { return x + 1 }

func main() {
    // Mock ordinary variable (assign desired value)
    GlobalAnswer = 0
    fmt.Println(GlobalAnswer) // 0

    // Mock function variable via replacement
    Mock(&Compute).To(func(x int) int { return 100 }).Build()
    fmt.Println(Compute(10))  // 100
}
```

## Key Points
- Function variables can be patched via `To`; ordinary variables rely on assignment or test wiring.
- Prefer keeping such variables in test-only scopes or injected via constructors for clarity.
