# 函数设计最佳实践

函数是代码的基本构建块，良好的函数设计对于代码的可读性、可维护性和可测试性至关重要。TikTok Go代码规范对函数设计提出了明确的要求和最佳实践。

## 函数长度

### 编写小而专注的函数
- **原则**：应编写小而专注的函数，即使长函数现在工作完美，几个月后有人修改它时可能会添加新行为
- **优势**：短小简单的函数使其他人更容易阅读和修改代码
- **重构建议**：当遇到长而复杂的函数时，如果难以处理、错误难以调试或需要在多个不同上下文中使用其部分功能，应考虑将其分解为更小、更易管理的部分

### 示例对比
**不推荐的长函数示例**：
```go
func GetCommentList() []*packComment {
    // 1. 从pack获取原始评论
    resp, err := packCommentClient.GetComments()
    if err != nil {
        // 处理错误
    }
    rawComments := resp.GetRawComments()
    
    // 2. 过滤评论
    // 2.1 获取屏蔽信息
    blockInfos, err := relationClient.GetBlockInfo()
    if err != nil {
        // 处理错误
    }
    // 2.2 获取评论创建者信息
    commentCreatorInfos, err := userClient.GetUserInfos()
    if err != nil {
        // 处理错误
    }
    // 2.3 根据屏蔽和用户进行过滤
    filteredComments := make([]Comment, 0)
    for _, cmt := range rawComments {
        // 执行过滤逻辑
    }
    
    // 3. 打包评论
    packInfo, err := packClient.GetPackInfo()
    if err != nil {
        // 处理错误
    }
    packedComments := packInfo.GetPackComments()
    return packedComments
}
```

**推荐的分解函数示例**：
```go
func GetCommentList() []*packComment {
    // 1. 从pack获取原始评论
    rawComments := getRawComments()
    // 2. 过滤评论
    filteredComments := getFilteredComments()
    // 3. 打包评论
    packedComments := getPackedComments()
    return packedComments
}

func getRawComments() []*RawComment {
    // ...
}

func getFilteredComments() []*RawComment {
    // ...
}

func getPackedComments() []*PackComment {
    // ...
}
```

## 函数分组和排序

### 排序原则
- **调用顺序**：函数应按大致调用顺序排序
- **接收者分组**：文件中的函数应按接收者分组

### 文件结构顺序
1. **导出函数**：导出函数应出现在文件的开头，在`struct`、`const`、`var`定义之后
2. **构造函数**：`newXYZ()`/`NewXYZ()`可以出现在类型定义之后，但在接收者的其他方法之前
3. **工具函数**：由于函数按接收者分组，普通工具函数应出现在文件的末尾

### 示例结构
```go
type User struct {
    ID int64
    Name string
    Age int
}

func (u *User) ID() int64 {
    return u.ID
}

func (u *User) Name() string {
    return u.Name
}

func (u *User) Age() int {
    return u.Age
}

func Function1() {}

func Function2() {}

func internalFunction1() {}

func internalFunction2() {}

func utilityFunction1() {}

func utilityFunction2() {}
```

## 上下文参数

### 上下文作为第一个参数
- **原则**：使用`context.Context`作为函数的第一个参数
- **原因**：`context.Context`类型的值携带安全凭据、跟踪信息、截止时间和取消信号，这些信息在API和进程边界之间传递

### 正确用法
```go
func F(ctx context.Context, xxx) {}
```

### 避免的做法
- **不要**将`Context`成员添加到结构体类型中
- **正确做法**：将`ctx`参数添加到需要传递它的该类型的每个方法中
- **唯一例外**：方法的签名必须与标准库或第三方库中的接口匹配时

## 命名返回值参数

### 使用命名返回值
- **优势**：命名返回值可以使代码更清晰，它们作为文档使用
- **初始化**：当命名时，它们在函数开始时被初始化为其类型的零值
- **无参数返回**：如果函数执行没有参数的`return`语句，则使用结果参数的当前值作为返回值

### 清晰示例
```go
func nextInt(b []byte, pos int) (value, nextPos int) {}
```

### 裸返回
- **适用场景**：如果函数相对较短且逻辑简单，可以使用裸返回
- **示例**：
```go
func ReadFull(r Reader, buf []byte) (n int, err error) {
    for len(buf) > 0 && err == nil {
        var nr int
        nr, err = r.Read(buf)
        n += nr
        buf = buf[nr:]
    }
    return
}
```

## 延迟执行（Defer）

### 资源清理
- **原则**：应使用`defer`清理文件、锁等资源
- **优势**：
  1. 保证永远不会忘记关闭文件
  2. 关闭操作靠近打开操作，比放在函数末尾更清晰

### 示例
```go
p.Lock()
defer p.Unlock()

// 执行其他操作
return p
```

## 值传递与指针传递

### 传递指针的场景
- **大型结构体**：对于大型结构体使用指针
- **可能增长的结构体**：对于可能增长的结构体使用指针

### 直接传递值的场景
- **固定大小值**：如果函数仅将参数`x`引用为`*x`，则参数不应是指针
- **常见实例**：
  - 字符串指针（`*string`）
  - 接口值指针（`*io.Reader`）
- **内部指针类型**：切片、映射、通道、字符串、函数值和接口值在内部使用指针实现，指向它们的指针通常是多余的

### 讨论参考
更多讨论可参考：[https://stackoverflow.com/questions/23542989/pointers-vs-values-in-parameters-and-return-values](https://stackoverflow.com/questions/23542989/pointers-vs-values-in-parameters-and-return-values)

## 函数命名规范

### 命名格式
- **导出函数**：使用MixedCaps（首字母大写）
- **非导出函数**：使用mixedCaps（首字母小写）
- **测试函数**：可以包含下划线以分组相关测试用例，例如`TestMyFunction_MyTest`

### 避免重复引用包内容
- **原则**：函数名不应引用包内容，以避免重复
- **不推荐**：
```go
package http
func HttpServer() {}
```
- **推荐**：
```go
package http
func Server() {}
```

### 使用动词或动词短语
- **原则**：函数名应具有动词或动词短语名称
- **示例**：`GetCommentList()`比`CommentList()`更好，但结合包名，`comment.GetList()`更精确

## 函数注释规范

### 导出函数注释
- **要求**：导出函数必须有注释描述其用法，除非函数名是自解释的
- **注释内容**：包括但不限于先决条件、预期输入、输出、性能影响以及如何使用和错误处理
- **推荐格式**：建议以函数名开头

### 函数参数注释
- **推荐**：如果必要，应有函数参数注释
- **格式**：对函数参数注释使用块注释`/*argument=*/`

### 避免参数注释的方法
1. **命名常量**：如果参数是字面常量，并且在多个函数调用中以相同的方式使用，应使用命名常量
2. **配置结构体**：对于具有多个配置选项的函数，考虑定义一个结构体来保存所有选项
3. **命名变量**：用命名变量替换大型或复杂的嵌套表达式

### 示例对比
**不清晰**：
```go
// 这些参数是什么？
var matchedFriends = FindMatchedFriends(1, false)
```

**清晰**：
```go
const (
    kMatchedByDefault = iota
    kMatchedByLink
    kMatchedByContacts
)

var matchedFriends = FindMatchedFriends(kMatchedByLink, /*useCache=*/false)
```

## 错误处理

### 错误包装
- **推荐做法**：为返回的错误添加上下文时，保持上下文简洁，避免使用"failed to"这样的短语
- **错误传播选项**：
  1. 按原样返回原始错误
  2. 使用`fmt.Errorf`和`%w`动词添加上下文
  3. 使用`fmt.Errorf`和`%v`动词添加上下文

### 示例对比
**不推荐**：
```go
s, err := store.New()
if err != nil {
    return fmt.Errorf("failed to create new store: %w", err)
}
// 打印结果："failed to x: failed to y: failed to create new store: the error"
```

**推荐**：
```go
s, err := store.New()
if err != nil {
    return fmt.Errorf("new store: %w", err)
}
// 打印结果："x: y: new store: the error"
```

### 避免panic
- **原则**：生产环境中的代码必须避免panic（除非在启动/初始化任务中，当作业绝对无法恢复时）
- **正确做法**：如果发生错误，函数必须返回错误并允许调用者决定如何处理

### 示例对比
**不推荐**：
```go
func run(args []string) {
    if len(args) == 0 {
        panic("an argument is required")
    }
    // ...
}
```

**推荐**：
```go
func run(args []string) error {
    if len(args) == 0 {
        return errors.New("an argument is required")
    }
    // ...
    return nil
}
```

## 总结

TikTok的函数设计规范强调：
1. **简洁性**：编写小而专注的函数
2. **清晰性**：使用有意义的命名和适当的注释
3. **一致性**：遵循统一的参数传递和错误处理模式
4. **可维护性**：通过合理的函数分组和结构提高代码可读性
5. **可靠性**：正确处理错误和资源清理

这些实践有助于确保TikTok代码库中的函数既高效又易于理解和维护。

