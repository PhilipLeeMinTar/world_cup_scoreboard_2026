#!/usr/bin/env python3
"""
build_common_metrics.py — 复用/采集公共字段并写入 metrics_common.json（缓存）和 metrics.json。

用法:
  python3 build_common_metrics.py \
    --workdir <specDir>/test/.api-mind \
    --user-name "wangjingjing.vector"

脚本自动完成:
  - 缓存完整时直接复用 metrics_common.json，避免重复采集
  - 从 workdir 推断 spec_name
  - 从 test/task.md 或 case.md 轻量提取 PSM（也可通过 --psm 显式传入）
  - git rev-parse --show-toplevel → repo_name
  - git remote get-url origin → repo_link
  - 写入 metrics_common.json（缓存，供后续子任务复用）
  - 写入 metrics.json（当前子任务）

macOS 兼容: 纯 Python stdlib。
"""

import argparse
import json
import os
import re
import subprocess
import sys


COMMON_FIELDS = ("user_name", "spec_name", "psm", "repo_name", "repo_link")


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_complete_common(data):
    return (
        isinstance(data, dict)
        and isinstance(data.get("user_name"), str)
        and isinstance(data.get("spec_name"), str)
        and isinstance(data.get("psm"), list)
        and isinstance(data.get("repo_name"), str)
        and isinstance(data.get("repo_link"), str)
        and data.get("spec_name") != ""
    )


def run_git(args, cwd=None):
    """执行 git 命令，失败返回空字符串。"""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def infer_feature_dir(workdir):
    """从 <FEATURE_DIR>/test/.api-mind 推断 FEATURE_DIR；失败则返回 workdir 的上级。"""
    abs_workdir = os.path.abspath(workdir)
    parent = os.path.dirname(abs_workdir)
    if os.path.basename(abs_workdir) == ".api-mind" and os.path.basename(parent) == "test":
        return os.path.dirname(parent)
    return os.path.dirname(parent) if os.path.basename(abs_workdir) == ".api-mind" else parent


def infer_spec_name(workdir, explicit_spec_name):
    if explicit_spec_name:
        return explicit_spec_name
    return os.path.basename(infer_feature_dir(workdir))


def read_small_text(path, max_bytes=256 * 1024):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except OSError:
        return ""


def extract_psm_from_text(text):
    """从少量 task/case 文本中提取 PSM-like token，避免模型读取大上下文。"""
    if not text:
        return []

    candidates = []
    psm_pattern = re.compile(r"\b[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_\-]+){2,}\b")
    for line in text.splitlines():
        lower = line.lower()
        if "psm" not in lower and "service" not in lower and "服务" not in line:
            continue
        candidates.extend(psm_pattern.findall(line))

    # 保序去重
    seen = set()
    result = []
    for item in candidates:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def infer_psm(workdir, explicit_psm, task_file=None, case_file=None):
    if explicit_psm:
        try:
            parsed = json.loads(explicit_psm)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            print(f"[WARN] 无法解析 --psm: {explicit_psm}", file=sys.stderr)

    feature_dir = infer_feature_dir(workdir)
    task_file = task_file or os.path.join(feature_dir, "test", "task.md")
    case_file = case_file or os.path.join(feature_dir, "test", "case.md")

    psm = extract_psm_from_text(read_small_text(task_file))
    if psm:
        return psm
    return extract_psm_from_text(read_small_text(case_file))


def collect_common_fields(workdir, spec_name, psm_list, user_name):
    """
    采集 5 个公共字段:
      - user_name: 由调用方传入
      - spec_name: 由调用方传入
      - psm: 由调用方传入
      - repo_name: git rev-parse --show-toplevel → basename
      - repo_link: git remote get-url origin
    """
    # 从 workdir 推断仓库根目录
    # workdir 通常是 <repo_root>/specs/<spec_name>/test/.api-mind
    # 向上找到 git 仓库根目录
    repo_root = run_git(["rev-parse", "--show-toplevel"], cwd=workdir)
    if not repo_root:
        # fallback: 从 workdir 向上查找
        repo_root = run_git(["rev-parse", "--show-toplevel"], cwd=os.path.dirname(workdir))

    repo_name = os.path.basename(repo_root) if repo_root else ""
    repo_link = run_git(["remote", "get-url", "origin"], cwd=repo_root) if repo_root else ""

    common = {
        "user_name": user_name,
        "spec_name": spec_name,
        "psm": psm_list,
        "repo_name": repo_name,
        "repo_link": repo_link,
    }

    return common


def main():
    parser = argparse.ArgumentParser(
        description="采集公共 metrics 字段并写入缓存和 metrics.json"
    )
    parser.add_argument("--workdir", required=True,
                        help="metrics 工作目录，如 <specDir>/test/.api-mind")
    parser.add_argument("--spec-name", default=None,
                        help="spec 目录名")
    parser.add_argument("--psm", default=None,
                        help='PSM JSON 数组，如 \'["tiktokqa.quality.god"]\'')
    parser.add_argument("--user-name", default="",
                        help="用户名")
    parser.add_argument("--task-file", default=None,
                        help="可选：task.md 路径；未传则从 workdir 推断")
    parser.add_argument("--case-file", default=None,
                        help="可选：case.md 路径；未传则从 workdir 推断")
    parser.add_argument("--force", action="store_true",
                        help="忽略 metrics_common.json 缓存，重新采集公共字段")
    args = parser.parse_args()

    os.makedirs(args.workdir, exist_ok=True)

    common_path = os.path.join(args.workdir, "metrics_common.json")
    metrics_path = os.path.join(args.workdir, "metrics.json")

    # 缓存完整时直接复用，避免重复读取 task/case、git、JWT 解析等动作。
    cached = load_json(common_path)
    if not args.force and is_complete_common(cached):
        metrics = load_json(metrics_path)
        metrics.update({field: cached[field] for field in COMMON_FIELDS})
        save_json(metrics_path, metrics)
        print(f"[build_common_metrics] 已复用缓存 {common_path}")
        print(f"[build_common_metrics] 已写入 {metrics_path}")
        return

    spec_name = infer_spec_name(args.workdir, args.spec_name)
    psm_list = infer_psm(args.workdir, args.psm, args.task_file, args.case_file)

    # 采集公共字段
    common = collect_common_fields(
        args.workdir, spec_name, psm_list, args.user_name
    )

    # 写入 metrics_common.json（缓存）
    save_json(common_path, common)
    print(f"[build_common_metrics] 已写入缓存 {common_path}")

    # 写入 metrics.json（当前子任务）
    metrics = load_json(metrics_path)

    metrics.update(common)

    save_json(metrics_path, metrics)
    print(f"[build_common_metrics] 已写入 {metrics_path}")
    print(f"  user_name={common['user_name']}, spec_name={common['spec_name']}")
    print(f"  psm={common['psm']}, repo_name={common['repo_name']}")


if __name__ == "__main__":
    main()
