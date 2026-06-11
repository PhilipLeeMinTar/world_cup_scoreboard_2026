#!/usr/bin/env python3
"""Small CLI for api-mind state.json maintenance.

The skill should call this script instead of asking the model to rewrite the
whole state.json.  The script keeps the state schema stable, writes atomically,
and prints compact summaries by default to reduce model context usage.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional


TASKS = ("generate", "execute", "report")
STATUSES = ("pending", "running", "completed", "failed", "skipped")


def default_task() -> Dict[str, Any]:
    return {"status": "pending", "inputs": [], "outputs": [], "error": None}


def default_state(task_id: str = "", language: str = "go") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "language": language,
        "tasks": {task: default_task() for task in TASKS},
        "warnings": [],
    }


def state_path(workdir: str) -> str:
    return os.path.join(os.path.abspath(workdir), ".api-mind", "state.json")


def load_state(path: str, *, create: bool = False, task_id: str = "", language: str = "go") -> Dict[str, Any]:
    if not os.path.exists(path):
        if create:
            return default_state(task_id=task_id, language=language)
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return normalize_state(raw, task_id=task_id, language=language)


def normalize_state(state: Dict[str, Any], *, task_id: str = "", language: str = "go") -> Dict[str, Any]:
    normalized = deepcopy(state) if isinstance(state, dict) else {}
    normalized.setdefault("task_id", task_id)
    normalized.setdefault("language", language)
    normalized.setdefault("tasks", {})
    for task in TASKS:
        task_state = normalized["tasks"].setdefault(task, default_task())
        task_state.setdefault("status", "pending")
        task_state.setdefault("inputs", [])
        task_state.setdefault("outputs", [])
        task_state.setdefault("error", None)
    normalized.setdefault("warnings", [])
    return normalized


def save_state(path: str, state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="state.", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def parse_json_or_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {"value": value}


def append_many(target: List[Any], values: Optional[Iterable[str]]) -> None:
    if not values:
        return
    for value in values:
        target.append(parse_json_or_value(value))


def compact_error(error: Optional[Any], limit: int = 160) -> Optional[str]:
    if error is None:
        return None
    if isinstance(error, str):
        text = error
    else:
        text = json.dumps(error, ensure_ascii=False, sort_keys=True)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def next_task(state: Dict[str, Any]) -> str:
    for task in TASKS:
        if state["tasks"][task].get("status") != "completed":
            return task
    return "done"


def build_summary(state: Dict[str, Any], path: str) -> Dict[str, Any]:
    tasks = {}
    for task in TASKS:
        item = state["tasks"][task]
        tasks[task] = {
            "status": item.get("status", "pending"),
            "inputs": len(item.get("inputs", [])),
            "outputs": len(item.get("outputs", [])),
            "fix_attempts": item.get("fix_attempts", 0),
            "error": compact_error(item.get("error")),
        }
    return {
        "path": path,
        "task_id": state.get("task_id", ""),
        "language": state.get("language", ""),
        "next": next_task(state),
        "tasks": tasks,
        "warnings": len(state.get("warnings", [])),
    }


def print_summary(summary: Dict[str, Any], *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
        return
    parts = [
        f"state={summary['path']}",
        f"task_id={summary['task_id']}",
        f"language={summary['language']}",
        f"next={summary['next']}",
        f"warnings={summary['warnings']}",
    ]
    print(" ".join(parts))
    for task in TASKS:
        item = summary["tasks"][task]
        line = f"{task}: status={item['status']} inputs={item['inputs']} outputs={item['outputs']} fix_attempts={item['fix_attempts']}"
        if item["error"]:
            line += f" error={item['error']}"
        print(line)


def cmd_init(args: argparse.Namespace) -> int:
    path = state_path(args.workdir)
    state = load_state(path, create=True, task_id=args.task_id, language=args.language)
    if args.task_id and not state.get("task_id"):
        state["task_id"] = args.task_id
    if args.language:
        state["language"] = args.language
    save_state(path, state)
    print_summary(build_summary(state, path), as_json=args.json)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    path = state_path(args.workdir)
    state = load_state(path)
    print_summary(build_summary(state, path), as_json=args.json)
    return 0


def cmd_set_task(args: argparse.Namespace) -> int:
    path = state_path(args.workdir)
    state = load_state(path, create=args.create, task_id=args.task_id, language=args.language)
    task_state = state["tasks"][args.task]
    if args.status:
        task_state["status"] = args.status
        if args.status in ("running", "completed", "skipped") and not args.error:
            task_state["error"] = None
    append_many(task_state["inputs"], args.input)
    append_many(task_state["outputs"], args.output)
    if args.error is not None:
        task_state["error"] = parse_json_or_value(args.error)
    save_state(path, state)
    print_summary(build_summary(state, path), as_json=args.json)
    return 0


def cmd_warn(args: argparse.Namespace) -> int:
    path = state_path(args.workdir)
    state = load_state(path, create=args.create, task_id=args.task_id, language=args.language)
    warning: Dict[str, Any] = {"code": args.code}
    if args.message:
        warning["message"] = args.message
    if args.detail:
        warning["detail"] = parse_json_or_value(args.detail)
    state["warnings"].append(warning)
    save_state(path, state)
    print_summary(build_summary(state, path), as_json=args.json)
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    path = state_path(args.workdir)
    state = load_state(path)
    task_state = state["tasks"][args.task]
    task_state["fix_attempts"] = int(task_state.get("fix_attempts", 0)) + 1
    item: Dict[str, Any] = {"summary": args.summary}
    if args.result:
        item["result"] = args.result
    if args.files:
        item["files"] = args.files
    task_state.setdefault("fix_history", []).append(item)
    save_state(path, state)
    print_summary(build_summary(state, path), as_json=args.json)
    return 0


def cmd_show_task(args: argparse.Namespace) -> int:
    path = state_path(args.workdir)
    state = load_state(path)
    print(json.dumps(state["tasks"][args.task], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain api-mind .api-mind/state.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--workdir", required=True, help="Feature test workdir; state is stored in <workdir>/.api-mind/state.json")
        p.add_argument("--json", action="store_true", help="Print compact machine-readable summary")

    init = subparsers.add_parser("init", help="Create or normalize state.json")
    add_common(init)
    init.add_argument("--task-id", default="")
    init.add_argument("--language", choices=("go", "python"), default="go")
    init.set_defaults(func=cmd_init)

    summary = subparsers.add_parser("summary", help="Print compact state summary")
    add_common(summary)
    summary.set_defaults(func=cmd_summary)

    set_task = subparsers.add_parser("set-task", help="Update one subtask without rewriting the whole state manually")
    add_common(set_task)
    set_task.add_argument("--task", choices=TASKS, required=True)
    set_task.add_argument("--status", choices=STATUSES)
    set_task.add_argument("--input", action="append", help="JSON object/string to append to inputs[]")
    set_task.add_argument("--output", action="append", help="JSON object/string to append to outputs[]")
    set_task.add_argument("--error", help="JSON object/string error; omit to keep current error")
    set_task.add_argument("--create", action="store_true", help="Create state if missing")
    set_task.add_argument("--task-id", default="")
    set_task.add_argument("--language", choices=("go", "python"), default="go")
    set_task.set_defaults(func=cmd_set_task)

    warn = subparsers.add_parser("warn", help="Append one warning")
    add_common(warn)
    warn.add_argument("--code", required=True)
    warn.add_argument("--message", default="")
    warn.add_argument("--detail", help="JSON object/string detail")
    warn.add_argument("--create", action="store_true", help="Create state if missing")
    warn.add_argument("--task-id", default="")
    warn.add_argument("--language", choices=("go", "python"), default="go")
    warn.set_defaults(func=cmd_warn)

    fix = subparsers.add_parser("fix", help="Append one auto-fix record and increment fix_attempts")
    add_common(fix)
    fix.add_argument("--task", choices=TASKS, default="execute")
    fix.add_argument("--summary", required=True)
    fix.add_argument("--result", default="")
    fix.add_argument("--files", nargs="*")
    fix.set_defaults(func=cmd_fix)

    show_task = subparsers.add_parser("show-task", help="Print full detail for a single subtask only")
    add_common(show_task)
    show_task.add_argument("--task", choices=TASKS, required=True)
    show_task.set_defaults(func=cmd_show_task)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"state not found: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"invalid state json: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
