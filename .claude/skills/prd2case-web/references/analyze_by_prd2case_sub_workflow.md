# Analyze by PRD2Case Sub-Workflow

## Principle
- If a step is marked as `Execute by API`, call the local PRD2Case API through `scripts/call_prd2case_api.py`, **DO NOT generate it manually**.
- If a step requires `display test case to user`, you **MUST** follow `references/case_visualization_guide.md` to give the user the path to html file.
- The API call may take a few minutes to finish, check its result every 60 seconds, just check result and sleep(wait), don't try anything else. Set timeout to 900s.
- Execute **STEP bt STEP**, !!NEVER!! jump skills or merge commands.

## Procedure to use API in this workflow
0. Input identification: In each step, treat this step as a function call, there will be input definitions in each step.
1. Prepare the required input files under `$TEST_DIR`.
2. Call `scripts/call_prd2case_api.py` with file paths, let the Python script read file content locally, call the API, and write the result into the specified file in `$TEST_DIR/step_results`.

## Workflow
### step0: Ensure dir
- `$TEST_DIR/step_results`

### step1: Test Analysis
**Execute by API**
- Input file: the original `test_analysis.md`
```bash
python3 skills/prd2case/scripts/call_prd2case_api.py prd-analysis "<input_document_path>" "$TEST_DIR/step_results/test_analysis_by_prd2case.json"
```
- Result file: `test_analysis_by_prd2case.json`

### step2: A/B Experiment Analysis
**NOT Execute by API**, Do it yourself

- Three types of experiment settings:
  - No experiment: No A/B experiment related content in the context, or there is A/B experiment section but no specific A/B setting logic in the input document(usually from PRD/Analysis template)
  - Single Experiment(Most common): Specific logic for each experiment group
  - Multi Experiments: Explicit content shows that there are more than one experiment, and multiple groups under each experiment
- Do the analysis yourself and save result into `$TEST_DIR/step_results/experiment_setting.md`
  - Judge result: `No experiment`, `Single Experiment` or `Multi Experiments`
  - Experiment detail: `$group_identifier: $brief_description_of_logic`


### step3: Test Framework Generation
**Execute by API**
**display test case to user**

- Input files
  - the original `test_analysis.md` as input_document_path
  - `step_results/test_analysis_by_prd2case.json` as test_analysis_path
  - `step_results/experiment_setting.md` as experiment_setting_path

```bash
python3 skills/prd2case/scripts/call_prd2case_api.py framework-generation "<input_document_path>" "<test_analysis_path>" "<experiment_setting_path>" "$TEST_DIR/step_results/framework.md"
```
- Result file: `framework.md`

### step4: Detailed test case generation
**Execute by API**
**display test case to user**

- Input files
  - the original `test_analysis.md` as input_document_path
  - `step_results/framework.md` as framework_path
  - `step_results/test_analysis_by_prd2case.json` as test_analysis_path

```bash
python3 skills/prd2case/scripts/call_prd2case_api.py detailed-case-generation "<input_document_path>" "<framework_path>" "<test_analysis_path>" "$TEST_DIR/case.md"
```

- Web e2e 场景下 `case_mode` 固定为 `Web`，必须追加 `--case-mode "Web"`。
- The result should be written in `$TEST_DIR/case.md`, NOT `$TEST_DIR/step_results/test_case.md`
