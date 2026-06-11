# 用户组 & 用户管理

覆盖 IAM 自定义用户组（`/iam/group/list` 页面）与用户目录查询相关 action。

## Action 汇总

| Action | 描述 | 必填 | 可选 |
|---|---|---|---|
| `list_groups` | 分页查询我的用户组 | - | `vregion`, `page`, `page_size`, `search` |
| `list_all_groups` | 分页查询全量用户组 | - | `vregion`, `page`, `page_size`, `search` |
| `create_group` | 创建用户组 | `name` | `vregion`, `description`, `description_en` |
| `get_group_summary` | 查询用户组摘要 | `custom_group_id` | `vregion` |
| `list_group_members` | 查询用户组成员 | `custom_group_id` | `vregion`, `page`, `page_size` |
| `add_members` | 添加普通成员 | `custom_group_id`, `usernames` | `vregion`, `page_size` |
| `add_admins` | 添加管理员 | `custom_group_id`, `usernames` | `vregion`, `page_size` |
| `remove_members` | 移除普通成员 | `custom_group_id`, `usernames` | `vregion`, `page_size` |
| `remove_admins` | 移除管理员 | `custom_group_id`, `usernames` | `vregion`, `page_size` |
| `search_users` | 模糊搜索用户 | `query` | `vregion`, `page` |
| `get_users_by_usernames` | 按用户名精确查询用户 | `usernames` | `vregion` |

## 示例

### 创建用户组

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "create_group",
  "vregion": "cn",
  "name": "gdpa_skill_dev",
  "description": "gdpa skill dev",
  "description_en": "gdpa skill dev"
}'
```

### 给用户组添加普通成员 / 管理员

```bash
# 普通成员
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "add_members",
  "vregion": "cn",
  "custom_group_id": "cn_xxxxx",
  "usernames": ["alice", "bob"]
}'

# 管理员
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "add_admins",
  "vregion": "eu-ttp",
  "custom_group_id": "euttp_xxxxx",
  "usernames": ["alice"]
}'
```

### 移除成员

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "remove_members",
  "vregion": "cn",
  "custom_group_id": "cn_xxxxx",
  "usernames": ["alice"]
}'
```

### 查用户组摘要 & 成员

```bash
# 摘要
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "get_group_summary",
  "vregion": "us-ttp",
  "custom_group_id": "tx_hyx0l5b1d6"
}'

# 成员列表
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "list_group_members",
  "vregion": "us-ttp",
  "custom_group_id": "tx_hyx0l5b1d6",
  "page_size": 50
}'
```

### 搜索 / 精确查询用户

```bash
# 模糊搜索
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "search_users",
  "vregion": "us-ttp",
  "query": "laihongquan"
}'

# 按用户名精确查询（支持数组或逗号分隔字符串）
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "get_users_by_usernames",
  "vregion": "i18n",
  "usernames": ["laihongquan", "chenglinfeng"]
}'
```

## 约定

1. `usernames` 支持 JSON 字符串数组，也支持逗号分隔字符串（`"alice,bob"`）。
2. `vregion` 取值见入口 SKILL.md 的「共享约定」。
3. `custom_group_id` 通常带区域前缀（`cn_xxx` / `tx_xxx` / `i18n_xxx` / `euttp_xxx`）。
