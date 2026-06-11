# Combination Test Proposal Workflow

## Table of Contents

- Global Prerequisite
- Goal
- When to Use
- Inputs
- Session Files
- Workflow
  - Step 0. Prepare the source material
  - Step 1. Decide whether combination testing is actually needed
  - Step 2. Extract candidate combination dimensions
  - Step 3. Remove combinations that should not be expanded blindly
  - Step 4. Prioritize the combinations that are worth testing
  - Step 5. Write `combination_test_proposal.md`
  - Step 6. Stop after proposal by default
- Required Output Structure
- Output Quality Rules
- Handoff to Formal Test Cases

## Global Prerequisite
- Before executing this workflow, the agent MUST complete the Version Gate defined in `skills/prd2case/SKILL.md`.
- If Version Gate is not completed, stop immediately and do not continue this workflow.

## Goal
Produce a reviewable combination-test proposal when the input PRD / analysis document contains meaningful combinational scenarios.

This workflow is for proposal-first requests. By default, stop after writing the proposal. Do NOT directly generate formal test cases unless the user explicitly asks for that next step.

## When to Use
Use this workflow when the user asks for any of the following:
- whether the requirement needs combination testing
- a combination-test proposal
- a test matrix
- 参数组合测试建议
- 高风险组合场景梳理
- combination coverage suggestions before formal case generation

Use this workflow especially when the user explicitly says things like:
- "先不要生成正式用例"
- "先给 proposal"
- "just propose the matrix first"

## Inputs
Possible inputs:
- Lark PRD / analysis doc URL
- local markdown document
- existing session files such as `input_document/content.md` or `test_analysis.md`
- user-provided feature summary

## Session Files
Store artifacts under the standard session directory defined in `skills/prd2case/SKILL.md`:

```text
input_document/
  content.md
  assets/
test_analysis.md                 # optional, if already exists in session
combination_test_proposal.md
meta.yaml
```

The required output of this workflow is:
- `combination_test_proposal.md`

## Workflow

### Step 0. Prepare the source material
- Reuse the normal session workflow conventions from `SKILL.md`.
- If the user provides a Lark document, fetch it into the session as a canonical document directory.
- If the session already contains the relevant `input_document/content.md` or `test_analysis.md`, reuse them.
- Read the most relevant source material before proposing combinations.

### Step 1. Decide whether combination testing is actually needed
Do not assume all requirements need combination testing.

Judge whether the document contains interaction across multiple dimensions such as:
- multiple input modes
- multiple roles / permissions / account states
- multiple status transitions
- multiple async/sync execution paths
- multiple configuration switches / experiment groups
- multiple upstream/downstream dependency chains
- multiple review / rollback / approval branches
- multiple environments / entry points / data sources

If the PRD is mostly a single straight-through flow with little cross-dimension behavior, say so clearly and keep the proposal small.

### Step 2. Extract candidate combination dimensions
Extract the dimensions that can combine meaningfully.

Typical dimension types include:
- user role / permission / identity
- feature switch / experiment group / config variant
- input source / import method / attachment type / data source
- task mode / orchestration mode / sync vs async mode
- node priority / review status / rollback decision
- entry point / page state / object state
- upstream precondition / downstream dependency result
- success / failure / timeout / empty-state / retry branches

For each dimension, list the meaningful values or states.

### Step 3. Remove combinations that should not be expanded blindly
Do NOT default to full Cartesian expansion.

You must explicitly remove or deprioritize combinations that are:
- impossible by product logic
- redundant because they verify the same business rule
- low-value UI variations without business impact
- dominated by a more representative higher-risk combination

When excluding combinations, explain why.

### Step 4. Prioritize the combinations that are worth testing
Prefer a risk-based proposal.

Prioritize combinations that are most likely to hide defects, such as:
- state transitions + async execution
- permission / identity + action result
- experiment group + downstream behavior difference
- sync tool + async tool handoff
- input mode + validation / parsing behavior
- rollback / retry / recovery after partial success
- human-in-the-loop branching + process continuation / discard
- default path + exception path sharing the same resource

If useful, group the proposal into levels such as:
- smoke combinations
- core business combinations
- high-risk edge combinations

You may mention pairwise-style coverage as a strategy, but do not force formal combinatorial algorithm wording unless the user asks for it.

### Step 5. Write `combination_test_proposal.md`
Write a concise but structured proposal.

## Required Output Structure
Use this exact section structure:

```markdown
# Combination Test Proposal
## Objective
## Is Combination Testing Needed?
## Candidate Dimensions
## Recommended Coverage Strategy
## High-Priority Combinations
## Excluded / Deprioritized Combinations
## Suggested Next Step
```

Section requirements:
- `Objective`
  - summarize what feature / scope is being analyzed
- `Is Combination Testing Needed?`
  - answer yes / partially / no, with 1-3 reasons
- `Candidate Dimensions`
  - list each dimension and its key values or states
- `Recommended Coverage Strategy`
  - explain whether to use a small focused matrix, risk-based subset, pairwise-like coverage, or mostly single-flow testing
- `High-Priority Combinations`
  - list the combinations worth testing first
  - each item should include brief rationale
- `Excluded / Deprioritized Combinations`
  - list combinations you intentionally skip and why
- `Suggested Next Step`
  - recommend whether to:
    - stop at proposal
    - turn selected combinations into formal test cases
    - merge the combinations into an existing regression set

### Step 6. Stop after proposal by default
After writing the proposal:
- show the user the proposal summary
- ask whether they want to continue by converting selected combinations into formal test cases

Do NOT automatically enter full case generation unless the user explicitly requests it.

## Output Quality Rules
- Focus on meaningful business combinations, not exhaustive permutations.
- Prefer combinations that validate different business risks.
- Be explicit when a combination is valuable because of state interaction rather than UI variation.
- If the requirement already has obvious matrix dimensions, organize them clearly.
- If the requirement is weakly combinational, say that directly instead of inventing a large matrix.
- If the user already asked only a yes/no question about whether combination testing is needed, answer that first and keep the proposal lightweight.

## Handoff to Formal Test Cases
Only if the user asks to continue:
- treat the selected high-priority combinations as the scope input for formal test-case generation
- then return to the normal `prd2case` workflow and generate cases for the chosen combinations only
- avoid regenerating unrelated single-flow cases unless the user asks for full coverage
