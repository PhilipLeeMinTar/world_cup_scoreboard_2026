Generation Workflow Checkpoint Setting:
- Global: Semi Auto
> Options: `Semi Auto`, `Full Auto`  

- Checkpoints:
  - step0: check
  - step1: check
  - step2: check
  - step3: check
  - step4: check
> Options: `check` for stop and wait for user confirmation, `skip` for skipping user confirmation.


Bits Config
- devops_id: 310499123202
- dir_id: 1416963
> default: TikTok大模型 - PRD2Case MCP

- user_name: // Ask the user to fill


Generation Style: `Decide by Agent`
> Affects case_generation_workflow -> Step1. Generation Style Confirmation
> Options: `Decide by Agent`, `Follow the input`, `Analyze by PRD2Case`

case_mode: `General`
> Options: `General`, `Web`, `Use`

Knowledge Base Path: `NEED_TO_BE_CONFIGURED`
> Affects case_generation_workflow -> Step2. Context Gathering
> Value: a directory path to search. Set to empty to disable.
> Special: if the value is `NEED_TO_BE_CONFIGURED`, the agent MUST stop and ask the user whether to fill a real path, set to empty, or keep `NEED_TO_BE_CONFIGURED` (and write empty to meta.yaml).

Customized Skill Path: `NEED_TO_BE_CONFIGURED`
> Affects case_generation_workflow -> Step2. Context Gathering
> Value: a directory path to search. Set to empty to disable.
> Special: if the value is `NEED_TO_BE_CONFIGURED`, the agent MUST stop and ask the user whether to fill a real path, set to empty, or keep `NEED_TO_BE_CONFIGURED` (and write empty to meta.yaml).
