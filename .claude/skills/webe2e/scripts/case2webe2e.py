from __future__ import annotations

import argparse
import io
import os
import shutil
import sqlite3
import tempfile
from collections import Counter
import json
import re
import subprocess
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import requests


BASE_URL = "https://q9q0hn98.fn.bytedance.net"
WEBE2E_PLATFORM_LIST_URL = "https://po3gp9uh.fn.bytedance.net/getWebE2EPlatform"
WEBE2E_PLATFORM_DETAIL_URL = "https://po3gp9uh.fn.bytedance.net/getWebE2EPlatformDetail"
MARKDOWN_TO_MIDSCENE_URL = f"{BASE_URL}/ui2step/markdown2midscene"
CREATE_CASE_GROUP_URL = (
    "https://ttat-openapi-sg.tiktok-row.net/ui/web_e2e/create_case_group"
)
EDIT_CASE_GROUP_URL = (
    "https://ttat-openapi-sg.tiktok-row.net/ui/web_e2e/case_group/edit_with_cases"
)
GET_DYNAMIC_TOKEN_URL = "https://ttugqa-sg.tiktok-row.org/ttugqa/user/get_token"
CREATE_TASK_URL = "https://ttat-openapi-sg.tiktok-row.net/ui/web_e2e/create_task"
QUERY_TASK_EXECUTION_URL = (
    "https://ttat-openapi-sg.tiktok-row.net/ui/task/query_task_execution"
)
QUERY_TASK_LIST_URL = "https://ttat-openapi-sg.tiktok-row.net/ui/task/query_task_list"
QUERY_TASK_CASE_EXECUTION_URL = (
    "https://ttat-openapi-sg.tiktok-row.net/ui/task/query_task_case_execution"
)
QUERY_TASK_CASE_NODE_EXECUTION_URL = (
    "https://ttat-openapi-sg.tiktok-row.net/ui/task/query_task_case_node_execution"
)
X_CUSTOM_TOKEN = "fb1202cb29e923298f002b71e0889cc6"
TTAT_UI_ORIGIN = "https://ttat-us.byteintl.net"
TTAT_UI_REFERER = f"{TTAT_UI_ORIGIN}/"
TTAT_UI_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)
TTAT_UI_SEC_CH_UA = '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"'
TIMEOUT = 900
DEFAULT_EXEC_ENV = {"ttat_test_platform": "vitest", "PLAN_MODEL": "db20"}
DEFAULT_TEMPLATE_ID = 269368
DEFAULT_BIZ = 1988
DEFAULT_EXE_PLATFORM = "faas"
TASK_LINK_TEMPLATE = (
    "https://ttat-us.byteintl.net/web/trigger/tasklist/taskcaselist?task_id={task_id}"
)
TASK_CASE_DETAIL_LINK_TEMPLATE = "https://ttat-us.byteintl.net/web/trigger/tasklist/taskcaselist/detail?task_id={task_id}&case_execution_id={case_execution_id}"
MARKDOWN_REPORT_ARCHIVE_LINK_TEMPLATE = "https://tosv-sg.tiktok-row.org/obj/tiktok-ttat-uimost-sg/webui/{task_id}_{case_execution_id}.md.tar"
HTML_REPORT_LINK_TEMPLATE = "https://tosv-sg.tiktok-row.org/obj/tiktok-ttat-uimost-sg/webui/{task_id}_{case_execution_id}.html"
ANALYSIS_OVERVIEW_START = "<!-- webe2e-analysis-overview:start -->"
ANALYSIS_OVERVIEW_END = "<!-- webe2e-analysis-overview:end -->"
ANALYSIS_DETAIL_START = "<!-- webe2e-analysis-detail:start -->"
ANALYSIS_DETAIL_END = "<!-- webe2e-analysis-detail:end -->"
DEFAULT_POLL_INTERVAL = 30
DEFAULT_MAX_WAIT_SECONDS = 7200
DEFAULT_PAGE_SIZE = 100
MAX_REASONING_SNIPPET = 280
MAX_SCREENSHOT_SUMMARY = 180
DETAIL_ANALYSIS_SECONDS_PER_CASE = 20
DETAIL_ANALYSIS_FIXED_OVERHEAD_SECONDS = 30
CASE_META_COMMENT_PREFIX = "webe2e-analysis-case-meta:"
DEFAULT_EXECUTION_MODE = "ttat"
DEFAULT_LOCAL_RUNNER = "playwright-cli"
DEFAULT_LOCAL_CASE_CONCURRENCY = 10
SUPPORTED_EXECUTION_MODES = {"ttat", "local"}
SUPPORTED_LOCAL_RUNNERS = {"playwright-cli"}
SUPPORTED_RUN_ENVS = {"boe", "local", "online", "ppe"}
LOCAL_PLAN_FILENAME = "local_execution_plan.json"
LOCAL_ARTIFACTS_DIRNAME = "test_result"
YAML_SCRIPTS_DIRNAME = "yaml-scripts"
MIDSCENE_YAML_TEMPLATE_FILENAME = "midscene_template.yaml"
SUPPORTED_CASE_PRIORITIES = {"P0", "P1", "P2", "P3"}
CASE_PRIORITY_FILTER_CHOICES = (*sorted(SUPPORTED_CASE_PRIORITIES), "all")
CASE_HEADING_PATTERN = re.compile(r"^####\s+(?P<title>.+)$", re.MULTILINE)
EXPECTED_RESULT_HEADING_PATTERN = re.compile(
    r"^#{5,}\s+\*\*预期结果\*\*", re.MULTILINE
)
CASE_NODE_HEADING_PATTERN = re.compile(
    r"^#{5,}\s+\*\*(?P<label>操作步骤|预期结果)\*\*\s*(?P<inline>.*)$",
    re.MULTILINE,
)
CASE_PRIORITY_PATTERN = re.compile(
    r"\[(P[0-3])\]|\*\*\[priority\]\*\*\s*(P[0-3])", re.IGNORECASE
)
CASE_PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
CASE_PRIORITY_INLINE_LABEL = re.compile(r"\*\*\[priority\]\*\*", re.IGNORECASE)
BITS_CASE_DETAIL_URL_RE = re.compile(
    r"https://bits\.bytedance\.net/[a-zA-Z0-9_\-./?#=&%+]+"
)

DEFAULT_ENV_TEMPLATE = """# Web E2E 执行环境配置
# 创建者邮箱前缀（必填，用于 TTAT 用例和任务创建）
creator=
# 测试平台，如 live-campaign, your-platform
platform=live-campaign
# 执行模式: ttat, local
EXECUTION_MODE=ttat
# 本地执行 runner: playwright-cli
LOCAL_RUNNER=playwright-cli
# 本地 case 级并发度
LOCAL_CASE_CONCURRENCY=10
# 本地登录态来源: chrome-profile, none
STORAGE_STATE_MODE=chrome-profile
# Chrome user data dir；空值表示使用当前系统默认目录
CHROME_USER_DATA_DIR=
# Chrome profile 名称；空值表示必须先自动探测/展示候选，不得直接假设 Default
CHROME_PROFILE_NAME=
# 运行环境: local, boe, ppe, online
RUN_ENV=ppe
# 测试机房: sg, boe, ppe 等
TEST_IDC=sg
# 泳道标识（可选）
SWIMLANE=
# 任务超时时间（分钟）
TASK_TIMEOUT=10
# === Bits 用例与 TTAT create_case_group / edit_with_cases（extras.bitsConfig.url）===
# 归档到 Bits 后 save_result.json 会被 case2webe2e 自动读取；也可手动指定：
BITS_CASE_DETAIL_URL=
"""


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _normalize_case_priority(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().upper()
    return normalized if normalized in SUPPORTED_CASE_PRIORITIES else None


def _pick_highest_case_priority(values: list[str | None]) -> str | None:
    normalized_values = [
        item for item in (_normalize_case_priority(v) for v in values) if item
    ]
    if not normalized_values:
        return None
    return min(normalized_values, key=lambda item: CASE_PRIORITY_RANK[item])


def _extract_heading_case_priority(title: str) -> str | None:
    for candidate in CASE_PRIORITY_PATTERN.finditer(title):
        if CASE_PRIORITY_INLINE_LABEL.search(candidate.group(0)):
            continue
        return _normalize_case_priority(candidate.group(1) or candidate.group(2))
    return None


def _extract_case_priorities(markdown: str) -> list[str | None]:
    matches = list(CASE_HEADING_PATTERN.finditer(markdown))
    priorities: list[str | None] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        block = markdown[start:end]
        heading_priority = _extract_heading_case_priority(match.group("title"))
        if heading_priority:
            priorities.append(heading_priority)
            continue
        inline_values = [
            candidate.group(1) or candidate.group(2)
            for candidate in CASE_PRIORITY_PATTERN.finditer(block)
        ]
        priorities.append(_pick_highest_case_priority(inline_values))
    return priorities


def _iter_case_heading_blocks(
    markdown: str,
) -> list[tuple[re.Match[str], str]]:
    matches = list(CASE_HEADING_PATTERN.finditer(markdown))
    blocks: list[tuple[re.Match[str], str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        blocks.append((match, markdown[start:end]))
    return blocks


def _count_expected_result_nodes(block: str) -> int:
    return max(1, len(EXPECTED_RESULT_HEADING_PATTERN.findall(block)))


def _normalize_case_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_case_node_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("**[") and "]**" in line:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _extract_case_titles_in_order(markdown: str) -> list[str]:
    return [
        _normalize_case_heading(match.group("title"))
        for match in CASE_HEADING_PATTERN.finditer(markdown)
    ]


def _parse_case_expected_result_structure(markdown: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for case_index, (match, block) in enumerate(_iter_case_heading_blocks(markdown)):
        title = _normalize_case_heading(match.group("title"))
        heading_priority = _extract_heading_case_priority(title)
        inline_values = [
            candidate.group(1) or candidate.group(2)
            for candidate in CASE_PRIORITY_PATTERN.finditer(block)
        ]
        priority = heading_priority or _pick_highest_case_priority(inline_values)
        nodes = list(CASE_NODE_HEADING_PATTERN.finditer(block))
        steps: list[dict[str, Any]] = []
        step_index = -1
        for node_index, node in enumerate(nodes):
            label = node.group("label")
            section_end = (
                nodes[node_index + 1].start() if node_index + 1 < len(nodes) else len(block)
            )
            inline = node.group("inline").strip()
            body = block[node.end() : section_end].strip()
            text = _normalize_case_node_text(
                "\n".join(part for part in [inline, body] if part)
            )
            if label == "操作步骤":
                step_index += 1
                steps.append({"step_index": step_index, "expectations": []})
                continue
            if label != "预期结果":
                continue
            if step_index < 0:
                step_index = 0
                steps.append({"step_index": step_index, "expectations": []})
            expectation_index = len(steps[step_index]["expectations"])
            steps[step_index]["expectations"].append(
                {
                    "path": [step_index, expectation_index],
                    "expected_result": text,
                }
            )
        cases.append(
            {
                "case_index": case_index,
                "case_title": title,
                "priority": priority,
                "steps": steps,
            }
        )
    return cases


def _case_task_path_groups(case: dict[str, Any]) -> list[list[list[int]]]:
    steps = [
        step for step in case.get("steps", []) if isinstance(step.get("expectations"), list)
    ]
    steps_with_expectations = [step for step in steps if step["expectations"]]
    if not steps_with_expectations:
        return [[]]
    if len(steps_with_expectations) == 1:
        return [[node["path"]] for node in steps_with_expectations[0]["expectations"]]

    first_step = steps_with_expectations[0]
    tail_steps = steps_with_expectations[1:]
    if len(tail_steps) == 1:
        return [
            [
                node["path"]
                for step in steps_with_expectations
                for node in step["expectations"]
            ]
        ]
    if first_step["expectations"] and len(tail_steps) >= 2:
        prefix_paths = [node["path"] for node in first_step["expectations"]]
        return [
            prefix_paths + [node["path"] for node in tail_step["expectations"]]
            for tail_step in tail_steps
        ]

    return [
        [node["path"] for node in step["expectations"]]
        for step in steps_with_expectations
    ]


def _extract_case_execution_metadata(
    markdown: str,
) -> tuple[list[str | None], list[str], list[dict[str, Any]]]:
    priorities: list[str | None] = []
    titles: list[str] = []
    path_groups: list[dict[str, Any]] = []

    for case in _parse_case_expected_result_structure(markdown):
        paths = [
            node["path"]
            for step in case.get("steps", [])
            for node in step.get("expectations", [])
        ]
        priorities.append(case["priority"])
        titles.append(case["case_title"])
        path_groups.append({"case_index": case["case_index"], "paths": paths})

    return priorities, titles, path_groups


def _extract_case_metadata_for_midscene(
    markdown: str,
) -> tuple[list[str | None], list[str]]:
    priorities, titles, _ = _extract_case_execution_metadata(markdown)
    return priorities, titles


def _strip_trailing_bits_url_junk(url: str) -> str:
    return url.rstrip(".,;)'\"」）]")


def _first_bits_case_detail_url_in_text(text: str) -> str | None:
    match = BITS_CASE_DETAIL_URL_RE.search(text)
    if not match:
        return None
    return _strip_trailing_bits_url_junk(match.group(0))


def _load_save_result_bits_url(case_md: Path) -> str | None:
    path = case_md.parent / "save_result.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None

    detail_url = data.get("case_detail_url")
    detail_str = detail_url.strip() if isinstance(detail_url, str) else None
    return detail_str if detail_str else None


def _load_save_result_case_expectations(case_md: Path) -> list[dict[str, Any]] | None:
    path = case_md.parent / "save_result.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    entries = data.get("case_expectations")
    return entries if isinstance(entries, list) else None


def _replace_marked_section(
    content: str, start_marker: str, end_marker: str, section_body: str
) -> str:
    block = f"{start_marker}\n{section_body.rstrip()}\n{end_marker}"
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL
    )
    if pattern.search(content):
        return pattern.sub(block, content, count=1)
    suffix = "\n\n" if content.strip() else ""
    return content.rstrip() + suffix + block + "\n"


def _remove_marked_section(content: str, start_marker: str, end_marker: str) -> str:
    pattern = re.compile(
        r"\n?" + re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n?",
        re.DOTALL,
    )
    updated = pattern.sub("\n", content)
    return updated.rstrip() + ("\n" if updated.strip() else "")


def _extract_marked_section(
    content: str, start_marker: str, end_marker: str
) -> str | None:
    pattern = re.compile(
        re.escape(start_marker) + r"\n?(.*?)\n?" + re.escape(end_marker),
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return None
    return match.group(1).strip()


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json_maybe(raw: str) -> Any:
    text = raw.strip()
    if not text:
        raise ValueError("empty response body")
    return json.loads(text)


def _request_json(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError:
        payload = _load_json_maybe(response.text)
    if isinstance(payload, str):
        payload = _load_json_maybe(payload)
    return payload


def _coerce_items_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("data"),
        payload.get("list"),
        payload.get("items"),
        payload.get("platforms"),
        payload.get("variables"),
        payload.get("envConfig"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if not isinstance(candidate, dict):
            continue
        nested_candidates = [
            candidate.get("data"),
            candidate.get("list"),
            candidate.get("items"),
            candidate.get("platforms"),
            candidate.get("variables"),
            candidate.get("envConfig"),
        ]
        for nested_candidate in nested_candidates:
            if isinstance(nested_candidate, list):
                return [item for item in nested_candidate if isinstance(item, dict)]
    return []


def _coerce_domain(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""

    candidates = [payload, payload.get("data")]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        domain = str(candidate.get("domain") or "").strip()
        if domain:
            return domain
    return ""


def _fetch_registered_platforms() -> list[dict[str, Any]]:
    payload = _request_json(WEBE2E_PLATFORM_LIST_URL, params={"withMeta": "true"})
    items = _coerce_items_list(payload)
    platforms: list[dict[str, Any]] = []
    for item in items:
        platform = str(item.get("platform") or "").strip()
        name_zh = str(item.get("nameZh") or item.get("name_zh") or "").strip()
        domain = str(item.get("domain") or "").strip()
        poc = str(item.get("poc") or "").strip()
        if not platform:
            continue
        platforms.append(
            {
                "nameZh": name_zh,
                "platform": platform,
                "domain": domain,
                "poc": poc,
            }
        )
    return platforms


def _fetch_platform_detail(platform: str, domain: str = "") -> dict[str, Any]:
    params = {"platform": platform, "withMeta": "true"}
    if domain:
        params["domain"] = domain
    payload = _request_json(WEBE2E_PLATFORM_DETAIL_URL, params=params)
    items = _coerce_items_list(payload)
    details: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("key") or "").strip()
        if not key:
            continue
        value = item.get("value")
        use_default = bool(item.get("useDefault"))
        description = str(item.get("description") or "").strip()
        normalized_value = "" if value is None else str(value)
        details.append(
            {
                "key": key,
                "value": normalized_value,
                "useDefault": use_default,
                "needsInput": not use_default and not normalized_value,
                "description": description,
            }
        )
    return {
        "platform": platform,
        "domain": _coerce_domain(payload) or domain,
        "variables": details,
    }


def _extract_midscene_content(response_text: str) -> list[Any]:
    try:
        payload = _load_json_maybe(response_text)
    except ValueError:
        stripped = response_text.strip()
        if not stripped:
            raise
        return [stripped]

    if isinstance(payload, str):
        try:
            payload = _load_json_maybe(payload)
        except ValueError:
            stripped = payload.strip()
            if not stripped:
                raise ValueError("empty midscene_content string")
            return [stripped]

    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        raise ValueError("unexpected markdown2midscene response type")

    if payload.get("code") not in (None, 0, "0"):
        raise ValueError(
            f"markdown2midscene failed: code={payload.get('code')} msg={payload.get('msg')}"
        )

    candidates = [
        payload.get("midscene_content"),
        payload.get("data", {}).get("midscene_content")
        if isinstance(payload.get("data"), dict)
        else None,
        payload.get("data"),
    ]

    for candidate in candidates:
        if isinstance(candidate, str):
            try:
                candidate = _load_json_maybe(candidate)
            except Exception:
                continue
        if isinstance(candidate, list):
            return candidate

    raise ValueError("cannot locate midscene_content in markdown2midscene response")


def _guess_title(case_md: Path, markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return case_md.stem


def _default_creator() -> str:
    result = subprocess.run(
        ["git", "config", "user.email"],
        capture_output=True,
        text=True,
        check=False,
    )
    email = result.stdout.strip()
    if not email:
        raise SystemExit(
            "creator is required; pass --creator or configure git user.email"
        )
    return email.split("@", 1)[0]


def _get_env_template_path() -> Path:
    """Return the path to the env template file in resources directory."""
    return Path(__file__).resolve().parent.parent / "resources" / ".env"


def _get_default_env_path(case_md: Path) -> Path:
    """Return the default env file path next to case.md."""
    return case_md.resolve().parent / ".env"


def _get_default_report_path(case_md: Path) -> Path:
    return case_md.resolve().parent / "test_report.md"


def _resolve_report_path(case_md: Path, explicit_path: str | None) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()
    return _get_default_report_path(case_md)


def _resolve_local_plan_path(case_md: Path, explicit_path: str | None) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()
    return case_md.resolve().parent / LOCAL_PLAN_FILENAME


def _slugify_path_component(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "-", value.strip()).strip("-._")
    return normalized or fallback


def _get_local_artifacts_root(case_md: Path) -> Path:
    return case_md.resolve().parent / LOCAL_ARTIFACTS_DIRNAME


def _build_local_case_artifacts(
    case_md: Path, case_name: str, index: int
) -> dict[str, str]:
    case_slug = _slugify_path_component(case_name, f"case-{index}")
    case_dir = _get_local_artifacts_root(case_md) / f"{index:02d}-{case_slug}"
    return {
        "case_dir": str(case_dir),
    }


def _get_yaml_scripts_dir(case_md: Path, explicit_path: str | None = None) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()
    return case_md.resolve().parent / YAML_SCRIPTS_DIRNAME


def _build_yaml_filename(case_name: str, index: int) -> str:
    case_identifier = _extract_case_identifier(case_name)
    if case_identifier:
        return f"{case_identifier}.yaml"
    slug = _slugify_path_component(case_name, f"case-{index}")
    return f"{slug}.yaml"


def _extract_case_identifier(value: str) -> str:
    match = re.search(r"\b(?:TC-)?(WEB-\d+)\b", value or "", re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _split_flow_into_url_and_steps(
    flow: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Pull the first {url: X} step out of flow to serve as web.url.

    Remaining url steps stay in the flow so multi-page cases still work; only
    the leading one is promoted to the document-level web.url.
    """
    web_url = ""
    remaining: list[dict[str, Any]] = []
    promoted = False
    for step in flow or []:
        if (
            not promoted
            and isinstance(step, dict)
            and isinstance(step.get("url"), str)
            and step["url"].strip()
        ):
            web_url = step["url"].strip()
            promoted = True
            continue
        remaining.append(step)
    return web_url, remaining


def _extract_midscene_flow_preserving(item: Any) -> list[dict[str, Any]]:
    """Extract a midscene flow that preserves aiAssert, sleep, and other step kinds.

    Unlike _extract_flow, this keeps every single-key mapping the markdown2midscene
    response produced so the emitted YAML can be executed by midscene directly.
    Falls back to _extract_flow when the raw item does not expose a structured
    flow list.
    """
    if isinstance(item, dict) and isinstance(item.get("flow"), list):
        flow: list[dict[str, Any]] = []
        for step in item["flow"]:
            if not isinstance(step, dict) or not step:
                continue
            cleaned: dict[str, Any] = {}
            for key, value in step.items():
                if value is None:
                    continue
                if isinstance(value, str):
                    stripped = value.strip()
                    if not stripped:
                        continue
                    cleaned[str(key)] = stripped
                else:
                    cleaned[str(key)] = value
            if cleaned:
                flow.append(cleaned)
        if flow:
            return flow
    return _extract_flow(item)


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(str(value), ensure_ascii=False)


def _decode_maybe_json_string(value: Any) -> str:
    text = str(value or "").strip()
    for _ in range(2):
        if not (len(text) >= 2 and text.startswith("\"") and text.endswith("\"")):
            break
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            break
        if not isinstance(decoded, str):
            break
        text = decoded.strip()
    return text


def _format_yaml_task_name(value: Any) -> str:
    text = _decode_maybe_json_string(value)
    text = re.sub(
        r"\s*\n\s*\*\*\[analysis-id\]\*\*\s*(WEB-\d+)\s*-\s*",
        r" / \1 / ",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", text).strip()


def _format_ai_instruction_text(value: Any) -> str:
    text = _decode_maybe_json_string(value)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return text

    assertion_index = next(
        (index for index, line in enumerate(lines) if line.rstrip(":：") == "断言"),
        -1,
    )
    if assertion_index < 0:
        return "\n".join(lines)

    step_lines = lines[:assertion_index]
    assertion_lines = lines[assertion_index + 1 :]
    formatted: list[str] = ["步骤:"]
    for index, line in enumerate(step_lines, start=1):
        content = re.sub(r"^\d+[.)、]\s*", "", line).strip()
        formatted.append(f"{index}.{content}")
    formatted.append("断言：")
    for index, line in enumerate(assertion_lines, start=1):
        content = re.sub(r"^\d+[.)、]\s*", "", line).strip()
        formatted.append(f"{index}.{content}")
    return "\n".join(formatted)


def _yaml_inline_scalar(value: Any) -> str:
    if not isinstance(value, str):
        return _yaml_scalar(value)
    text = _decode_maybe_json_string(value)
    if not text:
        return "\"\""
    if (
        "\n" in text
        or text[0] in "-?:,[]{}#&*!|>" + chr(39) + "\"%@`"
        or re.search(r"^\s|[\r\t]|:\s", text)
    ):
        return _yaml_scalar(text)
    return text


def _append_yaml_value(lines: list[str], prefix: str, key: str, value: Any) -> None:
    rendered = _format_ai_instruction_text(value) if key == "ai" else value
    if isinstance(rendered, str) and "\n" in rendered:
        lines.append(f"{prefix}{key}: |")
        block_indent = " " * (len(prefix) + 2)
        for line in rendered.splitlines():
            lines.append(f"{block_indent}{line}")
        return
    lines.append(f"{prefix}{key}: {_yaml_inline_scalar(rendered)}")


def _render_midscene_yaml_document(
    web_url: str, task_name: str, flow: list[dict[str, Any]]
) -> str:
    lines: list[str] = ["web:", f"  url: {_yaml_scalar(web_url or str())}", "", "tasks:"]
    lines.append(f"  - name: {_yaml_inline_scalar(_format_yaml_task_name(task_name))}")
    lines.append("    flow:")
    emitted = False
    for step in flow or []:
        if not isinstance(step, dict) or not step:
            continue
        items = list(step.items())
        first_key, first_val = items[0]
        _append_yaml_value(lines, f"      - ", first_key, first_val)
        for key, val in items[1:]:
            _append_yaml_value(lines, "        ", key, val)
        emitted = True
    if not emitted:
        lines.append("      []")
    return "\n".join(lines) + "\n"


def _resolve_analysis_report_path(
    case_md_arg: str | None, explicit_path: str | None
) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()
    if case_md_arg:
        return _get_default_report_path(Path(case_md_arg).expanduser().resolve())
    return (Path.cwd() / "test_report.md").resolve()


def _load_or_init_report(path: Path) -> str:
    if path.is_file():
        return _read_text(path)
    return "# Web E2E Test Report\n"


def _find_env_file(explicit_env: str | None, case_md: Path) -> Path | None:
    if explicit_env:
        path = Path(explicit_env).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"env file not found: {path}")
        return path

    candidates = [
        _get_default_env_path(case_md),
        Path.cwd() / ".env",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _find_task_md(case_md: Path) -> Path | None:
    start_dir = case_md.resolve().parent
    for directory in [start_dir, *start_dir.parents]:
        candidate = directory / "task.md"
        if candidate.is_file():
            return candidate
    return None


def _extract_task_var_from_line(line: str, key: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""

    if "|" in stripped:
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == key:
            value = cells[1].strip().strip("`")
            return value

    patterns = [
        rf"^[-*]\s*`?{re.escape(key)}`?\s*[:=：]\s*`?([^`#\n]+?)`?\s*$",
        rf"^`?{re.escape(key)}`?\s*[:=：]\s*`?([^`#\n]+?)`?\s*$",
    ]
    for pattern in patterns:
        match = re.match(pattern, stripped, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_task_defaults(task_md: Path | None) -> dict[str, str]:
    if task_md is None:
        return {}

    content = _read_text(task_md)
    extracted: dict[str, str] = {}
    keys = ["RUN_ENV", "SWIMLANE", "TEST_IDC", "PPE_SWIMLANE", "BOE_SWIMLANE"]

    for line in content.splitlines():
        for key in keys:
            if key in extracted and extracted[key]:
                continue
            value = _extract_task_var_from_line(line, key)
            if value:
                extracted[key] = value

    if not extracted.get("SWIMLANE"):
        if extracted.get("PPE_SWIMLANE"):
            extracted["SWIMLANE"] = extracted["PPE_SWIMLANE"]
        elif extracted.get("BOE_SWIMLANE"):
            extracted["SWIMLANE"] = extracted["BOE_SWIMLANE"]

    return {
        key: value
        for key, value in extracted.items()
        if key in {"RUN_ENV", "SWIMLANE", "TEST_IDC"} and value
    }


def _apply_env_defaults(template_content: str, defaults: dict[str, str]) -> str:
    content = template_content
    for key in ["RUN_ENV", "SWIMLANE", "TEST_IDC"]:
        value = defaults.get(key)
        if not value:
            continue
        content = re.sub(
            rf"(?m)^{re.escape(key)}=.*$",
            f"{key}={value}",
            content,
        )
    return content


def _parse_env_file(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}

    parsed: dict[str, str] = {}
    for line in _read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")
    return parsed


def _build_exec_env(
    args: argparse.Namespace, env_values: dict[str, str]
) -> dict[str, str]:
    exec_env: dict[str, str] = dict(DEFAULT_EXEC_ENV)

    # Reserved keys that are not exec env parameters
    reserved_keys = {"creator"}

    # Add all env values (including custom variables) except reserved keys
    for key, value in env_values.items():
        if key not in reserved_keys and value:
            exec_env[key] = value

    # Command line overrides take precedence
    overrides = {
        "platform": args.platform,
        "RUN_ENV": args.run_env,
        "TEST_IDC": args.test_idc,
        "BOE_SWIMLANE": args.boe_swimlane,
        "PPE_SWIMLANE": args.ppe_swimlane,
    }
    for key, value in overrides.items():
        if value:
            exec_env[key] = value

    run_env = _resolve_run_env(args, exec_env)
    if run_env:
        exec_env["RUN_ENV"] = run_env

    # Handle SWIMLANE compatibility (map to BOE_SWIMLANE or PPE_SWIMLANE based on RUN_ENV)
    swimlane = exec_env.get("SWIMLANE", "")
    if swimlane:
        if run_env == "boe":
            exec_env["BOE_SWIMLANE"] = swimlane
        elif run_env == "ppe":
            exec_env["PPE_SWIMLANE"] = swimlane
    return exec_env


def _normalize_choice(
    value: str | None, *, default: str, supported: set[str], field_name: str
) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return default
    if normalized not in supported:
        supported_text = ", ".join(sorted(supported))
        raise SystemExit(
            f"unsupported {field_name}: {normalized}. expected one of: {supported_text}"
        )
    return normalized


def _resolve_execution_mode(
    args: argparse.Namespace, env_values: dict[str, str]
) -> str:
    return _normalize_choice(
        getattr(args, "execution_mode", None) or env_values.get("EXECUTION_MODE"),
        default=DEFAULT_EXECUTION_MODE,
        supported=SUPPORTED_EXECUTION_MODES,
        field_name="execution mode",
    )


def _resolve_local_runner(args: argparse.Namespace, env_values: dict[str, str]) -> str:
    return _normalize_choice(
        getattr(args, "local_runner", None) or env_values.get("LOCAL_RUNNER"),
        default=DEFAULT_LOCAL_RUNNER,
        supported=SUPPORTED_LOCAL_RUNNERS,
        field_name="local runner",
    )


def _resolve_run_env(args: argparse.Namespace, env_values: dict[str, str]) -> str:
    raw_value = getattr(args, "run_env", None) or env_values.get("RUN_ENV")
    normalized = str(raw_value or "").strip().lower()
    if not normalized:
        return ""
    if normalized not in SUPPORTED_RUN_ENVS:
        supported_text = ", ".join(sorted(SUPPORTED_RUN_ENVS))
        raise SystemExit(
            f"unsupported RUN_ENV: {normalized}. expected one of: {supported_text}"
        )
    return normalized


def _resolve_local_case_concurrency(
    args: argparse.Namespace, env_values: dict[str, str]
) -> int:
    raw_value = getattr(args, "local_case_concurrency", None)
    if raw_value is None:
        raw_value = env_values.get("LOCAL_CASE_CONCURRENCY")
    if raw_value in (None, ""):
        return DEFAULT_LOCAL_CASE_CONCURRENCY
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(
            f"invalid local case concurrency: {raw_value!r}. expected positive integer"
        ) from exc
    if value <= 0:
        raise SystemExit(
            f"invalid local case concurrency: {raw_value!r}. expected positive integer"
        )
    return value


def _build_local_browser_headers(
    args: argparse.Namespace, env_values: dict[str, str]
) -> dict[str, str]:
    headers: dict[str, str] = {}

    swimlane = str(env_values.get("SWIMLANE") or "").strip()
    if swimlane:
        headers["x-tt-env"] = swimlane

    run_env = _resolve_run_env(args, env_values)
    if run_env == "ppe":
        headers["x-use-ppe"] = "1"
    elif run_env == "boe":
        headers["x-use-boe"] = "1"

    return headers


def _build_local_browser_header_setup(headers: dict[str, str]) -> dict[str, Any]:
    if not headers:
        return {}
    header_json = json.dumps(headers, ensure_ascii=False, sort_keys=True)
    return {
        "command": "run-code",
        "order": "after_open_before_first_goto",
        "code": f"async (page) => {{ await page.setExtraHTTPHeaders({header_json}); }}",
        "note": (
            "Run once per playwright-cli session after `open` and before the "
            "first `goto`; `route --header` mocks responses and is not a "
            "global request-header injector."
        ),
    }


def _default_chrome_user_data_dir() -> str:
    home = Path.home()
    if sys.platform == "darwin":
        return str(home / "Library" / "Application Support" / "Google" / "Chrome")
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA") or str(
            home / "AppData" / "Local"
        )
        return str(Path(local_app_data) / "Google" / "Chrome" / "User Data")
    return str(home / ".config" / "google-chrome")


def _normalize_domain(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = parsed.hostname or raw
    return host.strip().lower().lstrip(".")


def _target_domains_from_urls(urls: list[str]) -> list[str]:
    domains: list[str] = []
    seen: set[str] = set()
    for url in urls:
        domain = _normalize_domain(url)
        if not domain or domain in seen:
            continue
        seen.add(domain)
        domains.append(domain)
    return domains


def _cookie_domain_matches(host_key: str, target_domain: str) -> bool:
    host = _normalize_domain(host_key)
    target = _normalize_domain(target_domain)
    return bool(host and target and (host == target or host.endswith(f".{target}")))


def _chrome_profile_sort_key(path: Path) -> tuple[int, int, str]:
    name = path.name
    if name == "Default":
        return (0, 0, name)
    match = re.match(r"^Profile\s+(\d+)$", name)
    if match:
        return (1, int(match.group(1)), name)
    return (2, 0, name.lower())


def _chrome_cookie_db_paths(profile_dir: Path) -> list[Path]:
    candidates = [
        profile_dir / "Network" / "Cookies",
        profile_dir / "Cookies",
    ]
    return [path for path in candidates if path.is_file()]


def _copy_cookie_db_family(src_db: Path, dest_db: Path) -> None:
    """Copy Chrome Cookies SQLite DB with its WAL/SHM sidecars.

    Copying only the main DB is the common reason a running Chrome profile
    appears to have "empty" cookies: recent writes may still live in
    Cookies-wal. The destination uses the same basename so SQLite can replay
    the sidecars when opened.
    """
    dest_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_db, dest_db)
    for suffix in ("-wal", "-shm"):
        sidecar = src_db.with_name(src_db.name + suffix)
        if sidecar.is_file():
            shutil.copy2(sidecar, dest_db.with_name(dest_db.name + suffix))


def _count_cookie_rows(db_path: Path, target_domains: list[str] | None = None) -> int:
    if not db_path.is_file():
        return 0
    with tempfile.TemporaryDirectory(prefix="webe2e-cookie-read-") as tmp_dir:
        copied_db = Path(tmp_dir) / "Cookies"
        _copy_cookie_db_family(db_path, copied_db)
        try:
            conn = sqlite3.connect(f"file:{copied_db}?mode=ro", uri=True)
            rows = conn.execute("select host_key from cookies").fetchall()
        except sqlite3.Error:
            return 0
        finally:
            try:
                conn.close()
            except Exception:
                pass
    if not target_domains:
        return len(rows)
    return sum(
        1
        for (host_key,) in rows
        if any(_cookie_domain_matches(str(host_key), domain) for domain in target_domains)
    )


def _looks_like_chrome_profile_dir(path: Path) -> bool:
    return any(
        (path / item).exists()
        for item in [
            "Preferences",
            "Secure Preferences",
            "Network",
            "Cookies",
            "Local Storage",
            "Session Storage",
            "IndexedDB",
        ]
    )


def _discover_chrome_profiles(
    user_data_dir: str | Path,
    target_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    root = Path(user_data_dir).expanduser().resolve()
    if not root.is_dir():
        return []
    profile_dirs = [
        path
        for path in root.iterdir()
        if path.is_dir()
        and (path.name == "Default" or path.name.startswith("Profile "))
        and _looks_like_chrome_profile_dir(path)
    ]
    result: list[dict[str, Any]] = []
    for profile_dir in sorted(profile_dirs, key=_chrome_profile_sort_key):
        cookie_dbs = _chrome_cookie_db_paths(profile_dir)
        cookie_count = sum(_count_cookie_rows(path) for path in cookie_dbs)
        target_cookie_count = sum(
            _count_cookie_rows(path, target_domains or []) for path in cookie_dbs
        )
        result.append(
            {
                "name": profile_dir.name,
                "path": str(profile_dir),
                "cookie_db_paths": [str(path) for path in cookie_dbs],
                "cookie_count": cookie_count,
                "target_cookie_count": target_cookie_count,
                "has_local_storage": (profile_dir / "Local Storage").exists(),
                "has_session_storage": (profile_dir / "Session Storage").exists(),
                "has_indexed_db": (profile_dir / "IndexedDB").exists(),
            }
        )
    return result


def _copy_profile_tree_for_storage_state(
    src_user_data_dir: Path,
    profile_name: str,
    dest_user_data_dir: Path,
) -> None:
    src_profile = src_user_data_dir / profile_name
    if not src_profile.is_dir():
        raise SystemExit(f"chrome profile not found: {src_profile}")
    dest_user_data_dir.mkdir(parents=True, exist_ok=True)
    local_state = src_user_data_dir / "Local State"
    if local_state.is_file():
        shutil.copy2(local_state, dest_user_data_dir / "Local State")

    dest_profile = dest_user_data_dir / profile_name
    ignore_names = {
        "Crashpad",
        "BrowserMetrics",
        "GrShaderCache",
        "ShaderCache",
        "DawnCache",
        "optimization_guide_prediction_model_downloads",
    }

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignore_names}

    shutil.copytree(src_profile, dest_profile, dirs_exist_ok=True, ignore=ignore)


def _load_storage_state_summary(path: Path, target_domains: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except Exception:
        return {"cookies": 0, "target_cookies": 0, "origins": 0}
    cookies = payload.get("cookies") if isinstance(payload, dict) else []
    origins = payload.get("origins") if isinstance(payload, dict) else []
    if not isinstance(cookies, list):
        cookies = []
    if not isinstance(origins, list):
        origins = []
    target_cookies = [
        cookie
        for cookie in cookies
        if isinstance(cookie, dict)
        and any(
            _cookie_domain_matches(str(cookie.get("domain") or ""), domain)
            for domain in target_domains
        )
    ]
    return {
        "cookies": len(cookies),
        "target_cookies": len(target_cookies),
        "origins": len(origins),
    }


def _export_chrome_storage_state(
    *,
    user_data_dir: str | Path,
    profile_name: str,
    output_path: str | Path,
    target_urls: list[str] | None = None,
    target_domains: list[str] | None = None,
    headless: bool = False,
) -> dict[str, Any]:
    """Export Playwright storageState from a cloned Chrome profile.

    We intentionally launch a cloned profile instead of directly parsing
    encrypted cookie values. Chrome/Playwright can load the profile with the
    correct platform decryption path, and `storage_state` captures cookies plus
    origin storage for visited target URLs.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "python playwright package is required to export storage state. "
            "Install it with `python3 -m pip install playwright` and run "
            "`python3 -m playwright install chrome` or ensure local Chrome exists."
        ) from exc

    src_user_data_dir = Path(user_data_dir).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    urls = [url for url in (target_urls or []) if str(url).strip()]
    domains = list(target_domains or []) or _target_domains_from_urls(urls)

    with tempfile.TemporaryDirectory(prefix="webe2e-chrome-profile-") as tmp_dir:
        shadow_root = Path(tmp_dir) / "Chrome"
        _copy_profile_tree_for_storage_state(src_user_data_dir, profile_name, shadow_root)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(shadow_root),
                channel="chrome",
                headless=headless,
                args=[f"--profile-directory={profile_name}"],
            )
            try:
                for url in urls[:3]:
                    page = context.new_page()
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        page.wait_for_timeout(1500)
                    except Exception:
                        # Storage export is still useful even if a target URL
                        # is unreachable; the caller gets counts in summary.
                        pass
                    finally:
                        page.close()
                context.storage_state(path=str(output))
            finally:
                context.close()

    summary = _load_storage_state_summary(output, domains)
    summary.update(
        {
            "storage_state_file": str(output),
            "chrome_user_data_dir": str(src_user_data_dir),
            "chrome_profile_name": profile_name,
            "target_domains": domains,
        }
    )
    return summary


def _build_local_auth_profile_config(env_values: dict[str, str]) -> dict[str, Any]:
    """Describe how local playwright-cli should obtain browser login state.

    Do not silently assume Chrome's `Default` profile. Many users run their
    business login in `Profile 1`/`Profile 2`, and reading `Default/Cookies`
    alone commonly produces an empty cookie set. The executor must either use
    the explicitly configured profile or enumerate candidates and confirm the
    active one before exporting storage state.
    """
    mode = str(env_values.get("STORAGE_STATE_MODE") or "chrome-profile").strip()
    user_data_dir = str(env_values.get("CHROME_USER_DATA_DIR") or "").strip()
    profile_name = str(env_values.get("CHROME_PROFILE_NAME") or "").strip()
    resolved_user_data_dir = user_data_dir or _default_chrome_user_data_dir()
    return {
        "storage_state_mode": mode,
        "chrome_user_data_dir": resolved_user_data_dir,
        "chrome_profile_name": profile_name,
        "profile_detection_required": mode == "chrome-profile" and not profile_name,
        "profile_detection_rule": (
            "If chrome_profile_name is empty, enumerate Default/Profile * under "
            "chrome_user_data_dir and pick/confirm the profile that actually has "
            "target-domain login state; never assume Default."
        ),
        "cookie_db_read_rule": (
            "When reading a running Chrome profile, copy Cookies together with "
            "Cookies-wal and Cookies-shm, or launch a cloned profile and let "
            "Chrome/Playwright emit storageState. Reading only Cookies can miss "
            "recent WAL entries and look empty."
        ),
        "storage_scope_rule": (
            "Export cookies plus localStorage/sessionStorage/IndexedDB-relevant "
            "state when needed; some SSO flows are not cookie-only."
        ),
    }


def _extract_target_urls_from_local_cases(case_entries: list[dict[str, Any]]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for case in case_entries:
        for step in case.get("flow") or []:
            if not isinstance(step, dict):
                continue
            url = str(step.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            urls.append(url)
    return urls


def _default_storage_state_path(case_md: Path) -> Path:
    return case_md.resolve().parent / ".webe2e" / "storage_state.json"


def _ensure_local_storage_state_ready(
    *,
    auth_profile: dict[str, Any],
    case_md: Path,
    case_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    mode = str(auth_profile.get("storage_state_mode") or "").strip()
    if mode in ("", "none"):
        auth_profile["storage_state_file"] = ""
        auth_profile["export_summary"] = {"status": "skipped", "reason": "storage disabled"}
        return auth_profile
    if mode != "chrome-profile":
        raise SystemExit(f"unsupported STORAGE_STATE_MODE: {mode}")

    user_data_dir = Path(str(auth_profile["chrome_user_data_dir"])).expanduser().resolve()
    profile_name = str(auth_profile.get("chrome_profile_name") or "").strip()
    target_urls = _extract_target_urls_from_local_cases(case_entries)
    target_domains = _target_domains_from_urls(target_urls)

    if not profile_name:
        candidates = _discover_chrome_profiles(user_data_dir, target_domains)
        raise SystemExit(
            "CHROME_PROFILE_NAME is required for local chrome-profile auth. "
            "Do not assume Default. Set CHROME_PROFILE_NAME to the profile that "
            "actually has target-domain login state, or set STORAGE_STATE_MODE=none. "
            f"candidates={json.dumps(candidates, ensure_ascii=False)}"
        )

    storage_state_path = _default_storage_state_path(case_md)
    summary = _export_chrome_storage_state(
        user_data_dir=user_data_dir,
        profile_name=profile_name,
        output_path=storage_state_path,
        target_urls=target_urls,
        target_domains=target_domains,
    )
    if target_domains and summary.get("target_cookies") == 0 and summary.get("origins") == 0:
        raise SystemExit(
            "exported storage state has no target-domain cookies and no origins. "
            "This usually means the wrong Chrome profile was selected, the login "
            "state is not present, or the target domain is only available after "
            "an interactive SSO step. "
            f"summary={json.dumps(summary, ensure_ascii=False)}"
        )
    auth_profile["storage_state_file"] = str(storage_state_path)
    auth_profile["target_urls"] = target_urls
    auth_profile["target_domains"] = target_domains
    auth_profile["export_summary"] = summary
    return auth_profile


def _require_env_confirmation(
    args: argparse.Namespace, execution_mode: str, env_file: Path | None
) -> None:
    if getattr(args, "confirmed_env", False):
        return
    env_file_display = str(env_file) if env_file else "(missing .env)"
    raise SystemExit(
        "refuse to execute without explicit environment confirmation. "
        f"current execution_mode={execution_mode}, env_file={env_file_display}. "
        "Run `show-env`, wait for user confirmation, then rerun with `--confirmed-env`."
    )


def _json_headers(custom_token: str | None = None) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Custom-Token": custom_token or X_CUSTOM_TOKEN,
    }


def _task_query_headers(custom_token: str | None = None) -> dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": TTAT_UI_ORIGIN,
        "Pragma": "no-cache",
        "Referer": TTAT_UI_REFERER,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": TTAT_UI_USER_AGENT,
        "X-Custom-Token": custom_token or X_CUSTOM_TOKEN,
        "sec-ch-ua": TTAT_UI_SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }


def _extract_list(payload: Any, candidates: list[tuple[str, ...]]) -> list[Any]:
    if not isinstance(payload, dict):
        return []

    for path in candidates:
        current: Any = payload
        for key in path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(key)
        if isinstance(current, list):
            return current
    return []


def _extract_task_name(payload: Any) -> str:
    task_list = _extract_list(
        payload,
        [
            ("data", "task_list"),
            ("data", "taskList"),
            ("data", "tasks"),
            ("task_list",),
            ("taskList",),
            ("tasks",),
        ],
    )
    if not task_list:
        return ""
    first = task_list[0]
    if not isinstance(first, dict):
        return ""
    task_name = first.get("task_name") or first.get("taskName") or ""
    return str(task_name)


def _extract_task_record(payload: Any) -> dict[str, Any]:
    task_list = _extract_list(
        payload,
        [
            ("data", "task_list"),
            ("data", "taskList"),
            ("data", "tasks"),
            ("task_list",),
            ("taskList",),
            ("tasks",),
        ],
    )
    if not task_list:
        return {}
    first = task_list[0]
    return first if isinstance(first, dict) else {}


def _get_first_present(mapping: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _extract_task_execute_status(payload: Any) -> Any:
    task_record = _extract_task_record(payload)
    return _get_first_present(task_record, ["execute_status", "executeStatus"])


def _extract_task_counts(payload: Any) -> dict[str, Any]:
    task_record = _extract_task_record(payload)
    if not task_record:
        return {}
    return {
        "case_total_num": _get_first_present(
            task_record, ["case_total_num", "caseTotalNum"]
        ),
        "case_success_num": _get_first_present(
            task_record, ["case_success_num", "caseSuccessNum"]
        ),
        "case_failed_num": _get_first_present(
            task_record, ["case_failed_num", "caseFailedNum"]
        ),
        "case_unknown_num": _get_first_present(
            task_record, ["case_unknown_num", "caseUnknownNum"]
        ),
    }


def _query_task_list(task_id: Any) -> dict[str, Any]:
    payload = {
        "page_request": {
            "page_size": 1,
            "cur_page": 1,
            "sort_key": "",
            "sort_descending": True,
        },
        "task_id": task_id,
    }
    response = requests.post(
        QUERY_TASK_LIST_URL,
        headers=_task_query_headers(),
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _query_task_execution(task_id: Any) -> dict[str, Any]:
    payload = {
        "page_request": {
            "page_size": 1,
            "cur_page": 1,
            "sort_key": "",
            "sort_descending": True,
        },
        "task_id": task_id,
    }
    response = requests.post(
        QUERY_TASK_EXECUTION_URL,
        headers=_task_query_headers(),
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _task_polling_succeeded(task_execution_payload: Any) -> bool:
    if not isinstance(task_execution_payload, dict):
        return False
    if str(task_execution_payload.get("status_code")) != "0":
        return False
    return str(_extract_task_execute_status(task_execution_payload)) == "10"


def _can_start_analysis(task_execution_payload: Any) -> bool:
    return _task_polling_succeeded(task_execution_payload)


def _query_failed_cases(task_id: Any) -> list[dict[str, Any]]:
    failed_cases: list[dict[str, Any]] = []
    cur_page = 1

    while True:
        payload = {
            "page_request": {
                "page_size": DEFAULT_PAGE_SIZE,
                "cur_page": cur_page,
                "sort_key": "",
                "sort_descending": True,
            },
            "task_id": task_id,
            "test_status": 2,
            "tag_filter": 0,
        }
        response = requests.post(
            QUERY_TASK_CASE_EXECUTION_URL,
            headers=_task_query_headers(),
            json=payload,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        response_payload = response.json()
        items = _extract_list(
            response_payload,
            [
                ("data", "case_execution_list"),
                ("data", "caseExecutionList"),
                ("data", "taskCaseExecutions"),
                ("data", "task_case_executions"),
                ("case_execution_list",),
                ("caseExecutionList",),
                ("taskCaseExecutions",),
                ("task_case_executions",),
            ],
        )
        if not items:
            break

        for item in items:
            if not isinstance(item, dict):
                continue
            case_execution_id = item.get("case_execution_id") or item.get(
                "caseExecutionId"
            )
            if not case_execution_id:
                continue
            case_name = item.get("case_name") or item.get("caseName") or ""
            status = (
                item.get("status") or item.get("test_status") or item.get("testStatus")
            )
            failed_cases.append(
                {
                    "case_name": str(case_name),
                    "case_execution_id": str(case_execution_id),
                    "status": status,
                    "detail_url": TASK_CASE_DETAIL_LINK_TEMPLATE.format(
                        task_id=task_id,
                        case_execution_id=case_execution_id,
                    ),
                    "markdown_report_url": MARKDOWN_REPORT_ARCHIVE_LINK_TEMPLATE.format(
                        task_id=task_id,
                        case_execution_id=case_execution_id,
                    ),
                    "html_report_url": HTML_REPORT_LINK_TEMPLATE.format(
                        task_id=task_id,
                        case_execution_id=case_execution_id,
                    ),
                }
            )

        if len(items) < DEFAULT_PAGE_SIZE:
            break
        cur_page += 1

    return failed_cases


def _query_case_nodes(case_execution_id: Any) -> list[dict[str, Any]]:
    payload = {
        "page_request": {
            "page_size": DEFAULT_PAGE_SIZE,
            "cur_page": 1,
            "sort_key": "",
            "sort_descending": True,
        },
        "case_execution_id": case_execution_id,
    }
    response = requests.post(
        QUERY_TASK_CASE_NODE_EXECUTION_URL,
        headers=_task_query_headers(),
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_payload = response.json()
    items = _extract_list(
        response_payload,
        [
            ("data", "taskCaseNodeExecutions"),
            ("data", "task_case_node_executions"),
            ("taskCaseNodeExecutions",),
            ("task_case_node_executions",),
        ],
    )
    result: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            result.append(item)
    return result


def _fetch_html_report(report_url: str) -> str:
    response = requests.get(report_url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.text


def _fetch_markdown_report_archive(report_url: str) -> bytes:
    response = requests.get(report_url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def _read_report_md_from_archive(archive_bytes: bytes) -> str:
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as archive:
        report_member = None
        for member in archive.getmembers():
            normalized_name = member.name.lstrip("./")
            if member.isfile() and normalized_name == "report.md":
                report_member = member
                break
        if report_member is None:
            raise ValueError("report.md not found in markdown report archive")
        extracted = archive.extractfile(report_member)
        if extracted is None:
            raise ValueError("failed to read report.md from markdown report archive")
        return extracted.read().decode("utf-8", errors="replace")


def _extract_screenshots_from_archive(
    archive_bytes: bytes,
    screenshot_paths: list[str],
    target_dir: Path,
) -> dict[str, str]:
    """Extract specific screenshot files from a `.md.tar` archive.

    Returns a mapping from the original relative path inside the archive
    (e.g. ``./screenshots/step_03_failure.jpg``) to a filesystem path where
    the screenshot has been written. Missing entries simply mean the file
    was not present in the archive.
    """
    if not screenshot_paths:
        return {}
    target_dir.mkdir(parents=True, exist_ok=True)
    normalized_targets: dict[str, str] = {}
    for path in screenshot_paths:
        normalized = path.lstrip("./").lstrip("/")
        normalized_targets[normalized] = path
    result: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            normalized_member = member.name.lstrip("./").lstrip("/")
            original = normalized_targets.get(normalized_member)
            if original is None:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            basename = Path(normalized_member).name
            out_path = target_dir / basename
            out_path.write_bytes(extracted.read())
            result[original] = str(out_path)
    return result


_MARKDOWN_TASK_HEADER_PATTERN = re.compile(r"^##\s+(\d+)\.\s+([^-]+?)\s*-\s*(.*)$")
_MARKDOWN_FIELD_PATTERN = re.compile(r"^-\s+([^:]+):\s*(.*)$")
_MARKDOWN_SCREENSHOT_PATTERN = re.compile(r"!\[[^\]]*\]\((\./screenshots/[^)]+)\)")


def _parse_markdown_report_payload(report_markdown: str) -> dict[str, Any]:
    """Parse Midscene report.md into the same rough shape as the HTML dump."""
    executions: list[dict[str, Any]] = []
    current_execution: dict[str, Any] | None = None
    current_task: dict[str, Any] | None = None

    def ensure_execution(name: str) -> dict[str, Any]:
        execution = {"name": name.strip() or "Execution", "tasks": []}
        executions.append(execution)
        return execution

    for raw_line in report_markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("# ") and not line.startswith("# Midscene Report"):
            current_execution = ensure_execution(line[2:].strip())
            current_task = None
            continue

        task_header = _MARKDOWN_TASK_HEADER_PATTERN.match(line)
        if task_header:
            if current_execution is None:
                current_execution = ensure_execution("Execution")
            current_task = {
                "task_index": int(task_header.group(1)),
                "type": task_header.group(2).strip(),
                "description": task_header.group(3).strip(),
                "status": "",
                "errorMessage": "",
                "errorStack": "",
                "reasoning_content": task_header.group(3).strip(),
                "screenshots": [],
            }
            current_execution["tasks"].append(current_task)
            continue

        if current_task is None:
            continue

        field_match = _MARKDOWN_FIELD_PATTERN.match(line)
        if field_match:
            key = field_match.group(1).strip().lower()
            value = field_match.group(2).strip()
            if key == "status":
                current_task["status"] = value.lower()
            elif key == "error":
                current_task["errorMessage"] = value
            elif key == "error stack":
                current_task["errorStack"] = value
            continue

        for screenshot_match in _MARKDOWN_SCREENSHOT_PATTERN.finditer(line):
            current_task["screenshots"].append(screenshot_match.group(1))

    for execution in executions:
        tasks = execution.get("tasks") or []
        first_screenshots = (
            tasks[0].get("screenshots") if tasks and isinstance(tasks[0], dict) else []
        )
        first_screenshot_summary = (
            "Markdown 报告首步截图: " + ", ".join(first_screenshots)
            if first_screenshots
            else ""
        )
        for task in tasks:
            if not isinstance(task, dict):
                continue
            screenshots = task.get("screenshots") or []
            task["first_screenshot_summary"] = first_screenshot_summary
            task["failed_screenshot_summary"] = (
                "Markdown 报告失败步骤截图: " + ", ".join(screenshots)
                if screenshots
                else ""
            )

    return {"executions": executions}


def _extract_report_payload(report_html: str) -> dict[str, Any] | None:
    """Extract the richest execution payload from Midscene HTML report.

    Midscene reports embed progressive snapshots across many <script> tags.
    Earlier snapshots contain pending/incomplete tasks; the final snapshot
    holds the complete execution with error messages and reasoning.
    We pick the payload whose total task count is highest.
    """
    matches = re.findall(
        r"<script[^>]*>(.*?)</script>", report_html, flags=re.DOTALL | re.IGNORECASE
    )
    best_payload: dict[str, Any] | None = None
    best_score: tuple[bool, int, int] = (False, -1, -1)
    for idx, match in enumerate(matches):
        candidate = match.strip()
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except Exception:
            continue
        if not isinstance(payload, dict) or "executions" not in payload:
            continue
        exes = payload["executions"]
        if not isinstance(exes, list):
            continue
        task_count = sum(
            len(e.get("tasks", []))
            for e in exes
            if isinstance(e, dict)
        )
        has_terminal = any(
            isinstance(t, dict)
            and (t.get("status") in ("failed", "error") or t.get("errorMessage"))
            for e in exes
            if isinstance(e, dict)
            for t in (e.get("tasks") or [])
        )
        score = (has_terminal, task_count, idx)
        if score >= best_score:
            best_score = score
            best_payload = payload
    return best_payload


def _extract_failed_tasks(
    report_payload: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(report_payload, dict):
        return []

    failed_tasks: list[dict[str, Any]] = []
    executions = report_payload.get("executions")
    if not isinstance(executions, list):
        return []

    for execution_index, execution in enumerate(executions, start=1):
        if not isinstance(execution, dict):
            continue
        execution_name = str(execution.get("name") or f"Execution {execution_index}")
        tasks = execution.get("tasks")
        if not isinstance(tasks, list):
            continue
        for task_index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                continue
            status = str(task.get("status") or "")
            error_message = str(
                task.get("errorMessage") or task.get("error_message") or ""
            )
            if status != "failed" and not error_message:
                continue
            failed_tasks.append(
                {
                    "execution_name": execution_name,
                    "task_index": task_index,
                    "task_type": str(task.get("type") or ""),
                    "error_message": error_message,
                    "error_stack": str(
                        task.get("errorStack") or task.get("error_stack") or ""
                    ),
                    "reasoning_content": str(
                        task.get("reasoning_content")
                        or task.get("reasoningContent")
                        or ""
                    ),
                    "first_screenshot_summary": str(
                        task.get("first_screenshot_summary")
                        or task.get("firstScreenshotSummary")
                        or ""
                    ),
                    "failed_screenshot_summary": str(
                        task.get("failed_screenshot_summary")
                        or task.get("failedScreenshotSummary")
                        or task.get("screenshot_summary")
                        or task.get("screenshotSummary")
                        or ""
                    ),
                }
            )
    return failed_tasks


def _collect_report_reasoning(report_payload: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(report_payload, dict):
        return {
            "first_reasoning": "",
            "last_reasoning": "",
            "combined_reasoning": "",
        }

    executions = report_payload.get("executions")
    if not isinstance(executions, list):
        return {
            "first_reasoning": "",
            "last_reasoning": "",
            "combined_reasoning": "",
        }

    snippets: list[str] = []
    for execution in executions:
        if not isinstance(execution, dict):
            continue
        tasks = execution.get("tasks")
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            if not isinstance(task, dict):
                continue
            reasoning = str(
                task.get("reasoning_content") or task.get("reasoningContent") or ""
            ).strip()
            if reasoning:
                snippets.append(reasoning)

    combined = " ".join(snippets)
    return {
        "first_reasoning": snippets[0] if snippets else "",
        "last_reasoning": snippets[-1] if snippets else "",
        "combined_reasoning": combined,
    }




def _normalize_loop_signature(text: str) -> str:
    normalized = text.lower().strip()
    if not normalized:
        return ""
    normalized = re.sub(r"https?://\S+", " ", normalized)
    normalized = re.sub(
        r"\b(got it|let'?s look|look at this|look at the current state|so let'?s|wait no|first|current|page|screenshot|need to|we need to|用户现在需要|看截图里|看截图中的|所以|首先|需要确定|对应的位置)\b",
        " ",
        normalized,
    )
    normalized = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", normalized)
    tokens = [
        token
        for token in normalized.split()
        if len(token) >= 3
        and token
        not in {
            "the",
            "this",
            "that",
            "there",
            "then",
            "with",
            "from",
            "into",
            "next",
            "left",
            "right",
            "top",
            "text",
            "icon",
            "page",
            "current",
            "screenshot",
            "need",
            "find",
            "click",
            "open",
            "look",
            "dropdown",
        }
    ]
    return " ".join(tokens[:10])


def _truncate_prompt_example(text: str, limit: int = 72) -> str:
    normalized = " ".join(text.split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _summarize_execution_loop(
    report_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    default_signal = {
        "detected": False,
        "execution_name": "",
        "summary": "",
        "key_evidence": [],
        "prompt_patterns": [],
        "planning_count": 0,
        "action_space_count": 0,
    }
    if not isinstance(report_payload, dict):
        return default_signal

    executions = report_payload.get("executions")
    if not isinstance(executions, list):
        return default_signal

    best_signal = default_signal
    best_score = 0
    for execution_index, execution in enumerate(executions, start=1):
        if not isinstance(execution, dict):
            continue
        tasks = execution.get("tasks")
        if not isinstance(tasks, list) or len(tasks) < 8:
            continue

        execution_name = str(execution.get("name") or f"Execution {execution_index}")
        planning_count = 0
        action_space_count = 0
        failed_like_count = 0
        running_count = 0
        signatures: Counter[str] = Counter()
        signature_examples: dict[str, str] = {}

        for task in tasks:
            if not isinstance(task, dict):
                continue
            task_type = str(task.get("type") or "")
            status = str(task.get("status") or "")
            error_message = str(
                task.get("errorMessage") or task.get("error_message") or ""
            )
            reasoning = str(
                task.get("reasoning_content") or task.get("reasoningContent") or ""
            ).strip()
            if task_type == "Planning":
                planning_count += 1
            elif task_type == "Action Space":
                action_space_count += 1
            if status == "running":
                running_count += 1
            if status == "failed" or error_message:
                failed_like_count += 1
            if task_type != "Planning" or not reasoning:
                continue
            signature = _normalize_loop_signature(reasoning)
            if signature:
                signatures[signature] += 1
                signature_examples.setdefault(signature, reasoning)

        repeated_patterns = [
            (signature, count)
            for signature, count in signatures.most_common()
            if count >= 2
        ]
        repeated_signature_count = repeated_patterns[0][1] if repeated_patterns else 0
        repeated_prompt_total = sum(count for _, count in repeated_patterns)
        high_task_count = (planning_count + action_space_count) >= 60
        loop_detected = (
            planning_count >= 6
            and action_space_count >= 2
            and failed_like_count == 0
            and (
                (repeated_signature_count >= 3
                 and repeated_prompt_total >= max(4, planning_count // 3))
                or high_task_count
            )
        )
        if not loop_detected:
            continue

        score = (
            planning_count
            + action_space_count
            + repeated_signature_count * 3
            + repeated_prompt_total
            + running_count
        )
        if score <= best_score:
            continue

        repeated_prompt_examples = [
            _truncate_prompt_example(signature_examples.get(signature) or signature)
            for signature, _ in repeated_patterns[:3]
        ]
        prompt_text = (
            "；".join(f"`{example}`" for example in repeated_prompt_examples)
            if repeated_prompt_examples
            else "同一类 prompt"
        )
        summary = (
            f"HTML 报告显示执行在 `{execution_name}` 中反复进行 Planning / Action Space，"
            f"共出现 {planning_count} 次 Planning、{action_space_count} 次 Action Space；"
            f"其中重复 prompt 模式累计出现 {repeated_prompt_total} 次，典型重复 prompt 为 {prompt_text}，"
            f"执行未进入稳定的后续步骤。"
        )
        best_signal = {
            "detected": True,
            "execution_name": execution_name,
            "summary": summary,
            "key_evidence": _compact_evidence(
                [
                    f"`{execution_name}` 中出现 {planning_count} 次 Planning 和 {action_space_count} 次 Action Space。",
                    "HTML 报告没有明确 failed task，而是长时间停留在同一执行段循环。",
                    (
                        "重复 prompt 模式："
                        + "；".join(
                            f"{count} 次 `{_truncate_prompt_example(signature_examples.get(signature) or signature)}`"
                            for signature, count in repeated_patterns[:3]
                        )
                        + "。"
                        if repeated_patterns
                        else "循环中的 Planning prompt 高度重复。"
                    ),
                ]
            ),
            "prompt_patterns": repeated_prompt_examples,
            "planning_count": planning_count,
            "action_space_count": action_space_count,
        }
        best_score = score

    return best_signal


def _trim_text(value: str, limit: int = MAX_REASONING_SNIPPET) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _get_node_extra_info(node: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(node, dict):
        return {}
    for key in ("extra_info", "extraInfo"):
        raw_extra_info = node.get(key)
        if isinstance(raw_extra_info, dict):
            return raw_extra_info
    return {}


def _extract_text_candidate(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()
    if isinstance(value, dict):
        for key in (
            "instruction",
            "step_name",
            "stepName",
            "step_instruction",
            "stepInstruction",
            "ai_action",
            "aiAction",
            "content",
            "text",
            "value",
            "description",
            "desc",
            "prompt",
        ):
            extracted = _extract_text_candidate(value.get(key))
            if extracted:
                return extracted
    if isinstance(value, list):
        for item in value:
            extracted = _extract_text_candidate(item)
            if extracted:
                return extracted
    return ""


def _extract_node_instruction(node: dict[str, Any] | None) -> str:
    if not isinstance(node, dict):
        return ""

    for key in (
        "step_name",
        "stepName",
        "instruction",
        "step_instruction",
        "stepInstruction",
        "ai_action",
        "aiAction",
        "content",
        "text",
        "value",
        "description",
        "desc",
        "prompt",
    ):
        extracted = _extract_text_candidate(node.get(key))
        if extracted:
            return extracted

    extra_info = _get_node_extra_info(node)
    for key in (
        "instruction",
        "step_name",
        "stepName",
        "step_instruction",
        "stepInstruction",
        "ai_action",
        "aiAction",
        "content",
        "text",
        "value",
        "description",
        "desc",
        "prompt",
    ):
        extracted = _extract_text_candidate(extra_info.get(key))
        if extracted:
            return extracted

    return ""


def _has_missing_instruction_signal(
    failed_step_name: str,
    error_message: str,
    reasoning_content: str,
) -> bool:
    if failed_step_name.strip():
        return False

    combined = "\n".join([error_message, reasoning_content]).lower()
    return any(
        token in combined
        for token in [
            "no specific instruction was provided",
            "no instruction was provided",
            "instruction is empty",
            "empty instruction",
            "missing instruction",
            "no executable instruction",
            "empty ai action",
            "ai action is empty",
        ]
    )


def _get_first_node(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    return nodes[0] if nodes else None


def _get_failed_node(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    fallback = None
    for node in nodes:
        test_status = node.get("test_status") or node.get("testStatus")
        extra_info = _get_node_extra_info(node)
        error_msg = str(extra_info.get("error_msg") or "")
        if str(test_status) == "2":
            return node
        if error_msg:
            fallback = node
    return fallback


def _get_node_error(node: dict[str, Any] | None) -> str:
    if not isinstance(node, dict):
        return ""
    extra_info = _get_node_extra_info(node)
    return str(extra_info.get("error_msg") or "")


def _looks_like_mixed_url_step(step_name: str) -> bool:
    stripped = step_name.strip()
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        return False
    if "，" in stripped or "," in stripped:
        return True
    tail = re.sub(r"^https?://\S+", "", stripped).strip()
    return bool(tail)


def _is_business_bug(text: str) -> bool:
    normalized = text.lower()
    keywords = [
        "500",
        "api error",
        "exception",
        "internal server error",
        "graphql error",
    ]
    return any(keyword in normalized for keyword in keywords)


def _looks_like_assertion_step(step_name: str) -> bool:
    normalized = step_name.lower()
    return any(
        token in normalized
        for token in [
            "assert",
            "check",
            "verify",
            "ensure",
            "expect",
            "should",
            "确认",
            "校验",
            "验证",
            "断言",
        ]
    )


def _looks_like_empty_data_signal(text: str) -> bool:
    normalized = text.lower()
    return any(
        token in normalized
        for token in [
            "list is empty",
            "strategy group list is empty",
            "list area is empty",
            "empty no results state",
            "instead of containing data",
            "instead of showing groups",
            "no pagination controls are present",
            "no data rows",
            "列表为空",
            "无结果态",
        ]
    )


def _looks_like_service_error_signal(text: str) -> bool:
    normalized = text.lower()
    return any(
        token in normalized
        for token in [
            "request error",
            "rpc error",
            "permission check rpc error",
            "service error prompt",
            "service prompts",
            "unhandled service error",
            "red request error popups",
        ]
    )


def _looks_like_login_page_signal(text: str) -> bool:
    normalized = text.lower()
    return (
        "login" in normalized
        or any(
            token in normalized
            for token in [
                "sign in",
                "log in",
                "session expired",
                "session invalid",
                "google sign in",
                "google login",
            ]
        )
    )


def _looks_like_404_signal(text: str) -> bool:
    normalized = text.lower()
    return any(token in normalized for token in ["page not found", "404"])


def _looks_like_loading_signal(text: str) -> bool:
    normalized = text.lower()
    return any(
        token in normalized
        for token in [
            "timeout",
            "timed out",
            "loading",
            "spinner",
            "splash screen",
            "logo on a white background",
            "white background with only the tiktok logo",
            "white screen",
            "blank screen",
        ]
    )


def _looks_like_access_blocked_signal(text: str) -> bool:
    """Detect access-control / network-segregation / IP-block style failures.

    These show up as gateway-side rejection JSON or banners (e.g.
    ``network_segregation_rejected``, ``rejected by ROW Operations
    Gateway``, ``IP is not allowed to connect``). They are environment
    failures, not assertion / data / step description issues.
    """
    normalized = text.lower()
    tokens = [
        "network_segregation_rejected",
        "network segregation",
        "operations gateway",
        "rejected by row operations",
        "rejected by gateway",
        "request is rejected",
        "is not allowed to connect",
        "not allowed to connect",
        "ip not allowed",
        "ip is not allowed",
        "blocked by firewall",
        "blocked by gateway",
        "access denied",
        "permission denied",
        "403 forbidden",
        "fail to discover office network",
        "segregator",
    ]
    return any(token in normalized for token in tokens)


def _summarize_screenshot_signals(
    first_screenshot_summary: str = "",
    failed_screenshot_summary: str = "",
) -> str:
    return "\n".join(
        part.strip()
        for part in [first_screenshot_summary, failed_screenshot_summary]
        if str(part).strip()
    )


def _first_step_gate_signal(
    first_screenshot_summary: str = "",
    failed_screenshot_summary: str = "",
    error_message: str = "",
) -> str:
    """Build the input fed to the Layer 1.5 first-step gate.

    History: this used to be ``first_screenshot_summary`` only — but that
    summary is just the JPEG filenames extracted from ``report.md`` and
    contains no ``login``/``404``/``loading`` keywords, so the gate
    silently never fired and downstream layers (Layer 3 assertion, Layer 6
    loading) wrongly grabbed cases whose true root cause was a SSO login
    interception or a gateway access block. We now also feed in the
    failed-step screenshot summary and the original ``error_message`` so
    the gate can see textual evidence about the actual page state.
    """
    return "\n".join(
        part.strip()
        for part in [
            first_screenshot_summary,
            failed_screenshot_summary,
            error_message,
        ]
        if str(part).strip()
    )


def _reasoning_conflicts_with_screenshot(
    reasoning_content: str,
    screenshot_signals: str,
) -> bool:
    reasoning = reasoning_content.lower()
    screenshot = screenshot_signals.lower()
    if not reasoning or not screenshot:
        return False

    reasoning_denies_login = any(
        phrase in reasoning
        for phrase in [
            "no login",
            "no sign in",
            "no log in",
            "without login",
            "login prompt is not visible",
            "no login prompt is visible",
        ]
    )
    if _looks_like_login_page_signal(screenshot):
        if reasoning_denies_login:
            return True
        if not _looks_like_login_page_signal(reasoning):
            return _looks_like_empty_data_signal(reasoning) or any(
                token in reasoning
                for token in ["table", "list", "dashboard", "business page"]
            )
    if _looks_like_404_signal(screenshot) and not _looks_like_404_signal(reasoning):
        return _looks_like_empty_data_signal(reasoning) or any(
            token in reasoning for token in ["table", "list", "dashboard", "business page"]
        )
    if _looks_like_loading_signal(screenshot) and not _looks_like_loading_signal(reasoning):
        return _looks_like_empty_data_signal(reasoning) or any(
            token in reasoning for token in ["loaded", "stable", "table", "list"]
        )
    return False


def _looks_like_tenant_switch_loop(text: str) -> bool:
    normalized = text.lower()
    tenant_tokens = ["tenant", "tiktok test", "boe test data center", "tenant selector"]
    boe_tokens = ["boe", "tsop"]
    return (
        any(token in normalized for token in tenant_tokens)
        and any(token in normalized for token in boe_tokens)
        and any(
            token in normalized
            for token in [
                "click the boe text",
                "click the arrow next to boe",
                "dropdown only shows boe",
                "switch to tiktok test",
                "open the tenant selection dropdown",
                "expand the full tenant list",
            ]
        )
    )


def _build_decision_line(layer: str, status: str, detail: str) -> str:
    if status == "hit":
        return f"- {layer}：❌ 命中 → {detail}"
    if status == "insufficient":
        return f"- {layer}：⚠️ 证据不足（{detail}）"
    return f"- {layer}：✅ 排除（{detail}）"


def _compact_evidence(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = " ".join(str(item).split()).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result[:4]


def _collect_report_screenshot_relpaths(
    report_payload: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    """Collect first-step and failure-step screenshot relpaths.

    Aggregates across **every** execution (including retries) and dedupes,
    so the download stage fetches every screenshot the narrative might
    reference. Previously the collector stopped at the first execution
    that produced any screenshots, which left retry-execution paths
    referenced in ``key_evidence`` but never extracted to disk.
    """
    first: list[str] = []
    failure: list[str] = []
    seen_first: set[str] = set()
    seen_failure: set[str] = set()

    if not isinstance(report_payload, dict):
        return first, failure
    executions = report_payload.get("executions")
    if not isinstance(executions, list):
        return first, failure

    for execution in executions:
        if not isinstance(execution, dict):
            continue
        tasks = execution.get("tasks") or []
        if not isinstance(tasks, list):
            continue
        first_task = next(
            (task for task in tasks if isinstance(task, dict)), None
        )
        if first_task is not None:
            for p in first_task.get("screenshots") or []:
                if isinstance(p, str) and p and p not in seen_first:
                    seen_first.add(p)
                    first.append(p)
        for task in tasks:
            if not isinstance(task, dict):
                continue
            if str(task.get("status") or "").lower() != "failed":
                continue
            for p in task.get("screenshots") or []:
                if isinstance(p, str) and p and p not in seen_failure:
                    seen_failure.add(p)
                    failure.append(p)

    return first, failure


def _format_screenshot_evidence(
    label: str,
    paths: list[str] | None = None,
    relpaths: list[str] | None = None,
) -> str:
    """Render a single ``key_evidence`` line for one screenshot category.

    Emits inline markdown image syntax (``![label](path)``) for every
    locally-extracted path so reviewers see frames in IDE preview; falls
    back to backtick-quoted archive relpaths when nothing was downloaded.
    Returns an empty string when neither is available so the caller can
    skip the bullet.

    No truncation is applied — earlier behaviour passed these strings
    through ``_trim_text(..., limit=120)`` which silently chopped multi-
    path summaries, producing dangling ``...`` paths.
    """
    clean_paths = [str(p) for p in (paths or []) if str(p).strip()]
    if clean_paths:
        images = " ".join(f"![{label}]({p})" for p in clean_paths)
        return f"{label}：{images}"
    clean_rels = [str(p) for p in (relpaths or []) if str(p).strip()]
    if clean_rels:
        joined = "、".join(f"`{p}`" for p in clean_rels)
        return f"{label}（未本地落盘）：{joined}"
    return ""


def _build_classification_result(
    *,
    category: str,
    subcategory: str,
    confidence: str,
    summary: str,
    direct_cause: str,
    root_cause: str,
    suggestion: str,
    failure_phenomenon: str,
    key_evidence: list[str],
    exclusion_reasoning: str,
    decision_path: list[str],
) -> dict[str, Any]:
    return {
        "owner": category,
        "summary": summary,
        "direct_cause": direct_cause,
        "root_cause": root_cause,
        "suggestion": suggestion,
        "attribution_category": category,
        "attribution_subcategory": subcategory,
        "confidence": confidence,
        "failure_phenomenon": failure_phenomenon,
        "key_evidence": key_evidence,
        "exclusion_reasoning": exclusion_reasoning,
        "decision_path": decision_path,
        "reasoning": root_cause,
        "convergence_note": "",
    }


def _classify_case(
    first_step_name: str,
    failed_step_name: str,
    error_message: str,
    reasoning_content: str,
    loop_signal: dict[str, Any] | None = None,
    first_screenshot_summary: str = "",
    failed_screenshot_summary: str = "",
    first_screenshot_paths: list[str] | None = None,
    failure_screenshot_paths: list[str] | None = None,
    first_screenshot_relpaths: list[str] | None = None,
    failure_screenshot_relpaths: list[str] | None = None,
) -> dict[str, Any]:
    effective_failed_step_name = failed_step_name or first_step_name
    loop_signal = loop_signal or {}
    loop_summary = str(loop_signal.get("summary") or "")
    loop_evidence = loop_signal.get("key_evidence") or []
    if not isinstance(loop_evidence, list):
        loop_evidence = []
    screenshot_signals = _summarize_screenshot_signals(
        first_screenshot_summary, failed_screenshot_summary
    )
    first_step_gate_signal = _first_step_gate_signal(
        first_screenshot_summary,
        failed_screenshot_summary,
        error_message,
    )
    combined = "\n".join(
        [
            first_step_name,
            effective_failed_step_name,
            error_message,
            reasoning_content,
            loop_summary,
            screenshot_signals,
        ]
    ).lower()
    evidence_lines = _compact_evidence(
        [
            f"失败步骤：{effective_failed_step_name}" if effective_failed_step_name else "",
            f"错误信息：{error_message}" if error_message else "",
            f"推理片段：{_trim_text(reasoning_content, limit=120)}"
            if reasoning_content
            else "",
            _format_screenshot_evidence(
                "首步截图",
                paths=first_screenshot_paths,
                relpaths=first_screenshot_relpaths,
            ),
            _format_screenshot_evidence(
                "失败截图",
                paths=failure_screenshot_paths,
                relpaths=failure_screenshot_relpaths,
            ),
        ]
    )
    phenomenon = (
        f"失败步骤 `{effective_failed_step_name or '未知步骤'}` 执行失败"
        + (f"，错误信息为 `{error_message}`" if error_message else "")
    )
    decision_path: list[str] = []

    has_evidence = bool(
        effective_failed_step_name
        or error_message
        or reasoning_content
        or screenshot_signals
    )
    decision_path.append(
        _build_decision_line(
            "Layer 1 证据充分性",
            "excluded" if has_evidence else "insufficient",
            "已拿到节点步骤、错误信息、HTML 报告线索或截图摘要"
            if has_evidence
            else "节点步骤、错误信息、HTML 报告线索和截图摘要都较弱",
        )
    )
    confidence = "中" if has_evidence else "低"

    if _looks_like_404_signal(first_step_gate_signal):
        decision_path.append(
            _build_decision_line(
                "Layer 1.5 首步截图 Gate",
                "hit",
                "首步截图直接显示 404 / Page not found，优先收敛为访问入口错误",
            )
        )
        summary = "首步 URL 进入 404 / Page not found，case 配置的访问地址不正确（Case 描述 - 业务QA / URL）"
        return _build_classification_result(
            category="Case 描述 - 业务QA",
            subcategory="URL",
            confidence="高",
            summary=summary,
            direct_cause="首步截图已经落到错误地址或 404 页面，后续步骤都建立在错误入口上。",
            root_cause="case 中配置的 URL、域名或必要参数已过期或填写错误。",
            suggestion="修正 case 中的 URL，并先单独验证首步能否进入正确业务页。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "首步截图直接显示 404 / Page not found。",
                    "根据首步截图优先规则，后续失败应按连锁反应收敛。",
                ]
            ),
            exclusion_reasoning="首步截图已给出更强证据，优先级高于后续空列表或断言失败描述。",
            decision_path=decision_path + ["- 归因结论：Case 描述 - 业务QA / URL"],
        )
    if _looks_like_access_blocked_signal(first_step_gate_signal):
        decision_path.append(
            _build_decision_line(
                "Layer 1.5 首步截图 Gate",
                "hit",
                "页面/接口被网关或网络隔离拦截（network_segregation_rejected / rejected by gateway / IP not allowed），优先收敛为环境访问拦截",
            )
        )
        summary = "请求被网关或网络隔离策略拦截，当前环境无法访问目标业务（环境问题 / 访问拦截）"
        return _build_classification_result(
            category="环境问题",
            subcategory="访问拦截",
            confidence="高",
            summary=summary,
            direct_cause="页面或接口请求被 ROW Operations Gateway / 网络隔离策略 / 防火墙直接拒绝，没有进入业务页面。",
            root_cause="当前执行环境的出口 IP / 网络段没有访问目标服务的权限（network segregation / IP allowlist）。",
            suggestion="联系基础设施 / 网络运维核对出口 IP 与目标服务的访问策略，或在允许的网络段内重跑；同时回查 case 是否本应在专用环境执行。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误中出现 network_segregation_rejected / rejected by gateway / not allowed to connect / IP not allowed 等访问拦截关键词。",
                    "失败发生在进入业务页面之前，是环境访问策略问题，不是 case 描述/数据/断言问题。",
                ]
            ),
            exclusion_reasoning="拦截信号在进入业务页面之前就出现，比下游断言失败、空数据等现象更接近根因。",
            decision_path=decision_path + ["- 归因结论：环境问题 / 访问拦截"],
        )
    if _looks_like_login_page_signal(first_step_gate_signal):
        decision_path.append(
            _build_decision_line(
                "Layer 1.5 首步截图 Gate",
                "hit",
                "页面进入登录态/SSO 登录卡片，优先收敛为环境登录态问题（gate 同时考察首步截图、失败截图与 error_message 文本）",
            )
        )
        summary = "执行链路进入登录态或 session 失效，当前环境不满足自动化前置条件（环境问题 / 登录态）"
        return _build_classification_result(
            category="环境问题",
            subcategory="登录态",
            confidence="高",
            summary=summary,
            direct_cause="页面被 TikTok SSO / 二级登录卡片 / session 失效页拦下，业务内容没有渲染出来。",
            root_cause="当前环境登录凭证缺失、失效或被重定向到外部/嵌入式登录页（含 TikTok SSO 子站点登录）。",
            suggestion="补齐目标站点（含子域）的有效登录态 / storageState；执行前先验证首屏不是 SSO 登录卡片再触发回归。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "首步/失败截图或 error_message 命中 sign in / login / SSO / session expired 等登录态信号。",
                    "断言失败、列表为空等现象都是登录页阻断业务后的连锁结果，不是独立根因。",
                ]
            ),
            exclusion_reasoning="登录页证据强于后续业务态推理，当前失败不应继续落到数据缺失或断言描述问题。",
            decision_path=decision_path + ["- 归因结论：环境问题 / 登录态"],
        )
    if _looks_like_loading_signal(first_step_gate_signal) and not _looks_like_assertion_step(
        effective_failed_step_name
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 1.5 首步截图 Gate",
                "hit",
                "截图显示页面仍停留在启动页或白屏，优先收敛为框架未等到稳定业务态",
            )
        )
        summary = "首屏页面长时间停留在启动页或白屏，Midscene 未等到稳定业务态（Midscene / 启动失败）"
        return _build_classification_result(
            category="Midscene",
            subcategory="启动失败",
            confidence="高",
            summary=summary,
            direct_cause="截图显示页面仍处于加载态、白屏或启动页，后续步骤没有真实进入业务页面。",
            root_cause="自动化框架对页面就绪态的等待和重试不足。",
            suggestion="增强首屏稳定判断与重试逻辑，并在关键步骤前识别启动页/白屏状态。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "截图直接显示 splash screen / white screen / loading / timeout。",
                    "根据首步截图优先规则，后续失败属于连锁反应。",
                ]
            ),
            exclusion_reasoning="截图给出的页面未稳定证据强于后续业务断言描述。",
            decision_path=decision_path + ["- 归因结论：Midscene / 启动失败"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 1.5 首步截图 Gate",
            "excluded",
            "首步截图未命中 404、登录页或白屏/启动页强信号",
        )
    )

    data_conflict_tokens = [
        "already exists",
        "already been authorized",
        "has already been",
        "must be consistent",
        "duplicate key",
        "duplicate entry",
        "unique constraint",
        "conflict",
    ]
    if any(token in combined for token in data_conflict_tokens):
        decision_path.append(
            _build_decision_line(
                "Layer 2 测试数据",
                "hit",
                "接口返回数据冲突错误（重复 key / 已存在 / 一致性约束），命中测试数据冲突特征",
            )
        )
        summary = "接口提交时因数据冲突失败（如 key 已存在、字段一致性约束），测试数据与 BOE 环境现有数据冲突（Case 测试数据问题 / 数据冲突）"
        return _build_classification_result(
            category="Case 测试数据问题",
            subcategory="数据冲突",
            confidence="高",
            summary=summary,
            direct_cause="接口返回数据已存在或字段一致性约束错误，操作被拒绝。",
            root_cause="测试用例使用的数据（如 feature key）在当前环境已被占用，或与已有记录冲突。",
            suggestion="使用带时间戳的唯一 key 避免冲突，或在测试前清理相关数据。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误信息包含 already exists / must be consistent 等数据冲突关键词。",
                    "失败发生在提交阶段，而非页面加载或元素定位阶段。",
                ]
            ),
            exclusion_reasoning="错误信息明确指向数据冲突，非模型操作能力、页面加载或断言描述问题。",
            decision_path=decision_path
            + ["- 归因结论：Case 测试数据问题 / 数据冲突"],
        )

    data_tokens = [
        "couldn't find this account",
        "account not found",
        "already in collections",
        "no favorite videos available to add",
        "all favorite videos are already in collections",
        "no videos in this collection",
        "no result",
        "no tasks found",
    ]
    if _looks_like_service_error_signal(combined) and _looks_like_empty_data_signal(
        combined
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 2 测试数据",
                "excluded",
                "页面虽为空，但同时出现 Request Error / RPC error，更像上游服务异常导致的连锁失败",
            )
        )
    elif any(token in combined for token in data_tokens) or _looks_like_empty_data_signal(
        combined
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 2 测试数据",
                "hit",
                "页面或目标对象不存在，命中空数据/前置数据不足特征",
            )
        )
        summary = "页面数据为空或目标对象不可用，导致当前 case 无法按预期继续（Case 测试数据问题 / 空数据）"
        return _build_classification_result(
            category="Case 测试数据问题",
            subcategory="空数据",
            confidence="高",
            summary=summary,
            direct_cause="页面返回空列表、账号不存在或前置数据已被占用，当前步骤无法找到可操作目标。",
            root_cause="测试数据未满足执行前置条件，或被引用的数据在当前环境已失效。",
            suggestion="补齐可用测试数据，或在执行前先重置账号、收藏、列表等依赖数据。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "页面线索出现空数据、账号不存在或列表为空。",
                    "失败并非由模型空响应触发，而是目标数据本身不可用。",
                ]
            ),
            exclusion_reasoning="未见空 instruction 或模型服务异常信号，且页面状态直接显示数据缺失。",
            decision_path=decision_path
            + ["- 归因结论：Case 测试数据问题 / 空数据"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 2 测试数据",
            "excluded",
            "未看到明确的空列表、账号不存在或前置数据缺失信号",
        )
    )

    assertion_tokens = [
        "does not match the expected url",
        "does not match the assertion",
        "assertion is not fully satisfied",
        "assertions are not fully satisfied",
        "assertions are not satisfied",
        "assertion fails",
        "assertion failed",
        "column order does not match",
        "order is swapped",
        "instead of the expected",
        "not editable",
        "is editable",
        "redirected page is",
        "reposts tab is displayed",
        "displayed on the page, the assertion that it is not displayed is not satisfied",
        "open time",
        "publish time",
    ]
    has_assertion_signal = any(token in combined for token in assertion_tokens)
    has_login_signal_in_combined = _looks_like_login_page_signal(combined)
    has_access_block_in_combined = _looks_like_access_blocked_signal(combined)
    if has_assertion_signal and (has_login_signal_in_combined or has_access_block_in_combined):
        decision_path.append(
            _build_decision_line(
                "Layer 3 断言一致性",
                "excluded",
                "虽然报告里出现 `assertion failed` 字样，但同时检出登录态 / 访问拦截信号；断言失败只是被前置拦截后的连锁现象，根因应落到环境层（见下文 Layer 6 早绑定）",
            )
        )
        summary = (
            "执行链路被 SSO 登录卡片 / 网关访问拦截阻断，业务内容未渲染，由此触发 `assertion failed`；"
            "根因属于环境而不是断言描述（环境问题 / 登录态 或 访问拦截）"
        )
        if has_access_block_in_combined:
            return _build_classification_result(
                category="环境问题",
                subcategory="访问拦截",
                confidence="高",
                summary="请求被网关或网络隔离策略拦截，业务页未渲染，断言失败只是连锁现象（环境问题 / 访问拦截）",
                direct_cause="ROW Operations Gateway / 网络隔离策略直接拒绝了页面或接口请求，业务内容根本没渲染。",
                root_cause="执行环境的出口 IP / 网络段没有访问目标服务的权限。",
                suggestion="切换到允许的网络段重跑；或与基础设施 / 网络运维确认 case 应该在哪个环境执行。",
                failure_phenomenon=phenomenon,
                key_evidence=_compact_evidence(
                    evidence_lines
                    + [
                        "error_message 中出现 network_segregation_rejected / rejected by gateway / not allowed to connect。",
                        "断言失败仅是访问拦截后的连锁结果，不是独立根因。",
                    ]
                ),
                exclusion_reasoning="访问拦截发生在进入业务页之前，所有后续断言失败都属于连锁失败。",
                decision_path=decision_path + ["- 归因结论：环境问题 / 访问拦截"],
            )
        return _build_classification_result(
            category="环境问题",
            subcategory="登录态",
            confidence="高",
            summary="执行链路被 SSO / 登录卡片阻断，业务页未渲染，断言失败是连锁现象（环境问题 / 登录态）",
            direct_cause="目标页面被 TikTok SSO / 二级登录卡片拦下，业务内容（容器、按钮、列表）根本没有出现。",
            root_cause="当前环境登录凭证缺失、失效或目标站点（含子域）登录态未注入。",
            suggestion="补齐目标站点的 storageState / SSO 登录态；执行前先验证首屏不是 SSO 登录卡片。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "error_message 同时出现 `assertion failed` 与 `TikTok SSO login` / `sign in` / `login page` 等登录信号。",
                    "断言失败是登录页阻断业务后的连锁现象，不是断言描述本身过期。",
                ]
            ),
            exclusion_reasoning="登录信号比断言失败信号更接近根因，断言失败仅是连锁结果。",
            decision_path=decision_path + ["- 归因结论：环境问题 / 登录态"],
        )
    if has_assertion_signal:
        decision_path.append(
            _build_decision_line(
                "Layer 3 断言一致性",
                "hit",
                "页面实际文案、字段或跳转结果与断言口径不一致",
            )
        )
        summary = "页面实际表现与断言口径不一致，当前断言描述已过期或不准确（Case 测试数据问题 / 断言描述）"
        return _build_classification_result(
            category="Case 测试数据问题",
            subcategory="断言描述",
            confidence="高",
            summary=summary,
            direct_cause="断言中的 URL、字段名、展示顺序或可见性与页面当前实际状态不一致。",
            root_cause="测试断言没有及时跟随页面实现或环境数据状态更新。",
            suggestion="按当前页面结构和环境数据修正断言，再重新执行回归。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "报告中同时出现预期和实际不一致的字段/跳转描述。",
                    "失败现象集中在断言校验，而不是页面无法进入或模型无响应。",
                ]
            ),
            exclusion_reasoning="已排除空数据和空 instruction，失败点集中在断言口径与页面实际不一致。",
            decision_path=decision_path
            + ["- 归因结论：Case 测试数据问题 / 断言描述"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 3 断言一致性",
            "excluded",
            "未看到明确的断言文案、字段或结构冲突信号",
        )
    )

    missing_instruction = _has_missing_instruction_signal(
        failed_step_name, error_message, reasoning_content
    )
    if missing_instruction:
        decision_path.append(
            _build_decision_line(
                "Layer 4 步骤/instruction",
                "hit",
                "原始错误明确指出缺少可执行 instruction",
            )
        )
        summary = "失败步骤 instruction 为空，转换链路没有产出可执行步骤文本（Bits2Midscene-解析步骤 / 空步骤）"
        return _build_classification_result(
            category="Bits2Midscene-解析步骤",
            subcategory="空步骤",
            confidence="高",
            summary=summary,
            direct_cause="节点执行时没有下发可执行 instruction，模型无法开始操作。",
            root_cause="markdown2midscene 转换阶段丢失了步骤文本或 aiAction 内容。",
            suggestion="回查 markdown2midscene 产物，补齐空 instruction，并阻断空步骤继续下发执行。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "原始错误直接出现 `No specific instruction was provided` 或同类信号。",
                    "失败步骤文本为空，模型没有拿到可执行动作。",
                ]
            ),
            exclusion_reasoning="该 case 的强证据直接指向转换产物缺少 instruction，不是页面数据或模型服务异常。",
            decision_path=decision_path
            + ["- 归因结论：Bits2Midscene-解析步骤 / 空步骤"],
        )

    if _looks_like_mixed_url_step(first_step_name) or _looks_like_mixed_url_step(
        failed_step_name
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 4 步骤/instruction",
                "hit",
                "同一节点混写 URL 与 AI 操作，命中 URL 解析异常特征",
            )
        )
        summary = "URL 和 AI 操作被混写在同一步，转换后步骤拆分异常（Bits2Midscene-解析步骤 / URL）"
        return _build_classification_result(
            category="Bits2Midscene-解析步骤",
            subcategory="URL",
            confidence="高",
            summary=summary,
            direct_cause="同一步同时包含 URL 与操作描述，执行时无法稳定拆分成正确节点。",
            root_cause="转换链路没有把 url 节点与 aiAction 节点分开生成。",
            suggestion="把 URL 跳转与 AI 操作拆成独立步骤，再重新生成 Midscene 用例。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "失败步骤文本同时包含 URL 和操作描述。",
                    "问题更像转换阶段拆步异常，而不是页面运行时故障。",
                ]
            ),
            exclusion_reasoning="不是页面运行时问题，而是步骤结构在转换阶段就已不合法。",
            decision_path=decision_path
            + ["- 归因结论：Bits2Midscene-解析步骤 / URL"],
        )

    if any(token in combined for token in ["page not found", "404"]):
        decision_path.append(
            _build_decision_line(
                "Layer 4 步骤/instruction",
                "hit",
                "首步访问直接落到 404，URL 配置明显错误",
            )
        )
        summary = "首步 URL 进入 404 / Page not found，case 配置的访问地址不正确（Case 描述 - 业务QA / URL）"
        return _build_classification_result(
            category="Case 描述 - 业务QA",
            subcategory="URL",
            confidence="高",
            summary=summary,
            direct_cause="首个页面访问就落到错误地址，后续步骤全部失去执行基础。",
            root_cause="case 中配置的 URL、域名或必要参数已过期或填写错误。",
            suggestion="修正 case 中的 URL，并先单独验证首步能否进入正确业务页。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "首步页面直接出现 404 / Page not found。",
                    "失败发生在进入业务页之前，不属于模型执行阶段问题。",
                ]
            ),
            exclusion_reasoning="问题在用例给出的访问入口本身，而不是环境稳定性或模型执行路径。",
            decision_path=decision_path
            + ["- 归因结论：Case 描述 - 业务QA / URL"],
        )

    step_issue_text = "\n".join([error_message, failed_step_name, first_step_name]).lower()
    if any(
        token in step_issue_text
        for token in [
            "no user found",
            "required field",
            "is required",
            "must select",
            "please select",
            "please enter",
            "must enter",
            "必填",
            "请选择",
            "请输入",
        ]
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 4 步骤/instruction",
                "hit",
                "步骤缺少明确的可操作对象或必要输入",
            )
        )
        summary = "步骤描述缺少明确目标对象或必要输入，模型无法稳定执行（Case 描述 - 业务QA / 步骤描述）"
        return _build_classification_result(
            category="Case 描述 - 业务QA",
            subcategory="步骤描述",
            confidence="中",
            summary=summary,
            direct_cause="页面要求明确对象或必填项，但用例没有给出足够具体的操作目标。",
            root_cause="case 步骤描述过于泛化，缺少数据、对象或前置状态约束。",
            suggestion="在步骤里补充明确对象、筛选条件和必填数据，减少执行歧义。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误信息提示 required / must select / no user found。",
                    "问题更像步骤描述没有提供足够上下文，而不是页面加载失败。",
                ]
            ),
            exclusion_reasoning="未命中空 instruction、空数据或环境异常，失败更像步骤描述不充分。",
            decision_path=decision_path
            + ["- 归因结论：Case 描述 - 业务QA / 步骤描述"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 4 步骤/instruction",
            "excluded",
            "未命中空步骤、URL 错误或明显的步骤描述缺失信号",
        )
    )

    loading_tokens = [
        "timeout",
        "timed out",
        "loading",
        "spinner",
        "splash screen",
        "logo on a white background",
        "white background with only the tiktok logo",
        "white screen",
        "blank screen",
    ]
    if any(token in combined for token in loading_tokens) and _looks_like_assertion_step(
        effective_failed_step_name
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 5 时序检查",
                "hit",
                "失败步骤包含断言，且页面仍处于加载/等待状态",
            )
        )
        summary = "操作后过早发起断言，页面尚未稳定就进入校验（工具问题 - 模型 / 断言太快）"
        return _build_classification_result(
            category="工具问题 - 模型",
            subcategory="断言太快",
            confidence="中",
            summary=summary,
            direct_cause="操作刚执行完即开始断言，页面仍处于加载态或结果尚未刷新完成。",
            root_cause="模型在关键状态切换后缺少足够等待与重试策略。",
            suggestion="把操作与断言拆开，并在关键状态变化后增加显式等待。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "失败步骤本身带有明显断言语义。",
                    "截图或推理线索显示页面仍在 loading / splash / timeout 状态。",
                ]
            ),
            exclusion_reasoning="不是数据为空或 URL 错误，而是断言发起时机早于页面稳定时机。",
            decision_path=decision_path
            + ["- 归因结论：工具问题 - 模型 / 断言太快"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 5 时序检查",
            "excluded",
            "未同时命中断言步骤和页面未稳定的组合特征",
        )
    )

    if _looks_like_access_blocked_signal(combined):
        decision_path.append(
            _build_decision_line(
                "Layer 6 环境检查",
                "hit",
                "请求被网关或网络隔离策略拦截（network_segregation_rejected / rejected by gateway / IP not allowed）",
            )
        )
        summary = "请求被网关或网络隔离策略拦截，当前环境无法访问目标业务（环境问题 / 访问拦截）"
        return _build_classification_result(
            category="环境问题",
            subcategory="访问拦截",
            confidence="高",
            summary=summary,
            direct_cause="ROW Operations Gateway / 网络隔离策略直接拒绝了页面或接口请求。",
            root_cause="当前执行环境的出口 IP / 网络段没有访问目标服务的权限。",
            suggestion="切换到允许的网络段执行，或与基础设施 / 网络运维核对访问策略。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误中出现 network_segregation_rejected / rejected by gateway / not allowed to connect / IP not allowed。",
                    "失败发生在进入业务页面之前，是环境访问策略问题。",
                ]
            ),
            exclusion_reasoning="拦截信号位于进入业务页面之前，所有后续断言/数据现象都是连锁结果。",
            decision_path=decision_path + ["- 归因结论：环境问题 / 访问拦截"],
        )

    if _looks_like_login_page_signal(combined):
        decision_path.append(
            _build_decision_line(
                "Layer 6 环境检查",
                "hit",
                "链路进入登录页 / SSO 登录卡片 / session 失效（合并 error_message 与截图摘要后命中登录信号）",
            )
        )
        summary = "执行链路进入登录态或 session 失效，当前环境不满足自动化前置条件（环境问题 / 登录态）"
        return _build_classification_result(
            category="环境问题",
            subcategory="登录态",
            confidence="高",
            summary=summary,
            direct_cause="页面被 TikTok SSO / 二级登录卡片 / session 失效页拦下，业务内容未渲染。",
            root_cause="当前环境登录凭证缺失、失效或目标站点（含子域）登录态未注入。",
            suggestion="补齐目标站点（含子域）的有效登录态 / storageState；执行前先验证首屏不是 SSO 登录卡片。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "页面或日志出现 sign in / log in / SSO / session expired / Google 登录等登录态信号。",
                    "失败发生在进入业务页面之前，断言/数据现象均为连锁结果。",
                ]
            ),
            exclusion_reasoning="不是 case 步骤本身错误，而是执行环境没有准备好登录态。",
            decision_path=decision_path
            + ["- 归因结论：环境问题 / 登录态"],
        )

    if any(token in combined for token in ["dns", "cdn", "network error", "connection reset", "connection refused"]):
        decision_path.append(
            _build_decision_line(
                "Layer 6 环境检查",
                "hit",
                "网络或 CDN 访问异常",
            )
        )
        summary = "环境网络链路异常，页面或资源请求未能稳定完成（环境问题 / 网络错误）"
        return _build_classification_result(
            category="环境问题",
            subcategory="网络错误",
            confidence="中",
            summary=summary,
            direct_cause="关键资源或页面请求失败，导致自动化无法继续执行。",
            root_cause="当前执行环境存在网络连通性、CDN 或 DNS 问题。",
            suggestion="先排查环境网络、代理、CDN 可达性，再重试自动化任务。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误信息包含 network error / dns / cdn 等网络层信号。",
                    "问题出现在环境访问链路，而不是具体业务交互本身。",
                ]
            ),
            exclusion_reasoning="未命中 case URL 配错或模型空响应，更像环境连通性问题。",
            decision_path=decision_path
            + ["- 归因结论：环境问题 / 网络错误"],
        )

    if bool(loop_signal.get("detected")) and _looks_like_service_error_signal(combined):
        decision_path.append(
            _build_decision_line(
                "Layer 6 环境检查",
                "hit",
                "HTML 报告显示执行在同一前置步骤循环，且伴随 Request Error / RPC error",
            )
        )
        summary = "执行长时间卡在同一前置步骤循环，且同时出现服务异常信号（环境问题 / 网络错误）"
        return _build_classification_result(
            category="环境问题",
            subcategory="网络错误",
            confidence="高",
            summary=summary,
            direct_cause="自动化在同一组页面锚点上反复规划和重试，没有完成前置切换/展开/定位动作。",
            root_cause="环境侧接口、权限或服务异常阻断了前置步骤，导致执行只能在同一阶段循环重试。",
            suggestion="先排查该前置步骤依赖的接口、权限和 Request Error / RPC error，再确认页面能稳定进入下一步。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + loop_evidence
                + ["同时伴随 Request Error / RPC error，说明不是单纯的模型定位问题。"]
            ),
            exclusion_reasoning="失败发生在前置步骤循环阶段，后续业务断言尚未真正开始，不应继续落到步骤描述兜底。",
            decision_path=decision_path
            + ["- 归因结论：环境问题 / 网络错误"],
        )

    if _looks_like_service_error_signal(combined):
        decision_path.append(
            _build_decision_line(
                "Layer 6 环境检查",
                "hit",
                "HTML 报告出现 Request Error / RPC error / 未处理服务错误提示",
            )
        )
        summary = "页面出现 Request Error 或 RPC error，导致列表和断言相关步骤连锁失败（环境问题 / 网络错误）"
        return _build_classification_result(
            category="环境问题",
            subcategory="网络错误",
            confidence="高" if _looks_like_empty_data_signal(combined) else "中",
            summary=summary,
            direct_cause="页面存在未处理的服务错误提示或 RPC 错误，关键数据未能成功加载。",
            root_cause="环境侧接口、权限校验或服务调用异常，导致后续列表/分页断言失真。",
            suggestion="先排查 Request Error / permission check RPC error 的上游服务和权限链路，再重跑相关列表类 case。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "HTML 报告直接出现 Request Error、RPC error 或未处理服务错误提示。",
                    "列表为空、分页控件缺失等现象更像服务错误后的连锁结果。",
                ]
            ),
            exclusion_reasoning="问题根源在服务错误信号，而不是 case 步骤本身描述不清或模型空响应。",
            decision_path=decision_path
            + ["- 归因结论：环境问题 / 网络错误"],
        )

    if any(token in combined for token in loading_tokens):
        decision_path.append(
            _build_decision_line(
                "Layer 6 环境检查",
                "hit",
                "首屏长时间停留在 loading、白屏或启动页",
            )
        )
        summary = "首屏页面长时间停留在启动页或白屏，Midscene 未等到稳定业务态（Midscene / 启动失败）"
        return _build_classification_result(
            category="Midscene",
            subcategory="启动失败",
            confidence="高",
            summary=summary,
            direct_cause="页面仍处于加载态、白屏或启动页，等待超时导致后续步骤无法执行。",
            root_cause="自动化框架对页面就绪态的等待和重试不足。",
            suggestion="增强首屏稳定判断与重试逻辑，并在关键步骤前识别启动页/白屏状态。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "截图或推理中出现 splash screen / white screen / loading / timeout。",
                    "失败发生在进入正确业务页之前。",
                ]
            ),
            exclusion_reasoning="问题更像框架等待页面稳定失败，而不是 case 本身描述错误。",
            decision_path=decision_path
            + ["- 归因结论：Midscene / 启动失败"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 6 环境检查",
            "excluded",
            "未看到登录态、网络异常或首屏启动失败的强信号",
        )
    )

    if _is_business_bug(combined):
        decision_path.append(
            _build_decision_line(
                "Layer 7 产品 Bug",
                "hit",
                "执行路径正确，但业务侧返回异常错误",
            )
        )
        summary = "操作路径正确但业务侧返回异常，当前问题更像产品实现缺陷（Bug / 功能异常）"
        return _build_classification_result(
            category="Bug",
            subcategory="功能异常",
            confidence="中",
            summary=summary,
            direct_cause="页面或接口在关键动作执行时返回异常错误。",
            root_cause="业务逻辑、接口处理或页面状态机存在缺陷。",
            suggestion="按 Bug 提交给开发团队，并附上详情页、HTML 报告和错误信息。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误信息包含 500 / api error / internal server error / graphql error。",
                    "问题发生在正确业务路径中，而非进入页面前。",
                ]
            ),
            exclusion_reasoning="已排除 URL、数据、环境和明显模型异常，业务错误信号最强。",
            decision_path=decision_path + ["- 归因结论：Bug / 功能异常"],
        )
    decision_path.append(
        _build_decision_line(
            "Layer 7 产品 Bug",
            "excluded",
            "未拿到足够强的业务异常错误信号",
        )
    )

    model_boundary_tokens = [
        "429",
        "empty content from ai model",
        "failed to parse llm response into json",
        "tokens per minute",
    ]
    if any(token in combined for token in model_boundary_tokens):
        decision_path.append(
            _build_decision_line(
                "Layer 8 模型能力问题",
                "hit",
                "模型返回限流、空响应或 JSON 解析异常",
            )
        )
        summary = "模型服务返回异常或输出不可解析，当前步骤无法继续执行（工具问题 - 模型 / 执行边界）"
        return _build_classification_result(
            category="工具问题 - 模型",
            subcategory="执行边界",
            confidence="高",
            summary=summary,
            direct_cause="模型返回限流、空响应或结构化结果解析失败。",
            root_cause="模型服务稳定性或输出格式不稳定，当前步骤超出可稳定执行边界。",
            suggestion="降低并发、切换更稳定模型，或把大步骤拆成更小动作后重试。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误信息中出现 429、empty content 或 JSON parse failed。",
                    "前面的数据、URL、环境层已排除。",
                ]
            ),
            exclusion_reasoning="不是页面本身无数据，也不是环境异常，核心问题在模型响应质量。",
            decision_path=decision_path
            + ["- 归因结论：工具问题 - 模型 / 执行边界"],
        )

    if any(token in combined for token in ["replanned 100 times", "replanned 30 times"]):
        decision_path.append(
            _build_decision_line(
                "Layer 8 模型能力问题",
                "hit",
                "模型长时间重规划但未收敛",
            )
        )
        summary = "模型在当前页面上长时间重规划未收敛，执行路径规划失败（工具问题 - 模型 / 规划能力）"
        return _build_classification_result(
            category="工具问题 - 模型",
            subcategory="规划能力",
            confidence="高",
            summary=summary,
            direct_cause="模型持续 replanning，但没有找到可执行且收敛的操作路径。",
            root_cause="当前页面结构复杂或步骤上下文过长，超出模型稳定规划能力。",
            suggestion="补充更清晰的定位锚点，并把复合步骤拆小后重试。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "报告中出现 Replanned 30/100 times。",
                    "前置层级已排除数据、URL、环境问题。",
                ]
            ),
            exclusion_reasoning="失败主因不是环境或数据，而是模型规划反复失败。",
            decision_path=decision_path
            + ["- 归因结论：工具问题 - 模型 / 规划能力"],
        )

    if not bool(loop_signal.get("detected")) and any(
        token in combined
        for token in [
            "unable to locate",
            "element not found",
            "failed to locate",
            "misclick",
            "not visible",
        ]
    ):
        decision_path.append(
            _build_decision_line(
                "Layer 8 模型能力问题",
                "hit",
                "步骤清晰但模型仍未稳定定位到目标元素",
            )
        )
        summary = "页面已有内容但模型未稳定找到目标元素，执行边界不足（工具问题 - 模型 / 执行边界）"
        return _build_classification_result(
            category="工具问题 - 模型",
            subcategory="执行边界",
            confidence=confidence,
            summary=summary,
            direct_cause="模型没有稳定找到目标元素，或点击位置与页面真实结构不匹配。",
            root_cause="视觉锚点不足、页面结构复杂，导致模型执行边界暴露。",
            suggestion="在步骤中补充更明确的定位信息，并把复杂交互拆成更小动作。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + [
                    "错误信息包含 failed to locate / element not found / not visible。",
                    "前置层级未命中数据、URL、环境等更强证据。",
                ]
            ),
            exclusion_reasoning="在排除数据、URL、环境问题后，元素定位失败更符合模型执行边界问题。",
            decision_path=decision_path
            + ["- 归因结论：工具问题 - 模型 / 执行边界"],
        )

    if bool(loop_signal.get("detected")):
        decision_path.append(
            _build_decision_line(
                "Layer 8 模型能力问题",
                "hit",
                "HTML 报告显示执行在同一组页面锚点上反复规划/定位，但没有形成有效前进",
            )
        )
        summary = "执行长时间卡在同一前置步骤循环，未形成有效推进（工具问题 - 模型 / 规划能力）"
        return _build_classification_result(
            category="工具问题 - 模型",
            subcategory="规划能力",
            confidence="中",
            summary=summary,
            direct_cause="模型在同一组页面锚点上持续重试，没有稳定完成下一步动作。",
            root_cause="当前页面结构或交互反馈不足，导致模型规划长期不收敛。",
            suggestion="补充更明确的步骤锚点，或在前置步骤完成后再拆分执行后续动作。",
            failure_phenomenon=phenomenon,
            key_evidence=_compact_evidence(
                evidence_lines
                + loop_evidence
                + ["没有检测到更强的服务错误、空数据或 URL 错误信号。"]
            ),
            exclusion_reasoning="已排除更强的环境、URL 和空数据信号，剩余最强特征是执行在同一阶段长期循环。",
            decision_path=decision_path
            + ["- 归因结论：工具问题 - 模型 / 规划能力"],
        )

    decision_path.append(
        _build_decision_line(
            "Layer 8 模型能力问题",
            "excluded",
            "未看到足以确定模型服务或规划问题的强信号",
        )
    )

    summary = "当前证据不足以确定唯一根因，优先怀疑步骤描述或断言口径存在缺口（Case 描述 - 业务QA / 步骤描述）"
    return _build_classification_result(
        category="Case 描述 - 业务QA",
        subcategory="步骤描述",
        confidence="低",
        summary=summary,
        direct_cause="现有报告没有给出足够强的单点证据，无法直接锁定某一层责任。",
        root_cause="步骤描述、页面状态和报告线索之间仍存在信息缺口。",
        suggestion="补充页面状态截图、节点错误和更明确的步骤目标后，再重新分析或重跑。",
        failure_phenomenon=phenomenon,
        key_evidence=_compact_evidence(
            evidence_lines
            + [
                "现有线索没有形成单一强证据链。",
                "根据新版规则，证据不足时不能直接归为空 instruction。",
            ]
        ),
        exclusion_reasoning="已按数据、断言、步骤、时序、环境、Bug、模型层逐层排除，但没有单一命中项。",
        decision_path=decision_path
        + ["- 归因结论：Case 描述 - 业务QA / 步骤描述（低置信度）"],
    )


def _summarize_screenshot_verification(
    first_step_name: str,
    failed_step_name: str,
    error_message: str,
    combined_reasoning: str,
    first_screenshot_summary: str = "",
    failed_screenshot_summary: str = "",
) -> str:
    effective_failed_step_name = failed_step_name or first_step_name
    screenshot_signals = _summarize_screenshot_signals(
        first_screenshot_summary, failed_screenshot_summary
    )
    combined = "\n".join(
        [
            first_step_name,
            effective_failed_step_name,
            error_message,
            combined_reasoning,
            screenshot_signals,
        ]
    ).lower()

    if _reasoning_conflicts_with_screenshot(combined_reasoning, screenshot_signals):
        if _looks_like_login_page_signal(screenshot_signals):
            return "AI reasoning 与截图结论存在冲突：截图显示登录页/会话失效，但 reasoning 仍按业务页面或空列表继续分析，应以截图中的登录页线索为准。"
        if _looks_like_404_signal(screenshot_signals):
            return "AI reasoning 与截图结论存在冲突：截图显示 404 / Page not found，但 reasoning 仍按业务页面继续分析，应以首步错误地址线索为准。"
        if _looks_like_loading_signal(screenshot_signals):
            return "AI reasoning 与截图结论存在冲突：截图显示页面仍处于启动页、白屏或 loading，但 reasoning 已按稳定业务态分析，应以截图中的未稳定页面线索为准。"
    if _has_missing_instruction_signal(
        failed_step_name, error_message, combined_reasoning
    ):
        return "失败节点没有 instruction，问题首先出在步骤生成，当前截图线索不足以支撑执行。"
    if _looks_like_loading_signal(combined):
        return "截图线索显示页面停留在 TikTok logo 白底启动页或白屏，尚未进入目标业务页面。"
    if any(
        token in combined
        for token in [
            "couldn't find this account",
            "account not found",
        ]
    ):
        return "截图线索对应账号不存在页，而不是目标 profile 页面。"
    if _looks_like_404_signal(combined):
        return "截图线索应为 404 / Page not found，后续失败属于连锁反应。"
    if any(
        token in combined
        for token in ["does not match the expected url", "redirected page is"]
    ):
        return "截图线索显示点击后跳到了与预期不同的 URL 或账号页面。"
    if "reposts tab is displayed" in combined:
        return "截图线索显示 profile 页面可见 Reposts tab，与“不可见”的断言不一致。"
    if any(
        token in combined for token in ["no videos in this collection", "no result"]
    ):
        return "截图线索显示列表为空或 collection 无内容，页面实际数据状态与断言不一致。"
    if any(
        token in combined
        for token in ["failed to locate", "unable to find", "element not found"]
    ):
        return "截图线索显示页面已有内容，但模型未能稳定找到目标元素。"
    return "截图原图未直接结构化提取，当前结论基于 Markdown/HTML 报告中的页面描述与 AI 推理线索。"


def _analyze_failed_case(
    task_id: Any,
    case_item: dict[str, Any],
    report_dir: Path | None = None,
) -> dict[str, Any]:
    case_execution_id = case_item.get("case_execution_id")
    nodes = _query_case_nodes(case_execution_id)
    first_node = _get_first_node(nodes)
    failed_node = _get_failed_node(nodes)
    failed_step_index = 0
    if failed_node is not None:
        for index, node in enumerate(nodes, start=1):
            if node is failed_node:
                failed_step_index = index
                break

    report_payload = None
    failed_tasks: list[dict[str, Any]] = []
    report_source = "none"
    report_error = ""
    markdown_report_url = str(
        case_item.get("markdown_report_url")
        or MARKDOWN_REPORT_ARCHIVE_LINK_TEMPLATE.format(
            task_id=task_id,
            case_execution_id=case_execution_id,
        )
    )
    report_url = str(case_item.get("html_report_url") or "")

    archive_bytes: bytes | None = None
    if markdown_report_url:
        try:
            archive_bytes = _fetch_markdown_report_archive(markdown_report_url)
            report_payload = _parse_markdown_report_payload(
                _read_report_md_from_archive(archive_bytes)
            )
            failed_tasks = _extract_failed_tasks(report_payload)
            report_source = "markdown_tar"
        except Exception as exc:
            report_error = f"markdown tar unavailable: {exc}"
            archive_bytes = None

    if report_source != "markdown_tar" and report_url:
        try:
            report_payload = _extract_report_payload(_fetch_html_report(report_url))
            failed_tasks = _extract_failed_tasks(report_payload)
            report_source = "html"
        except Exception as exc:
            report_error = (
                f"{report_error}; html fallback failed: {exc}"
                if report_error
                else f"html fallback failed: {exc}"
            )

    loop_signal = _summarize_execution_loop(report_payload)
    primary_failed_task = failed_tasks[0] if failed_tasks else {}
    report_reasoning = _collect_report_reasoning(report_payload)
    first_step_name = _extract_node_instruction(first_node)
    failed_step_name = _extract_node_instruction(failed_node)
    report_execution_name = str(
        primary_failed_task.get("execution_name") or loop_signal.get("execution_name") or ""
    )
    failed_step_display_name = failed_step_name or report_execution_name or first_step_name
    error_message = _get_node_error(failed_node) or str(
        primary_failed_task.get("error_message") or ""
    )
    reasoning_content = str(
        primary_failed_task.get("reasoning_content")
        or report_reasoning.get("last_reasoning")
        or report_reasoning.get("first_reasoning")
        or ""
    )
    case_level_reasoning = "\n".join(
        part
        for part in [
            error_message,
            reasoning_content,
            str(loop_signal.get("summary") or ""),
        ]
        if part
    )
    classification_reasoning = str(
        case_level_reasoning
        or reasoning_content
        or str(report_reasoning.get("last_reasoning") or "")
        or str(report_reasoning.get("first_reasoning") or "")
    )
    first_screenshot_summary = str(
        primary_failed_task.get("first_screenshot_summary") or ""
    )
    failed_screenshot_summary = str(
        primary_failed_task.get("failed_screenshot_summary") or ""
    )

    first_screenshot_relpaths, failure_screenshot_relpaths = (
        _collect_report_screenshot_relpaths(report_payload)
    )

    first_screenshot_paths: list[str] = []
    failure_screenshot_paths: list[str] = []
    if archive_bytes is not None and report_dir is not None and (
        first_screenshot_relpaths or failure_screenshot_relpaths
    ):
        try:
            target_dir = (
                Path(report_dir)
                / "analysis_screenshots"
                / str(case_execution_id or "unknown")
            )
            extracted_map = _extract_screenshots_from_archive(
                archive_bytes,
                list({*first_screenshot_relpaths, *failure_screenshot_relpaths}),
                target_dir,
            )
            for rel in first_screenshot_relpaths:
                local = extracted_map.get(rel)
                if local:
                    try:
                        first_screenshot_paths.append(
                            str(Path(local).relative_to(report_dir))
                        )
                    except ValueError:
                        first_screenshot_paths.append(local)
            for rel in failure_screenshot_relpaths:
                local = extracted_map.get(rel)
                if local:
                    try:
                        failure_screenshot_paths.append(
                            str(Path(local).relative_to(report_dir))
                        )
                    except ValueError:
                        failure_screenshot_paths.append(local)
        except Exception as exc:
            report_error = (
                f"{report_error}; screenshot extraction failed: {exc}"
                if report_error
                else f"screenshot extraction failed: {exc}"
            )
    classification = _classify_case(
        first_step_name,
        failed_step_name,
        error_message,
        classification_reasoning,
        loop_signal,
        first_screenshot_summary,
        failed_screenshot_summary,
        first_screenshot_paths=first_screenshot_paths,
        failure_screenshot_paths=failure_screenshot_paths,
        first_screenshot_relpaths=first_screenshot_relpaths,
        failure_screenshot_relpaths=failure_screenshot_relpaths,
    )
    screenshot_verification = _summarize_screenshot_verification(
        first_step_name,
        failed_step_name,
        error_message,
        classification_reasoning,
        first_screenshot_summary,
        failed_screenshot_summary,
    )
    display_reasoning = (
        str(loop_signal.get("summary") or "")
        or reasoning_content
        or str(report_reasoning.get("last_reasoning") or "")
        or str(report_reasoning.get("first_reasoning") or "")
    )

    return {
        "case_name": str(case_item.get("case_name") or ""),
        "case_execution_id": str(case_execution_id or ""),
        "detail_url": str(case_item.get("detail_url") or ""),
        "markdown_report_url": markdown_report_url,
        "html_report_url": report_url,
        "report_source": report_source,
        "failed_step_index": failed_step_index,
        "failed_step": failed_step_display_name,
        "first_step": first_step_name,
        "error_message": error_message,
        "reasoning_snippet": _trim_text(display_reasoning),
        "screenshot_verification": _trim_text(
            screenshot_verification, limit=MAX_SCREENSHOT_SUMMARY
        ),
        "first_screenshot_paths": first_screenshot_paths,
        "failure_screenshot_paths": failure_screenshot_paths,
        "first_screenshot_relpaths": first_screenshot_relpaths,
        "failure_screenshot_relpaths": failure_screenshot_relpaths,
        "execution_name": report_execution_name,
        "task_type": str(primary_failed_task.get("task_type") or ""),
        "loop_summary": str(loop_signal.get("summary") or ""),
        "owner": classification["owner"],
        "attribution_category": classification["attribution_category"],
        "attribution_subcategory": classification["attribution_subcategory"],
        "confidence": classification["confidence"],
        "failure_phenomenon": classification["failure_phenomenon"],
        "key_evidence": classification["key_evidence"],
        "exclusion_reasoning": classification["exclusion_reasoning"],
        "decision_path": classification["decision_path"],
        "reasoning": classification["reasoning"],
        "convergence_note": classification["convergence_note"],
        "summary": classification["summary"],
        "direct_cause": classification["direct_cause"],
        "root_cause": classification["root_cause"],
        "suggestion": classification["suggestion"],
        "report_error": report_error,
    }


def _analyze_failed_cases(
    task_id: Any,
    failed_cases: list[dict[str, Any]],
    report_dir: Path | None = None,
) -> list[dict[str, Any]]:
    analyzed: list[dict[str, Any]] = []
    for item in failed_cases:
        try:
            analyzed.append(_analyze_failed_case(task_id, item, report_dir))
        except Exception as exc:
            analyzed.append(
                {
                    "case_name": str(item.get("case_name") or ""),
                    "case_execution_id": str(item.get("case_execution_id") or ""),
                    "detail_url": str(item.get("detail_url") or ""),
                    "markdown_report_url": str(item.get("markdown_report_url") or ""),
                    "html_report_url": str(item.get("html_report_url") or ""),
                    "report_source": "analysis_error",
                    "failed_step_index": 0,
                    "failed_step": "",
                    "first_step": "",
                    "error_message": "",
                    "reasoning_snippet": "",
                    "screenshot_verification": "报告分析脚本异常，未能提取截图验证线索",
                    "first_screenshot_paths": [],
                    "failure_screenshot_paths": [],
                    "first_screenshot_relpaths": [],
                    "failure_screenshot_relpaths": [],
                    "execution_name": "",
                    "task_type": "",
                    "loop_summary": "",
                    "owner": "分析失败",
                    "attribution_category": "分析失败",
                    "attribution_subcategory": "脚本异常",
                    "confidence": "低",
                    "failure_phenomenon": "报告分析脚本异常，未能完成该 case 的结构化解析。",
                    "key_evidence": [f"脚本异常：{exc}"],
                    "exclusion_reasoning": "分析脚本在提取节点或 HTML 报告时异常退出，无法继续逐层归因。",
                    "decision_path": [
                        "- Layer 1 证据充分性：⚠️ 证据不足（分析脚本异常，未能拿到完整节点与报告线索）",
                        "- 归因结论：分析失败 / 脚本异常",
                    ],
                    "reasoning": "当前失败由分析脚本自身异常导致，而不是 case 本身完成了有效归因。",
                    "convergence_note": "",
                    "summary": "脚本未能完成该 case 的报告解析",
                    "direct_cause": "报告分析脚本执行异常",
                    "root_cause": str(exc),
                    "suggestion": "手动打开详情页与 HTML 报告补充分析",
                    "report_error": str(exc),
                }
            )
    return analyzed


def _format_flow(flow: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for index, step in enumerate(flow, start=1):
        if "url" in step:
            lines.append(f"{index}. [url] {step['url']}")
        elif "ai" in step:
            lines.append(f"{index}. [ai] {step['ai']}")
    return "\n".join(lines)


def _format_task_status(task_status_payload: dict[str, Any] | None) -> str:
    if not task_status_payload:
        return "已创建任务，待轮询执行结果"

    status_code = task_status_payload.get("status_code")
    code = task_status_payload.get("code")
    message = (
        task_status_payload.get("status_msg")
        or task_status_payload.get("msg")
        or task_status_payload.get("message")
        or ""
    )
    execute_status = _extract_task_execute_status(task_status_payload)
    counts = _extract_task_counts(task_status_payload)

    if _task_polling_succeeded(task_status_payload):
        prefix = "任务已完成，可开始分析"
    else:
        prefix = "执行中"

    parts = [prefix, f"status_code={status_code}"]
    if execute_status is not None:
        parts.append(f"execute_status={execute_status}")
    if code is not None:
        parts.append(f"code={code}")
    if counts:
        parts.append(
            "cases={success}/{failed}/{unknown}/{total}".format(
                success=counts.get("case_success_num", "-"),
                failed=counts.get("case_failed_num", "-"),
                unknown=counts.get("case_unknown_num", "-"),
                total=counts.get("case_total_num", "-"),
            )
        )
    if message:
        parts.append(f"msg={message}")
    return "，".join(parts)


def _render_failed_case_rows(
    failed_cases: list[dict[str, Any]], ready_for_analysis: bool
) -> str:
    if not failed_cases:
        if ready_for_analysis:
            return "- 轮询成功后未查询到失败 case。\n"
        return "- 任务已触发，待轮询状态成功后补充。\n"

    rows = [
        "| # | Case 名称 | Case Execution ID | 详情页 | Markdown 报告 | HTML 回退报告 |",
        "|---|-----------|-------------------|--------|---------------|--------------|",
    ]
    for index, item in enumerate(failed_cases, start=1):
        rows.append(
            "| {index} | {case_name} | {case_execution_id} | [详情页]({detail_url}) | [md.tar]({markdown_report_url}) | [HTML]({html_report_url}) |".format(
                index=index,
                case_name=str(item.get("case_name") or "-").replace("|", "\\|"),
                case_execution_id=item.get("case_execution_id") or "-",
                detail_url=item.get("detail_url") or "-",
                markdown_report_url=item.get("markdown_report_url") or "-",
                html_report_url=item.get("html_report_url") or "-",
            )
        )
    return "\n".join(rows) + "\n"


def _render_generated_cases(tasks: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for index, task in enumerate(tasks, start=1):
        name = str(task.get("name") or f"Case {index}")
        raw_flow_value = task.get("flow")
        raw_flow: list[Any] = raw_flow_value if isinstance(raw_flow_value, list) else []
        flow: list[dict[str, str]] = []
        for step in raw_flow:
            if isinstance(step, dict):
                normalized_step: dict[str, str] = {}
                if isinstance(step.get("url"), str) and step.get("url"):
                    normalized_step["url"] = str(step["url"])
                if isinstance(step.get("ai"), str) and step.get("ai"):
                    normalized_step["ai"] = str(step["ai"])
                if normalized_step:
                    flow.append(normalized_step)
        sections.append(f"### {index}. {name}\n")
        sections.append("```text")
        sections.append(_format_flow(flow) or "No steps")
        sections.append("```\n")
    return "\n".join(sections).strip() + "\n"


def _annotate_converged_cases(analyzed_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for item in analyzed_cases:
        key = (
            str(item.get("attribution_category") or ""),
            str(item.get("attribution_subcategory") or ""),
            str(item.get("summary") or ""),
        )
        groups.setdefault(key, []).append(item)

    for group in groups.values():
        if len(group) <= 1:
            for item in group:
                item["convergence_note"] = ""
            continue
        case_names = [str(item.get("case_name") or "未知 Case") for item in group]
        for item in group:
            peer_names = [name for name in case_names if name != str(item.get("case_name") or "")]
            if peer_names:
                item["convergence_note"] = (
                    f"与 {peer_names[0]} 等 {len(group) - 1} 个 case 共享上游原因："
                    f"{item.get('summary') or '同类根因'}"
                )
            else:
                item["convergence_note"] = ""
    return analyzed_cases


def _render_analysis_summary(
    analyzed_cases: list[dict[str, Any]], ready_for_analysis: bool
) -> str:
    if not analyzed_cases:
        if ready_for_analysis:
            return "- 轮询成功后未产出失败 case 分析。\n"
        return "- 任务已触发，待轮询状态成功后开始分析。\n"

    analyzed_cases = _annotate_converged_cases(analyzed_cases)
    rows = [
        "| # | Case 名称 | 归因类别 | 归因子分类 | 根因摘要 | 关键截图 | 置信度 |",
        "|---|-----------|----------|------------|----------|----------|--------|",
    ]
    for index, item in enumerate(analyzed_cases, start=1):
        screenshot_cell = _format_summary_screenshot_cell(item)
        rows.append(
            "| {index} | {case_name} | {category} | {subcategory} | {summary} | {screenshot} | {confidence} |".format(
                index=index,
                case_name=str(item.get("case_name") or "-").replace("|", "\\|"),
                category=str(item.get("attribution_category") or item.get("owner") or "-").replace("|", "\\|"),
                subcategory=str(item.get("attribution_subcategory") or "-").replace("|", "\\|"),
                summary=str(item.get("summary") or "-").replace("|", "\\|"),
                screenshot=screenshot_cell.replace("|", "\\|"),
                confidence=str(item.get("confidence") or "-").replace("|", "\\|"),
            )
        )
    return "\n".join(rows) + "\n"


def _format_summary_screenshot_cell(item: dict[str, Any]) -> str:
    """Pick the most decisive screenshot for the summary table cell.

    Prefers the failure screenshot; falls back to the first-step screenshot.
    Renders as inline markdown image so the analyzed report visually shows
    the evidence instead of pointing at the raw `.md.tar` archive.
    """
    failure_paths = item.get("failure_screenshot_paths") or []
    first_paths = item.get("first_screenshot_paths") or []
    if isinstance(failure_paths, list) and failure_paths:
        path = str(failure_paths[0])
        return f"![失败截图]({path})"
    if isinstance(first_paths, list) and first_paths:
        path = str(first_paths[0])
        return f"![首步截图]({path})"
    failure_rel = item.get("failure_screenshot_relpaths") or []
    if isinstance(failure_rel, list) and failure_rel:
        return f"`{failure_rel[0]}` (未本地落盘)"
    first_rel = item.get("first_screenshot_relpaths") or []
    if isinstance(first_rel, list) and first_rel:
        return f"`{first_rel[0]}` (未本地落盘)"
    return "-"


_MARKDOWN_ARCHIVE_SCREENSHOT_REF_PATTERN = re.compile(
    r"(?<![\w/])(?:\./)?screenshots/([^\s),\]]+)"
)


def _rewrite_markdown_archive_screenshot_refs(text: str, case_execution_id: str) -> str:
    if not text or not case_execution_id:
        return text

    def replace(match: re.Match[str]) -> str:
        screenshot_name = match.group(1).lstrip("/")
        if not screenshot_name or ".." in Path(screenshot_name).parts:
            return match.group(0)
        return f"analysis_screenshots/{case_execution_id}/{screenshot_name}"

    return _MARKDOWN_ARCHIVE_SCREENSHOT_REF_PATTERN.sub(replace, text)


def _rewrite_case_analysis_screenshot_refs(value: Any, case_execution_id: str) -> Any:
    if isinstance(value, str):
        return _rewrite_markdown_archive_screenshot_refs(value, case_execution_id)
    if isinstance(value, list):
        return [
            _rewrite_case_analysis_screenshot_refs(item, case_execution_id)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _rewrite_case_analysis_screenshot_refs(item, case_execution_id)
            for key, item in value.items()
        }
    return value


def _normalize_case_analysis_local_paths(item: dict[str, Any]) -> dict[str, Any]:
    case_execution_id = str(item.get("case_execution_id") or "").strip()
    if not case_execution_id:
        return item
    rewritten = _rewrite_case_analysis_screenshot_refs(item, case_execution_id)
    return rewritten if isinstance(rewritten, dict) else item


def _build_case_meta_comment(item: dict[str, Any]) -> str:
    return (
        "<!-- "
        + CASE_META_COMMENT_PREFIX
        + json.dumps(item, ensure_ascii=False)
        + " -->"
    )


def _extract_existing_analyzed_cases(report_path: Path) -> list[dict[str, Any]]:
    if not report_path.is_file():
        return []

    content = _read_text(report_path)
    detail_body = _extract_marked_section(
        content, ANALYSIS_DETAIL_START, ANALYSIS_DETAIL_END
    )
    if not detail_body:
        return []

    pattern = re.compile(
        r"<!--\s*" + re.escape(CASE_META_COMMENT_PREFIX) + r"(.*?)\s*-->",
        re.DOTALL,
    )
    analyzed_cases: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for raw_payload in pattern.findall(detail_body):
        try:
            item = json.loads(raw_payload.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        case_execution_id = str(item.get("case_execution_id") or "").strip()
        if not case_execution_id or case_execution_id in seen_case_ids:
            continue
        seen_case_ids.add(case_execution_id)
        analyzed_cases.append(item)
    return analyzed_cases


def _format_screenshot_verification_lines(item: dict[str, Any]) -> list[str]:
    """Render the per-case screenshot verification block.

    Replaces the old single-line verification text with the verification
    summary plus inline image embeds for the first-step and failure-step
    screenshots, so reviewers see the actual frame instead of being told
    to fetch the `.md.tar` archive.
    """
    lines: list[str] = []
    verification_text = item.get("screenshot_verification") or "未提取到截图验证线索"
    lines.append(f"- 验证结论：{verification_text}")

    first_paths = item.get("first_screenshot_paths") or []
    failure_paths = item.get("failure_screenshot_paths") or []
    first_rel = item.get("first_screenshot_relpaths") or []
    failure_rel = item.get("failure_screenshot_relpaths") or []

    if isinstance(first_paths, list) and first_paths:
        for path in first_paths:
            lines.append(f"- 首步截图：![首步截图]({path})")
    elif isinstance(first_rel, list) and first_rel:
        for rel in first_rel:
            lines.append(f"- 首步截图（未本地落盘，仅留归档相对路径）：`{rel}`")

    if isinstance(failure_paths, list) and failure_paths:
        for path in failure_paths:
            lines.append(f"- 失败截图：![失败截图]({path})")
    elif isinstance(failure_rel, list) and failure_rel:
        for rel in failure_rel:
            lines.append(f"- 失败截图（未本地落盘，仅留归档相对路径）：`{rel}`")

    if (
        not first_paths
        and not failure_paths
        and not first_rel
        and not failure_rel
    ):
        lines.append(
            "- 当前 case 未提取到具体截图，可能是 .md.tar 不可用或 report.md 中没有截图引用。"
        )
    return lines


def _format_summary_drilldown_lines(
    item: dict[str, Any], key_evidence: list[str]
) -> list[str]:
    """Render the drill-down `根因摘要` block under `最终归因`.

    The earlier format printed only ``item['summary']`` as a single line,
    forcing reviewers to scroll back up through `失败现象`, `关键证据`,
    `截图验证` etc. to understand why the responsibility lands where it
    does. This helper inlines the decisive drill-down—failure step,
    concrete phenomenon, top evidence, key screenshot, and the final
    responsibility verdict—so the summary stands alone.
    """
    failed_step_index = item.get("failed_step_index") or "-"
    failed_step = str(item.get("failed_step") or "-")
    failure_phenomenon = str(
        item.get("failure_phenomenon") or item.get("summary") or "-"
    )
    error_message = str(item.get("error_message") or "").strip()
    loop_summary = str(item.get("loop_summary") or "").strip()
    attribution_category = str(
        item.get("attribution_category") or item.get("owner") or "-"
    )
    attribution_subcategory = str(item.get("attribution_subcategory") or "-")
    summary_text = str(item.get("summary") or "-")

    lines: list[str] = []
    lines.append(f"  - 失败环节：第 {failed_step_index} 步 — {failed_step}")
    lines.append(f"  - 具体现象：{failure_phenomenon}")
    if error_message:
        lines.append(f"  - 报告原始错误：{_trim_text(error_message, limit=240)}")
    if loop_summary:
        lines.append(f"  - 循环/序列特征：{_trim_text(loop_summary, limit=240)}")
    if isinstance(key_evidence, list) and key_evidence:
        top_evidence = [str(e) for e in key_evidence[:2] if e]
        for evidence in top_evidence:
            lines.append(f"  - 关键证据：{evidence}")

    failure_paths = item.get("failure_screenshot_paths") or []
    first_paths = item.get("first_screenshot_paths") or []
    if isinstance(failure_paths, list) and failure_paths:
        lines.append(f"  - 关键截图：![失败截图]({failure_paths[0]})")
    elif isinstance(first_paths, list) and first_paths:
        lines.append(f"  - 关键截图：![首步截图]({first_paths[0]})")
    else:
        failure_rel = item.get("failure_screenshot_relpaths") or []
        first_rel = item.get("first_screenshot_relpaths") or []
        if isinstance(failure_rel, list) and failure_rel:
            lines.append(f"  - 关键截图（仅归档相对路径）：`{failure_rel[0]}`")
        elif isinstance(first_rel, list) and first_rel:
            lines.append(f"  - 关键截图（仅归档相对路径）：`{first_rel[0]}`")

    lines.append(
        f"  - 责任判定：{attribution_category} / {attribution_subcategory}"
    )
    lines.append(f"  - 一句话摘要：{summary_text}")
    return lines


def _render_analysis_details(
    analyzed_cases: list[dict[str, Any]],
    ready_for_analysis: bool,
    include_meta_comments: bool = False,
) -> str:
    if not analyzed_cases:
        if ready_for_analysis:
            return "- 轮询成功后未产出失败 case 详细分析。\n"
        return "- 任务已触发，待轮询状态成功后补充详细分析。\n"

    analyzed_cases = _annotate_converged_cases(analyzed_cases)
    sections: list[str] = []
    for index, item in enumerate(analyzed_cases, start=1):
        item = _normalize_case_analysis_local_paths(item)
        if include_meta_comments:
            sections.append(_build_case_meta_comment(item))
        key_evidence = item.get("key_evidence") or []
        if not isinstance(key_evidence, list):
            key_evidence = []
        decision_path = item.get("decision_path") or []
        if not isinstance(decision_path, list):
            decision_path = []
        screenshot_lines = _format_screenshot_verification_lines(item)
        summary_drilldown_lines = _format_summary_drilldown_lines(item, key_evidence)
        sections.extend(
            [
                f"### Case {index}: {item.get('case_name') or '-'}",
                "",
                "| 项目 | 值 |",
                "|------|-----|",
                f"| 归因类别 | {item.get('attribution_category') or item.get('owner') or '-'} |",
                f"| 归因子分类 | {item.get('attribution_subcategory') or '-'} |",
                f"| 置信度 | {item.get('confidence') or '-'} |",
                f"| 失败步骤序号 | {item.get('failed_step_index') or '-'} |",
                f"| 失败步骤 | {item.get('failed_step') or '-'} |",
                f"| 首步 instruction | {item.get('first_step') or '-'} |",
                f"| 执行节点 | {item.get('execution_name') or '-'} |",
                f"| 任务类型 | {item.get('task_type') or '-'} |",
                f"| 报告来源 | {item.get('report_source') or '-'} |",
                f"| 错误信息 | {item.get('error_message') or '-'} |",
                "",
                "#### 失败现象",
                "",
                f"- {item.get('failure_phenomenon') or item.get('summary') or '-'}",
                "",
                "#### AI 推理关键信息",
                "",
                f"> {item.get('reasoning_snippet') or 'HTML 报告中未提取到 reasoning_content'}",
                "",
                "#### 循环特征",
                "",
                f"- {item.get('loop_summary') or '当前未检测到 execution 级循环特征'}",
                "",
                "#### 截图验证",
                "",
                *screenshot_lines,
                "",
                "#### 关键证据",
                "",
                *(
                    [f"- {evidence}" for evidence in key_evidence]
                    if key_evidence
                    else ["- 当前未提取到足够强的结构化证据"]
                ),
                "",
                "#### 归因决策路径",
                "",
                *(
                    decision_path
                    if decision_path
                    else ["- 当前未生成结构化决策路径"]
                ),
                "",
                "#### 排除判断",
                "",
                f"- {item.get('exclusion_reasoning') or '当前未补充排除判断'}",
                "",
                "#### 最终归因",
                "",
                "- 根因摘要（直接下钻到详细分析原因，不必再回看上文）：",
                *summary_drilldown_lines,
                f"- 归因类别 / 子分类：{item.get('attribution_category') or item.get('owner') or '-'} / {item.get('attribution_subcategory') or '-'}",
                f"- 直接原因：{item.get('direct_cause') or '-'}",
                f"- 根本原因：{item.get('root_cause') or '-'}",
                f"- 归因理由：{item.get('reasoning') or item.get('root_cause') or '-'}",
                f"- 置信度：{item.get('confidence') or '-'}",
                f"- 收敛标记：{item.get('convergence_note') or '-'}",
                f"- 修复建议：{item.get('suggestion') or '-'}",
                f"- 详情页：{item.get('detail_url') or '-'}",
                f"- Markdown 报告归档：{item.get('markdown_report_url') or '-'}",
                f"- HTML 回退报告：{item.get('html_report_url') or '-'}",
                "",
            ]
        )
        if item.get("report_error"):
            sections.extend(
                [
                    f"- 报告解析备注：{item.get('report_error')}",
                    "",
                ]
            )
    return "\n".join(sections).strip() + "\n"


def _estimate_detail_analysis_seconds(failed_case_count: int) -> int:
    if failed_case_count <= 0:
        return 0
    return DETAIL_ANALYSIS_FIXED_OVERHEAD_SECONDS + (
        failed_case_count * DETAIL_ANALYSIS_SECONDS_PER_CASE
    )


def _format_duration(seconds: int) -> str:
    normalized = max(int(seconds), 0)
    minutes, remain_seconds = divmod(normalized, 60)
    if minutes and remain_seconds:
        return f"约 {minutes} 分 {remain_seconds} 秒"
    if minutes:
        return f"约 {minutes} 分钟"
    return f"约 {remain_seconds} 秒"


def _shell_quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def _build_detail_command(task_id: Any, case_md_arg: str | None) -> str:
    command = (
        "python3 $SKILL_DIR/scripts/case2webe2e.py analyze-task "
        f"--task-id {task_id} --detail"
    )
    if case_md_arg:
        command += f" --case-md {_shell_quote(case_md_arg)}"
    return command


def _render_analysis_overview_section(
    report_path: Path,
    task_id: Any,
    task_name: str,
    task_status_payload: dict[str, Any],
    failed_cases: list[dict[str, Any]],
    case_md_arg: str | None,
) -> str:
    ready_for_analysis = _can_start_analysis(task_status_payload)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    failed_case_count = len(failed_cases)
    estimated_seconds = _estimate_detail_analysis_seconds(failed_case_count)

    confirmation_lines: list[str] = []
    if not ready_for_analysis:
        confirmation_lines.append("- 任务尚未完成，暂时不要进入失败 case 详细分析。")
    elif failed_case_count == 0:
        confirmation_lines.append("- 当前未发现失败 case，无需继续下钻详细分析。")
    else:
        confirmation_lines.extend(
            [
                f"- 是否继续对 {failed_case_count} 个失败 case 下钻详细分析？",
                f"- 预计耗时：{_format_duration(estimated_seconds)}",
                "- AI 必须在此处暂停，等待用户确认后再继续详细分析。",
                f"- 继续分析命令：`{_build_detail_command(task_id, case_md_arg)}`",
            ]
        )

    sections = [
        "## 报告分析 Overview",
        "",
        "| 项目 | 值 |",
        "|------|-----|",
        f"| 更新时间 | {updated_at} |",
        f"| report_file | `{report_path}` |",
        f"| task_id | {task_id} |",
        f"| task_name | {task_name or '-'} |",
        f"| 当前状态 | {_format_task_status(task_status_payload)} |",
        f"| 失败 Case 数 | {failed_case_count} |",
        f"| 预计详细分析耗时 | {_format_duration(estimated_seconds) if failed_case_count else '-'} |",
        "",
        "### 失败 Case 列表",
        "",
        _render_failed_case_rows(failed_cases, ready_for_analysis).strip(),
        "",
        "### 用户确认",
        "",
        *confirmation_lines,
        "",
    ]
    return "\n".join(sections).strip() + "\n"


def _render_analysis_detail_section(
    analyzed_cases: list[dict[str, Any]],
    ready_for_analysis: bool,
    total_failed_case_count: int,
    include_meta_comments: bool = False,
) -> str:
    completed_count = len(analyzed_cases)
    remaining_count = max(total_failed_case_count - completed_count, 0)

    progress_lines = [
        f"- 已完成详细分析：{completed_count}/{total_failed_case_count}",
        f"- 剩余待分析：{remaining_count}",
    ]
    if total_failed_case_count == 0:
        progress_lines.append("- 当前没有失败 case，无需生成详细分析。")
    elif remaining_count > 0:
        progress_lines.append(
            "- 当前详细分析未完成，可能因为命令超时或中断结束；重新执行同一条 `--detail` 命令会自动跳过已完成 case。"
        )
    else:
        progress_lines.append("- 当前已完成全部失败 case 的详细分析。")

    sections = [
        "## 失败 Case 详细分析",
        "",
        "### 分析进度",
        "",
        *progress_lines,
        "",
        "### 根因汇总",
        "",
        _render_analysis_summary(analyzed_cases, ready_for_analysis).strip(),
        "",
        "### 详细下钻",
        "",
        _render_analysis_details(
            analyzed_cases,
            ready_for_analysis,
            include_meta_comments=include_meta_comments,
        ).strip(),
        "",
    ]
    return "\n".join(sections).strip() + "\n"


def _write_analysis_sections_to_report(
    report_path: Path,
    overview_section: str,
    detail_section: str | None = None,
) -> None:
    content = _load_or_init_report(report_path)
    content = _replace_marked_section(
        content, ANALYSIS_OVERVIEW_START, ANALYSIS_OVERVIEW_END, overview_section
    )
    if detail_section is not None:
        content = _replace_marked_section(
            content, ANALYSIS_DETAIL_START, ANALYSIS_DETAIL_END, detail_section
        )
    _write_text(report_path, content)


def _render_task_analysis_report(
    task_id: Any,
    task_name: str,
    task_status_payload: dict[str, Any],
    failed_cases: list[dict[str, Any]],
    analyzed_cases: list[dict[str, Any]],
) -> str:
    task_url = TASK_LINK_TEMPLATE.format(task_id=task_id)
    ready_for_analysis = _can_start_analysis(task_status_payload)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = [
        "# Web E2E Task Analysis",
        "",
        "## 任务概览",
        "",
        "| 项目 | 值 |",
        "|------|-----|",
        f"| 更新时间 | {updated_at} |",
        f"| task_id | {task_id} |",
        f"| task_name | {task_name or '-'} |",
        f"| task_url | [TTAT任务链接]({task_url}) |",
        f"| 当前状态 | {_format_task_status(task_status_payload)} |",
        "",
        "## 失败 Case 列表",
        "",
        _render_failed_case_rows(failed_cases, ready_for_analysis).strip(),
        "",
        "## 根因汇总",
        "",
        _render_analysis_summary(analyzed_cases, ready_for_analysis).strip(),
        "",
        "## 详细分析",
        "",
        _render_analysis_details(analyzed_cases, ready_for_analysis).strip(),
        "",
    ]
    return "\n".join(sections)


def _render_test_report(
    report_path: Path,
    payload: dict[str, Any],
    metadata: dict[str, Any],
    case_group_id: Any,
    task_name: str,
    task_id: Any,
    task_status_payload: dict[str, Any] | None = None,
    task_name_from_query: str = "",
    failed_cases: list[dict[str, Any]] | None = None,
    analyzed_cases: list[dict[str, Any]] | None = None,
) -> str:
    task_url = TASK_LINK_TEMPLATE.format(task_id=task_id)
    effective_task_name = task_name_from_query or task_name
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return "\n".join(
        [
            "# Web E2E Test Report",
            "",
            "## 执行概览",
            "",
            "| 项目 | 值 |",
            "|------|-----|",
            f"| 更新时间 | {updated_at} |",
            f"| case.md | `{metadata['case_md']}` |",
            f"| report_file | `{report_path}` |",
            f"| env_file | `{metadata['env_file'] or '-'}` |",
            f"| creator | {metadata['creator']} |",
            f"| case_group_name | {metadata['case_group_name']} |",
            f"| case_group_id | {case_group_id} |",
            f"| case_group_action | {metadata.get('case_group_action') or '-'} |",
            f"| case_count | {metadata['case_count']} |",
            f"| case_priority_filter | {metadata['case_priority_filter']} |",
            f"| task_name | {effective_task_name} |",
            f"| task_id | {task_id} |",
            f"| task_url | [TTAT任务链接]({task_url}) |",
            "",
            "## 任务状态",
            "",
            f"- 当前状态：{_format_task_status(task_status_payload)}",
            "- 已创建任务并写入任务信息。",
            "",
        ]
    )


def _write_test_report(
    report_path: Path,
    payload: dict[str, Any],
    metadata: dict[str, Any],
    case_group_id: Any,
    task_name: str,
    task_id: Any,
    task_status_payload: dict[str, Any] | None = None,
    task_name_from_query: str = "",
    failed_cases: list[dict[str, Any]] | None = None,
    analyzed_cases: list[dict[str, Any]] | None = None,
) -> None:
    content = _render_test_report(
        report_path=report_path,
        payload=payload,
        metadata=metadata,
        case_group_id=case_group_id,
        task_name=task_name,
        task_id=task_id,
        task_status_payload=task_status_payload,
        task_name_from_query=task_name_from_query,
        failed_cases=failed_cases,
        analyzed_cases=analyzed_cases,
    )
    _write_text(report_path, content)


def _wait_for_task_completion(
    task_id: Any,
    poll_interval: int,
    max_wait_seconds: int,
    on_poll: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    start_time = time.time()
    while True:
        task_status_payload = _query_task_execution(task_id)
        if on_poll is not None:
            on_poll(task_status_payload)
        status_line = _format_task_status(task_status_payload)
        print(f"task_status: {status_line}")

        if _task_polling_succeeded(task_status_payload):
            return task_status_payload

        if max_wait_seconds > 0 and (time.time() - start_time) >= max_wait_seconds:
            raise SystemExit(
                "timed out waiting for task completion: "
                f"task_id={task_id}, max_wait_seconds={max_wait_seconds}"
            )

        time.sleep(max(poll_interval, 1))


def _normalize_flow_item(operation: dict[str, Any]) -> dict[str, str] | None:
    op_type = str(operation.get("operation") or operation.get("type") or "").strip()
    content = operation.get("content")
    if content is None:
        content = operation.get("text")
    if content is None:
        content = operation.get("value")
    if content is None:
        return None

    content_str = str(content).strip()
    if not content_str:
        return None

    if op_type == "url":
        return {"url": content_str}
    if op_type in {"aiAction", "ai", "action", "assert"}:
        return {"ai": content_str}
    return {"ai": content_str}


def _extract_flow(item: Any) -> list[dict[str, str]]:
    if isinstance(item, dict):
        raw_flow = item.get("flow")
        if isinstance(raw_flow, list):
            flow: list[dict[str, str]] = []
            for step in raw_flow:
                if not isinstance(step, dict):
                    continue
                if "url" in step and step["url"]:
                    flow.append({"url": str(step["url"]).strip()})
                elif "ai" in step and step["ai"]:
                    flow.append({"ai": str(step["ai"]).strip()})
            if flow:
                return flow

        case_obj = item.get("case")
        if isinstance(case_obj, dict):
            operations = case_obj.get("operations")
            if isinstance(operations, list):
                flow = []
                for operation in operations:
                    if isinstance(operation, dict):
                        normalized = _normalize_flow_item(operation)
                        if normalized:
                            flow.append(normalized)
                if flow:
                    return flow

        if isinstance(item.get("midscene_script"), str):
            steps = []
            for line in item["midscene_script"].splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("http://") or stripped.startswith("https://"):
                    steps.append({"url": stripped})
                else:
                    steps.append({"ai": stripped})
            if steps:
                return steps

    if isinstance(item, str):
        stripped = item.strip()
        if stripped:
            steps = []
            for line in stripped.splitlines():
                normalized = line.strip()
                if not normalized:
                    continue
                if normalized.startswith("http://") or normalized.startswith(
                    "https://"
                ):
                    steps.append({"url": normalized})
                else:
                    steps.append({"ai": normalized})
            if steps:
                return steps

    return []


def _extract_expectation_ids(item: Any) -> list[str]:
    if not isinstance(item, dict):
        return []
    candidates = [item.get("expectation_ids")]
    extra_info = item.get("extra_info")
    if isinstance(extra_info, dict):
        candidates.append(extra_info.get("expectation_ids"))

    for candidate in candidates:
        if isinstance(candidate, list):
            ids = [str(value).strip() for value in candidate if str(value).strip()]
            if ids:
                return ids
        if isinstance(candidate, str) and candidate.strip():
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                return [candidate.strip()]
            if isinstance(parsed, list):
                ids = [str(value).strip() for value in parsed if str(value).strip()]
                if ids:
                    return ids
    return []


def _case_expectation_count(case_expectations: list[dict[str, Any]]) -> int:
    total = 0
    for entry in case_expectations:
        nodes = entry.get("expectation_nodes") if isinstance(entry, dict) else None
        if isinstance(nodes, list):
            total += len(nodes)
    return total


def _parsed_expected_result_count(markdown: str) -> int:
    return sum(
        len(step["expectations"])
        for case in _parse_case_expected_result_structure(markdown)
        for step in case["steps"]
    )


def _expectation_ids_by_path(
    case_expectations: list[dict[str, Any]],
) -> dict[tuple[int, tuple[int, int]], str]:
    ids_by_path: dict[tuple[int, tuple[int, int]], str] = {}
    for entry in case_expectations:
        if not isinstance(entry, dict):
            continue
        raw_case_index = entry.get("case_index")
        if not isinstance(raw_case_index, int):
            continue
        nodes = entry.get("expectation_nodes")
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if not isinstance(node, dict):
                continue
            raw_path = node.get("path")
            node_id = node.get("id")
            if (
                isinstance(raw_path, list)
                and len(raw_path) == 2
                and all(isinstance(part, int) for part in raw_path)
                and isinstance(node_id, str)
                and node_id.strip()
            ):
                ids_by_path[(raw_case_index, (raw_path[0], raw_path[1]))] = node_id.strip()
    return ids_by_path


def _align_expectation_ids_to_tasks(
    case_md_text: str,
    midscene_content: list[Any],
    case_expectations: list[dict[str, Any]] | None,
    path_groups: list[dict[str, Any]] | None = None,
) -> list[list[str]]:
    if not case_expectations:
        return [[] for _ in midscene_content]

    parsed_count = _parsed_expected_result_count(case_md_text)
    saved_count = _case_expectation_count(case_expectations)
    if parsed_count != saved_count:
        raise SystemExit(
            "expectation node count mismatch: case.md has "
            f"{parsed_count} 预期结果 nodes but save_result.json has {saved_count}. "
            "Rerun prd2case-web Stage-4.1 to refresh save_result.json."
        )

    if path_groups is None:
        _, _, path_groups = _extract_case_execution_metadata(case_md_text)
    if len(path_groups) != len(midscene_content):
        raise SystemExit(
            "expectation task alignment mismatch: case.md-derived task groups "
            f"({len(path_groups)}) do not match markdown2midscene cases "
            f"({len(midscene_content)})."
        )

    ids_by_path = _expectation_ids_by_path(case_expectations)
    aligned: list[list[str]] = []
    for group in path_groups:
        case_index = group.get("case_index")
        paths = group.get("paths")
        if not isinstance(case_index, int) or not isinstance(paths, list):
            aligned.append([])
            continue
        ids: list[str] = []
        for path in paths:
            if not (
                isinstance(path, list)
                and len(path) == 2
                and all(isinstance(part, int) for part in path)
            ):
                continue
            node_id = ids_by_path.get((case_index, (path[0], path[1])))
            if not node_id:
                raise SystemExit(
                    "expectation path missing in save_result.json: "
                    f"case_index={case_index}, path={path}. "
                    "Rerun prd2case-web Stage-4.1 to refresh save_result.json."
                )
            ids.append(node_id)
        aligned.append(ids)
    return aligned


def _build_tasks(
    midscene_content: list[Any],
    creator: str,
    expectation_ids_per_item: list[list[str]] | None = None,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for index, item in enumerate(midscene_content, start=1):
        name = f"Case {index}"
        if isinstance(item, dict) and item.get("name"):
            name = str(item["name"]).strip()

        flow = _extract_flow(item)
        if not flow:
            continue

        task = {
            "title": name,
            "flow": flow,
            "itemKey": f"case_{len(tasks)}",
            "tags": ["ttat", "e2e", "newFeature"],
            "case_id": None,
            "case_name": name,
            "creator": creator,
            "name": name,
            "tag_names": ["ttat", "e2e", "newFeature"],
        }
        expectation_ids = _extract_expectation_ids(item)
        if (
            not expectation_ids
            and expectation_ids_per_item is not None
            and index - 1 < len(expectation_ids_per_item)
        ):
            expectation_ids = expectation_ids_per_item[index - 1]
        if expectation_ids:
            task["case_extra"] = {
                "expectation_ids": json.dumps(expectation_ids, ensure_ascii=False)
            }
        tasks.append(task)
    return tasks


def _call_markdown_to_midscene(markdown: str) -> list[Any]:
    response = requests.post(
        MARKDOWN_TO_MIDSCENE_URL,
        json={"case_content": markdown},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return _extract_midscene_content(response.text)



def _resolve_case_priority_filter(raw_value: str | None) -> str:
    normalized = (raw_value or "P0").strip().upper()
    if normalized == "ALL":
        return "all"
    if normalized not in SUPPORTED_CASE_PRIORITIES:
        raise SystemExit(
            "unsupported case priority filter: {0}. expected one of: P0, P1, P2, P3, all".format(
                raw_value
            )
        )
    return normalized


def _select_cases(
    midscene_content: list[Any],
    case_priorities: list[str | None],
    case_titles: list[str],
    *,
    case_priority_filter: str,
    parallel: list[list[Any]] | None = None,
) -> tuple[list[Any], list[str], tuple[list[Any], ...]]:
    if not (len(midscene_content) == len(case_priorities) == len(case_titles)):
        raise SystemExit(
            "case priority parsing mismatch: case.md headings, titles, and "
            "markdown2midscene cases are out of sync"
        )
    if parallel is not None:
        for idx, plist in enumerate(parallel):
            if len(plist) != len(midscene_content):
                raise SystemExit(
                    f"parallel[{idx}] length mismatch: expected "
                    f"{len(midscene_content)}, got {len(plist)}"
                )
    if case_priority_filter == "all":
        indices = list(range(len(midscene_content)))
    else:
        indices = [
            i for i, priority in enumerate(case_priorities)
            if priority == case_priority_filter
        ]
    if not indices:
        raise SystemExit(
            "no cases matched case priority filter {0}. try --case-priority all or choose another priority".format(
                case_priority_filter
            )
        )
    filtered_parallel: tuple[list[Any], ...] = tuple()
    if parallel is not None:
        filtered_parallel = tuple([plist[i] for i in indices] for plist in parallel)
    return (
        [midscene_content[i] for i in indices],
        [case_titles[i] for i in indices],
        filtered_parallel,
    )


def _resolve_bits_case_detail_url(env_values: dict[str, str], case_md: Path) -> str:
    env_url = (env_values.get("BITS_CASE_DETAIL_URL") or "").strip()
    if env_url:
        return env_url
    save_url = _load_save_result_bits_url(case_md)
    if save_url:
        return save_url.strip()
    try:
        return (_first_bits_case_detail_url_in_text(_read_text(case_md)) or "").strip()
    except OSError:
        return ""


def _build_bits_config(bits_case_url: str) -> dict[str, Any]:
    return {
        "url": bits_case_url,
        "useKnowledgeBase": False,
        "filter": "PGC",
        "caseFilter": "All",
        "tag": "e2e",
        "strict": True,
        "transformMode": True,
    }


def _build_execution_context(args: argparse.Namespace) -> dict[str, Any]:
    case_md = Path(args.case_md).expanduser().resolve()
    if not case_md.is_file():
        raise SystemExit(f"case.md not found: {case_md}")

    markdown = _read_text(case_md)
    env_file = _find_env_file(args.env_file, case_md)
    env_values = _parse_env_file(env_file)
    creator = args.creator or env_values.get("creator") or _default_creator()
    title = args.title or _guess_title(case_md, markdown)
    case_priority_filter = _resolve_case_priority_filter(
        getattr(args, "case_priority", None)
    )
    midscene_content = _call_markdown_to_midscene(markdown)
    parsed_priorities, parsed_titles, parsed_path_groups = _extract_case_execution_metadata(
        markdown
    )
    midscene_content, case_titles, filtered_parallel = _select_cases(
        midscene_content,
        parsed_priorities,
        parsed_titles,
        case_priority_filter=case_priority_filter,
        parallel=[parsed_path_groups],
    )
    filtered_path_groups = filtered_parallel[0] if filtered_parallel else []
    case_expectations = _load_save_result_case_expectations(case_md)
    expectation_ids_per_item = _align_expectation_ids_to_tasks(
        markdown,
        midscene_content,
        case_expectations,
        filtered_path_groups,
    )
    tasks = _build_tasks(midscene_content, creator, expectation_ids_per_item)
    if not tasks:
        raise SystemExit("no valid tasks generated from markdown2midscene response")
    if len(tasks) != len(case_titles):
        survived_titles: list[str] = []
        for item, ctitle in zip(midscene_content, case_titles):
            if _extract_flow(item):
                survived_titles.append(ctitle)
        case_titles = survived_titles
        if len(tasks) != len(case_titles):
            raise SystemExit(
                "internal error: case_titles failed to align with tasks "
                f"({len(case_titles)} titles vs {len(tasks)} tasks)"
            )

    for task, ctitle in zip(tasks, case_titles):
        task["case_title"] = ctitle

    metadata = {
        "case_md": str(case_md),
        "case_title": title,
        "creator": creator,
        "case_count": len(tasks),
        "env_file": str(env_file) if env_file else "",
        "case_priority_filter": case_priority_filter,
        "bits_config_url": _resolve_bits_case_detail_url(env_values, case_md),
    }
    return {
        "case_md": case_md,
        "markdown": markdown,
        "env_file": env_file,
        "env_values": env_values,
        "creator": creator,
        "title": title,
        "midscene_content": midscene_content,
        "tasks": tasks,
        "case_titles": case_titles,
        "metadata": metadata,
    }


def _build_case_group_payload(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any]]:
    context = _build_execution_context(args)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    case_group_name = f"{context['title']}_{timestamp}"
    exec_env = _build_exec_env(args, context["env_values"])

    payload = {
        "creator": context["creator"],
        "case_group_name": case_group_name,
        "web": {"bridgeMode": "false"},
        "tasks": context["tasks"],
        "extras": {"execEnv": exec_env, "extras": {}},
    }
    if context["metadata"]["bits_config_url"]:
        payload["extras"]["extras"]["bitsConfig"] = _build_bits_config(
            context["metadata"]["bits_config_url"]
        )
    metadata = dict(context["metadata"])
    metadata["case_group_name"] = case_group_name
    return payload, metadata


def _enforce_ttat_bits_archive_gate(payload: dict[str, Any], case_md: str) -> None:
    extras = payload.get("extras")
    nested_extras = extras.get("extras") if isinstance(extras, dict) else None
    bits_config = (
        nested_extras.get("bitsConfig") if isinstance(nested_extras, dict) else None
    )
    bits_url = bits_config.get("url") if isinstance(bits_config, dict) else None
    if isinstance(bits_url, str) and bits_url.strip():
        return

    tasks = payload.get("tasks")
    case_titles: list[str] = []
    if not isinstance(tasks, list):
        tasks = []
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            continue
        title = (
            str(task.get("case_title") or task.get("case_name") or task.get("name") or "")
            .strip()
            or f"task #{index}"
        )
        case_titles.append(title)

    case_text = "\n".join(f"- {title}" for title in case_titles[:10])
    if len(case_titles) > 10:
        case_text += f"\n- ... and {len(case_titles) - 10} more"
    if not case_text:
        case_text = "- <no task title available>"
    raise SystemExit(
        "Bits archive gate failed: TTAT create-group/edit-group/run requires "
        "extras.extras.bitsConfig.url to bind the case group to a Bits case.\n"
        f"case.md: {case_md}\n"
        f"Current task titles:\n{case_text}\n"
        "Run prd2case-web Stage-4.1 first, for example:\n"
        "  python3 $prd2case-web_SKILL/scripts/case_management.py save "
        "<case.md> --case-title \"<title>\" -o <case_dir>/save_result.json\n"
        "For an existing Bits case, rerun the same command with --case-id <existing id>. "
        "Alternatively set BITS_CASE_DETAIL_URL in the env file."
    )


def _enforce_expectation_ids_gate(payload: dict[str, Any], case_md: str) -> None:
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        tasks = []
    missing: list[str] = []
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            missing.append(f"task #{index}")
            continue
        case_extra = task.get("case_extra")
        expectation_ids = (
            case_extra.get("expectation_ids") if isinstance(case_extra, dict) else None
        )
        if not (isinstance(expectation_ids, str) and expectation_ids.strip()):
            title = (
                str(task.get("case_title") or task.get("case_name") or task.get("name") or "")
                .strip()
                or f"task #{index}"
            )
            missing.append(title)
    if not missing:
        return

    missing_text = "\n".join(f"- {title}" for title in missing[:10])
    if len(missing) > 10:
        missing_text += f"\n- ... and {len(missing) - 10} more"
    raise SystemExit(
        "Expectation IDs gate failed: TTAT tasks require "
        "tasks[].case_extra.expectation_ids bound to Bits 预期结果 nodes.\n"
        f"case.md: {case_md}\n"
        f"Missing task titles:\n{missing_text}\n"
        "Rerun prd2case-web Stage-4.1 to refresh save_result.json:\n"
        "  python3 $prd2case-web_SKILL/scripts/case_management.py save "
        "<case.md> --case-title \"<title>\" -o <case_dir>/save_result.json\n"
        "For an existing Bits case, rerun the same command with --case-id <existing id>."
    )


def _build_local_execution_bundle(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    context = _build_execution_context(args)
    execution_mode = _resolve_execution_mode(args, context["env_values"])
    if execution_mode != "local":
        raise SystemExit(
            "local execution requires EXECUTION_MODE=local or --execution-mode local"
        )

    local_runner = _resolve_local_runner(args, context["env_values"])
    local_case_concurrency = _resolve_local_case_concurrency(
        args, context["env_values"]
    )
    plan_path = _resolve_local_plan_path(
        context["case_md"],
        getattr(args, "plan_out", None) or getattr(args, "payload_out", None),
    )
    report_path = _resolve_report_path(
        context["case_md"], getattr(args, "report_out", None)
    )
    artifacts_root = _get_local_artifacts_root(context["case_md"])
    case_entries = []
    for index, task in enumerate(context["tasks"], start=1):
        artifacts = _build_local_case_artifacts(context["case_md"], task["name"], index)
        case_entries.append(
            {
                "name": task["name"],
                "flow": task["flow"],
                "artifacts": artifacts,
            }
        )
    auth_profile = _ensure_local_storage_state_ready(
        auth_profile=_build_local_auth_profile_config(context["env_values"]),
        case_md=context["case_md"],
        case_entries=case_entries,
    )
    browser_headers = _build_local_browser_headers(args, context["env_values"])
    bundle = {
        "execution_mode": execution_mode,
        "local_runner": local_runner,
        "runtime": {
            "playwright_cli": {
                "binary": "playwright-cli",
                "install_command": (
                    "npx @tiktok-fe/skills add microsoft/playwright-cli "
                    "--source github --skill playwright-cli"
                ),
                "session_arg_template": "-s={case_id}",
            }
        },
        "runner_mode": "case_parallel",
        "case_concurrency": local_case_concurrency,
        "case_isolation": "session_per_case",
        "case_md": str(context["case_md"]),
        "case_title": context["title"],
        "creator": context["creator"],
        "env_file": str(context["env_file"]) if context["env_file"] else "",
        "report_file": str(report_path),
        "artifacts_root": str(artifacts_root),
        "case_count": len(context["tasks"]),
        "case_priority_filter": context["metadata"]["case_priority_filter"],
        "env": {key: value for key, value in context["env_values"].items() if value},
        "browser_headers": browser_headers,
        "browser_header_setup": _build_local_browser_header_setup(browser_headers),
        "auth_profile": auth_profile,
        "cases": case_entries,
        "midscene_content": context["midscene_content"],
    }
    metadata = dict(context["metadata"])
    metadata["case_priority_filter"] = bundle["case_priority_filter"]
    metadata["execution_mode"] = execution_mode
    metadata["local_runner"] = local_runner
    metadata["runtime"] = dict(bundle["runtime"])
    metadata["runner_mode"] = bundle["runner_mode"]
    metadata["case_concurrency"] = bundle["case_concurrency"]
    metadata["case_isolation"] = bundle["case_isolation"]
    metadata["artifacts_root"] = str(artifacts_root)
    metadata["browser_headers"] = dict(bundle["browser_headers"])
    metadata["browser_header_setup"] = dict(bundle["browser_header_setup"])
    metadata["auth_profile"] = dict(bundle["auth_profile"])
    return bundle, metadata, plan_path, report_path


def _post_case_group(
    url: str,
    payload: dict[str, Any],
    *,
    action: str,
    require_response_id: bool,
) -> tuple[dict[str, Any], Any]:
    response = requests.post(
        url,
        headers=_json_headers(),
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_payload = response.json()

    extracted_id: Any = None
    if isinstance(response_payload, dict):
        data = response_payload.get("data")
        if isinstance(data, dict):
            extracted_id = data.get("case_group_id") or data.get("id")
        extracted_id = extracted_id or response_payload.get("id")
        status_code = response_payload.get("status_code")
        if status_code not in (None, 0, "0"):
            if require_response_id and extracted_id:
                pass
            else:
                raise SystemExit(json.dumps(response_payload, ensure_ascii=False, indent=2))

    if require_response_id and not extracted_id:
        raise SystemExit(
            f"{action} did not return case_group_id: {json.dumps(response_payload, ensure_ascii=False)}"
        )

    return response_payload, extracted_id


def _create_case_group(payload: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    return _post_case_group(
        CREATE_CASE_GROUP_URL,
        payload,
        action="create_case_group",
        require_response_id=True,
    )


def _edit_case_group(
    payload: dict[str, Any], case_group_id: Any
) -> tuple[dict[str, Any], Any]:
    normalized_id: Any = case_group_id
    if isinstance(case_group_id, str) and case_group_id.isdigit():
        normalized_id = int(case_group_id)

    edit_payload = dict(payload)
    edit_payload["case_group_id"] = normalized_id
    response_payload, _ = _post_case_group(
        EDIT_CASE_GROUP_URL,
        edit_payload,
        action="edit_with_cases",
        require_response_id=False,
    )
    return response_payload, normalized_id


def _get_dynamic_token(token_name: str) -> str:
    response = requests.get(
        GET_DYNAMIC_TOKEN_URL,
        params={"name": token_name},
        headers={"X-Custom-Token": X_CUSTOM_TOKEN},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise SystemExit("unexpected token response")
    token = payload.get("data")
    if not token:
        raise SystemExit(
            f"failed to get dynamic token: {json.dumps(payload, ensure_ascii=False)}"
        )
    return str(token)


def _create_task(
    case_group_id: Any, creator: str, task_name: str, token_name: str | None = None
) -> tuple[dict[str, Any], Any]:
    dynamic_token = _get_dynamic_token(token_name or creator)
    payload = {
        "space_id": 0,
        "creator": creator,
        "case_group_id": case_group_id,
        "task_name": task_name,
        "template_id": DEFAULT_TEMPLATE_ID,
        "biz": DEFAULT_BIZ,
        "exe_platform": DEFAULT_EXE_PLATFORM,
    }
    response = requests.post(
        CREATE_TASK_URL,
        headers=_json_headers(dynamic_token),
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    response_payload = response.json()
    task_id = (
        response_payload.get("task_id") if isinstance(response_payload, dict) else None
    )
    if not task_id:
        raise SystemExit(
            f"failed to create task: {json.dumps(response_payload, ensure_ascii=False)}"
        )
    return response_payload, task_id


def cmd_list_platforms(_: argparse.Namespace) -> int:
    platforms = _fetch_registered_platforms()
    result = {
        "count": len(platforms),
        "platforms": sorted(
            platforms,
            key=lambda item: (
                str(item.get("nameZh") or "").lower(),
                str(item.get("platform") or "").lower(),
                str(item.get("domain") or "").lower(),
            ),
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_platform_detail(args: argparse.Namespace) -> int:
    detail_payload = _fetch_platform_detail(args.platform, args.domain or "")
    details = detail_payload["variables"]
    result = {
        "platform": detail_payload["platform"],
        "domain": detail_payload["domain"],
        "variable_count": len(details),
        "variables": details,
        "default_keys": [item["key"] for item in details if item["useDefault"]],
        "required_keys": [item["key"] for item in details if item["needsInput"]],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    payload, metadata = _build_case_group_payload(args)
    out_path = Path(args.out).expanduser().resolve() if args.out else None
    if out_path:
        _write_json(out_path, payload)
        print(out_path)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


def cmd_init_env(args: argparse.Namespace) -> int:
    """Initialize .env file next to case.md from template."""
    case_md = Path(args.case_md).expanduser().resolve()
    if not case_md.is_file():
        raise SystemExit(f"case.md not found: {case_md}")

    env_path = _get_default_env_path(case_md)
    if env_path.is_file():
        print(f"env_file: {env_path}")
        print("status: already_exists")
        return 0

    template_path = _get_env_template_path()
    if template_path.is_file():
        content = _read_text(template_path)
    else:
        content = DEFAULT_ENV_TEMPLATE

    task_md = _find_task_md(case_md)
    task_defaults = _extract_task_defaults(task_md)
    if task_defaults:
        content = _apply_env_defaults(content, task_defaults)

    # Replace empty creator with git user.email
    try:
        git_creator = _default_creator()
        content = content.replace("creator=", f"creator={git_creator}")
    except SystemExit:
        pass  # Keep empty creator if git user.email not configured

    _write_text(env_path, content)
    print(f"env_file: {env_path}")
    if task_md is not None:
        print(f"task_md: {task_md}")
    if task_defaults:
        print(f"task_defaults: {json.dumps(task_defaults, ensure_ascii=False)}")
    print("status: created")
    return 0


def cmd_show_env(args: argparse.Namespace) -> int:
    """Read and output current env config for user confirmation."""
    case_md = Path(args.case_md).expanduser().resolve()
    if not case_md.is_file():
        raise SystemExit(f"case.md not found: {case_md}")

    env_file = _find_env_file(args.env_file, case_md)

    # Get git user.email as fallback for creator
    git_creator = _default_creator() if not args.creator else None

    if not env_file:
        config = {
            "creator": args.creator or git_creator or "",
            "EXECUTION_MODE": DEFAULT_EXECUTION_MODE,
            "LOCAL_RUNNER": DEFAULT_LOCAL_RUNNER,
            "LOCAL_CASE_CONCURRENCY": str(DEFAULT_LOCAL_CASE_CONCURRENCY),
            "STORAGE_STATE_MODE": "chrome-profile",
            "CHROME_USER_DATA_DIR": "",
            "CHROME_PROFILE_NAME": "",
        }
        result = {
            "env_file": "",
            "status": "not_found",
            "config": config,
            "git_creator": git_creator,
            "default_env_path": str(_get_default_env_path(case_md)),
        }
        if _resolve_execution_mode(args, {}) == "local":
            result["local_browser_headers"] = _build_local_browser_headers(args, {})
            result["local_auth_profile"] = _build_local_auth_profile_config({})
            result["local_case_concurrency"] = _resolve_local_case_concurrency(
                args, {}
            )
    else:
        env_values = _parse_env_file(env_file)
        env_creator = env_values.get("creator", "")

        config = {
            "creator": args.creator or env_creator or git_creator or "",
            "EXECUTION_MODE": DEFAULT_EXECUTION_MODE,
            "LOCAL_RUNNER": DEFAULT_LOCAL_RUNNER,
            "LOCAL_CASE_CONCURRENCY": str(DEFAULT_LOCAL_CASE_CONCURRENCY),
            "STORAGE_STATE_MODE": "chrome-profile",
            "CHROME_USER_DATA_DIR": "",
            "CHROME_PROFILE_NAME": "",
        }
        for key, value in env_values.items():
            if key != "creator":
                config[key] = value

        result: dict[str, Any] = {
            "env_file": str(env_file),
            "status": "found",
            "config": config,
            "env_creator": env_creator,
            "git_creator": git_creator,
        }
        if _resolve_execution_mode(args, env_values) == "local":
            result["local_browser_headers"] = _build_local_browser_headers(
                args, env_values
            )
            result["local_auth_profile"] = _build_local_auth_profile_config(env_values)
            result["local_case_concurrency"] = _resolve_local_case_concurrency(
                args, env_values
            )

    print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_export_storage_state(args: argparse.Namespace) -> int:
    env_values: dict[str, str] = {}
    if getattr(args, "case_md", None):
        case_md = Path(args.case_md).expanduser().resolve()
        env_values = _parse_env_file(_find_env_file(args.env_file, case_md))
    elif getattr(args, "env_file", None):
        env_values = _parse_env_file(Path(args.env_file).expanduser().resolve())

    if args.user_data_dir:
        env_values["CHROME_USER_DATA_DIR"] = args.user_data_dir
    if args.profile_name:
        env_values["CHROME_PROFILE_NAME"] = args.profile_name
    if args.storage_state_mode:
        env_values["STORAGE_STATE_MODE"] = args.storage_state_mode

    auth_profile = _build_local_auth_profile_config(env_values)
    user_data_dir = Path(str(auth_profile["chrome_user_data_dir"])).expanduser().resolve()
    target_urls = [str(url) for url in (args.target_url or []) if str(url).strip()]
    target_domains = [str(domain) for domain in (args.target_domain or []) if str(domain).strip()]
    target_domains = target_domains or _target_domains_from_urls(target_urls)

    if args.list_profiles:
        result = {
            "chrome_user_data_dir": str(user_data_dir),
            "target_domains": target_domains,
            "profiles": _discover_chrome_profiles(user_data_dir, target_domains),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    profile_name = str(auth_profile.get("chrome_profile_name") or "").strip()
    if not profile_name:
        candidates = _discover_chrome_profiles(user_data_dir, target_domains)
        raise SystemExit(
            "CHROME_PROFILE_NAME/--profile-name is required. "
            "Run with --list-profiles and choose the profile that actually has "
            "target-domain login state. "
            f"candidates={json.dumps(candidates, ensure_ascii=False)}"
        )

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else Path.cwd() / ".webe2e" / "storage_state.json"
    )
    summary = _export_chrome_storage_state(
        user_data_dir=user_data_dir,
        profile_name=profile_name,
        output_path=output,
        target_urls=target_urls,
        target_domains=target_domains,
        headless=bool(args.headless),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_create_group(args: argparse.Namespace) -> int:
    payload, metadata = _build_case_group_payload(args)
    _enforce_ttat_bits_archive_gate(payload, metadata["case_md"])
    _enforce_expectation_ids_gate(payload, metadata["case_md"])
    if args.payload_out:
        _write_json(Path(args.payload_out).expanduser().resolve(), payload)

    existing_id = getattr(args, "case_group_id", None)
    if existing_id:
        _, case_group_id = _edit_case_group(payload, existing_id)
        action = "updated"
    else:
        _, case_group_id = _create_case_group(payload)
        action = "created"

    print(f"case_group_name: {metadata['case_group_name']}")
    print(f"case_count: {metadata['case_count']}")
    print(f"case_priority_filter: {metadata['case_priority_filter']}")
    if metadata["env_file"]:
        print(f"env_file: {metadata['env_file']}")
    print(f"case_group_id: {case_group_id}")
    print(f"case_group_action: {action}")
    return 0


def cmd_edit_group(args: argparse.Namespace) -> int:
    if not getattr(args, "case_group_id", None):
        raise SystemExit("--case-group-id is required for edit-group")

    payload, metadata = _build_case_group_payload(args)
    _enforce_ttat_bits_archive_gate(payload, metadata["case_md"])
    _enforce_expectation_ids_gate(payload, metadata["case_md"])
    if args.payload_out:
        _write_json(Path(args.payload_out).expanduser().resolve(), payload)

    _, case_group_id = _edit_case_group(payload, args.case_group_id)

    print(f"case_group_name: {metadata['case_group_name']}")
    print(f"case_count: {metadata['case_count']}")
    print(f"case_priority_filter: {metadata['case_priority_filter']}")
    if metadata["env_file"]:
        print(f"env_file: {metadata['env_file']}")
    print(f"case_group_id: {case_group_id}")
    print("case_group_action: updated")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    case_md = Path(args.case_md).expanduser().resolve()
    env_file = _find_env_file(args.env_file, case_md)
    env_values = _parse_env_file(env_file)
    execution_mode = _resolve_execution_mode(args, env_values)
    _require_env_confirmation(args, execution_mode, env_file)
    if execution_mode == "local":
        return cmd_run_local(args)

    payload, metadata = _build_case_group_payload(args)
    _enforce_ttat_bits_archive_gate(payload, metadata["case_md"])
    _enforce_expectation_ids_gate(payload, metadata["case_md"])
    if args.payload_out:
        _write_json(Path(args.payload_out).expanduser().resolve(), payload)

    existing_id = getattr(args, "case_group_id", None)
    if existing_id:
        _, case_group_id = _edit_case_group(payload, existing_id)
        case_group_action = "updated"
    else:
        _, case_group_id = _create_case_group(payload)
        case_group_action = "created"
    metadata["case_group_action"] = case_group_action
    task_name = args.task_name or metadata["case_group_name"]
    _, task_id = _create_task(
        case_group_id, metadata["creator"], task_name, args.token_name
    )
    report_path = _resolve_report_path(Path(metadata["case_md"]), args.report_out)
    _write_test_report(
        report_path=report_path,
        payload=payload,
        metadata=metadata,
        case_group_id=case_group_id,
        task_name=task_name,
        task_id=task_id,
    )

    print(f"case_group_name: {metadata['case_group_name']}")
    print(f"case_count: {metadata['case_count']}")
    print(f"case_priority_filter: {metadata['case_priority_filter']}")
    if metadata["env_file"]:
        print(f"env_file: {metadata['env_file']}")
    print(f"case_group_id: {case_group_id}")
    print(f"case_group_action: {case_group_action}")
    print(f"task_name: {task_name}")
    print(f"task_id: {task_id}")
    print(f"task_url: {TASK_LINK_TEMPLATE.format(task_id=task_id)}")
    print(f"report_file: {report_path}")
    return 0


def _render_local_test_report(
    report_path: Path,
    metadata: dict[str, Any],
    bundle: dict[str, Any],
    plan_path: Path,
) -> str:
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    case_rows = [
        "| 序号 | Case 名称 | 步骤数 | 本地产物目录 |",
        "|------|-----------|--------|--------------|",
    ]
    for index, item in enumerate(bundle.get("cases") or [], start=1):
        artifacts = item.get("artifacts") or {}
        case_rows.append(
            "| {index} | {case_name} | {step_count} | `{case_dir}` |".format(
                index=index,
                case_name=item.get("name") or f"Case {index}",
                step_count=len(item.get("flow") or []),
                case_dir=artifacts.get("case_dir") or "-",
            )
        )

    return "\n".join(
        [
            "# Web E2E Test Report",
            "",
            "## 执行概览",
            "",
            "| 项目 | 值 |",
            "|------|-----|",
            f"| 更新时间 | {updated_at} |",
            f"| case.md | `{metadata['case_md']}` |",
            f"| report_file | `{report_path}` |",
            f"| env_file | `{metadata['env_file'] or '-'}` |",
            f"| creator | {metadata['creator']} |",
            f"| case_group_name | - |",
            f"| case_group_id | - |",
            f"| case_count | {metadata['case_count']} |",
            f"| task_name | - |",
            f"| task_id | - |",
            f"| task_url | `{metadata['artifacts_root']}` |",
            f"| case_priority_filter | {metadata['case_priority_filter']} |",
            f"| execution_mode | {metadata['execution_mode']} |",
            f"| local_runner | {metadata['local_runner']} |",
            f"| runtime.playwright_cli | `{json.dumps(metadata['runtime'].get('playwright_cli', {}), ensure_ascii=False)}` |",
            f"| runner_mode | {metadata['runner_mode']} |",
            f"| case_concurrency | {metadata['case_concurrency']} |",
            f"| case_isolation | {metadata['case_isolation']} |",
            f"| plan_file | `{plan_path}` |",
            f"| browser_headers | `{json.dumps(metadata['browser_headers'], ensure_ascii=False) if metadata['browser_headers'] else '-'}` |",
            f"| browser_header_setup | `{json.dumps(metadata['browser_header_setup'], ensure_ascii=False) if metadata['browser_header_setup'] else '-'}` |",
            f"| auth_profile | `{json.dumps(metadata['auth_profile'], ensure_ascii=False)}` |",
            "",
            "## 任务状态",
            "",
            "- 当前状态：已生成本地执行计划，等待通过 `playwright-cli` 执行。",
            "- 本地模式不会创建 TTAT case group 或 task_id。",
            f"- 本地模式由单一执行 agent 编排，再由 `playwright-cli` / runner 按 case 级并发执行，最大并发度为 `{metadata['case_concurrency']}`；避免多个 subagent 并发写报告、注册 mock 或归档共享产物。",
            "- 单个 case 内 flow 仍需保持顺序。",
            "- 每个 case 必须使用独立的 `playwright-cli -s=<caseId>` session 执行，避免共享登录态和页面状态互相污染。",
            "- playwright-cli 必须将截图、trace、录像、控制台日志等过程产物统一整理到 `test_result/`。",
            "- 每个 case 完成后，必须立刻把该 case 的过程产物落到对应的 `test_result/<case目录>/`；不允许使用无法归属到 case 目录的批量执行方式。",
            "- 执行时必须使用 `playwright-cli`，禁止回退到旧版 `playwright` runner。",
            "- 每个 case session `open` 后、首次 `goto` 前，必须按 `browser_header_setup` 执行 `playwright-cli -s=<caseId> run-code ...page.setExtraHTTPHeaders(...)`，使 `browser_headers` 中列出的请求头进入后续请求。",
            "- 本地登录态默认来自 Chrome profile；如果 `CHROME_PROFILE_NAME` 为空，必须先枚举并确认实际登录过目标域名的 profile，禁止直接假设 `Default`。",
            "- 导出运行中的 Chrome 登录态时，不能只读取 `Cookies` 主库；必须连同 `Cookies-wal` / `Cookies-shm` 处理，或用克隆 profile 让 Chrome/Playwright 生成 storage state。",
            "- 每个 case 至少要落地入口截图 `step_001_*.png` 和结束截图 `final.png`；失败/抛错/超时路径还需在 close 前补 `failure.png`。",
            "- 初始化阶段只预留每个 case 的产物目录；具体截图、trace、录像、日志路径必须在执行后再回填。",
            "- 执行完成后，需要将每个 case 的结果与关键证据补充回本报告。",
            "",
            "## 用例清单",
            "",
            "\n".join(case_rows),
            "",
        ]
    )


def cmd_run_local(args: argparse.Namespace) -> int:
    case_md = Path(args.case_md).expanduser().resolve()
    env_file = _find_env_file(args.env_file, case_md)
    env_values = _parse_env_file(env_file)
    execution_mode = _resolve_execution_mode(args, env_values)
    _require_env_confirmation(args, execution_mode, env_file)
    bundle, metadata, plan_path, report_path = _build_local_execution_bundle(args)
    Path(metadata["artifacts_root"]).mkdir(parents=True, exist_ok=True)
    for item in bundle.get("cases") or []:
        artifacts = item.get("artifacts") or {}
        case_dir = artifacts.get("case_dir")
        if case_dir:
            Path(case_dir).mkdir(parents=True, exist_ok=True)
    _write_json(plan_path, bundle)
    _write_text(
        report_path,
        _render_local_test_report(
            report_path=report_path,
            metadata=metadata,
            bundle=bundle,
            plan_path=plan_path,
        ),
    )

    print("execution_mode: local")
    print(f"local_runner: {metadata['local_runner']}")
    print(
        "runtime.playwright_cli: "
        + json.dumps(metadata["runtime"].get("playwright_cli", {}), ensure_ascii=False)
    )
    print(f"runner_mode: {metadata['runner_mode']}")
    print(f"case_concurrency: {metadata['case_concurrency']}")
    print(f"case_count: {metadata['case_count']}")
    print(f"case_priority_filter: {metadata['case_priority_filter']}")
    if metadata["env_file"]:
        print(f"env_file: {metadata['env_file']}")
    print(f"task_url: {metadata['artifacts_root']}")
    print(f"artifacts_root: {metadata['artifacts_root']}")
    print(f"plan_file: {plan_path}")
    print(f"report_file: {report_path}")
    return 0


def cmd_gen_yaml(args: argparse.Namespace) -> int:
    """Atomic capability: call markdown2midscene and dump per-case midscene YAML."""
    context = _build_execution_context(args)
    case_md = context["case_md"]
    out_dir = _get_yaml_scripts_dir(
        case_md, getattr(args, "out_dir", None)
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    default_url = ""
    if getattr(args, "default_url", None):
        default_url = str(args.default_url).strip()

    midscene_items = context.get("midscene_content") or []
    tasks = context.get("tasks") or []

    written: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    used_filenames: set[str] = set()

    for index in range(1, max(len(midscene_items), len(tasks)) + 1):
        raw_item = (
            midscene_items[index - 1] if index - 1 < len(midscene_items) else None
        )
        task = tasks[index - 1] if index - 1 < len(tasks) else {}
        name = ""
        if isinstance(raw_item, dict) and raw_item.get("name"):
            name = str(raw_item["name"]).strip()
        if not name:
            name = task.get("name") or f"Case {index}"

        flow: list[dict[str, Any]] = []
        if raw_item is not None:
            flow = _extract_midscene_flow_preserving(raw_item)
        if not flow:
            flow = list(task.get("flow") or [])

        web_url, remaining_flow = _split_flow_into_url_and_steps(flow)
        if not web_url:
            web_url = default_url

        filename = _build_yaml_filename(name, index)
        if filename in used_filenames:
            filename = f"{Path(filename).stem}-{index}.yaml"
        used_filenames.add(filename)
        out_path = out_dir / filename

        if not web_url:
            skipped.append(
                {
                    "name": name,
                    "path": str(out_path),
                    "reason": "no url in flow and --default-url not provided",
                }
            )
            continue

        document = _render_midscene_yaml_document(
            web_url=web_url, task_name=name, flow=remaining_flow
        )
        _write_text(out_path, document)
        written.append(
            {
                "name": name,
                "path": str(out_path),
                "web_url": web_url,
                "step_count": len(remaining_flow),
            }
        )

    result = {
        "case_md": str(case_md),
        "out_dir": str(out_dir),
        "case_count": len(context["tasks"]),
        "written_count": len(written),
        "skipped_count": len(skipped),
        "case_priority_filter": context["metadata"]["case_priority_filter"],
        "files": written,
    }
    if skipped:
        result["skipped"] = skipped
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_query_task(args: argparse.Namespace) -> int:
    task_id: Any = args.task_id
    if isinstance(task_id, str) and task_id.isdigit():
        task_id = int(task_id)
    task_status_payload = _query_task_execution(task_id)
    result = {
        "task_id": task_id,
        "task_name": _extract_task_name(task_status_payload),
        "execute_status": _extract_task_execute_status(task_status_payload),
        "task_counts": _extract_task_counts(task_status_payload),
        "status_line": _format_task_status(task_status_payload),
        "done": _task_polling_succeeded(task_status_payload),
        "response": task_status_payload,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_analyze_task(args: argparse.Namespace) -> int:
    task_id: Any = args.task_id
    if isinstance(task_id, str) and task_id.isdigit():
        task_id = int(task_id)

    report_path = _resolve_analysis_report_path(args.case_md, args.report_out)
    task_list_payload = _query_task_list(task_id)
    task_status_payload = _query_task_execution(task_id)
    task_name = _extract_task_name(task_list_payload) or _extract_task_name(
        task_status_payload
    )

    failed_cases: list[dict[str, Any]] = []
    analyzed_cases: list[dict[str, Any]] = []
    resumed_completed_count = 0
    if _can_start_analysis(task_status_payload):
        failed_cases = _query_failed_cases(task_id)
    overview_section = _render_analysis_overview_section(
        report_path=report_path,
        task_id=task_id,
        task_name=task_name,
        task_status_payload=task_status_payload,
        failed_cases=failed_cases,
        case_md_arg=args.case_md,
    )

    if _can_start_analysis(task_status_payload) and args.detail:
        analyzed_cases = _extract_existing_analyzed_cases(report_path)
        failed_case_ids = {
            str(item.get("case_execution_id") or "") for item in failed_cases
        }
        analyzed_cases = [
            item
            for item in analyzed_cases
            if str(item.get("case_execution_id") or "") in failed_case_ids
        ]
        completed_case_ids = {
            str(item.get("case_execution_id") or "") for item in analyzed_cases
        }
        resumed_completed_count = len(completed_case_ids)
        pending_failed_cases = [
            item
            for item in failed_cases
            if str(item.get("case_execution_id") or "") not in completed_case_ids
        ]
        detail_section = _render_analysis_detail_section(
            analyzed_cases,
            _can_start_analysis(task_status_payload),
            total_failed_case_count=len(failed_cases),
            include_meta_comments=True,
        )
        _write_analysis_sections_to_report(
            report_path=report_path,
            overview_section=overview_section,
            detail_section=detail_section,
        )
        for case_item in pending_failed_cases:
            analyzed_cases.append(
                _analyze_failed_case(task_id, case_item, report_path.parent)
            )
            detail_section = _render_analysis_detail_section(
                analyzed_cases,
                _can_start_analysis(task_status_payload),
                total_failed_case_count=len(failed_cases),
                include_meta_comments=True,
            )
            _write_analysis_sections_to_report(
                report_path=report_path,
                overview_section=overview_section,
                detail_section=detail_section,
            )
    detail_section = None
    report_detail_section = None
    if args.detail:
        detail_section = _render_analysis_detail_section(
            analyzed_cases,
            _can_start_analysis(task_status_payload),
            total_failed_case_count=len(failed_cases),
            include_meta_comments=False,
        )
        report_detail_section = _render_analysis_detail_section(
            analyzed_cases,
            _can_start_analysis(task_status_payload),
            total_failed_case_count=len(failed_cases),
            include_meta_comments=True,
        )

    _write_analysis_sections_to_report(
        report_path=report_path,
        overview_section=overview_section,
        detail_section=report_detail_section,
    )

    estimated_detail_seconds = _estimate_detail_analysis_seconds(len(failed_cases))

    result = {
        "task_id": task_id,
        "task_name": task_name,
        "mode": "detail" if args.detail else "overview",
        "report_file": str(report_path),
        "execute_status": _extract_task_execute_status(task_status_payload),
        "task_counts": _extract_task_counts(task_status_payload),
        "status_line": _format_task_status(task_status_payload),
        "done": _can_start_analysis(task_status_payload),
        "failed_case_count": len(failed_cases),
        "estimated_detail_seconds": estimated_detail_seconds,
        "estimated_detail_duration": _format_duration(estimated_detail_seconds)
        if estimated_detail_seconds
        else "-",
        "detail_command": _build_detail_command(task_id, args.case_md),
        "resumed_completed_case_count": resumed_completed_count,
        "remaining_detail_case_count": max(len(failed_cases) - len(analyzed_cases), 0),
        "detail_resume_detected": bool(
            args.detail
            and resumed_completed_count > 0
            and resumed_completed_count < len(failed_cases)
        ),
        "needs_user_confirmation": bool(
            _can_start_analysis(task_status_payload)
            and len(failed_cases) > 0
            and not args.detail
        ),
        "failed_cases": failed_cases,
        "analyzed_cases": analyzed_cases,
    }

    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = overview_section
        if detail_section is not None:
            output = output.rstrip() + "\n\n" + detail_section

    print(output)
    return 0


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--case-md", required=True)
    parser.add_argument("--title")
    parser.add_argument("--creator")
    parser.add_argument("--env-file")
    parser.add_argument(
        "--case-priority",
        default="P0",
        help="Case priority filter: P0, P1, P2, P3, or all. Defaults to P0.",
    )
    parser.add_argument("--execution-mode")
    parser.add_argument("--local-runner")
    parser.add_argument("--local-case-concurrency", type=int)
    parser.add_argument("--platform")
    parser.add_argument("--run-env")
    parser.add_argument("--test-idc")
    parser.add_argument("--boe-swimlane")
    parser.add_argument("--ppe-swimlane")


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--payload-out")
    parser.add_argument("--plan-out")
    parser.add_argument("--task-name")
    parser.add_argument("--token-name")
    parser.add_argument("--report-out")
    parser.add_argument("--case-group-id")
    parser.add_argument(
        "--confirmed-env",
        action="store_true",
        help="Explicitly confirm that show-env has been reviewed and user confirmation was received",
    )


def _add_local_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--payload-out")
    parser.add_argument("--plan-out")
    parser.add_argument("--report-out")
    parser.add_argument("--case-group-id")
    parser.add_argument(
        "--confirmed-env",
        action="store_true",
        help="Explicitly confirm that show-env has been reviewed and user confirmation was received",
    )
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create TTAT web e2e tasks or prepare local execution from case.md"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_env_parser = subparsers.add_parser(
        "init-env", help="Initialize .env file next to case.md"
    )
    init_env_parser.add_argument("--case-md", required=True)
    init_env_parser.set_defaults(func=cmd_init_env)

    list_platforms_parser = subparsers.add_parser(
        "list-platforms", help="List registered Web E2E platforms"
    )
    list_platforms_parser.set_defaults(func=cmd_list_platforms)

    platform_detail_parser = subparsers.add_parser(
        "platform-detail", help="Show env vars required by a platform"
    )
    platform_detail_parser.add_argument("--platform", required=True)
    platform_detail_parser.add_argument("--domain")
    platform_detail_parser.set_defaults(func=cmd_platform_detail)

    show_env_parser = subparsers.add_parser(
        "show-env", help="Show current env config for confirmation"
    )
    show_env_parser.add_argument("--case-md", required=True)
    show_env_parser.add_argument("--env-file")
    show_env_parser.add_argument("--creator")
    show_env_parser.set_defaults(func=cmd_show_env)

    export_storage_parser = subparsers.add_parser(
        "export-storage-state",
        help="Export Playwright storageState from a selected Chrome profile",
    )
    export_storage_parser.add_argument("--case-md")
    export_storage_parser.add_argument("--env-file")
    export_storage_parser.add_argument("--user-data-dir")
    export_storage_parser.add_argument("--profile-name")
    export_storage_parser.add_argument("--storage-state-mode")
    export_storage_parser.add_argument("--target-url", action="append")
    export_storage_parser.add_argument("--target-domain", action="append")
    export_storage_parser.add_argument("--output")
    export_storage_parser.add_argument("--list-profiles", action="store_true")
    export_storage_parser.add_argument("--headless", action="store_true")
    export_storage_parser.set_defaults(func=cmd_export_storage_state)

    prepare_parser = subparsers.add_parser(
        "prepare", help="Build create_case_group payload from case.md"
    )
    _add_common_arguments(prepare_parser)
    prepare_parser.add_argument("--out")
    prepare_parser.set_defaults(func=cmd_prepare)

    create_parser = subparsers.add_parser(
        "create-group", help="Create case group from case.md"
    )
    _add_common_arguments(create_parser)
    create_parser.add_argument("--payload-out")
    create_parser.add_argument("--case-group-id")
    create_parser.set_defaults(func=cmd_create_group)

    edit_parser = subparsers.add_parser(
        "edit-group", help="Update an existing case group from case.md"
    )
    _add_common_arguments(edit_parser)
    edit_parser.add_argument("--payload-out")
    edit_parser.add_argument("--case-group-id", required=True)
    edit_parser.set_defaults(func=cmd_edit_group)

    run_parser = subparsers.add_parser(
        "run", help="Create case group and trigger TTAT task"
    )
    _add_common_arguments(run_parser)
    _add_run_arguments(run_parser)
    run_parser.set_defaults(func=cmd_run)

    run_local_parser = subparsers.add_parser(
        "run-local", help="Prepare local execution bundle and initialize report"
    )
    _add_common_arguments(run_local_parser)
    _add_local_run_arguments(run_local_parser)
    run_local_parser.set_defaults(func=cmd_run_local)

    gen_yaml_parser = subparsers.add_parser(
        "gen-yaml",
        help=(
            "Call markdown2midscene and write per-case midscene YAML scripts to "
            "test/yaml-scripts/ (atomic capability, user-invoked only)."
        ),
    )
    _add_common_arguments(gen_yaml_parser)
    gen_yaml_parser.add_argument(
        "--out-dir",
        help=(
            "Output directory for per-case YAML files. Defaults to the "
            "'yaml-scripts' directory next to case.md."
        ),
    )
    gen_yaml_parser.add_argument(
        "--default-url",
        help=(
            "Fallback web.url when the parsed case flow does not contain a URL "
            "step. If omitted, such cases are skipped with a warning."
        ),
    )
    gen_yaml_parser.set_defaults(func=cmd_gen_yaml)

    query_task_parser = subparsers.add_parser(
        "query-task", help="Query TTAT task status by task_id"
    )
    query_task_parser.add_argument("--task-id", required=True)
    query_task_parser.set_defaults(func=cmd_query_task)

    analyze_task_parser = subparsers.add_parser(
        "analyze-task", help="Analyze failed cases by task_id"
    )
    analyze_task_parser.add_argument("--task-id", required=True)
    analyze_task_parser.add_argument("--case-md")
    analyze_task_parser.add_argument("--detail", action="store_true")
    analyze_task_parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown"
    )
    analyze_task_parser.add_argument("--report-out")
    analyze_task_parser.set_defaults(func=cmd_analyze_task)

    args = parser.parse_args()
    try:
        return int(args.func(args))
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else str(exc)
        print(body, file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
