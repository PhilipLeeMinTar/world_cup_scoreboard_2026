#!/usr/bin/env python3
"""
Transform test case between text and json forms.

Support:
- markdown -> json
- json -> markdown

Output JSON shape (single supported form):
{
  "data": {
    "text": "node content",
    "nodeType": 0,
    "priority": 0,
    "resource": null,
    "hyperlink": "",
    "hyperlinkTitle": ""
  },
  "children": []
}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


HEADER_RE = re.compile(r"^(#{1,})\s*(.*?)\s*$")
TYPE_PREFIX_RE = re.compile(r"^\*\*(测试点|用例标题|前置条件|操作步骤|预期结果)\*\*\s*([:：]?\s*.*)$")
TYPE_PLAIN_RE = re.compile(r"^(测试点|用例标题|前置条件|操作步骤|预期结果)\s+(.+)$")
ATTR_RE = re.compile(r"^\*\*\[(priority|tag|hyperlink)\]\*\*\s*(.+)\s*$")
HYPERLINK_RE = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")
TEST_CONTENT_RE = re.compile(r"^\*\*测试内容\*\*\s*(.*)$")


NODE_TYPE_TO_CODE = {
    "测试点": 0,
    "用例标题": 12,
    "前置条件": 3,
    "操作步骤": 5,
    "预期结果": 4,
}

PRIORITY_TO_CODE = {
    "P0": 99,
    "P1": 1,
    "P2": 2,
    "P3": 3,
}

CODE_TO_NODE_TYPE = {
    0: "测试点",
    2: "测试点",
    3: "前置条件",
    4: "预期结果",
    5: "操作步骤",
    6: "操作步骤",
    12: "用例标题",
    13: "预期结果",
}

CODE_TO_PRIORITY = {
    99: "P0",
    1: "P1",
    2: "P2",
    3: "P3",
}


@dataclass
class Node:
    level: int
    node_type: str
    text: str
    body_lines: List[str] = field(default_factory=list)
    children: List["Node"] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert test case between markdown and json tree forms."
    )
    parser.add_argument("input_file", help="Path to markdown or json file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path. If omitted, print to stdout.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation")
    return parser.parse_args()


def normalize_inline_text(text: str) -> str:
    # Keep compatibility with escaped newlines produced by upstream generation.
    return text.replace("\\n", "\n")


def parse_title(title: str) -> Tuple[str, str]:
    stripped = title.strip()

    prefix_match = TYPE_PREFIX_RE.match(stripped)
    if prefix_match:
        node_type = prefix_match.group(1)
        raw_tail = prefix_match.group(2).strip()
        content = raw_tail.lstrip(":：").strip()
        return node_type, normalize_inline_text(content)

    plain_match = TYPE_PLAIN_RE.match(stripped)
    if plain_match:
        node_type = plain_match.group(1)
        content = plain_match.group(2).strip()
        return node_type, normalize_inline_text(content)

    # Default heading node type is 测试点 ("功能点")
    return "测试点", normalize_inline_text(stripped)


def parse_markdown(markdown_text: str) -> List[Node]:
    nodes: List[Node] = []
    current_node: Optional[Node] = None

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip("\n")
        header_match = HEADER_RE.match(line)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2)
            node_type, text = parse_title(title)
            node = Node(level=level, node_type=node_type, text=text)
            nodes.append(node)
            current_node = node
            continue

        if current_node is not None:
            current_node.body_lines.append(line)

    if not nodes:
        raise ValueError("No markdown heading found. Expected lines starting with '#'.")
    if nodes[0].level != 1:
        raise ValueError("The first markdown heading must start with a single '#'.")

    return nodes


def build_tree(nodes: List[Node]) -> Node:
    stack: List[Node] = []
    for node in nodes:
        while stack and stack[-1].level >= node.level:
            stack.pop()

        if not stack:
            if node is not nodes[0]:
                raise ValueError(f"Invalid hierarchy near node text: {node.text}")
            stack.append(node)
            continue

        parent = stack[-1]
        if node.level != parent.level + 1:
            raise ValueError(
                f"Invalid hierarchy jump near node text: {node.text} (parent level {parent.level}, child level {node.level})"
            )

        parent.children.append(node)
        stack.append(node)

    return nodes[0]


def extract_node_meta_and_text(node: Node) -> Tuple[int, Optional[List[str]], str, str, List[str]]:
    priority_code = 0
    resources: Optional[List[str]] = None
    hyperlink = ""
    hyperlink_title = ""
    extra_text_lines: List[str] = []

    for raw_line in node.body_lines:
        line = raw_line.strip()
        if not line:
            continue

        attr_match = ATTR_RE.match(line)
        if attr_match:
            key, value = attr_match.group(1), attr_match.group(2).strip()
            if key == "priority":
                priority_code = PRIORITY_TO_CODE.get(value, 0)
            elif key == "tag":
                tags = [part.strip() for part in value.split(",") if part.strip()]
                resources = tags or None
            elif key == "hyperlink":
                link_match = HYPERLINK_RE.match(value)
                if link_match:
                    hyperlink_title = link_match.group(1).strip()
                    hyperlink = link_match.group(2).strip()
            continue

        test_content_match = TEST_CONTENT_RE.match(line)
        if test_content_match:
            tail = test_content_match.group(1).strip()
            if tail:
                extra_text_lines.append(normalize_inline_text(tail))
            continue

        extra_text_lines.append(normalize_inline_text(line))

    return priority_code, resources, hyperlink, hyperlink_title, extra_text_lines


def to_json_node(node: Node) -> dict:
    priority, resource, hyperlink, hyperlink_title, extra_lines = extract_node_meta_and_text(node)

    text_parts: List[str] = []
    if node.text:
        text_parts.append(node.text)
    text_parts.extend(extra_lines)

    json_node = {
        "data": {
            "text": "\n".join(text_parts).strip(),
            "nodeType": NODE_TYPE_TO_CODE[node.node_type],
            "priority": priority,
            "resource": resource,
            "hyperlink": hyperlink,
            "hyperlinkTitle": hyperlink_title,
        },
        "children": [to_json_node(child) for child in node.children],
    }
    return json_node


def markdown_to_json_tree(markdown_text: str) -> dict:
    flat_nodes = parse_markdown(markdown_text)
    root = build_tree(flat_nodes)
    return to_json_node(root)


def split_text_lines(text: str) -> List[str]:
    normalized = normalize_inline_text(text)
    if not normalized:
        return []
    return normalized.splitlines()


def extract_json_node_fields(node: dict) -> Tuple[dict, List[dict]]:
    if not isinstance(node, dict):
        raise TypeError(f"Expected json node to be dict, got {type(node).__name__}")

    data = node.get("data")
    if not isinstance(data, dict):
        raise TypeError("JSON node missing `data` object.")

    raw_children = node.get("children")
    if raw_children in (None, []):
        children: List[dict] = []
    elif isinstance(raw_children, list):
        children = raw_children
    else:
        raise TypeError("JSON node `children` must be a list, null, or omitted.")

    return data, children


def build_heading(level: int, node_type: str, text_lines: List[str]) -> str:
    prefix = "#" * level
    first_line = text_lines[0] if text_lines else ""
    if node_type == "测试点":
        return f"{prefix} {first_line}".rstrip()
    if first_line:
        return f"{prefix} **{node_type}** {first_line}"
    return f"{prefix} **{node_type}**"


def json_node_to_markdown_lines(node: dict, level: int = 1) -> List[str]:
    data, children = extract_json_node_fields(node)

    raw_text = data.get("text")
    if raw_text is None:
        raw_text = ""
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)

    node_type_code = data.get("nodeType", 0)
    if not isinstance(node_type_code, int):
        raise TypeError("JSON node `data.nodeType` must be an integer.")
    node_type = CODE_TO_NODE_TYPE.get(node_type_code)
    if node_type is None:
        raise ValueError(f"Unsupported nodeType code: {node_type_code}")

    text_lines = split_text_lines(raw_text)
    lines = [build_heading(level, node_type, text_lines)]

    priority = data.get("priority", 0)
    if isinstance(priority, int) and priority in CODE_TO_PRIORITY:
        lines.append(f"**[priority]** {CODE_TO_PRIORITY[priority]}")

    resource = data.get("resource")
    if isinstance(resource, list):
        tags = [str(item).strip() for item in resource if str(item).strip()]
        if tags:
            lines.append(f"**[tag]** {','.join(tags)}")

    hyperlink = data.get("hyperlink", "")
    hyperlink_title = data.get("hyperlinkTitle", "")
    if hyperlink:
        title = str(hyperlink_title).strip() or str(hyperlink).strip()
        lines.append(f"**[hyperlink]** [{title}]({str(hyperlink).strip()})")

    extra_text_lines = text_lines[1:]
    if extra_text_lines:
        lines.extend(extra_text_lines)

    for child in children:
        lines.extend(json_node_to_markdown_lines(child, level + 1))

    return lines


def json_to_markdown_tree(tree: dict) -> str:
    return "\n".join(json_node_to_markdown_lines(tree)).strip()


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    raise ValueError(f"Unsupported input file type: {path.suffix or '<no suffix>'}")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    input_format = detect_format(input_path)
    text = input_path.read_text(encoding="utf-8")

    if input_format == "markdown":
        tree = markdown_to_json_tree(text)
        output = json.dumps(tree, ensure_ascii=False, indent=args.indent)
    else:
        tree = json.loads(text)
        output = json_to_markdown_tree(tree)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
