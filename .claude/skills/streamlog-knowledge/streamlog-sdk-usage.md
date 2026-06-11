# StreamLog Golang SDK 接入指南

## 适用范围与简述

StreamLog Golang SDK 主要用于将应用日志高效、可靠地发送至 Argos 日志服务平台，支持在不同环境（如本地开发、TCE）下的多种日志输出方式（控制台、文件、Agent）。

推荐使用的 SDK 版本为 `v2` (`code.byted.org/gopkg/logs/v2`)，它提供了性能更优的链式 API、更灵活的配置选项，并对 `v1` 版本的大部分 API 实现了兼容。

## 安装与升级

### 安装

推荐使用 `go get` 命令安装最新的 `v2` 版本 SDK：

```bash
go get code.byted.org/gopkg/logs/v2
```

### 从 v1 升级

如果你正在使用旧版的 `gopkg/logs` (`v1`)，可以直接将代码中的 import 路径从 `code.byted.org/gopkg/logs` 替换为 `code.byted.org/gopkg/logs/v2`。

`v2.1.49` 及之后版本兼容了 `v1` 的绝大部分常用 API，这使得迁移过程通常只需修改包名即可完成。但仍需注意 `v1` 采用纯异步可丢弃的日志发送方式，而 `v2` 默认为同步不丢弃，行为上存在差异。

## 初始化与基础用法

SDK 提供了两个预先配置好的全局 Logger：`log.V1` 和 `log.V2`，可以直接使用。`log.V2` 采用了性能更优的链式 API，是当前推荐的选择。

### 最小可运行示例

以下是一个最小化的可运行示例，展示了如何使用默认的 `log.V2` Logger 打印一条简单的日志。

```go
package main

import (
    "context"

    "code.byted.org/gopkg/logid"
    "code.byted.org/gopkg/logs/v2/log"
)

func main() {
    // 1. 生成一个唯一的 Log ID
    ctx := context.Background()
    ctx = logid.NewContext(ctx, logid.GenLogID())

    // 2. 使用链式 API 打印一条 Info 级别的日志
    // .With(ctx) 会自动提取上下文中的 Log ID 和 Span ID
    log.V2.Info().
        With(ctx).
        Str("这是一个简单的日志示例").
        KV("user_id", "12345").
        KV("status", "success").
        Emit()

    // 3. 打印一条 Error 级别的日志
    log.V2.Error().
        With(ctx).
        Str("这是一个错误日志示例").
        KV("error_code", 500).
        Emit()
}
```

> **注意**：
> 在实际项目中，通常会在 `init` 函数中根据需要自定义 Logger，例如设置日志级别、添加或修改输出目标（Writer）。如果直接使用 `log.V2`，其默认行为是：TCE 环境下输出到文件和 Agent，非 TCE 环境下输出到控制台。

### 自定义 Logger 初始化

你可以通过 `log.SetDefaultLogger` 函数来覆盖默认的 Logger 配置。

```go
package main

import (
    "code.byted.org/gopkg/logs/v2"
    "code.byted.org/gopkg/logs/v2/log"
    "code.byted.org/gopkg/logs/v2/writer"
)

func init() {
    // 定义一系列配置选项
    options := []logs.Option{
        // 设置日志输出目标和级别
        logs.SetWriter(
            logs.InfoLevel, // 全局最低日志级别
            writer.NewConsoleWriter(), // 输出到控制台
            writer.NewAgentWriter(),   // 输出到 Argos Agent
            writer.NewAsyncWriter( // 异步写入文件
                writer.NewFileWriter("logs/app.log", writer.Hourly), // 按小时轮转
                true, // Channel 满时丢弃日志
            ),
        ),
        // 设置在日志中打印函数名
        logs.SetDisplayFuncName(true),
    }

    // 应用配置到全局默认 Logger
    log.SetDefaultLogger(options...)
}

func main() {
    log.V2.Info().Str("这条日志会根据 init 中的配置进行输出").Emit()
}

```

## 典型场景示例

以下示例演示了在一个业务函数中，如何记录一条包含上下文、结构化信息和错误处理的完整日志。

```go
package main

import (
	"context"
	"errors"
	"fmt"

	"code.byted.org/gopkg/logid"
	"code.byted.org/gopkg/logs/v2/log"
)

// UserInfo 定义了用户信息的结构体
type UserInfo struct {
	UserID   string `json:"user_id"`
	UserName string `json:"user_name"`
}

// processUserRequest 模拟处理用户请求的函数
func processUserRequest(ctx context.Context, userID string) error {
	// 模拟从数据库或缓存获取用户信息
	userInfo, err := getUserInfo(userID)
	if err != nil {
		// 记录错误日志
		log.V2.Error().
			With(ctx).
			Str("获取用户信息失败").
			KV("target_user_id", userID).
			Error(err). // 使用 .Error() 方法记录错误详情
			Emit()
		return fmt.Errorf("无法获取用户信息: %w", err)
	}

	// 记录成功日志，并附带结构化的用户信息
	log.V2.Info().
		With(ctx).
		Str("成功处理用户请求").
		Obj(userInfo). // 使用 .Obj() 方法记录结构体信息，会自动进行 JSON 序列化
		Emit()

	return nil
}

// getUserInfo 模拟获取用户信息的函数
func getUserInfo(userID string) (*UserInfo, error) {
	if userID == "1001" {
		return &UserInfo{
			UserID:   "1001",
			UserName: "zhangsan",
		}, nil
	}
	// 模拟用户不存在的场景
	return nil, errors.New("用户不存在或数据库连接失败")
}

func main() {
	// 场景一：成功处理
	ctxSuccess := logid.NewContext(context.Background(), logid.GenLogID())
	fmt.Println("--- 开始处理成功场景 ---")
	if err := processUserRequest(ctxSuccess, "1001"); err != nil {
		fmt.Printf("处理失败：%v\n", err)
	}
	fmt.Println("--- 成功场景处理结束 ---")

	fmt.Println()

	// 场景二：处理失败
	ctxFail := logid.NewContext(context.Background(), logid.GenLogID())
	fmt.Println("--- 开始处理失败场景 ---")
	if err := processUserRequest(ctxFail, "9999"); err != nil {
		fmt.Printf("处理失败，已记录错误日志：%v\n", err)
	}
	fmt.Println("--- 失败场景处理结束 ---")

	// 确保异步日志有机会被写入
	log.Flush()
}
```

**示例说明**：

1.  **上下文与 LogID**：通过 `logid.GenLogID()` 创建唯一请求标识，并使用 `log.V2.With(ctx)` 将其贯穿整个请求处理链路，便于问题排查。
2.  **结构化日志**：使用 `.KV()` 和 `.Obj()` 记录关键字段和业务对象。这比拼接字符串更易于机器解析和后续的日志检索分析。
3.  **错误处理**：当发生错误时，使用 `log.V2.Error()` 记录错误级别的日志，并通过 `.Error(err)` 将详细的 `error` 信息附加到日志中。

## 进阶配置

### 异步与批量写入

为了提升性能，特别是对于高并发场景，推荐使用异步写入（`AsyncWriter`）。`AsyncWriter` 会将日志放入一个 channel 中，由后台 goroutine 负责写入目标。

```go
// 示例：配置一个异步写入文件的 Writer
// 第二个参数 `true` 表示当 channel 满时，允许丢弃新的日志
asyncFile := writer.NewAsyncWriter(
    writer.NewFileWriter("logs/app.log", writer.Daily), // 按天轮转
    true, // 允许丢弃
)
```

### 日志限流

-   **针对单条日志**：对于循环或高频调用的日志点，可以使用 `.Limit(n)` API 限制其每秒最多输出 `n` 次，以避免日志风暴。

    ```go
    for i := 0; i < 1000; i++ {
        log.V2.Info().
            Limit(10). // 此日志点每秒最多输出 10 次
            Str("在循环中打印日志").
            KV("iteration", i).
            Emit()
    }
    ```
-   **针对 Writer**：也可以在 Writer 层面进行限流，控制某个输出目标的整体写入速率。

    ```go
    // 每秒最多向控制台写入 100 条日志
    rateLimitedConsole := writer.NewRateLimitWriter(writer.NewConsoleWriter(), 100)
    ```

### 日志轮转与清理

使用 `FileWriter` 时，可以配置日志文件的轮转策略（按小时/天）和保留策略。

```go
fileWriter := writer.NewFileWriter("logs/app.log",
    writer.Hourly, // 按小时轮转
    writer.SetKeepFiles(24), // 保留最近 24 个日志文件
    writer.SetFileSizeLimit(100 * 1024 * 1024), // 单个文件最大 100MB
)
```

## 常见问题与排错

1.  **为什么在程序退出时会丢失最后几条日志？**
    -   **原因**：如果你使用了异步 Writer（`AsyncWriter`），日志写入操作是在后台 goroutine 中进行的。如果主程序在日志被完全写入前就退出了，这部分日志就会丢失。
    -   **解决方案**：在程序正常退出前（例如 `main` 函数末尾），调用 `log.Flush()` 方法，它会阻塞并等待所有缓冲区的日志被清空，确保日志完整写入。

2.  **为什么从 v1 升级到 v2 后，应用性能感觉变慢了？**
    -   **原因**：`v1` SDK 采用纯异步且可丢弃的策略，写入压力大时会直接丢日志以保证应用性能。而 `v2` SDK 为了保证日志的可靠性，默认采用同步或不丢弃的异步策略。
    -   **解决方案**：评估业务对日志可靠性的要求。如果可以接受在极端情况下丢失部分日志，可以在初始化 `AsyncWriter` 时将其 `discard` 参数设为 `true`。

3.  **如何在封装了 log 包后，打印正确的源文件和行号？**
    -   **原因**：当你将 `log.V2` 的调用封装在自己的函数（如 `myLogger.Info(...)`）中时，SDK 默认获取到的调用位置是你的封装函数，而不是实际业务代码的位置。
    -   **解决方案**：使用 `.CallDepth(n)` API 调整调用栈深度。默认值为 `0`，指向 `log.V2` 的直接调用方。如果封装了一层，通常需要设置为 `1`。可以在 Logger 初始化时通过 `logs.SetCallDepth()` 全局设置，或在单条日志上动态调整。

4.  **如何在开发环境打印 Debug 日志，但在生产环境只打印 Info 及以上级别？**
    -   **原因**：不同环境对日志详细程度的要求不同。
    -   **解决方案**：在初始化 Logger 时，通过 `logs.SetWriter(level, ...)` 设置不同 Writer 的最低日志级别。更灵活的方式是利用动态日志级别功能，通过 `context` 临时覆盖 Logger 的级别设置。

    ```go
    // 生产环境 Logger 默认级别为 Info
    // log.SetDefaultLogger(logs.SetWriter(logs.InfoLevel, ...))
    
    // 在需要调试时，通过 context 临时开启 Debug 日志
    ctxDebug := context.WithValue(context.Background(), logs.DynamicLogLevelKey, logs.DebugLevel)
    log.V2.Debug(logs.WithCtx(ctxDebug)).Str("这条 Debug 日志可以被打印出来").Emit()
    ```
