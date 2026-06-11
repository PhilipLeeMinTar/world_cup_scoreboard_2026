# 注释规范指南

TikTok代码规范对注释有明确的要求，旨在提高代码的可读性和可维护性。以下是详细的注释规范指南：

## 注释类型选择

- **[SHOULD] 对于大多数情况使用行注释**：Go语言提供C风格的`/* */`块注释和C++风格的`//`行注释。为了保持一致性，建议在大多数情况下使用行注释（包括包注释），除非在表达式内部使用注释

## 语言要求

- **[SHOULD] 使用英文编写注释**：注释应使用英文编写，以确保国际化团队的一致理解

## 包注释

- **[RECOMMENDED] 在包顶部包含简要的注释部分**：建议在包顶部包含一个简要的注释部分来描述包的功能，并可选择性地提供使用示例

## 函数注释

- **[MUST] 导出的函数必须有注释**：导出的函数必须有注释描述其用法，除非函数名称是自解释的。注释应包括但不限于前提条件、预期输入、输出、性能影响以及错误处理方式

- **[RECOMMENDED] 以函数名开头**：建议以函数名开头编写函数注释，例如：
  ```go
  // Compile parses a regular expression and returns, if successful,
  // a Regexp that can be used to match against text.
  func Compile(str string) (*Regexp, error) {
  ```

- **避免冗余注释**：对于自解释的函数，可能不需要注释。例如，`AddOne`函数名已经足够清晰，不需要额外注释

## 函数参数注释

- **[RECOMMENDED] 必要时添加函数参数注释**：即使许多IDE会自动在调用点添加参数信息，仍然建议在必要时为函数参数添加注释。使用块注释`/*argument=*/`格式

- **避免参数注释的方法**：
  - 如果参数是字面常量，并且在多个函数调用中以相同方式使用，应使用命名常量来明确约束
  - 对于具有多个配置选项的函数，考虑定义一个结构体来保存所有选项
  - 用命名变量替换大型或复杂的嵌套表达式

## 实现注释

- **[SHOULD] 为代码的棘手、不明显、有趣或重要部分添加实现注释**：注释应解释代码中不明显的部分，而不是陈述显而易见的内容

- **避免的示例**：
  ```go
  // Calculate the sum of integers from 1 to 5. 
  sum := 0
  for i := 1; i < 5; ++i {
      sum += i
  }
  ```

## 变量注释

- **[SHOULD] 为不具自解释性的变量声明添加注释**：如果变量名称在其上下文中不够自解释，应添加注释说明

- **避免的示例**：
  ```go
  // A list of labels indicate the relation between the user and their friends.
  var relationLabels []string
  for _, friend := friends {
      relationLabels = append(relationLabels, friend.relationLabel)
  }
  ```

## TODO注释

- **[SHOULD] 始终在TODO注释中提及负责人**：悬空的TODO很可能永远不会完成，并且很可能被永久遗忘

- **[RECOMMENDED] 将TODO分配给JIRA工单而非个人**：工单可以转移并易于跟踪，因为人们迟早会忘记事情

- **正确的示例**：
  ```go
  // TODO(SOCIAL-1234): Leap to web3.0
  // TODO(kongzy): Pave the way.
  ```

## 注释编写原则

1. **避免冗余**：不要陈述代码中已经显而易见的内容
2. **解释原因而非内容**：注释应解释代码为什么这样做，而不是它在做什么
3. **保持简洁**：注释应简洁明了，避免冗长的描述
4. **及时更新**：当代码修改时，相关的注释也应相应更新
5. **一致性**：在整个项目中保持注释风格的一致性

## 自动化检查规则

TikTok ByteCheck包含以下与注释相关的规则：
- `byted_s_comment`：检查注释规范
- `byted_s_comment_space`：检查注释空格规范
- `CheckPackageComment`：检查包注释（警告级别，因为难以确定是否自解释）

这些规范应作为代码审查的参考，并应用于合并到TikTok代码仓库的任何代码，以确保代码质量、可读性和团队协作效率。
