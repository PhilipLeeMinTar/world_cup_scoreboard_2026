---
name: testing-knowledge
description: Testing knowledge base for Golang unit tests, mockey usage (PatchConvey/MockGeneric/When/Sequence/Origin), Overpass/KiteX RPC mocks, storage (TCC), goroutines, private methods. Invoke when writing tests.
user-invocable: false
---

# Testing Knowledge Base

A concise guide for Golang testing with Bytedance mockey, RPC mocking (Overpass/Kite/KiteX), storage/TCC mocking, goroutine filtering, private/unexported methods, and more.

## Rules
- Only use mockey within files that end with `_test.go`.
- Do not declare explicit `init()` in `_test.go`. Prefer an explicit `Init()` and `sync.Once` for only once initialization , and wire it from `TestMain`.

## Usage Guide 
This section merges the essential “Usage Guide” previously in `mockey-usage.md`, aligned to mockey’s official documentation. For full, runnable code, use the example set below.

- Simple functions/methods: Mock(Foo), Mock(A.Foo), Mock((*B).Foo)
- Generics: MockGeneric(FooGeneric[T]) and methods; gcshape isolation from v1.3.1
- Variadics: functions and methods with `...`
- Hooks: `To` custom function; method receivers supported
- Lifecycle: `PatchConvey` (auto unpatch per test) and `PatchRun`
- Special cases: `GetMethod` for instances, unexported types/methods, nested structs
- Advanced: interface-wide mock (experimental `exp/iface`)
- Conditional: `When(...)` chains by argument predicates
- Sequence returns: `Return(Sequence(...).Then(...).Times(n)...)`
- Decorator: `Origin(&origin)` + `To(decorator)` for AOP around original
- Goroutines: `IncludeCurrentGoRoutine`, `ExcludeCurrentGoRoutine` (avoid FilterGoRoutine unless necessary)
- Mocker metrics: `MockTimes()`, `Times()`, `Return(...)`, `Release()`

## Examples Index (relative links)
- [01-basic-fib.md](./examples/01-basic-fib.md)
- [02-mockey-table-driven.md](./examples/02-mockey-table-driven.md)
- [03-overpass-gomock.md](./examples/03-overpass-gomock.md)
- [04-overpass-mock-api.md](./examples/04-overpass-mock-api.md)
- [05-goroutine-filters.md](./examples/05-goroutine-filters.md)
- [06-anonymous-fn-limits.md](./examples/06-anonymous-fn-limits.md)
- [07-private-method-getmethod.md](./examples/07-private-method-getmethod.md)
- [08-kitex-mock.md](./examples/08-kitex-mock.md)
- [09-tcc-mock.md](./examples/09-tcc-mock.md)
- [10-simple-funcs-methods.md](./examples/10-simple-funcs-methods.md)
- [11-generics-mock.md](./examples/11-generics-mock.md)
- [12-when-conditional-mock.md](./examples/12-when-conditional-mock.md)
- [13-sequence-returns.md](./examples/13-sequence-returns.md)
- [14-decorator-to.md](./examples/14-decorator-to.md)
- [15-mocker-metrics-remock.md](./examples/15-mocker-metrics-remock.md)
- [16-variables-mock.md](./examples/16-variables-mock.md)

## References
- Mockey official usage: https://github.com/bytedance/mockey
- [Mockey Usage Guide (internal doc)](https://bytedance.larkoffice.com/wiki/wikcn2apwF3H9HhQHQjWa5yLRtf)
