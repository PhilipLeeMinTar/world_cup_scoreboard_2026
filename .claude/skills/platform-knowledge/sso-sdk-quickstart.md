# SSO SDK 快速入门

本文档提供一个最小可用的 SSO 接入流程，帮助开发者在项目中快速实现登录、登出等核心功能，并提供可复制的 TypeScript/JavaScript 代码示例。

## 一、安装

首先，将 SSO SDK 添加到你的项目依赖中。

```bash
npm install @byted-sdk/account-api --save
```

## 二、初始化

在应用入口文件或统一的 SDK 管理模块中，使用你的应用 `aid` 实例化 `SsoInterfaceSdk`。

```typescript
import { SsoInterfaceSdk } from '@byted-sdk/account-api';

const accountSDK = new SsoInterfaceSdk({
  aid: 1234, // 替换为你的应用 AID
  // host: 'https://test-sso.bytedance.net' // 测试环境请指定 host
});

export default accountSDK;
```

## 三、最小可用流程

以下是实现一个基本登录功能的步骤，包括检查登录状态、发起登录和处理登出。

### 1. 检查登录态 (checkLogin)

在应用加载时，首先应检查用户是否已存在有效的 SSO 登录态。

```typescript
// 在应用根组件或路由守卫中调用
async function checkUserLoginStatus() {
  try {
    const res = await accountSDK.login.checkLogin({ service: 'https://your.app.com/callback' });
    if (res.data?.has_login) {
      console.log('用户已登录', res.data.userInfo);
      // 在此处理业务侧的登录逻辑，例如存储用户信息、换取业务 token
    } else {
      console.log('用户未登录，引导用户进行登录操作。');
    }
  } catch (err) {
    console.error('检查登录态失败', err);
  }
}
```

### 2. 手机验证码与帐密登录

对于未登录用户，可以提供手机验证码或账号密码登录方式。

```typescript
// a. 发送手机验证码
await accountSDK.login.sendMobileCodeV2({ mobile: '13800138000' });

// b. 使用验证码登录
const res_quick = await accountSDK.login.quickAuthV2({
  service: 'https://your.app.com/welcome',
  mobile: '13800138000',
  code: '123456',
});
console.log('手机登录成功', res_quick.data.userInfo);

// c. 或使用帐密登录
const res_account = await accountSDK.login.accountLoginV2({
  service: 'https://your.app.com/welcome',
  account: 'user@example.com',
  password: 'your_password',
});
console.log('帐密登录成功', res_account.data.userInfo);
```

### 3. 登出 (logout)

调用 `logout` 方法可以清除 SSO 的全局登录态，并重定向到指定页面。

```typescript
function handleLogout() {
  // 调用登出接口，将自动清除 SSO 会话 Cookie
  accountSDK.login.logout({
    service: 'https://your.app.com/login', // 登出后重定向到的页面
  });
  // 此处还需处理业务侧的登出逻辑，如清空本地存储、重置状态
}
```

## 四、三方与二维码登录简述

- **三方登录 (`wapLogin`/`authLogin`)**：通过 `wapLogin` 发起跳转至第三方授权页（如飞书）。授权成功后，页面将携带 `code` 重定向回来，此时再调用 `authLogin` 并传入 `code` 即可完成 SSO 登录。

- **二维码登录 (`getQrcode`/`checkQrconnect`)**：
    1. 调用 `getQrcode` 获取二维码内容和唯一 `token`。
    2. 将获取到的内容渲染成二维码。
    3. 客户端轮询 `checkQrconnect` 并传入 `token`，检查扫码状态（`new` -> `scanned` -> `confirmed`），直至成功或超时。

## 五、重要参数解析

- **`service` / `redirect_uri` / `next`**：这三个参数都用于指定操作成功后的**重定向地址**。所有这些地址都必须预先在 SSO 开发者中心配置到**回调白名单**中，且要求**完全匹配**。

- **`state`**：此参数用于在重定向过程中传递客户端上下文。SSO 服务在回调时会原样返回 `state` 的值。强烈建议用它来传递登录前的页面路径或操作意图，以便在登录后恢复用户状态。
  ```typescript
  // 登录前在 /dashboard?tab=analytics
  const state = encodeURIComponent('/dashboard?tab=analytics');
  // 发起登录时带上 state
  accountSDK.login.wapLogin({ ..., state });
  // 回调后解析 state 参数，实现精准跳转
  ```

## 六、极简用法：@byted/easy-sso

对于仅需快速实现SSO登录墙的 React 项目，可使用 `@byted/easy-sso` 简化接入。

```typescript
// 1. 在应用入口调用
import { loginSSO } from '@byted/easy-sso';

// 若未登录，将自动跳转至 SSO 登录页；登录后会自动跳回原页面
loginSSO();

// 2. 在组件中获取用户信息
import { useAtom } from 'jotai';
import { IsLogin, UserInfo } from '@byted/easy-sso';

function UserProfile() {
  const [isLogin] = useAtom(IsLogin);
  const [userInfo] = useAtom(UserInfo);

  if (!isLogin) return <div>未登录</div>;
  return <div>欢迎, {userInfo.name}</div>;
}
```
该库通过 `jotai` 自动管理登录状态，极大简化了流程。
