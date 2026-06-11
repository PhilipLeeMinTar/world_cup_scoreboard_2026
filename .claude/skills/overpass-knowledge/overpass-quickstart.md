# Overpass Quick Start

## 概述

本文通过一个完整的实例,演示如何使用 Overpass 完成一次 RPC 调用。

**示例场景**: 调用 `toutiao.location.location` 服务的 `MultiGetIPInfo` 方法

**完整流程**:
```
1. 在 Overpass 网站添加白名单
2. 在本地添加依赖
3. 编写代码进行 RPC 调用
```

---

## Step 1: 在 Overpass 网站添加白名单

### 白名单机制说明

Overpass 会为每个 PSM 创建一个代码仓库,包含:
- 自动生成的 `kitex_gen`
- Client 的创建
- 常用通用能力的封装实现
- IDL 变化时自动更新

**白名单原因**: 公司 RPC 服务众多,无法为所有服务预生成仓库,因此采用白名单机制,仅对用户需要调用的 PSM 创建仓库。

### 操作步骤

#### 1.1 访问 Overpass 网站

访问 [overpass.bytedance.net](https://overpass.bytedance.net/)

**网站功能**:
- **IDL 信息查询** - 查询 PSM 信息,生成仓库
- **仓库信息管理** - 查看已生成的仓库

#### 1.2 查询 PSM 并生成仓库

在 "IDL 信息查询" 页面:

1. 搜索目标 PSM (例如: `toutiao.location.location`)
2. 点击 **"生成 Overpass 仓库"** 按钮
3. 等待数秒,页面自动刷新
4. 按钮变为 **"仓库已存在"**

**生成的仓库路径**:
```
https://code.byted.org/overpass/toutiao_location_location
```

#### 1.3 验证仓库生成

在 "仓库信息管理" 页面可以查询到生成的仓库信息:
- 仓库 URL
- 生成时间
- IDL 版本
- 自动更新状态

**异常处理**: 如果遇到生成失败或自动更新失败,参考 [添加白名单详细说明](https://site.bytedance.net/docs/3861/5551/47098/)

---

## Step 2: 在本地编写代码

### 2.1 添加依赖

Overpass 网站提供了快捷命令功能,简化操作流程。

**方法 1: 使用快捷命令** (推荐)

1. 在 Overpass 网站的仓库详情页,点击 **"添加依赖"** 按钮
2. 命令自动复制到剪贴板
3. 在终端执行:

```bash
go get code.byted.org/overpass/toutiao_location_location
```

**方法 2: 手动添加**

```bash
go get code.byted.org/overpass/<P_S_M>
```

将 `<P_S_M>` 替换为下划线形式的 PSM (例如: `toutiao_location_location`)

**验证依赖**:

```bash
go mod tidy
```

### 2.2 获取 Import 路径

**方法 1: IDE 自动导入** (推荐)

使用 `go get` 添加依赖后,IDE (如 GoLand) 会自动识别并导入包。

**方法 2: 使用快捷命令**

在 Overpass 网站点击 **"import 路径"** 按钮,复制以下内容:

```go
"code.byted.org/overpass/toutiao_location_location/rpc/toutiao_location_location"
```

---

## Step 3: 编写代码进行 RPC 调用

### 3.1 基础调用示例

创建文件 `main.go`:

```go
package main

import (
    "context"
    "fmt"

    "code.byted.org/overpass/toutiao_location_location/rpc/toutiao_location_location"
)

func main() {
    ctx := context.Background()

    // 只需一行代码完成 RPC 调用
    resp, err := toutiao_location_location.MultiGetIPInfo(ctx, []string{"8.8.8.8"})

    fmt.Println(resp, err)
}
```

### 3.2 调用格式说明

**标准格式**:

```go
resp, err := P_S_M.Method(ctx, YourParams)
```

**格式解析**:
- `P_S_M` - 下划线形式的 PSM 作为包名
- `Method` - IDL 中定义的方法名
- `ctx` - Context 对象
- `YourParams` - 方法参数 (非 optional 字段)

**示例**:

```go
// 调用 tiktok.user.service 的 GetUserInfo 方法
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)

// 调用 tiktok.payment.service 的 CreateOrder 方法
resp, err := tiktok_payment_service.CreateOrder(ctx, &OrderRequest{
    Amount: 100,
    Currency: "USD",
})
```

### 3.3 "默认封装" 和 "默认方法"

本示例使用的是 Overpass 的 **"默认封装"** 调用方式。

**特点**:
- ✅ 自动创建 Client (指定 PSM)
- ✅ 不需要 Kitex Option
- ✅ Request 结构体简化,只接受非 optional 字段
- ✅ 自动处理错误和日志

**适用场景**: 简单的 RPC 调用场景

**高级用法**: 如需自定义 Client、配置 Option、处理 optional 字段等,参考后续文档。

---

## Step 4: 运行和验证

### 4.1 编译和运行

```bash
# 编译
go build -o main main.go

# 运行
./main
```

### 4.2 预期输出

```
&{IpInfos:map[8.8.8.8:0xc00012e000] LogID:20250115123456} <nil>
```

**输出说明**:
- `IpInfos` - IP 信息的 map
- `LogID` - 请求日志 ID
- `<nil>` - 没有错误

---

## 进阶使用

### 场景 1: 调用需要多个参数的方法

```go
resp, err := tiktok_user_service.UpdateUserInfo(ctx, &UpdateUserInfoRequest{
    UserID: 12345,
    Nickname: "NewName",
    Avatar: "https://example.com/avatar.png",
})
```

### 场景 2: 处理错误

```go
resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
if err != nil {
    // Overpass 自动封装了错误信息
    fmt.Printf("RPC 调用失败: %v\n", err)
    return
}

fmt.Printf("用户信息: %+v\n", resp)
```

### 场景 3: 使用 Context 传递元数据

```go
import "github.com/cloudwego/kitex/pkg/klog"

ctx := context.Background()
ctx = context.WithValue(ctx, "trace_id", "abc123")

resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
```

---

## 你可能会关心的问题

### Q1: IDL 文件是从哪里获取的?

**A**: Overpass 从 **DevFlow 平台**自动获取 IDL 文件。

**要求**:
- 服务的 IDL 必须在 DevFlow 中注册
- IDL 必须提交到主干或任务分支

**验证**: 在 DevFlow 平台搜索 PSM,确认 IDL 文件存在

### Q2: 生成代码需要多久?

**A**:
- **简单 IDL**: 数秒内完成
- **复杂 IDL**: 10-30 秒
- **大型项目**: 最多 1-2 分钟

### Q3: 采用哪个 RPC 框架?

**A**: Overpass 基于 **Kitex** 框架生成代码。

**Kitex 特性**:
- CloudWeGo 开源项目
- 高性能 RPC 框架
- 支持 Thrift 和 Protobuf
- 字节跳动内部广泛使用

### Q4: Overpass 网站还有什么实用功能?

**A**: 参考 [前端实用功能](https://site.bytedance.net/docs/3861/5551/71387/) 文档

**核心功能**:
- IDL 信息查询
- 仓库信息管理
- 快捷命令 (添加依赖、复制 import 路径)
- 代码生成进度查询
- 手动触发更新

### Q5: Overpass 除了 RPC 调用,还提供什么能力?

**A**: 参考 [其他功能](https://site.bytedance.net/docs/3861/5551/68396/) 文档

**其他能力**:
- RPC Mock 支持
- 自定义扩展能力
- 错误封装和日志打印
- Kitex Option 配置
- 下游 PSM 指定

### Q6: 为什么要为每个 PSM 创建一个仓库?

**A**: 参考 [设计上的考虑](https://site.bytedance.net/docs/3861/5551/73480/) 文档

**设计理由**:
- 独立版本管理
- 避免依赖冲突
- 按需加载
- 自动更新隔离
- 更清晰的依赖关系

---

## 常见错误排查

### 错误 1: "找不到包"

**错误信息**:

```
cannot find package "code.byted.org/overpass/xxx"
```

**原因**: 未添加依赖或依赖未同步

**解决方案**:

```bash
go get code.byted.org/overpass/<P_S_M>
go mod tidy
```

### 错误 2: "方法不存在"

**错误信息**:

```
undefined: toutiao_location_location.MultiGetIPInfo
```

**原因**:
1. 方法名拼写错误
2. IDL 中没有定义该方法
3. Overpass 仓库未更新

**解决方案**:

1. 检查方法名拼写
2. 在 Overpass 网站查看 IDL 定义
3. 更新依赖:

```bash
go get -u code.byted.org/overpass/<P_S_M>@latest
```

### 错误 3: "仓库生成失败"

**可能原因**:
- IDL 在 DevFlow 中不存在
- IDL 语法错误
- PSM 格式错误

**解决方案**: 参考 [添加白名单](https://site.bytedance.net/docs/3861/5551/47098/) 详细说明

---

## 最佳实践

### 1. 及时更新依赖

IDL 变更后,及时更新 Overpass 依赖:

```bash
go get -u code.byted.org/overpass/<P_S_M>@latest
go mod tidy
```

### 2. 使用 Context 传递请求元数据

```go
import (
    "context"
    "github.com/cloudwego/kitex/pkg/rpcinfo"
)

ctx := context.Background()
ctx = rpcinfo.NewCtxWithCallInfo(ctx, rpcinfo.FromHTTPRequest(req))

resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
```

### 3. 统一错误处理

```go
func callRPC(ctx context.Context, userID int64) error {
    resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
    if err != nil {
        return fmt.Errorf("调用 RPC 失败: %w", err)
    }

    // 处理响应
    return nil
}
```

### 4. 添加日志

```go
import "github.com/cloudwego/kitex/pkg/klog"

resp, err := tiktok_user_service.GetUserInfo(ctx, userID)
if err != nil {
    klog.Errorf("GetUserInfo failed: %v", err)
    return err
}

klog.Infof("GetUserInfo success: userID=%d", userID)
```

---

## 下一步

完成 Quick Start 后,可以学习:

1. **[overpass Go 代码基本使用](overpass-go-usage.md)** - 深入了解 Overpass 的各种用法
2. **[overpass 平台基础操作](overpass-platform-operations.md)** - 掌握 Overpass 网站的所有功能
3. **[DevFlow Overpass 集成](devflow-overpass-integration.md)** - 在 GDP 开发中使用 Overpass

---

## 相关文档

- [overpass-introduction.md](overpass-introduction.md) - Overpass 平台简介
- [devflow-overpass-integration.md](devflow-overpass-integration.md) - GDP 开发中使用 Overpass
- [概况文档](https://site.bytedance.net/docs/3861/5551/71170/) - 更详细的参数和细节
- [前端实用功能](https://site.bytedance.net/docs/3861/5551/71387/) - Overpass 网站功能详解
