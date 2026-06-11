#!/usr/bin/env python3
"""
Validate test-case grammar defined in:
references/test_case_grammar.md

Current support:
- Markdown input (.md/.markdown)
- JSON input detection only (not supported yet)

Output:
- JSON with:
  - overall_result
  - detailed_check_result
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


NODE_TYPES = {"测试点", "用例标题", "前置条件", "操作步骤", "预期结果", "测试内容"}
ALLOWED_PRIORITY = {"P0", "P1", "P2", "P3"}
HEADER_RE = re.compile(r"^(#{1,})\s*(.*?)\s*$")
TYPE_PREFIX_RE = re.compile(r"^\*\*(测试点|用例标题|前置条件|操作步骤|预期结果|测试内容)\*\*\s*(.*)$")
TYPE_PLAIN_RE = re.compile(r"^(测试点|用例标题|前置条件|操作步骤|预期结果|测试内容)\s*(.*)$")
ATTR_RE = re.compile(r"^\*\*\[(priority|tag|hyperlink|analysis-id)\]\*\*\s*(.+)\s*$")
HYPERLINK_RE = re.compile(r"^\[[^\]]+\]\([^)]+\)$")
TEST_CONTENT_LINE_RE = re.compile(r"^\*\*测试内容\*\*\s*(.+)\s*$")
PRECONDITION_URL_RE = re.compile(r"访问\s*[:：]\s*(\S+)")
ABSOLUTE_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
URL_PLACEHOLDER_HINTS = (
    "<",
    "${",
    "{host",
    "{env",
    "{stage",
    "TO_FILL",
    "TODO",
    "example.com",
    "localhost",
    "127.0.0.1",
)
UNRESOLVED_CASE_TAGS = {
    "manual-review",
    "needs-data",
    "blocked",
    "manual-prep",
    "skip",
    "unverified",
}


@dataclass
class Node:
    index: int
    line_no: int
    level: int
    raw_title: str
    node_type: str
    node_content: str
    body_lines: List[Tuple[int, str]] = field(default_factory=list)
    parent: Optional["Node"] = None
    children: List["Node"] = field(default_factory=list)


@dataclass
class RuleResult:
    rule_id: str
    description: str
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.passed = False
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check grammar of generated test case markdown."
    )
    parser.add_argument("input_file", help="Path to markdown or json file.")
    parser.add_argument(
        "--strict-title",
        action="store_true",
        help="Treat `用例标题` nodes as hard errors (default: warning).",
    )
    parser.add_argument(
        "--analysis-file",
        help=(
            "Optional test_analysis.md path. When provided, require one case per "
            "analysis id via `**[analysis-id]** <id>` in case.md."
        ),
    )
    return parser.parse_args()


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".json":
        return "json"
    return "unknown"


def extract_type_and_content(title: str) -> Tuple[str, str]:
    stripped = title.strip()
    match = TYPE_PREFIX_RE.match(stripped)
    if match:
        return match.group(1), match.group(2).strip()
    match = TYPE_PLAIN_RE.match(stripped)
    if match:
        plain_content = match.group(2).strip()
        # If title is exactly the enum word (e.g. "用例标题"), treat it as
        # plain node content by default, not as an explicit node type.
        if plain_content:
            return match.group(1), plain_content
    return "测试点", stripped


def parse_markdown(markdown_text: str) -> Tuple[List[Node], RuleResult]:
    rule = RuleResult(
        rule_id="R0_PARSE",
        description="Parse markdown rows into node tree.",
    )
    nodes: List[Node] = []
    current_node: Optional[Node] = None

    for line_no, raw_line in enumerate(markdown_text.splitlines(), start=1):
        line = raw_line.rstrip("\n")
        match = HEADER_RE.match(line)
        if match:
            hashes, title = match.groups()
            node_type, content = extract_type_and_content(title)
            node = Node(
                index=len(nodes),
                line_no=line_no,
                level=len(hashes),
                raw_title=title.strip(),
                node_type=node_type,
                node_content=content,
            )
            nodes.append(node)
            current_node = node
        else:
            if current_node is not None:
                current_node.body_lines.append((line_no, line))
    if not nodes:
        rule.add_error("No markdown node found. Expected lines starting with '#'.")
    return nodes, rule


def link_tree(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R1_LEVEL_AND_PARENT",
        description="Child node level must be parent level + 1.",
    )
    stack: List[Node] = []
    for node in nodes:
        while stack and stack[-1].level >= node.level:
            stack.pop()
        if stack:
            if stack[-1].level == node.level - 1:
                parent = stack[-1]
                node.parent = parent
                parent.children.append(node)
            else:
                rule.add_error(
                    f"Line {node.line_no}: invalid level jump from parent level "
                    f"{stack[-1].level} to child level {node.level}."
                )
        stack.append(node)
    return rule


def check_node_type(nodes: List[Node], strict_title: bool) -> RuleResult:
    rule = RuleResult(
        rule_id="R2_NODE_TYPE",
        description="Node type must be in allowed enum.",
    )
    for node in nodes:
        if node.node_type not in NODE_TYPES:
            rule.add_error(
                f"Line {node.line_no}: invalid node type `{node.node_type}`."
            )
        if node.node_type == "用例标题":
            msg = (
                f"Line {node.line_no}: node type `用例标题` is reading-only and "
                "should not be generated."
            )
            if strict_title:
                rule.add_error(msg)
            else:
                rule.add_warning(msg)
    return rule


def check_special_node_emphasis(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R2A_SPECIAL_NODE_EMPHASIS",
        description="Special node types must use `**NodeType**` form, plain form is not allowed.",
    )
    special_node_types = {"用例标题", "前置条件", "操作步骤", "预期结果", "测试内容"}
    for node in nodes:
        if node.node_type not in special_node_types:
            continue
        if not TYPE_PREFIX_RE.match(node.raw_title):
            rule.add_error(
                f"Line {node.line_no}: special node `{node.node_type}` must use "
                f"`**{node.node_type}**` form."
            )
    return rule


def check_parent_child_relation(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R3_PARENT_CHILD",
        description="Node parent-child relation must follow grammar constraints.",
    )
    allowed_child: Dict[str, set] = {
        "测试点": {"测试点", "前置条件", "用例标题"},
        "用例标题": {"前置条件"},
        "前置条件": {"操作步骤"},
        "操作步骤": {"操作步骤", "预期结果"},
        "预期结果": set(),
        "测试内容": {"测试点", "前置条件"},
    }
    for node in nodes:
        for child in node.children:
            allowed = allowed_child.get(node.node_type, set())
            if child.node_type not in allowed:
                rule.add_error(
                    f"Line {child.line_no}: `{child.node_type}` cannot be child of "
                    f"`{node.node_type}`."
                )
    return rule


def check_leaf_node(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R4_LEAF_TYPE",
        description="Leaf node must be `预期结果` or have `**测试内容**` in body.",
    )

    def has_test_content_line(node: Node) -> bool:
        for _, line in node.body_lines:
            if TEST_CONTENT_LINE_RE.match(line.strip()):
                return True
        return False

    for node in nodes:
        if not node.children and node.node_type != "预期结果" and not has_test_content_line(node):
            rule.add_error(
                f"Line {node.line_no}: leaf node type is `{node.node_type}`, expected `预期结果` "
                "or a `**测试内容**` line in node body."
            )
    return rule


def check_top_down_order(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R5_TOP_DOWN_ORDER",
        description="Top-down order should be 测试点 -> 用例标题(optional) -> 前置条件 -> 操作步骤 -> 预期结果.",
    )
    order = {"测试点": 0, "用例标题": 1, "前置条件": 2, "操作步骤": 3, "预期结果": 4, "测试内容": 0}
    for node in nodes:
        for child in node.children:
            p = order.get(node.node_type, -1)
            c = order.get(child.node_type, -1)
            if node.node_type in {"测试点", "操作步骤"} and c == p:
                continue
            if c < p:
                rule.add_error(
                    f"Line {child.line_no}: order regression `{node.node_type}` -> `{child.node_type}`."
                )
    return rule


def check_attributes(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R6_ATTRIBUTES",
        description="Check attribute line format for priority/tag/hyperlink.",
    )
    for node in nodes:
        for line_no, line in node.body_lines:
            stripped = line.strip()
            if not stripped.startswith("**["):
                continue
            match = ATTR_RE.match(stripped)
            if not match:
                rule.add_error(
                    f"Line {line_no}: invalid attribute format `{stripped}`."
                )
                continue
            key, value = match.group(1), match.group(2).strip()
            if key == "priority" and value not in ALLOWED_PRIORITY:
                rule.add_error(
                    f"Line {line_no}: invalid priority `{value}`, expected one of {sorted(ALLOWED_PRIORITY)}."
                )
            if key == "tag":
                tags = [x.strip() for x in value.split(",")]
                if not tags or any(not tag for tag in tags):
                    rule.add_error(
                        f"Line {line_no}: tag list must use comma-separated non-empty values."
                    )
            if key == "hyperlink" and not HYPERLINK_RE.match(value):
                rule.add_error(
                    f"Line {line_no}: hyperlink must be `[title](url)` format."
                )
            if key == "analysis-id":
                ids = [item.strip() for item in re.split(r"[,，]", value) if item.strip()]
                if not ids:
                    rule.add_error(
                        f"Line {line_no}: analysis-id must contain a non-empty id."
                    )
    return rule


def _split_markdown_table_row(line: str) -> List[str]:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _is_table_separator(cells: List[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _looks_like_placeholder_row(cells: List[str]) -> bool:
    joined = " ".join(cells).lower()
    return any(
        marker in joined
        for marker in (
            "...",
            "其他测试场景",
            "页面的名称",
            "测试执行前所需",
            "完成该核心场景",
        )
    )


def parse_analysis_ids(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    ids: List[str] = []
    seen: set[str] = set()
    active_header: Optional[List[str]] = None
    id_index: Optional[int] = None

    for raw_line in text.splitlines():
        cells = _split_markdown_table_row(raw_line)
        if not cells:
            active_header = None
            id_index = None
            continue
        if _is_table_separator(cells):
            continue
        normalized = [cell.replace(" ", "").lower() for cell in cells]
        if any(cell in {"分析id", "分析ID".lower(), "id", "caseid"} for cell in normalized):
            active_header = cells
            for index, cell in enumerate(normalized):
                if cell in {"分析id", "id", "caseid"}:
                    id_index = index
                    break
            continue
        if active_header is None or id_index is None:
            continue
        if id_index >= len(cells) or _looks_like_placeholder_row(cells):
            continue
        analysis_id = cells[id_index].strip()
        if not analysis_id or analysis_id in seen:
            continue
        seen.add(analysis_id)
        ids.append(analysis_id)
    return ids


def _extract_analysis_ids_from_node(node: Node) -> List[Tuple[int, str]]:
    ids: List[Tuple[int, str]] = []
    for line_no, line in node.body_lines:
        match = ATTR_RE.match(line.strip())
        if not match or match.group(1) != "analysis-id":
            continue
        for item in re.split(r"[,，]", match.group(2)):
            analysis_id = item.strip()
            if analysis_id:
                ids.append((line_no, analysis_id))
    return ids


def _is_case_root(node: Node) -> bool:
    return any(child.node_type in {"用例标题", "前置条件"} for child in node.children)


def check_analysis_case_mapping(nodes: List[Node], analysis_ids: List[str]) -> RuleResult:
    rule = RuleResult(
        rule_id="R10_ANALYSIS_CASE_MAPPING",
        description=(
            "When an analysis file is provided, each test_analysis row id must map "
            "to exactly one case, and each case must reference exactly one analysis id."
        ),
    )
    if not analysis_ids:
        rule.add_error(
            "analysis-file contains no analysis ids. Add a `分析ID` column to "
            "test_analysis.md and give every verification-point row a stable id."
        )
        return rule

    analysis_id_set = set(analysis_ids)
    case_roots = [node for node in nodes if node.node_type == "测试点" and _is_case_root(node)]
    case_to_ids: Dict[int, List[str]] = {}
    id_to_lines: Dict[str, List[int]] = {}

    for case in case_roots:
        pairs = _extract_analysis_ids_from_node(case)
        ids = [analysis_id for _, analysis_id in pairs]
        case_to_ids[case.line_no] = ids
        if not ids:
            rule.add_error(
                f"Line {case.line_no}: case `{case.node_content}` is missing "
                "`**[analysis-id]** <id>`; cannot prove it maps back to Stage-1."
            )
            continue
        if len(ids) != 1:
            rule.add_error(
                f"Line {case.line_no}: case `{case.node_content}` references multiple "
                f"analysis ids {ids}. Do not merge independent verification points into one case."
            )
        for line_no, analysis_id in pairs:
            if analysis_id not in analysis_id_set:
                rule.add_error(
                    f"Line {line_no}: analysis-id `{analysis_id}` is not present in "
                    "the provided test_analysis.md."
                )
            id_to_lines.setdefault(analysis_id, []).append(case.line_no)

    missing = [analysis_id for analysis_id in analysis_ids if analysis_id not in id_to_lines]
    if missing:
        rule.add_error(
            "Missing case mapping for analysis ids: " + ", ".join(missing[:20])
        )

    duplicates = {
        analysis_id: lines
        for analysis_id, lines in id_to_lines.items()
        if analysis_id in analysis_id_set and len(lines) > 1
    }
    for analysis_id, lines in duplicates.items():
        rule.add_error(
            f"analysis-id `{analysis_id}` is mapped by multiple cases at lines {lines}; "
            "each Stage-1 verification point must produce exactly one case."
        )

    mapped_case_count = sum(1 for ids in case_to_ids.values() if len(ids) == 1)
    if mapped_case_count != len(analysis_ids):
        rule.add_error(
            f"analysis/case count mismatch: test_analysis ids={len(analysis_ids)}, "
            f"single-id cases={mapped_case_count}. case count must match Stage-1 "
            "verification-point count."
        )
    return rule


def check_consecutive_operation_steps(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R8_CONSECUTIVE_OPERATION_STEPS",
        description="First child of `操作步骤` must be `预期结果`, not another `操作步骤`. "
        "Consecutive operation steps should be merged into one node using numbered lines.",
    )
    for node in nodes:
        if node.node_type != "操作步骤" or not node.children:
            continue
        if (
            node.parent
            and node.parent.node_type == "操作步骤"
            and node.parent.children[0] is node
        ):
            continue
        first_child = node.children[0]
        if first_child.node_type == "操作步骤":
            chain = [node]
            current = first_child
            while current.node_type == "操作步骤":
                chain.append(current)
                if current.children and current.children[0].node_type == "操作步骤":
                    current = current.children[0]
                else:
                    break
            lines_desc = ", ".join(f"Line {n.line_no}" for n in chain)
            rule.add_error(
                f"Lines [{lines_desc}]: found {len(chain)} consecutive `操作步骤` nodes "
                f"chained as parent-child. Per rule common 3-a, merge them into a single "
                f"`操作步骤` node with numbered lines (e.g. '1. step1\\n2. step2\\n3. step3')."
            )
    return rule


def _extract_tags_from_node(node: Node) -> set[str]:
    tags: set[str] = set()
    for _, line in node.body_lines:
        match = ATTR_RE.match(line.strip())
        if not match or match.group(1) != "tag":
            continue
        tags.update(item.strip().lower() for item in match.group(2).split(",") if item.strip())
    return tags


def _node_or_ancestor_has_unresolved_tag(node: Node) -> bool:
    current: Optional[Node] = node
    while current is not None:
        if _extract_tags_from_node(current) & UNRESOLVED_CASE_TAGS:
            return True
        current = current.parent
    return False


def check_precondition_url(nodes: List[Node]) -> RuleResult:
    """Validate executable `前置条件` lines `访问: <url>` carry an absolute URL.

    The most common failure is an LLM dropping the relative route from the
    spec / frontend code (e.g. `/ads-creation/dashboard`, `/creation`) into
    `case.md`'s `前置条件` instead of doing TDRS Phase 6/7 to resolve a real
    sample id and producing a full direct URL. Without an absolute URL the
    downstream runner (TTAT / playwright-cli) cannot navigate, so the case
    is unexecutable even though the markdown is structurally valid.
    """
    rule = RuleResult(
        rule_id="R9_PRECONDITION_URL",
        description=(
            "Executable `前置条件` lines `访问: <url>` must carry an absolute, "
            "currently-executable URL (^https?://...). Unresolved cases tagged "
            "manual-review/needs-data may keep the original precondition text."
        ),
    )
    for node in nodes:
        if node.node_type != "前置条件":
            continue
        if _node_or_ancestor_has_unresolved_tag(node):
            # Unresolved cases intentionally preserve the original precondition
            # text so humans can complete data prep later; they are not runnable.
            continue
        # Look for `访问:` either on the title line or in the body.
        candidates: List[Tuple[int, str]] = []
        title_match = PRECONDITION_URL_RE.search(node.node_content or "")
        if title_match:
            candidates.append((node.line_no, title_match.group(1).strip()))
        for line_no, line in node.body_lines:
            for body_match in PRECONDITION_URL_RE.finditer(line):
                candidates.append((line_no, body_match.group(1).strip()))
        if not candidates:
            rule.add_error(
                f"Line {node.line_no}: `前置条件` is missing the required "
                "`访问: <url>` line. case.md needs an absolute URL the "
                "runner can navigate to; if Stage-2 has not resolved a real "
                "sample id yet, stop and finish TDRS Phase 6/7 before "
                "writing case.md."
            )
            continue
        for line_no, raw_url in candidates:
            stripped = raw_url.rstrip(",.;)")
            if not ABSOLUTE_URL_RE.match(stripped):
                rule.add_error(
                    f"Line {line_no}: `前置条件 访问:` URL `{stripped}` is "
                    "not absolute (must start with `http://` or `https://`). "
                    "Relative routes from spec / frontend code are not "
                    "executable URLs — go back to Stage-2 / TDRS to resolve "
                    "the real sample id, then write the direct page URL."
                )
                continue
            lower = stripped.lower()
            if any(hint.lower() in lower for hint in URL_PLACEHOLDER_HINTS):
                rule.add_error(
                    f"Line {line_no}: `前置条件 访问:` URL `{stripped}` "
                    "looks like a placeholder / template / localhost. Replace "
                    "it with a concrete page URL pointing at a verified "
                    "sample (TDRS Phase 7.1)."
                )
                continue
            # Reject pure host (no path beyond `/`).
            try:
                _scheme, rest = stripped.split("://", 1)
            except ValueError:
                rest = stripped
            host_path = rest.split("/", 1)
            if len(host_path) < 2 or not host_path[1].strip():
                rule.add_error(
                    f"Line {line_no}: `前置条件 访问:` URL `{stripped}` is "
                    "host-only (no business path). The runner will land on "
                    "the home / login page instead of the case's target "
                    "page. Append the real page path resolved during TDRS."
                )
    return rule


def check_test_content_usage(nodes: List[Node]) -> RuleResult:
    rule = RuleResult(
        rule_id="R7_TEST_CONTENT",
        description="`**测试内容**` should be attached to a leaf `测试点` node.",
    )
    for node in nodes:
        matched_lines = []
        for line_no, line in node.body_lines:
            stripped = line.strip()
            if TEST_CONTENT_LINE_RE.match(stripped):
                matched_lines.append(line_no)
        if not matched_lines:
            continue

        if node.node_type != "测试点":
            for line_no in matched_lines:
                rule.add_error(
                    f"Line {line_no}: `**测试内容**` can only appear under a `测试点` node."
                )
        if node.children:
            for line_no in matched_lines:
                rule.add_error(
                    f"Line {line_no}: `**测试内容**` must be attached to a leaf node."
                )
    return rule


def make_output(
    input_file: str, input_format: str, rules: List[RuleResult], supported: bool
) -> Dict[str, object]:
    errors = sum(len(rule.errors) for rule in rules)
    warnings = sum(len(rule.warnings) for rule in rules)
    passed = supported and all(rule.passed for rule in rules)
    if not supported:
        summary = "Input format is recognized but not yet supported."
    elif passed:
        summary = "Grammar check passed."
    else:
        summary = "Grammar check failed."
    return {
        "overall_result": {
            "passed": passed,
            "summary": summary,
            "error_count": errors,
            "warning_count": warnings,
        },
        "detailed_check_result": [
            {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "passed": rule.passed,
                "errors": rule.errors,
                "warnings": rule.warnings,
            }
            for rule in rules
        ],
        "meta": {
            "input_file": str(input_file),
            "input_format": input_format,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file)
    if not input_path.exists():
        result = make_output(
            input_file=args.input_file,
            input_format="unknown",
            rules=[
                RuleResult(
                    rule_id="R_INPUT",
                    description="Input file must exist.",
                    passed=False,
                    errors=[f"Input file not found: {args.input_file}"],
                    warnings=[],
                )
            ],
            supported=False,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    input_format = detect_format(input_path)
    if input_format == "json":
        result = make_output(
            input_file=args.input_file,
            input_format=input_format,
            rules=[
                RuleResult(
                    rule_id="R_INPUT_FORMAT",
                    description="Input format support check.",
                    passed=False,
                    errors=["JSON input is not supported yet. Please provide markdown file."],
                    warnings=[],
                )
            ],
            supported=False,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    if input_format != "markdown":
        result = make_output(
            input_file=args.input_file,
            input_format=input_format,
            rules=[
                RuleResult(
                    rule_id="R_INPUT_FORMAT",
                    description="Input format support check.",
                    passed=False,
                    errors=["Unsupported file extension. Use .md or .markdown."],
                    warnings=[],
                )
            ],
            supported=False,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    text = input_path.read_text(encoding="utf-8")
    nodes, parse_rule = parse_markdown(text)
    rules = [parse_rule]

    if parse_rule.passed:
        rules.extend(
            [
                link_tree(nodes),
                check_node_type(nodes, strict_title=args.strict_title),
                check_special_node_emphasis(nodes),
                check_parent_child_relation(nodes),
                check_leaf_node(nodes),
                check_top_down_order(nodes),
                check_attributes(nodes),
                check_consecutive_operation_steps(nodes),
                check_test_content_usage(nodes),
                check_precondition_url(nodes),
            ]
        )
        if args.analysis_file:
            analysis_path = Path(args.analysis_file)
            if not analysis_path.exists():
                rules.append(
                    RuleResult(
                        rule_id="R10_ANALYSIS_CASE_MAPPING",
                        description="Analysis file must exist when --analysis-file is provided.",
                        passed=False,
                        errors=[f"Analysis file not found: {args.analysis_file}"],
                    )
                )
            else:
                rules.append(
                    check_analysis_case_mapping(nodes, parse_analysis_ids(analysis_path))
                )

    result = make_output(
        input_file=args.input_file,
        input_format=input_format,
        rules=rules,
        supported=True,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall_result"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
