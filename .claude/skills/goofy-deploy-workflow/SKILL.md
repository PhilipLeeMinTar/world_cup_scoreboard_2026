---
name: goofy-deploy-workflow
description: "Goofy Deploy 一键部署流程（bytedcli）。当用户说 Goofy 部署/Goofy Deploy/部署 channel/channel-id/appid/app-id/env/泳道环境/上线灰度/回滚/查询部署状态，或贴出 PSM 想找到对应通道并发起部署时，必须使用此 Skill。Skill 会优先从上下文/当前仓库/本地 git 自动提取必要参数（站点、appid、channel、env、部署类型、分支/commit 或 scm-version）；并设置默认值以减少追问：site 默认 cn、git 分支默认当前分支、默认 deploy-new；仅对缺失或歧义参数再用 AskUserQuestion 补齐。支持创建和部署泳道环境。真正触发部署前，会再次向用户确认关键参数，并给出可直接执行的 bytedcli 命令与 deploy_id 状态查询。"
---

# Goofy Deploy 部署流程（bytedcli）

目标：把「登录鉴权 → 找到 app/channel → 触发部署/回滚 → 查询结果」做成可复用、低误操作的交互式流程。

## 0. 运行前检查（必须）

1) 先检查认证状态：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest auth status
```

2) 若提示 `Not authenticated`，让用户完成登录（设备码或浏览器登录均可）：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest auth login
```

3) 登录成功后再跑一次 `auth status`（确保存储生效）。

## 1. 参数收集：先自动推断，再补齐（必须）

目标：当用户“已经在上下文里给了信息”或“当前目录本身就是目标仓库”时，不要重复追问；仅对缺失/歧义字段再询问，降低交互成本。

需要的关键变量（尽量从上到下填充）：
- `site`：`cn|boe`
- `app-id`：`APP_ID`（可选，但用于列通道/查历史时很有用）
- `env`：泳道环境名（可选，如果用户提供 env 将触发新建通道后部署的泳道流程）
- `channel-id`：`CHANNEL_ID`（普通部署必须，泳道部署由新建获得）
- `action`：`deploy-new | deploy-version | query`
- `branch` + `commit`：用于 `deploy-new`
- `scm-version`：用于 `deploy-version`
- `deploy-id`：用于 `query` 或 `deploy-version` 的结果确认

### 1.1 优先从上下文自动提取（先做，别急着问）

1) 从用户对话里提取（包含历史上下文）：
- `site`：出现 “boe/测试/预发” → `boe`；出现 “cn/线上/生产/ppe” → `cn`；都没有 → 先默认 `cn`（不要为默认值额外提问）。
- `APP_ID`：形如 `app-id=...` / `appid=...` / `appId: ...` / “appId 123456”。
- `CHANNEL_ID`：形如 `channel-id=...` / `channelId: ...` / “channel 123456”。
- `ENV`：形如 `env=...` / “环境 xxx” / “泳道 xxx”。
- `DEPLOY_ID`：形如 `deploy-id=...` / “deploy_id 123456”。
- `SCM_VERSION`：形如 `scm-version=...` / “scmVersion ...”。
- `branch`/`commit`：用户显式给出时优先采用用户给的（例如 “用 release/xxx 分支的 1a2b3c4”）。

2) 从当前工作区（仓库）提取：
- 如果当前目录在 git 仓库中，优先自动读取：
  - `branch`：`git rev-parse --abbrev-ref HEAD`
  - `commit`：`git rev-parse HEAD`

3) 从仓库配置文件“弱匹配”提取（仅当用户没给 app/channel 时尝试）：
- 在当前仓库内搜索关键词（示例：`goofy` / `cloud.bytedance.net` / `cloud-boe.bytedance.net` / `appId` / `channelId` / `channel-id` / `app-id` / `env` / `scmVersion` / `PSM`）。
- 若找到多个候选（例如多个 `appId` 或多个 `channelId`），把候选列表展示给用户，并用 `AskUserQuestion` 让用户选一个；不要自行猜测。

### 1.2 仅对缺失/歧义参数使用 AskUserQuestion（一次性补齐）

原则：
- 只问缺失项，不要重复确认已明确给出的字段。
- 若字段存在“多个候选”，用单选让用户确认。
- 不要提供“其他”选项（系统会自动加）。

**站点（默认 `cn`，不要为默认值额外追问；仅当用户明确要 `boe`，或你确认默认 `cn` 会导致明显误操作风险时才问）**

```json
{
  "questions": [
    {
      "header": "Goofy Deploy 站点",
      "question": "本次要操作哪个 Goofy Deploy 站点？",
      "multiSelect": false,
      "options": [
        {"label": "cn（默认/生产）(Recommended)", "description": "对应 cloud.bytedance.net"},
        {"label": "boe（测试）", "description": "对应 cloud-boe.bytedance.net"}
      ]
    }
  ]
}
```

**目标定位（仅当 `APP_ID` 与 `CHANNEL_ID` 都缺失时才问）**

```json
{
  "questions": [
    {
      "header": "目标定位",
      "question": "你手里已有哪类信息用于定位部署目标？",
      "multiSelect": false,
      "options": [
        {"label": "我有 app-id（项目ID）(Recommended)", "description": "可列通道/查历史后再部署"},
        {"label": "我只有 channel-id", "description": "可直接部署/查询部署"},
        {"label": "我只有 PSM（例如 toutiao.xxx.yyy）", "description": "先从仓库/平台信息辅助定位 app/channel"}
      ]
    }
  ]
}
```

处理策略：
- 若已有 `APP_ID`：走第 2 节列通道（若 `CHANNEL_ID` 也已有，可直接跳到第 3 节）。
- 若已有 `CHANNEL_ID`：可跳过列通道，直接走第 3 节。
- 若只有 `PSM`：优先在“当前仓库配置”里搜索 PSM/appId/channelId 线索；仍无法定位时，再向用户索要 `app-id` 或 `channel-id`（注意：`goofy-deploy` 通常不支持按 PSM 直接反查 app/channel）。

## 2. 列出 app 的部署通道或创建泳道环境（当你有 app-id 时）

如果用户指定了 `env`（泳道环境），请直接跳过 2.1 和 2.2，走 **2.3 部署泳道环境流程**。否则走普通的 2.1 列通道流程。

### 2.1 列通道（推荐先做，避免误选 channel）

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --json goofy-deploy list-channels \
  --app-id <APP_ID> \
  --page-num 1 --page-size 20 \
  --site <cn|boe>
```

输出里关注：`channel.id`、`channel.name`、`regionId`、（若是 TCE 部署）`configForTceDeployPlatform.tcePsm`。

### 2.2 让用户确认要部署的 channel

用 `AskUserQuestion` 让用户从列表里选择一个 `channel-id`（不要猜）：

```json
{
  "questions": [
    {
      "header": "选择部署通道",
      "question": "请选择要操作的 channel（建议优先选择全流量/指定灰度通道，避免误部署）",
      "multiSelect": false,
      "options": [
        {"label": "<channel-id> - <channel-name>", "description": "region=<regionId>, psm=<tcePsm(如有)>"}
      ]
    }
  ]
}
```

（由调用方在运行时把 options 填成真实列表。）

### 2.3 部署泳道环境流程（当用户传入 env 时）

当用户明确提出要部署泳道环境，或给出了 `env` 参数，需执行以下步骤创建并选择通道：

1) **列出支持的 Region 并让用户选择**：
执行命令列出 app 支持的 region：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --json goofy-deploy list-regions \
  --app-id <APP_ID> \
  --site <cn|boe>
```

根据返回的列表，使用 `AskUserQuestion` 让用户选择要部署的 Region：

```json
{
  "questions": [
    {
      "header": "选择部署 Region",
      "question": "请选择要在哪个 Region 创建并部署泳道环境？",
      "multiSelect": false,
      "options": [
        {"label": "<region-id>", "description": "<region-name>"}
      ]
    }
  ]
}
```

2) **创建泳道环境的 Channel**：
直接使用用户提供的 `env` 作为通道的 `name` 参数值（除非用户明确指定了其他名称）。
用户选择 `<REGION>` 后，调用以下命令创建通道：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --json goofy-deploy create-channel \
  --region-id <REGION> \
  --env-name <ENV> \
  --name <NAME: 默认为 ENV 的值> \
  --site <cn|boe>
```

从命令返回的结果中提取新创建的 `channel-id`。

3) 成功获取 `channel-id` 后，直接进入 **第 3 节**（通常是 deploy-new）继续后续部署。

## 3. 选择部署方式：新版本 / 回滚

默认策略（减少追问）：
- 用户说“部署/发版/上线/灰度”但未说明回滚/查状态 → 默认 `deploy-new`
- 用户说“回滚/重放历史版本/用 scm-version” → 选择 `deploy-version`
- 用户说“查询/查状态/给了 deploy-id” → 选择 `query`

仅当你无法从用户意图明确判断（例如“帮我处理一下这个 channel”）时，再用 `AskUserQuestion` 询问部署动作：

```json
{
  "questions": [
    {
      "header": "部署动作",
      "question": "本次要执行哪种部署？",
      "multiSelect": false,
      "options": [
        {"label": "deploy-new（按 git 分支 + commit 部署新版本）(Recommended)", "description": "适合日常发版"},
        {"label": "deploy-version（按 scm-version 回滚/部署已有版本）", "description": "适合回滚或重放已存在版本"},
        {"label": "仅查询部署状态", "description": "已有 deploy-id 时使用"}
      ]
    }
  ]
}
```

### 3.0 最终确认（触发真实部署前必须做）

在真正执行 `deploy-new` / `deploy-version` 前，必须把解析出的关键参数一次性展示给用户并二次确认；默认选项应为“确认并开始部署”，但仍需等待用户显式确认。

确认内容至少包含：`site`、`channel-id`、`action`、以及版本信息（`deploy-new`：`branch/commit`；`deploy-version`：`scm-version`）。

```json
{
  "questions": [
    {
      "header": "最终确认",
      "question": "即将触发 Goofy Deploy（真实变更）。请确认以下参数无误后再继续：site=<cn|boe>, channel-id=<CHANNEL_ID>, action=<deploy-new|deploy-version>, version=<branch/commit 或 scm-version>。是否继续？",
      "multiSelect": false,
      "options": [
        {"label": "确认并开始部署 (Recommended)", "description": "执行 bytedcli goofy-deploy deploy-*"},
        {"label": "取消（先不部署）", "description": "不执行部署命令，可继续修改参数/仅查询"}
      ]
    }
  ]
}
```

### 3.1 deploy-new

优先从当前 git 仓库读取 `branch/commit`（见 1.1）；仅当以下情况才询问/让用户手填：
- 当前目录不是 git 仓库，或无法读取
- 用户明确指定了不同的分支/commit

若确实需要询问，再用 AskUserQuestion：

```json
{
  "questions": [
    {
      "header": "版本来源",
      "question": "commit hash 从哪里取？",
      "multiSelect": false,
      "options": [
        {"label": "使用当前本地 git 仓库的分支/HEAD (Recommended)", "description": "会读取 git rev-parse 输出"},
        {"label": "我手动输入 git-branch + commit-hash", "description": "适合没有本地仓库时"}
      ]
    }
  ]
}
```

命令模板：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --json goofy-deploy deploy-new \
  --channel-id <CHANNEL_ID> \
  --git-branch <BRANCH> \
  --commit-hash <COMMIT> \
  --site <cn|boe>
```

成功后拿到 `deploy_id` 后：
- **立即输出部署链接**（便于打开控制台查看进度）：
  - `cn`：`https://cloud.bytedance.net/goofydeploy/deployments/<DEPLOY_ID>`
  - `boe`：`https://cloud-boe.bytedance.net/goofydeploy/deployments/<DEPLOY_ID>`
- **输出对应的通道(channel)详细信息**：如果在部署过程中没有获取或展示过所选通道的详细信息，请在此处补充展示该 channel 的信息（如路由、灰度配置、名称、区域等），可使用 `list-channels --app-id <APP_ID>` 提取对应通道后进行展示。
- 立刻进入第 4 节查询。

### 3.2 deploy-version

如果用户不知道 `scm-version`：先让用户提供一个 `deploy-id`（通常是上一条成功部署），或改用部署历史辅助定位（需要 `app-id`）：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest goofy-deploy list-deployments \
  --app-id <APP_ID> \
  --page-num 1 --page-size 20 \
  --site <cn|boe>
```

执行回滚/部署已有版本：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --json goofy-deploy deploy-version \
  --channel-id <CHANNEL_ID> \
  --scm-version <SCM_VERSION> \
  --site <cn|boe>
```

## 4. 查询部署结果（拿到 deploy-id 后必须做）

目标：部署触发后并不代表最终成功；必须**每 30 秒**查询一次，直到到达终态（成功/失败/取消）或超时。


### 4.1 每 30 秒轮询（必须将结果输出到前台）

说明：
- 轮询间隔固定为 30 秒（满足定时查询要求）。
- 终态通常包括：`success` / `failed` / `cancelled`（以实际返回为准）。
- 超时后要明确告知用户“仍在进行中”，并给出继续查询命令。

当使用本 skill 触发部署（`deploy-new` / `deploy-version`）并拿到 `deploy_id` 后，**必须自动完成轮询直到终态或超时**。
为了确保轮询进度能**每隔 30s 获取部署过程并且将结果输出到前台**，**绝对不要**使用长时间占用的单次 Bash 调用（例如运行长耗时的循环脚本会阻塞对话，导致用户在几十分钟内看不到任何输出），也不要后台起进程去“拉日志”。**必须采用以下由大模型主导的“前台对话循环”方式**：

1) 单次查询命令（每次循环执行一次）：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --json goofy-deploy get-deployment \
  --deploy-id <DEPLOY_ID> \
  --site <cn|boe>
```

2) 轮询循环（由你主动每 30 秒重复一次“单次查询”）：
- 执行单次查询命令，并解析返回的 JSON 结果。
- 将当前的部署状态、时间等关键信息（字段见下方“输出要求”）**作为对话文本，直接输出回复给前台用户**，让用户看到实时进度。
- 若判定为终态（`endTime != null` 或 `status` 明确为 `success/failed/cancelled` 等）：立即停止循环，并进入最终汇总（第 5 节）。
- 若未到终态：使用 Bash 工具执行 `sleep 30` 等待 30 秒，等待完成后，再触发下一次“单次查询命令”，并重复此过程（直到到达终态或经过约 30 分钟超时）。

输出要求（轮询过程向用户的输出）：
- 每次轮询后，向用户输出的内容必须包含简明的结构化状态。例如：
  “第X次查询：状态为 `running`，channelId 为 `12345`，分支为 `feat/demo`... 等待 30s 后再次查询。”

输出要求（最终回复给用户）：
- 必须包含：`deploy-id`、`channel-id`、`status`、`scmName`、`scmVersion`、`branch`、`commit`、**部署链接**。

常见异常处理：
- 如果 `status=cancelled`：
  - 先让用户确认是否有人/系统取消（或通道策略不允许）
  - 再建议：用同一 `scmVersion` 走 `deploy-version` 重试，或检查通道权限/策略
- 如果 `Not authenticated`：回到第 0 节重新 `auth login`。

## 5. 最终输出格式（固定）

最终回复必须用以下结构（中文、简洁、可复制）：

- 站点：`<cn|boe>`
- app-id：`<APP_ID 或 - >`
- channel：`<CHANNEL_ID> (<CHANNEL_NAME 可选>)`
- 动作：`deploy-new | deploy-version | query`
- deploy-id：`<DEPLOY_ID 或 - >`
- 部署链接：`https://cloud.bytedance.net/goofydeploy/deployments/<DEPLOY_ID>`（boe 则替换域名为 `cloud-boe.bytedance.net`）
- 版本：`branch=<BRANCH>, commit=<COMMIT>, scmVersion=<SCM_VERSION>`
- 查询命令：`... goofy-deploy get-deployment --deploy-id <DEPLOY_ID> --site <cn|boe>`
