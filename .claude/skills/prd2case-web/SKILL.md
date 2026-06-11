---
name: prd2case-web
description: 指导如何生成Web e2e场景的文本测试用例(case.md), 文本测试用例将作为后续流程中Web e2e自动化测试的输入
user-invocable: true
---

# PRD to Web E2E Test Cases
- 本 skill 专注于生成 Web e2e 自动化测试所需的文本测试用例
- 任务的产出需要放在本次开发任务的对应目录下，通常为`specs/yyyymmdd-feature-name`
- 在进入任务流程前，**必须**先执行下一节的 `前置：读取仓库偏好设置 (.test_config.ini)`


## 前置：读取仓库偏好设置 (.test_config.ini)

**适用范围**：进入下方任务流程前必须先执行此步骤，不得跳过。

**读取位置**：仅读取 git 仓库根目录下的 `.test_config.ini`（通过 `git rev-parse --show-toplevel` 定位仓库根），不读取其他目录或上层目录。

**文件格式**：INI，prd2case 偏好集中写在 `[prd2case]` section 下。当前支持以下字段（均为可选）：

```ini
[prd2case]
# 产出文档 (test_analysis.md / case.md) 的语言偏好
# 取值：zh | en；未配置时跟随用户与 agent 的交流语言
language = zh

# 业务自定义知识库路径，绝对路径，或以项目根目录为基础的相对路径
business_knowledge_path = .../path/to/knowledge_base
```

说明：
- 该文件可同时承载其他工具的配置，各自放到自己的 section 下；prd2case 只读取并只认 `[prd2case]` section
- 不在 `[prd2case]` section 下的键值对于 prd2case 一律忽略

**执行步骤**：
1. 使用 bash 获取仓库根目录，例如 `REPO_ROOT="$(git rev-parse --show-toplevel)"`
2. 判断 `$REPO_ROOT/.test_config.ini` 是否存在
3. **文件存在**：
   - 使用标准 INI 解析器（如 Python `configparser`）读取 `[prd2case]` section
   - 逐一校验字段取值（详见下文"字段语义与合法取值"）
   - 将合法字段保存到当前任务的偏好上下文中，后续所有阶段均以该上下文为准，不得被默认逻辑覆盖
   - 向用户一次性回显本次加载到的偏好，例如："已加载 .test_config.ini [prd2case]：language=zh, business_knowledge_path=xxx"
   - 若文件存在但 `[prd2case]` section 缺失或为空，等同于"无偏好"，按下方"文件不存在"的提示流程处理
4. **文件不存在**：
   - 必须向用户输出一次性提示："未找到仓库根目录下的 `.test_config.ini`（或其中缺少 `[prd2case]` section），将使用默认流程"
   - 之后按原有流程继续，**不得**中断任务、**不得**反复追问用户是否需要创建
5. **文件存在但解析失败或部分字段非法**：
   - 对非法字段输出提示后忽略该字段，继续使用默认值
   - 合法字段仍正常加载，不因个别字段非法而终止任务

**字段语义与合法取值**（均位于 `[prd2case]` section 下）：
- `language`：
  - 合法取值：`zh` 或 `en`
  - 作用：覆盖"语言跟随用户交流语言"的默认策略，决定 `test_analysis.md` 和 `case.md` 的输出语言
- `business_knowledge_path`：
  - 合法取值：一个在本地文件系统中存在的路径
  - 作用：在 Stage-3 生成测试用例时，读取业务知识补充和完善测试分析文档，为具体用例生成提供更完整的上下文

## 任务流程: 生成 Web E2E 自动化测试所需的文本测试用例

目标：从需求 / `spec.md` 生成可执行的 Web E2E 输入文档，产物固定在本次需求目录的 `test/` 下：

```text
specs/<feature>/test/
├── test_analysis.md   # 测试分析 + 数据可执行性记录
└── case.md            # 下游 webe2e / TTAT / Bits 使用的文本用例
```

**边界**：Web 侧「执行—任务状态—失败诊断与报告」均在 **`webe2e`**；本 skill 负责 `test_analysis.md` / `case.md` 与 Bits/TTAT 同步编排，不包含报告分析。

### 固定配置

- `Global`: Semi Auto
- `Generation Style`: Follow the input
- `CASE_GENERATION_MODE`: Web
- 输出语言：优先读取仓库根目录 `.test_config.ini` 的 `[prd2case].language`；未配置时跟随用户语言。

### Stage-1：生成 `test_analysis.md`

从测试执行视角分析需求，而不是复述实现细节。`test_analysis.md` 必须先基于上下文完整枚举验收点，再按可执行性分类；优先级只是排序和标注，不是裁剪范围的依据。

开始 Stage-1 前，先确定产物目录并创建初始分析文档：

- Web E2E 产物固定放在本次需求目录的 `test/` 子目录；如目录不存在，先创建。
- 若 `test_analysis.md` 不存在，复制 `resources/test_analysis_template.md` 到该目录并命名为 `test_analysis.md`，再在模板结构内填写分析内容。
- 若 `test_analysis.md` 已存在，本轮只能在保留既有验证点的基础上补齐/修正，不得整文件覆盖导致历史已确认的验证点、用户提供检查点或上轮分析行丢失。
- Stage-1 是覆盖矩阵的唯一来源；后续 Stage-2 TDRS 只能对这些行做数据研究、可执行性分类和回填，不能替代 Stage-1 重新生成覆盖范围。

**上下文输入范围**：

- 必读：`spec.md` / PRD / 用户提供的需求文档。
- 如存在则必须参考：技术实现文档（ERD / design doc）、代码变更、Figma / 交互稿、历史 `test_analysis.md` / `case.md`、`.test_config.ini` 中的 `business_knowledge_path`、`business_knowledge/${Business Identifier}` 与 `skills/custom/${Business Identifier}`。
- 业务自定义知识 / 技能优先级高于通用规则；如和通用规则冲突，说明采用原因。
- 上下文只用于 **Stage-1 枚举和补齐验证点**，不得替代 Stage-2 的 TDRS：不能因为上下文里有样例 URL / ID 就跳过代码分析、live API 查数、Gate B 造数确认或 Gate C 裁决。

`test_analysis.md` 必须覆盖（覆盖范围先于可执行性判断）：

- 功能验证点：覆盖需求涉及的主链路、关键分支、异常 / 边界场景。
- P0 标记：只给核心验收链路加 `[P0]`，不要把所有场景都标 P0；P0 / P1 / P2 / P3 只表示优先级，不得作为丢弃非 P0 验收点的理由。
- 执行信息：每个验证点都要记录页面入口、数据状态、可观察锚点与可执行性状态；缺失处先保留原始数据要求并标 `UNVERIFIED` / `BLOCKED` / `manual-prep` / `skip`，不要猜。

**覆盖完整性硬规则**：

- 一个验证点 = 一行 `test_analysis.md`。预期清单（用户给出的检查点、PRD 验收点、上一轮 spec / case.md 已经枚举的项）里有几条，就要落几行；**禁止**把若干验证点合并成"综合用例"或因为优先级不是 P0、数据暂缺、暂不可自动执行而在 Stage-1 / Stage-2 静默丢失。
- 每行必须有稳定 `分析ID`（如 `WEB-001`）。后续 `case.md` 必须通过 `**[analysis-id]** <id>` 一对一引用；一条 case 只能引用一个 id，多个独立验收点必须拆成多条 case。
- 进入下一阶段前自查：把需求里所有验收点 / 用户给定的检查点 ↔ `test_analysis.md` 行数做一次显式对账。任一条没对应行（包括"可能是 manual-prep"或"暂时不好测"），必须先标记原因再继续，不允许悄悄少。
- 数据可行性 ≠ 是否保留行。"难造数 / 不好稳定执行"在 Stage-1 不是裁掉验证点的理由；这类行先保留，留给 Stage-2 的 TDRS 用 `manual-prep` / `BLOCKED` / `CLOSED with provided sample` 等正式状态裁决。
- 可执行性不是进入 `case.md` 的门槛，只决定后续是生成可自动执行 case，还是生成带 `manual-review,needs-data` 等标记的未完成 / 待人工补全 case；不得因为缺鉴权、缺 owner、缺故障注入能力或缺大数据量样本而减少用例范围。
- 前置条件必须精确到测试对象和状态，不能只写"进入某页面"或"存在某数据"。例如应写"进入包含至少 2 个版本且含 Auto Prompt 标识的项目详情页"，而不是"进入项目详情页"。

**二次反思（必做）**：

完成功能测试章节后，不能直接进入 Stage-2；必须结合 `spec.md`、当前 `test_analysis.md`，以及可用的 ERD / 代码变更 / 业务知识做一次系统性查漏补缺，并使用下面的固定 prompt：

```text
请结合 spec.md 与当前 test_analysis.md，对测试分析做一次系统性查漏补缺。

检查时至少覆盖以下维度：
1. 全量功能覆盖：spec 中涉及的每一个功能模块是否都已分析，不能只覆盖核心功能而遗漏次要功能
2. 全量场景覆盖：每个功能模块下的正向主链路、关键分支、异常/边界场景是否都已列出
3. P0 标注：P0 核心验证点的标注是否准确，是否把非核心场景错误标为 P0，或遗漏了真正的核心链路
4. 关键验证点：每个测试场景是否都写清楚了必须断言的结果、状态、文案、页面变化或产物
5. 关键分支：如果 spec 中存在必须验证的关键分支、状态切换或前后置依赖，是否已经纳入

输出要求：
- 先列出"发现的遗漏点"
- 再说明"需要如何补到 test_analysis.md"
- 如果没有遗漏，也要明确写出"未发现明显遗漏"，不能跳过这一步
```

如果发现遗漏，必须先回写并更新 `test_analysis.md`，再进入 Stage-2。二次反思只能补齐验证点和测试意图；不得在这里把样本标 `CLOSED`，也不得替代 TDRS 的代码分析、真实 API 查数、Gate B / Gate C。

### Stage-2：代码分析 + 数据研究回填（强制）

生成 `case.md` 前，**必须**对 `test_analysis.md` 的每一行执行 `webe2e/test-data-research-and-seeding`（TDRS）的固定四步流程，目标是最大化可执行样本闭环与 URL / 数据回填收益；**不得**把 TDRS 变成覆盖范围裁剪器，也不得替换为"case 执行时自包含构造"。`prd2case` 只声明门禁，每一步的方法论以 TDRS skill 为准。

**Stage-2 第 0 步——鉴权前置门禁（preflight）**：在做任何分类、查数、写 `TDRS证据` 之前，必须先跑 `python3 $WEBE2E_SKILL/scripts/tdrs_preflight.py <workspace>`。preflight 检查的是 workspace 下结构化文件是否存在：`.env`（含 token 形的 KEY=VALUE）、`cookies.txt`、`auth.json`、`save_result.json`，或 `auth_log.md` 中至少有一条 `user_reply_verbatim: <非空>` 条目。任意一个存在即可通过。preflight 不通过时，必须用 `AskQuestion`（或当前 agent 等价的用户交互工具）向用户发起鉴权 / API 材料请求（curl / cookie / token / owner scope / list 或 detail 接口），把用户的逐字回复追加到 `auth_log.md` 后再重跑 preflight。**禁止**只在 `test_analysis.md` 或对话里写一句"已请求材料"就视为问过用户——preflight 检查的是文件，不是 prose。preflight 通过前不得开始 TDRS 行操作。

四步流程（顺序不得颠倒，每一步必须留下证据）：

1. **逐行数据需求拆解（不重建覆盖范围）**：以 Stage-1 已生成的 `test_analysis.md` 中每个验证点为单位，逐条列出该验证点要测什么、依赖什么前置条件。禁止在这里重新按 PRD/spec 生成一份新的测试分析来覆盖 Stage-1；若发现遗漏验证点，必须回 Stage-1 补行，再重新进入 Stage-2。
2. **前置条件数据要求**：把每条验证点的前置条件展开为可执行的数据需求字段——目标实体 + 父容器、页面入口 / router provenance、URL 初始化参数策略、step 1 初始状态、运行时门控链（ambient enable chain）、结构不变量、可观察锚点、stateful 标记、可行性。占位符（"存在一条数据""一个可用项目"等）一律视为缺失。
3. **代码分析 + API 调用查找 / 构造测试数据**：严格的优先级顺序如下，**不得跳级**——
   1. **先做代码分析沉淀取数知识**：按 TDRS 硬规则做前端代码分析（路由 → 页面 → hooks → API wrapper → 权限 / 类型），把"在哪个 API、用哪些过滤参数、能筛出什么样的样本"写进 `business_knowledge/**/data_queries.md`；
   2. **基于取数知识用真实 API 查找可复用样本**：用户已经给出稳定 ID / URL / 账号 / fixture 的，直接采用并标 `CLOSED — provided stable sample: <ref>`；其他行用沉淀好的 query 跑业务接口找现成可用样本；
   3. **找不到再列造数方案给用户确认**（Gate B）：列出 `实体 + API + payload + 归属 + 原因 + 验证方式`，等用户显式确认后再执行；用户拒绝就重新规划或走 Gate C；
   4. **manual-prep 类目走 Gate C** 输出 Manual-Prep Request，不要在 query / create 上反复试。
4. **回填 URL，替换前置条件**：URL / 样本 id 的替换**只在 row 的样本被 live API 验证已满足数据要求，且页面 URL 已由目标 app 的真实 router / basename 或现有页面入口配置证明后才发生**。在此之前——查询中、Gate B 等用户确认中、未验证、只知道功能路径但未查路由——**保留**前置条件原本的数据要求描述（仅以 `UNVERIFIED — data requirement: <原描述>` 标注，元数据 tag 保留），**不要**写半成品 URL，也**不要**只凭应用名 + 功能路径直觉拼 URL。已 CLOSED 的 row 才按 **TDRS Phase 7.1 格式**回填：每行保留**原有元数据标签**（`[P0]` / `[P1]` / `[E2E]` / `[API]` / `[Smoke]` / `[Regression]` 等方括号 tag）+ 解析后的 `entity id (state, ownership 等关键事实)` + 直连 URL + route provenance + URL 初始化参数策略；**不要**把元数据 tag 删掉，**不要**把"需要存在 / 至少有 / 应该是"这类 setup 动词留下来。**前置条件依赖的数据必须在 Stage-2 全部就位**，不允许落到 case 执行时再现造（包括"运行时临时 KB / Text / CSV fixture"、"操作步骤里先 create 再 assert"等任何执行期补数据的写法）；只有验证目标本身就是"创建动作"的 case，才在操作步骤里执行创建。

> 注意：`test_analysis.md` 的前置条件列保留**完整元数据 + 解析样本**，是给 `prd2case` 自己 / executing test agent 看的；下一步 Stage-3 在生成 `case.md` 时会把它**精简**为只剩"访问 URL + tag"两行（见下方 Web 用例硬约束）。两套格式各有用途，不能互相替代，也不能混用。

硬门禁：

- 四步缺一不可，但门禁对象是"每一行都有裁决状态"，不是"每一行都必须闭环可执行"。已完成真实查询 / 代码分析 / Gate B 或 Gate C 裁决的行可以分别标为 `CLOSED`、`BLOCKED`、`manual-prep`、`skip`、`UNVERIFIED` 等状态进入 Stage-3；不接受未分类行，也不接受因为未闭环就从 `test_analysis.md` 或 `case.md` 删除。
- **TDRS gate 必跑**：Stage-2 结束后、Stage-3 之前必须运行 `python3 $WEBE2E_SKILL/scripts/tdrs_gate.py <test_analysis.md>`。该 gate 不要求所有行都 `CLOSED`，但要求每个 `分析ID` 都有终态、数据要求和裁决证据；`CLOSED` 行必须有 live API / provided sample 证据、查数参数、查数结果和回填 URL；`UNVERIFIED` 行也必须有尝试证据或阻断原因。gate 不通过不得生成 `case.md`。
- **TDRS 证据列保持可读**：`test_analysis.md` 默认只保留 `TDRS状态` + `TDRS证据` 两列。`TDRS证据` 用分号分隔的 `key=value` 写法承载细节，例如：`数据要求=...; 查数API=...; 查数参数=...; 查数结果=...; 回填URL=...; 裁决证据=...; 查询次数=1; 造数次数=0`。如业务特别复杂，也可临时展开为独立列；`tdrs_gate.py` 同时兼容两种格式。
- **缺鉴权 / 缺 API 信息先问用户**：`no live sample data provided`、`未提供样本`、`没有数据` 不是终态裁决，只是 Stage-2 起点。没有可用鉴权、curl、cookie、token、owner scope 或 list/detail API 时，必须先向用户请求这些信息；只有用户明确拒绝 / 明确无法提供 / 确认无对应权限，或已有真实 API 尝试/权限失败证据后，才允许写 `BLOCKED` / `manual-prep` / `UNVERIFIED`。`tdrs_gate.py` 会拒绝空泛的“未提供样本”裁决证据，也会拒绝只有“已请求材料”但没有明确用户结果的裁决。
- `TDRS证据` 里只写 `查数结果=缺少鉴权/API 信息` 不算 API 尝试证据；必须补 `裁决证据=已向用户请求鉴权 curl / owner scope，用户明确无法提供`，或记录真实请求（如 `GET /api/...`、`curl ...`、`HTTP 403`、`API 500`）。
- **有限尝试预算**：每个 `分析ID` 默认最多 2 次 query、1 次 Gate-B-confirmed create；超过预算必须停止尝试并记录 `UNVERIFIED` / `manual-prep` / `BLOCKED` 裁决，禁止无限查数或反复造数。
- **数据准备顺序硬约束**：代码分析沉淀取数知识 → 用知识跑真实 API 找可复用样本（用户已给的样本直接 `CLOSED`）→ 找不到再列造数方案给用户确认 → 用户拒绝或不可造则走 Gate C。**不得**跳过任何一级，**不得**没查就直接进 Gate B，**不得**没确认就直接造数。
- **Phase 3 必须真打 API**：Phase 3 查数 = 用 `.env` 里的鉴权（或用户粘贴的 curl）直接调平台 list/detail 接口。grep `specs/**` / 历史 spec 是 Phase 0 历史样本检索，结果是未验证线索；没有 live API 调用确认当前样本仍满足 row 要求之前，**不得**记 `CLOSED`，也**不得**升级到 Gate B / Manual-Prep。
- **前置条件数据不得延迟到执行时**：所有前置条件依赖的数据必须在 Stage-2 就完成查询 / 创建并回填真实 ID / URL，case 操作步骤的第一步必须是"在已就位数据上的真实用户动作"，不能是"为了凑前置条件而创建数据"。仅当 case 的验证主题本身就是"创建动作"时，操作步骤才执行创建。
- 每个可执行场景必须回填：直连 URL、目标数据引用、router provenance（例如 `basename=/moderation-system` + `route=/recall-strategy/strategy-group/list` + 来源文件）、URL 初始化参数策略、step 1 初始状态、可观察断言锚点；这些字段必须来自真实代码 / 页面入口配置 + 真实查询 / 已确认创建的样本，不得是构造性描述。
- **URL 初始化参数策略**：必须区分稳定业务上下文参数与动态初始化参数。稳定参数（如 `tenantId`、`owners`、目标 id、筛选枚举）如果决定页面上下文或目标样本定位，应写入直连 URL；动态参数（如相对当前时间生成的 `startTime` / `endTime`）不要盲目固化过期时间戳，应在 `test_analysis.md` 记录来源和处理方式：由执行脚本动态补齐、或选择覆盖目标样本且长期有效的稳定时间范围。若候选 URL 打开后页面会通过 redirect / `history.replaceState` 补齐 query，Stage-2 必须记录最终落地 URL 与哪些参数被保留 / 动态化；不能只凭初始 URL 在手动浏览器会跳转就标 `CLOSED`。
- 需要创建数据时，必须先给出 Gate B 创建计划（实体 + API + payload + 归属 + 原因 + 验证方式）并等用户显式确认后再执行；能复用已有样本则不创建。
- 无法自动准备的数据（不同账号、外部原料导入 + 交互式鉴权、瞬态运行时状态、外部失败注入、第三方凭据等），按 Gate C 标为 `BLOCKED — needs manual prep: <原因>`，不得用 case 执行时自造数绕过。
- 禁止带 `<TO_FILL>`、`<id>`、示例 URL、泛化描述（如"存在一条数据"）进入 `case.md` 的可执行 case。数据未就位的行不得用占位符凑成可执行 case，但必须按 Stage-3 的"需人工 Review / 非自动执行项"格式保留在 `case.md`，提示用户人工补数或确认跳过。

### Stage-3：生成 `case.md`

读取并遵守 `references/case_generation_workflow.md`。生成时只消费已通过 `tdrs_gate.py` 的 `test_analysis.md`，不得绕过回填结果直接从 PRD / 原始分析稿生成用例。

进入 Stage-3 前先按行分类；分类只影响 case 的可执行性标记和前置条件格式，不影响是否进入 `case.md`：

- **可执行行**：状态为 `auto` / `CLOSED`，且已具备直连 URL、目标数据引用、step 1 初始状态和可观察锚点。这类行生成标准 Web 可执行 case。
- **未完成 / 待人工补全行**：状态为 `BLOCKED` / `manual-prep` / `skip` / `UNVERIFIED`，或仍缺少直连 URL、目标数据引用、初始状态、可观察锚点。这类行不得伪装成可执行 case，但必须在 `case.md` 中保留为对应 case：使用 prd2case 标准节点结构，保留原始前置条件描述，并在前置条件节点写 `**[tag]** manual-review,needs-data`。已做过的代码分析 / 查询 API、查询不满足原因、数据构造计划或人工补数动作只放在 `test_analysis.md`。
- **未分类行**：既没有满足可执行条件，也没有明确不可执行状态。遇到未分类行必须 STOP，先回 Stage-2 补分类，不能静默丢弃。

Web 用例硬约束：

- **以下 URL 硬约束只适用于可执行 case**；未完成 / 待人工补全 case 也必须使用 `前置条件`、`操作步骤`、`预期结果` 等 prd2case 标准节点，保证 `case.md` 语法检查通过，但前置条件保留原始描述并标 `**[tag]** manual-review,needs-data`，不得写假 URL。
- **`case.md` 可执行 case 的前置条件节点严格只写两行**：`##### **前置条件** 访问: <裸 URL>` 和 `**[tag]** e2e`。这是 case.md 的**专用精简格式**，用来给 TTAT / 本地 runner 当导航入口；任何样本 id、状态、权限、说明文字、`[P0]` / `[E2E]` 类元数据 tag 都**只**留在 `test_analysis.md` 的前置条件列里（见 Stage-2 第 4 步与 TDRS Phase 7.1），不要写进 `case.md` 的前置条件。
  - 反例（混了 `test_analysis.md` 的 Phase 7.1 格式进来）：`##### **前置条件** [P0] [E2E] KB 7615... (Available); URL https://...`
  - 正例：`##### **前置条件** 访问: https://vine.tiktok-row.net/rd_test/knowledge_base/7615.../document/7615...` + `**[tag]** e2e`
  - 反过来也不允许：**禁止**把 `test_analysis.md` 的前置条件列裁成 `case.md` 那两行（裁掉了 `[P0]` / `[E2E]` 等下游过滤 tag 与样本事实，会破坏 TDRS Phase 7.1 的资产）。
- **裸 URL 必须是完整可直连的绝对 URL**：必须以 `http://` 或 `https://` 开头，正则 `^https?://[^\s]+`。**禁止**写：
  - 相对路径或路由片段：`/ads-creation/dashboard`、`/creation`、`./detail`、`../list`——这些是 spec / 前端代码里的 react-router / next-router 路由，不是可执行 URL。
  - 仅 host：`https://platform.example.com`（少了业务页面路径，访问后落到首页或登录页，不是 case 想验证的入口）。
  - 占位符：`<URL>`、`<TO_FILL>`、`https://example.com/...`、`http://localhost:xxx`。
  - 模板片段：`https://{host}/path`、`https://${env}/...`。
  - 判定原则：把字符串原样粘到浏览器 / `playwright-cli goto` 里，**当前账号**就能直接落到对应的"目标数据 + 初始状态"页面；做不到就不是裸 URL，必须回 Stage-2 通过 TDRS Phase 6/7 跑 live API 拿到真实样本 ID，把 URL 拼出来再回填。
  - 把 spec 路由当成 URL 是 Stage-2 没做完的信号，不是 Stage-3 的锅；遇到就停 Stage-3，回 Stage-2 补样本，**不要**用相对路径凑数。
- **裸 URL 的业务路径必须有 route provenance**：生成 Web E2E URL 前必须先查目标 app 的 router / basename（如 `apps/<app>/src/routers/index.tsx`、Next/React Router route config）或现有页面入口配置，确认最终路径由 `host + basename + route + query/hash` 组成。**禁止**根据应用名、目录名、功能路径或历史 URL 形状猜测路径，尤其是微前端仓库里 app 名、basename、业务 route 可能重复或不一致。若只知道"应用名 + 功能路径"，Stage-3 必须 STOP，回 Stage-2 补 route provenance。
- `操作步骤` 不写"打开 / 访问 / 进入 URL"；第一步必须是页面已加载后的真实用户动作。
- 上传文件步骤必须写成一行 Markdown 链接：`[<上传控件可见文本>](<file path or bytest URL>)`。
- `[P0]` 验证点对应的每一个 `预期结果` 都要追加 `**[priority]** P0`。
- 生成后运行 `scripts/case_grammar_check.py <case.md> --analysis-file <test_analysis.md>`；不通过就先修 `case.md` / `test_analysis.md`，不得进入 Stage-4。其中 `R9_PRECONDITION_URL` 会逐个可执行 case 的 `前置条件` 节点校验"`访问:` 后跟绝对 URL"；`R10_ANALYSIS_CASE_MAPPING` 会校验 `test_analysis.md` 每个 `分析ID` 都有且只有一条 case 对应，防止遗漏和聚合。带 `manual-review` / `needs-data` 等未完成标记的 case 可保留原始前置条件描述，但必须在 `test_analysis.md` 写清对应的数据要求、查询证据和补数计划。

**用例粒度与覆盖硬规则**：

- **一条 case = 一个稳定验证主题**（如"禁用 KB"、"启用 KB"、"非自管 KB 只读"、"Row 删除限制"、"Disabled 内容不被检索"）。**禁止**把若干独立验证点串成长链路用例；这类用例步数多、依赖累积，TTAT 失败定位困难。
- **一对一映射**：`test_analysis.md` 中每一行都必须与 `case.md` 中一条 case 对应；`auto` / `CLOSED` 生成可执行 case，`BLOCKED` / `manual-prep` / `skip` / `UNVERIFIED` 生成未完成 / 待人工补全 case。Stage-3 不得合并多行成一条 case；不得静默丢弃任何行。
- **analysis-id 映射硬门禁**：每条 `case.md` case 的 `测试点` 节点 body 必须写一行 `**[analysis-id]** <test_analysis.md 的分析ID>`。一条 case 只能写一个 id；多个独立验收点必须拆成多条 case。`R10_ANALYSIS_CASE_MAPPING` 不通过时，不得归档 Bits，也不得进入 TTAT。
- **禁止聚合断言**：同一验证主题下多个独立验收标准必须拆成多个 `预期结果` 节点；如果一个 `预期结果` 同时包含多个可独立成败的验收标准，先拆节点。不得为了让执行更简单，把多条断言合并成一条大颗粒预期。
- **全量保留映射**：`test_analysis.md` 中每一行都必须进入 `case.md`，要么成为一条已 URL 化的可执行 case，要么成为一条保留原始前置条件的未完成 / 待人工补全 case；不得因为数据缺失、人工准备、skip 或优先级较低而从 `case.md` 消失。
- **覆盖对账自检**：写完 `case.md` 后，必须把"`test_analysis.md` 总行数 = `case.md` 可执行 case 数 + `case.md` 未完成 case 数"显式列出来；同时列出 `auto+CLOSED` 行数、`BLOCKED` / `manual-prep` / `skip` / `UNVERIFIED` 行数。差值不为 0 必须解释并补齐。
- **状态变更场景必须独立成 case**：禁用 / 启用 / 删除 / 编辑 / 切换等 stateful 动作，每条都要独立 case，不能塞进同一条用例里走多个状态流转——这是 TDRS 「stateful 样本隔离」的下游硬约束（见 TDRS skill）。

### Stage-4：同步 Bits 与 TTAT（顺序硬约束：Bits 先 → TTAT 后）

`case.md` 生成或更新后**强制**走以下顺序，**Bits 归档必须先完成**，TTAT 才允许动；首次生成 / 增量更新都一样，不存在"首次跳过 Bits"的写法。

#### Stage-4.1：Bits 归档（必做，不可跳）

1. 解析当前 case 是否已有 Bits `case_id`：依次看
   - `case.md` 同目录的 `save_result.json`（之前 `case_management.py save` 产出，含 `data.case_id` / `data.url`）；
   - 已有 `case.md` 头部 / `####` 用例块里出现的 `https://bits.bytedance.net/.../caseDetail/<id>`；
   - `.env` 的 `BITS_CASE_ID` / `BITS_CASE_DETAIL_URL`。
2. **首次（无任何 case_id）→ 必须新建 Bits 用例**：
   ```bash
   python3 $PRD2CASE_SKILL/scripts/case_management.py save \
     <test/case.md> \
     --case-title "<feature 名 / case 集合的可读标题>" \
     -o <test/save_result.json>
   ```
3. **已有 case_id → 必须更新同一个 Bits 用例**（`case_id` 不变）：
   ```bash
   python3 $PRD2CASE_SKILL/scripts/case_management.py save \
     <test/case.md> \
     --case-title "<同标题>" \
     --case-id <已有 id> \
     -o <test/save_result.json>
   ```
4. 命令产出的 `save_result.json` 必须落到 `case.md` 同目录；这是 Stage-4.2 拼装 TTAT payload 级 `extras.extras.bitsConfig.url` 与 task 级 `tasks[].case_extra.expectation_ids` 的来源。失败时 STOP，**不得**带空 Bits 链接或空 expectation_ids 进 TTAT。
5. `save_result.json` 必须包含 `data.case_expectations`：按 `case.md` 中每个 `####` 用例块保存 `expectation_nodes[]`，每个节点至少包含 `path: [操作步骤序号, 预期结果序号]`、`id`、`expected_result`。**Bits 预期结果节点数必须与当前 `case.md` 的 `##### **预期结果**` 节点数一致**；它不与 `####` 用例数、TTAT task 数或 markdown2midscene 拆出的 case 数对齐。若修改过 `case.md`，必须重跑 Stage-4.1 刷新该映射。

#### Stage-4.2：TTAT case group + 任务

只有 Stage-4.1 已经产出 `save_result.json`（含 Bits 详情 URL 与 `data.case_expectations`），且能被 `webe2e/scripts/case2webe2e.py` 解析成 payload 级 `extras.extras.bitsConfig.url` 和 task 级 `tasks[].case_extra.expectation_ids` 时，才允许进 TTAT：

- 已有 `case_group_id`（来自 `test_report.md` 或上一次命令行）→ 走 `edit-group` / `run --case-group-id <id>` 更新同一个 case group；不得新建平行 case group。
- 无 `case_group_id` → 调 `create-group` / `run` 新建。
- 拼装请求体时，**整份 `case.md` 必须能映射到一个 Bits 链接**，且每个 TTAT task 必须能按自身覆盖到的 `预期结果` 节点集合写入 `case_extra.expectation_ids`。同一个公共前缀步骤下的 `预期结果` 可以被多个拆分 task 共享；分支尾部的 `预期结果` 只进入对应 task。`webe2e` 侧若发现 Bits 链接或 expectation_ids 缺失，必须 STOP 并把缺失的 case 名/标题报回，要求先回 Stage-4.1 补归档。
- 下游同步的具体请求体和字段由 `webe2e` skill / `case2webe2e.py` 维护，`prd2case` 不内联 curl 或 token。

#### Stage-4 STOP 条件

- `case.md` 已生成/更新但 Stage-4.1 没跑（没有 `save_result.json` 也没有内嵌 Bits 链接）→ 禁止动 TTAT。
- Stage-4.1 跑了但接口失败 / 返回里没有 `case_id` 或 URL → 禁止动 TTAT，先排错。
- Stage-4.2 拼装时 payload 级 `bitsConfig.url` 解析为空，或任意 task 缺少 `case_extra.expectation_ids` → 禁止下发请求，回到 Stage-4.1 刷新归档和预期结果节点映射。

#### 最终回复前阶段审计（必写）

完成 prd2case 后，最终回复必须列出以下审计信息；缺任何一项都不能声称完成：

- `Stage-1 verification point count`: `test_analysis.md` 中有效 `分析ID` 数。
- `Stage-2 preflight`: `tdrs_preflight.py <workspace>` 的结果，并列出已检测到的资产（如 `env`/`cookies`/`auth_json`/`save_result`/`auth_log`）；preflight 不通过时必须写明已通过 `AskQuestion` 等工具问过用户，以及用户逐字回复在 `auth_log.md` 的位置。
- `Stage-2 TDRS gate`: `tdrs_gate.py <test_analysis.md>` 的结果，并列出 CLOSED / BLOCKED / manual-prep / skip / UNVERIFIED 数量。
- `Stage-3 case count`: `case.md` 中带 `**[analysis-id]**` 的 case 数。
- `Grammar gate`: `case_grammar_check.py <case.md> --analysis-file <test_analysis.md>` 的结果。
- `Bits archive`: `save_result.json` 路径与 Bits URL / case_id；若用户明确只要求到 Stage-3，写明 `skipped by request`，否则视为未完成。
- `TTAT gate`: 是否创建 / 更新 case group；未执行时写明原因。

### 读取 Lark 文档
使用 `lark-docs` MCP 读取 Lark 文档，不要使用 fetch

## Lessons Learned

### 前置条件必须精确到具体测试对象，URL 不等于可执行

**问题**：泛化的前置条件（如"进入项目详情页"、"存在历史版本"）会导致测试执行 Agent 进入不满足条件的页面，产生误判。只写页面 URL 只能保证"进到哪个页面"，不能保证"页面里的数据状态满足可执行前置条件"。

**典型失败场景**：
- URL 指向一个项目详情页，但该项目只有 v1，没有可比较的历史版本
- URL 指向一个列表页，但列表为空态，没有可操作记录
- URL 指向一个详情页，但该页面不包含所需的特定标识（如 Auto Prompt）

**正确做法**：
- 前置条件写死到具体测试对象的特征和状态
- `test_analysis.md` 的测试执行信息不能只给 URL，必须额外补充"可执行数据要求"
- 如果数据要求无法从 spec 直接得到，必须在生成用例前显式向用户确认
- 测试执行 Agent 应能据此判断"当前页面 + 数据状态是否满足要求"

### 失败归因不要过度依赖自动分析的保守结论

**问题**：自动分析脚本可能给出保守兜底结论（如"低置信度 - 步骤描述问题"），但实际报错信息中已包含足够的业务语义（如"当前项目只有 v1，没有可比较历史版本"），应优先从报错信息提取精确的失败原因。

**正确做法**：
- 优先从平台原始报错中提取业务含义，翻译成准确的测试前置问题
- 需要结合执行失败结论迭代 `test_analysis.md` / `case.md` 时：先在 **`webe2e`** 侧完成执行与报告结论；本 skill 仅在已有明确结论后协助改文档，不在本 skill 内做报告解读
- 归因粒度要足够细："进入了不满足前置条件的详情页"比"空数据/没有数据"更准确
