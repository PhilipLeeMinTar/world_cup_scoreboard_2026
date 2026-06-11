# 快速入门指南

## 概述

metricx是字节跳动内部的Go语言监控打点库，通过预定义Metric Model的集中管理方式，提供高效、高质量的metrics上报能力。本指南将帮助你快速上手使用metricx进行监控打点。

## 核心概念

### Metric Model设计理念

metricx的核心设计是通过结构体预定义所有打点，这种方式具有以下优势：

1. **集中管理**：所有metrics定义在一个地方，便于维护和查看
2. **代码生成友好**：结构化的定义方式为代码生成提供了清晰的模板
3. **类型安全**：编译时检查，避免运行时错误
4. **Lint支持**：配套Lint工具避免metrics v3可能遇到的误用问题

### 基本组件

- **Counter**：累积值统计，用于计数类指标
- **Timer**：耗时统计，计算min/max/avg/sum/count/分位值
- **Gauge**：瞬时值记录，用于当前状态指标
- **RateCounter**：单位时间累积值统计
- **Histogram**：直方图类型打点

## 快速开始

## 安装

```shell
go get code.byted.org/gopkg/metricx
```

### 步骤1：定义Metric Model

首先创建一个结构体来定义你的metrics：

```go
package main

import "code.byted.org/gopkg/metricx"

// 定义Metric Model
var AppMetrics = &struct {
    RequestCount metricx.Counter `metric:"request_count" tnames:"method,status"`
    ResponseTime metricx.Timer   `metric:"response_time" tnames:"method"`
    ActiveUsers  metricx.Gauge   `metric:"active_users"`
}{}
```

### 步骤2：初始化metricx

在程序启动时初始化metricx：

```go
func main() {
    // 初始化metricx，默认使用env.PSM()作为前缀
    metricx.MustInit(AppMetrics)
    
    // 或者使用自定义配置
    metricx.MustInit(
        AppMetrics,
        metricx.WithNamespace("myapp"),
        metricx.WithGlobalTags(map[string]string{
            "env": "production",
            "version": "1.0.0",
        }),
    )
}
```

### 步骤3：进行打点

在业务代码中进行metrics上报：

```go
func handleRequest(method string) {
    // 记录请求计数
    AppMetrics.RequestCount.Inc(1, 
        metricx.T{"method", method},
        metricx.T{"status", "success"},
    )
    
    // 记录响应时间
    start := time.Now()
    // ... 业务逻辑处理
    elapsed := time.Since(start)
    AppMetrics.ResponseTime.Record(elapsed, 
        metricx.T{"method", method},
    )
    
    // 更新活跃用户数
    AppMetrics.ActiveUsers.Update(getActiveUserCount())
}
```

## 字段标签详解

metricx通过结构体字段标签来定义metric的元信息：

### metric标签
定义metric name后缀：
```go
`metric:"request_count"`  // 完整的metric name为: {prefix}.request_count
```

### tnames标签
定义预定义的tag name，允许打点时动态传入对应的value：
```go
`tnames:"method,status"`  // 打点时可传入method和status的tag值
```

### tags标签
定义静态键值对，适用于tag键值均已知的情况：
```go
`tags:"service=user,type=api"`  // 每次打点都会携带这些静态tag
```

### prefix标签
用于嵌套结构体，为结构体内字段统一加前缀：
```go
`prefix:"api"`  // 结构体内的metrics会加上"api."前缀
```

## 初始化选项

metricx提供多种初始化选项来满足不同需求：

### 基本初始化
```go
metricx.MustInit(Model)  // 使用默认配置
```

### 自定义命名空间
```go
metricx.MustInit(Model, metricx.WithNamespace("custom_namespace"))
```

### 添加全局标签
```go
metricx.MustInit(Model, metricx.WithGlobalTags(map[string]string{
    "env": "prod",
    "region": "sg",
}))
```

### 调整时间单位
```go
metricx.MustInit(Model, metricx.WithTimeUnit(time.Millisecond))
```

## 最佳实践建议

1. **统一管理**：将所有metrics定义在专门的包或文件中
2. **合理命名**：使用有意义的metric名称和tag名称
3. **避免过度打点**：只打点对监控和排障有意义的指标
4. **使用静态标签**：对于不变的元信息使用tags标签
5. **使用动态标签**：对于运行时变化的元信息使用tnames标签

## 常见问题

### Q: metricx默认的前缀是什么？
A: 默认使用`env.PSM()`作为metric name前缀。

### Q: 如何同时上报到多个存储？
A: 使用`WithFactories`选项，可以同时向metrics和influxdb等存储打点。

### Q: 打点时忘记传tnames定义的tag会怎样？
A: 如果tnames里已定义但打点时未传相应tag或者tag value为空，会填默认tag value为`-`。

### Q: 如何避免打点时的误用？
A: 建议安装golintx和bytecheck插件，在MR阶段和编码阶段进行前置检查。

## 下一步

完成快速入门后，建议深入了解：
- [打点类型详解](./metric-types.md) - 各种打点类型的具体使用场景
- [字段标签配置](./field-tags.md) - 高级标签配置技巧
- [最佳实践指南](./best-practices.md) - 实际业务场景的示例
- [高级选项配置](./advanced-options.md) - 定制化配置选项

