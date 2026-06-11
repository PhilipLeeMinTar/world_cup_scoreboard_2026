# 调试指南与常见问题

“我的埋点上报了吗？”、“为什么平台上看不到数据？” 这是前端工程师在接入 TEA 时最常遇到的问题。本篇文档提供了一套系统的调试方法和常见问题排查清单，帮助你快速定位和解决问题。

## 1. 调试与验数指南

在开发环境中进行充分的调试和验证，是保证线上数据质量的关键。核心工具就是你浏览器自带的开发者工具（按 F12 打开）。

### 第一步：开启 SDK 调试模式

在初始化 SDK 时，确保 `log` 配置为 `true`。这会使 SDK 在浏览器的 **Console (控制台)** 面板中打印详细的生命周期日志、事件上报信息和潜在的错误警告。

```javascript
Tea.init({
  app_id: 1234,
  log: true, // 开启调试模式
  // ...
});
```

开启后，当你调用 `Tea.event()` 或其他 API 时，控制台会输出类似以下的信息，这是验证 API 是否被成功调用的第一步。

```
[TEA-SDK] Event tracked: button_click, with params: { from_page: "home" }
```

### 第二步：检查网络请求 (Network)

数据最终是通过网络请求发送到 TEA 服务器的。检查网络请求是验证数据是否**真正发出**的最可靠方式。

1.  打开开发者工具，切换到 **Network (网络)** 面板。
2.  在筛选框中输入 `app_log` 或 SDK 上报接口的部分路径（如 `mcs.zijieapi.com`），以过滤出埋点上报请求。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)
3.  触发你需要验证的埋点事件（例如，点击一个按钮）。
4.  观察 Network 面板是否出现新的网络请求。

如果看到了对应的请求，点击它，查看其详细信息：

*   **Headers (标头)**：检查 `Request URL` 是否正确，`Request Method` 通常是 `POST`。
*   **Payload (载荷)** 或 **Request Body (请求正文)**：这是上报数据的核心。你需要检查：
    *   `header` 部分：`app_id`, `channel`, `user_unique_id` 等初始化和配置的参数是否正确。
    *   `events` 数组：这里包含了本次请求上报的所有事件。展开它，检查：
        *   `event`: 事件名称是否与你代码中调用的 `eventName` 一致。
        *   `params`: 事件属性是否与你传入的 `params` 对象一致，公共属性是否也已正确合并进来。

通过以上步骤，你可以 100% 确认前端的数据是否已按照预期格式正确发送。

### 第三步：使用 WebAppLog-DevTools 插件（推荐）

为了提供更便捷的调试体验，官方提供了一款名为 **WebAppLog-DevTools** 的浏览器插件。它可以可视化地展示 SDK 的状态、配置信息、已上报的事件列表等，极大简化了调试流程。

*   **安装方式**：请在内部工具市场或联系 TEA 技术支持获取该插件的安装方式。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)
*   **使用**：安装后，在开发者工具中会出现一个名为 “AppLog” 的新面板，所有埋点相关信息一目了然。

## 2. 常见问题 (FAQ)

**Q1: 我调用了 `Tea.event()`，但平台上为什么看不到数据？**

**A:** 这是一个最常见的问题，请按以下步骤排查：

1.  **是否调用了 `Tea.start()`？**：`Tea.start()` 是启动上报的“开关”。如果没有调用它，所有事件都会被缓存在本地而不会发送。请确保在初始化和配置后，调用了 `Tea.start()`。
2.  **`app_id` 是否正确？**：检查 `Tea.init()` 中传入的 `app_id` 是否与你在 TEA 平台创建应用时获取的 ID 完全一致。
3.  **网络请求是否成功？**：按照上文的“网络请求检查”方法，确认数据是否已成功发送。如果请求本身就失败了（例如，状态码是 4xx 或 5xx），请检查网络环境或联系 TEA 技术支持。
4.  **是否上报到了测试环境？**：检查 `config` 中是否设置了 `_staging_flag: 1`。这个标志会将数据发送到测试库，而不会进入线上生产环境的数据库。线上验证时请务必移除此配置。[[22]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnumvCkKN6ACLAizeEYTxdj6)
5.  **数据延迟**：在确认前端上报无误后，数据进入 TEA 平台并可供查询通常会有一定的延迟（从几分钟到半小时不等）。请耐心等待一段时间再刷新查看。
6.  **ET 平台配置**：对于某些需要预先在 ET (Event Tracking) 平台定义事件和属性的场景，请确保你上报的事件名和属性名已经在 ET 平台注册并上线。

**Q2: 如何在单页应用 (SPA) 中正确上报 PV (页面浏览) 事件？**

**A:** SPA 需要手动上报 PV。请参考 **[Web 端最佳实践](./tea_web_best_practices.md)** 中的“单页应用 (SPA) 路由处理”章节。

**Q3: 如何给所有事件都带上一些公共参数，比如页面名称、版本号？**

**A:** 使用 `Tea.config()` 方法。具体用法请参考 **[Web 端 API 参考](./tea_web_api_reference.md)** 中关于 `Tea.config()` 的说明。

**Q4: 用户登录后，如何关联登录前后的行为？**

**A:** 在用户成功登录并获取到其唯一业务 ID 后，立即调用 `Tea.config({ user_unique_id: '你的用户ID' })`。SDK 会自动将这个业务 ID 与登录前的匿名设备 ID 进行关联，从而串联起完整的用户行为链路。

**Q5: 为什么 `user_unique_id` 必须是字符串？**

**A:** 这是 TEA 平台对用户标识符的统一规范。即使你的业务用户 ID 是数字类型，也请在传给 SDK 前将其转换为字符串，例如 `Tea.config({ user_unique_id: String(userId) })`，以避免潜在的数据类型问题。

---

### 参考资料

*   [埋点SDK WEB 5.0 版本使用文档](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb)[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)
*   [TEA-SDK 【小程序、QQ轻游戏、快应用】版本接入说明](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f)[[22]](https://bytedance.larkoffice.com/docx/MSKwdkhRpoUePFxwh7qcQMyxn8f?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnumvCkKN6ACLAizeEYTxdj6)
