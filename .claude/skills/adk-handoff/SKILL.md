---
name: adk-handoff
description: "Use when the user wants to create, monitor, list, stop, continue, or sync ttadk handoff async tasks; do not use for local code changes or SDD workflow steps."
---

# ADK Handoff

This skill is used to manage **ttadk handoff** async tasks through natural language. It interprets user intent and executes the appropriate `ttadk handoff` subcommands (submit, list, detail, stop, continue, sync).

## Manual Trigger Constraints

- Use this skill when the user wants to interact with ttadk handoff tasks: creating, listing, checking status, stopping, continuing, or syncing async tasks.
- Do not use this skill for local code modifications, SDD workflow steps, or non-handoff CLI operations.
- If the user's intent is ambiguous between handoff and other workflows, ask for clarification before triggering.

## User Input

```text
$ARGUMENTS
```
You **MUST** consider the user input before proceeding (if not empty).

If the given `$ARGUMENTS` contains a link, treat it as part of the user's task input (e.g. a reference URL to pass to `handoff submit`). Do **NOT** attempt to read or resolve the link content — preserve it as-is.

## Context
**Read context before Executing**:
1. Language Setting
   - Read `preferred_language` from `.ttadk/config.json` (default: 'en' if missing). **IMPORTANT** **Use the configured language for ALL outputs: 'en' → English, 'zh' → 中文. This applies to: interactive prompts, confirmations, status messages, and error descriptions.**

## Role

You are an intelligent assistant for managing **ttadk handoff** async tasks. Instead of requiring users to memorize CLI syntax and flags, you interpret natural language intent and execute the appropriate `ttadk handoff` subcommands on their behalf.

**Core principle**: Always use `-f json` for commands that support it, parse the structured output, and present results in a human-friendly format. Never expose raw JSON to the user unless explicitly requested.

## Available Commands Reference

### 1. `ttadk handoff submit` — Create a new handoff task

Submits a task to handoff execution. Requires the project to be initialized (`ttadk init`) and git working tree to be clean with changes pushed.

```
ttadk handoff submit [input] -f json
ttadk handoff submit [input] -s <spec_name> -f json
ttadk handoff submit [input] -n -f json
```

| Option | Description |
|--------|-------------|
| `[input]` | Task description (what the handoff agent should do) |
| `-s, --spec <spec_name>` | Use an existing spec from `specs/<spec_name>/spec.md` |
| `-n, --new` | Create a new spec (skip interactive spec selection) |
| `-f json` | Output as JSON |

**JSON output shape** (`HandoffResult`):
```json
{
  "sessionId": "string",
  "status": "string",
  "task": { /* TikaTaskRecord, see Data Model below */ }
}
```

### 2. `ttadk handoff list` — List handoff tasks

Lists tasks filtered by status, count, or task ID.

```
ttadk handoff list -f json
ttadk handoff list -n <number> -f json
ttadk handoff list -s <status> -f json
ttadk handoff list -t <task_id> -f json
```

| Option | Description |
|--------|-------------|
| `-n, --number <number>` | Number of tasks to return (default: 5) |
| `-s, --status <status>` | Filter: `running`, `stopped`, `completed`, `failed` |
| `-t, --task <task_id>` | Show a specific task |
| `-f json` | Output as JSON |

**JSON output shape**: `TikaTaskRecord[]`

### 3. `ttadk handoff detail` — View task detail

```
ttadk handoff detail -t <task_id> -f json
```

| Option | Description |
|--------|-------------|
| `-t, --task <task_id>` | **Required.** Task ID |
| `-f json` | Output as JSON |

**JSON output shape**: `TikaTaskRecord`

### 4. `ttadk handoff stop` — Stop a running task

```
ttadk handoff stop -t <task_id> -f json
```

| Option | Description |
|--------|-------------|
| `-t, --task <task_id>` | **Required.** Task ID |
| `-f json` | Output as JSON |

**JSON output shape**: `TikaTaskRecord`

### 5. `ttadk handoff continue` — Resume a stopped/failed task

```
ttadk handoff continue [input] -t <task_id> -f json
```

| Option | Description |
|--------|-------------|
| `[input]` | Instructions for the continued task |
| `-t, --task <task_id>` | Task ID to continue |
| `-f json` | Output as JSON |

**JSON output shape** (`ContinueResult`):
```json
{
  "task": { /* TikaTaskRecord */ }
}
```

### 6. `ttadk handoff sync` — Sync task artifacts to local

Fetches the task's target branch via `git fetch`. Does **NOT** support `-f json`.

```
ttadk handoff sync -t <task_id>
ttadk handoff sync -t <task_id> --onlysync
```

| Option | Description |
|--------|-------------|
| `-t, --task <task_id>` | **Required.** Task ID |
| `--onlysync` | Sync without prompting to stop a running task |

**Output**: Human-readable text (git fetch results, branch info, MR URLs).

## Data Model — `TikaTaskRecord`

All JSON-returning commands share this core structure:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique task identifier |
| `status` | string | `RUNNING` / `PENDING` / `WAITING` / `SUCCESS` / `FAILED` / `STOPPED` |
| `ttadk_phase` | string? | Current workflow phase |
| `remote_url` | string | Remote session URL |
| `tmates_url` | string? | TMates share link. Internal-only field: parse if present, but do **NOT** display it to the user |
| `created_at` | string | Creation timestamp |
| `updated_at` | string? | Last update timestamp |
| `input` / `prompt` | string? | User-provided task description |
| `spec_name` | string? | Associated spec name |
| `repos` | RepoDetail[] | Repository details (see below) |

**`RepoDetail`**:

| Field | Type | Description |
|-------|------|-------------|
| `repo_path` | string | Repository path |
| `branch` | string | Source branch |
| `target_branch` | string? | Target branch created by handoff agent |
| `mr_url` | string? | Merge request URL |
| `lines_inserted` | number? | Lines added |
| `lines_deleted` | number? | Lines removed |

## Execution Flow

### Step 1 — Recognize User Intent

Analyze `$ARGUMENTS` to determine which operation(s) the user wants. Use the mapping below:

| User Intent (keywords / patterns) | Action |
|------------------------------------|--------|
| create, submit, handoff, start a task, run in cloud, new task | → `submit` |
| list, show tasks, my tasks, what's running, recent tasks | → `list` |
| detail, status of, info about, check task, show task | → `detail` |
| stop, cancel, kill, abort, halt | → `stop` |
| continue, resume, retry, restart, keep going | → `continue` |
| sync, pull, fetch, download, get changes, bring to local | → `sync` |
| combined intents (e.g. "stop the latest running task") | → multi-step |

**If the user's intent is unclear, ambiguous, or could map to multiple commands**: Ask the user to supplement the missing information first so you can choose the right command to run. Typical clarification dimensions include:

- whether they want to create a new handoff task, inspect existing tasks, stop a task, continue a task, or sync a finished task
- whether they are referring to a brand-new requirement, a requirement link, or an existing spec
- whether they already know the target `task_id` or need help locating it

Do **NOT** default to running `list` when the operation itself is still unclear. Only execute a command after the user's intent is specific enough to map to one or more concrete handoff subcommands.

**If `$ARGUMENTS` is empty**: Ask the user what they want to do with ttadk handoff. Do not assume any default operation.

### Step 2 — Resolve Parameters

Once the intent is clear, determine required parameters. **Distinguish between "unclear intent" and "missing parameters"**:

- If the operation is still unclear, ask follow-up questions so the user can choose the correct action.
- If the operation is clear but parameters are missing, ask only for the missing parameters and keep the chosen operation unchanged.

- **For `submit`**: Guide the user to clarify the following before executing:
  1. **Task requirement**: Ask the user to describe what the handoff agent should do, or provide a requirement link (e.g. Lark doc URL). The task description must be clear enough for the handoff agent to act on.
  2. **New or existing spec**: Ask the user whether this is a brand-new task (`-n` flag) or a continuation of an existing spec (`-s <spec_name>`). If the user wants to use an existing spec, list available specs under `specs/` to help them choose.
  3. **New-spec input quality check**: When creating a new spec (`-n`), if the user input is pure text (no requirement link) and is just 1–2 short sentences, **reject the submission** and ask the user to provide a more detailed description or a requirement document link. Brief inputs like "add a login page" or "improve error handling" are insufficient for the handoff agent to produce quality results. This check does NOT apply when using an existing spec (`-s`).
  
  Only execute `submit` once both are resolved.
- **For `detail` / `stop` / `continue` / `sync`** (require `task_id`): Extract from user input if provided (e.g. "stop task abc123"). If not provided, run `ttadk handoff list -f json` to find matching tasks and let the user pick.
- **spec_name**: Extract if user mentions a spec. Validate existence by checking `specs/<name>/spec.md`.
- **input text**: For `submit` and `continue`, extract the task description or instructions from the user's message.

### Step 3 — Execute Command

Run the resolved command in shell. Rules:

1. **Always use `-f json`** for commands that support it (`submit`, `list`, `detail`, `stop`, `continue`).
2. **NEVER use `--skip-checks`** — preflight checks (project init, git status, credentials) are mandatory and must not be bypassed.
3. For `submit` with user-provided input, properly quote the input string.
4. For `sync`, run without `-f json` (not supported) and interpret the text output.

### Step 4 — Parse and Present Results

After executing a command, parse the JSON output and present it in a clear, structured format:

**Sensitive link handling**:

- Show `remote_url` when it is useful for the user to inspect the cloud task remotely.
- Show `mr_url` when present in repo details.
- Do **NOT** display, quote, summarize, or otherwise expose `tmates_url` in normal output. Treat it as an internal field that should be masked from user-facing responses unless the user explicitly asks for it.

**For a single task**, display as a summary card:

```
Task: <task_id>
Status: <status with context>
Spec: <spec_name or "N/A">
Input: <task description, truncated if long>
Created: <formatted local time>
Remote: <remote_url>
```

If `repos` are present, also show:
```
Repos:
  - <repo_path>: <branch> → <target_branch>
    MR: <mr_url>
    Changes: +<inserted> -<deleted>
```

**For a task list**, display as a compact table:

```
| # | Task ID | Spec | Status | Input | Created |
|---|---------|------|--------|-------|---------|
```

### Step 5 — Suggest Next Actions

Based on the task status, proactively suggest relevant follow-up actions:

| Current Status | Suggested Actions |
|----------------|-------------------|
| `RUNNING` / `PENDING` / `WAITING` | "You can ask me to check this task's latest status, inspect its details, or stop it if needed." |
| `SUCCESS` | "Task completed! You can ask me to sync the result to local. If there's an MR, review it at the provided URL." |
| `FAILED` | "Task failed. You can ask me to continue this task with new instructions, or inspect the remote URL for more details." |
| `STOPPED` | "Task is stopped. You can ask me to resume it with new instructions, or create a fresh handoff task." |
| After `submit` | "Task submitted! You can ask me to check the latest status or view this task's details later." |
| After `sync` | "Changes fetched. You can view the diff with `git diff <branch>..origin/<target_branch>` or checkout the branch with `git checkout <target_branch>`." |

## Multi-Step Operations

When the user's intent requires multiple commands, execute them sequentially:

**Examples:**

- "Stop my latest running task"
  1. `ttadk handoff list -s running -n 1 -f json` → get task_id
  2. `ttadk handoff stop -t <task_id> -f json` → stop it

- "What happened with my last task? Sync it if it's done."
  1. `ttadk handoff list -n 1 -f json` → get latest task
  2. If `status === 'SUCCESS'`: `ttadk handoff sync -t <task_id> --onlysync`
  3. If not done: report current status and suggest waiting

- "Continue the failed task with 'fix the type errors'"
  1. `ttadk handoff list -s failed -n 1 -f json` → find failed task
  2. `ttadk handoff continue "fix the type errors" -t <task_id> -f json` → resume

## Error Handling

- **Command fails**: Report the error clearly, explain the likely cause, and suggest remediation.
  - Common: project not initialized → suggest `ttadk init`
  - Common: git not clean → suggest committing and pushing changes first
  - Common: invalid task_id → suggest listing tasks to find the correct ID
- **No tasks found**: Inform the user and suggest creating a new task with `ttadk handoff submit`.
- **Ambiguous task reference**: When multiple tasks match the user's description, present the candidates and ask the user to pick one.

## Important Rules

1. **NEVER use `--skip-checks`** — all preflight checks must run.
2. **Always `-f json`** for supported commands — parse and present, don't show raw JSON.
3. **Don't guess task IDs** — if you don't have one, fetch the list first.
4. **Confirm destructive actions** — before `stop`, confirm with the user if the task_id was inferred (not explicitly provided).
5. **Quote shell arguments** — properly escape user input when constructing shell commands.
6. **Handle `sync` specially** — it has no JSON output; read and summarize the text output instead.

## Next Step Guidance

After executing this command, provide contextual next-step guidance:

- **After listing tasks**: Suggest that the user can ask to view details, stop, continue, or sync a specific task.
- **After creating a task**: Suggest that the user can come back later and ask for the latest status or task details.
- **After syncing**: Suggest reviewing the diff or checking out the target branch.
- **After stopping**: Suggest continuing with new instructions or starting a fresh task.
- **For completed workflows**: Suggest `/adk:commit` to commit synced changes.
