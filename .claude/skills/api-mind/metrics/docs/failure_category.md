# metrics failure_category 枚举

本文件仅在 execute 阶段出现失败 / error case，需要写入 `case_info_list[].failure_category` 时读取。

| 枚举值 | 含义 |
| --- | --- |
| `""` | 该 case 成功 |
| `tool_issue` | 工具 / CLI / driver 自身缺陷 |
| `business_bug` | 被测服务的业务 bug |
| `user_issue` | 用户配置 / 输入问题，例如 task.md 缺字段、JWT 没拿到 |
| `env_issue` | 环境问题，例如 PPE / BOE 不可用、网络异常 |
| `unknown` | 未能归因 |

归因不确定时优先写 `unknown`，不要发明新枚举。

