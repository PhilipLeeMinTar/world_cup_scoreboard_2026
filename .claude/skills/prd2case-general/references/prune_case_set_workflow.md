## Prune Case Set Workflow

### Global Prerequisite
- Before executing this workflow, the agent MUST complete the Version Gate defined in `skills/prd2case/SKILL.md`.
- If Version Gate is not completed, stop immediately and do not continue this workflow.

### Goal
Prune the current test case set for inclusion in a regression suite.

This workflow is intentionally lightweight:
- It is an agent-assisted/manual workflow, not a standardized auto-prune algorithm.
- Do not claim automatic scoring or automatic prioritization logic unless the user explicitly provides such rules.

### When To Use
Use this workflow when the user asks to:
- prune the current test case set
- keep only regression-worthy cases
- reduce a case set to a smaller regression subset
- select must-keep / should-drop cases based on explicit criteria

### Required Input
Before pruning, ask the user to provide explicit prune criteria. Examples:
- core path / smoke only
- high-risk cases first
- online regression only
- exclude low-value duplicates
- keep only P0/P1 scenarios

If the criteria are missing or ambiguous, stop and ask. Do not invent hidden rules.

### Recommended Working Method
1. Read the current case set from the local working copy first.
2. If the user says the Bits case was edited remotely, sync the latest remote version first by following `Stage-4: Update loop` in `skills/prd2case/SKILL.md`.
3. Summarize the prune criteria back to the user in concise operational terms if the criteria are complex or potentially ambiguous.
4. Review the existing cases against the user-provided criteria.
5. Produce one of these outputs depending on the user request:
   - a pruned markdown case file
   - a keep/drop recommendation list with reasons
   - an updated Bits case if the user asked for in-place synchronization
6. If the user wants the pruned result synchronized back to Bits and the current working copy is markdown, convert it to JSON first with `scripts/case_form_transfer.py`, then upload the JSON result.
7. In the standard non-UG-PA flow, if `$SESSION_DIR/input_document/assets/meta.yaml` exists, you MAY append `--image-meta-yaml "$SESSION_DIR/input_document/assets/meta.yaml"` during that conversion step.

### Allowed Tools
- Local markdown editing
- [MCP Tool] `prd2case.read_bits_case` when remote sync is needed
- [MCP Tool] `prd2case.save_case_to_bits` when the user wants the pruned result synchronized back to Bits after markdown-to-json conversion
- `scripts/case_form_transfer.py` when Bits JSON needs to be converted into markdown for review or diff

### Guardrails
- Do not prune before the user provides explicit criteria.
- Do not silently delete cases only because they look repetitive; explain the keep/drop basis.
- Do not treat this workflow as a formal optimization algorithm.
- If the pruning decision depends on business risk or release scope that is not stated clearly, ask the user instead of assuming.

### Output Expectations
The final response should clearly state:
- the prune criteria used
- which cases were kept
- which cases were removed or deprioritized
- any assumptions or unresolved ambiguities

If a Bits case was updated, include the resulting Bits case link.
