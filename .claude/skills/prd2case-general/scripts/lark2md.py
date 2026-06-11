#!/usr/bin/env python3
"""
Fetch a Lark/PRD document by URL and return its markdown content.
"""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.request
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError


FETCH_PRD_URL = "https://bits.bytedance.net/quality/caseScore/api/v1/caseGenerate/prdLinkUpload"
JWT_TOKEN_FILE = Path("/tmp/.jwt_token")
JWT_TOKEN_COMMAND = 'npm_config_registry="https://bnpm.byted.org" npx -y skills get-jwt --region cn'
TIMEOUT = 900


def _resolve_output_file(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _jwt_token_error() -> RuntimeError:
    return RuntimeError(
        "JWT token is missing or invalid. Run "
        f"`{JWT_TOKEN_COMMAND}` "
        f"and save the output to `{JWT_TOKEN_FILE}` before calling lark2md.py."
    )


def _load_jwt_token() -> str:
    try:
        jwt_token = JWT_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise _jwt_token_error() from exc

    if not jwt_token:
        raise _jwt_token_error()
    return jwt_token


def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    ssl_context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=ssl_context) as response:
            resp_json = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc

    if not isinstance(resp_json, dict):
        raise TypeError(f"Expected dict JSON payload, got {type(resp_json).__name__}")
    return resp_json


def convert_lark_document_to_md(lark_doc_url: str) -> str:
    lark_doc_url = str(lark_doc_url or "").strip()
    if not lark_doc_url:
        raise ValueError("lark_doc_url is required")

    jwt_token = _load_jwt_token()

    prd_data = _post_json(
        FETCH_PRD_URL,
        payload={"link": lark_doc_url},
        headers={"x-jwt-token": jwt_token},
    )
    if prd_data.get("code") == 2002 and prd_data.get("description") == "no permission, jwt invalid":
        raise _jwt_token_error()

    prd = prd_data.get("prd")
    if not isinstance(prd, dict):
        raise ValueError("invalid response: missing prd object")

    title = prd.get("title")
    content = prd.get("full_content")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("invalid response: missing prd.title")
    if not isinstance(content, str):
        raise ValueError("invalid response: missing prd.full_content")

    return f"<title>\n{title}\n</title>\n<content>\n{content}\n</content>"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a Lark/PRD document and export markdown content.",
    )
    parser.add_argument("lark_doc_url", help="Lark/PRD document URL.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output path for the markdown content.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    doc = convert_lark_document_to_md(args.lark_doc_url)
    if not args.output:
        print(doc)
        return 0

    output_file = _resolve_output_file(args.output)
    output_file.write_text(doc, encoding="utf-8")
    print(str(output_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
