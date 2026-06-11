# meego-manage · 工作流操作详解

`query_workflow` / `update_node` / `operate_node` / `state_change` 四个 action 的完整使用文档。先读 `SKILL.md` 拿全局参数表与本地配置约定。

四个动作覆盖 Meego 工作流的常见运维场景。**入口顺序固定：先用 `query_workflow` 拿到目标节点的 `node_id`（或状态流的 `transition_id`），再调用其余动作。**

## 公共入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `project_key` | string | 是（可省，自动读取 `./.gdpa/meego.yaml`） | 空间 ID 或 simple_name |
| `work_item_type_key` | string | 是 | 工作项类型（如 `task` / `story` / `issue`） |
| `work_item_id` | int64 | 是 | 工作项实例 ID |

## action=query_workflow（获取工作流详情）

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `flow_type` | int64 | `0` | `0`=节点流（task/story 等），`1`=状态流（issue/缺陷/版本等，必传） |
| `fields` | []string | — | 字段筛选；指定模式 `["name","priority"]` 或排除模式 `["-priority"]`（不可混用） |

返回结构精简后包含：
- `workflow_nodes`：节点流模式下的节点列表（`id` / `state_key` / `name` / `status` / `owners` / `node_schedule` / `schedules` / `role_assignee`）
- `stateflow_nodes`：状态流模式下的状态列表
- `connections`：上下游连接（含 `transition_id`，状态流必读）

```bash
# 节点流：拿当前在哪个 node + 节点级排期/负责人
gdpa-cli run meego-manage --input '{
  "action": "query_workflow",
  "work_item_type_key": "task",
  "work_item_id": 6921539228,
  "flow_type": 0
}'

# 状态流：拿 transition_id 列表，喂给 state_change
gdpa-cli run meego-manage --input '{
  "action": "query_workflow",
  "work_item_type_key": "issue",
  "work_item_id": 12694xxx,
  "flow_type": 1
}'
```

## action=update_node（更新节点 / 排期 / 表单 / 角色）

仅适用于**节点流**。Path 上的 `node_id` 来自 `query_workflow` 返回的 `workflow_nodes[i].id`（也可用 `state_key`）。

| 参数 | 类型 | 说明 |
|---|---|---|
| `node_id` | string | **必填**，目标节点 ID 或 state_key |
| `node_owners` | []string | 用户 user_key 数组；不传=不更新；空数组=清空所有人 |
| `node_schedule` | object | 单一排期；字段：`estimate_start_date` / `estimate_end_date` / `points` / `owners` |
| `schedules` | []object | 按人差异化排期；同 `node_schedule` 字段。开启差异化排期需要节点负责人 ≥ 2 人 |
| `fields` / `update_fields` / `field_value_pairs` | []object | 节点表单字段，`{"field_key":"...","field_value":...}` |
| `role_assignee` | []object | 角色负责人，`[{"role":"DA","owners":["user_key"]}]` |

`estimate_start_date` / `estimate_end_date` 接受多种格式（统一按本机时区解析）：
- 数字毫秒级时间戳（≥ 1e12）或秒级（10 位）
- `"YYYY-MM-DD"` / `"YYYY/MM/DD"` / `"YYYY.MM.DD"` / `"YYYYMMDD"`
- `"M-D"` / `"M.D"` —— 自动补当前年份（适合写 `4.20`、`4.21` 这种简写）

> 系统会把 `estimate_start_date` 拉到当天 00:00:00.000，把 `estimate_end_date` 拉到当天 23:59:59.999，与 Meego Open API 约定一致。

```bash
# 把节点 doing 的排期改成 4.20~4.21、共 2 人天
gdpa-cli run meego-manage --input '{
  "action": "update_node",
  "work_item_type_key": "task",
  "work_item_id": 6921539228,
  "node_id": "doing",
  "node_schedule": {
    "estimate_start_date": "4-20",
    "estimate_end_date": "4-21",
    "points": 2
  }
}'
```

## action=operate_node（完成 / 回滚节点）

仅适用于**节点流**。

| 参数 | 类型 | 说明 |
|---|---|---|
| `node_id` | string | **必填**，目标节点 ID 或 state_key |
| `node_action` | string | **必填**，`confirm`=完成，`rollback`=回滚 |
| `rollback_reason` | string | `node_action=rollback` 时必填 |
| `node_owners` / `node_schedule` / `schedules` / `fields` / `role_assignee` | 同 `update_node`，可在流转的同时一并更新 |

```bash
# 推进当前节点 doing 完成
gdpa-cli run meego-manage --input '{
  "action": "operate_node",
  "work_item_type_key": "task",
  "work_item_id": 6921539228,
  "node_id": "doing",
  "node_action": "confirm"
}'

# 回滚节点并附带原因
gdpa-cli run meego-manage --input '{
  "action": "operate_node",
  "work_item_type_key": "task",
  "work_item_id": 6921539228,
  "node_id": "review",
  "node_action": "rollback",
  "rollback_reason": "评审未通过，回滚到 review"
}'
```

## action=state_change（状态流流转）

仅适用于**状态流**工作项（如 issue / 缺陷 / 版本）。

| 参数 | 类型 | 说明 |
|---|---|---|
| `transition_id` | int64 | **必填**，从 `query_workflow`（`flow_type=1`）的 `connections[i].transition_id` 拿 |
| `fields` | []object | 状态表单字段（仅状态表单内的字段才能改） |
| `role_owners` | []object | 角色负责人，`[{"role":"PM","owners":["user_key"]}]` |

```bash
gdpa-cli run meego-manage --input '{
  "action": "state_change",
  "work_item_type_key": "issue",
  "work_item_id": 12694xxx,
  "transition_id": 12345,
  "fields": [
    {"field_key": "field_658c22", "field_value": "23333", "field_type_key": "text", "field_alias": "sentry_link"}
  ]
}'
```

## 推进任务到完成的标准编排

例：「推进任务 6921539228 完成，并把当前节点排期改为 4.20~4.21 共 2 人力」：

1. `action=query_workflow`（`flow_type=0`） → 找到 `status=2`（进行中）的节点 `id`
2. `action=update_node`（带 `node_schedule`） → 更新该节点排期
3. `action=operate_node`（`node_action=confirm`） → 完成该节点

> 也可以在 step 3 的 `operate_node` 里直接带 `node_schedule`，一次请求同时更新排期并流转节点。

## operate_node 报「Should Be Passed / signal field required」时的处理

部分研发流模板（如 ttarch story）在 `operate_node confirm` 时会校验配套的 **`signal` 类型字段**（如「服务端开发完成 field_7f7819」「服务端上线完成 field_cac015」），这些字段由 CI / QA / 上线系统自动回写，**不能通过 OpenAPI 直接由用户写入**（试图 update 会得到 `field [...] is illegal`）。

此时改走 Meego 内置的「**手动完成XXX节点**」`bool` 开关：在 `action=fields` 里搜「手动完成」就能拿到对应 `field_key`，常见的有：

| 节点用途 | 字段名 | field_key（ttarch story 模板示例） |
|---|---|---|
| Server 开发节点 | 手动完成Server开发节点 | `field_41ae90` |
| Server 测试节点 | 手动完成Server测试节点 | `field_5ca858` |
| Server 上线节点 | 手动完成Server上线节点 | `field_2553bc` |
| FE/iOS/Android 同理 | 手动完成XX节点 | 在 `fields` 接口中检索 |
| 结束节点 | 手动完成结束节点 | `field_23c3d2` |

> ⚠️ `field_key` 在不同模板下可能不同，必须先 `action=fields` 查询确认；不要硬编码本表里的 key。

操作模式：

```bash
# 1) 先把对应的「手动完成」开关置 true（用 update，而不是 operate_node.fields）
gdpa-cli run meego-manage --input '{
  "action": "update",
  "work_item_type_key": "story",
  "work_item_id": 7190185011,
  "fields": [
    {"field_key": "field_41ae90", "field_value": true}
  ],
  "confirm_update": true
}'

# 2) 设置成功后，对应节点会被 Meego 自动推进到「已完成」，下游节点自动激活；
#    再次 query_workflow 确认状态即可，无需再调 operate_node confirm
```

适用场景：跑通 demo / 联调验证 / 推进卡在外部 signal 上的研发流任务。**生产上线前的真实需求不要用这个 bypass**，应让 CI/QA 信号正常流转。
