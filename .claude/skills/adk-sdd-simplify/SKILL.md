---
name: adk-sdd-simplify
description: "Built-in post-phase refinement step in implement; also available standalone for manual re-simplify or ad-hoc refinement. Does NOT change behavior or scope."
---

# ADK SDD Simplify

This is a **built-in implementation phase** in `/adk-sdd-implement`. It auto-runs after each story/phase completion to reduce duplication, trim unnecessary complexity, and improve reuse without changing behavior.

## Standalone Use

Use this skill standalone only when:
- Re-running simplification after manual code adjustments
- Ad-hoc refinement outside the normal implement flow

## Normal Flow

```text
/adk-sdd-implement → /adk-sdd-codereview → /adk-commit
```

## Manual Trigger Constraints

- Normally invoked automatically by implement; standalone use is optional.
- This is a post-implementation convergence pass. It must not expand scope or turn into a broad refactor.
- If the user wants to add functionality or continue implementation, use `adk-sdd-implement` instead.

## User Input

```text
$ARGUMENTS
```
You **MUST** consider the user input before proceeding (if not empty).

If the given `$ARGUMENTS` contains a link, you need to read the content of the link (use lark-docs mcp if it's a lark doc) and replace the link with content.

## Context
**Read context before Executing**:
1. Language Setting
   - Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing). **IMPORTANT** **Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: generated documents, interactive prompts, confirmations, status messages, and error descriptions.**

## Goal

Simplify the latest implementation without changing intended behavior, expanding scope, or drifting from the current SDD artifacts. This is a **post-implementation refinement pass**: reduce duplication, increase reuse, remove unnecessary complexity, and keep the code aligned with `spec.md`, `plan.md`, `tasks.md`, and the constitution.

**When invoked by implement**: Focus on the just-completed scope, then return control to implement for continued execution.

**When invoked standalone**: Complete the simplify pass and provide next-step guidance.

## Outline

1. **Resolve the target scope**:
   - If `$ARGUMENTS` identifies a story, task, file path, or feedback, use that as the simplify scope.
   - Otherwise, default to the most recently implemented code for the current feature.

2. **Load implementation context**:
   - Run `node .ttadk/plugins/ttadk/core/resources/scripts/check-prerequisites.js --json --include-tasks` from repo root and parse `FEATURE_DIR` and `AVAILABLE_DOCS`. All paths must be absolute.
   - Read `docs/CONSTITUTION.md` (fallback: `.ttadk/memory/constitution.md` for legacy projects).
   - **IF EXISTS**: Scan `docs/` for available knowledge assets (e.g., check `docs/arch/`, `docs/references/`, root-level `docs/*.md`). Load whichever files are relevant to the current task based on their filenames and contents — do not rely on a hardcoded list.
   - Read `FEATURE_DIR/spec.md`, `FEATURE_DIR/plan.md`, and `FEATURE_DIR/tasks.md`.
   - If available, also read `data-model.md`, `contracts/`, `research.md`, and `quickstart.md`.
   - Determine the relevant story/task boundaries before making any code changes.

3. **Identify implementation changes**:
   - Run `git diff` (or `git diff HEAD` if there are staged changes) to inspect the changed files.
   - If `$ARGUMENTS` specifies files or a narrower target, focus the simplify pass on that subset.
   - If there is no git diff, review the most recently modified files that were just implemented for the active scope.

4. **Launch three review agents in parallel**:
   - If the current environment supports sub-agent or delegation capabilities, use them to launch all three review agents concurrently in a single message.
   - If the current environment does not support sub-agents, fall back to a single-agent sequential review covering the same three perspectives.
   - Pass each agent the same scope description plus the relevant diff/file set.
   - Ask each agent to stay within the current feature scope and avoid suggesting unrelated refactors.

   ### Agent 1: Code Reuse Review
   For each change:
   1. Search for existing utilities, helpers, and shared modules that can replace newly written code.
   2. Flag duplicated functionality and prefer the existing implementation.
   3. Flag inline logic that should reuse an existing abstraction when a clear local fit already exists.

   ### Agent 2: Code Quality Review
   Review the same changes for unnecessary complexity:
   1. Redundant state or derived values that do not need to be stored.
   2. Parameter sprawl, copy-paste variation, and leaky abstractions.
   3. Stringly-typed code where existing constants/types already exist.
   4. Unnecessary wrappers, comments, or one-off abstractions that add noise without value.

   ### Agent 3: Efficiency Review
   Review the same changes for waste:
   1. Redundant computation, repeated reads, duplicate requests, N+1 patterns.
   2. Missed concurrency for independent work.
   3. Hot-path bloat, recurring no-op updates, unnecessary existence checks, and overly broad operations.
   4. Missing cleanup or unbounded memory growth.

5. **Apply only safe simplifications**:
   - Aggregate the agent findings.
   - Fix the worthwhile issues directly.
   - Keep external behavior and acceptance criteria unchanged.
   - Prefer reusing existing code over inventing new abstractions.
   - If a finding is not worth addressing, note it briefly and move on.

6. **Re-validate the affected scope**:
   - Re-run the relevant checks for the touched code paths.
   - If simplify changed implementation details for the active story/task, confirm the result still matches the corresponding requirements and task intent.

7. **Report**:
   - Report the simplify pass in concise process-oriented language.
   - State the simplify scope first, then summarize what was simplified.
   - Note any findings intentionally skipped.
   - End by confirming the validation result for the affected scope.

## Decision Rules

- Do **not** change product behavior, acceptance criteria, or architecture direction.
- Do **not** expand beyond the current story/task unless a tiny adjacent cleanup is required to keep the code correct.
- Do **not** introduce a broad refactor just because duplication exists elsewhere.
- Do **not** replace working code with a shared abstraction unless it is clearly better and already aligned with the current design.

## Next Step Guidance

**When invoked by implement (built-in phase)**:
- Return control to implement for continued execution.
- Do not provide standalone next-step guidance.

**When invoked standalone**:

After executing this command, provide next-step guidance to user:

### Step 1 - Confirmation
Guide user to verify the simplified code still matches expectations.

**If needs adjustment**:
- Run `/adk-sdd-implement [feedback]` to continue implementation changes
- Run `/adk-sdd-clarify [feedback]` if the simplification exposed a spec/plan/task mismatch

### Step 2 - Next Step Recommendation
Once the implementation is confirmed and stable:

**Run Code Review**: Execute `/adk-sdd-codereview` for a comprehensive review before commit.
