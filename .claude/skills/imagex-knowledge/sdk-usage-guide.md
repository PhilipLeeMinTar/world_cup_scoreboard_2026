# veImageX 服务端 SDK 使用指南

veImageX 提供了配套的服务端 SDK，支持多种编程语言，帮助开发者更方便地调用 API。

## 支持的编程语言

veImageX 服务端 SDK 支持以下编程语言：

- **Golang SDK** - 适用于 Go 语言项目
- **Java SDK** - 适用于 Java 语言项目  
- **Python SDK** - 适用于 Python 语言项目
- **PHP SDK** - 适用于 PHP 语言项目

## SDK 主要功能

服务端 SDK 主要覆盖以下功能场景：

### 1. 图片检测与识别
- 获取图片人脸坐标等检测功能
- 建议使用服务端 SDK 来调用相关 API

### 2. 智能审核
- 创建图片、音频、视频审核任务
- 获取审核任务结果
- 支持智能审核 2.0 版本

### 3. AI 图像处理
- 创建 AI 图像处理任务（同步/异步）
- 查询 AI 图像处理任务执行详情
- 获取 AI 图像处理任务信息

### 4. 画质增强
- 获取编码后图片二进制数据
- 支持多种画质增强算法

## 使用建议

1. **优先使用 SDK**：建议使用服务端 SDK 来调用 API，而不是直接调用原始 API 接口
2. **错误处理**：SDK 提供了完善的错误码处理机制，建议参考[错误码文档](https://www.volcengine.com/docs/508/66156)进行错误处理
3. **版本兼容**：注意不同版本 SDK 的兼容性，建议使用最新版本

## 快速开始示例

### Golang 示例
```go
// 使用 veImageX Golang SDK 进行图片处理
import "github.com/volcengine/ve-imagex-sdk-golang"

// 初始化客户端
client := imagex.NewClient(accessKey, secretKey, region)

// 调用图片处理 API
result, err := client.ProcessImage(params)
```

### Java 示例
```java
// 使用 veImageX Java SDK
import com.volcengine.imagex.ImageXClient;

// 初始化客户端
ImageXClient client = new ImageXClient(accessKey, secretKey, region);

// 调用图片处理 API
ImageResult result = client.processImage(params);
```

### Python 示例
```python
# 使用 veImageX Python SDK
from volcengine.imagex import ImageXClient

# 初始化客户端
client = ImageXClient(access_key=access_key, secret_key=secret_key, region=region)

# 调用图片处理 API
result = client.process_image(params)
```

## 注意事项

1. **认证信息**：使用 SDK 前需要获取正确的 Access Key 和 Secret Key
2. **区域配置**：根据业务所在区域配置正确的 region 参数
3. **版本更新**：定期更新 SDK 版本以获取最新功能和修复
4. **性能优化**：对于高频调用场景，建议使用连接池和缓存机制

## 相关文档

- [veImageX 官方文档](https://www.volcengine.com/docs/508)
- [错误码说明](https://www.volcengine.com/docs/508/66156)
- [公共错误码](https://www.volcengine.com/docs/6369/68677)
