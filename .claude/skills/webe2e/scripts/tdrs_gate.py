#!/usr/bin/env python3
"""
Gate Stage-2 TDRS completion before case.md generation.

The gate does not require every row to be executable. It requires every
analysis row to reach a terminal TDRS decision with evidence, so agents cannot
skip live query / sample backfill and continue with empty UNVERIFIED rows.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {
    "CLOSED": "CLOSED",
    "BLOCKED": "BLOCKED",
    "MANUAL-PREP": "manual-prep",
    "MANUAL_PREP": "manual-prep",
    "MANUAL PREP": "manual-prep",
    "SKIP": "skip",
    "SKIPPED": "skip",
    "UNVERIFIED": "UNVERIFIED",
}
PLACEHOLDER_VALUES = {
    "",
    "...",
    "-",
    "无",
    "n/a",
    "na",
    "todo",
    "to_fill",
    "<to_fill>",
    "<todo>",
}
DEFAULT_MAX_QUERY_ATTEMPTS = 2
DEFAULT_MAX_CREATE_ATTEMPTS = 1
VAGUE_NO_SAMPLE_EVIDENCE_PATTERNS = (
    "no live sample data",
    "no sample data",
    "no data provided",
    "not provided yet",
    "未提供样本",
    "没有提供样本",
    "未提供数据",
    "没有数据",
    "缺少样本",
)
USER_REQUEST_EVIDENCE_PATTERNS = (
    "用户拒绝",
    "用户无法提供",
    "用户明确无法提供",
    "用户明确拒绝",
    "用户确认无",
    "用户确认没有",
    "user declined",
    "user cannot provide",
    "user confirmed no",
)
USER_REQUEST_WITHOUT_OUTCOME_PATTERNS = (
    "已请求",
    "请求材料",
    "请求用户",
    "询问用户",
    "向用户",
    "asked user",
    "requested",
    "用户暂未提供",
    "用户未提供",
    "user unavailable",
    "user did not provide",
)
QUERY_RESULT_SIGNAL_PATTERNS = (
    r"\b[1-5]\d{2}\b",
    r"命中",
    r"匹配",
    r"空结果",
    r"无结果",
    r"未查到",
    r"无数据",
    r"成功",
    r"失败",
    r"超时",
    r"\btimeout\b",
    r"\berror\b",
    r"\breturn(?:ed)?\b",
    r"\bexists?\b",
    r"\bok\b",
)
COMPACT_EVIDENCE_COLUMNS = ("TDRS证据", "tdrs_evidence", "裁决证据", "evidence")


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _normalize_header(text: str) -> str:
    return re.sub(r"\s+", "", text).strip().lower()


def _is_meaningful(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip()
    if not normalized:
        return False
    return normalized.lower() not in PLACEHOLDER_VALUES


def _normalize_status(value: str) -> str | None:
    normalized = value.strip().upper()
    return TERMINAL_STATUSES.get(normalized)


def _parse_int(value: str | None) -> int | None:
    if not value or not value.strip():
        return None
    match = re.search(r"\d+", value)
    if not match:
        return None
    return int(match.group(0))


def parse_analysis_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None

    for raw_line in text.splitlines():
        cells = _split_markdown_table_row(raw_line)
        if not cells:
            headers = None
            continue
        if _is_table_separator(cells):
            continue
        normalized_cells = [_normalize_header(cell) for cell in cells]
        if "分析id" in normalized_cells:
            headers = cells
            continue
        if headers is None:
            continue
        row: dict[str, str] = {}
        for index, header in enumerate(headers):
            row[header.strip()] = cells[index].strip() if index < len(cells) else ""
        analysis_id = _value(row, "分析ID", "analysis_id", "id")
        if not _is_meaningful(analysis_id):
            continue
        rows.append(row)
    return rows


def _value(row: dict[str, str], *names: str) -> str:
    normalized = {_normalize_header(key): value for key, value in row.items()}
    for name in names:
        value = normalized.get(_normalize_header(name))
        if value is not None and _is_meaningful(value):
            return value.strip()
    compact = _compact_evidence_values(row)
    for name in names:
        value = compact.get(_normalize_header(name))
        if value is not None and _is_meaningful(value):
            return value.strip()
    return ""


def _has_any(row: dict[str, str], *names: str) -> bool:
    return any(_is_meaningful(_value(row, name)) for name in names)


def _compact_evidence_values(row: dict[str, str]) -> dict[str, str]:
    normalized = {_normalize_header(key): value for key, value in row.items()}
    raw = ""
    for column in COMPACT_EVIDENCE_COLUMNS:
        candidate = normalized.get(_normalize_header(column), "")
        if candidate and candidate.strip():
            raw = candidate.strip()
            break
    if not raw:
        return {}

    values: dict[str, str] = {}
    free_text_parts: list[str] = []
    for part in re.split(r"[;；]\s*", raw):
        item = part.strip()
        if not item:
            continue
        match = re.match(r"([^=:：]+)\s*[=:：]\s*(.+)$", item)
        if not match:
            free_text_parts.append(item)
            continue
        key = _normalize_header(match.group(1))
        value = match.group(2).strip()
        if key and value:
            values[key] = value
    if free_text_parts:
        evidence_key = _normalize_header("裁决证据")
        existing = values.get(evidence_key, "")
        values[evidence_key] = "；".join(part for part in [existing, *free_text_parts] if part)
    return values


def _contains_any_pattern(value: str, patterns: tuple[str, ...]) -> bool:
    normalized = value.strip().lower()
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns)


def _row_id(row: dict[str, str]) -> str:
    return _value(row, "分析ID", "analysis_id", "id") or "<missing-id>"


def _check_closed(row: dict[str, str], errors: list[str]) -> None:
    analysis_id = _row_id(row)
    required = [
        ("数据要求", ("数据要求", "data_requirement")),
        ("查数API", ("查数API", "query_api", "api")),
        ("查数参数", ("查数参数", "query_params", "params")),
        ("查数结果", ("查数结果", "query_result", "result")),
        ("回填URL", ("回填URL", "backfilled_url", "url")),
        ("裁决证据", ("裁决证据", "evidence", "tdrs_evidence")),
    ]
    for label, names in required:
        if not _has_any(row, *names):
            errors.append(f"{analysis_id}: CLOSED row missing {label}.")


def _check_non_closed(status: str, row: dict[str, str], errors: list[str]) -> None:
    analysis_id = _row_id(row)
    if not _has_any(row, "数据要求", "data_requirement"):
        errors.append(f"{analysis_id}: {status} row missing 数据要求.")
    evidence = _value(row, "裁决证据", "evidence", "tdrs_evidence")
    query_result = _value(row, "查数结果", "query_result")
    query_api = _value(row, "查数API", "query_api", "api")
    if not (_is_meaningful(evidence) or _is_meaningful(query_result)):
        if status == "UNVERIFIED":
            errors.append(f"{analysis_id}: UNVERIFIED row missing attempt evidence.")
        else:
            errors.append(f"{analysis_id}: {status} row missing decision evidence.")
        return

    combined_evidence = " ".join([evidence, query_result])
    if _contains_any_pattern(combined_evidence, VAGUE_NO_SAMPLE_EVIDENCE_PATTERNS):
        errors.append(
            f"{analysis_id}: `{combined_evidence}` is not valid decision evidence. "
            "No live sample data provided is a Stage-2 starting point; ask user "
            "for auth/API/curl or record a real API attempt before terminal classification."
        )

    query_api_filled = _is_meaningful(query_api)
    query_result_filled = _is_meaningful(query_result)
    query_result_has_signal = query_result_filled and _contains_any_pattern(
        query_result, QUERY_RESULT_SIGNAL_PATTERNS
    )
    has_query_attempt = query_api_filled and query_result_filled and query_result_has_signal
    has_user_request = _contains_any_pattern(
        combined_evidence, USER_REQUEST_EVIDENCE_PATTERNS
    )
    has_request_without_outcome = _contains_any_pattern(
        combined_evidence, USER_REQUEST_WITHOUT_OUTCOME_PATTERNS
    )
    if not has_query_attempt and not has_user_request:
        if has_request_without_outcome:
            errors.append(
                f"{analysis_id}: {status} row records that auth/API material was requested, "
                "but has no explicit user outcome. Stop and ask the user; only a "
                "clear decline/cannot-provide/confirmed-no-permission response or a real "
                "per-row API attempt can be terminal evidence."
            )
            return
        if query_api_filled and not query_result_has_signal:
            errors.append(
                f"{analysis_id}: {status} row has `查数API` but `查数结果` lacks a concrete "
                "result signal (HTTP code / 命中 / 空结果 / 失败 / timeout / error / returned). "
                "Run the per-row API call and record the real result."
            )
            return
        errors.append(
            f"{analysis_id}: {status} row has no per-row API attempt (`查数API` + signaled "
            "`查数结果`) and no explicit user-decline evidence. The user-provided curl is "
            "an auth scaffold (cookies / host / headers), not a data answer; extract its "
            "credentials and call this row's target API identified in Phase 1 code analysis."
        )


def _check_attempt_budget(
    row: dict[str, str],
    errors: list[str],
    *,
    max_query_attempts: int,
    max_create_attempts: int,
) -> None:
    analysis_id = _row_id(row)
    query_attempts = _parse_int(_value(row, "查询次数", "query_attempts"))
    if query_attempts is not None and query_attempts > max_query_attempts:
        errors.append(
            f"{analysis_id}: query attempt budget exceeded "
            f"({query_attempts}>{max_query_attempts}). Stop querying and record a terminal decision."
        )
    create_attempts = _parse_int(_value(row, "造数次数", "create_attempts"))
    if create_attempts is not None and create_attempts > max_create_attempts:
        errors.append(
            f"{analysis_id}: create attempt budget exceeded "
            f"({create_attempts}>{max_create_attempts}). Stop creating and record Gate C / manual-prep."
        )


def check_tdrs_gate(
    analysis_file: str | Path,
    *,
    max_query_attempts: int = DEFAULT_MAX_QUERY_ATTEMPTS,
    max_create_attempts: int = DEFAULT_MAX_CREATE_ATTEMPTS,
) -> dict[str, Any]:
    path = Path(analysis_file)
    errors: list[str] = []
    warnings: list[str] = []
    rows = parse_analysis_rows(path)
    if not rows:
        errors.append(
            "No analysis rows found. test_analysis.md must contain a table with 分析ID."
        )

    summary: dict[str, int] = {
        "total": len(rows),
        "CLOSED": 0,
        "BLOCKED": 0,
        "manual-prep": 0,
        "skip": 0,
        "UNVERIFIED": 0,
    }
    seen_ids: set[str] = set()
    for row in rows:
        analysis_id = _row_id(row)
        if analysis_id in seen_ids:
            errors.append(f"{analysis_id}: duplicate 分析ID.")
        seen_ids.add(analysis_id)

        status_raw = _value(row, "TDRS状态", "tdrs_status", "状态")
        status = _normalize_status(status_raw)
        if not status:
            errors.append(
                f"{analysis_id}: missing or invalid TDRS状态 `{status_raw}`. "
                "Expected CLOSED/BLOCKED/manual-prep/skip/UNVERIFIED."
            )
            continue

        summary[status] += 1
        _check_attempt_budget(
            row,
            errors,
            max_query_attempts=max_query_attempts,
            max_create_attempts=max_create_attempts,
        )
        if status == "CLOSED":
            _check_closed(row, errors)
        else:
            _check_non_closed(status, row, errors)

    return {
        "passed": not errors,
        "summary": summary,
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gate Stage-2 TDRS evidence before generating case.md."
    )
    parser.add_argument("analysis_file", help="Path to test_analysis.md.")
    parser.add_argument("--max-query-attempts", type=int, default=DEFAULT_MAX_QUERY_ATTEMPTS)
    parser.add_argument("--max-create-attempts", type=int, default=DEFAULT_MAX_CREATE_ATTEMPTS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.analysis_file)
    if not path.exists():
        result = {
            "passed": False,
            "summary": {"total": 0},
            "errors": [f"analysis file not found: {args.analysis_file}"],
            "warnings": [],
        }
    else:
        result = check_tdrs_gate(
            path,
            max_query_attempts=args.max_query_attempts,
            max_create_attempts=args.max_create_attempts,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
