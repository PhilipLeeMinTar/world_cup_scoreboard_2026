#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


NODE_TYPE_LABEL: Dict[int, str] = {
    12: "用例标题",
    3: "前置条件",
    5: "操作步骤",
    6: "操作步骤",
    4: "预期结果",
    13: "预期结果",
}

_ID_SUFFIX_RE = re.compile(r"\s*\[id=[^\]]+\]\s*$")
_MATCH_WS_RE = re.compile(r"\s+")
_MATCH_ZWS_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def _node_text(data: Dict[str, Any], default: str = "-") -> str:
    raw_text = data.get("text", default)
    if raw_text is None:
        return default
    text = str(raw_text).strip()
    return text or default


def _clean_case_tree(node: Any) -> Any:
    if not isinstance(node, dict):
        return None
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    children = node.get("children")
    if not isinstance(children, list):
        children = []
    cleaned_children = []
    for c in children:
        cc = _clean_case_tree(c)
        if cc is not None:
            cleaned_children.append(cc)
    out = {"data": dict(data), "children": cleaned_children}
    for k, v in node.items():
        if k in ("data", "children"):
            continue
        out[k] = v
    return out


def segment_tree_by_node(
    tree: Dict[str, Any],
    *,
    segment_node_type: int = 3,
    on_not_found: str = "empty",
    keep_prefix: bool = False,
) -> List[Dict[str, Any]]:
    if not tree:
        return []
    segments: List[Dict[str, Any]] = []

    def dfs(node: Dict[str, Any], path: List[Dict[str, Any]]) -> None:
        if not node:
            return
        current_path = path + [node]
        node_data = node.get("data", {}) or {}
        current_node_type = node_data.get("nodeType")
        if current_node_type == segment_node_type:
            segment = json.loads(json.dumps(node, ensure_ascii=False))
            if keep_prefix:
                prefix = [_node_text(n.get("data", {}) or {}) for n in current_path]
                segment["prefix"] = prefix
            segments.append(segment)
            return
        for child in node.get("children", []) or []:
            if isinstance(child, dict):
                dfs(child, current_path)

    dfs(tree, [])
    if not segments:
        if on_not_found == "origin":
            segment = json.loads(json.dumps(tree, ensure_ascii=False))
            if keep_prefix:
                segment["prefix"] = [_node_text(tree.get("data", {}) or {})]
            return [segment]
        if on_not_found == "empty":
            return []
        raise ValueError("on_not_found must be 'empty' or 'origin'")
    return segments


def _tree_to_text(node: Dict[str, Any], *, include_ids: bool, max_lines: int = 2500) -> str:
    lines: List[str] = []

    def dfs(n: Dict[str, Any], level: int) -> None:
        if max_lines > 0 and len(lines) >= max_lines:
            return
        data = n.get("data") or {}
        text = _node_text(data)
        node_type = data.get("nodeType")
        node_id = data.get("id")
        label = NODE_TYPE_LABEL.get(int(node_type)) if isinstance(node_type, int) else None
        prefix = "  " * max(level, 0)
        meta = ""
        if include_ids and node_id is not None:
            meta = f" [id={node_id}]"
        if label:
            lines.append(f"{prefix}{label}{meta} {text}".rstrip())
        else:
            lines.append(f"{prefix}{text}{meta}".rstrip())
        if max_lines > 0 and len(lines) >= max_lines:
            return
        for child in n.get("children") or []:
            if isinstance(child, dict):
                dfs(child, level + 1)

    dfs(node, 0)
    return "\n".join([l for l in lines if l.strip()])


def _md_collect_headings(md: str) -> List[Dict[str, Any]]:
    """
    Collect markdown headings with their level and line index.
    """
    out: List[Dict[str, Any]] = []
    for i, raw in enumerate(md.splitlines()):
        line = raw.rstrip("\n")
        if not line.startswith("#"):
            continue
        j = 0
        while j < len(line) and line[j] == "#":
            j += 1
        if j <= 0:
            continue
        title = line[j:].strip()
        out.append({"level": j, "line": i, "text": title})
    return out


def _md_slice_block_by_heading(md: str, headings: List[Dict[str, Any]], idx: int) -> str:
    """
    Slice a markdown block starting from headings[idx] until the next heading
    with level <= current level (or end of file).
    """
    lines = md.splitlines()
    start = int(headings[idx]["line"])
    level = int(headings[idx]["level"])
    end = len(lines)
    for j in range(idx + 1, len(headings)):
        if int(headings[j]["level"]) <= level:
            end = int(headings[j]["line"])
            break
    return "\n".join(lines[start:end]).rstrip()


def _preorder_collect_nodes_with_indices(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Preorder traversal of JSON tree and return the node list (dicts) in order.
    """
    nodes: List[Dict[str, Any]] = []

    def walk(n: Dict[str, Any]) -> None:
        if not isinstance(n, dict):
            return
        nodes.append(n)
        for ch in n.get("children") or []:
            if isinstance(ch, dict):
                walk(ch)

    walk(tree)
    return nodes


def _map_json_nodes_to_markdown_blocks(tree: Dict[str, Any], md: str) -> Dict[int, str]:
    """
    Map each JSON node (by its id() at runtime) to the markdown block of the
    same preorder position.
    Assumes the markdown is rendered by a preorder json->markdown process.
    """
    nodes = _preorder_collect_nodes_with_indices(tree)
    headings = _md_collect_headings(md)
    mapping: Dict[int, str] = {}
    count = min(len(nodes), len(headings))
    for i in range(count):
        block = _md_slice_block_by_heading(md, headings, i)
        mapping[id(nodes[i])] = block
    return mapping


def _extract_paths_to_expectations(pc_tree: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
    out: List[List[Dict[str, Any]]] = []

    def walk(node: Dict[str, Any], path: List[Dict[str, Any]]) -> None:
        data = node.get("data") or {}
        nt = data.get("nodeType")
        new_path = path + [node]
        if nt in (4, 13):
            out.append(new_path)
            return
        for child in node.get("children") or []:
            if isinstance(child, dict):
                walk(child, new_path)

    walk(pc_tree, [])
    return out


def _get_parent_chain_texts(root: Dict[str, Any], target: Dict[str, Any]) -> List[str]:
    """
    Build parent chain texts from root to parent(target). Used as prefix context.
    """
    path: List[Dict[str, Any]] = []
    found = False

    def walk(n: Dict[str, Any], stk: List[Dict[str, Any]]) -> None:
        nonlocal path, found
        if found:
            return
        ns = stk + [n]
        if n is target:
            path = ns
            found = True
            return
        for ch in n.get("children") or []:
            if isinstance(ch, dict):
                walk(ch, ns)

    walk(root, [])
    out: List[str] = []
    for n in path[:-1]:
        data = n.get("data") or {}
        txt = str(data.get("text") or "").strip()
        if txt:
            out.append(txt)
    return out


def _format_bits_path_text(path_nodes: List[Dict[str, Any]], *, include_ids: bool = True) -> str:
    lines: List[str] = []
    for n in path_nodes:
        data = n.get("data") or {}
        nt = data.get("nodeType")
        nid = data.get("id")
        text = _node_text(data)
        label = NODE_TYPE_LABEL.get(int(nt)) if isinstance(nt, int) else None
        meta = f" [id={nid}]" if include_ids and nid is not None else ""
        if label:
            lines.append(f"{label}: {text}{meta}")
        else:
            lines.append(f"{text}{meta}")
    return "\n".join([l for l in lines if l.strip()])


def _format_bits_path_text_with_prefix(prefix: List[Any], path_nodes: List[Dict[str, Any]], *, include_ids: bool = True) -> str:
    lines: List[str] = []
    for i, p in enumerate(prefix or []):
        p = str(p).strip()
        if p:
            lines.append(f"前缀层级{i+1}: {p}")
    lines.extend([ln for ln in _format_bits_path_text(path_nodes, include_ids=include_ids).splitlines() if ln.strip()])
    return "\n".join(lines)


def _extract_expectation_text(path_text: str) -> str:
    lines = [ln.strip() for ln in (path_text or "").splitlines() if ln.strip()]
    exp_lines: List[str] = []
    start_idx: Optional[int] = None
    for idx in range(len(lines) - 1, -1, -1):
        ln = lines[idx]
        if ln.startswith("预期结果:") or ln.lower().startswith("expected:"):
            start_idx = idx
            break
    if start_idx is not None:
        first = lines[start_idx]
        exp_lines.append(first.split(":", 1)[1].strip() if ":" in first else "")
        exp_lines.extend(lines[start_idx + 1 :])
    elif lines:
        exp_lines.append(lines[-1])
    exp = "\n".join([ln for ln in exp_lines if ln.strip()])
    return _ID_SUFFIX_RE.sub("", exp).strip()


def _normalize_text_for_match(text: Any) -> str:
    s = str(text or "")
    if not s:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _MATCH_ZWS_RE.sub("", s)
    s = _MATCH_WS_RE.sub(" ", s)
    return s.strip()


def _infer_expectation_type(path_text: str, expectation_text: str) -> str:
    return "semantic_review"


def _build_judge_steps(expectation_type: str) -> List[str]:
    return [
        "先用 human_pc_slice 和 path_text 总结人工路径的测试意图，不要直接下结论。",
        "不要依赖 expectation_type 或 type_override_allowed 做预分类；它们只为兼容输出结构保留，必须直接根据人工路径本身判断它在检查什么对象，以及该对象是否能由主流程自然推出。",
        "先区分人工路径检查的是用户可见业务结果，还是 UI细节、否定/消失约束、接口字段/错误码、埋点日志、权限、配置/风控规则等独立契约。只有当 AI 证据与人工预期在同一粒度时，才允许判 covered=true。",
        "如果人工路径挂在某个入口（如 Feedbanner/弹窗/卡片）下，先判断它检查的是入口自身展示、按钮、频控、埋点等入口表面对象，还是点击该入口后的下游业务结果。前者必须命中入口同粒度证据；后者不能仅因缺少入口表面证据就直接判未覆盖。",
        "如果人工预期主要检查用户可见业务结果，则在 AI 证据明确验证同一用户动作、同一核心功能结果和关键条件时，允许按语义等价判 covered=true；不要求措辞或步骤逐字一致。",
        "如果 AI 证据已经明确命中最终业务结果，只缺少中间描述、附带说明或非核心修饰，不要仅因 wording 更短就判未覆盖。",
        "对配置/实验驱动但最终是用户可见结果的路径，要按真实测试意图判断；若 AI 明确验证的是同一业务规则生效后的结果，可接受数值不同，但不能把真正的配置字段/规则校验误放宽。",
        "优先在 ai_modules 中查找同模块或相关模块的明确证据；如果入口同名模块证据较弱，但人工检查的是入口后的业务结果，必须继续向下游页面/流程相关模块和 ai_full_text 做语义检索，不要停在入口表面对象上。只有在这些检索都做完后，才允许判 covered=false。",
        "同模块、同页面、同功能域只能帮助缩小搜索范围，本身不是覆盖证据；不能用泛化主流程结果吸收 UI 细节、否定约束、埋点、接口或内部契约检查点。",
        "自检只做轻量误覆盖审计：优先复查 covered=true 里高风险项（UI细节、负向/消失、接口/字段/错误码、埋点、权限、内部规则）以及被大量复用的 ai_evidence；不要因为自检而整体下调普通业务结果类路径。",
        "如果很多路径都用同一段 ai_evidence 判 covered=true，要停下来复查这些复用证据；如果很多路径都用同一类 reason 模板判 covered=false，也要复查是否把自检错误地做成了第二轮整体收紧。",
        "本次 judgement 只能读取当前输入并写 coverage_result.json（或必要的结果文件）；严禁生成任何额外代码文件，也严禁修改当前项目中的现有代码文件。",
    ]


def _build_module_key_from_prefix(prefix: List[Any]) -> str:
    parts = [str(p).strip() for p in (prefix or [])[:-1] if str(p or "").strip()]
    return " > ".join(parts)


def _extract_ai_modules(
    ai_tree: Dict[str, Any],
    *,
    include_ids: bool,
    module_max_lines: int,
) -> Dict[str, str]:
    modules: Dict[str, str] = {}

    for path_nodes in _extract_paths_to_expectations(ai_tree):
        first_labeled_idx = None
        for i, node in enumerate(path_nodes):
            node_type = (node.get("data") or {}).get("nodeType")
            if node_type in NODE_TYPE_LABEL:
                first_labeled_idx = i
                break
        if first_labeled_idx is None:
            module_nodes = path_nodes
            module_node = path_nodes[-1]
        elif first_labeled_idx <= 0:
            module_nodes = path_nodes[:1]
            module_node = path_nodes[0]
        else:
            module_nodes = path_nodes[:first_labeled_idx]
            module_node = path_nodes[first_labeled_idx - 1]

        module_prefix = [_node_text(n.get("data") or {}) for n in module_nodes]
        module_key = " > ".join(module_prefix)
        if module_key and module_key not in modules:
            modules[module_key] = _tree_to_text(module_node, include_ids=include_ids, max_lines=module_max_lines)

    return modules


def _extract_ai_modules_from_markdown(
    ai_tree: Dict[str, Any],
    ai_md: str,
    *,
    module_max_lines: int,
) -> Dict[str, str]:
    """
    Build AI modules using markdown blocks (preserve heading structure).
    """
    modules: Dict[str, str] = {}
    md_blocks = _map_json_nodes_to_markdown_blocks(ai_tree, ai_md)

    for path_nodes in _extract_paths_to_expectations(ai_tree):
        first_labeled_idx = None
        for i, node in enumerate(path_nodes):
            node_type = (node.get("data") or {}).get("nodeType")
            if node_type in NODE_TYPE_LABEL:
                first_labeled_idx = i
                break
        if first_labeled_idx is None:
            module_nodes = path_nodes
            module_node = path_nodes[-1]
        elif first_labeled_idx <= 0:
            module_nodes = path_nodes[:1]
            module_node = path_nodes[0]
        else:
            module_nodes = path_nodes[:first_labeled_idx]
            module_node = path_nodes[first_labeled_idx - 1]

        module_prefix = [str((n.get("data") or {}).get("text") or "").strip() for n in module_nodes if str((n.get("data") or {}).get("text") or "").strip()]
        module_key = " > ".join(module_prefix)
        if not module_key or module_key in modules:
            continue
        block = md_blocks.get(id(module_node)) or ""
        if module_max_lines > 0:
            block_lines = [ln for ln in block.splitlines() if ln.strip()]
            block = "\n".join(block_lines[:module_max_lines])
        modules[module_key] = block
    return modules


def _detect_lang(text: str) -> str:
    s = str(text or "")
    if not s.strip():
        return "unknown"
    cjk = sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in s if ("a" <= ch.lower() <= "z"))
    if cjk == 0 and latin == 0:
        return "unknown"
    if cjk > 0 and latin == 0:
        return "zh"
    if latin > 0 and cjk == 0:
        return "en"
    return "mixed"


def _read_case_mind_from_fetch_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    data = resp.get("data")
    if not isinstance(data, dict):
        raise ValueError("invalid fetch response: missing data")
    case_data = data.get("case_data")
    if not isinstance(case_data, dict):
        raise ValueError("invalid fetch response: missing data.case_data")
    return case_data


def build_coverage_inputs(
    *,
    ai_case_url: str,
    human_case_url: str,
    ai_tree: Dict[str, Any],
    human_tree: Dict[str, Any],
    include_ai_ids: bool,
    include_prefix_in_path_text: bool,
    merge_size: int,
    batch_chunk: int,
    ai_module_max_lines: int,
    ai_md_text: Optional[str] = None,
    human_md_text: Optional[str] = None,
) -> Dict[str, Any]:
    ai_tree = _clean_case_tree(ai_tree)
    human_tree = _clean_case_tree(human_tree)
    if not isinstance(ai_tree, dict) or not isinstance(human_tree, dict):
        raise ValueError("invalid case tree")

    # Prefer markdown (if provided) to preserve heading structure; fallback to JSON->text
    ai_md = (ai_md_text or "").strip()
    human_md = (human_md_text or "").strip()

    if ai_md:
        ai_full_text = "\n".join([ln for ln in ai_md.splitlines()][:2500])
        ai_modules = _extract_ai_modules_from_markdown(
            ai_tree,
            ai_md,
            module_max_lines=max(50, int(ai_module_max_lines or 0)),
        )
    else:
        ai_full_text = _tree_to_text(ai_tree, include_ids=bool(include_ai_ids), max_lines=2500)
        ai_modules = _extract_ai_modules(
            ai_tree,
            include_ids=bool(include_ai_ids),
            module_max_lines=max(50, int(ai_module_max_lines or 0)),
        )
    ai_lang = _detect_lang(ai_full_text)

    pc_work: List[Dict[str, Any]] = []
    pc_slices_by_id: Dict[str, str] = {}
    total_paths_all = 0
    pc_slices = segment_tree_by_node(human_tree, segment_node_type=3, on_not_found="empty", keep_prefix=True)
    for pc in pc_slices:
        manual_slice_text = _tree_to_text(pc, include_ids=True, max_lines=2500)
        paths = _extract_paths_to_expectations(pc)
        if not paths:
            continue
        pc_work.append({"pc": pc, "manual_slice_text": manual_slice_text, "paths": paths})
        pc_node_id = (pc.get("data") or {}).get("id")
        if pc_node_id is not None and manual_slice_text.strip():
            pc_slices_by_id[str(pc_node_id)] = manual_slice_text
        total_paths_all += len(paths)

    planned_total_paths = total_paths_all

    predictions: List[Dict[str, Any]] = []
    path_seq = 0
    for w in pc_work:
        pc = w["pc"]
        paths = w["paths"]
        # Build prefix: prefer existing prefix from segment_tree_by_node; otherwise compute from JSON chain
        prefix = pc.get("prefix") or _get_parent_chain_texts(human_tree, pc)
        for path_nodes in paths:
            path_seq += 1
            path_node_ids = [
                str((n.get("data") or {}).get("id"))
                for n in path_nodes
                if (n.get("data") or {}).get("id") is not None
            ]
            expectation_node_id = None
            if path_nodes:
                last_id = (path_nodes[-1].get("data") or {}).get("id")
                expectation_node_id = str(last_id) if last_id is not None else None

            path_text = (
                _format_bits_path_text_with_prefix(prefix, path_nodes, include_ids=True)
                if include_prefix_in_path_text
                else _format_bits_path_text(path_nodes, include_ids=True)
            )
            expectation_text = _extract_expectation_text(path_text)
            expectation_lang = _detect_lang(expectation_text)
            expectation_type = _infer_expectation_type(path_text, expectation_text)
            module_fallback_key = _build_module_key_from_prefix(prefix)

            predictions.append(
                {
                    "path_id": str(path_seq),
                    "pc_node_id": (pc.get("data") or {}).get("id"),
                    "expectation_node_id": expectation_node_id,
                    "path_node_ids": path_node_ids,
                    "prefix": prefix,
                    "path_text": path_text,
                    "expectation_text": expectation_text,
                    "expectation_lang": expectation_lang,
                    "expectation_type": expectation_type,
                    "judge_steps": _build_judge_steps(expectation_type),
                    "module_fallback_key": module_fallback_key,
                    "type_override_allowed": False,
                    "model": None,
                }
            )

    return {
        "meta": {
            "ai_case_url": ai_case_url,
            "human_case_url": human_case_url,
            "total_paths_all": total_paths_all,
            "planned_total_paths": planned_total_paths,
            "merge_size": int(merge_size or 0),
            "batch_chunk": int(batch_chunk or 0),
            "include_ai_ids": bool(include_ai_ids),
            "include_prefix_in_path_text": bool(include_prefix_in_path_text),
            "ai_lang": ai_lang,
            "ai_module_count": len(ai_modules),
            "ai_module_max_lines": int(ai_module_max_lines or 0),
            "judge_strategy": "module_first_global_fallback",
        },
        "ai_full_text": ai_full_text,
        "human_pc_slices": pc_slices_by_id,
        "predictions": predictions,
    }


def _compute_summary(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    decided: List[bool] = []
    for it in predictions:
        model = it.get("model")
        if isinstance(model, dict) and isinstance(model.get("covered"), bool):
            decided.append(model["covered"])
    covered_num = len([v for v in decided if v is True])
    decided_num = len(decided)
    coverage_rate = covered_num / decided_num if decided_num else 0.0
    return {
        "total_paths": len(predictions),
        "decided_paths": decided_num,
        "covered_paths": covered_num,
        "undecided_paths": len(predictions) - decided_num,
        "coverage_rate": coverage_rate,
    }


def merge_result_files(paths: List[Path]) -> Dict[str, Any]:
    predictions: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}
    for p in paths:
        obj = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            continue
        if not meta and isinstance(obj.get("meta"), dict):
            meta = obj["meta"]
        preds = obj.get("predictions")
        if isinstance(preds, list):
            for it in preds:
                if isinstance(it, dict):
                    predictions.append(it)

    by_id: Dict[str, Dict[str, Any]] = {}
    for it in predictions:
        pid = it.get("path_id")
        if isinstance(pid, str) and pid:
            by_id[pid] = it

    merged = [by_id[k] for k in sorted(by_id.keys(), key=lambda x: int(x) if x.isdigit() else x)]
    return {"meta": meta, "summary": _compute_summary(merged), "predictions": merged}


def _index_nodes_by_id(tree: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}

    def walk(node: Dict[str, Any]) -> None:
        data = node.get("data") or {}
        nid = data.get("id")
        if nid is not None:
            out[str(nid)] = node
        for ch in node.get("children") or []:
            if isinstance(ch, dict):
                walk(ch)

    walk(tree)
    return out


def _build_path_id_to_expectation_node_id(coverage_inputs: Dict[str, Any]) -> Dict[str, str]:
    preds = coverage_inputs.get("predictions")
    if not isinstance(preds, list):
        return {}
    out: Dict[str, str] = {}
    for it in preds:
        if not isinstance(it, dict):
            continue
        pid = it.get("path_id")
        nid = it.get("expectation_node_id")
        if isinstance(pid, str) and isinstance(nid, str) and pid and nid:
            out[pid] = nid
    return out


def fill_expectation_node_ids_in_predictions(
    predictions: List[Dict[str, Any]],
    *,
    coverage_inputs: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not coverage_inputs:
        return predictions
    mapping = _build_path_id_to_expectation_node_id(coverage_inputs)
    if not mapping:
        return predictions
    for it in predictions:
        if not isinstance(it, dict):
            continue
        if it.get("expectation_node_id") is not None:
            continue
        pid = it.get("path_id")
        if isinstance(pid, str) and pid in mapping:
            it["expectation_node_id"] = mapping[pid]
    return predictions


def annotate_human_case_tree(
    human_tree: Dict[str, Any],
    predictions: List[Dict[str, Any]],
    *,
    field_name: str = "coverage",
    write_bits_fields: bool = True,
) -> Dict[str, Any]:
    def norm_tag(s: Any, *, prefix: str) -> str:
        txt = str(s or "").strip().replace("\n", " ").replace("\r", " ")
        txt = " ".join(txt.split())
        if not txt:
            return ""
        max_len = 80
        if len(txt) > max_len:
            txt = txt[: max_len - 1] + "…"
        return f"{prefix}{txt}"

    idx = _index_nodes_by_id(human_tree)
    for it in predictions:
        if not isinstance(it, dict):
            continue
        nid = it.get("expectation_node_id")
        if nid is None:
            continue
        node = idx.get(str(nid))
        if not isinstance(node, dict):
            continue
        model = it.get("model") if isinstance(it.get("model"), dict) else {}
        node[field_name] = {
            "path_id": it.get("path_id"),
            "covered": model.get("covered") if isinstance(model.get("covered"), bool) else None,
            "reason": model.get("reason") or "",
            "evidence": model.get("evidence") if isinstance(model.get("evidence"), list) else [],
        }
        if write_bits_fields:
            data = node.get("data")
            if isinstance(data, dict):
                covered = model.get("covered") if isinstance(model.get("covered"), bool) else None
                if covered is True:
                    tags = ["覆盖"]
                    ev_list = model.get("evidence") if isinstance(model.get("evidence"), list) else []
                    explain = ""
                    if ev_list and isinstance(ev_list[0], dict):
                        explain = str(ev_list[0].get("explain") or "").strip()
                    t = norm_tag(explain, prefix="依据:")
                    if t:
                        tags.append(t)
                    data["resource"] = tags
                elif covered is False:
                    tags = ["未覆盖"]
                    reason = str(model.get("reason") or "").strip()
                    t = norm_tag(reason, prefix="原因:")
                    if t:
                        tags.append(t)
                    data["resource"] = tags
                else:
                    data["resource"] = []
    return human_tree


def _read_case_mind_from_any(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict) and isinstance(obj.get("data"), dict) and isinstance(obj.get("children"), list):
        return obj
    if isinstance(obj, dict) and isinstance(obj.get("code"), int) and isinstance(obj.get("data"), dict):
        return _read_case_mind_from_fetch_response(obj)
    raise ValueError("case json must be a Bits case_mind tree or fetch response")


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _chunked(seq: List[Any], size: int) -> List[List[Any]]:
    size = max(1, int(size or 0))
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def _read_predictions_from_result(result_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    preds = result_obj.get("predictions")
    if not isinstance(preds, list):
        return []
    return [x for x in preds if isinstance(x, dict)]


def _cmd_prepare(args: argparse.Namespace) -> int:
    ai_case_url = str(getattr(args, "ai_case_url", "") or "").strip()
    human_case_url = str(getattr(args, "human_case_url", "") or "").strip()

    if args.ai_case_json and args.human_case_json:
        ai_tree = _read_case_mind_from_any(_load_json(args.ai_case_json))
        human_tree = _read_case_mind_from_any(_load_json(args.human_case_json))
    else:
        raise SystemExit("prepare requires --ai-case-json and --human-case-json (export the Bits case JSON first)")

    # Optional markdown inputs prepared by external converter (case_form_transfer.py)
    ai_md_text = ""
    human_md_text = ""
    if getattr(args, "ai_case_md", ""):
        p = Path(args.ai_case_md)
        if p.is_file():
            ai_md_text = p.read_text(encoding="utf-8")
    if getattr(args, "human_case_md", ""):
        p = Path(args.human_case_md)
        if p.is_file():
            human_md_text = p.read_text(encoding="utf-8")

    inputs = build_coverage_inputs(
        ai_case_url=ai_case_url,
        human_case_url=human_case_url,
        ai_tree=ai_tree,
        human_tree=human_tree,
        include_ai_ids=bool(args.include_ai_ids),
        include_prefix_in_path_text=bool(args.include_prefix_in_path_text),
        merge_size=int(args.merge_size),
        batch_chunk=int(args.batch_chunk),
        ai_module_max_lines=int(args.ai_module_max_lines),
        ai_md_text=ai_md_text,
        human_md_text=human_md_text,
    )
    out_json = Path(args.out_json)
    ai_modules_json = out_json.with_name("ai_modules.json")
    # Use markdown-based modules when available, fallback to JSON-based
    if ai_md_text.strip():
        ai_modules = _extract_ai_modules_from_markdown(
            _clean_case_tree(ai_tree),
            ai_md_text,
            module_max_lines=max(50, int(args.ai_module_max_lines or 0)),
        )
    else:
        ai_modules = _extract_ai_modules(
            _clean_case_tree(ai_tree),
            include_ids=bool(args.include_ai_ids),
            module_max_lines=max(50, int(args.ai_module_max_lines or 0)),
        )
    ai_modules_json.write_text(json.dumps(ai_modules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inputs.setdefault("meta", {})["ai_modules_json"] = ai_modules_json.name
    out_json.write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared inputs: {out_json.resolve()}")
    print(f"Prepared AI modules: {ai_modules_json.resolve()}")
    print(json.dumps(inputs.get("meta") or {}, ensure_ascii=False, indent=2))

    chunk_size = int(args.chunk_size or 0)
    if chunk_size > 0:
        parts_dir = out_json.with_name(out_json.stem + "_parts")
        parts_dir.mkdir(parents=True, exist_ok=True)
        preds = inputs.get("predictions") if isinstance(inputs.get("predictions"), list) else []
        chunks = _chunked(preds, chunk_size)
        total = len(chunks)
        for idx, chunk in enumerate(chunks, start=1):
            relevant_pc_ids = {
                str(it.get("pc_node_id"))
                for it in chunk
                if isinstance(it, dict) and it.get("pc_node_id") is not None
            }
            human_pc_slices = inputs.get("human_pc_slices") if isinstance(inputs.get("human_pc_slices"), dict) else {}
            part = {
                "meta": dict(inputs.get("meta") or {}),
                "human_pc_slices": {k: v for k, v in human_pc_slices.items() if k in relevant_pc_ids},
                "predictions": chunk,
            }
            part["meta"]["part_index"] = idx
            part["meta"]["part_total"] = total
            part["meta"]["part_size"] = len(chunk)
            part["meta"]["part_scope_human_pc_count"] = len(part["human_pc_slices"])
            part["meta"]["part_scope_ai_module_count"] = len(ai_modules)
            part["meta"]["ai_modules_json"] = os.path.relpath(ai_modules_json, start=parts_dir)
            part["meta"]["global_fallback_coverage_inputs_json"] = os.path.relpath(out_json, start=parts_dir)
            part_path = parts_dir / f"coverage_inputs_part_{idx:03d}.json"
            part_path.write_text(json.dumps(part, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Prepared chunked inputs dir: {parts_dir.resolve()}")
    return 0


def _cmd_merge(args: argparse.Namespace) -> int:
    results_dir = Path(args.results_dir)
    paths = sorted(results_dir.glob("coverage_result_part_*.json"))
    if not paths:
        raise SystemExit("no coverage_result_part_*.json found")
    merged = merge_result_files(paths)
    out = Path(args.out_json)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(merged.get("summary") or {}, ensure_ascii=False, indent=2))
    return 0


def _cmd_annotate(args: argparse.Namespace) -> int:
    cov = _load_json(args.coverage_result_json)
    if not isinstance(cov, dict):
        raise SystemExit("coverage-result-json must be a JSON object")
    predictions = _read_predictions_from_result(cov)

    coverage_inputs = _load_json(args.coverage_inputs_json) if args.coverage_inputs_json else None
    if not isinstance(coverage_inputs, dict):
        coverage_inputs = None
    predictions = fill_expectation_node_ids_in_predictions(predictions, coverage_inputs=coverage_inputs)

    if not args.human_case_json:
        raise SystemExit("annotate requires --human-case-json (export the human Bits case JSON first)")
    human_tree = _read_case_mind_from_any(_load_json(args.human_case_json))

    annotated = annotate_human_case_tree(human_tree, predictions, field_name="coverage", write_bits_fields=True)
    out = Path(args.out_annotated_json)
    out.write_text(json.dumps(annotated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote annotated human case: {out.resolve()}")
    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Coverage rate tools (prepare/merge/annotate/upload).")
    sub = p.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="Fetch AI/Human cases and generate coverage_inputs.json (+ parts).")
    prepare.add_argument("--ai-case-url", default="")
    prepare.add_argument("--human-case-url", default="")
    prepare.add_argument("--ai-case-json", default="", help="Local AI case JSON (fetch response or case_mind tree).")
    prepare.add_argument("--human-case-json", default="", help="Local human case JSON (fetch response or case_mind tree).")
    prepare.add_argument("--ai-case-md", default="", help="Optional AI case markdown (converted externally).")
    prepare.add_argument("--human-case-md", default="", help="Optional human case markdown (converted externally).")
    prepare.add_argument("--out-json", default="coverage_inputs.json")
    prepare.add_argument("--chunk-size", type=int, default=100)
    prepare.add_argument("--merge-size", type=int, default=10)
    prepare.add_argument("--batch-chunk", type=int, default=10)
    prepare.add_argument("--ai-module-max-lines", type=int, default=120)
    prepare.add_argument("--include-ai-ids", action="store_true")
    prepare.add_argument("--include-prefix-in-path-text", action="store_true")

    merge = sub.add_parser("merge", help="Merge coverage_result_part_*.json into a single coverage_result.json.")
    merge.add_argument("--results-dir", required=True)
    merge.add_argument("--out-json", default="coverage_result.json")

    annotate = sub.add_parser("annotate", help="Annotate human case tree with resource tags (write annotated JSON).")
    annotate.add_argument("--coverage-result-json", required=True)
    annotate.add_argument("--coverage-inputs-json", default="")
    annotate.add_argument("--human-case-json", default="")
    annotate.add_argument("--out-annotated-json", default="human_case_annotated.json")

    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "prepare":
        return _cmd_prepare(args)
    if args.command == "merge":
        return _cmd_merge(args)
    if args.command == "annotate":
        return _cmd_annotate(args)
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
