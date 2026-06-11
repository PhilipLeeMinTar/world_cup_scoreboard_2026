# 小程序快速上手指南

本指南旨在为字节跳动小程序、微信小程序等平台提供 TEA SDK 的基础接入方法。 

> **[重要] 信息时效性警告：**
> 当前文档基于较早版本的内部资料（`byted-tea-sdk` 3.x 版本及其附属的小程序 SDK）编写。[[21]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcn0JEd7rJJ99zHJwPQaOv5Nd) 资料显示已有更新的 2.0 版本，但相关链接已失效。[[23]](https://bytedance.larkoffice.com/wiki/wikcnw7SBOhd2Lm4Stlde5gExye?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnSNrBEYqLsNjkNXwhCiQxib) 因此，本文档中的 API 和部分实践**可能已经过时**。
> 
> **在正式投入生产前，强烈建议你联系公司内部的 TEA 技术支持团队，以获取最新、最准确的小程序 SDK 文档和资源。**

## 1. 获取与安装 SDK

小程序 SDK 通常不通过 NPM 分发，而是直接提供编译好的 `.js` 文件。

1.  **获取文件**：你需要从 TEA 官方渠道获取名为 `tea-sdk-miniProduct.min.js`（或类似名称）的 SDK 文件。根据历史文档，这可以通过下载旧版 `byted-tea-sdk` 的 npm Tarball 包获得。[[21]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcn0JEd7rJJ99zHJwPQaOv5Nd)
2.  **引入项目**：将获取到的 `.js` 文件复制到你的小程序项目的 `utils` 或类似功能的目录下。

## 2. 接入步骤

以微信/字节跳动小程序为例，主要修改入口文件 `app.js`。

### 步骤一：在 `app.js` 中引入并初始化

在 `app.js` 的顶部，引入 SDK 文件，并立即进行初始化和配置。

```javascript
// 1. 在 app.js 顶部引入 SDK 文件
const $$TEA = require('./utils/tea-sdk-miniProduct.min.js');

// 2. 初始化 SDK，传入你的 App ID
$$TEA.init(1234); // 【必填】替换为你的产品在 TEA 平台申请的 App ID

// 3. 配置 SDK
$$TEA.config({
  log: true, // 建议开发环境下开启，会在控制台打印日志
  _staging_flag: 1, // 值为 1 表示数据上报至测试库，正式上线前务必移除或设为 0
});

// 4. 启动上报队列
// 注意：小程序 SDK 的启动方法名为 send()，而非 Web 端的 start()
$$TEA.send();

App({
  onLaunch: function (options) {
    // 5. 将 SDK 实例挂载到全局 app 对象上，方便在其他页面调用
    this.$$TEA = $$TEA;

    // 示例：上报一个应用启动事件
    this.$$TEA.event('app_launch', {
      scene: options.scene, // 将小程序的启动场景值作为事件属性上报
    });
  },

  // ... 其他生命周期函数
});
```

### 步骤二：在页面中上报事件

完成 `app.js` 的配置后，你可以在任何页面的 `.js` 文件中，通过 `getApp()` 来获取全局实例并上报事件。

```javascript
// 在 pages/index/index.js 中
const app = getApp();

Page({
  onShow: function () {
    // 页面展示时，上报一个页面浏览事件
    app.$$TEA.event('index_page_view');
  },

  handleCardClick: function (e) {
    const cardId = e.currentTarget.dataset.id;

    // 点击卡片时，上报一个点击事件，并附带卡片 ID
    app.$$TEA.event('card_click', {
      card_id: cardId,
      page: 'index',
    });
  },
});
```

## 3. 核心 API 差异说明

根据现有资料，小程序 SDK 的 API 与 Web 端存在一些关键差异：

*   **SDK 对象**：引入后通常命名为 `$$TEA`。[[21]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcn0JEd7rJJ99zHJwPQaOv5Nd)
*   **启动方法**：Web 端使用 `Tea.start()`，而小程序端使用 `$$TEA.send()`。[[22]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnumvCkKN6ACLAizeEYTxdj6)
*   **用户标识**：同样通过 `config` 方法设置 `user_unique_id`。在用户登录后，应及时调用 `$$TEA.config({ user_unique_id: '...' })` 并再次调用 `$$TEA.send()` 使其生效。

    ```javascript
    // 在获取到 openid 或 unionid 后
    app.globalData.$$TEA.config({
      user_unique_id: '用户的 OpenID 或 UnionID'
    });
    app.globalData.$$TEA.send();
    ```

## 4. 调试与域名白名单

*   **调试**：与 Web 端类似，将 `log: true` 传入 `config` 方法，即可在小程序的控制台看到详细的日志输出。
*   **域名白名单**：小程序平台要求所有网络请求的域名必须预先配置在白名单中。请务必将 TEA 的数据上报域名（如 `mcs.zijieapi.com` 等）添加到你的小程序管理后台的 **request 合法域名**列表中，否则所有埋点请求都将失败。

---

### 参考资料

*   [TEA-SDK 【小程序、QQ轻游戏、快应用】版本接入说明](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f)[[21]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcn0JEd7rJJ99zHJwPQaOv5Nd)
*   [TEA-SDK【字节小程序】版本接入文档](https://bytedance.larkoffice.com/wiki/wikcnw7SBOhd2Lm4Stlde5gExye)[[23]](https://bytedance.larkoffice.com/wiki/wikcnw7SBOhd2Lm4Stlde5gExye?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnSNrBEYqLsNjkNXwhCiQxib)
