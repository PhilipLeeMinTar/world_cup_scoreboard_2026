# MCP Setup

## Goal

This document defines how the agent should configure the `prd2case` MCP server when the current environment does not provide it.

## When To Use

Use this file only after `SKILL.md` has already determined that:
- the current environment does not have a usable `prd2case` MCP
- the user has granted permission to configure it automatically

If the user does not allow configuration, stop and tell the user that PRD2Case MCP setup is required before the workflow can continue.

## Hard Gate

- All Bits/Lark IO and case generation outputs must be verifiable; pretending the MCP exists creates non-auditable (hallucinated) artifacts.
- If MCP is unavailable: fail fast, explain the missing MCP prerequisite, and ask for permission to configure it.

## Setup Workflow

Follow the steps below in order when configuration is needed.

### Stage-0: Inform and Ask Permission

1. Tell the user that PRD2Case MCP is not configured or not available in the current agent environment.
2. Ask for permission to configure it automatically.
3. If the user does not allow configuration, stop and tell the user that PRD2Case MCP setup is required before the workflow can continue.

### Stage-1: Locate The Correct MCP Config File (Current Runtime Only)

1. Locate the MCP config file used by the current agent runtime.
2. The agent MUST operate only on the MCP config file used by the current agent runtime.
3. The agent MUST prefer the current agent's default config location first, instead of doing a broad filesystem search.
4. The agent MUST NOT search or modify MCP config files for other agents or unrelated tools.
5. If the current runtime config cannot be identified confidently, stop and ask the user instead of guessing.

### Stage-2: Add Or Update `prd2case` Server Config

1. Add the `prd2case` server config in the current runtime config file using the file's native format (JSON or TOML).
2. If the target config file already contains `prd2case` with different content:
   - Show the diff and ask for confirmation before overwriting it.
   - If the user does not confirm the overwrite, stop and do not modify the config.
3. Always write timeout fields required by this format (see "Timeout Requirement").

### Stage-3: Confirm Result and Restart Reminder

1. Tell the user which config file was updated.
2. Remind the user to restart the current agent session so the newly added MCP can be loaded.

## Required Server Config

If the current agent uses JSON-style MCP config, the expected server config is:

```json
{
  "mcpServers": {
    "prd2case": {
      "command": "npx",
      "args": [
        "-y",
        "--registry",
        "https://bnpm.byted.org",
        "@bytedance-dev/prd2case-mcp-server"
      ],
      "tool_timeout_sec": 900.0,
      "startup_timeout_sec": 60.0
    }
  }
}
```

If the current agent uses TOML-style MCP config, the equivalent `prd2case` config should be:

```toml
[mcp_servers.prd2case]
command = "npx"
args = [
  "-y",
  "--registry",
  "https://bnpm.byted.org",
  "@bytedance-dev/prd2case-mcp-server",
]
tool_timeout_sec = 900.0
startup_timeout_sec = 60.0
```

## Timeout Requirement

- `tool_timeout_sec = 900.0` is mandatory because detailed case generation can exceed the default 120-second limit in some agent runtimes.
- `startup_timeout_sec = 60.0` is mandatory because MCP startup may take longer than shorter default values in some environments.
- When adding the config, the agent MUST write these timeout fields in the current config format. Do not omit them.

## Fail-Fast Rule

Do not fabricate case links, Bits results, Lark exports, or any MCP-backed outputs when `prd2case` MCP is unavailable. If MCP is required and not available, stop and resolve setup first.
