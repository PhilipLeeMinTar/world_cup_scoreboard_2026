#!/usr/bin/env python3
"""scan_case.py — case.md 前置扫描，输出紧凑 JSON。

go_driver generate 阶段的 case.md 前置校验包含三类确定性扫描：
  1. 未解析参数：`[tt-nova-datagen]`、`[USER_INPUT_REQUIRED: ...]`、`[Manual Prompt]`
  2. SecretRuntime 业务鉴权变量：Cookie / Hex-Auth-Key / Authorization / JWT 等
  3. 每个 case 的「非鉴权 Header 清单」：Content-Type / X-Device-Type 等
     业务请求头（排除上面的鉴权 header）。模型极易在生成 Go 代码时漏掉
     这类 header，故由脚本确定性地提取成清单，供 generate 阶段逐项对照核对。

这三类都是确定性解析，无需模型读 case.md 全文。SKILL 调用本脚本拿到
紧凑清单（含 case_id 与行号）后，把「凭记忆生成 header」变成「对照脚本
清单逐项核对」，从而显著降低非鉴权 header 的遗漏概率。

用法:
  python3 scan_case.py --case-file <FEATURE_DIR/test/case.md>
  python3 scan_case.py --case-file <case.md> --json --compact

输出契约:
  exists: bool                      case.md 是否存在
  unresolved_items[]: {marker, line, text}
  unresolved_count: int
  secret_runtime_hits[]: {key, line, text}
  secret_runtime_count: int
  has_unresolved: bool              是否存在未解析项(需 AskUserQuestion)
  has_secret_runtime: bool          是否命中鉴权变量(写 warnings, 不阻塞)
  case_headers[]: {case_id, line, non_auth_headers[]:{key,value,line}}
                                    每个 case 的非鉴权 header 清单(Headers 生成的权威来源)
                                    --compact 时只输出存在非鉴权 header 的 case
  non_auth_header_count: int        所有 case 非鉴权 header 总数
  has_non_auth_headers: bool        是否存在需叠加进 HTTPRequest.Headers 的非鉴权 header

退出码: 0 正常(无论是否有命中); 2 文件不存在。

macOS 兼容: 纯 Python stdlib。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional


# 未解析参数标记：占位符 / 待补充输入 / 人工提示
UNRESOLVED_PATTERNS = [
    ("tt-nova-datagen", re.compile(r"\[tt-nova-datagen[^\]]*\]", re.IGNORECASE)),
    ("USER_INPUT_REQUIRED", re.compile(r"\[USER_INPUT_REQUIRED:[^\]]*\]", re.IGNORECASE)),
    ("Manual Prompt", re.compile(r"\[Manual Prompt[^\]]*\]", re.IGNORECASE)),
]

# SecretRuntime 业务鉴权变量关键字（出现在 Headers / 参数中即命中）
SECRET_RUNTIME_KEYS = [
    "Cookie",
    "Hex-Auth-Key",
    "Authorization",
    "Hex-Login-User-Info",
    "X-Auth",
    "JWT",
    "Token",
]
SECRET_RUNTIME_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in SECRET_RUNTIME_KEYS) + r")\b",
    re.IGNORECASE,
)

# case 标题：`### [TC-001] ...`，兼容转义 `\[` 与非转义 `[`
CASE_HEADING_PATTERN = re.compile(r"^\s*#{2,4}\s*\\?\[(TC-[^\]]+)\\?\]", re.IGNORECASE)

# Headers 子段起始：`- **Headers**:`（允许任意缩进、可选冒号）
HEADERS_SECTION_PATTERN = re.compile(r"^\s*[-*]\s*\*\*Headers\*\*\s*:?\s*$", re.IGNORECASE)

# Headers 子段内的同级兄弟子段（出现即退出 Headers 解析）
SIBLING_SECTION_PATTERN = re.compile(
    r"^\s*[-*]\s*\*\*(Path Parameters|Query Parameters|Body Parameters|"
    r"Request Parameters|Assertions|Variable Extraction)\*\*",
    re.IGNORECASE,
)

# header 行：`- `<key>`: `<value>` *(可选注释)*`
HEADER_LINE_PATTERN = re.compile(
    r"^\s*[-*]\s*`(?P<key>[^`]+)`\s*:\s*`(?P<value>[^`]*)`"
)


def truncate(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def is_auth_header(key: str) -> bool:
    """是否为鉴权 header（复用 SecretRuntime 关键字判定）。"""
    return bool(SECRET_RUNTIME_PATTERN.search(key))


def scan(case_file: str) -> Dict[str, Any]:
    unresolved: List[Dict[str, Any]] = []
    secret_hits: List[Dict[str, Any]] = []
    seen_secret_keys = set()

    # 非鉴权 header 解析状态机：
    #   current_case  当前所属 case（{case_id, line, non_auth_headers[]}）
    #   in_headers    是否正处于某个 case 的 `**Headers**:` 子段内
    case_headers: List[Dict[str, Any]] = []
    current_case: Optional[Dict[str, Any]] = None
    in_headers = False

    with open(case_file, "r", encoding="utf-8", errors="ignore") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")

            for marker, pattern in UNRESOLVED_PATTERNS:
                if pattern.search(line):
                    unresolved.append({
                        "marker": marker,
                        "line": lineno,
                        "text": truncate(line),
                    })

            for m in SECRET_RUNTIME_PATTERN.finditer(line):
                key = m.group(1)
                # 同一鉴权 key 只记录首次命中行，降低噪声与上下文占用
                norm = key.lower()
                if norm in seen_secret_keys:
                    continue
                seen_secret_keys.add(norm)
                secret_hits.append({
                    "key": key,
                    "line": lineno,
                    "text": truncate(line),
                })

            # ── 非鉴权 header 清单解析 ──
            case_match = CASE_HEADING_PATTERN.match(line)
            if case_match:
                current_case = {
                    "case_id": case_match.group(1),
                    "line": lineno,
                    "non_auth_headers": [],
                }
                case_headers.append(current_case)
                in_headers = False
                continue

            if HEADERS_SECTION_PATTERN.match(line):
                # 仅在已进入某个 case 后才记录其 Headers 子段
                in_headers = current_case is not None
                continue

            if in_headers:
                if not line.strip():
                    continue  # 空行不终止子段
                if SIBLING_SECTION_PATTERN.match(line):
                    in_headers = False
                    continue
                hm = HEADER_LINE_PATTERN.match(line)
                if hm:
                    key = hm.group("key").strip()
                    if not is_auth_header(key):
                        current_case["non_auth_headers"].append({
                            "key": key,
                            "value": hm.group("value").strip(),
                            "line": lineno,
                        })
                    continue
                # 既非 header 行也非兄弟子段：保守地退出 Headers 子段
                in_headers = False

    non_auth_total = sum(len(c["non_auth_headers"]) for c in case_headers)

    return {
        "exists": True,
        "unresolved_items": unresolved,
        "unresolved_count": len(unresolved),
        "secret_runtime_hits": secret_hits,
        "secret_runtime_count": len(secret_hits),
        "has_unresolved": bool(unresolved),
        "has_secret_runtime": bool(secret_hits),
        "case_headers": case_headers,
        "non_auth_header_count": non_auth_total,
        "has_non_auth_headers": non_auth_total > 0,
    }


def compact_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """压缩 JSON 输出，减少大 case.md 在模型上下文中的占用。"""
    if not result.get("exists"):
        return result
    compacted = dict(result)
    compacted["case_headers"] = [
        case for case in result.get("case_headers", [])
        if case.get("non_auth_headers")
    ]
    compacted["case_headers_omitted_empty"] = len(result.get("case_headers", [])) - len(compacted["case_headers"])
    return compacted


def emit(result: Dict[str, Any], as_json: bool, compact: bool = False) -> None:
    if compact:
        result = compact_result(result)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return
    if not result.get("exists"):
        print("exists=false")
        return
    print(f"exists=true unresolved={result['unresolved_count']} "
          f"secret_runtime={result['secret_runtime_count']} "
          f"non_auth_headers={result['non_auth_header_count']}")
    for item in result["unresolved_items"]:
        print(f"  unresolved L{item['line']} [{item['marker']}]: {item['text']}")
    for item in result["secret_runtime_hits"]:
        print(f"  secret    L{item['line']} {item['key']}: {item['text']}")
    for case in result["case_headers"]:
        for h in case["non_auth_headers"]:
            print(f"  header    L{h['line']} [{case['case_id']}] "
                  f"{h['key']}: {h['value']}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="扫描 case.md 的未解析项与鉴权变量")
    parser.add_argument("--case-file", required=True, help="case.md 路径")
    parser.add_argument("--json", action="store_true", help="输出紧凑 JSON")
    parser.add_argument("--compact", action="store_true",
                        help="JSON 中仅保留含非鉴权 header 的 case_headers 项，降低上下文占用")
    args = parser.parse_args(argv)

    if not os.path.exists(args.case_file):
        emit({"exists": False, "case_file": args.case_file}, args.json, args.compact)
        return 2

    emit(scan(args.case_file), args.json, args.compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
