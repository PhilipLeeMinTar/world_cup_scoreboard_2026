# Analyze by PRD2Case Sub-Workflow

## Table of Contents

- Global Prerequisite
- Principle
- Procedure to use API in this workflow
- Workflow
  - step0: Ensure dir
  - step1: Test Analysis
  - step2: A/B Experiment Analysis
  - step3: Test Framework Generation
  - step4: Detailed test case generation

## Global Prerequisite
- Before executing this workflow, the agent MUST complete the Version Gate defined in `skills/prd2case/SKILL.md`.
- If Version Gate is not completed, stop immediately and do not continue this workflow.

## Principle
- If a step is marked as `Execute by API`, call the corresponding PRD2Case MCP tool first, **DO NOT generate it manually unless a later step explicitly defines a fallback**.
  - Why: the API output schema is a downstream contract (later steps/tools/scripts expect specific fields and structure).
  - If violated: downstream steps may fail to read/merge results or produce inconsistent cases. Stop and redo the step via the MCP tool.
- Keep all generated artifacts as markdown or JSON files inside `$SESSION`, and do NOT generate HTML preview files in this workflow.
- The MCP call may take a few minutes to finish. Wait for the tool result and do not replace the step with manual generation unless this workflow explicitly defines a failure fallback for that step.
- Execute **STEP BY STEP**. !!NEVER!! jump steps or merge commands.
  - Why: each step defines explicit inputs/outputs and acts as an audit checkpoint; later steps depend on the intermediate artifacts.
  - If violated: required `$SESSION/step_results/*` artifacts may be missing, making the run unreproducible. Stop and backfill the skipped steps before proceeding.

## Procedure to use API in this workflow
0. Input identification: In each step, treat this step as a function call, there will be input definitions in each step.
1. Prepare the required input files under `$SESSION`.
2. Call the corresponding PRD2Case MCP tool with file paths, let the tool read local files, and write the result into the specified file in `$SESSION/step_results`.

## Workflow
### step0: Ensure dir
- `$SESSION/step_results`
- Ensure the source analysis document is stored at the canonical path expected by this workflow.
- If it was exported by [MCP Tool] `prd2case.read_lark_doc`, pass `$SESSION` as `export_dir` in the MCP call. Do not pass `$SESSION/input_document/` itself as `export_dir`, because the tool creates the canonical document directory under the export root.
- For all later API calls in this workflow, use `$SESSION/input_document/content.md` as the canonical file path for the exported document body.

### step1: Test Analysis
**Execute by API**
- Input file: the original `test_analysis.md` or the canonical `$SESSION/input_document/content.md`
- Use [MCP Tool] `prd2case.requirement_analysis` with:
  - `input_document_path="<input_document_path>"`
  - `output_path="$SESSION/step_results/test_analysis_by_prd2case.json"`
- Result file: `test_analysis_by_prd2case.json`

### step2: A/B Experiment Analysis
**NOT Execute by API**, Do it yourself

- [**FORCE**] Read `references/ab_setting_rule.md` to classify the case and,
  when applicable, run the user-confirmation question defined there
  (Option A / B / C).
- Classification result must be one of: `No experiment`, `Single Experiment`,
  `Multi Experiments` (mapped to case1 / case2 / case3 in the rule).
- The downstream framework-generation agent is context-independent and only
  consumes `experiment_setting.md`. It does NOT know about the Option
  A / B / C concept, so the chosen option must be baked into the file
  content using the layouts below.
- Save the result to `$SESSION/step_results/experiment_setting.md`.

**Layout — case1 (No experiment)**
```
## 实验判定
- 结论: No experiment
## 实验详情
- 无
## 框架组织提示
- 不需要按实验或分组拆分
```

**Layout — case2 / case3 + Option A (full function per group, default)**
```
## 实验判定
- 结论: Single Experiment  # 或 Multi Experiments
## 实验详情
- v0: $brief_logic
- v1: $brief_logic
## 框架组织提示
- 每个实验分组均需完整展开功能点（每组独立验证全部功能）
```

**Layout — case2 / case3 + Option B (shared logic extracted)**
```
## 实验判定
- 结论: Single Experiment  # 或 Multi Experiments
## 实验详情
- 共性逻辑: $shared_main_logic
- v0 差异点: $diff_from_shared
- v1 差异点: $diff_from_shared
## 框架组织提示
- 组间主逻辑相同，仅在列出的差异点上有区别
- 框架请按「共性逻辑」一节 + 各分组「差异点」一节组织
- 禁止在每个分组下重复展开共性逻辑
```

> 对于 `Multi Experiments` + Option B，按每个实验单独写一段
> `实验详情` + `框架组织提示`，让每个实验自己有一套共性逻辑与差异点。

**Layout — Option C (user-specified structure)**
```
## 实验判定
- 结论: Single Experiment  # 或 Multi Experiments
## 实验详情
- <按用户描述整理>
## 框架组织提示
- 按用户指定结构组织: <user's description>
- 需满足 references/test_case_grammar.md 的编写规范
```

### step3: Test Framework Generation
**Execute by API**

- Input files
  - the original `test_analysis.md`, or `$SESSION/input_document/content.md` when the source document came from the canonical Lark export directory, as input_document_path
  - `step_results/test_analysis_by_prd2case.json` as test_analysis_path
  - `step_results/experiment_setting.md` as experiment_setting_path

- Use [MCP Tool] `prd2case.framework_generation` with:
  - `input_document_path="<input_document_path>"`
  - `requirement_analysis_result_path="<test_analysis_path>"`
  - `experiment_setting_path="<experiment_setting_path>"`
  - `output_path="$SESSION/step_results/framework.md"`
- Result file: `framework.md`
- Keep `framework.md` as the markdown artifact for later review; do not generate any HTML view for it.

### step4: Detailed test case generation
**Execute by API**

- Input files
  - the original `test_analysis.md`, or `$SESSION/input_document/content.md` when the source document came from the canonical Lark export directory, as input_document_path
  - `step_results/framework.md` as framework_path
  - `step_results/test_analysis_by_prd2case.json` as test_analysis_path

- Use [MCP Tool] `prd2case.detailed_case_generation` with:
  - `input_document_path="<input_document_path>"`
  - `framework_path="<framework_path>"`
  - `requirement_analysis_result_path="<test_analysis_path>"`
  - `output_path="$SESSION/test_case.md"`
- Append `case_mode="<mode>"` if the decided `case_mode` is not `General`.

- Failure fallback for this step only:
  - If [MCP Tool] `prd2case.detailed_case_generation` fails after retrying, the agent MUST generate the detailed test cases manually.
  - Manual generation MUST still use the same three inputs of this step as the source of truth:
    - the original input document
    - `step_results/framework.md`
    - `step_results/test_analysis_by_prd2case.json`
  - Keep the generated result aligned with the framework structure and write it to the same canonical output path: `$SESSION/test_case.md`
  - Before writing the manual result, explicitly tell the user that the MCP detailed-case step failed and that the workflow is falling back to model-generated detailed cases for this step.
  - Do not overwrite any successful API result with a manual rewrite. Use the fallback only when the API result is unavailable for this step.

- Read `.prd2case_preference.md` to fetch default `case_mode`, if the context clearly suggests a different one, ask the user to confirm.
- The result should be written in `$SESSION/test_case.md`, NOT `$SESSION/step_results/test_case.md`
- Hand off the generated `$SESSION/test_case.md` to the standard Bits upload stage; that stage will convert it to `$SESSION/test_case.json` first, then upload with `case_form=json`. Do not generate any HTML preview for it.
