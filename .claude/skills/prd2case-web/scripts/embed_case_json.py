#!/usr/bin/env python3
"""
Embed case JSON into the HTML template block:
<script id="embedded-case-json" type="application/json"> ... </script>

Usage:
  python3 embed_case_json.py <json_path> <html_path>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PATTERN = re.compile(
    r'(^\s*<script id="embedded-case-json" type="application/json">)([\s\S]*?)(^\s*</script>)',
    re.M,
)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 embed_case_json.py <json_path> <html_path>", file=sys.stderr)
        return 2

    json_path = Path(sys.argv[1])
    html_path = Path(sys.argv[2])

    if not json_path.is_file():
        print(f"JSON file not found: {json_path}", file=sys.stderr)
        return 1
    if not html_path.is_file():
        print(f"HTML file not found: {html_path}", file=sys.stderr)
        return 1

    data = json.loads(json_path.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    html = html_path.read_text(encoding="utf-8")

    def repl(match: re.Match[str]) -> str:
        return match.group(1) + "\n" + payload + "\n" + match.group(3)

    new_html, count = PATTERN.subn(repl, html, count=1)
    if count != 1:
        print(
            "Failed to find a unique '<script id=\"embedded-case-json\" type=\"application/json\">' block.",
            file=sys.stderr,
        )
        return 1

    html_path.write_text(new_html, encoding="utf-8")
    print(f"Embedded JSON into: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
