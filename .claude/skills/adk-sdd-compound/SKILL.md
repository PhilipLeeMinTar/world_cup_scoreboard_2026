---
name: adk-sdd-compound
description: "Use when the user wants to scan services/* code and specs/ requirements, extract reusable knowledge patterns, and populate docs/ with compound-generated assets."
---

# ADK SDD Compound

This skill scans `services/*` code and `specs/` requirements, extracts reusable knowledge patterns, and populates `docs/` with compound-generated assets.

## Manual Trigger Constraints

- Use this skill when the user explicitly wants to scan code/specs and generate or refresh compound knowledge assets.
- Do not use it for normal implementation, bug fixing, or one-off documentation edits.

## Shared Workflow

This skill and `/adk-sdd-compound` are two entrypoints to the same workflow.

This file is the skill entrypoint. The workflow behavior must stay aligned with the command definition and the runtime assets under `.ttadk/plugins/ttadk/core/resources/compound/`.

## Goal

Populate `docs/` with reusable knowledge patterns derived from the current codebase and checked-in specs, while preserving valuable human-authored content and handling conflicts explicitly.

## Context

**Read context before Executing**:
1. Language Setting
   - Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing). **IMPORTANT** **Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: generated documents, interactive prompts, confirmations, status messages, and error descriptions.**

2. Compound Knowledge Assets
   - Read `.ttadk/plugins/ttadk/core/resources/compound/schema.yaml` for dimension schema, activation rules, constraints, and scan routing
   - Read `.ttadk/compound-schema-extra.yaml` if it exists — list of user-discovered extra dimensions; entries with `enabled: true` are merged with `schema.yaml` dimensions as the active dimension list. If missing or empty, treat as no extra dimensions.
   - Read `.ttadk/plugins/ttadk/core/resources/compound/output-templates.md` for output format templates (frontmatter, TOC, cross-reference, source trace, verification markers)

## Outline

Execute the following workflow to scan code and requirements, then populate the docs/ directory with reusable knowledge patterns.

### Phase 0.5: Dimension Activation

1. Iterate all enabled dimensions (from `schema.yaml` merged with `compound-schema-extra.yaml`). For each dimension, activate as follows:
   - No `control.activation.probe_paths` defined → **always activate** (null-value passthrough is the safety net if no relevant content exists).
   - `probe_paths` defined: check if `output_path` file exists in `docs/` → if yes, activate. If not, use Glob to check if any `probe_paths` exists → if yes, activate. If both miss → mark `enabled: false`.
2. **User intent override**: If the user's natural language input indicates they want to scan specific dimensions, force-enable those dimensions regardless of activation result.

### Phase 1: Discover

#### 1.0 Resume check (run before anything else)

Read `.ttadk/compound-run-state.json`. If the file is missing or `"status": "done"`, proceed normally — no prior run to resume.

If found and `status` is not `"done"`: a previous run was interrupted. Present the user with two choices via AskUserQuestion:
- **Resume** — restore `code_root` and `scan_mode` from the state file. Skip agents whose result file already exists in `.ttadk/compound-agent-results/`. Skip docs already in `completed_docs` during Phase 3.
- **Restart** — delete `.ttadk/compound-run-state.json` and the entire `.ttadk/compound-agent-results/` directory, then proceed fresh.

#### 1.1 基础信息收集

1. Read `preferred_language` from `.ttadk/config.json` (default: `'en'` if missing). **Use the configured language for ALL outputs.**

2. Parse user input:
   - **Lark link**: Detect if it contains `bytedance.larkoffice.com`, `feishu.cn`, or `larksuite.com`
   - **Local file**: Detect if it starts with `/`, or contains common file extensions (`.md`, `.txt`, `.docx`, `.pdf`, etc.)
   - **Plain text**: Treat all other non-empty input as business background / requirement notes
   - **Empty input**: Run with repository-only auto-detect mode

3. Ingest optional business documents:
   - **If Lark link**: Use `lark-docs` MCP to export the document as markdown; store under `specs/doc_export/`; preserve original URL and local exported path for provenance.
   - **If local file**: For markdown/text files, read directly. For unsupported formats, ask user to convert first. Keep local copy under `specs/doc_export/` if provenance needed.
   - **If plain text**: Use the text directly as seed material.
   - **If empty input**: Skip ingestion and continue with repository-only scan.

4. **Detect `code_root`** (using the Bash tool):

   ```bash
   # Layer ①: .gitmodules → extract unique top-level path
   if [ -f .gitmodules ]; then
     UNIQUE=$(grep "path = " .gitmodules | awk '{print $3}' | awk -F'/' '{print $1}' | sort -u)
     COUNT=$(echo "$UNIQUE" | grep -c .)
     if [ "$COUNT" -eq 1 ]; then echo "code_root=${UNIQUE}/" && exit 0; fi
   fi
   # Layer ②: services/
   [ -d services ] && echo "code_root=services/" && exit 0
   # Layer ③: common multi-package directories
   for dir in packages apps modules lib; do [ -d "$dir" ] && echo "code_root=${dir}/" && exit 0; done
   # Layer ④: fallback
   echo "code_root=."
   ```

   Parse the Bash output to set `{code_root}`. When `{code_root} = "."`, classify top-level subdirectories (excluding `.git/`, `node_modules/`) as source vs. non-source by inspecting file types; inject the classified source directory list into Agent A scan scope.

#### 1.2 Scan 模式判断

- If any file in `docs/` has `last_compound_scan` frontmatter → **incremental** mode.
- Otherwise → **full scan** mode.

**Incremental mode — build changed file list**:
- Scan all `docs/**/*.md` for `last_compound_scan` frontmatter; take the **earliest** value as `<since_timestamp>`.
- Run: `git log --since="<since_timestamp>" --name-only --pretty=format:""`
- Also run: `git diff --name-only`, `git diff --cached --name-only`, `git status --short`
- Dedupe all results into a single changed file list.
- If no `last_compound_scan` frontmatter found → fall back to full scan.

#### 1.3 Docs 盘点

Three categories of docs/ files:

| Type | How to detect | Handling |
|---|---|---|
| Schema-declared | `output_path` in `schema.yaml` or `compound-schema-extra.yaml` | Process only if dimension is enabled (per Phase 0.5) |
| Compound-managed | has `last_compound_scan` frontmatter | incremental: check stale; full: regenerate |
| User-built | not in schema, no compound frontmatter | auto-append to `compound-schema-extra.yaml` with `enabled: true`, scan and write same as schema dimensions |

#### 1.4 Stale 检测 (incremental mode)

For each compound-managed entry (has `**Source**` line with `[Code Direct]` or legacy `[代码直引]`):
- Legacy compat: treat `[代码直引]` = `[Code Direct]`, `[AI 推断]` = `[AI Inferred]`; `**Scanned**:` lines are ignored.
- Extract source file path from the Source line.
- If source file appears in changed-files list → mark entry as stale.
- Granularity is entry-level (not doc-level).

#### 1.5 Few-shot 提取

Scan `docs/` paragraphs WITHOUT `**Source**` lines (human content) and extract style signals:
- Expression granularity (brief vs detailed)
- Structure preference (lists vs prose)
- Technical detail density

Inject these style signals into Phase 2 agent prompts.

**First run** (no human content yet): use built-in default few-shot examples from `.ttadk/plugins/ttadk/core/resources/compound/few-shot/` (one set per project type: TypeScript / Go / Python).

#### 1.6 Multi-instance 检测

Execute `node .ttadk/plugins/ttadk/core/resources/scripts/compound-preprocess.js` from repo root; parse the JSON output.

Capture `multi_instance` (array of `{kind, instances, fingerprint_sample}` groups where ≥ 3 sibling directories share a fingerprint). When non-empty, inject the list verbatim into Agent A's **Design Patterns**, **Coding Standards**, and **Service Topology** dimension prompts. When empty, skip injection — null-value passthrough applies.

#### 1.7 用户自建文档处理

Scan ALL `.md` files under `docs/` recursively. For each file not in any `output_path` in `schema.yaml` and without `last_compound_scan` frontmatter, auto-append to `.ttadk/compound-schema-extra.yaml` (create if missing):

```yaml
- output_path: docs/arch/auth.md
  target: "认证流程与 token 生命周期"
  enabled: true
```

Infer `target` from first non-empty heading + first paragraph; if file is empty, infer from filename + directory path. Target must describe the document's purpose in one sentence — no method counts, table counts, or other quantitative enumerations (e.g. "履约中心：审核流程与多级审批" not "履约中心：26方法、3表"). Every qualifying file must be registered — skipping because "too many" or "less important" is not allowed. Report newly registered files in run summary.

All `enabled: true` entries run through the same scan/write pipeline as `schema.yaml` dimensions. To opt out: set `enabled: false` in `.ttadk/compound-schema-extra.yaml`.

**Persist run state** (end of Phase 1):

Write `.ttadk/compound-run-state.json`:

```json
{
  "run_id": "2026-05-06T14:23:00",
  "status": "running",
  "completed_docs": [],
  "agents": [
    {"id": "a-1", "scope": ["services/ttadk_cli"], "status": "pending"},
    {"id": "b",   "scope": ["specs/"],             "status": "pending"}
  ]
}
```

### Phase 2: Synthesize

#### 2.0 Pre-flight checks

- If `{code_root}` is empty or missing → skip Agent A, inform user.
- If `specs/` is empty and no seed material → skip Agent B.
- If both empty and no seed material → exit early with suggestion to add code, specs, or a business document first.

#### 2.1 Agent 分发

**Dynamic agent budget** (compute before launching):

- Extract all submodule paths from `.gitmodules`. If none, treat the repo as a single flat scope.
- Build scope groups using `multi_instance` from Phase 1.6:
  1. **multi_instance groups first**: each entry covering ≥ 1 submodule path becomes one Agent A scope group.
  2. **Remainder grouping**: remaining submodule paths grouped sequentially in batches of **4**.
  3. **No-submodule fallback**: assign entire `{code_root}` as a single scope group.
- Agent B is always a single instance.
- Write `agents[]` with `status: "pending"` to run-state before launching.

**Pre-launch injection manifest** (required before drafting any sub-agent prompt):

- All agents receive **all enabled dimensions**. Null-value passthrough handles dimensions where an agent finds no signal.
- Output manifest line: `[Agent dimensions (N total)]: dim1, dim2, ...` Any enabled dimension absent MUST be added before finalizing the prompt.

**Launch all Agent A groups and Agent B in parallel.** Each agent writes its result to `.ttadk/compound-agent-results/<id>.md` and then exits. Coordinator does not hold agent output in memory — it only tracks which result files exist.

- On agent completion: update `agents[id].status = "done"` in run-state.
- On continuation signal (`COMPOUND_META: {"status": "continuation"}`): re-dispatch that agent with `remaining_scope`; append new output to its result file.

**Agent A — Code Scanner** (one instance per scope group):

- **Scope**: non-overlapping submodule paths from the dynamic budget.
- **Input**: for each dimension, `target` + `constraints`; few-shot style examples from `docs/`.
- **Output**: write COMPOUND_META markdown to `.ttadk/compound-agent-results/<id>.md`. Null-value passthrough — no Source, no write.
- **Write-size guardrail**: First write ≤ 150 lines; each subsequent append/update ≤ 100 lines (measured by newline-delimited line count). Split output across multiple Write/Edit calls if needed.
- **Context self-monitoring**: stop and signal continuation when cumulative lines read exceed **6,000**.

**Agent B — Spec Scanner**:

- **Input**: all enabled dimensions + `specs/` content + optional seed material. Mark seed findings as `seed_material` in Source lines.
- **Output**: same format, write to `.ttadk/compound-agent-results/b.md`.
- **Write-size guardrail**: First write ≤ 150 lines; each subsequent append/update ≤ 100 lines. Split output across multiple Write/Edit calls if needed.
- **Context self-monitoring**: signal continuation when cumulative lines exceed **4,000**.

#### 2.2 Agent A/B 输出格式

Agents output markdown directly, grouped by document key, each entry with a Source line:

```
COMPOUND_META: {"status": "done|continuation", "remaining_scope": [], "progress": "3/5 services"}
---
## docs/arch/patterns.md

### Strategy Pattern

The strategy pattern is used for coordinating loader selection...

**Source**: `services/ttadk_cli/src/loader/loader-factory.ts` [Code Direct]

---

### Observer Pattern

Event hooks in the plugin system follow observer pattern...

**Source**: `services/ttadk_cli/src/plugin-loader.ts` [Code Direct]

## docs/arch/data-models.md

### User Config Entity

Stores per-project AI tool preferences...

**Source**: `services/ttadk_cli/src/config/config-schema.ts` [Code Direct]
```

Rules:
- `COMPOUND_META` header is parsed by coordinator and does NOT appear in final docs.
- Every entry MUST have a Source line; entries without source evidence are skipped (null-value passthrough).
- `[AI Inferred]` allowed for cross-file architectural inferences, but Phase 3 will attempt upgrade.
- `###` and below headings are agent-free; `##` headings are coordinator-controlled.

#### 2.3 Continuation 机制

- Agent signals continuation via `COMPOUND_META: {"status": "continuation", "remaining_scope": [...]}`.
- Coordinator detects → re-dispatch with `scope = remaining_scope`, includes `prior_results`.
- Loop until `status = "done"`.

#### 2.4 Merge 逻辑

Agent C merges all result files into final docs:
- `[Code Direct]` merge key: `(source_file, heading_text)`.
- `[AI Inferred]` merge key: `(dimension_name, heading_text)`.
- Path normalization: all source paths → repo-root-relative. Strip leading `./`; reject and log paths that cannot be normalized.
- Stale entries: replaced by new content with matching key.
- Human content (no Source line, bounded by `##` headings): Agent C skips entirely.

#### 2.5 Output Scope Guard

Each agent only outputs entries for documents where it found signal within its assigned scope. Coordinator ignores agent output for out-of-scope documents.

### Phase 3: Anchor & Write (Agent C)

Once all Agent A/B result files exist, launch **Agent C — Docs Writer**:

- **Input**: all `.ttadk/compound-agent-results/*.md` result files + existing `docs/` content.
- **Task**: merge results, run source verification and AI Inferred upgrade, write final docs.
- **Resume**: if `completed_docs` in run-state is non-empty, skip those files — read result files and continue from where Phase 3 left off.
- **CRITICAL — read before write**: before writing any file, Agent C MUST read the current content of that file from disk. Never write without first reading — existing human-edited content and compound entries must be loaded before merge.

#### 3.1 Source 验证

For all `[Code Direct]` entries:
- Source file path exists → append `[Verified]`.
- File not found → append `[Pending]`, log in run summary.

#### 3.2 Stale 标记处理

- Compound entry updated (new content replaced stale): auto-clear stale marker.
- Human entry whose source changed:
  - Trigger: source_file appears in changed-files list.
  - One inline LLM judgment — is human description still accurate?
    - Still accurate → auto-clear `[Stale]`.
    - Not accurate → retain `[Stale]`, append one-sentence "source change summary".
  - **Hard cap: max 5 inline LLM judgments per run.** Entries beyond cap: retain `[Stale]`, log "pending human review (cap reached)".

#### 3.3 `[AI Inferred]` 升级尝试

For every **newly generated** `[AI Inferred]` entry (current run only, not existing docs/):

1. Extract `heading_text`.
2. Run `grep -r "<heading keyword>" {code_root}` (fall back to `.` if `{code_root}` is unset).
3. Match found → upgrade to `[Code Direct]`, write `file`.
4. No match → null-value passthrough: do NOT write this entry; log: "`[AI Inferred]` entry '<heading>' could not be upgraded — omitted".

Existing `[AI Inferred]` entries in docs/ are untouched. Non-blocking; run summary counts omitted entries.

#### 3.4 Constitution 文档轻量验证

For `output.style: constitution` docs: scan `## Fixed Rules` section for `Evidence:` lines. Missing evidence → list in run summary (non-blocking).

#### 3.5 写文件

- Write YAML frontmatter: `last_compound_scan` + `compound_scan_mode`.
- File not exist → create.
- File exists with compound frontmatter → merge (preserve human content, replace/append compound content).
  - **Human entry accuracy check (incremental mode only)**:
    - Trigger: source_file appears in changed-files list.
    - If triggered: one inline LLM judgment (counts toward 5-judgment cap).
    - If only file changed but entry seems still accurate → auto-clear `[Stale]`, no LLM call.
- File exists as unfilled skeleton (AI semantic judgment) → full overwrite.
- **After writing each file**: immediately update `completed_docs` in `.ttadk/compound-run-state.json`.
- **Heading stability**: coordinator controls `##` headings; TOC entries are generated from the actual sections AI produced (null-value passthrough applied — only sections with content appear); agent `###` and below accepted as-is.
- **Batched file write**: if ≤ 150 lines, single Write. If > 150 lines: Write frontmatter + section headings, then Edit per section body.
- **Cross-reference validation** (before write): verify all `[text](path#anchor)` links resolve. Drop dangling links rather than pointing at loosely related headings; log corrections.
- **Constitution-style output**: use `.ttadk/plugins/ttadk/core/resources/templates/constitution/{TYPE}.md` as structure reference.

#### 3.6 Run 收尾

- Write run summary (updated files, skip reasons, Pending sources, constitution missing evidence, omitted `[AI Inferred]` count).
- Update `.ttadk/compound-run-state.json` `status: "done"` (or delete file).
- Update `compound-schema-extra.yaml` (append newly discovered user docs).

### Lightweight Run State

```json
{
  "run_id": "2026-05-06T14:23:00",
  "status": "running",
  "completed_docs": ["docs/arch/patterns.md"],
  "agents": [
    {"id": "a-1", "scope": ["services/ttadk_cli"], "status": "done"},
    {"id": "a-2", "scope": ["services/ttadk_web"], "status": "pending"},
    {"id": "b",   "scope": ["specs/"],             "status": "done"}
  ]
}
```

- Only records which agents completed and which docs were written.
- Agent result files (`.ttadk/compound-agent-results/`) serve as the crash-safe checkpoint for Phase 2.
- On abort recovery: agents with existing result files are skipped; agents without are re-run. `completed_docs` is used to skip already-written docs in Phase 3.
- Delete run-state and result files on normal completion.

### Edge Cases

- If `{code_root}` directory is empty or doesn't exist → Code Scanner returns empty results, inform user
- If `specs/` directory is empty and there is no seed material → Spec Scanner returns empty results
- If `specs/` directory is empty but seed material exists → continue with seed-material-only spec extraction
- If sub-agent context overflows → fall back to scanning by dimension isolation (one dimension per sub-agent call)
- If a Lark link cannot be accessed → report error with suggestion to check the link or permissions
- If a local file path does not exist → report error with suggestion to verify the path
- If a local file format is unsupported for direct reading → ask the user to convert it to markdown/text first

## General Guidelines

- **Schema-driven**: All dimension definitions and rules are read from `schema.yaml` and `compound-schema-extra.yaml` (merged). Do NOT hardcode dimension lists. Do NOT emit files for dimensions not declared in either schema file.
- **File-level null-value passthrough**: If a dimension produces no signal across every section, do NOT write a skeleton file. Empty placeholder files pollute the knowledge index and waste SDD-loading context. The only exception is `output.style: constitution` dimensions, which must always emit.
- **No code templates in output**: Compound outputs MUST NOT contain runnable code templates or how-to snippets (see output-templates.md "Code Template Prohibition"). Replace any "how to add an X" scaffold with the invariants + pitfalls it would embody.
- **Use the configured language** for all prompts, status messages, and generated content.
- **Preserve human-edited content** when it's correct and valuable; suggest updates only when content is outdated or incorrect.
- **Always include YAML frontmatter** in compound-generated files; do NOT add a duplicate `> Auto-generated by ttadk, last updated: {DATE}` blockquote under the title (the frontmatter date is authoritative).
- **Deduplication**: When merging incremental results, remove duplicates while preserving existing correct content.
- **Format authority**: All output formats (frontmatter, TOC, cross-reference, source trace, verification markers) are defined in `output-templates.md` — follow that document, do not redefine formats here.

## Next Step Guidance

After executing this command, provide next-step guidance:

### Immediate Verification
- Check that all expected files were generated in docs/
- Review the content of key files (patterns.md, CODING.md, service-topology.md)

### Follow-up Commands
- `/adk-sdd-brainstorm` — Now leverages compound-generated knowledge assets
- `/adk-sdd-specify` — References requirement patterns from compound
- `/adk-sdd-plan` — References service topology and design patterns
- `/adk-sdd-implement` — References coding standards and config templates

### Maintenance
- Run `/adk-sdd-compound` again after significant code changes or after receiving new business documents to refresh knowledge assets
- When business context changes substantially, rerun compound with the updated Lark document, local markdown/text file, or plain-text background notes
