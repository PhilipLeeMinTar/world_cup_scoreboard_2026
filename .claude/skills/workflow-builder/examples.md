# Workflow Builder 生成示例

本文档展示使用 Workflow Builder 生成的完整 workflow 示例，帮助理解生成产物的结构和质量标准。

---

## 示例 1：数据库 Schema 迁移 Workflow

### 需求画像

| 项目 | 内容 |
|------|------|
| 名称 | db-migration |
| 场景 | MySQL 数据库 schema 变更的灰度迁移 |
| 触发条件 | 需要变更数据库表结构时 |
| 涉及系统 | MySQL (RDS)、DevFlow、Argos |
| 核心目标 | 安全地执行 schema 变更，支持灰度和回滚 |
| 阶段数 | 7 |

### 生成的阶段定义

| # | 阶段名 | 描述 | 可跳过 |
|---|--------|------|--------|
| 0 | info_collection | 收集迁移需求和目标表信息 | 否 |
| 1 | schema_review | 审核 SQL 变更脚本 | 否 |
| 2 | backup | 备份目标表数据 | 否 |
| 3 | canary_migrate | 灰度执行（单个 VDC） | 是 |
| 4 | full_migrate | 全量执行 | 否 |
| 5 | verify | 验证迁移结果 | 否 |
| 6 | completion | 清理临时资源 & 生成报告 | 否 |

### 流转图

```
info_collection → schema_review → backup → canary_migrate → full_migrate → verify → completion
                       ↑                                                      │
                       └──────────────────────────────────────────────────────┘
                       (验证失败时回退到 schema_review)
```

### Context 字段

| 字段名 | 类型 | 来源阶段 | 使用阶段 | 说明 |
|--------|------|----------|----------|------|
| db_name | string | info_collection | 全部 | 数据库名 |
| table_name | string | info_collection | 全部 | 目标表名 |
| sql_script | string | info_collection | schema_review, canary_migrate, full_migrate | DDL 语句 |
| backup_id | string | backup | verify, completion | 备份标识 |
| canary_vdc | string | info_collection | canary_migrate, verify | 灰度 VDC |
| all_vdcs | string[] | info_collection | full_migrate, verify | 全量 VDC 列表 |
| psm | string | info_collection | 全部 | 服务 PSM |

### 产出物

| 阶段 | 产出文件路径 | 完成检查条件 |
|------|-------------|-------------|
| info_collection | `info/migration_config.json` | 文件存在 |
| schema_review | `review/review_result.json` | 文件存在且 approved=true |
| backup | `backup/backup_info.json` | 文件存在且 backup_id 有效 |
| canary_migrate | `migrate/canary_result.json` | 文件存在且 success=true |
| full_migrate | `migrate/full_result.json` | 文件存在且 success=true |
| verify | `verify/verify_result.json` | 文件存在且 all_passed=true |
| completion | `summary/report.md` | 文件存在 |

### Skill 绑定

| 阶段 | 绑定 Skills | 用途 |
|------|------------|------|
| info_collection | rds_query | 查询目标表当前结构 |
| schema_review | (无) | AI 自主审核 SQL |
| verify | argos-query | 检查迁移后日志 |

### 生成的 SKILL.md（关键片段）

```markdown
### Phase 3: canary_migrate（灰度迁移）

> **目标**：在单个 VDC 上执行 schema 变更，验证安全性。

**入口条件**：`backup` 已完成

**跳过判断**：用户选择直接全量执行 → 标记为 `skipped`

**操作步骤**：

1. 从 `context.canary_vdc` 获取灰度目标 VDC
2. 在灰度 VDC 上执行 `context.sql_script`
3. 等待执行完成，检查执行结果
4. 简单验证：查询变更后的表结构确认变更生效

**退出条件**：SQL 执行成功 + 表结构验证通过

**产出文件**：`migrate/canary_result.json`（执行结果、影响行数、耗时）

> 完成检查：`canary_result.json` 存在且 `success` 为 true → 标记 completed
```

---

## 示例 2：安全审计 Workflow

### 需求画像

| 项目 | 内容 |
|------|------|
| 名称 | security-audit |
| 场景 | 对服务进行安全合规审计 |
| 触发条件 | 新服务上线前或定期审计 |
| 涉及系统 | Repotalk、IAM、TCC、Argos |
| 核心目标 | 检查服务代码和配置的安全合规性 |
| 阶段数 | 5 |

### 生成的阶段定义

| # | 阶段名 | 描述 | 可跳过 |
|---|--------|------|--------|
| 0 | info_collection | 收集审计目标和范围 | 否 |
| 1 | code_scan | 代码安全扫描 | 否 |
| 2 | config_audit | 配置安全检查 | 是 |
| 3 | permission_audit | 权限合规检查 | 否 |
| 4 | completion | 生成审计报告 | 否 |

### 流转图

```
info_collection → code_scan → config_audit → permission_audit → completion
                                (可跳过)
```

### Skill 绑定

| 阶段 | 绑定 Skills | 用途 |
|------|------------|------|
| code_scan | repotalk | 扫描代码仓库中的安全风险 |
| config_audit | tcc-query | 检查 TCC 配置安全性 |
| permission_audit | iam | 检查服务权限配置 |
| completion | (无) | 汇总生成报告 |

---

## 示例 3：微服务联调 Workflow

### 需求画像

| 项目 | 内容 |
|------|------|
| 名称 | service-integration |
| 场景 | 多个微服务间的联调测试 |
| 触发条件 | 跨服务功能开发完成后 |
| 涉及系统 | DevFlow、BAM、Argos、TCE |
| 核心目标 | 确保多服务协作链路正常 |
| 阶段数 | 6 |

### 生成的阶段定义

| # | 阶段名 | 描述 | 可跳过 |
|---|--------|------|--------|
| 0 | info_collection | 确认联调服务列表和环境 | 否 |
| 1 | env_check | 检查各服务部署状态 | 否 |
| 2 | contract_verify | 验证服务间接口契约 | 否 |
| 3 | chain_test | 链路联调测试 | 否 |
| 4 | log_analysis | 全链路日志分析 | 否 |
| 5 | completion | 联调报告 | 否 |

### 流转图

```
info_collection → env_check → contract_verify → chain_test → log_analysis → completion
                                                     ↑             │
                                                     └─────────────┘
                                                     (日志发现问题时回退)
```

### 特殊 Context 字段

| 字段名 | 类型 | 来源阶段 | 说明 |
|--------|------|----------|------|
| services | object[] | info_collection | 联调服务列表（含 PSM、branch、env） |
| upstream_psm | string | info_collection | 上游服务 PSM |
| downstream_psms | string[] | info_collection | 下游服务 PSM 列表 |
| test_endpoint | string | contract_verify | 联调入口接口 |

### Skill 绑定

| 阶段 | 绑定 Skills | 用途 |
|------|------------|------|
| env_check | tce, devflow | 检查各服务部署状态 |
| contract_verify | bam-api | 验证接口定义一致性 |
| chain_test | bam-query | 发起链路测试请求 |
| log_analysis | argos-query | 分析全链路日志 |

---

## 对比：base-workflow vs 生成的 workflow

| 维度 | base-workflow | 生成的 workflow |
|------|--------------|----------------|
| 阶段 | 固定 7 个阶段 | 用户自定义（数量、名称、顺序） |
| 流转 | 固定线性 + testing→coding 回退 | 自定义（线性、分支、回退、循环） |
| Context | 固定字段（PSM、branch、env...） | 按需定义，字段来源和使用关系清晰 |
| Skill 绑定 | 固定绑定 devflow、edit-idl 等 | 按阶段灵活绑定 |
| 产出物 | 固定文件结构 | 按阶段自定义 |
| 核心不变 | — | status.json 驱动、四拍节奏、session 隔离、断点恢复 |
