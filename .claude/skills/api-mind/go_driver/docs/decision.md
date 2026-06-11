# go_driver Reuse / Amend / New 决策

本文件在 Go generate 阶段需要做用例分流时读取。

## 1. IDL 与接口形态获取

- 全新接口：优先读取 `erd.md` → 本地特性分支 `conf/.idl/` → 线上平台查询（`bam-api` skill）。
- 存量接口：优先查找本地 `conf/.idl/` → 线上平台查询（`bam-api` skill）。
- 未找到任何定义时，触发审计记录并请求用户确认；严禁使用假想字段拼凑接口模型。

## 2. 请求数据构造策略

- `explicit`：严格以 `case.md` 为准；未赋值字段触发审计并请求用户确认。
- `resource_ref`：必须调用提供方接口查询提取，或遵循知识库规范；严禁随意传 `[0]` 或写死假 ID。
- `dynamic_construct`：唯一约束 / 时间戳 / 名称等每次运行刷新的字段，必须使用 `apitest` Helper，如 `UniqueName` / `NowMilli` / `RandString`。
- `env_business_sample`：使用包级 `envSamples` 与 `apitest.Sample` 动态加载，支持多环境切换。

## 3. 分流定义

- **New**：增量业务且无基准覆盖，使用模板全新生成。
- **Amend**：已有基准覆盖但需因需求变更调整，采用最小文本 Diff，仅变更目标范围。
- **Reuse**：目标代码已完全覆盖测试诉求，无需更新，仅记录标记并参与运行。

实际操作时同时参考 `../resources/reuse_amend_guide.md`，并生成 / 更新 `triage.yaml`。
