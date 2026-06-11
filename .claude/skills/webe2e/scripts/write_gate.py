#!/usr/bin/env python3
"""
write_gate.py — Stage-3 pre-check that audits write operations.

This gate cross-checks two files in the workspace:

- `http_log.jsonl`        — append-only audit produced by `safe_http.py`
- `write_consent_log.md`  — explicit user-consent entries per write op

Rules:
1. Every row in `http_log.jsonl` whose `method` is a write method
   (POST/PUT/PATCH/DELETE) and was NOT rejected by safe_http must have a
   non-null `consent_match`. A null `consent_match` means a write call slipped
   through (e.g. someone bypassed safe_http with raw curl, but still logged
   to http_log.jsonl somehow) and must be investigated.
2. Every entry in `write_consent_log.md` must have:
   - non-empty `analysis_ids`
   - non-empty `user_reply_verbatim`
   - parseable ISO-8601 `approved_at`
3. Missing log files are tolerated: a workspace with no writes is valid.

Exit code 0 when all checks pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
DEFAULT_HTTP_LOG = "http_log.jsonl"
DEFAULT_CONSENT_LOG = "write_consent_log.md"


def _parse_consent_log(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        if raw.lstrip().startswith("#"):
            continue
        stripped = raw.rstrip()
        if stripped.startswith("- "):
            if current is not None:
                entries.append(current)
            current = {}
            body = stripped[2:].strip()
            if ":" in body:
                key, _, value = body.partition(":")
                current[key.strip()] = value.strip()
        elif raw.startswith(" ") and current is not None:
            body = raw.strip()
            if ":" in body:
                key, _, value = body.partition(":")
                current[key.strip()] = value.strip()
    if current is not None:
        entries.append(current)

    normalised: list[dict[str, Any]] = []
    for entry in entries:
        if not entry:
            continue
        ids_raw = entry.get("analysis_ids", "")
        if ids_raw.startswith("[") and ids_raw.endswith("]"):
            ids = [x.strip() for x in ids_raw[1:-1].split(",") if x.strip()]
        else:
            ids = [x.strip() for x in ids_raw.split(",") if x.strip()]
        entry["analysis_ids"] = ids
        for key in ("method", "url_pattern", "user_reply_verbatim", "body_summary", "approved_at"):
            if key in entry and isinstance(entry[key], str):
                entry[key] = entry[key].strip().strip('"').strip("'")
        normalised.append(entry)
    return normalised


def _check_consent_entries(entries: list[dict[str, Any]], errors: list[str]) -> None:
    for idx, entry in enumerate(entries):
        ref = f"consent_entry#{idx}"
        analysis_ids = entry.get("analysis_ids") or []
        if not analysis_ids:
            errors.append(f"{ref}: analysis_ids is empty; consent must scope to at least one row.")
        reply = (entry.get("user_reply_verbatim") or "").strip()
        if not reply:
            errors.append(f"{ref}: user_reply_verbatim is empty; record the user's verbatim reply.")
        approved_at = entry.get("approved_at", "")
        if not approved_at:
            errors.append(f"{ref}: approved_at is missing.")
        else:
            try:
                dt.datetime.fromisoformat(approved_at)
            except ValueError:
                errors.append(f"{ref}: approved_at `{approved_at}` is not a valid ISO-8601 timestamp.")


def _iter_log_rows(path: Path):
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def check_write_gate(
    workspace: str | Path,
    *,
    http_log: str | Path | None = None,
    consent_log: str | Path | None = None,
) -> dict[str, Any]:
    ws = Path(workspace)
    log_path = Path(http_log) if http_log else ws / DEFAULT_HTTP_LOG
    consent_path = Path(consent_log) if consent_log else ws / DEFAULT_CONSENT_LOG

    errors: list[str] = []
    summary: dict[str, int] = {
        "read_calls": 0,
        "write_calls": 0,
        "rejected_writes": 0,
        "consent_entries": 0,
    }

    if consent_path.exists():
        entries = _parse_consent_log(consent_path.read_text(encoding="utf-8"))
        summary["consent_entries"] = len(entries)
        _check_consent_entries(entries, errors)

    if log_path.exists():
        for row in _iter_log_rows(log_path):
            method = str(row.get("method", "")).upper()
            rejected = bool(row.get("rejected_reason"))
            if method in WRITE_METHODS:
                if rejected:
                    summary["rejected_writes"] += 1
                    continue
                summary["write_calls"] += 1
                consent_match = row.get("consent_match")
                if not consent_match:
                    aid = row.get("analysis_id") or "<missing>"
                    url = row.get("url") or "<missing>"
                    errors.append(
                        f"{aid}: write call to {method} {url} has no consent_match. "
                        "Add a matching entry to write_consent_log.md (with user_reply_verbatim) "
                        "and re-run via safe_http.py."
                    )
            else:
                summary["read_calls"] += 1

    return {
        "passed": not errors,
        "summary": summary,
        "errors": errors,
        "warnings": [],
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Audit write_consent_log.md vs http_log.jsonl before Stage-3 generation."
    )
    parser.add_argument("workspace")
    parser.add_argument("--http-log", default=None)
    parser.add_argument("--consent-log", default=None)
    return parser.parse_args(argv)


def run(argv=None) -> int:
    args = parse_args(argv)
    result = check_write_gate(
        args.workspace,
        http_log=args.http_log,
        consent_log=args.consent_log,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(run())
