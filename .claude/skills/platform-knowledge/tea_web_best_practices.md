# Web 端埋点最佳实践

遵循一套统一的最佳实践，不仅能保证数据质量，还能极大提升团队协作效率和数据分析的有效性。本篇文档汇集了 TEA Web 端埋点的命名规范、属性设计、性能建议及常见场景处理策略。

## 1. 命名规范

清晰、一致的命名是数据治理的基石。

### 事件命名 (Event Name)

*   **格式**：统一使用**小写字母**、**数字**和**下划线 `_`** 的组合。
*   **结构**：推荐采用 `对象_动作` 或 `场景_对象_动作` 的结构，使其具有自解释性。
    *   `对象`：事件发生的主体，如 `button`, `page`, `form`。
    *   `动作`：用户的行为，如 `click`, `view`, `submit`, `expose`。
*   **示例**：
    *   **推荐**：`login_button_click`, `article_detail_page_view`, `search_form_submit`。
    *   **不推荐**：`LoginButtonClick` (大小写混用), `click-button` (使用连字符), `事件1` (使用中文)。

### 属性命名 (Property Name)

*   **格式**：与事件命名规则相同，统一使用小写蛇形命名法（`snake_case`）。
*   **通用性**：尽量使用通俗易懂、业界共识的词汇。例如，使用 `duration` 而不是 `time_len` 表示时长。
*   **一致性**：在不同事件中，表达相同含义的属性必须使用完全相同的名称。例如，商品 ID 在 `add_to_cart` 事件和 `purchase_success` 事件中都应命名为 `item_id`，而不是一个用 `item_id` 另一个用 `product_id`。

## 2. 属性设计

### 公共属性 (Common Properties)

充分利用公共属性，可以有效减少重复代码，并为所有事件自动添加必要的上下文信息。

*   **会话级公共属性**：对于在用户整个访问期间基本不变的属性，如 `project_name`, `user_level`, `app_version`，应通过 `Tea.config()` 在顶层设置。

    ```javascript
    Tea.config({
      app_version: '2.5.1', // 应用版本
      user_role: 'admin' // 用户角色
    });
    ```

*   **事件级公共属性**：对于和事件紧密相关，但多个事件都会用到的属性，如当前页面 `page`、当前模块 `module`，可以通过 `Tea.config({ evtParams: { ... } })` 设置。

    ```javascript
    Tea.config({
      evtParams: {
        page: 'user_profile',
        module: 'avatar_setting'
      }
    });
    ```

### 事件属性 (Event-specific Properties)

*   **必要性**：为每个事件精心设计其特有的属性，以提供最丰富的分析维度。例如，`video_play` 事件应包含 `video_id`, `video_duration`, `play_progress` 等属性。
*   **数据类型**：确保属性值的数据类型正确且一致。需要计算的指标（如价格、数量）应使用 `Number` 类型，分类标签（如名称、类型）应使用 `String` 类型。

## 3. 性能与上报策略

*   **页面离开时的上报**：对于需要在用户关闭页面或跳转前上报的事件（如统计页面停留时长），请务必使用 `Tea.beaconEvent()`。这个 API 利用浏览器的 `sendBeacon` 机制，能显著提高数据发送的成功率。直接使用 `Tea.event()` 可能会因为页面即将卸载、网络请求被中断而导致数据丢失。[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)

*   **高频事件的节流**：避免对高频触发的事件（如 `mouse_move`, `scroll`）进行无节制的上报，这会产生大量冗余数据并可能影响页面性能。如果确实需要采集此类行为，应采用节流（Throttle）或防抖（Debounce）策略，在一定时间间隔内合并上报。

*   **批量上报**：SDK 内部已实现了批量上报机制，会在短时间内将多个事件合并到一个网络请求中发送，你无需手动处理。这是默认行为，旨在优化性能。

## 4. 场景处理最佳实践

### 单页应用 (SPA) 路由处理

*   **问题**：在 React、Vue、Angular 等构建的单页应用中，路由切换不会触发页面刷新，导致 SDK 无法自动上报页面浏览（PV）事件。
*   **解决方案**：
    1.  在初始化 SDK 时，设置 `disable_auto_pv: true` 来禁用默认的 PV 上报行为。
    2.  在应用的路由监听器（如 Vue Router 的 `afterEach`，React Router 的 `useEffect` 依赖 `location`）中，手动调用 `Tea.predefinePageView()`。

    ```javascript
    // 示例：Vue Router
    router.afterEach((to, from) => {
      Tea.predefinePageView();
    });
    ```

### 跨域与 Cookie

*   **问题**：当主站和子站部署在不同的子域名下（如 `main.example.com` 和 `sub.example.com`），默认情况下 `web_id` 等存储在 Cookie 中的身份标识无法共享，可能导致同一用户在不同子域名下被识别为不同用户。
*   **解决方案**：在初始化 SDK 时，可以配置 `domain` 字段来设置 Cookie 的主域。

    ```javascript
    Tea.init({
      app_id: 1234,
      // ...其他配置
      domain: '.example.com' // 设置为主域
    });
    ```
    *注意：此功能可能依赖特定 SDK 版本，请查阅最新的 `init` API 文档确认字段名。*

## 5. 隐私合规提示

*   **禁止采集敏感信息**：严禁通过埋点采集任何可直接识别个人身份的敏感信息，除非已获得用户的明确授权。例如，不要上报用户的完整姓名、身份证号、手机号、精确家庭住址等。
*   **用户 ID 处理**：上报 `user_unique_id` 时，应使用业务内部经过脱敏或抽象的用户标识，而不是原始的敏感账号信息。
*   **遵守数据规范**：遵循公司和国家/地区关于数据隐私和安全的法规政策，确保数据采集、传输和使用的全过程合规。

---

### 参考资料

*   [埋点SDK WEB 5.0 版本使用文档](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb)[[13]](https://bytedance.larkoffice.com/wiki/wikcnKdSt5GhwkiR99p65Rkc5nb?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnn2dN0OmT3JGFhUj59Jkvih)
*   [WEB SDK 使用说明（V4）](https://bytedance.larkoffice.com/wiki/wikcnUGmq3tK9Snq3xCVWqovfQg)[[12]](https://bytedance.larkoffice.com/wiki/wikcnUGmq3tK9Snq3xCVWqovfQg?from=lark_search_qa&ccm_open_type=lark_search_qa#doxcnPR0CGl4AgbSsahRrXF3eMh)
