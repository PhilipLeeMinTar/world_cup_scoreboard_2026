---
name: adk-sdd-checkout
description: "Switch to a different spec workspace and load its context. Use when the user wants to change the active spec, switch workspace, or checkout a different feature spec."
---

# ADK SDD Checkout

This skill switches the active SDD spec workspace by reading target spec files and outputting a context override declaration.

## Manual Trigger Constraints

- Use this skill only when the user explicitly asks to switch/checkout a spec workspace.
- User mentions wanting to work on a different spec.
- User says "checkout", "switch to", or "change spec".
- Do not use for general coding requests or standard SDD flow.

## User Input

```text
$ARGUMENTS
```
You **MUST** consider the user input before proceeding (if not empty).

## Context
**Read context before Executing**:
1. Language Setting
   - Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing). **IMPORTANT** **Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: generated documents (specs, plans, tasks), interactive prompts, confirmations, status messages, and error descriptions.**

## Outline

Switch the active SDD spec workspace by reading target spec files and outputting a context override declaration.

### Step 1: Determine Target Spec

**If `$ARGUMENTS` is empty** (no spec name provided):

1. Run `node .ttadk/plugins/ttadk/core/resources/scripts/checkout.js --list --json` from repo root
2. Parse the JSON output to get the list of available specs
3. Display the specs as a table:
   ```
   | # | Spec Name | spec.md | plan.md | tasks.md |
   |---|-----------|---------|---------|----------|
   | 1 | 20260418-... | ✓ | ✓ | ✗ |
   ```
4. Use the AskUserQuestion tool to let the user select a spec from the list
5. Set the selected spec name as the target

**If `$ARGUMENTS` is non-empty** (spec name provided):

1. Use the provided argument as the target spec name
2. Proceed directly to Step 2

---

### Step 2: Validate and Switch

1. Run `node .ttadk/plugins/ttadk/core/resources/scripts/checkout.js --spec {target_spec_name} --json` from repo root
2. Parse the JSON output

**If `success` is false**:
- Display the error message
- Show the list of available specs from the `available_specs` field
- Ask the user to try again with a valid spec name
- STOP execution

**If `success` is true**:
- Proceed to Step 3

---

### Step 3: Activate Workspace

> **Note**: The checkout script automatically persists `TTADK_FEATURE` into `.claude/settings.local.json` env field. All subsequent Bash calls in this session (and future sessions) will have the environment variable set, so `check-prerequisites.js` and other SDD commands will automatically target the correct spec.

1. **Read all available files** from the `available_files` list in the JSON output:
   - For each file in `available_files`, read it from `{feature_dir}/{filename}`
   - Priority order: spec.md first, then plan.md, then tasks.md, then others

2. **Output context override declaration**:

   ```
   ---
   ⚠️ CONTEXT SWITCH COMPLETE
   
   Active spec: {spec_name}
   Working directory: {feature_dir}
   Available files: {available_files joined by comma}
   
   From this point forward, ALL SDD commands operate on specs/{spec_name}/.
   Ignore any previous spec context from earlier in this conversation.
   ---
   ```

3. **Display summary**:
   - Show the first 5 lines of spec.md (if exists) as a quick reminder of the feature purpose
   - Show task completion status if tasks.md exists (count of `- [x]` vs `- [ ]`)

---

### Step 4: Next Steps Guidance

After successful checkout, suggest:
- `/adk:sdd:implement` — to continue implementing tasks
- `/adk:sdd:clarify [feedback]` — to refine the spec
- `/adk:sdd:checkout` — to switch to another spec
