#!/usr/bin/env python3
"""
safe_http.py — auth-aware HTTP wrapper that enforces write-method gating.

Default policy:
- GET / HEAD: allowed.
- POST / PUT / PATCH / DELETE: rejected unless ALL of the following are true:
  1. `--allow-write` flag is present.
  2. The workspace contains `write_consent_log.md` with a matching entry:
     - `analysis_ids` contains the value passed to `--analysis-id`
     - `method` (case-insensitive) equals the request method
     - `url_pattern` (fnmatch glob) matches the request URL
     - `user_reply_verbatim` is non-empty
  3. The matching entry's `approved_at` (ISO-8601 with timezone) is no older
     than `--max-consent-age-minutes` (default 30).

Every invocation appends a JSONL audit row to `http_log.jsonl` in the
workspace, including rejections. Downstream `write_gate.py` cross-checks
that every write call in this log has a non-null `consent_match`.

Test design: pass `transport=...` and `now=...` to `run()` to inject HTTP and
clock so tests are deterministic without real network or wall-clock time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import io
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Callable, Optional, Sequence


READ_ONLY_METHODS = ("GET", "HEAD")
SUPPORTED_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE")
DEFAULT_CONSENT_LOG = "write_consent_log.md"
DEFAULT_HTTP_LOG = "http_log.jsonl"
DEFAULT_MAX_CONSENT_AGE_MIN = 30


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
        else:
            if current is not None and not stripped:
                continue
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


def _entry_id(entry: dict[str, Any], index: int) -> str:
    h = hashlib.sha256()
    h.update(str(index).encode())
    h.update(str(entry.get("approved_at", "")).encode())
    h.update(str(entry.get("url_pattern", "")).encode())
    h.update(str(entry.get("method", "")).encode())
    return h.hexdigest()[:12]


def _match_consent(
    entries: list[dict[str, Any]],
    *,
    analysis_id: str,
    method: str,
    url: str,
    now: dt.datetime,
    max_age_minutes: int,
) -> tuple[Optional[dict[str, Any]], Optional[str], Optional[str]]:
    """Return (matched_entry, entry_id, reason_if_no_match)."""
    if not entries:
        return None, None, "no entries in write_consent_log.md"
    method_upper = method.upper()
    failures: list[str] = []
    for idx, entry in enumerate(entries):
        if analysis_id not in entry.get("analysis_ids", []):
            failures.append(f"entry#{idx}: analysis_id mismatch")
            continue
        if str(entry.get("method", "")).upper() != method_upper:
            failures.append(f"entry#{idx}: method mismatch")
            continue
        url_pattern = entry.get("url_pattern", "")
        if not url_pattern or not fnmatch.fnmatch(url, url_pattern):
            failures.append(f"entry#{idx}: url_pattern mismatch")
            continue
        reply = (entry.get("user_reply_verbatim") or "").strip()
        if not reply:
            failures.append(f"entry#{idx}: empty user_reply_verbatim")
            continue
        approved_at_raw = entry.get("approved_at", "")
        approved_at: Optional[dt.datetime] = None
        try:
            approved_at = dt.datetime.fromisoformat(approved_at_raw)
        except ValueError:
            failures.append(f"entry#{idx}: invalid approved_at `{approved_at_raw}`")
            continue
        if approved_at.tzinfo is None or now.tzinfo is None:
            age_minutes = abs((now.replace(tzinfo=None) - approved_at.replace(tzinfo=None)).total_seconds()) / 60
        else:
            age_minutes = abs((now - approved_at).total_seconds()) / 60
        if age_minutes > max_age_minutes:
            failures.append(
                f"entry#{idx}: approved_at {approved_at_raw} older than {max_age_minutes}min (age={age_minutes:.1f}min)"
            )
            continue
        return entry, _entry_id(entry, idx), None
    return None, None, "; ".join(failures) or "no matching consent entry"


def _append_audit(log_path: Path, row: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _default_transport(method: str, url: str, headers: dict[str, str], body: Optional[bytes]) -> dict[str, Any]:
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"status": resp.status, "body": resp.read().decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": e.read().decode("utf-8", "replace")}


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Auth-aware HTTP wrapper. GET/HEAD allowed by default; "
            "POST/PUT/PATCH/DELETE require --allow-write plus a matching entry in "
            "write_consent_log.md."
        )
    )
    parser.add_argument("--workspace", default=".", help="Workspace dir containing consent + audit logs.")
    parser.add_argument("--analysis-id", required=True, help="Analysis row id this call is attributed to.")
    parser.add_argument("--method", required=True, choices=list(SUPPORTED_METHODS) + [m.lower() for m in SUPPORTED_METHODS])
    parser.add_argument("--url", required=True)
    parser.add_argument("--header", action="append", default=[], help="Extra header NAME=VALUE; can repeat.")
    parser.add_argument("--body", default=None, help="Request body string, or @path/to/file.")
    parser.add_argument("--allow-write", action="store_true", help="Required for write methods.")
    parser.add_argument("--consent-log", default=None)
    parser.add_argument("--http-log", default=None)
    parser.add_argument("--max-consent-age-minutes", type=int, default=DEFAULT_MAX_CONSENT_AGE_MIN)
    return parser.parse_args(argv)


def _load_body(body_arg: Optional[str]) -> Optional[bytes]:
    if body_arg is None:
        return None
    if body_arg.startswith("@"):
        return Path(body_arg[1:]).read_bytes()
    return body_arg.encode("utf-8")


def _parse_headers(header_args: Sequence[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw in header_args:
        if "=" not in raw:
            continue
        name, _, value = raw.partition("=")
        headers[name.strip()] = value.strip()
    return headers


def run(
    argv: Optional[Sequence[str]] = None,
    *,
    transport: Optional[Callable[..., dict[str, Any]]] = None,
    now: Optional[Callable[[], dt.datetime]] = None,
) -> int:
    args = parse_args(argv)
    method = args.method.upper()
    workspace = Path(args.workspace)
    consent_path = Path(args.consent_log) if args.consent_log else workspace / DEFAULT_CONSENT_LOG
    log_path = Path(args.http_log) if args.http_log else workspace / DEFAULT_HTTP_LOG
    ts = (now() if now else dt.datetime.now(dt.timezone.utc)).isoformat()

    base_row: dict[str, Any] = {
        "ts": ts,
        "analysis_id": args.analysis_id,
        "method": method,
        "url": args.url,
        "allow_write": bool(args.allow_write),
        "status": None,
        "consent_match": None,
        "rejected_reason": None,
    }

    if method not in READ_ONLY_METHODS:
        if not args.allow_write:
            base_row["rejected_reason"] = "missing_allow_write"
            _append_audit(log_path, base_row)
            print(
                f"write method {method} requires --allow-write plus a matching "
                "entry in write_consent_log.md.",
                file=sys.stderr,
            )
            return 2

        if not consent_path.exists():
            base_row["rejected_reason"] = "consent_log_missing"
            _append_audit(log_path, base_row)
            print(
                f"write_consent_log.md not found at {consent_path}. Append an "
                "entry with the user's verbatim reply before retrying.",
                file=sys.stderr,
            )
            return 3

        entries = _parse_consent_log(consent_path.read_text(encoding="utf-8"))
        now_dt = now() if now else dt.datetime.now(dt.timezone.utc)
        matched, entry_id, reason = _match_consent(
            entries,
            analysis_id=args.analysis_id,
            method=method,
            url=args.url,
            now=now_dt,
            max_age_minutes=args.max_consent_age_minutes,
        )
        if matched is None:
            base_row["rejected_reason"] = f"consent_no_match: {reason}"
            _append_audit(log_path, base_row)
            print(
                f"no matching consent entry for analysis_id={args.analysis_id} "
                f"method={method} url={args.url}: {reason}",
                file=sys.stderr,
            )
            return 3
        base_row["consent_match"] = entry_id

    headers = _parse_headers(args.header)
    body = _load_body(args.body)
    transport_fn = transport or _default_transport
    try:
        result = transport_fn(method, args.url, headers, body)
    except Exception as exc:
        base_row["rejected_reason"] = f"transport_error: {exc}"
        _append_audit(log_path, base_row)
        print(f"transport error: {exc}", file=sys.stderr)
        return 4

    base_row["status"] = result.get("status")
    _append_audit(log_path, base_row)
    body_text = result.get("body", "")
    if body_text:
        sys.stdout.write(body_text if isinstance(body_text, str) else str(body_text))
        sys.stdout.write("\n")
    return 0 if isinstance(base_row["status"], int) and base_row["status"] < 400 else 4


if __name__ == "__main__":
    sys.exit(run())
