# Table-Driven Tests with Mockey (PatchConvey)

## Purpose
- Show a table-driven test that uses mockey to break downstream dependencies.
- Use `PatchConvey` for automatic unpatch per test case.

## Code

```go
// Reduce deduplicates adjacent duplicates in a slice.
func Reduce(in []string) []string {
    // ... business logic ...
    return in // placeholder
}

// ContainsUniqueMX checks uniqueness via downstream call; mocked in tests.
func ContainsUniqueMX(s string) bool {
    // downstream dependency
    return false
}

// TestReduce validates Reduce behavior via table-driven tests with Mockey.
func TestReduce(t *testing.T) {
    type Args struct { Slc []string }
    type test struct {
        Name  string
        Args  Args
        Want  []string
        Mocks func()
    }
    tests := []test{
        {
            Name:  "ContainsUniqueMX",
            Args:  Args{Slc: []string{"NIYJD"}},
            Want:  []string{},
            Mocks: func() { mockey.Mock(ContainsUniqueMX).Return(true).Build() },
        },
        {
            Name:  "NotContainsUniqueMX",
            Args:  Args{Slc: []string{"TXC","TXC","TXC"}},
            Want:  []string{"TXC"},
            Mocks: func() { mockey.Mock(ContainsUniqueMX).Return(false).Build() },
        },
    }
    for _, tt := range tests {
        mockey.PatchConvey(tt.Name, t, func() {
            tt.Mocks()                                 // activate mocks
            got := Reduce(tt.Args.Slc)                 // execute
            convey.So(got, convey.ShouldResemble, tt.Want) // assert
        })
    }
}
```

## Key Points
- `PatchConvey` automatically releases mocks after each case.
- Keep per-case mock setup within the case closure.
