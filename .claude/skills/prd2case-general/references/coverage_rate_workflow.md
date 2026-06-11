## Coverage Rate Workflow (AI Cases Cover Human Cases)

### Global Prerequisite
- Before executing this workflow, the agent MUST complete the Version Gate defined in `skills/prd2case/SKILL.md`.
- If Version Gate is not completed, stop immediately and do not continue this workflow.

### Table of Contents
- [Goal](#goal)
- [Inputs](#inputs)
- [Working Directory](#working-directory)
- [Step 1: Fetch Bits Case JSON Locally](#step-1-fetch-bits-case-json-locally)
- [Step 2: Run Coverage Preparation Locally](#step-2-run-coverage-preparation-locally)
- [Step 3: Agent Judgement](#step-3-agent-judgement)
- [Appendix A: Evidence Strictness by Checked Object](#appendix-a-evidence-strictness-by-checked-object)
- [Appendix B: Allowed vs Not Allowed Examples](#appendix-b-allowed-vs-not-allowed-examples)
- [Appendix C: Explain/Reason Templates](#appendix-c-explainreason-templates)

### Goal
Compute the coverage rate of an AI-generated Bits test case against a human-written Bits test case:
- Input: 2 Bits case detail URLs (AI case URL + Human case URL)
- Output:
  - Coverage summary (total/covered/undecided/coverage_rate)
  - Per-path predictions (covered + evidence / reason)

Acceptance criteria (mandatory):
- Files are written to disk under a session folder: `ai_case.json`, `human_case.json`, `coverage_inputs.json`, `ai_modules.json`, `coverage_result.json`, `human_case_annotated.json`.
- A final Bits case link is produced (from the upload response), and the workflow must not stop before printing it.

### Inputs
- `ai_case_url`: Bits case detail URL of AI-generated test case
- `human_case_url`: Bits case detail URL of human-written test case

### Working Directory
All intermediate files are written to the current working directory by default (paths like `./coverage_inputs.json` are relative).

Recommended:
- Run this workflow inside the standard session directory defined in `skills/prd2case/SKILL.md`.
- Run all commands inside that session folder, or set explicit output paths via `--out-json` / `--out-annotated-json`.

### Step 1: Fetch Bits Case JSON Locally
Use [MCP Tool] `prd2case.read_bits_case` to export both Bits cases as local JSON files:
- Export the AI case directly as `./ai_case.json`
- Export the human case directly as `./human_case.json`
- When calling the MCP tool, always pass the canonical target filename instead of relying on the default exported filename.

The API response file format is:
- `{"code": 0, "data": {"case_form": "json", "case_data": <case_mind_json>}}`

If you need only the `case_mind` JSON subtree, read `data.case_data`.


### Step 2: Run Coverage Preparation Locally
Prepare the structured inputs locally for the Agent to finish the coverage judgement. This step does not call any external model API.

1. Convert JSON to Markdown (preserves heading hierarchy while compressing size):

```bash
# json -> markdown
python3 $SKILL_DIR/scripts/case_form_transfer.py "./ai_case.json" -o "./ai_case.md"

python3 $SKILL_DIR/scripts/case_form_transfer.py "./human_case.json" -o "./human_case.md"
```

2. Run (use locally fetched case JSON and the generated Markdown):

```bash
python3 $SKILL_DIR/scripts/coverage_rate.py prepare \
  --ai-case-json "./ai_case.json" \
  --human-case-json "./human_case.json" \
  --ai-case-md "./ai_case.md" \
  --human-case-md "./human_case.md" \
  --include-prefix-in-path-text \
  --chunk-size 100 \
  --out-json "./coverage_inputs.json"
```

Outputs:
- `coverage_inputs.json`: structured data for the Agent to judge. It keeps:
  - `ai_full_text` only as global fallback
  - metadata pointing to `ai_modules.json`
  - per-path `expectation_type`, `judge_steps`, `module_fallback_key`, `type_override_allowed`
- `ai_modules.json`: the primary AI-case corpus for judgement. The Agent should search this file first instead of loading all AI content into every chunk.
- `coverage_inputs_parts/`: chunked inputs for judgement. Each part keeps only:
  - the current prediction chunk
  - related `human_pc_slices`
  - a relative pointer to `ai_modules.json`
  - a relative pointer back to the full `coverage_inputs.json` for global fallback

### Step 3: Agent Judgement
Use the local Agent to read `coverage_inputs.json`, judge coverage, write `coverage_result.json`, then upload the annotated human case to Bits for visualization. The workflow is incomplete without the final Bits link.

#### Guardrails (Read This First)
- Even if the user only says “根据这个项目中的相关 skill 帮我计算召回率”, the Agent MUST still follow the decision checklist below. Otherwise the judgement becomes inconsistent and non-auditable across runs.
- Do NOT inline or mentally summarize all AI content at once when `ai_modules.json` exists. Open and search `ai_modules.json` first, then use `coverage_inputs.json` only as global fallback.

Recommended for large cases:
- Judge per chunk file under `coverage_inputs_parts/coverage_inputs_part_*.json` and write `coverage_result_part_*.json`.
- After all chunks are judged, merge them:
```bash
python3 $SKILL_DIR/scripts/coverage_rate.py merge --results-dir "./coverage_inputs_parts" --out-json "./coverage_result.json"
```

#### Judgement Standard (Balanced, Mandatory)
- This workflow MUST use a balanced judgement standard. Do NOT silently switch to stricter or looser standards.
- The target is to estimate whether the AI case covers the human testing intent at a practical/manual-test level, not whether two paths are textually identical.
- Flow-level intent: allow semantic equivalence and nearby functional coverage when the user-visible outcome is the same.
- Detail-level intent (UI detail / negative / API / analytics / config-rule): require same-granularity evidence.
- Do NOT output internal judgement-standard labels (e.g., “Balanced”, “Strict”, “Loose”) in user-visible results; only provide the concrete judgement + evidence + reasoning.

#### Inputs Used for Judgement
- Human slice text (by pc): `human_pc_slices[predictions[i].pc_node_id]`
- Human path text (root-to-leaf): `predictions[i].path_text`
- Expectation type (hint only): `predictions[i].expectation_type`
- Judge checklist (hint only): `predictions[i].judge_steps`
- AI corpus (primary): `ai_modules.json`
- Preferred same-module start: `predictions[i].module_fallback_key` in `ai_modules.json`
- Global fallback: `ai_full_text` from the full `coverage_inputs.json`

#### Decision Checklist (Mandatory)
1. Summarize the human testing intent from `human_pc_slices[...]` and `path_text`. Do not jump to the final verdict first.
2. Decide what the human is checking: user-visible business result vs strict-detail contract (UI detail, negative/disappearance, API/field/value, analytics, permission, config/rule).
3. If the path sits under an entry surface, distinguish whether it checks the entry surface itself or the downstream result after using that entry.
4. Open `ai_modules.json` as the main AI-case corpus. Start with `module_fallback_key` when available.
5. If exact module-name lookup is weak or empty, search semantically related modules in `ai_modules.json` before concluding uncovered.
6. If the entry module is weakly matched but the checked object is the downstream business result, continue searching downstream page/flow modules before concluding uncovered.
7. If `ai_modules.json` is insufficient, open the full `coverage_inputs.json` and search `ai_full_text` as a global fallback.
8. Only after the module/global fallback chain is exhausted may you decide `covered=false`.

#### Fallback (Translation/Rewrite, Only When Needed)
- If you cannot find explicit evidence due to language mismatch (`meta.ai_lang` vs `predictions[i].expectation_lang`), rewrite/translate only `predictions[i].expectation_text` into the AI language, then search again.
- Keep the full multi-line expectation body; do not collapse it to just the first label line (e.g. `文案：`).
- Do NOT translate the whole slice/path. Do NOT loosen evidence requirements.

#### Search Constraints
- Do NOT do repository/workspace-wide searches. Only search inside the current chunk input file, `ai_modules.json`, and the parent `coverage_inputs.json` fallback file.
- Searching is only navigation. Final judgement must be based on reading the surrounding AI text and quoting the exact evidence.

#### Evidence & Output Requirements (Minimal Contract)
- `ai_evidence` must be a short verbatim quote from AI case content, and must include the key subject + outcome (e.g. “preview 按钮展示/不展示”, “可点击/不可点击”, “存在/不存在”).
- `explain` must map the human expectation to the AI evidence and state why it is same-intent + same-granularity coverage.
- When `covered=false`, `reason` must state: what the human checks, what was searched (module and/or fallback), and why found AI evidence is missing/weaker/wrong-granularity/contradictory.
- Do NOT use vague templates (e.g. “语义相近，因此覆盖”, “同模块可认为覆盖”) or empty reasons (e.g. “未覆盖/证据不足/未找到相关证据”).
- See Appendix C for concrete templates and examples.

#### Quality Self-Check (Light Audit)
- Self-check is a light false-positive audit, not a second full judgement pass.
- Prioritize re-checking covered=true paths that are high-risk: explicit UI detail, negative/disappearance, API/field/value/err_no, analytics, permission, config/rule, reused evidence snippets.

Output schema:
```json
{
  "summary": { "total_paths": 0, "decided_paths": 0, "covered_paths": 0, "undecided_paths": 0, "coverage_rate": 0.0 },
  "predictions": [
    {
      "path_id": "1",
      "expectation_node_id": "xxx",
      "path_node_ids": ["..."],
      "prefix": ["..."],
      "path_text": "...",
      "expectation_type": "flow",
      "type_override_allowed": false,
      "match_scope": "module|global_fallback|not_found",
      "review_flag": "",
      "model": {
        "covered": true,
        "evidence": [{"ai_evidence": "...", "explain": "..."}],
        "reason": ""
      }
    }
  ]
}
```

Important:
- `expectation_node_id` is required for annotating the human case tree. The Agent should copy it from `coverage_inputs.json` for each `path_id`.

#### Hard Constraints
- Do NOT create or run any extra judge script (e.g. judge_coverage.py). The judgement must be done directly by the local Agent.
- Do NOT generate any new code files during the coverage workflow. Use PRD2Case MCP tools for Lark/Bits IO and the existing local scripts only for local processing such as prepare/annotate/merge.
- Do NOT modify any existing project code files during judgement. The Agent may only read inputs and write the allowed coverage output files.
- Do NOT call any external model API in this workflow.

#### File Policy
- Allowed outputs (only): `coverage_result.json` or `coverage_result_part_*.json`, optional `human_case_annotated.json`.
- Forbidden outputs: any new `.py/.sh/.js/.ts` files (e.g. `coverage_judge_temp.py`). If such a file is created accidentally, delete it and redo judgement without using it.

Mandatory: annotate the human Bits case tree so the UI can render a coverage-marked tree:
```bash
python3 $SKILL_DIR/scripts/coverage_rate.py annotate \
  --human-case-json "./human_case.json" \
  --coverage-result-json "./coverage_result.json" \
  --coverage-inputs-json "./coverage_inputs.json" \
  --out-annotated-json "./human_case_annotated.json"
```

Final step (mandatory): upload JSON mindNodes to Bits with [MCP Tool] `prd2case.save_case_to_bits`:
- `case_file_path="./human_case_annotated.json"`
- `case_form="json"`
- `case_title="覆盖标注-人工用例"`
- `user_name="<your_email_prefix>"`
- `devops_id=310499123202`
- `dir_id=1416963`

The MCP response includes the Bits case detail URL.

Retention policy:
- Do NOT delete intermediate artifacts after uploading. Keep `coverage_inputs.json`, `ai_modules.json`, `coverage_inputs_parts/`, `coverage_result.json` (or `coverage_result_part_*.json`), and `human_case_annotated.json` for auditing.

### Appendix A: Evidence Strictness by Checked Object
This appendix is a quick "what counts as evidence" reference. When in doubt, default to conservative for strict-detail contracts.

| Checked object | Required evidence (same granularity) | Common pitfall |
| --- | --- | --- |
| User-visible business result (flow-level) | A logically consistent AI path/result that hits the same user-visible outcome and key conditions | Marking uncovered only because the step path/wording differs |
| Explicit UI detail (copy/button/icon/layout/state) | Explicit UI detail statement (or clearly equivalent detail-level statement) | Using “page displays normally” to cover specific UI copy/state |
| Negative/disappearance (not shown/cannot click/does not exist/disappears) | Explicit negative/disappearance evidence | Using positive evidence of a related flow as "coverage" |
| API/protocol contract (endpoint/params/fields/status/err_no/task key/refresh) | Explicit API-level evidence including the checked field/value | Using page-level success as a substitute for API evidence |
| Analytics/logging/metrics (埋点/exposure/click) | Explicit analytics evidence (event name/trigger/params) | Assuming "normal flow" implies analytics coverage |
| Risk-control/experiment/config-rule/internal-state | Explicit same-granularity rule/field evidence | Using business outcome to cover an internal rule contract (or vice versa) |
| Error code vs business failure outcome | If intent is business outcome: explicit same-outcome failure is enough; if intent is code/value contract: require exact code/value evidence | Treating any failure popup as coverage for an `err_no` contract |

### Appendix B: Allowed vs Not Allowed Examples
Allowed (flow-level semantic equivalence):
- Human: “点击入口后进入转盘二级页并自动开启轮次” -> AI: “成功跳转至玩法二级页，自动开启新轮次”
- Human: “出现文案且内容为 X” -> AI: “展示正确提示文案 X” (both are explicit result statements, no contradiction)

Allowed (business failure outcome, not code/value contract):
- Human: “错误码 11007/11300，对用户展示助力失败或邀请过期结果” -> AI: “弹窗提示助力失败，失败原因为师傅轮次已过期” (intent is the user-visible outcome)

Not allowed (wrong granularity):
- Human: “请求 `detail_page` 接口并返回 `status=1`” -> AI: “成功进入二级页”
- Human: “按钮文案为 Download（高亮）” -> AI: “回流页正常展示”
- Human: “校验 `task_done` 返回 `err_no=11300`” -> AI: “展示助力失败弹窗” (intent is code/value contract)

### Appendix C: Explain/Reason Templates
`explain` must include:
- the human expectation being judged,
- the exact AI quote used as evidence,
- why it is same-intent and same-granularity coverage under the balanced standard.

Forbidden `explain` patterns (too vague):
- “AI用例在相同功能模块给出了明确结果，可覆盖该人工预期”
- “同模块可认为覆盖”
- “语义相近，因此覆盖”
- “功能一致，可覆盖”

Good `explain` examples:
- “人工预期是‘点击入口后进入转盘二级页并自动开启轮次’。AI 证据是‘成功跳转至玩法二级页，自动开启新轮次’。两者都在验证同一用户动作后的页面跳转与轮次开启结果，属于 flow 粒度的等价覆盖。”
- “人工预期校验 `task_done` 返回 `$.err_no=11021`。AI 证据是‘task_done接口返回 $.err_no=11021’。两者在同一接口字段和错误码粒度上一致，因此判定覆盖。”

`reason` (when `covered=false`) must include:
- what the human expectation is checking,
- what evidence was searched (module and/or global fallback),
- why found AI evidence is missing/weaker/wrong-granularity/contradictory.

Forbidden `reason` patterns (not reviewable):
- “未找到相关证据”
- “证据不足”
- “未覆盖”
