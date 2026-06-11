---
name: learning-capture
description: Capture reusable workflows, reasoning patterns, and domain knowledge from work sessions into persistent skill files. Trigger at task completion, after error correction, or when the user shares domain knowledge — to prevent repeated mistakes across conversations.
---

> **session_id 传递**：若本次任务需要在多次 `gdpa-cli run` 之间串联 workflow 状态、日志或上下文，请复用同一个 `session_id`。如果当前 skill / Agent 已经提供了 `session_id`，**请直接复用，不要新建**。
>
> - **已有时优先复用**：不要重复执行 `create-session`。
> - **没有时再创建**：执行 `gdpa-cli create-session`。
> - **后续调用**：可以显式传 `--session-id <session_id>`，例如 `gdpa-cli run <agent> --session-id <session_id> --input '{...}'`。
> - **适用场景**：Base Workflow、BITS Dev Workflow、post-coding-verify 及其他依赖 Session 工作目录的场景需要持续复用；普通单次查询通常可以不传。

# Learning Capture

## When to Trigger

Run this skill when **any** of the following occur:

| Trigger | Description |
|---|---|
| **Error recovery** | You made errors or tried multiple approaches before finding the correct solution — especially after user correction. |
| **Domain knowledge shared** | The user provides terminology, abbreviations, company processes, naming conventions, or standards not previously captured. |
| **Existing learning outdated** | You followed a previously captured lesson but discovered it needs correction, extension, or superseding. |

> **Do NOT trigger** for trivial or one-off fixes unlikely to recur across sessions.

## Capture Process

### Step 1: Identify What to Capture

Classify the learning into exactly one type:

| Type | Filename Pattern | When to Use |
|---|---|---|
| Task workflow | `task-<name>.md` | Reusable multi-step procedures for a recurring task. |
| Codebase / service convention | `convention-<repo-or-service-name>.md` | User provided conventions that cannot be inferred from other sources. |
| Terminology / abbreviations | `terminology.md` | Domain-specific terms, abbreviations, or jargon (single shared file). |

**Rules:**
- One file per task *category* (e.g., "log search"), NOT per task *instance* (e.g., "search logs for order #123").
- One file per repository or service for conventions.
- All terminology goes into the single shared `terminology.md`.

### Step 2: Write or Update the Learning File

Save files to `~/.agents/${workdir.replace_all('/', '-')}/captured-learning/`

```
~/.agents/${workdir.replace_all('/', '-')}/captured-learning/
├── task-log-search.md
├── task-ppe-testing.md
├── convention-payment-service.md
├── convention-user-service.md
└── terminology.md
```

**Writing guidelines:**
- Follow the structure shown in the reference examples below.
- Keep entries **actionable**: prefer "do X when Y" over vague descriptions.
- Include the **context** that makes the lesson applicable (error messages, symptoms, tool versions).
- When updating an existing file, **append or revise** — do not duplicate entries; mark superseded lessons with `~~strikethrough~~` or remove them.

### Step 3: Update the Memory Index

Add or update an entry in your main memory file:
- Your primary memory files are ${workdir}/AGENTS.md, ${workdir}/CLAUDE.local.md, ${workdir}/MEMORY.md, or equivalent files. These will be loaded automatically, or you will read them when a new session begins. It is not ~/.agents/x/captured-learning/AGENTS.md.
- Note: If the `Captured Learning` section is added to ${workdir}/AGENTS.md for the first time, and the file is under Git management, prompt the user whether to save the memory index to ~/.agents/x/captured-learning/MEMORY.md and add a corresponding note in ${workdir}/AGENTS.md.

Memory Index Example:
```markdown
## Captured Learning [Managed by learning-capture Skill]
> Before starting any task, scan this list and load relevant files to avoid repeat mistakes.
> New task requirements from the user always take precedence over captured learning.
> Evolve these entries as new tasks reveal better patterns — captured learning is living documentation.

- **key**: One-line summary. → `~/.agents/${workdir.replace_all('/', '-')}/captured-learning/<filename>.md`
```

Format: `- **bold-key**: One-line summary. → file path`

## References

- [references/task-example.md](references/task-example.md)
- [references/convention-example.md](references/convention-example.md)
- [references/terminology-example.md](references/terminology-example.md)
