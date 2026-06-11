---
name: api-test
description: Automatically manage the lifecycle of API testing. Supports stateful re-entrancy. Generate from scratch, Modify existing cases, Execute, Full-Pipeline, or Resume interrupted workflows.
---

## User Input

```text
$ARGUMENTS
```
You **MUST** consider the user input before proceeding (if not empty).

If the given `$ARGUMENTS` contains a link, you need to read the content of the link (use lark-docs mcp if it's a lark doc) and replace the link with content.

## Context
**Read context before Executing**:
1. Language Setting
   - Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing). **IMPORTANT** **Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: generated documents (specs, plans, tasks), interactive prompts, confirmations, status messages, and error descriptions.** 

## Phase 0: State Discovery (Mandatory First Step)
Before planning or classifying the task, you MUST check the current state of the workspace for the target PSM:
1. Identify if `FEATURE_DIR/test/{PSM}/api_test_checklist.md` exists. If it exists, read its content to identify any pending `[ ]` items.
2. Check if `FEATURE_DIR/test/{PSM}/api_test_case.yaml` exists.
3. Check if `FEATURE_DIR/test/{PSM}/.env` exists.

## Phase 1: Task Classification (Routing)
Analyze the User Input and the Phase 0 State Discovery results to strictly classify the task into ONE of the following modes:

- **Mode R: Resume** (User asks to "continue", "proceed", OR user provides no specific instruction but there are pending `[ ]` items in the existing checklist).
- **Mode M: Modify/Update** (User wants to update, add, or fix specific parameters/cases in an existing `api_test_case.yaml`).
- **Mode A: Generate Only** (User explicitly wants to generate test cases/data from scratch. If cases already exist, you MUST ask for confirmation to overwrite unless user specifically forced it).
- **Mode B: Execute Only** (User wants to run existing test cases and generate reports).
- **Mode C: Full Pipeline** (User wants to generate test cases AND execute them).

**Prerequisite Validations**:
- For **Mode B**: You MUST verify `api_test_case.yaml` exists and is populated. If not, halt and prompt the user to Generate (Mode A) first.
- For **Mode M**: You MUST verify `api_test_case.yaml` exists. If not, gracefully fallback to Mode A and inform the user.
- **Figure out PSM**: Analyze User Input to figure out the PSM. If missing, ask the user. If multiple PSMs, create independent parallel sub-tasks and execute them concurrently without interference.

## Phase 2: Workflow Checklist Management
Manage the checklist file at `FEATURE_DIR/test/{PSM}/api_test_checklist.md`.
**CRITICAL RULES**:
- **If Mode R (Resume)**: Do NOT append new templates. Simply use the existing checklist and resume execution starting from the very first pending `[ ]` item.
- **If Mode M, A, B, or C**: Use **append mode**. If the checklist exists, **append** the new Mode-specific section to the end of the file. Do NOT overwrite or delete previous completed `[x]` items. 

### Checklist Templates (Append ONLY the selected section if not Mode R)

<!-- Include this section ONLY if Mode is A or C -->
## Part 1: Test Case Generation
- [ ] Setup: Install/Reinstall `api-mind` tool and read `scripts/api-mind.md`.
- [ ] Setup: Verify `spec.md`, `task.md`, `case.md` exist.
- [ ] Setup: Generate/Update `.env` based on `task.md`.
- [ ] Setup: Generate skeleton `api_test_case.yaml` based on `case.md`.
- [ ] Setup: Inquire user for Knowledge Base (skill name, local path, or skip) and wait for response.
- [ ] Generation: Get X-Jwt-Token by running `gdpa-cli login -p cn` (use the token from the CLI output / login flow).
- [ ] Generation: Establish Data Correlation & Knowledge Constraints, then update `api_test_case.yaml`.
- [ ] Generation: Use `api-mind generate-param` to generate test data, apply constraints/overrides, then update `api_test_case.yaml`.

<!-- Include this section ONLY if Mode is M (Modify) -->
## Part X: Test Case Modification
- [ ] Modify: Read existing `api_test_case.yaml` and understand the structure.
- [ ] Modify: Parse user's specific modification instructions (e.g., change user_id to 999, add a new edge case).
- [ ] Modify: Apply targeted updates to `api_test_case.yaml` without destructing unaffected cases.

<!-- Include this section ONLY if Mode is B or C -->
## Part 2: Test Case Execution & Reporting
- [ ] Preparation: Install/Reinstall `api-mind` tool if not already done.
- [ ] Preparation: Verify `api_test_case.yaml` exists. (If not done yet, get X-Jwt-Token by running `gdpa-cli login -p cn`.)
- [ ] Assess Risk: Check environment safety (boe/localhost vs ppe/prod) and test accounts.
- [ ] Assess Risk: Check for write operations (POST/PUT/DELETE) in test cases.
- [ ] Assess Risk: Obtain user confirmation to continue if the environment is unsafe and contains write operations.
- [ ] Execution: Use `api-mind test-exec` to execute cases and save logs.
- [ ] Reporting: Read `resources/test_report_guide.md` and generate `test_report.md`.

*Note: Update the checklist file (change `[ ]` to `[x]`) whenever an item is completed.*

## Phase 3: Detailed Execution Instructions
*Execute strictly according to the pending `[ ]` items in your checklist.*

### Instructions for Part X: Modification (If Mode M)
1. Safely read `api_test_case.yaml`.
2. Apply changes strictly as requested by the user. Do not recreate the file from scratch.
3. Save the modified YAML and verify syntax correctness.

### Instructions for Part 1: Generation (If applicable)
1. **Setup**: Install `api-mind`. Verify `spec.md`, `task.md`, `case.md` exist. Generate `.env` (from `resources/env_template.md`) and skeleton `api_test_case.yaml` (from `resources/test_case_template.md` with empty params/body).
2. **Knowledge Base Inquiry**: Use `AskUserQuestion` tool to ask: *"Before generating test data, could you provide a knowledge base? (skill name / local path / skip)"* **Halt execution and wait for the user's response.**
3. **Data Correlation & Generation**: Obtain JWT by running `gdpa-cli login -p cn` and use that token for downstream steps. Analyze IDL and user-provided Knowledge Base to extract mandatory values, enum constraints, and DB dependencies. Update `api_test_case.yaml`. Run `api-mind generate-param` and merge results with manual overrides.

### Instructions for Part 2: Execution & Reporting (If applicable)
1. **Assess risk**: 
   - Safe if domain contains "boe" or "localhost" OR if test account is provided. Unsafe if "ppe".
   - Write operations exist if API method is POST/PUT/DELETE or name implies modification.
   - If unsafe AND has write operations: **Halt and prompt user** for a safe environment/account (via `.env` modification), then redo Risk Assessment.
2. **Execute**: Run `./api-mind test-exec [FEATURE_DIR/test/{PSM}/api_test_case.yaml] --token [X-Jwt-Token] --env-file [FEATURE_DIR/test/{PSM}/.env] --log-dir [FEATURE_DIR/test/{PSM}/api_test_logs/]`
3. **Report**: Parse test results based on `resources/test_report_guide.md` and output `test_report.md` (overwrite if exists).

## Strict Constraints
1. **No Premature Confirmation**: You are strictly prohibited from changing `[ ]` to `[x]` before the task is actually finished and the deliverable is validated.
2. **Proof of Completion**: Every `[x]` must correspond to a tangible deliverable successfully provided in your current response.
3. **Strict Sequential Single-Step Execution**: In each response, you must execute exactly ONE pending item (`[ ]`) from the checklist, strictly top to bottom. Do not skip ahead or batch multiple interactive steps.
4. **State Persistence**: Never blindly overwrite `api_test_case.yaml` or `.env` without user consent if they already contain valid data, unless explicitly in Generate mode and confirmed.
5. **NEVER USE CURL**: Strictly use `api-mind` to test cases.
6. **DO NOT EDIT `.env` DIRECTLY**: Prompt the user to edit it if environment/credential adjustments are needed.