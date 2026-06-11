#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Dict, List


NODE_TYPE_LABEL = {
    12: "**用例标题**",
    3: "**前置条件**",
    5: "**操作步骤**",
    6: "**操作步骤**",
    4: "**预期结果**",
    13: "**预期结果**",
}


def case_tree_to_bits_markdown(node: Dict[str, Any], level: int = 1) -> str:
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    node_type = data.get("nodeType")
    label = NODE_TYPE_LABEL.get(node_type, "")
    text = str(data.get("text") or "").strip()
    if not label and not text:
        text = "（空）"
    elif label and not text:
        text = "（空）"
    text = text.replace("\n", "\\n")
    prefix = "#" * int(level or 1)
    title = f"{prefix} {label} {text}".rstrip()

    body_lines: List[str] = []
    resources = data.get("resource")
    if isinstance(resources, list):
        tags = [str(x).strip() for x in resources if str(x).strip()]
        if tags:
            body_lines.append(f"**[tag]** {','.join(tags)}")

    md = "\n".join([title, *body_lines]).rstrip()
    parts = [md]
    for child in node.get("children") or []:
        if isinstance(child, dict):
            parts.append(case_tree_to_bits_markdown(child, level + 1))
    return "\n".join([p for p in parts if str(p).strip()])
