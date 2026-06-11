---
name: adk-sdt-clarify
description: "Use when the user wants to clarify test cases, verify the logical correctness and rationality of test cases; do not use for ordinary coding requests."
---

# ADK SDT Clarify

This skill is an SDT stage skill for clarifying test cases and verify the logical correctness and rationality of test cases. It is suitable for It is suitable for secondary clarification of controversial cases.

## Manual Trigger Constraints

- Use this skill only when the user explicitly wants to clarify test cases, verify the logical correctness and rationality of test cases.
- This is a formal synchronization flow during the SDT test phase, not a general "add more explanation" action.

## User Input

```text
$ARGUMENTS
```
You **MUST** consider the user input before proceeding (if not empty).

If the given `$ARGUMENTS` contains a link, you need to read the content of the link. For lark/feishu doc URLs, export it via lark-docs MCP (`mcp__lark-docs__export_lark_doc_markdown`), then read the exported markdown content to understand the feedback context.

If `$ARGUMENTS` explicitly provides a `FEATURE_DIR` value, or clearly provides a feature-directory path, you **MUST**
treat it as the highest-priority target feature input. Reuse that exact value when invoking prerequisite scripts, and do
not ask the user to choose a different feature unless the provided path is invalid or ambiguous.

## Context
**Read context before Executing**:
1. Language Setting
   - Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing). **IMPORTANT** **Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: generated documents (specs, plans, tasks), interactive prompts, confirmations, status messages, and error descriptions.**

## Outline

Goal: Interactively review and modify test cases in `FEATURE_DIR/test/case.md` based on user feedback and code implementation comparison. Operates in a brainstorm-style multi-round dialogue, providing recommended modification options for each review point.

### Step 1: Pre-check

1. Inspect `$ARGUMENTS` first:
   - If it explicitly contains `FEATURE_DIR`, or clearly contains a feature-directory path, store it as `EXPLICIT_FEATURE_DIR`.
   - Otherwise leave `EXPLICIT_FEATURE_DIR` empty.
2. Run `node .ttadk/plugins/ttadk/core/resources/scripts/check-prerequisites.js --json` from repo root.
   - If `EXPLICIT_FEATURE_DIR` is present, append `--feature-dir "<EXPLICIT_FEATURE_DIR>"`.
3. Parse the JSON output to get `FEATURE_DIR`.
   - If parsing fails, abort and instruct user to verify the feature directory environment.
4. Set:
   - `CASE_FILE = FEATURE_DIR/test/case.md`
   - `TASK_FILE = FEATURE_DIR/test/task.md`
5. Read `CASE_FILE`.
   - If `CASE_FILE` does not exist, **STOP** and display error: "`FEATURE_DIR/test/case.md` not found. Please run `/adk-sdt-ff` first to generate test cases."
6. Read `TASK_FILE`.
   - If `TASK_FILE` does not exist, **STOP** and display error: "`FEATURE_DIR/test/task.md` not found. Please run `/adk-sdt-ff` first to generate test execution tasks."

### Step 2: Load Context

1. **REQUIRED**: Read `CASE_FILE` — the test cases to review.
2. **REQUIRED**: Read `FEATURE_DIR/spec.md` — for requirement context.
3. **Explore codebase**: Use `Grep` and `Glob` tools to search for relevant code implementations mentioned in the test cases (API endpoints, functions, components, etc.).

### Step 3: Parse User Feedback

**If `$ARGUMENTS` is not empty:**
1. Parse the user feedback to extract:
   - **TC-ID** (if mentioned): e.g., "TC-001", "TC-003"
   - **Feedback content**: the specific issue or concern
2. Locate the referenced test case(s) in `CASE_FILE`.
3. Proceed to Step 4 with the identified test case(s).

**If `$ARGUMENTS` is empty:**
1. Start with a full scan mode — analyze all test cases for potential issues.
2. Proceed to Step 5 directly.

### Step 4: Display Test Case Analysis

For each test case identified from user feedback (or from scan):

1. **Display the current test case**: Show the full content.
2. **Compare with code implementation**:
   - Use `Grep` to search for relevant API routes, function names, or component references.
   - Use `Read` to examine the actual code implementation.
   - Identify discrepancies between test expectations and actual code behavior.
3. **Present analysis results**:
   - Highlight differences between test case assumptions and code reality.
   - Mark specific Given/When/Then items that may be incorrect or outdated.

### Step 5: Evaluate Validity and Provide Modification Options

For each reviewed test case:

**If the test case is NOT reasonable (has issues):**

1. Use `AskUserQuestion` to present 2-3 modification options:
   - **Option A (Recommended)**: The best-practice fix with explanation.
   - **Option B**: An alternative approach with different trade-offs.
   - **Option C** (optional): A minimal change option.

2. After user selects an option:
   - Use `Edit` tool to immediately update the corresponding test case in `CASE_FILE`.
   - Confirm the change was applied successfully.

**If the test case IS reasonable (no issues found):**

1. Display: "✓ TC-XXX: Test case is valid, no modification needed"
2. Use `AskUserQuestion` to ask: "Continue reviewing the next test case?"
   - Yes → Continue to next test case
   - No → Proceed to Step 6

### Step 6: Proactively Identify Other Suspicious Test Cases

After completing user-specified reviews:

1. Scan remaining test cases in `CASE_FILE` that were NOT explicitly reviewed.
2. For each case, check:
   - Are the Given conditions still valid based on current code?
   - Do the When steps match actual API/UI flows?
   - Are the Then expectations consistent with code behavior?
3. If suspicious cases are found:
   - Present each suspicious case with analysis.
   - Use `AskUserQuestion` to ask if the user wants to fix it.
   - Apply fixes using the same Step 5 workflow.
4. If no suspicious cases found:
   - Display: "No other suspicious test cases found."

### Step 7: Report Change Summary

Display a summary of all changes made during this session:

```
## Change Summary

### Modified Test Cases
| TC-ID | Modification | Modification Type |
|-------|-------------|-------------------|
| TC-001 | Updated parameters | User feedback |
| TC-005 | Corrected expected API result | Proactive identification |

### Unmodified Test Cases
- TC-002, TC-003, TC-004: Review passed, no modification needed

### Statistics
- Test cases reviewed: N
- Test cases modified: M
- Proactively identified and fixed: K
```

## Error Handling

| Scenario | Handling |
|----------|---------|
| `FEATURE_DIR/test/case.md` does not exist | Prompt user to run `/adk-sdt-ff` first |
| User-specified TC-ID does not exist | Display "TC-XXX not found in case.md" and list available TC-IDs |
| User cancels operation | Preserve already-applied modifications and output current change summary |
| Related code files not found | Warn "Related code implementation not found, reviewing based on spec.md only" |

## Next Step Guidance

After executing this command:

### Step 1 - Confirmation
Review the updated `FEATURE_DIR/test/case.md` to verify all modifications are correct.

**If needs further adjustment**: Run `/adk-sdt-clarify [feedback]` again with additional feedback.

### Step 2 - Next Step Recommendation
Once test cases are finalized:

**Execute Tests**: Execute `/adk-sdt-implement` to run tests. Skill selection is resolved automatically (domain/profile based) and should be invisible to normal users.
