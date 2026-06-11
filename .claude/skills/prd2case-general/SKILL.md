---
name: prd2case-general
description: "Guide for test case generation and related operations and rules. Use this skill when you need to generate (write), modify, read (from Bits) and save (to Bits) test cases."
---

# PRD2Case

## MCP Prerequisite Gate

- This skill depends on the PRD2Case MCP server.
- Before starting any workflow, the agent MUST check whether the `prd2case` MCP is actually available in the current environment.
- If the MCP tool is unavailable, the agent MUST NOT continue the workflow by pretending the MCP exists. Instead, follow `references/mcp_setup.md` to set it up in the current agent runtime.

## Path Conventions

- `$SKILL_DIR` means the absolute path of the current skill root directory, i.e. the directory containing this `SKILL.md`.
- The agent MUST resolve `$SKILL_DIR` from the current skill location instead of assuming the current working directory.
- Script examples under `references/` that use `$SKILL_DIR/...` are defined relative to this skill root.

## Overview
- Standard outline: If the user simply ask you to generate test cases based on some input(Lark URL, existing local markdown files), follow the standard outlines step by step.
- Non-standard: For other use cases, use the relevant tools and follow the closest matching sub-workflow under `references/` (e.g. coverage rate, PRD2Case analysis).

## References Index
Read each reference file only when the corresponding trigger applies. Do not preload any of them.

| File | When to read |
| --- | --- |
| `references/mcp_setup.md` | When PRD2Case MCP is unavailable and setup/configuration is required. |
| `references/preference_template.md` | Stage-0, or when detecting template field drift against local `.prd2case_preference.md`. |
| `references/case_generation_workflow.md` | Standard case generation in Stage-2 of the Standard Outline. |
| `references/analyze_by_prd2case_sub_workflow.md` | Inside case generation when `Generation Style = Analyze by PRD2Case`. |
| `references/test_case_grammar.md` | Before writing or validating any markdown test case, and whenever `scripts/case_grammar_check.py` reports issues. |
| `references/ab_setting_rule.md` | When the input contains A/B experiment settings and you need to decide the framework layout. |
| `references/combination_test_proposal_workflow.md` | When the user asks for a combination-test proposal / test matrix / 参数组合测试建议, BEFORE generating formal cases. |
| `references/coverage_rate_workflow.md` | When the user asks to compute AI-vs-human case coverage. |
| `references/prune_case_set_workflow.md` | When the user asks to prune the current case set for regression-suite inclusion. |

## Standard Outline

### Stage-0: Session initialization
- Make sure dir: `$PROJECT_ROOT/sessions/`, where `$PROJECT_ROOT` is usually your working dir.
- At the start of every task, you MUST create the session folder under `$PROJECT_ROOT/sessions/`.
Session folder name must use suffix format `yyyymmdd-hhmmss` (example: `session-20260325-153045`), and all related result files should be stored there.

```
sessions/<session-yyyymmdd-hhmmss>/
├── input_document/
│   ├── content.md
│   └── assets/
├── test_analysis.md
├── test_case.md
├── test_case.json
└── meta.yaml // store session related information, like input_document url, input_document dir, case_id, Bits case url, knowledge_base_path, and customized_skill_path
```

### Stage-1: Read User preference
- Find and read `.prd2case_preference.md` located in your working dir.
- If not found, create one in your working dir from `references/preference_template.md`.
- Compare the local `.prd2case_preference.md` with `references/preference_template.md`; ask the user to update it only when template fields were added or removed.
- Resolve `Knowledge Base Path` and `Customized Skill Path`, then write them into `$SESSION_DIR/meta.yaml`:
  - If the configured value is an empty string: write an empty value.
  - If the configured value is a local directory path and it exists: write the path value as-is.
  - If the configured value is a path but it does not exist: write an empty value, and explicitly tell the user the path is invalid.
  - If the configured value is `NEED_TO_BE_CONFIGURED` (after trimming whitespace and stripping surrounding markdown backticks):
    - Hard gate: the agent MUST ask the user to choose, and MUST STOP the workflow and wait for the user's answer. Do NOT silently treat `NEED_TO_BE_CONFIGURED` as empty, and do NOT proceed to Stage-2 before the user answers.
    - Choices:
      - Fill a correct path: write the chosen path back to `.prd2case_preference.md` and write it to `meta.yaml`.
      - Set to empty: update `.prd2case_preference.md` to an empty value and write an empty value to `meta.yaml`.
      - Keep `NEED_TO_BE_CONFIGURED`: keep `.prd2case_preference.md` unchanged and write an empty value to `meta.yaml` (so the next run can ask again).
- Output requirement for this stage:
  - Report whether the preference file existed or was newly drafted.
  - Report whether any template fields were added/removed and whether a user confirmation is required.
  - Report the values written to `meta.yaml` for `knowledge_base_path` and `customized_skill_path`.


### Stage-2: Test case generation
- Read `references/case_generation_workflow.md` (force reload), and follow its instructions.
- Generate the initial `test_case.md`


### Stage-3: Initial upload to Bits
- After generating the initial `test_case.md`, convert it to `$SESSION_DIR/test_case.json` first, then upload the JSON result to Bits immediately.
- Standard conversion command:
```bash
python3 $SKILL_DIR/scripts/case_form_transfer.py "$SESSION_DIR/test_case.md" -o "$SESSION_DIR/test_case.json"
```
- If the standard session contains `$SESSION_DIR/input_document/assets/meta.yaml`, you MAY append:
```bash
--image-meta-yaml "$SESSION_DIR/input_document/assets/meta.yaml"
```
- Use the converted `$SESSION_DIR/test_case.json` as the upload payload for the standard `prd2case` flow.
- Use `create` logic for this first upload: DO NOT pass `case_id`.
- Save the API response to `$SESSION_DIR/save_result.json`, and record the created `case_id` and case URL in the session metadata for later updates.
- After uploading, explicitly notify the user of the Bits case URL.
- Explicitly remind the user: if they modify the case on the Bits page, they MUST say so in the next turn before asking for more updates.

Mandatory: Ask for Meego story association before the initial upload
- This is a hard gate before the first `create` upload to Bits: ALWAYS STOP and ASK the user whether they want to associate a Meego story.
- Explain the constraint explicitly: Meego association must be attached during the initial Bits creation request, and cannot be added afterward by updating the same case.
- If the user provides the Meego story URL (e.g., `https://meego.larkoffice.com/projectKey/*/*/workItemId?...`), extract from the URL:
  - `projectKey`: the first path segment after the domain (example: `tiktok`).
  - `workItemId`: the trailing numeric path segment (example: `6731326613`).
- Pass them explicitly to [MCP Tool] `prd2case.save_case_to_bits` as `meego_project_key` and `meego_work_item_id`.
- Example fields: `case_form=json`, `case_title="xxx"`, `user_name="your_name"`, `meego_project_key=tiktok`, `meego_work_item_id=6731326613`

### Stage-4: Update loop
- After the initial upload, continue the conversation in an update loop until the user tells you to stop.
- Keep the local working copy in `$SESSION_DIR/test_case.md`, and treat the created Bits case as the remote source that should stay synchronized with this session.
- If the user says they modified the case on Bits，follow the following steps:
  1. Fetch the latest remote case from Bits by using [MCP Tool] `prd2case.read_bits_case`
  2. Convert the fetched JSON to markdown.
  ```bash
  python3 $SKILL_DIR/scripts/case_form_transfer.py "$SESSION_DIR/latest_bits_case.json" -o "$SESSION_DIR/latest_bits_case.md" --drop-root
  ```
  3. Compare the converted markdown with the current local `test_case.md` to understand what changed.
  ```bash
  git --no-pager diff --no-index --patience "$SESSION_DIR/test_case.md" "$SESSION_DIR/latest_bits_case.md"
  ```
  4. After understanding the differences, replace `$SESSION_DIR/test_case.md` with `$SESSION_DIR/latest_bits_case.md`.
- If the user asks you to modify the case content:
  1. Edit the latest local working copy.
  2. Convert the edited `$SESSION_DIR/test_case.md` to `$SESSION_DIR/test_case.json` by following the same standard conversion rule in Stage-3.
  3. Upload the converted JSON by passing the existing `case_id` created in this session, so the same Bits case is updated in place.
- Only create a new Bits case again if the user explicitly asks for a new/forked case instead of updating the current one.


## Non-standard Procedures
Typical non-standard tasks asked by users are listed below. Follow the mapped section/reference instead of improvising a new workflow.

| Task | Primary reference / section | Scripts / tools | Notes |
| --- | --- | --- | --- |
| Analyze test cases based on context in this session | `Stage-4: Update loop` in this file | [MCP Tool] `prd2case.read_bits_case`, `scripts/case_form_transfer.py`, [MCP Tool] `prd2case.save_case_to_bits` | Reuse the normal sync/update flow. Keep the corresponding Bits case synchronized when needed. |
| Generate test case based on a template test case | `references/case_generation_workflow.md` and `references/test_case_grammar.md` | `scripts/case_grammar_check.py` | Treat the template case as additional context and important reference, not as a replacement for the workflow or grammar rules. |
| Prune the current test case set for inclusion in the regression test suite | `references/prune_case_set_workflow.md` | Local markdown editing and PRD2Case MCP tools when Bits sync is needed | This is an agent-assisted/manual workflow. Ask the user for explicit prune criteria first. |
| Calculate coverage rate (AI cases cover human cases) | `references/coverage_rate_workflow.md` | `scripts/coverage_rate.py`, `scripts/case_form_transfer.py`, PRD2Case MCP tools | Compute coverage and produce a Bits visualization of covered/uncovered expectations. |
| Propose combination-test scenarios / test matrix / 参数组合测试方案 | `references/combination_test_proposal_workflow.md` | No dedicated script required | Output the proposal first, and do NOT generate formal test cases unless the user explicitly asks for that next step. |


## Available Tools

Use PRD2Case MCP tools as the primary toolset. Agents MUST prefer MCP tools whenever they are available. Use local HTTPS script tools only as a fallback when MCP is unavailable.

### Primary tools: PRD2Case MCP
- [MCP Tool] `prd2case.read_bits_case`: use when the workflow needs to fetch an existing Bits case for reading, syncing, diffing, coverage analysis, or follow-up updates.
- [MCP Tool] `prd2case.save_case_to_bits`: use when the workflow needs to create a new Bits case or update an existing Bits case from the current session files. In the standard `prd2case` flow, prefer converting `test_case.md` to `test_case.json` first, then upload with `case_form=json`.
- [MCP Tool] `prd2case.read_lark_doc`: use when the user provides a Lark/Feishu document and the workflow needs to export it into a local canonical document directory. The standard layout is `<document_dir>/content.md` plus `<document_dir>/assets/` for mounted images and other local resources. By default the MCP creates `input_document/`; when another workflow needs a different directory name under the same `export_dir`, pass `folder_name`.
- [MCP Tool] `prd2case.requirement_analysis`: use in `Analyze by PRD2Case` flow when the input should first be analyzed as a PRD or augmented PRD.
- [MCP Tool] `prd2case.framework_generation`: use in `Analyze by PRD2Case` flow after requirement analysis to generate the case framework.
- [MCP Tool] `prd2case.detailed_case_generation`: use in `Analyze by PRD2Case` flow after framework generation to generate the detailed test cases.

### Fallback tools: local HTTPS scripts
- `scripts/case_management.py`: HTTPS equivalents for reading Bits cases and saving cases to Bits
- `scripts/lark2md.py`: HTTPS export of Lark/Feishu documents to markdown
- `scripts/call_prd2case_api.py`: HTTPS entry points for PRD analysis, framework generation, and detailed case generation
