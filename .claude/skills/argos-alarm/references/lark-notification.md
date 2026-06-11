# Lark 群 / LarkBot 通知配置

Argos-Alarm 原生支持飞书卡片、@ 用户、加急 + 电话/短信升级。`argos-alarm`
skill **不需要改代码** —— 把下面这些字段填进 `create_rule` / `update_rule`
的 `rule` body 即可透传到 Argos。

## 默认回退行为（不配 Lark 群也不会丢告警）

Argos-Alarm 规则在 `lark_ids=""`、`receiver_mode=override`、
`follow_empty_receivers=false` 时，告警会自动回退到**服务树 owner + 值班**，
通过他们绑定的飞书身份推卡片。所以"不显式配飞书群"并不意味着"告警发不出"
—— 只是走 owner 默认订阅链路。

| `receiver_mode` | `lark_ids` | `follow_empty_receivers` | 实际接收人 | 适用场景 |
|---|---|---|---|---|
| `bytetree_node_setting` | — | — | 服务树 owner + oncall | 默认够用，最省事 |
| `override` | 空 | `false` | 回退到服务树 owner | 同上（多数线上规则为此态） |
| `override` | 有值 | `false` | 指定的飞书群（覆盖 owner） | **告警进群而非 owner 个人** |
| `append` | 有值 | `false` | 服务树 owner + 指定群 | owner 也收、群也收 |
| `override` | 空 | `true` | **不发送** | 静默规则 |

## 规则 body 上相关字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `lark_ids` | `string` | 一个或多个飞书群 ID 逗号分隔。官方虽标 Deprecated，SG 线上规则仍在用 |
| `webhooks` | `[]string` | 已在 Argos 注册的 webhook 名称，≤3 个 |
| `webhook_configs` | `[]{key_name,type,params}` | 绑定多个 webhook，常见 `type=internal_bound_analysis`（官方自带如 `Argos-Auto-RCA`）或自定义 |
| `receiver_mode` | `string` | `override` / `append` / `bytetree_node_setting` |
| `follow_empty_receivers` | `bool` | 默认 `false`，设 `true` 才会空接收人时真正静默 |

## 通知渠道枚举（channel，用在订阅人/升级配置里）

- 单项：`Lark` | `LarkUrgent`（加急）| `LarkAtUser`（@ 用户）| `Phone` | `SMS`
- Lark 组合：`Lark_LarkUrgent` | `Lark_LarkAtUser` | `Lark_LarkUrgent_LarkAtUser`
- 含电话/短信升级：`Phone_Lark_LarkUrgent` | `Phone_SMS_Lark_LarkUrgent_LarkAtUser` …

> 枚举顺序固定：**Phone, SMS, Lark, LarkUrgent, LarkAtUser**。除了单独的
> `Lark`，其它单项不要单独使用 —— 必须和 `Lark` 组合。

## Receiver type 枚举

`tree_node_owner` / `rule_owner` / `tree_node_oncall` / `rule_lark_group` /
`node_oncall_lark_group` / `node_oncall_phone_lark_group` / `upgrade_to_owner` /
`upgrade_to_oncall`

## LarkBot 两种接入路径

1. **飞书应用机器人绑群（推荐）**：ByteCloud 后台创建应用机器人 → 加到目标
   飞书群 → 规则填群 ID 到 `lark_ids`。卡片由 Argos 原生渲染，无坑。
2. **飞书自定义机器人 webhook**：飞书群加自定义机器人拿 webhook URL → 填
   `webhooks` / `webhook_configs`。⚠️ Argos 发的是特定卡片协议，自定义
   webhook 收到的原始 payload 无法渲染，**需要自建中转服务**把 Argos 回调
   payload 翻译成飞书卡片 JSON。参考回调结构体 V2（doc_id
   `658a4c83eb2dd902ee1a0d6e`）。

## 示例 1：告警直接发到飞书群（最常用）

```bash
gdpa-cli run argos-alarm --session-id "$SESSION_ID" --input '{
  "action":"create_rule",
  "vregion":"sg",
  "rule":{
    "name":"my-cpu-high",
    "attach_model":{"psm":"ies.gdp.open_api","vregion":"Singapore-Central","cluster":"default"},
    "check_vregions":["Singapore-Central"],
    "level":"warning",
    "status":"normal",
    "executor":"balarm",
    "rule":"$q = sum(q(\"sum:rate:...\",\"3m\",\"1m\"))\nwarn = $q>0.8\nrunEvery=2",
    "receiver_mode":"override",
    "lark_ids":"<飞书群 ID1>,<飞书群 ID2>",
    "check_interval":2
  }
}'
```

## 示例 2：群 + 电话/加急升级

```bash
gdpa-cli run argos-alarm --session-id "$SESSION_ID" --input '{
  "action":"create_rule",
  "vregion":"sg",
  "rule":{
    "name":"my-latency-critical",
    "attach_model":{"psm":"ies.gdp.open_api","vregion":"Singapore-Central","cluster":"default"},
    "check_vregions":["Singapore-Central"],
    "level":"critical",
    "status":"normal",
    "executor":"balarm",
    "rule":"<bosun 表达式>",
    "receiver_mode":"append",
    "lark_ids":"<飞书群 ID>",
    "send_policy":{
      "mode":"classic",
      "original_alert_count":2,
      "send_interval_min":3,
      "send_traditional_notification":true
    },
    "upgrade_setting":{
      "window_settings":[
        {"interval_count":5,"count":3,"upgrade_level":1},
        {"interval_count":10,"count":8,"upgrade_level":2},
        {"interval_count":20,"count":18,"upgrade_level":3}
      ]
    }
  }
}'
```

> 升级效果取决于各 level 绑定的通道（在告警平台 UI 配置）：L1 默认
> `Lark_LarkUrgent`，L2 加 `Phone`，L3 加电话 + SMS。枚举映射见上面
> "通知渠道枚举"。

## 示例 3：绑自定义 Webhook（带中转服务）

```bash
gdpa-cli run argos-alarm --session-id "$SESSION_ID" --input '{
  "action":"create_rule",
  "vregion":"sg",
  "rule":{
    "name":"my-webhook-rule",
    "attach_model":{"psm":"ies.gdp.open_api","vregion":"Singapore-Central","cluster":"default"},
    "check_vregions":["Singapore-Central"],
    "level":"warning",
    "status":"normal",
    "executor":"balarm",
    "rule":"<bosun 表达式>",
    "receiver_mode":"append",
    "webhook_configs":[
      {"key_name":"Argos-Auto-RCA","type":"internal_bound_analysis","params":[]},
      {"key_name":"<你在 Argos 注册的 webhook 名>","type":"custom_webhook","params":[]}
    ]
  }
}'
```

> ⚠️ 自定义 webhook 目标必须是**你自建的中转服务**，接收 Argos 回调 payload
> 后翻译成飞书卡片 JSON 再转发到飞书群机器人 URL。直接把飞书自定义机器人
> webhook URL 注册成 `custom_webhook` 会成功发送但飞书群内无法渲染（已知坑，
> doc_id `66a6fc8276a54702fb91e63e`）。
