# Experiment Setting Judgement and Framework Organization

This rule decides how to organize the `功能测试` skeleton when the input
document contains A/B experiment settings. It applies to BOTH generation
styles (`Follow the input` and `Analyze by PRD2Case`), and should be consulted
right before you start drafting the framework.

## Table of Contents

- 1. Experiment Setting (A/B Settings) Cases
- 2. Ask for user confirmation (case2 / case3 only)
- 3. Framework skeletons
  - case1 — No experiment
  - case2-A — One experiment, full function per group
  - case2-B — One experiment, shared-logic extracted
  - case3-A — Multiple experiments, full function per group
  - case3-B — Multiple experiments, shared-logic extracted per experiment
- 4. How this rule is consumed per generation style

Execution order:
1. Classify the input into one of the three cases below.
2. If the case is `case2` or `case3`, evaluate the shared-logic condition and
   ask the user only when it is met.
3. Pick the framework skeleton based on the case + user choice.

## 1. Experiment Setting (A/B Settings) Cases

- **case1 — No experiment**: No experiment info in the context, or only an
  empty `A/B Settings` section with no real content.
- **case2 — One experiment with multiple groups**: The context usually does
  not say "one experiment" explicitly; it simply lists the groups (v0/v1/...)
  and their logic.
- **case3 — Multiple experiments with multiple groups**: Several experiments,
  each with multiple groups.

## 2. Ask for user confirmation (case2 / case3 only)

**Why this question exists**: when groups share the same main logic and only
differ in small ways (UI style, copy, reward amount, etc.), some users want
every group re-validated end-to-end, while others prefer a single shared
section plus per-group diffs. Both shapes are legitimate, so the agent must
ask instead of guessing.

**Trigger condition (all must hold):**
- The case is `case2` or `case3`.
- Groups share the same main logic / functions.
- Differences are localized — e.g. different UI style, different copy,
  different reward amounts. If groups differ in core flow, feature entry, or
  produce materially different end states, treat it as "not minor": skip the
  question and default to Option A.

**Question** (use `AskUserQuestion` / `AskQuestion`, or the nearest equivalent
tool available in the current agent):

- **Option A** — Validate the full function under each group (repeat the
  whole feature tree per group). Matches skeletons `case2-A` / `case3-A`
  below.
- **Option B** — Keep one shared "common logic" section, and only put
  group-specific differences under each group. Matches skeletons `case2-B` /
  `case3-B` below.
- **Option C** — The user describes another structure; follow that
  description and keep it consistent with `references/test_case_grammar.md`.

Do NOT ask this question for `case1`, or when groups have no real shared
logic (the question would be meaningless — just use Option A).

## 3. Framework skeletons

> The examples only show the skeleton. Fill in real module/feature nodes
> according to the input document.

### case1 — No experiment

```
# 功能测试
// ... 直接开始测试场景梳理
```

### case2-A — One experiment, full function per group

Group name MUST include the experiment group identifier (e.g. v0, v1, v2).

```
# 功能测试
## $分组名称1（比如v0）
### xxx
#### xxx
**测试内容** xxx
## $分组名称2（比如v1）
### xxx
#### xxx
**测试内容** xxx
```

### case2-B — One experiment, shared-logic extracted

```
# 功能测试
## 实验共性逻辑
### xxx
**测试内容** xxx
## $分组名称1（比如v0）差异点
### xxx
**测试内容** xxx
## $分组名称2（比如v1）差异点
### xxx
**测试内容** xxx
```

### case3-A — Multiple experiments, full function per group

For each experiment, expand functional points under every group.

```
# 功能测试
## 实验1: $实验内容
### $分组名称1
#### xxx
##### xxx
**测试内容** xxx
### $分组名称2
#### xxx
##### xxx
**测试内容** xxx
## 实验2: $实验内容
### $分组名称1
...
### $分组名称2
...
```

### case3-B — Multiple experiments, shared-logic extracted per experiment

```
# 功能测试
## 实验1: $实验内容
### 实验1 共性逻辑
**测试内容** xxx
### $分组名称1 差异点
**测试内容** xxx
### $分组名称2 差异点
**测试内容** xxx
## 实验2: $实验内容
### 实验2 共性逻辑
**测试内容** xxx
### $分组名称1 差异点
**测试内容** xxx
### $分组名称2 差异点
**测试内容** xxx
```

## 4. How this rule is consumed per generation style

The case + user-choice decision produced by sections 1–2 is applied
differently depending on the active `Generation Style`:

- **Follow the input**: The current agent drafts the framework itself, so
  the skeletons in section 3 are used directly.
- **Analyze by PRD2Case**: The framework is produced by a downstream,
  context-independent agent that only consumes `<prd>`, `<function>`, and
  `<experiment>` (i.e. the content of `experiment_setting.md`). That
  downstream framework-generation step only supports the default Option-A
  shape unless the chosen structure is encoded explicitly, and is unaware of the Option A / B / C confirmation concept.
  Therefore the current agent must encode the case + user-choice outcome
  **into `experiment_setting.md`**, so the downstream agent naturally
  reproduces the intended shape. See
  `analyze_by_prd2case_sub_workflow.md` step2 for the exact file layout
  per option.
