#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://q9q0hn98.fn.bytedance.net"
# DEFAULT_BASE_URL = "http://127.0.0.1:8001" 
TIMEOUT = 900


def _resolve_existing_file(path_str: str, label: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def _resolve_output_file(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _post_json(base_url: str, endpoint: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{endpoint}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            resp_json = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc

    if resp_json.get("code") != 0:
        raise RuntimeError(
            f"API returned error: code={resp_json.get('code')}, msg={resp_json.get('msg')}"
        )
    return resp_json


def run_prd_analysis(
    input_document_path: str,
    output_path: str,
    base_url: str = DEFAULT_BASE_URL,
    user_instruction_path: str | None = None,
) -> Path:
    input_document = _resolve_existing_file(input_document_path, "input document")
    output_file = _resolve_output_file(output_path)

    payload = {
        "input_document_content": _read_text(input_document),
    }
    if user_instruction_path:
        user_instruction = _resolve_existing_file(user_instruction_path, "user instruction")
        payload["user_instruction"] = _read_text(user_instruction)

    result = _post_json(base_url, "/agent_api/prd_analysis", payload)
    output_file.write_text(
        json.dumps(result["data"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_file


def run_framework_generation(
    input_document_path: str,
    prd_analyze_result_path: str,
    experiment_setting_path: str,
    output_path: str,
    base_url: str = DEFAULT_BASE_URL,
) -> Path:
    input_document = _resolve_existing_file(input_document_path, "input document")
    prd_analyze_result = _resolve_existing_file(prd_analyze_result_path, "prd analyze result")
    experiment_setting = _resolve_existing_file(experiment_setting_path, "experiment setting")
    output_file = _resolve_output_file(output_path)

    payload = {
        "input_document_content": _read_text(input_document),
        "prd_analyze_result": json.loads(_read_text(prd_analyze_result)),
        "ab_setting_result": _read_text(experiment_setting),
    }

    result = _post_json(base_url, "/agent_api/framework_generation", payload)
    output_file.write_text(result["data"], encoding="utf-8")
    return output_file


def run_detailed_case_generation(
    input_document_path: str,
    framework_path: str,
    prd_analyze_result_path: str,
    output_path: str,
    base_url: str = DEFAULT_BASE_URL,
    case_mode: str = "General",
) -> Path:
    input_document = _resolve_existing_file(input_document_path, "input document")
    framework_file = _resolve_existing_file(framework_path, "framework markdown")
    prd_analyze_result = _resolve_existing_file(prd_analyze_result_path, "prd analyze result")
    output_file = _resolve_output_file(output_path)

    payload = {
        "input_document_content": _read_text(input_document),
        "framework_text": _read_text(framework_file),
        "prd_analyze_result": json.loads(_read_text(prd_analyze_result)),
        "case_mode": case_mode,
    }

    result = _post_json(base_url, "/agent_api/generate_detailed_case", payload)
    output_file.write_text(result["data"], encoding="utf-8")
    return output_file


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call local PRD2Case APIs with file-path inputs and save results to files.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base url, default: {DEFAULT_BASE_URL}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    prd_analysis_parser = subparsers.add_parser(
        "prd-analysis",
        help="Call /agent_api/prd_analysis and save JSON result.",
    )
    prd_analysis_parser.add_argument("input_document_path", help="Path to source document.")
    prd_analysis_parser.add_argument("output_path", help="Path to output JSON file.")
    prd_analysis_parser.add_argument(
        "--user-instruction-path",
        help="Optional path to extra user instruction text.",
    )

    framework_parser = subparsers.add_parser(
        "framework-generation",
        help="Call /agent_api/framework_generation and save markdown framework.",
    )
    framework_parser.add_argument("input_document_path", help="Path to source document.")
    framework_parser.add_argument(
        "prd_analyze_result_path",
        help="Path to JSON result from prd-analysis.",
    )
    framework_parser.add_argument(
        "experiment_setting_path",
        help="Path to experiment setting markdown/text file.",
    )
    framework_parser.add_argument("output_path", help="Path to output markdown file.")

    detailed_case_parser = subparsers.add_parser(
        "detailed-case-generation",
        help="Call /agent_api/generate_detailed_case and save detailed case markdown.",
    )
    detailed_case_parser.add_argument("input_document_path", help="Path to source document.")
    detailed_case_parser.add_argument(
        "framework_path",
        help="Path to markdown framework generated from framework-generation.",
    )
    detailed_case_parser.add_argument(
        "prd_analyze_result_path",
        help="Path to JSON result from prd-analysis.",
    )
    detailed_case_parser.add_argument("output_path", help="Path to output markdown file.")
    detailed_case_parser.add_argument(
        "--case-mode",
        default="General",
        help="Optional case mode passed to PRD2Case API. Default: General.",
    )

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.command == "prd-analysis":
            output_path = run_prd_analysis(
                input_document_path=args.input_document_path,
                output_path=args.output_path,
                base_url=args.base_url,
                user_instruction_path=args.user_instruction_path,
            )
        elif args.command == "framework-generation":
            output_path = run_framework_generation(
                input_document_path=args.input_document_path,
                prd_analyze_result_path=args.prd_analyze_result_path,
                experiment_setting_path=args.experiment_setting_path,
                output_path=args.output_path,
                base_url=args.base_url,
            )
        else:
            output_path = run_detailed_case_generation(
                input_document_path=args.input_document_path,
                framework_path=args.framework_path,
                prd_analyze_result_path=args.prd_analyze_result_path,
                output_path=args.output_path,
                base_url=args.base_url,
                case_mode=args.case_mode,
            )
    except Exception as exc:
        print(str(exc))
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
