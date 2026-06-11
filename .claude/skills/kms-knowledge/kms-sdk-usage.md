基于检索到的KMS SDK相关信息，我现在为"SDK接入"模块生成细节说明文档 `kms-sdk-usage.md` 的内容。根据检索结果，我将严格遵循文档内容，不添加任何未在片段中明确提及的信息。

# KMS SDK 使用指南

## 概述

KMS SDK 支持多种编程语言，包括 Golang、Python、Java、C++ 和 NodeJS，分为 V1 SDK（Wrapper SDK）和 V2 SDK 两个版本。

## 身份认证

使用 SDK 时需要进行身份认证：

- **本地测试**：使用 doas 工具，如 `doas -p p.s.m go run main.go`
  - doas 文档：[doas工具使用说明](https://bytedance.feishu.cn/space/doc/85d9fb0GEEHalMJqmNvJNg)
  - doas 接入 ide 文档：[doas 原理 及 如何支持 debug](https://bytedance.feishu.cn/space/doc/doccnRmbMarAkjwOeH8lgPzcD5c)
- **服务部署**：tce 上的服务开启服务认证（tce服务信息页面-集群操作-集群配置-高级配置-服务认证）

## SDK 版本与实现逻辑

### KMS Wrapper SDK

在最新版本的 KMS V1 SDK（Go, Python, Java）中，支持自动通过安全组维护的 TCC 配置来判断某个 p.s.m 服务使用 KMS SDK 时连接到 KMS V1 或 KMS V2。

**实现逻辑**：如果在 SDK 建立 KMS client 时传入的 p.s.m 在对应环境（Maliva/VA/AliSG/BOEi18n）的 TCC p.s.m 服务列表中存在，则自动连到 KMS V2。否则默认连接到 KMS V1 后端。

SDK 接口与 V1 保持一致，但 V1 中已废弃的几个接口在 V2 中不再支持。

## SDK 安装方式

### Python SDK
- 库地址：https://code.byted.org/security/bytedkms/
- 安装：`bytedkms>=2.3.4`
  - `sudo pip install bytedkms==2.3.4`
  - 如果找不到库，加上 `--index-url=https://bytedpypi.byted.org/simple/`
- TCE 上的服务可以选择选装库依赖（`bytedkms>=2.3.4,<3.0.0`）
- 开发机安装时可能遇到 ss_lib 的问题，可以参考 [kms python 环境问题总结](https://bytedance.feishu.cn/docs/doccngd5tD3p5vhFRzG3OX#)

### Golang SDK
- 库地址：https://code.byted.org/security/gokms/
- 选择 tag：`v1.4.3`
- 或使用分支 master 并保证代码为最新

### NodeJS SDK
- 库地址：https://code.byted.org/nodejs/byted-service/tree/master/packages/kms/

### Java SDK
- 库地址：https://code.byted.org/security/kms-java

### C++ SDK
- 库地址：https://code.byted.org/security/cppkms

## DKMS SDK 使用

### DKMS 介绍
DKMS 是 KMS V2 版本，SDK 入口地址：
- Golang：https://code.byted.org/security/kms-v2-sdk-golang/tags
- Java：https://luban.bytedance.net/maven/publish/detail/105/versions
- NodeJS：https://bnpm.bytedance.net/package/@byted-service/kmsv2

### 重要注意事项
1. **推荐用户落盘持久化存储时将密文进行编码而不是直接将[]byte强转为string（推荐使用base64编码）**
2. **DKMS SDK并没有进行base64转码！** DKMS前端为了展示效果，前端加解密自带了base64转码
3. **DKMS client采用单例模式，每个client缓存相互独立，推荐用户全局使用同一个client进行加解密操作**

### 代码示例

#### Golang 示例
```go
package main

import (
    "context"
    "crypto/md5"
    "crypto/sha256"
    // b64 "encoding/base64"
    "fmt"

    "code.byted.org/security/kms-v2-sdk-golang/v2/dkms_client"
)

// **DKMS client 采用单例模式，每个 client 缓存相互独立，**
// **推荐用户全局使用同一个 client 进行加解密操作 。**
// **推荐用户落盘持久化存储时需要将密文进行编码而不是直接将[]byte强转为string（推荐使用base64编码）**

var defaultDkmsClient *dkms_client.DkmsClient

func InitDkmsClient() error {
    // 初始化代码
}
```


#### Java 示例
```java
package org.example;

import org.byted.dkms.DkmsClient;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public class DKMSDemo {
    public static void main(String[] args) {
        try{
            // Note: creating the client like this uses region auto-detection, which is the recommended way of using the SDK
            // 注意：从1.3.1版本起，DkmsClient()能自动判断区域，用户无需传region字符串
            DkmsClient client = new DkmsClient();
            byte[] plaintext = "hello dkms!".getBytes(StandardCharsets.UTF_8);
            byte[] ciphertext = client.Encrypt(dkmsKey, plaintext, null);
            // 更多代码
        }
    }
}
```


#### NodeJS 示例
```javascript
import { DKMSClient } from '@byted-service/kmsv2';
const client = new DKMSClient({})
const validDataKeyName = "dkms.datakey.sdkplayground"
const plaintext = "Hello World! Hello Javascript! Hello DKMS!"
const data = await client.encrypt(validDataKeyName, plaintext);
const decryptData = await client.decrypt(
    validDataKeyName,
    data.toString()
);
console.log(`Decrypted data: ${decryptData}`)
// expect(decryptData).toBe(plaintext);
```


## GORM 接入 DKMS/Encryption SDK

### 依赖项
- [code.byted.org/security/dkms-gorm](https://code.byted.org/security/dkms-gorm) **(请使用v0.2.0及以上版本)**
- https://gorm.io/ gorm
- https://gorm.io/ gen(暂未接入)

### 准备工作
- **计划以 DKMS SDK 形式接入时**：需要事先于 DKMS 前端创建对应区域的数据密钥，参考[DKMS 用户文档](https://bytedance.feishu.cn/wiki/wikcnaxLgRT9didC6EqYNC6Y6Td)，关注**2. DKMS 使用指南** 部分即可
- **计划以 Encryption SDK 形式接入时**：需要事先生成对应密钥的 HeadBytes，参考[KMS Encryption SDK Specification](https://bytedance.feishu.cn/docx/doxcn6iMuM3d0q7S42i9HDILn8d) (与 KMS V2 原生 SDK 加密结果不兼容)

## 相关文档
- [KMS v1 平台文档](https://bytedance.feishu.cn/docs/doccnxizYQpyZumlZOQZRkrIhKf)
- [KMS v1 SDK 文档](https://bytedance.feishu.cn/docs/doccnbIRKmIBUYoBgZ0nocahjBb)
- [KMS 新版本快速上手与最佳实践](https://bytedance.feishu.cn/docs/doccnxEOyPB3P0g6fTYxk51FMPh#NBAUvA)-身份认证

## 技术支持
- 如果有加解密的问题，请提 KMS oncall
- 如果有关于 DKMS-GORM 问题请问 cheowfu.wong@bytedance.com