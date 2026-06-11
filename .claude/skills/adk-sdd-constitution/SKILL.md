---
name: adk-sdd-constitution
description: "Use when the user wants to create or update the project constitution document set (5 files in docs/), change governance rules, or sync SDD templates and command constraints with new principles; do not use for ordinary coding or document editing."
---

# ADK SDD Constitution

This skill is an SDD stage skill for maintaining project governance rules. It is suitable for creating or updating the constitution document set (5 files in `docs/`) and syncing related templates and command constraints.

## Manual Trigger Constraints

- Use this skill only when the user explicitly wants to create or update the constitution, adjust governance rules, or sync related policy constraints.
- This is not ordinary document polishing. It is a governance-rules update flow.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

If the given `$ARGUMENTS` contains a link, you need to read the content of the link (use the lark_docs MCP if the link points to a Lark document) and replace the link with the document content.

## Context

**Read context before Executing**:

1. **Language Setting**: Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing).
   - **IMPORTANT**: Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: generated documents, interactive prompts, confirmations, status messages, and error descriptions.

2. **Initialize Constitution Documents**: Run `node .ttadk/plugins/ttadk/core/resources/scripts/init-constitution.js --json` from repo root.
   - This script checks `docs/` for 5 constitution-style files (CONSTITUTION.md, QUALITY.md, RELIABILITY.md, SECURITY.md, CODING.md). For any missing file, it copies from `.ttadk/plugins/ttadk/core/resources/templates/constitution/{TYPE}.md` and replaces `[PROJECT_NAME]` and `[DATE]` placeholders. Existing files are never overwritten.
   - If the script reports `legacy_detected: true`, inform the user that `.ttadk/memory/constitution.md` (legacy path) exists but is no longer maintained — the new path is `docs/CONSTITUTION.md`.

## Outline

You are updating the project constitution document set at `docs/`. This consists of 5 files, each following a constitution-style structure (Core Section → Fixed Rules → Governance → Version line). Your job is to (a) collect/derive concrete values for each file, (b) fill them precisely via interactive prompts, and (c) propagate any amendments across dependent artifacts.

The 5 files are:

| File | Core Section | Focus |
| --- | --- | --- |
| `docs/CONSTITUTION.md` | Core Principles | Project-level governance principles, non-negotiable rules |
| `docs/QUALITY.md` | Core Standards | Quality gates, testing strategy, CI requirements |
| `docs/RELIABILITY.md` | Core Practices | Fault tolerance, degradation, monitoring, graceful startup/shutdown |
| `docs/SECURITY.md` | Core Practices | Authentication, authorization, encryption |
| `docs/CODING.md` | Core Conventions | Naming, error handling, logging standards |

Follow this execution flow:

1. Load the 5 constitution files from `docs/`.
   - For each file, identify every placeholder token (e.g. `[PROJECT_NAME]`, `[Principle Name]`, `[Description]`, `[DATE]`).
   - **IMPORTANT**: The user might require less or more principles/standards/practices/conventions than the template provides. If a number is specified, respect that — follow the general template pattern. Adjust the `### I.` through `### N.` numbering accordingly.

2. Interactive filling — process each file sequentially:

   **2a. `docs/CONSTITUTION.md`**:
   - Collect/derive values for project name, core principles, custom sections, fixed rules, governance.
   - If user input supplies a value, use it. Otherwise infer from existing repo context (README, docs, prior constitution versions).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - Version increment follows semantic versioning:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.

   **2b. `docs/QUALITY.md`**:
   - Fill core standards (quality gates, testing strategy), fixed rules (CI, code review, coverage), governance.
   - Derive from repo context (existing CI config, test patterns) when user doesn't specify.

   **2c. `docs/RELIABILITY.md`**:
   - Fill core practices (fault tolerance, degradation, monitoring, graceful startup/shutdown), fixed rules, governance.
   - Derive from repo context (existing health checks, error handling patterns) when user doesn't specify.

   **2d. `docs/SECURITY.md`**:
   - Fill core practices (authentication, authorization, encryption), fixed rules, governance.
   - Derive from repo context (existing auth patterns, credential handling) when user doesn't specify.

   **2e. `docs/CODING.md`**:
   - Fill core conventions (naming, error handling, logging), fixed rules, governance.
   - Derive from repo context (existing code patterns, linter configs) when user doesn't specify.

3. Draft the updated content for each file:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots — explicitly justify any left).
   - Preserve heading hierarchy and structure.
   - Ensure each core section item: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.
   - **Fixed Rules Section**: This section contains default rules for AI-assisted development. Translate to match `preferred_language` while preserving the original meaning.

4. Consistency propagation checklist (convert prior checklist into active validations):

   **Constitution Document Set Cross-Validation:**
   - Verify CONSTITUTION.md principles have corresponding entries in QUALITY.md, RELIABILITY.md, SECURITY.md, and CODING.md where applicable.
   - Verify Fixed Rules across all 5 files are not contradictory.
   - Verify Governance sections across all 5 files are consistent.

   **Standard Workflow Templates:**
   - Read `.ttadk/plugins/ttadk/core/resources/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `.ttadk/plugins/ttadk/core/resources/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `.ttadk/plugins/ttadk/core/resources/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types.

   **Fast-forward Workflow Alignment:**
   - Treat `.ttadk/plugins/ttadk/core/resources/templates/spec-template.md` as the canonical specification template and ensure constitution changes remain reflected there for both standard and fast-forward flows.
   - Verify `plan.md` and `tasks.md` outputs remain aligned with constitution principles. Do not rely on `*-lite` templates as the source of truth.

   **Command Definitions and Documentation:**
   - Read each command file in `.ttadk/plugins/ttadk/core/commands/**/*.md` (including this one) to verify no outdated references remain.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`). Update references to principles changed.

5. Produce a Sync Impact Report (prepend as an HTML comment at top of each updated constitution file):
   - Version change: old → new
   - List of modified principles/standards/practices/conventions
   - Added sections
   - Removed sections
   - Cross-validation results (✅ consistent / ⚠ needs attention)
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Follow-up TODOs if any placeholders intentionally deferred.

6. Validation before final output:
   - No remaining unexplained bracket tokens in any of the 5 files.
   - Version lines match reports.
   - Dates ISO format YYYY-MM-DD.
   - Core section items are declarative, testable, and free of vague language.
   - Cross-validation between 5 files shows no contradictions.

7. Write each completed file back to `docs/` (overwrite with filled content).

8. Output a final summary to the user with:
   - Files updated (list all 5 with versions).
   - Cross-validation results.
   - Any files flagged for manual follow-up.
   - Suggested commit message (e.g., `docs: initialize constitution document set v1.0.0`).

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing files in `docs/`.

## Next Step Guidance

After executing this command, provide next-step guidance to user:

### Step 1 - Confirmation
Guide user to verify the generated constitution documents are correct and align with project principles.

**If needs adjustment**: Re-run `/adk-sdd-constitution [feedback]` to refine.

### Step 2 - Next Step Recommendation
Once constitution is confirmed and satisfactory:

**Create Feature Specification**:
- **Standard workflow**: Execute `/adk-sdd-specify [input]` to create detailed feature specification with validation and clarification flow
- **Fast-forward workflow**: Execute `/adk-sdd-ff [input]` to quickly draft spec, plan, and tasks together
