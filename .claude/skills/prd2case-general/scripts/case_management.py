#!/usr/bin/env python3
"""
Read/write test cases from local files and Bits APIs.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from typing import Any, Dict, Union


HOST = "https://q9q0hn98.fn.bytedance.net/"
# HOST = "http://127.0.0.1:8001/" 
TIMEOUT = 900
FETCH_URI = "/case2step/fetch_bits_case"
SAVE_URI = "/case2step/save_case_to_bits"


JSONLike = Union[Dict[str, Any], list, str, int, float, bool, None]
BITS_CASE_DETAIL_URL = "https://bits.bytedance.net/devops/{devops_id}/quality/case/caseDetail/{case_id}"
CASE_HEADING_PATTERN = re.compile(r"^####\s+(?P<title>.+)$", re.MULTILINE)
CASE_NODE_HEADING_PATTERN = re.compile(
    r"^#{5,}\s+\*\*(?P<label>操作步骤|预期结果)\*\*\s*(?P<inline>.*)$",
    re.MULTILINE,
)


def _call_api(uri: str, params: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.dumps(params, ensure_ascii=False).encode("utf-8")
    url = urljoin(HOST, uri.lstrip("/"))
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Internal gateway uses a self-signed chain in some environments.
    ssl_context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as resp:
        body = resp.read().decode("utf-8")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected dict JSON payload, got {type(payload).__name__}")
    return payload


def read_bits_case(bits_case_url: str, result_form: str = "json") -> Dict[str, Any]:
    params = {
        "case_url": bits_case_url,
        "result_form": result_form,
    }
    return _call_api(FETCH_URI, params)


def save_case_to_bits(
    case_form: str,
    case_content: Any,
    case_title: str,
    user_name: str,
    devops_id: int = 310499123202,
    dir_id: int = 1416963,
    case_id: int | None = None,
    meego_info: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    params = {
        "case_form": case_form,
        "case_content": case_content,
        "case_title": case_title,
        "user_name": user_name,
        "devops_id": devops_id,
        "dir_id": dir_id,
    }
    if case_id is not None:
        params["case_id"] = case_id
    if meego_info is not None:
        params["meego_info"] = meego_info
    return _call_api(SAVE_URI, params)

def read_case_from_file(path: Union[str, Path]) -> JSONLike:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        return json.loads(text)
    return text


def write_case_to_file(case: JSONLike, output_path: Union[str, Path], pretty: bool = True) -> None:
    file_path = Path(output_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.suffix.lower() == ".json":
        content = json.dumps(case, ensure_ascii=False, indent=2 if pretty else None)
    else:
        if isinstance(case, str):
            content = case
        else:
            content = json.dumps(case, ensure_ascii=False, indent=2 if pretty else None)
    file_path.write_text(content + ("" if content.endswith("\n") else "\n"), encoding="utf-8")


def _build_case_detail_url(devops_id: int, case_id: int) -> str:
    return BITS_CASE_DETAIL_URL.format(devops_id=devops_id, case_id=case_id)


def _normalize_case_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_node_text(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("**[") and "]**" in line:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _iter_case_heading_blocks(markdown: str) -> list[tuple[re.Match[str], str]]:
    matches = list(CASE_HEADING_PATTERN.finditer(markdown))
    blocks: list[tuple[re.Match[str], str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        blocks.append((match, markdown[start:end]))
    return blocks


def _parse_case_expectation_paths(markdown: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for case_index, (match, block) in enumerate(_iter_case_heading_blocks(markdown)):
        nodes = list(CASE_NODE_HEADING_PATTERN.finditer(block))
        expectation_nodes: list[dict[str, Any]] = []
        step_index = -1
        expectation_index_by_step: dict[int, int] = {}
        for node_index, node in enumerate(nodes):
            label = node.group("label")
            section_end = (
                nodes[node_index + 1].start() if node_index + 1 < len(nodes) else len(block)
            )
            inline = node.group("inline").strip()
            body = block[node.end() : section_end].strip()
            text = _normalize_node_text("\n".join(part for part in [inline, body] if part))
            if label == "操作步骤":
                step_index += 1
                expectation_index_by_step.setdefault(step_index, 0)
                continue
            if label != "预期结果":
                continue
            if step_index < 0:
                step_index = 0
                expectation_index_by_step.setdefault(step_index, 0)
            expectation_index = expectation_index_by_step.get(step_index, 0)
            expectation_index_by_step[step_index] = expectation_index + 1
            expectation_nodes.append(
                {
                    "path": [step_index, expectation_index],
                    "expected_result": text,
                }
            )
        cases.append(
            {
                "case_index": case_index,
                "case_title": _normalize_case_heading(match.group("title")),
                "expectation_nodes": expectation_nodes,
            }
        )
    return cases


def _node_text(node: dict[str, Any]) -> str:
    for key in ("title", "name", "text", "content", "value", "desc", "description"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return _normalize_node_text(value)
    return ""


def _is_expectation_node(node: dict[str, Any]) -> bool:
    for key in ("node_type", "nodeType", "type", "category", "label"):
        value = node.get(key)
        if isinstance(value, str) and "预期结果" in value:
            return True
    text = _node_text(node)
    return text.startswith("预期结果") or text.lower().startswith("expected result")


def _node_id(node: dict[str, Any]) -> str | None:
    for key in ("expectation_id", "expectationId", "id", "node_id", "nodeId", "key"):
        value = node.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(value).strip()
    return None


def _walk_nodes(root: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(root, dict):
        if _is_expectation_node(root):
            node_id = _node_id(root)
            if node_id:
                found.append({"id": node_id, "bits_text": _node_text(root)})
        for value in root.values():
            if isinstance(value, (dict, list)):
                found.extend(_walk_nodes(value))
    elif isinstance(root, list):
        for item in root:
            found.extend(_walk_nodes(item))
    return found


def _extract_bits_expectation_nodes(resp: Dict[str, Any]) -> list[dict[str, Any]]:
    data = resp.get("data")
    if not isinstance(data, dict):
        return []
    roots = [
        data.get("case_data"),
        data.get("mindNodes"),
        data.get("mind_nodes"),
        data.get("case_mind"),
        data.get("caseMind"),
    ]
    nodes: list[dict[str, Any]] = []
    for root in roots:
        nodes.extend(_walk_nodes(root))
    if not nodes:
        nodes.extend(_walk_nodes(data))
    seen: set[str] = set()
    unique_nodes: list[dict[str, Any]] = []
    for node in nodes:
        node_id = node["id"]
        if node_id in seen:
            continue
        seen.add(node_id)
        unique_nodes.append(node)
    return unique_nodes


def _extract_case_expectations_from_save_response(
    resp: Dict[str, Any],
    case_content: str | None,
) -> list[dict[str, Any]]:
    if not case_content:
        return []
    parsed_cases = _parse_case_expectation_paths(case_content)
    expected_paths = [
        (case["case_index"], node["path"])
        for case in parsed_cases
        for node in case["expectation_nodes"]
    ]
    bits_nodes = _extract_bits_expectation_nodes(resp)
    if not bits_nodes:
        return []
    if len(bits_nodes) != len(expected_paths):
        return []

    bits_iter = iter(bits_nodes)
    case_expectations: list[dict[str, Any]] = []
    for case in parsed_cases:
        nodes: list[dict[str, Any]] = []
        for parsed_node in case["expectation_nodes"]:
            bits_node = next(bits_iter)
            nodes.append(
                {
                    "path": parsed_node["path"],
                    "id": bits_node["id"],
                    "expected_result": parsed_node["expected_result"],
                    "bits_text": bits_node.get("bits_text", ""),
                }
            )
        case_expectations.append(
            {
                "case_index": case["case_index"],
                "case_title": case["case_title"],
                "expectation_nodes": nodes,
            }
        )
    return case_expectations


def _format_save_response(
    resp: Dict[str, Any],
    devops_id: int,
    case_content: str | None = None,
) -> Dict[str, Any]:
    data = resp.get("data")
    if not isinstance(data, dict):
        return resp

    raw_case_url = data.get("case_url")
    if isinstance(raw_case_url, dict):
        case_id = raw_case_url.get("caseId")
        if isinstance(case_id, int):
            data["case_detail_url"] = _build_case_detail_url(devops_id, case_id)
    elif isinstance(raw_case_url, int):
        data["case_detail_url"] = _build_case_detail_url(devops_id, raw_case_url)

    case_expectations = _extract_case_expectations_from_save_response(resp, case_content)
    if case_expectations:
        data["case_expectations"] = case_expectations

    return resp


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read/write test cases from Bits and local files.")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Fetch case data from Bits by case URL.")
    fetch.add_argument("case_url", help="Bits case detail URL.")
    fetch.add_argument("--result-form", default="json", help="Result form passed to API.")
    fetch.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path. Use .json for JSON output.",
    )

    save = sub.add_parser("save", help="Save local case content to Bits (supports markdown or json).")
    save.add_argument("input_file", help="Input case file path (markdown text or case_mind/fetch JSON).")
    save.add_argument("--case-form", choices=["markdown", "json"], required=True, help="Upload format.")
    save.add_argument("--case-title", required=True, help="Bits case title.")
    save.add_argument("--user-name", required=True, help="Uploader user name / email prefix.")
    save.add_argument("--devops-id", type=int, default=310499123202, help="Bits devops id.")
    save.add_argument("--dir-id", type=int, default=1416963, help="Bits directory id.")
    save.add_argument("--case-id", type=int, default=None, help="Optional existing Bits case id to update. Use absence of --case-id for initial create; Meego binding should be decided before that first create.")
    save.add_argument("--meego-project-key", default="", help="Optional Meego projectKey for the initial create request. Do not assume it can be added later by updating an existing case.")
    save.add_argument("--meego-work-item-id", type=int, default=None, help="Optional Meego workItemId for the initial create request. Do not assume it can be added later by updating an existing case.")
    save.add_argument("-o", "--output", help="Optional output file path for API response.")

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "fetch":
        data = read_bits_case(args.case_url, result_form=args.result_form)
        write_case_to_file(data, args.output, pretty=True)
        print(f"Fetched case and wrote response to: {args.output}")
        return 0

    if args.command == "save":
        case_form = str(args.case_form).strip()
        obj = read_case_from_file(args.input_file)
        if case_form == "markdown":
            if not isinstance(obj, str):
                raise TypeError("save (markdown) expects a markdown/text case file.")
            case_content = obj
        elif case_form == "json":
            case_mind = None
            if isinstance(obj, dict) and isinstance(obj.get("code"), int) and isinstance(obj.get("data"), dict):
                data = obj.get("data") or {}
                case_data = data.get("case_data")
                if isinstance(case_data, dict):
                    case_mind = case_data
            if case_mind is None and isinstance(obj, dict) and isinstance(obj.get("data"), dict) and isinstance(obj.get("children"), list):
                case_mind = obj
            if case_mind is None:
                raise TypeError("save (json) expects a case_mind JSON tree or a fetch response JSON.")
            case_content = [case_mind]
        else:
            raise ValueError(f"Unknown case_form: {case_form}")

        # Build optional meego_info
        meego_info = None
        project_key = str(getattr(args, "meego_project_key", "") or "").strip()
        work_item_id = getattr(args, "meego_work_item_id", None)
        if project_key and (work_item_id is not None):
            # Build full meegoInfo with fixed empty-string fields (agent won't set them)
            meego_info = {
                "projectKey": project_key,
                "workItemId": int(work_item_id),
                "title": "",
                "link": "",
                "spaceName": "",
                "simpleName": "",
                "businessPath": "",
                "tenantKey": "",
            }

        resp = save_case_to_bits(
            case_form=case_form,
            case_content=case_content,
            case_title=args.case_title,
            user_name=args.user_name,
            devops_id=args.devops_id,
            dir_id=args.dir_id,
            case_id=args.case_id,
            meego_info=meego_info,
        )
        resp = _format_save_response(resp, args.devops_id, case_content=case_data)
        if args.output:
            write_case_to_file(resp, args.output, pretty=True)
            print(f"Saved case to Bits. API response written to: {args.output}")
        else:
            print(json.dumps(resp, ensure_ascii=False, indent=2))
        return 0

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
