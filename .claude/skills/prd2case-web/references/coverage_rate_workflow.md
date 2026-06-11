## Coverage Rate Workflow (AI Cases Cover Human Cases)

### Goal
Compute the coverage rate of an AI-generated Bits test case against a human-written Bits test case:
- Input: 2 Bits case detail URLs (AI case URL + Human case URL)
- Output:
  - Coverage summary (total/covered/undecided/coverage_rate)
  - Per-path predictions (covered + evidence / reason)

Acceptance criteria (mandatory):
- Files are written to disk under a session folder: `ai_case.json`, `human_case.json`, `coverage_inputs.json`, `coverage_result.json`, `human_case_annotated.json`.
- A final Bits case link is produced (from the upload response), and the workflow must not stop before printing it.

### Inputs
- `ai_case_url`: Bits case detail URL of AI-generated test case
- `human_case_url`: Bits case detail URL of human-written test case

### Working Directory
All intermediate files are written to the current working directory by default (paths like `./coverage_inputs.json` are relative).

Recommended:
- Create a dedicated session folder per run under `sessions/` (this folder is gitignored), e.g. `sessions/session-yyyymmdd-hhmmss/`.
- Run all commands inside that session folder, or set explicit output paths via `--out-json` / `--out-annotated-json`.

### Step 1: Fetch Bits case JSON locally
Use the existing Bits fetch tool in `scripts/case_management.py`.

From the skill repo directory:

```bash
python skills/prd2case/scripts/case_management.py fetch "<ai_case_url>" --result-form json -o "./ai_case.json"
python skills/prd2case/scripts/case_management.py fetch "<human_case_url>" --result-form json -o "./human_case.json"
```

The API response file format is:
- `{"code": 0, "data": {"case_form": "json", "case_data": <case_mind_json>}}`

If you need only the `case_mind` JSON subtree, read `data.case_data`.

Note:
- All Bits fetch/upload operations in this workflow are performed via `scripts/case_management.py`.

### Step 2: Run coverage calculation locally (recommended)
The local workflow runs the model calls from the user machine (instead of a shared server).

#### Option A: Prepare inputs locally (no external model calls)
This option only prepares structured inputs for the local Agent to finish the coverage judgement. It does not call any model API.

Install dependencies:

```bash
pip install -r skills/prd2case/requirements.txt
```

Run (use locally fetched case JSON, no extra Bits fetch inside this step):

```bash
python skills/prd2case/scripts/coverage_rate.py prepare \
  --ai-case-json "./ai_case.json" \
  --human-case-json "./human_case.json" \
  --include-prefix-in-path-text \
  --chunk-size 100 \
  --out-json "./coverage_inputs.json"
```

Outputs:
- `coverage_inputs.json`: structured data for the Agent to judge (includes AI full text + per-path info)
- `coverage_inputs_parts/`: chunked inputs (recommended for large cases to avoid file-size/context issues)

### Step 3: Agent judgement (no external model calls)
Use the local Agent to read `coverage_inputs.json`, judge coverage, write `coverage_result.json`, then upload the annotated human case to Bits for visualization. The workflow is incomplete without the final Bits link.

Recommended for large cases:
- Judge per chunk file under `coverage_inputs_parts/coverage_inputs_part_*.json` and write `coverage_result_part_*.json`.
- After all chunks are judged, merge them:
```bash
python skills/prd2case/scripts/coverage_rate.py merge --results-dir "./coverage_inputs_parts" --out-json "./coverage_result.json"
```

Judgement mode (mandatory): `Balanced`
- This workflow MUST use a balanced judgement standard. Do NOT silently switch to stricter or looser standards.
- The target is to estimate whether the AI case has already covered the human testing intent at a practical/manual-test level, not whether the two paths are textually identical.
- Balanced means:
  - For flow-level expectations, allow semantic equivalence and nearby functional coverage.
  - For detail-level expectations, stay strict and require same-granularity evidence.
  - For failure/error scenarios, prioritize the same user-visible business result over exact numeric code/value matching, unless the human path is clearly validating an API/protocol contract.
  - Do NOT fall back to `Strict` just because the wording differs.
  - Do NOT fall forward to `Loose` by treating any same-page/same-feature mention as covered.

Judgement rules (Balanced, default to conservative on details):
- The judgement must be evidence-based, not keyword-based.
- Default to `covered=false` unless you can point to a concrete AI path/result statement that covers the same intent and key conditions of the human path.
- `covered=true` only when the AI case contains a logically consistent path that covers the same intent and key conditions of the human path, even if the wording is different.
- `covered=false` when you cannot find a logically consistent covering path, when the evidence is weaker / more generic than the human expectation, or when the AI case contradicts the human expectation.
- If the human path appears in the AI case as an exact same-granularity copied path (allowing only harmless whitespace / zero-width-character differences), treat it as `covered=true` directly.
- Same module / same page / same feature can count as coverage only for flow-level expectations when the AI path is clearly testing the same user-visible function or outcome. It is NOT enough by itself for detail-level expectations.
- Do NOT use one broad success-path statement to cover a more detailed expectation about UI copy, button state, API field, exact code/value contract, analytics, permissions, retry, fallback, or internal state.
- If the human expectation is more specific than the AI evidence, mark `covered=false`.
- If the human path is mainly checking a business failure/success outcome, and the AI case clearly covers the same outcome with the same key conditions, you MAY mark `covered=true` even when the AI case does not spell out the exact `err_no` / `status` / numeric code value.
- If the human path is explicitly checking an API/protocol contract (for example endpoint name, request params, response fields, `err_no`, `status`, task key, refresh strategy), then exact code/value matching remains required.

Strictness by expectation type:
- Flow-level expectation: may be covered by a semantically equivalent AI flow/result at the same product behavior level. In Balanced mode, if the AI case is clearly on the same module/page and is testing roughly the same function with a logically consistent outcome, you SHOULD mark `covered=true` even if the AI wording is broader or the exact step path differs.
- UI detail expectation (specific copy/button/icon/layout/state): require explicit AI evidence for that UI detail or a clearly equivalent detail-level statement. A generic “page displays normally” is NOT enough.
- Negative expectation (not shown / cannot click / does not exist): require explicit negative evidence. Positive evidence for a related flow is NOT enough.
- API / protocol expectation (endpoint called, request params, response fields, status, err_no, task key, refresh behavior): require explicit API-level evidence. A page-level or flow-level statement is NOT enough.
- Analytics / logging / metrics expectation (埋点, launch_log, exposure/click events): require explicit analytics evidence. A normal UI flow is NOT enough.
- Risk-control / experiment / config-template / internal-state expectation (rule names, BindEventType, ScoreEventType, Redis-like keys, labels, account fields): require explicit same-granularity evidence. A business outcome is NOT enough.
- Error-code / fallback / retry expectation:
  - If the testing intent is the business result itself (for example “助力失败并展示邀请过期提示”, “抽奖失败但机会不扣减”), explicit AI evidence of the same failure/fallback/retry behavior is enough; exact numeric code/value does NOT have to match verbatim.
  - If the testing intent is the code/value contract itself (for example “校验 `err_no=11300`”, “接口返回 `status=2`”), require explicit same-granularity code/value evidence.

Allowed abstraction:
- For expectation details with the same product meaning, abstraction is allowed only within the same granularity.
- For flow-level expectations, abstraction may cross different but nearby step paths as long as the tested function, page/module, and user-visible outcome are substantially the same.
- In Balanced mode, when the human expectation is essentially “same page, same module, roughly same function”, prefer `covered=true` if the AI path is clearly exercising that same function and there is no contradiction.
- Example allowed: “出现文案且内容为 X” can be covered by “展示正确提示文案 X” if both are explicit result statements and there is no contradiction.
- Example allowed (Balanced / flow-level): “点击入口后进入转盘二级页并开启轮次” covered by “成功跳转至玩法二级页，自动开启新轮次”, even if the exact entry surface or wording is different.
- Example allowed (Balanced / flow-level): “同模块、同页面、差不多在测这个功能” can be marked covered when the AI case clearly tests the same user-facing behavior and outcome.
- Example allowed (Balanced / error outcome): human path says “错误码 11007 / 11300，对用户展示助力失败或邀请过期结果”, AI path says “弹窗提示助力失败，失败原因为师傅轮次已过期” or another explicit same-outcome failure statement. This can be marked covered when the testing intent is clearly the business failure result, not the numeric code contract.
- Example NOT allowed: “请求 `detail_page` 接口并返回 `status=1`” covered by “成功进入二级页”.
- Example NOT allowed: “按钮文案为 Download（高亮）” covered by “回流页正常展示”.
- Example NOT allowed: “校验 `task_done` 返回 `err_no=11300`” covered by “展示助力失败弹窗”. This remains not allowed when the human path is explicitly validating the API/code contract.
- Example NOT allowed: “展示某个具体 icon / 文案 / 按钮态 / 埋点 / err_no / 配置字段” covered by “同页面功能正常”.

Inputs to use for judgement:
- AI full case text: `ai_full_text`
- Human slice text (by pc): `human_pc_slices[predictions[i].pc_node_id]`
- Human path text (root-to-leaf): `predictions[i].path_text`
Fallback: light translation/rewrite (only when needed):
- Detect language mismatch by comparing `meta.ai_lang` vs `predictions[i].expectation_lang`.
- If you cannot find any explicit evidence in `ai_full_text` for the original expectation, rewrite/translate only the expectation sentence (`predictions[i].expectation_text`) into the AI language, then search again inside `ai_full_text`.
- `predictions[i].expectation_text` must keep the full expectation body for multi-line expectations; do not collapse it to only the first line label such as `文案：` or `弹窗文案：`.
- Do NOT translate the whole slice/path. Do NOT loosen the evidence requirements.

Do NOT do any keyword/token matching pre-filter in this workflow. The Agent should read the human slice/path and search for explicit evidence directly in `ai_full_text`.

Search constraints:
- Do NOT perform repository/workspace-wide searches for keywords. Only search within the current chunk input file content (especially `ai_full_text`) to locate candidate evidence.
- Searching is only a navigation aid. The final judgement must be based on reading the surrounding AI text and quoting the exact evidence.

Evidence requirements:
- `ai_evidence` must be a short verbatim quote from AI case content, and must include the key subject + outcome (e.g. “preview 按钮展示/不展示”, “可点击/不可点击”, “存在/不存在”).
- `explain` must map the human expected result to the AI evidence. Do NOT write “命中 token：...” as explain.
- For negative expectations (e.g. “不存在 preview 按钮”, “不展示”, “不可点击”), you must find explicit negative evidence. If only positive evidence exists, mark covered=false.
- Do not use outline/title-only text as evidence (e.g. project name, test analysis title). Evidence must be a concrete rule/step/result statement.
- Do not use evidence that is more generic than the human expectation. If the human path is checking API / analytics / risk-control / detailed UI, the evidence must be at the same granularity.
- If the same `ai_evidence` snippet is reused for many different human paths, stop and re-check. This is usually a false-positive signal.

Quality self-check (before writing `coverage_result.json`):
- If many paths become covered=true with similar evidence snippets, re-check for false positives.
- If coverage_rate is close to 1.0, double-check several random covered=true paths and ensure each has explicit evidence.
- If a large number of API / analytics / risk-control / detailed-UI paths become covered=true, explicitly re-check that they are supported by same-granularity evidence rather than generic page-flow evidence.

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

Hard constraints:
- Do NOT create or run any extra judge script (e.g. judge_coverage.py). The judgement must be done directly by the local Agent.
- Do NOT generate any new code files during the coverage workflow. Only use the existing scripts in `skills/prd2case/scripts/` for IO (fetch/annotate/upload).
- Do NOT call any external model API in this workflow.
File policy:
- Allowed outputs (only): `coverage_result.json` or `coverage_result_part_*.json`, optional `human_case_annotated.json`.
- Forbidden outputs: any new `.py/.sh/.js/.ts` files (e.g. `coverage_judge_temp.py`). If such a file is created accidentally, delete it and redo judgement without using it.

Mandatory: annotate the human Bits case tree so the UI can render a coverage-marked tree:
```bash
python skills/prd2case/scripts/coverage_rate.py annotate \
  --human-case-json "./human_case.json" \
  --coverage-result-json "./coverage_result.json" \
  --coverage-inputs-json "./coverage_inputs.json" \
  --out-annotated-json "./human_case_annotated.json"
```

Final step (mandatory): upload JSON mindNodes to Bits (preserves `data.resource` without markdown conversion):
```bash
python skills/prd2case/scripts/case_management.py save-mind-nodes "./human_case_annotated.json" \
  --case-title "覆盖标注-人工用例" \
  --devops-id 310499123202 \
  --dir-id 1416963
```

It prints the API response JSON which includes the Bits case detail URL (`data.case_detail_url`).

Retention policy:
- Do NOT delete intermediate artifacts after uploading. Keep `coverage_inputs.json`, `coverage_inputs_parts/`, `coverage_result.json` (or `coverage_result_part_*.json`), and `human_case_annotated.json` for auditing.
