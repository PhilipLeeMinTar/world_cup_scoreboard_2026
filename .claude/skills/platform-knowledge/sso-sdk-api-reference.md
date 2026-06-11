# SSO SDK API 参考

本文档提供 SSO SDK 核心方法的精简参考，包含一句话说明、核心入参、简短的 TS 示例以及关键注意事项。

## 一、通用返回形态与风控

- **成功响应**：返回的 Promise 会 `resolve` 一个包含 `data` 的对象，其中 `data.error_code` 为 `0`。
- **失败响应**：Promise 会 `reject` 一个包含错误码 `error_code` 和描述 `description` 的对象。
- **风控提示**：当接口触发风控时，会 `reject` 特定错误。此时需根据返回的 `data` 调起验证中心 SDK 提供的验证流程，完成后再重试原操作。

## 二、Login 模块

### checkLogin
检查当前是否存在有效的 SSO 登录态。
- **核心入参**: `service` (string, 登录成功后的回调地址)
- **示例**:
  ```typescript
  accountSDK.login.checkLogin({ service: 'https://your.app.com/' })
    .then(res => {
      if (res.data.has_login) console.log('已登录', res.data.userInfo);
    });
  ```

### sendMobileCodeV2
发送手机短信验证码。
- **核心入参**: `mobile` (string), `extra_params` (object)
- **示例**:
  ```typescript
  // 请求发送6位验证码
  accountSDK.login.sendMobileCodeV2({
    mobile: '13800138000',
    extra_params: { is6Digits: 1 }
  });
  ```

### quickAuthV2
使用手机和验证码进行登录或注册。
- **核心入参**: `service` (string), `mobile` (string), `code` (string)
- **示例**:
  ```typescript
  accountSDK.login.quickAuthV2({
    service: 'https://your.app.com/welcome',
    mobile: '13800138000',
    code: '123456',
  });
  ```

### accountLoginV2
使用账号（手机/邮箱）和密码登录。
- **核心入参**: `service` (string), `account` (string), `password` (string)
- **示例**:
  ```typescript
  // 登录成功后，SSO 登录态默认有效期 60 天
  accountSDK.login.accountLoginV2({
    service: 'https://your.app.com/',
    account: 'user@example.com',
    password: 'your_password',
  });
  ```

### logout
清除 SSO 登录态并登出。
- **核心入参**: `service` (string, 登出后的重定向地址)
- **示例**:
  ```typescript
  accountSDK.login.logout({ service: 'https://your.app.com/login' });
  ```

### wapLogin
发起三方授权登录，跳转至三方授权页。
- **核心入参**: `platform_app_id` (number), `next` (string, 授权成功回调地址)
- **示例**:
  ```typescript
  accountSDK.login.wapLogin({
    platform_app_id: 1479, // 以飞书为例
    next: 'https://your.app.com/auth/callback',
    type: 'sso'
  });
  ```

### authLogin
使用三方授权成功后返回的 `code` 或 `token` 完成 SSO 登录。
- **核心入参**: `service` (string), `token` (string), `platform_app_id` (number)
- **示例**:
  ```typescript
  accountSDK.login.authLogin({
      service: 'https://your.app.com/',
      token: 'third_party_auth_code_or_token',
      platform_app_id: 1479
  });
  ```

## 三、Register 模块

### emailRegister
使用邮箱和验证码进行注册。
- **核心入参**: `email` (string), `code` (string), `password` (string), `next` (string)
- **示例**:
  ```typescript
  accountSDK.register.emailRegister({
    email: 'newuser@example.com',
    code: 'email_code_from_server',
    password: 'new_password',
    next: 'https://your.app.com/register/success'
  });
  ```

## 四、Password 模块

### resetPassword
通过验证码（手机/邮箱）重置密码。
- **核心入参**: `account` (string), `code` (string), `password` (string)
- **示例**:
  ```typescript
  accountSDK.password.resetPassword({
    account: 'user@example.com', // 手机号或邮箱
    code: 'verification_code',
    password: 'new_strong_password'
  });
  ```

## 五、qrcodeLogin 模块

### getQrcode
获取用于扫码登录的二维码内容及 `token`。
- **核心入参**: `service` (string)
- **示例**:
  ```typescript
  const { data } = await accountSDK.qrcodeLogin.getQrcode({ service: 'https://your.app.com/' });
  const { token, qrcode } = data; // 使用 qrcode 内容生成二维码
  // 接下来轮询 checkQrconnect
  ```

### checkQrconnect
轮询此接口检查二维码的扫描状态。
- **核心入参**: `token` (string)
- **示例**:
  ```typescript
  const intervalId = setInterval(async () => {
    const { data } = await accountSDK.qrcodeLogin.checkQrconnect({ token });
    // data.status: 'new' -> 'scanned' -> 'confirmed'
    if (data.status === 'confirmed') {
      clearInterval(intervalId);
      // 登录成功, data 中会包含重定向 URL 或用户信息
      window.location.href = data.redirect_url;
    }
  }, 2000);
  ```
