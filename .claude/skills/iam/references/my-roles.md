# 我的授权（/iam/mine/role/list）

## Action 汇总

| Action | 描述 | 必填 | 可选 |
|---|---|---|---|
| `list_my_roles` | 查询当前用户在指定站点的全部 IAM 授权（= `/iam/mine/role/list` 页面；内部自动翻页抓全量） | - | `vregion`, `username`, `page_size` |

## 示例

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{"action":"list_my_roles","vregion":"cn"}'
gdpa-cli run iam --session-id "$SESSION_ID" --input '{"action":"list_my_roles","vregion":"i18n"}'
gdpa-cli run iam --session-id "$SESSION_ID" --input '{"action":"list_my_roles","vregion":"us-ttp"}'
gdpa-cli run iam --session-id "$SESSION_ID" --input '{"action":"list_my_roles","vregion":"eu-ttp"}'
```

`username` 默认从当前 site 的 JWT 解析，若两个站点登记的用户名不一致可以显式传入：

```bash
gdpa-cli run iam --session-id "$SESSION_ID" --input '{
  "action": "list_my_roles",
  "vregion": "i18n",
  "username": "haolun.xu"
}'
```

## 分页行为

`list_my_roles` 会从第一页开始自动抓取该 site 下的全部授权，返回与页面 `https://cloud.<site>.net/iam/mine/role/list` 底部显示一致的 Total 以及每一行的 Resources / Role / Component / Data sensitivity / Condition / Source 等信息。

`page_size` 仅用于控制内部单次抓取的批大小，CLI 会自动裁剪到上游允许的 `< 1000` 范围内（默认 500，上限 999）。调用方不需要手动翻页。

## 站点全量查询

该 action 本身只查单个 site。若需要「我在所有 site 的授权」，由调用方分别发起四次（`cn` / `i18n` / `us-ttp` / `eu-ttp`）并合并结果。上层 skill `iam-my-roles` 已经封装好这件事。
