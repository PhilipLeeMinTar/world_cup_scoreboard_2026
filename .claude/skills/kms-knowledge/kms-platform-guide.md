# KMS 平台操作指南

## 平台概述

KMS（密钥管理系统）平台是字节跳动内部的密钥管理服务，提供**主密钥加解密迁移敏感信息托管**能力。平台支持对落盘的敏感数据（如手机号、身份证、金额等）进行加解密操作。

## 平台地址

KMS 平台地址：https://security.bytedance.net/safety-ability/data/key-management/services-list

**各区域使用说明**：
- 可以在平台右上方切换 KMS 节点
- 不同区域（如 BOE）的使用说明请参考：[KMS 各区域使用说明](https://bytedance.feishu.cn/space/doc/doccnOqmjnDHEBHrn4UAH743bBb#)

## 核心功能模块

### 1. 服务注册与管理

**新建服务**：
1. 登录 KMS 平台，点击左侧的**服务列表**
2. 在服务列表页面顶部，单击**新建服务**
3. 填写服务相关信息完成注册

### 2. 敏感配置托管

**创建敏感配置**：
1. 在服务列表中找到目标服务
2. 点击操作中的**敏感配置托管**，进入敏感配置托管界面
3. 创建敏感配置，主要填写配置名称与配置内容

**敏感配置迁移**：
- 旧服务使用主密钥解密敏感配置，新服务使用敏感配置托管
- 迁移过程：旧服务继续使用主密钥解密，新服务创建敏感配置并共享给其他服务

### 3. 数据密钥管理

**创建数据密钥**：
1. 在服务列表中找到目标服务
2. 点击操作中的**绑定数据密钥**
3. 点击**新建密钥**创建新的数据密钥

**密钥共享**：
1. 选中需要共享的密钥
2. 点击**共享密钥**
3. 选择共享类型（如公共平台解密权限）并设置权限

### 4. 权限管理

**权限申请方式**：

**方式一：使用者主动申请**
- 登录 KMS 平台，点击**权限工单**-**申请权限**-**申请公共平台查询权限**

**方式二：联系数据加密方/提供方添加权限**
- 加密方登录 KMS 平台，点击**服务列表**-找到该服务后点击**服务数据密钥**
- 选择密钥后点击**共享密钥**-共享类型选择**公共平台解密权限**

## 最佳实践

### 1. 在 QueryEditor 和 Dorado 解密加密数据

**SQL 解密函数**：
```sql
-- 推荐使用
SELECT KMSDecryptExt(待解密列，加密时候的PSM) FROM XXX;

-- 解密失败时返回原文
SELECT kms_try_decrypt(待解密列，加密时候的PSM) FROM XXX;
```

**执行注意事项**：
- 如果 SQL 语句执行失败，尝试在 SQL 语句前添加：
  ```sql
  set tqs.query.engine.type=hive;
  -- 或者
  set tqs.query.engine.type=sparkCli;
  ```

### 2. 敏感信息分享

**旧版平台分享流程**：
1. 登录 KMS 平台 https://kms.bytedance.net/
2. 在平台顶部点击**敏感信息分享**操作
3. 填写敏感信息及分享给的用户后，点击分享

**查看分享记录**：
- 点击**敏感信息分享历史**查看分享详情
- 支持查看、删除、修改授权、复制查看链接等操作

## 平台操作截图

![权限申请界面](QyrpbmaIqoyh3bxXdNIckX3snIf)
![密钥共享界面](TeZ7bkKfoo1ARcxrK8lc5GtZn0b)

## 相关文档链接

- [KMS 新版本平台文档](https://bytedance.feishu.cn/space/doc/doccnxizYQpyZumlZOQZRkrIhKf#ObHqLl)
- [KMS 各区域使用说明](https://bytedance.feishu.cn/space/doc/doccnOqmjnDHEBHrn4UAH743bBb#)
- [KMS 新版本 SDK 文档](https://bytedance.feishu.cn/space/doc/doccnbIRKmIBUYoBgZ0nocahjBb)