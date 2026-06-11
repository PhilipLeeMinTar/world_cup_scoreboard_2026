# naming-conventions.md

## TikTok命名规范指南

TikTok命名规范旨在确保代码的可读性、一致性和可维护性。良好的命名能够清晰地表达代码的意图，减少对注释的依赖，提高团队协作效率。

### 基本原则

1. **揭示意图**：名称应该回答所有重要问题，包括为什么存在、做什么以及如何使用
2. **避免冗余注释**：如果名称需要注释才能理解，说明名称没有充分揭示其意图
3. **简洁准确**：名称应该简短但能准确表达含义，避免过于冗长或过于简略

### 命名格式要求

#### 大小写规则
- **[MUST] 使用CamelCase/camelCase**：大多数名称应使用驼峰命名法，避免使用下划线
- **导出函数**：使用MixedCaps（首字母大写）
- **非导出函数**：使用mixedCaps（首字母小写）
- **测试函数**：可以包含下划线用于分组相关测试用例，例如`TestMyFunction_MyTest`

**示例对比**：
```go
// 不推荐
var (
    userId      int64
    first_name  string
    lastName    string
)

// 推荐
var (
    userID      int64
    firstName   string
    lastName    string
)
```

#### 缩写词处理
- **[MUST] 首字母缩写词使用全大写**：如XML、HTTP、ID等
- **非导出变量**：如果缩写词在开头，则全部小写

**示例对比**：
```go
// 不推荐
type XmlRequest struct {}

// 推荐
type XMLRequest struct {}
```

### 包命名规范

#### 基本要求
- **[MUST] 同一项目中包名唯一**：每个包名在项目中应该是唯一的
- **[MUST] 全部小写**：不使用大写字母或下划线
- **[MUST] 使用单数形式**：Go语言中包名不使用复数形式
- **[SHOULD] 简短但有代表性**：名称应该简短但能清晰表达包的功能

#### 命名建议
- **基于功能命名**：包名应该反映其提供的功能，而不是包含的内容
- **避免通用名称**：避免使用过于宽泛的包名如`common`和`util`，特别是在最终包中
- **使用简单名词**：如`time`、`list`、`http`等

**示例**：
- `time`：提供时间测量和显示功能
- `list`：实现双向链表
- `http`：提供HTTP客户端和服务器实现

#### 子包处理
- **子包可以使用通用名称**：如`comment/common`比`commentcommon`更好
- **考虑功能拆分**：有时将不同功能拆分到不同的子包中更好

### 函数命名规范

#### 命名格式
- **[MUST] 使用MixedCaps或mixedCaps**：导出函数使用MixedCaps，非导出函数使用mixedCaps
- **[SHOULD NOT] 引用包内容**：函数名不应包含包信息，避免重复
- **[RECOMMENDED] 使用动词或动词短语**：如`postPayment`、`deletePage`、`save`等

**示例对比**：
```go
// 不推荐
package http
func HttpServer() {}

// 推荐
package http
func Server() {}
```

#### 命名建议
- **结合包名**：`comment.GetList()`比`GetCommentList()`更精确
- **避免冗余**：函数名不应重复包名中的信息

### 变量命名规范

#### 基本原则
- **[SHOULD] 简短而非冗长**：变量名应该简洁
- **[SHOULD NOT] 包含类型信息**：除非需要区分类型转换

#### 具体建议
1. **省略类型明显的信息**：如果类型从上下文可以推断，则省略类型信息

**示例对比**：
```go
// 不推荐
var nicknameStr string
var userSlice []*User

// 推荐
var nickname string
var users []*User
```

2. **类型转换时保留类型信息**：当变量需要从一种类型转换为另一种类型时，需要在名称中包含类型信息

**示例**：
```go
func getComments(commentID int64) map[int64]*Comment {
    commentIDStr := strconv.FormatInt(commentID, 10)
    // ...
}
```

3. **省略无歧义的信息**：省略不会引起歧义的词语
4. **省略上下文已知的信息**：省略从上下文中可以推断的信息
5. **省略无意义的词语**：省略没有实际含义的词语

#### 短变量名一致性
- **[SHOULD] 保持短变量名含义一致**：如果使用短变量名，应该在整个代码中保持一致性

**示例对比**：
```go
// 不推荐
for i, v := range slice {...}
for a, b := range slice {...}

// 推荐
// 应该保持一致
for i, v := range slice {...}
```

### 接收器命名规范

#### 基本原则
- **[SHOULD] 使用类型的一到两个字母缩写**：如"c"或"cl"表示"Client"
- **[SHOULD NOT] 使用通用名称**：避免使用"self"、"this"或"me"等面向对象语言的标识符

#### 命名建议
- **简短一致**：接收器名称可以很短，因为它会出现在该类型每个方法的几乎每一行中
- **保持一致性**：如果在某个方法中将接收器命名为"c"，不要在另一个方法中命名为"cl"

**示例对比**：
```go
// 不推荐
type User struct {
    Name string
}
func (self *User) Name() string {
    return self.Name
}

// 推荐
type User struct {
    Name string
}
func (u *User) Name() string {
    return u.Name
}
```

### 命名实践建议

#### 避免过度详细
- **不要追求最短**：命名过程中不应追求最短，最重要的是能够清晰表达
- **避免无意义缩写**：避免使用愚蠢的自造词代替正确的英语术语

**示例对比**：
```go
// 不推荐
var genmdhms int64

// 推荐
var generationTimestamp int64
```

#### 上下文考虑
- **考虑使用场景**：在特定上下文中，某些缩写可能是熟悉的，可以使用
- **避免宽泛名称**：如`common`、`util`等，特别是在最终包中

### 命名检查工具

TikTok使用以下golintx规则进行命名规范检查：

- **GO-520-A8022E byted_s_variable_name**：变量命名规则
- **GO-520-FE9F0A byted_s_package_name_same_with_dir**：包名与目录名一致规则
- **GO-520-2FEBA4 byted_s_package_name_lower_letter**：包名小写字母规则
- **GO-520-A93B4B byted_s_function_name**：函数命名规则

这些规则帮助确保代码符合TikTok命名规范，提高代码质量和可维护性。
