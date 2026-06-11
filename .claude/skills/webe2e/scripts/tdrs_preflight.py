#!/usr/bin/env python3
"""
Preflight gate that runs BEFORE Stage-2 TDRS.

The gate is intentionally structural, not prose-based. It only passes when at
least one of the recognised auth/API assets exists on disk:

- `.env`               — environment file with at least one token-like assignment
- `cookies.txt`        — cookie jar with at least one non-comment line
- `auth.json`          — JSON auth/session blob with non-empty payload
- `save_result.json`   — prior Bits save result with non-empty payload
- `auth_log.md`        — markdown ask log with at least one populated
                         `user_reply_verbatim: <non-empty>` entry

If none of these exist, the agent is told to call the user-question tool
(`AskQuestion`) to request auth/API material and append the user's verbatim
reply to `auth_log.md`. A prose claim like "I asked the user" is NOT enough;
the file must contain an explicit verbatim reply.

This script returns exit code 0 when at least one asset is present, otherwise
1, so it can be wired as a hard gate in Stage-2.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ENV_FILENAMES = (".env",)
COOKIE_FILENAMES = ("cookies.txt", "cookie.txt")
AUTH_JSON_FILENAMES = ("auth.json", "session.json")
SAVE_RESULT_FILENAMES = ("save_result.json",)
AUTH_LOG_FILENAMES = ("auth_log.md", "tdrs_auth_log.md")

ENV_ASSIGNMENT_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*\S+")
USER_REPLY_RE = re.compile(
    r"user[_\s-]*reply(?:[_\s-]*verbatim)?\s*[:：]\s*(.+?)\s*$",
    re.IGNORECASE,
)


def _strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def _env_has_value(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ENV_ASSIGNMENT_RE.match(line):
            return True
    return False


def _cookie_has_value(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(_strip_comments(text).strip())


def _json_has_payload(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if not raw:
        return False
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return False
    if isinstance(payload, dict):
        if not payload:
            return False
        data = payload.get("data") if "data" in payload else payload
        if isinstance(data, dict):
            return any(_meaningful(value) for value in data.values())
        return _meaningful(data)
    if isinstance(payload, list):
        return any(_meaningful(item) for item in payload)
    return _meaningful(payload)


def _meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _auth_log_has_user_reply(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    for raw in text.splitlines():
        match = USER_REPLY_RE.search(raw)
        if not match:
            continue
        reply = match.group(1).strip().strip("\"'")
        if reply and reply not in {"-", "...", "<TO_FILL>", "<todo>"}:
            return True
    return False


def _first_existing(workspace: Path, names: Iterable[str]) -> Path | None:
    for name in names:
        candidate = workspace / name
        if candidate.exists():
            return candidate
    return None


def check_preflight(
    workspace: str | Path,
    *,
    env_path: str | Path | None = None,
    cookies_path: str | Path | None = None,
    auth_json_path: str | Path | None = None,
    save_result_path: str | Path | None = None,
    auth_log_path: str | Path | None = None,
) -> dict[str, Any]:
    workspace = Path(workspace)
    present: list[str] = []
    detail: dict[str, str] = {}

    env_candidate = Path(env_path) if env_path else _first_existing(workspace, ENV_FILENAMES)
    if env_candidate and _env_has_value(env_candidate):
        present.append("env")
        detail["env"] = str(env_candidate)

    cookies_candidate = (
        Path(cookies_path) if cookies_path else _first_existing(workspace, COOKIE_FILENAMES)
    )
    if cookies_candidate and _cookie_has_value(cookies_candidate):
        present.append("cookies")
        detail["cookies"] = str(cookies_candidate)

    auth_json_candidate = (
        Path(auth_json_path) if auth_json_path else _first_existing(workspace, AUTH_JSON_FILENAMES)
    )
    if auth_json_candidate and _json_has_payload(auth_json_candidate):
        present.append("auth_json")
        detail["auth_json"] = str(auth_json_candidate)

    save_result_candidate = (
        Path(save_result_path)
        if save_result_path
        else _first_existing(workspace, SAVE_RESULT_FILENAMES)
    )
    if save_result_candidate and _json_has_payload(save_result_candidate):
        present.append("save_result")
        detail["save_result"] = str(save_result_candidate)

    auth_log_candidate = (
        Path(auth_log_path) if auth_log_path else _first_existing(workspace, AUTH_LOG_FILENAMES)
    )
    if auth_log_candidate and _auth_log_has_user_reply(auth_log_candidate):
        present.append("auth_log")
        detail["auth_log"] = str(auth_log_candidate)

    passed = bool(present)
    errors: list[str] = []
    if not passed:
        errors.append(
            "No auth/API material detected in workspace `"
            f"{workspace}`. Before running Stage-2 TDRS you MUST call the "
            "user-question tool (e.g. AskQuestion) to request auth/API "
            "material (curl, cookie, token, owner scope, list/detail API). "
            "Then make ONE of the following true and re-run this preflight:\n"
            "  - place real credentials in `.env` (token-like KEY=VALUE), "
            "`cookies.txt`, `auth.json`, or `save_result.json`; OR\n"
            "  - append an entry to `auth_log.md` with the user's verbatim "
            "reply, e.g.\n"
            "      - analysis_ids: [WEB-001]\n"
            "        asked_at: <iso-timestamp>\n"
            "        prompt: \"<what you asked>\"\n"
            "        user_reply_verbatim: \"<paste user reply here>\"\n"
            "        outcome: declined | provided | partial\n"
            "Prose statements like `已请求材料` or `asked user` without a "
            "verbatim reply do NOT satisfy this preflight."
        )

    return {
        "passed": passed,
        "present_assets": present,
        "detail": detail,
        "errors": errors,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stage-2 TDRS preflight. Refuses to start TDRS until auth/API "
            "material or an `auth_log.md` user reply is on disk."
        )
    )
    parser.add_argument(
        "workspace",
        help="Workspace directory to scan for .env / cookies.txt / save_result.json / auth_log.md.",
    )
    parser.add_argument("--env", dest="env_path", default=None)
    parser.add_argument("--cookies", dest="cookies_path", default=None)
    parser.add_argument("--auth-json", dest="auth_json_path", default=None)
    parser.add_argument("--save-result", dest="save_result_path", default=None)
    parser.add_argument("--auth-log", dest="auth_log_path", default=None)
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = Path(args.workspace)
    if not workspace.exists():
        result = {
            "passed": False,
            "present_assets": [],
            "detail": {},
            "errors": [f"workspace not found: {workspace}"],
        }
    else:
        result = check_preflight(
            workspace,
            env_path=args.env_path,
            cookies_path=args.cookies_path,
            auth_json_path=args.auth_json_path,
            save_result_path=args.save_result_path,
            auth_log_path=args.auth_log_path,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(run())
