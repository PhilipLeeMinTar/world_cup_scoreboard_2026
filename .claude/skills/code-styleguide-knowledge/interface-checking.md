# 接口检查规范

接口检查是TikTok Go代码规范中的重要实践，通过在编译时验证接口实现，可以提前暴露潜在错误，提高代码质量。

## 接口检查的目的

接口检查的主要目的是在编译过程中验证结构体是否正确地实现了指定的接口，从而：

- **提前发现错误**：在编译阶段就能发现接口实现不完整的问题
- **提高代码可维护性**：明确展示结构体与接口的关系
- **增强代码自描述性**：使代码结构更加清晰易懂

## 接口检查的实现方法

在TikTok代码规范中，推荐使用空白标识符来测试接口的实现。具体实现方式如下：

```go
var (
    _ Iface = (*impl1)(nil)
    _ Iface = (*impl2)(nil)
)

type Iface interface {
    Method1(xxx) xxx
    Method2(xxx) xxx
    // ... 其他方法
}

type impl1 struct {
    // ... 字段定义
}

type impl2 struct {
    // ... 字段定义
}
```

### 实现要点

1. **使用空白标识符**：通过 `_` 变量声明来检查接口实现
2. **类型转换**：使用 `(*impl1)(nil)` 将nil指针转换为具体类型
3. **编译时验证**：如果结构体没有完全实现接口的所有方法，编译时会报错

## 最佳实践

### 1. 明确接口定义
接口应该清晰定义所需的方法，避免过于宽泛或过于具体：

```go
type Runner interface {
    Setup(p Program)
    Run() error
    Close()
}
```

### 2. 结构体实现接口
结构体应该完整实现接口的所有方法：

```go
type programRunner struct {
    internalProgram InternalProgram
}

func (p *programRunner) Setup(p Program) Runner {
    return &programRunner{
        internalProgram: p,
    }
}

func (p *programRunner) Run() error {
    // 具体的运行逻辑
    return nil
}

func (p *programRunner) Close() error { 
    return p.internalProgram.Close()
}
```

### 3. 接口检查位置
接口检查应该放在相关代码附近，通常建议：

- 在接口定义文件或包级别进行集中检查
- 确保检查代码在编译时被执行
- 避免将检查代码放在可能被跳过的代码路径中

## 注意事项

1. **编译时特性**：接口检查是编译时行为，不会影响运行时性能
2. **错误信息**：当接口实现不完整时，编译器会提供清晰的错误信息
3. **代码组织**：建议将相关的接口检查和实现放在一起，便于维护

## 使用场景

接口检查特别适用于以下场景：

- **大型项目**：需要确保多个实现都符合接口约定
- **公共库开发**：对外提供稳定的API接口
- **重构代码**：验证重构后的代码是否仍然满足接口要求
- **团队协作**：确保不同开发者实现的代码符合统一接口规范

通过遵循这些接口检查规范，可以显著提高TikTok Go代码的质量和可维护性，减少因接口实现不完整导致的运行时错误。
