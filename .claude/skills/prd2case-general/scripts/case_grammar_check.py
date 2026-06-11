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
ATTR_RE = re.compile(r"^\*\*\[(priority|tag|hyperlink|img)\]\*\*:?\s*(.+)\s*$")
HYPERLINK_RE = re.compile(r"^\[[^\]]+\]\([^)]+\)$")
TEST_CONTENT_LINE_RE = re.compile(r"^\*\*测试内容\*\*\s*(.+)\s*$")


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
        description="Check attribute line format for priority/tag/hyperlink/img.",
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
            if key == "img" and not value:
                rule.add_error(f"Line {line_no}: img attribute must provide a non-empty image url.")
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
            ]
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
