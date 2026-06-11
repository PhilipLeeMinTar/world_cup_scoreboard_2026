#!/usr/bin/env python3
"""Sync the skill-managed apitest runtime into a target Go repo.

Source of truth: ../runtime/{manifest.json,*.go,README.md}.
Default usage:
  python3 go_driver/scripts/sync_runtime.py sync --dest <REPO_ROOT>/tests/integration/apitest --json --trust-version

The script compares manifest file names + sha256, copies missing/changed managed
files, preserves repo overlays (for example local_rpc.go), and never deletes
target extras. For the hot path, --trust-version skips per-file sha256 when the
target manifest version already matches and all managed files exist; this avoids
rehashing the runtime on every generate run. Output status: up-to-date | synced |
needs-sync | version-mismatch | error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from typing import Any, Dict, List, Optional


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare(manifest: Dict[str, Any], source_dir: str, dest_dir: str,
            *, trust_version: bool = False, dest_version: str = "") -> Dict[str, Any]:
    """比对 source(manifest 基准) 与 dest，返回差异分类。"""
    files = manifest.get("files", [])
    overlays = set(manifest.get("repo_overlays", []))

    missing: List[str] = []      # 目标缺失，需要补
    changed: List[str] = []      # 哈希不一致，需要覆盖
    replaced_skip: List[str] = []  # 源 stub 已被仓库覆盖文件替代，跳过

    managed_names = set()
    expected_version = str(manifest.get("version", ""))
    can_trust_version = bool(trust_version and expected_version and dest_version == expected_version)
    for item in files:
        name = item["name"]
        replaced_by = item.get("repo_overlay_replaced_by")
        dest_path = os.path.join(dest_dir, name)

        # stub 文件：目标已存在替代文件时跳过
        if replaced_by and os.path.exists(os.path.join(dest_dir, replaced_by)):
            replaced_skip.append(name)
            continue

        managed_names.add(name)

        if not os.path.exists(dest_path):
            missing.append(name)
            continue

        if not can_trust_version:
            expected = item.get("sha256", "")
            if expected and sha256_file(dest_path) != expected:
                changed.append(name)

    # 目标目录里多出来的文件（排除 overlay 与被管理文件）
    # manifest.json 会被一并同步，不算 extra。
    ignore_extra = {"manifest.json"}
    extra: List[str] = []
    if os.path.isdir(dest_dir):
        for entry in sorted(os.listdir(dest_dir)):
            full = os.path.join(dest_dir, entry)
            if not os.path.isfile(full):
                continue
            if entry in managed_names or entry in overlays or entry in ignore_extra:
                continue
            # 被替代的 stub 名也不算 extra
            if entry in replaced_skip:
                continue
            extra.append(entry)

    return {
        "missing": sorted(missing),
        "changed": sorted(changed),
        "extra": sorted(extra),
        "replaced_skip": sorted(replaced_skip),
        "trusted_version": bool(can_trust_version and not missing),
    }


def read_dest_version(dest_dir: str) -> str:
    """目标若有 manifest.json，读取其 version 以便版本比对。"""
    dest_manifest = os.path.join(dest_dir, "manifest.json")
    if os.path.exists(dest_manifest):
        try:
            return str(load_manifest(dest_manifest).get("version", ""))
        except (json.JSONDecodeError, OSError):
            return ""
    return ""


def do_sync(manifest: Dict[str, Any], source_dir: str, dest_dir: str,
            diff: Dict[str, Any]) -> List[str]:
    """覆盖同步：补齐 missing、覆盖 changed，并同步 manifest.json。

    overlay 文件与被替代 stub 不动；不删除 extra（交由人工判断）。
    """
    os.makedirs(dest_dir, exist_ok=True)
    synced: List[str] = []
    for name in diff["missing"] + diff["changed"]:
        src = os.path.join(source_dir, name)
        if not os.path.exists(src):
            continue
        shutil.copy2(src, os.path.join(dest_dir, name))
        synced.append(name)

    # 同步 manifest.json 自身，便于下次版本比对
    src_manifest = os.path.join(source_dir, "manifest.json")
    if os.path.exists(src_manifest):
        shutil.copy2(src_manifest, os.path.join(dest_dir, "manifest.json"))

    return sorted(synced)


def emit(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return
    print(f"status={result['status']} version={result.get('version','')} "
          f"dest_version={result.get('dest_version','')}")
    for key in ("missing", "changed", "extra", "synced", "replaced_skip"):
        vals = result.get(key) or []
        if vals:
            print(f"{key}({len(vals)}): {', '.join(vals)}")
    if result.get("message"):
        print(result["message"])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="比对/同步 apitest runtime")
    parser.add_argument("mode", choices=("check", "sync"),
                        help="check=仅比对; sync=不一致时覆盖同步")
    parser.add_argument("--dest", required=True,
                        help="目标 runtime 目录，如 <REPO_ROOT>/tests/integration/apitest")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_manifest = os.path.abspath(os.path.join(script_dir, "..", "runtime", "manifest.json"))
    parser.add_argument("--manifest", default=default_manifest,
                        help="manifest.json 路径，默认 ../runtime/manifest.json")
    parser.add_argument("--source", default=None,
                        help="runtime 源目录，默认 manifest.json 所在目录")
    parser.add_argument("--json", action="store_true", help="输出紧凑 JSON")
    parser.add_argument("--trust-version", action="store_true",
                        help="目标 manifest version 匹配且文件存在时跳过 sha256 热路径校验；怀疑本地 runtime 被手改时不要使用")
    args = parser.parse_args(argv)

    if not os.path.exists(args.manifest):
        emit({"status": "error", "message": f"manifest not found: {args.manifest}"}, args.json)
        return 2

    manifest = load_manifest(args.manifest)
    source_dir = args.source or os.path.dirname(os.path.abspath(args.manifest))
    dest_dir = os.path.abspath(args.dest)

    version = str(manifest.get("version", ""))
    dest_version = read_dest_version(dest_dir)
    diff = compare(manifest, source_dir, dest_dir,
                   trust_version=args.trust_version, dest_version=dest_version)
    needs_sync = bool(diff["missing"] or diff["changed"])

    result: Dict[str, Any] = {
        "version": version,
        "dest_version": dest_version,
        "missing": diff["missing"],
        "changed": diff["changed"],
        "extra": diff["extra"],
        "replaced_skip": diff["replaced_skip"],
        "trusted_version": diff.get("trusted_version", False),
    }

    if args.mode == "check":
        if needs_sync:
            result["status"] = "version-mismatch" if (dest_version and dest_version != version) else "needs-sync"
        else:
            result["status"] = "up-to-date"
        emit(result, args.json)
        return 0

    # sync 模式
    if needs_sync:
        result["synced"] = do_sync(manifest, source_dir, dest_dir, diff)
        result["status"] = "synced"
    else:
        result["synced"] = []
        result["status"] = "up-to-date"
    emit(result, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
