# 控制结构使用指南

TikTok代码规范中对控制结构的使用有明确的要求和最佳实践，主要涵盖if语句、for循环、switch语句等核心控制结构。

## If语句规范

### 避免使用else块
- **推荐做法**：尽可能避免使用`else`块，优先考虑初始化默认值并在`if`块中修改，而不是使用`if`/`else`块
- **示例对比**：
  ```go
  // 不推荐（较难阅读）
  var value string
  if input.value < 0 {
      value = "negative"
  } else {
      value = "positive"
  }
  fmt.Println(value)
  
  // 推荐做法
  value := "positive"
  if input.value < 0 {
      value = "negative"
  }
  fmt.Println(value)
  ```

### 错误处理模式
- **资源清理**：打开文件等操作后应立即检查错误，避免在`else`块中处理正常逻辑
- **示例**：
  ```go
  // 良好实践
  f, err := os.Open(name)
  if err != nil {
      return err
  }
  codeUsing(f)
  ```

## For循环规范

### 变量使用精简
- **原则**：只使用循环中需要的变量，避免声明未使用的变量
- **示例对比**：
  ```go
  // 不推荐
  m := map[string]string{"1": "1"}
  for key, value := range m {
      fmt.Println(value)
  }
  for key, _ := range m {
      fmt.Println(key)
  }
  
  // 推荐做法
  m := map[string]string{"1": "1"}
  for _, value := range m {
      fmt.Println(value)
  }
  for key := range m {
      fmt.Println(key)
  }
  ```

### 三种循环形式
TikTok规范支持Go语言的三种`for`循环形式，开发者应熟悉各自的使用场景：

1. **带初始化、条件和后操作的循环**
   ```go
   sum := 0
   for i := 0; i < 10; i++ {
       sum += i
   }
   ```

2. **仅带条件的循环**（类似while循环）
   ```go
   m := map[string]string{"1": "1"}
   for key, value := range m {
       fmt.Println(key, value)
   }
   ```

3. **无限循环**（需内部使用break/return退出）
   ```go
   count := 0
   for {
       count += 1
       if count == 100 {
           return
       }
   }
   ```

## Switch语句规范

### 优先使用switch替代多重if
- **推荐场景**：当有多个匹配条件时，优先使用`switch`语句而不是多个`if`语句
- **优势**：代码行数更少，通常更易阅读
- **示例对比**：
  ```go
  // 不推荐：多个if语句
  var t interface{}
  t = functionOfSomeType()
  tType := t.(type)
  if tType == bool {
      fmt.Printf("boolean %t\n", t)
  }
  if tType == int {
      fmt.Printf("integer %d\n", t)
  }
  // ...更多if语句
  
  // 推荐：使用switch语句
  var t interface{}
  t = functionOfSomeType()
  switch t := t.(type) {
  case bool:
      fmt.Printf("boolean %t\n", t)
  case int:
      fmt.Printf("integer %d\n", t)
  case *bool:
      fmt.Printf("pointer to boolean %t\n", *t)
  case *int:
      fmt.Printf("pointer to integer %d\n", *t)
  default:
      fmt.Printf("unexpected type %T\n", t)
  }
  ```

### 无限循环中的switch使用
- **典型场景**：在无限`for`循环中（如轮询操作），`switch`语句是处理不同情况的**标准方式**
- **示例**：后台任务定期执行命令
  ```go
  timeout := time.NewTimer(10 * time.Second)
  pollingTicker := time.NewTicker(1 * time.Second)
  for {
      select {
      case <-pollingTicker.C:
          err := func() // 每次轮询执行主函数
          return err
      case <-timeout.C:
          return errors.New(fmt.Sprintf("command did not finish within %s", timeoutDuration.String()))
      default:
      }
  }
  ```

## fallthrough关键字使用规范

### 谨慎使用原则
- **注意事项**：`fallthrough`关键字在switch语句中使用时需要特别谨慎
- **工作机制**：当`fallthrough`出现在case块中时，即使当前case已匹配，也会将控制权转移到下一个case

### 理解fallthrough的行为
- **默认行为**：switch语句从上到下遍历所有case，找到第一个匹配的case表达式后退出，不再考虑其他case
- **fallthrough作用**：绕过上述限制，允许匹配多个分支
- **重要特性**：`fallthrough`不仅取消后续case匹配判断，还会执行后续分支

### 使用示例与风险
```go
i := 5

switch {
case i < 6:
    fmt.Println("i is less than 6")
    fallthrough
case i < 7:
    fmt.Println("i is less than 7")
    fallthrough
case i < 5:
    fmt.Println("i is less than 5")
}
```

**预期输出**：
```
i is less than 6
i is less than 7
```

**实际输出**：
```
i is less than 6
i is less than 7
i is less than 5
```

### 使用要求
1. **分支顺序**：如果必须使用`fallthrough`，必须注意分支判断的顺序
2. **位置限制**：`fallthrough`不能放在最后一个分支，否则会编译异常
3. **明确意图**：使用时应确保代码意图清晰，避免引入难以理解的逻辑流

## 错误处理规范

### 错误必须处理
- **强制要求**：函数返回的错误不能通过空白标识符忽略，必须妥善处理
- **稳定性原则**：正确处理错误是保证程序**稳定**、**可靠**和**可测试**的关键

### 错误处理示例
```go
// 错误做法：忽略错误
val, _ := funcA(xxx)

// 正确做法：妥善处理错误
val, err := funcA(xxx)
if err != nil {
    // 处理错误逻辑
}
```

## 总结要点

1. **if语句**：优先避免`else`块，使用默认值初始化模式
2. **for循环**：精简变量使用，熟悉三种循环形式
3. **switch语句**：替代多重if，特别适合无限循环场景
4. **fallthrough**：谨慎使用，注意分支顺序和编译限制
5. **错误处理**：所有错误必须妥善处理，不得忽略

这些规范确保了TikTok代码在控制结构使用上的一致性和可维护性，帮助开发者编写更清晰、更可靠的代码。
