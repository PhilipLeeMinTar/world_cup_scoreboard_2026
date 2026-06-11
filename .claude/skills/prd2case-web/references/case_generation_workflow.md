# Web E2E Case Generation Workflow

本文件只负责一件事：把 Stage-2（代码分析 + 数据研究回填）后的 `test_analysis.md` 全量转成 `case.md`。可执行性不是进入 `case.md` 的门槛；`case.md` 必须同时包含已 URL 化的可执行 Web case 和未完成 / 待人工补全 case。代码分析、数据研究、造数、Bits/TTAT 同步不在这里展开。

## 输入门禁

开始生成前先检查：

- 输入必须是已按 TDRS 处理并完成可执行性分类的 `test_analysis.md`：测试分析 → 每个验证点的前置条件数据要求 → 代码分析 + 真实 API 调用查找 / 构造测试数据 → 对可执行行回填真实 URL 与样本 ID，对不可执行行标明 `BLOCKED` / `manual-prep` / `skip` / `UNVERIFIED` 及原因。存在未分类行时停止生成；存在不可执行行时不得停止生成，也不得把这些行从 `case.md` 覆盖范围中移除。
- 输入必须已经通过 Stage-2 门禁：`python3 $WEBE2E_SKILL/scripts/tdrs_gate.py <test_analysis.md>`。该 gate 只要求每个 `分析ID` 有有限预算内的终态裁决和证据，不要求全部 `CLOSED`；未通过时不得生成 `case.md`。
- 输入必须已经完成 Stage-1 的上下文全量验证点审查：`spec.md` / PRD、ERD、代码变更、业务知识、历史用例等上下文中的功能模块、关键分支、异常 / 边界场景都已映射到 `test_analysis.md` 行。若在本阶段才发现遗漏验证点，必须回到 Stage-1 补 `test_analysis.md`，再重新走 Stage-2 TDRS；不得在 `case.md` 生成阶段绕过数据研究临时新增可执行 case。
- 输入的 `test_analysis.md` 每个有效验证点行必须有稳定 `分析ID`。生成 `case.md` 时每条 case 必须写 `**[analysis-id]** <对应分析ID>`；一条 case 只能对应一个 `分析ID`，不得把多个独立验证点合并成一条 case。
- 每个可执行场景都有真实查询 / 已确认创建得到的直连 URL、目标数据引用、step 1 初始状态、可观察断言锚点；不得是"case 执行时再创建"或"临时 fixture 兜底"。缺少这些闭环信息的场景仍然必须生成未完成 / 待人工补全 case。
- 每个可执行场景的直连 URL 都必须有 route provenance：已在 Stage-2 查过目标 app 的 router / basename（或现有页面入口配置），并记录最终业务路径如何由 `host + basename + route + query/hash` 组成。没有 route provenance 的 URL 视为未完成，不能进入可执行 case。
- 每个可执行 URL 都必须有初始化参数策略：Stage-2 已区分稳定业务上下文参数与动态初始化参数。稳定参数（如租户、owner、目标 id、筛选枚举）决定样本定位时应保留在 `访问:` URL；动态参数（如相对当前时间的 `startTime` / `endTime`）不得盲目固化过期值，必须在 Stage-2 说明由执行脚本动态补齐，或回填一个覆盖目标样本且长期有效的稳定范围。缺少该策略时回 Stage-2，不要在 case 生成阶段猜。
- 操作步骤的第一步必须是已就位数据上的真实用户动作。**禁止**把"先创建 KB / document / workflow / row 等前置依赖，再做断言"写成操作步骤——这是 Stage-2 没把前置数据回填好的信号，应回到 TDRS 完成查询 / Gate B 创建后再生成。仅当 case 的验证主题本身就是"创建动作"时，操作步骤才执行创建。
- 可执行 case 不得残留 `<TO_FILL>`、`<id>`、示例 URL、"正确的入口"、"存在一条数据"等占位或泛化描述。
- 数据未就位、BLOCKED、manual-prep、skip、UNVERIFIED 场景不得作为可执行 case 输出；必须保留为 `case.md` 中对应的未完成 / 待人工补全 case，保留原始前置条件描述，并用 `**[tag]** manual-review,needs-data` 标明不可自动执行。代码分析、查询 API、查询不满足原因、构造计划或人工补数动作只写在 `test_analysis.md`，不要塞进 `case.md`。

可执行行不满足门禁时，不得用占位符凑 case；如果已经有明确不可执行状态，则生成未完成 / 待人工补全 case。只有遇到未分类行时才停止生成并回到 Stage-2 补分类。

## 生成步骤

1. 读取 `references/test_case_grammar.md` 和 `references/ab_setting_rule.md`。
2. 按 Follow the input 风格把 `test_analysis.md` 转成 `case.md`，保持原有验证意图，不新增未分析过的场景，也不丢弃任何验收点；可执行性只决定 tag / 前置条件格式，不决定是否生成 case。
3. 先按行分类：`auto` / `CLOSED` 且数据完整的行生成可执行 case；`BLOCKED` / `manual-prep` / `skip` / `UNVERIFIED` 或数据不完整的行生成未完成 / 待人工补全 case；未分类行停止并回 Stage-2。每条 case 的 `测试点` 节点 body 必须包含 `**[analysis-id]** <id>`，用于后续脚本校验覆盖矩阵。
4. 对所有 case（包括未完成 / 待人工补全 case），将一个逻辑动作和它的断言拆成相邻的 `操作步骤` / `预期结果` 节点；每个独立断言必须是独立 `预期结果` 节点。若拆分时发现该验证主题实际包含多个独立验收点，先回 `test_analysis.md` 拆行并重新走 Stage-2，不要在 `case.md` 中临时拆出未研究过的数据依赖。
5. 套用下方 Web 硬规则和未完成 case 保留格式。
6. 运行 `scripts/case_grammar_check.py <case.md> --analysis-file <test_analysis.md>`；失败则先修 `case.md` / `test_analysis.md`。未完成 / 待人工补全 case 也必须通过结构语法检查；它们通过 `manual-review` / `needs-data` tag 豁免 URL 强校验，但不豁免 `analysis-id` 一对一映射。

## Web 硬规则

### 1. 前置条件只放导航入口

每个可执行 Web case 的 `前置条件` 节点只能是两行：

```text
##### **前置条件** 访问: <裸 URL>
**[tag]** e2e
```

规则：

- URL 必须裸写，不加反引号、括号、引号、`<...>`、中文括号，不换行。
- URL 行不能混入样本 id、状态、权限、业务说明或 `；` 后缀。
- 样本事实、`[P0]` / `[P1]` / `[E2E]` / `[API]` 等元数据 tag、ownership 信息只保留在 `test_analysis.md` 的前置条件列里（按 TDRS Phase 7.1 格式书写），**不要**复制进 `case.md` 前置条件；反过来也**不要**把 `test_analysis.md` 的前置条件列改成 `case.md` 这两行——两套格式各有用途，不能互相替代或混用。
- 生成 `访问: <裸 URL>` 前必须先核对 `test_analysis.md` 中的 route provenance 和初始化参数策略。**禁止**从 app 名、目录名、功能路径或页面标题猜 URL；例如微前端下 `basename=/moderation-system` 与业务 route `/recall-strategy/strategy-group/list` 要组合成 `/moderation-system/recall-strategy/strategy-group/list`，不能把 app 名重复拼成 `/moderation-system/recall-strategy/recall-strategy/...`。如果页面依赖初始化 query（如列表页时间窗），不得因为手动浏览器会自动跳转就忽略；稳定参数写进 URL，动态参数按 Stage-2 记录的策略交给执行脚本动态补齐或使用稳定范围。缺少 provenance / 初始化策略时回 Stage-2，不要在本阶段补猜。

### 2. 未完成 Case 保留原始前置条件

`case.md` 必须保留所有不可自动执行的验收点，并按 prd2case 标准节点组织成对应 case：

- 必须保留对应 case，而不是改成普通列表或表格。
- 必须保留原始前置条件描述，不写 `访问: <URL>`，也不写 `<TO_FILL>`、`<id>`、示例 URL 或伪造入口。
- 必须在前置条件节点或其 body 写 `**[tag]** manual-review,needs-data`；如果有明确状态，可附加 `blocked` / `manual-prep` / `skip` / `unverified` tag。
- `操作步骤` / `预期结果` 保留原始测试意图和断言颗粒度；可以把执行说明改写得更适合人工补数，但不得合并多个独立断言，不得把代码分析、查询 API、查询失败原因或构造计划写进 `case.md`。
- 已经做过哪些代码分析 / 查询 API、查询为什么不满足、需要用户 review 的数据构造计划或人工补数动作，统一放在 `test_analysis.md` 对应行。

### 3. 操作步骤不负责打开页面

- 第一个 `操作步骤` 必须是页面已加载后的真实用户动作。
- 禁止写：打开 URL、访问上述链接、进入页面、Open / Visit / Navigate。
- 需要再次导航时，写真实动作，例如：刷新当前页面、点击面包屑返回列表后再点目标行。

### 4. 上传文件使用 Markdown 链接

涉及上传 / 选择文件 / 拖拽文件时，该步骤必须单独写成：

```text
[<上传控件可见文本>](<file path or bytest URL>)
```

打开弹框、进入上传页等前置动作要单独写在上一条操作步骤里。

### 5. P0 预期结果逐条标记

`test_analysis.md` 中标为 `[P0]` 的验证点，其对应的每一个 `预期结果` 下都追加：

```text
**[priority]** P0
```

未标 `[P0]` 的验证点不加 priority。

## 最小自检

生成后、语法检查前，逐条确认：

- [ ] 每个可执行 case 的前置条件正好是 `访问: <裸 URL>` + `**[tag]** e2e`。
- [ ] 每个可执行 URL 都能在 `test_analysis.md` 找到 route provenance（router / basename 或页面入口配置来源），不是由路径命名猜出来的。
- [ ] 每个可执行 URL 都能在 `test_analysis.md` 找到初始化参数策略：稳定上下文参数已保留，动态参数有执行期动态补齐或稳定范围说明。
- [ ] 每个 `test_analysis.md` 有效 `分析ID` 都在 `case.md` 中有且只有一条 case 引用；没有 case 引用多个 `分析ID`。
- [ ] 每个未完成 case 的前置条件保留原始描述，并带 `manual-review,needs-data` tag。
- [ ] 可执行 case 前置条件中没有样本元数据、权限说明、状态描述或占位符。
- [ ] 操作步骤没有打开 / 访问 URL 类指令。
- [ ] 上传步骤使用单行 Markdown 链接。
- [ ] 每个独立断言都是独立 `预期结果` 节点，没有为了执行便利聚合断言；P0 的每个预期结果都标了 `**[priority]** P0`。
- [ ] BLOCKED / manual-prep / skip / UNVERIFIED 场景没有被生成成可执行 case，且已保留为语法合法的未完成 case。
- [ ] `test_analysis.md` 总行数 = 可执行 case 数 + 未完成 case 数；差值为 0。
- [ ] 没有在 `case.md` 阶段新增未经过 Stage-1 全量验证点审查和 Stage-2 TDRS 裁决的 case。
