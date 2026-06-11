# veImageX API 分类与接口说明

veImageX 提供了丰富的 API 接口，主要分为图片资源管理和附加组件两大类，支持开发者通过服务端 SDK 进行调用。

## 图片资源管理 API

图片资源管理 API 主要用于处理图片的上传、查询、删除和更新等操作。

### 核心接口

1. **ApplyImageUpload** - 获取文件上传地址
   - **接口说明**：获取文件上传地址用于上传图片
   - **使用场景**：文件上传前的准备工作
   - **备注**：SDK 建议直接使用集成的 UploadImages 方法

2. **CommitImageUpload** - 文件上传上报
   - **接口说明**：文件上传完成后进行上报
   - **使用场景**：确认文件上传完成
   - **备注**：SDK 建议直接使用集成的 UploadImages 方法

3. **GetImageUploadFile** - 获取服务下单个上传文件
   - **接口说明**：获取指定服务下的单个上传文件信息
   - **使用场景**：查询特定文件的上传状态和元数据
   - **备注**：请使用 SDK，阅读 K3S 生成 URL

4. **GetImageUploadFiles** - 获取服务下的上传文件
   - **接口说明**：获取指定服务下的所有上传文件列表
   - **使用场景**：批量查询文件信息

5. **DeleteImageUploadFiles** - 删除服务下多个文件
   - **接口说明**：用于删除 veImageX 服务下的文件
   - **使用场景**：批量删除不需要的图片资源

6. **UpdateImageUploadFiles** - 禁用/更新/预热文件/刷新缓存
   - **接口说明**：提供多种文件管理操作，包括禁用、更新、预热文件和刷新缓存
   - **使用场景**：文件状态管理和缓存控制
   - **请求示例**：
     ```http
     POST /?Action=UpdateImageUploadFiles&Version=2018-08-01&ServiceId=WMKp6UXedj HTTP/1.1
     Host: imagex.bytedanceapi.com
     Content-Type: application/x-www-form-urlencoded
     
     {
       "Action": 1,
       "ImageUrls": [
         "domain-xxx/img/bkt/key~tpl:param.format",
         "domain-yyy/img/bkt/key~tpl:param.format"
       ]
     }
     ```
   - **返回参数**：
     - `ServiceId`：服务 ID
     - `ImageUrls`：操作成功的图片 URL 列表
     - `FailUrls`：操作失败的图片 URL

7. **FetchImageUrl** - 图片资源 fetch 抓取
   - **接口说明**：资源 fetch 抓取接口（支持同步和异步）
   - **使用场景**：从外部 URL 抓取图片资源到 veImageX

8. **${domain}/${image_uri}~info** - 获取图片 meta 信息
   - **接口说明**：获取图片的元数据信息
   - **使用场景**：查询图片的尺寸、格式、大小等信息

## 附加组件 API

附加组件 API 主要用于图像处理、AI 算法等高级功能。

### 核心接口

1. **GetImageEraseModels** - 获取擦除使用的模型列表
   - **接口说明**：获取可用于图像内容擦除的模型列表
   - **使用场景**：图像水印、物体擦除等处理

2. **GetImageEraseResult** - 擦除图片指定位置水印等
   - **接口说明**：擦除图片中指定位置的水印或其他内容
   - **使用场景**：图像内容修复和清理

## 附加组件 2.0 API

附加组件 2.0 主要解决附加组件 1.0 调用时需要 case by case 编写 API 的问题，通过传递不同的模板参数来提高开发效率。

### 调用方式变化

附加组件 2.0 支持多种调用方式：

- **同步 API 调用**：适用于实时处理场景，超时时间为 30 秒
- **异步 API 调用**：适用于批量处理场景，超时时间为 10 秒
- **模板调用**：通过传递模板参数简化调用
- **批处理调用**：通过控制台配置回调地址，批量添加任务

### 核心接口

1. **CreateImageAITask** - 创建异步处理任务
   - **接口说明**：提交一条或多条 URL 或 URI 资源执行异步 AI 图像处理任务
   - **请求方式**：POST
   - **请求地址**：`https://imagex.volcengineapi.com/?Action=CreateImageAITask&Version=2023-05-01`
   - **请求频率限制**：单用户 1 次/秒
   - **关键参数**：
     - `WorkflowParameter`：AI 图像处理模板参数，需要将 JSON 压缩并转义为字符串
     - `DataType`：需要提交的图片数据类型，取值 `uri` 或 `url`

2. **AIProcess** - 同步处理任务
   - **接口说明**：提交一条 URL 或 URI 资源执行同步 AI 图像处理任务
   - **请求方式**：POST
   - **请求地址**：`https://imagex.volcengineapi.com/?Action=AIProcess&Version=2023-05-01`
   - **请求频率限制**：单用户 1 次/秒

3. **GetImageAITasks** - 获取 AI 图像处理任务信息
   - **接口说明**：查询异步处理任务的状态信息
   - **关键参数**：
     - `ServiceId`：服务 ID
     - `QueueId`：队列 ID，通过 CreateImageAITask 接口返回

4. **GetImageAITaskDetail** - 查询 AI 图像处理任务执行详情
   - **接口说明**：获取异步处理任务的详细执行结果
   - **关键参数**：`ServiceId`：服务 ID

## 批处理调用

批处理调用主要通过控制台创建队列，然后批量提交任务进行处理。

### 配置说明

- **队列创建**：通过控制台创建处理队列
- **回调配置**：在 AI 图像处理任务结束后，veImageX 会将结果回调至指定的回调地址
- **解析注意事项**：解析回调时需要根据 `workflow_template_id` 的值来解析，以免解析失败

## 服务端 SDK 支持

veImageX 提供了多种编程语言的 SDK 支持：

- **Golang SDK**：[https://www.volcengine.com/docs/508/1521680](https://www.volcengine.com/docs/508/1521680)
- **Python SDK**：[https://www.volcengine.com/docs/508/1521681](https://www.volcengine.com/docs/508/1521681)
- **Java SDK**：[https://www.volcengine.com/docs/508/1521682](https://www.volcengine.com/docs/508/1521682)
- **PHP SDK**：[https://www.volcengine.com/docs/508/1521683](https://www.volcengine.com/docs/508/1521683)

## 错误码处理

veImageX API 调用可能返回的错误码包括：

- **公共错误码**：[https://www.volcengine.com/docs/6369/68677](https://www.volcengine.com/docs/6369/68677)
- **veImageX 错误码**：[https://www.volcengine.com/docs/508/66156](https://www.volcengine.com/docs/508/66156)

## 使用建议

1. **选择合适调用方式**：
   - 实时处理：使用同步 API 调用
   - 批量处理：使用异步 API 或批处理调用
   - 复杂处理：使用附加组件 2.0 的模板调用

2. **注意频率限制**：
   - 同步调用：1 次/秒，超时 30 秒
   - 异步调用：1 次/秒，超时 10 秒

3. **集团内部使用**：集团内部使用需要更换内部 SDK，ToB 使用请使用 ToB SDK（否则鉴权不通过）

4. **服务地址**：接口仅支持在中国区域调用，对应 region 为 `cn-north-1`

