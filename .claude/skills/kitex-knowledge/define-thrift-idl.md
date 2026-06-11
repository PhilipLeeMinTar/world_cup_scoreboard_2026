# Thrift IDL 基础

## 基本语法

### Namespace

```thrift
namespace go api
```

### 数据类型

#### 基本类型

```thrift
bool
byte
i16
i32
i64
double
string
binary
```

#### 容器类型

```thrift
list<T>
set<T>
map<K, V>
```

### 结构体

```thrift
struct User {
    1: required i64 uid
    2: required string name
    3: optional string email
}
```

### 服务定义

```thrift
service UserService {
    User GetUser(1: i64 uid)
    void UpdateUser(1: User user)
}
```

## Include

```thrift
include "base.thrift"

struct MyRequest {
    1: required string name
    2: required base.BaseReq base
}
```

## 最佳实践

### 字段编号

- 使用 1-255 获得更好的编码效率
- 255 通常保留给 Base 字段

### 向后兼容

- ✅ 添加 optional 字段
- ✅ 删除 optional 字段
- ❌ 修改字段编号
- ❌ 修改字段类型

## 相关文档

- [从 IDL 生成代码](./generate-code-from-idl.md)
- [创建第一个服务](./create-first-service.md)
