# Instruction for Test Case Generation

## Table of Contents

- Global Prerequisite
- Workflow overview
- step0. Input Confirmation
- step1. Generation Style Confirmation
  - Read preference
  - Judgement rule
- step2. Context Gathering
- step3. Test Case Generation
  - 3-1 Generate with style: `Analyze by PRD2Case`
  - 3-2 Generate with style: `Follow the input`

## Global Prerequisite
- Before executing this workflow, the agent MUST complete the Version Gate defined in `skills/prd2case/SKILL.md`.
- If Version Gate is not completed, stop immediately and do not continue this workflow.

## Workflow overview

Use the available tools to create the TODO list below, and finish it step by step.

```
- [] step0: Input Confirmation: Display the input you acquired from context to the user
  - Finish the step and display result to user.
  - Stop and wait for user confirmation

- [] step1: Generation Style Confirmation: Identify the `Test Analysis` and decide the generation style
  - Finish the step and display result to user.
  - Do NOT ask the user to confirm the generation style

- [] step2: Context Gathering: Read context paths from `$SESSION_DIR/meta.yaml` and gather usable local context

- [] step3: Test Case Generation: Generate test cases based on `Generation Style`
  - Framework generation
  - Save the generated framework as markdown and review it directly from the session files when needed
  - Detailed case generation
  - Finish with the generated `test_case.md`; the standard workflow will first convert it to `test_case.json`, then upload it to Bits immediately after generation
```

## step0. Input Confirmation

Go through the working dir, check whether the documents/sources below are available:

[ ] Input document (Required)
[ ] Customized business flow identifier, such as `UG-PA` (Optional; only needed when the downstream generation task itself requires a specific customized flow. Path handling alone does not make it required)
[ ] Other input(Optional): PRD, Tech design, spec.md, Codebase, Figma

Show the check result to the user, and ask the user to provide additional information if the required input is missing.

If the input document was exported from Lark/Feishu via MCP:
- pass the session directory as `export_dir` in the MCP call, not the final `input_document/` directory itself
- expect the exported canonical document directory to appear at `$SESSION_DIR/input_document/`
- read the document body from `input_document/content.md`
- do not rely on the default title-based exported filename

## step1. Generation Style Confirmation

### Read preference

Read `.prd2case_preference.md` to understand user preference:

- If user has a specific preference, follow it.
- If the user prefers `Decide by Agent`, follow the judgement rule in the next section.

### Judgement rule

**Follow the input**

- To generate with style: `Follow the input` (Try to follow the structure and content of input document, just do necessary modifications.)
- If the `Test Analysis` doc is written in style below:
  - Contains a `Test case`/`Case`/`Detailed Case` or similar sections
  - Contains a decomposition of functional modules and test content or detailed test cases(前置条件/操作步骤/预期结果)

**Analyze by PRD2Case**

- To generate with style: `Analyze by PRD2Case` (Treat the input as a PRD or augmented PRD, use the PRD2Case's standard analysis -> framework generation -> detailed case generation process.)

- If the `Test Analysis` is more about describing the functions, and is more likely an augmented Product Requirement Document(PRD)

## step2. Context Gathering

**Context Space**

- Read `knowledge_base_path` and `customized_skill_path` from `$SESSION_DIR/meta.yaml`.
- These fields are produced by `SKILL.md` during preference handling.
- If `knowledge_base_path` is non-empty, search that directory on the local filesystem to find references about:
  - Business Knowledge
  - Test case writing rules
  - Regression test cases
- If `knowledge_base_path` is empty, skip it directly in this step.
- If `customized_skill_path` is non-empty, search business customized skills under that directory.
- If `customized_skill_path` is empty, skip it directly in this step.

**Context Priority**

- Information from business customized knowledge/skill has a higher priority than the general information.
- If customized information contradicts with general information, follow the customized information and tell the user your choice. 

**How to use context**

- Write a plan about how to update input_document based on the context
- Do NOT ask the user to confirm the context update plan when no path handling decision is needed.
- Do NOT ask the user to handle path activation in this step; path resolution has already been written into `$SESSION_DIR/meta.yaml` before this step starts.

## step3. Test Case Generation

Based on the `Generation Style` of step1, follow the different sub-workflows below.

### 3-1 Generate with style: `Analyze by PRD2Case`

- Refer to `references/analyze_by_prd2case_sub_workflow.md`
- The **core** of this sub-workflow is: Call the local PRD2Case API with file-path inputs and write each step result into the session files.


### 3-2 Generate with style: `Follow the input`

#### General process

- [**FORCE**] Read `references/test_case_grammar.md`, and understand the grammar of test cases.
  - Why: the downstream scripts (grammar check / form transfer) and Bits IO assume this grammar; the case must remain parseable as a tree.
  - If violated: `case_grammar_check.py` and/or JSON conversion may fail, or the case tree may be corrupted (wrong node types/levels). Stop and re-read the grammar before continuing.
- [**FORCE**] Read `references/ab_setting_rule.md` to understand how to organize case structure based on A/B experiment setting.
  - Why: A/B settings affect how cases should be grouped and how branch coverage should be represented.
  - If violated: cases may mix groups, miss group-specific coverage, or become unreviewable. Pause and confirm the experiment grouping/logic with the user if it is unclear.
- Convert the input document into `test_case.md`, be loyal to the original input document.
- Use `scripts/case_grammar_check.py` to check generated test case.
- Read `references/test_case_grammar.md` **again** to check whether the current case is consistent with the test case grammar.

#### Special Post process

- `case_mode` == `Web`
  - Rule about how to start the case: Require `访问 $URL` in `前置条件` node, and the `操作步骤` node should start with the assumption that the page has been browsed.
    - Add URL to `前置条件`: Add `访问: $URL \n` at the beginning of each `前置条件` node.
    - The `$URL` should come from `input_document` or from context. If there is no specific URL information, ask the user to supply.
    - If there are existing content like `打开浏览器` and `访问 $URL` in `操作步骤` after the `前置条件` node, remove them and only keep actions after the browsing step.
  - Add `e2e` tag to `前置条件`, append it to the end of `前置条件` content with a new line.

#### Generation Instructions

**Separated Assertions**  
Each assertion should be an independent `预期结果` node, DO NOT aggregate them unless you feel necessary.

**Handle Aggregated steps and their assertions**  
For input with aggregated steps and assertions that need to be split:

| 操作步骤                                     | 预期结果                                        |
| -------------------------------------------- | ----------------------------------------------- |
| 1. step1<br>2. step2<br>3. step3<br>4. step4 | 1. assertion1<br>2. assertion2<br>3. assertion3 |

> For instance, if the real logical sequence of test execution of the table above is: 
> step1 -> step2 -> assertion1 -> step3 -> step4 -> assertion2 -> assertion3

Then the generated case should be like:

```text
## **操作步骤** 1. step1
2. step2
### **预期结果** assertion1
### **操作步骤** 1. step3
2. step4
#### **预期结果** assertion2
#### **预期结果** assertion3
```
