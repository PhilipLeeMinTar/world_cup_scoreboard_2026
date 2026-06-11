#!/usr/bin/env python3
"""
build_execute_metrics.py — 解析执行结果与日志，构造 case_info_list[] 并写入 metrics.json。

用法:
  python3 build_execute_metrics.py \
    --workdir <specDir>/test/.api-mind \
    --log-dir <specDir>/test/api_test_logs \
    --test-file <path/to/xxx_test.go> \
    --failure-category '{"TC-002":"env_issue","TC-003":"business_bug"}'

脚本自动完成:
  - 从 apitest_TC-*.log 文件名提取 case_id
  - 从 execution_result.log 解析 status（pass/fail/skip）
  - 从 test_file 解析 test_func → case_id 映射
  - 从 apitest_TC-*.log 定向提取 biz_log_id / bits_log_id
  - 组装完整 case_info_list[] 并写入 metrics.json

macOS 兼容: 纯 Python stdlib，不依赖 GNU grep。
"""

import argparse
import glob
import json
import os
import re
import sys


def parse_test_file_mapping(test_file_path):
    """
    从 _test.go 文件中提取 test_func_name → case_id 映射。

    匹配模式:
      func TestXxx(t *testing.T) {
          ...
          .WithCaseID("TC-001")

    返回: {"TestJobNewListBasicPagination": "TC-001", ...}
    """
    mapping = {}
    if not test_file_path or not os.path.exists(test_file_path):
        return mapping

    with open(test_file_path, "r") as f:
        content = f.read()

    # 匹配 func TestXxx(...) 和紧随的 WithCaseID("TC-XXX")
    # 使用非贪婪匹配，在下一个 func 或文件末尾停止
    pattern = r'func\s+(Test\w+)\([^)]*\)\s*\*?[^}]*?\.WithCaseID\("(TC-\d+)"\)'
    for match in re.finditer(pattern, content, re.DOTALL):
        func_name = match.group(1)
        case_id = match.group(2)
        mapping[func_name] = case_id

    return mapping


def parse_execution_result(log_dir):
    """
    解析 execution_result.log，提取每个 test_func 的 status。

    返回: {"TestJobNewListBasicPagination": "pass", ...}
    """
    result = {}
    exec_log = os.path.join(log_dir, "execution_result.log")
    if not os.path.exists(exec_log):
        return result

    with open(exec_log, "r") as f:
        content = f.read()

    # 匹配 --- PASS/FAIL/SKIP: TestXxx (duration)
    for line in content.splitlines():
        m = re.match(r'---\s+(PASS|FAIL|SKIP):\s+(\w+)', line)
        if m:
            status = m.group(1).lower()
            func_name = m.group(2)
            result[func_name] = status

    return result


def extract_log_ids(log_file_path):
    """
    从 apitest_TC-*.log 中提取 biz_log_id 和 bits_log_id。

    返回: (biz_log_id, bits_log_id)
    """
    biz_log_id = ""
    bits_log_id = ""

    if not os.path.exists(log_file_path):
        return biz_log_id, bits_log_id

    with open(log_file_path, "r") as f:
        for line in f:
            if "Business.LogID:" in line and not biz_log_id:
                biz_log_id = line.split("Business.LogID:", 1)[1].strip()
            if "Gateway.LogID:" in line and not bits_log_id:
                bits_log_id = line.split("Gateway.LogID:", 1)[1].strip()
            if biz_log_id and bits_log_id:
                break

    return biz_log_id, bits_log_id


def build_case_info_list(log_dir, test_file_path, failure_category_map):
    """
    构造完整的 case_info_list[]。

    步骤:
      1. 从 apitest_TC-*.log 文件名获取所有 case_id
      2. 从 test_file 解析 func_name → case_id 映射
      3. 从 execution_result.log 解析 func_name → status 映射
      4. 合并: case_id → status
      5. 对每个 case 提取 LogID
      6. 组装最终列表
    """
    # Step 1: 获取所有 case_id（从日志文件名）
    log_pattern = os.path.join(log_dir, "apitest_TC-*.log")
    log_files = sorted(glob.glob(log_pattern))

    case_ids_from_logs = set()
    for fpath in log_files:
        basename = os.path.basename(fpath)
        # apitest_TC-001.log → TC-001
        case_id = basename.replace("apitest_", "").replace(".log", "")
        case_ids_from_logs.add(case_id)

    # Step 2 & 3: 解析映射
    func_to_case = parse_test_file_mapping(test_file_path)
    func_to_status = parse_execution_result(log_dir)

    # Step 4: 合并 case_id → status
    # 构建反向映射: case_id → func_name
    case_to_func = {v: k for k, v in func_to_case.items()}

    case_status = {}
    for case_id in case_ids_from_logs:
        if case_id in case_to_func:
            func_name = case_to_func[case_id]
            case_status[case_id] = func_to_status.get(func_name, "error")
        else:
            # fallback: 无法映射时标记为 error
            case_status[case_id] = "error"

    # 也处理 execution_result.log 中有但日志文件缺失的 case
    for func_name, status in func_to_status.items():
        if func_name in func_to_case:
            case_id = func_to_case[func_name]
            if case_id not in case_status:
                case_status[case_id] = status

    # Step 5 & 6: 组装 case_info_list
    case_info_list = []
    # 按 case_id 排序
    for case_id in sorted(case_status.keys()):
        status = case_status[case_id]

        # 提取 LogID
        log_file = os.path.join(log_dir, f"apitest_{case_id}.log")
        biz_log_id, bits_log_id = extract_log_ids(log_file)

        # 失败归因
        failure_category = failure_category_map.get(case_id, "")

        case_info_list.append({
            "case_id": case_id,
            "status": status,
            "mock": 0,
            "has_to_be_filled": 0,
            "biz_log_id": biz_log_id,
            "bits_log_id": bits_log_id,
            "psm": [],  # 由调用方从已有 metrics.json 填充
            "failure_category": failure_category,
        })

    return case_info_list


def main():
    parser = argparse.ArgumentParser(
        description="解析测试执行结果，构造 case_info_list 并写入 metrics.json"
    )
    parser.add_argument("--workdir", required=True,
                        help="metrics 工作目录，如 <specDir>/test/.api-mind")
    parser.add_argument("--log-dir", required=True,
                        help="测试日志目录，如 <specDir>/test/api_test_logs")
    parser.add_argument("--test-file", default=None,
                        help="测试文件路径，如 tests/integration/xxx/xxx_test.go")
    parser.add_argument("--failure-category", default="{}",
                        help='失败归因 JSON 映射，如 \'{"TC-002":"env_issue"}\'')
    parser.add_argument("--psm", default=None,
                        help='PSM JSON 数组，如 \'["tiktokqa.quality.god"]\'')
    args = parser.parse_args()

    # 解析 failure_category
    try:
        failure_category_map = json.loads(args.failure_category)
    except json.JSONDecodeError:
        print(f"[WARN] 无法解析 --failure-category: {args.failure_category}", file=sys.stderr)
        failure_category_map = {}

    # 解析 PSM
    psm_list = []
    if args.psm:
        try:
            psm_list = json.loads(args.psm)
        except json.JSONDecodeError:
            print(f"[WARN] 无法解析 --psm: {args.psm}", file=sys.stderr)

    # 读取已有 metrics.json
    metrics_path = os.path.join(args.workdir, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
    else:
        metrics = {}

    # 如果未提供 --psm，从已有 metrics.json 中获取
    if not psm_list:
        psm_list = metrics.get("psm", [])

    # 构造 case_info_list
    case_info_list = build_case_info_list(
        args.log_dir, args.test_file, failure_category_map
    )

    # 填充 psm
    for case_info in case_info_list:
        if not case_info["psm"]:
            case_info["psm"] = psm_list

    # 统计
    pass_count = sum(1 for c in case_info_list if c["status"] == "pass")
    fail_count = sum(1 for c in case_info_list if c["status"] == "fail")
    skip_count = sum(1 for c in case_info_list if c["status"] == "skip")
    total_count = len(case_info_list)

    # 确定 execute_status
    if fail_count == 0 and skip_count == 0:
        execute_status = "pass"
    elif pass_count == 0 and skip_count == 0:
        execute_status = "fail"
    else:
        execute_status = "partial_pass"

    # 写入 metrics.json（保留已有字段）
    metrics["execute_status"] = execute_status
    metrics["total_count"] = total_count
    metrics["pass_count"] = pass_count
    metrics["fail_count"] = fail_count
    metrics["skip_count"] = skip_count
    metrics["case_info_list"] = case_info_list

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"[build_execute_metrics] 已写入 {metrics_path}")
    print(f"  total={total_count}, pass={pass_count}, fail={fail_count}, skip={skip_count}")
    print(f"  execute_status={execute_status}")


if __name__ == "__main__":
    main()
