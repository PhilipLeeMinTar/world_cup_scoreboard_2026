#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME=$(basename "$0")
DEFAULT_TTAT_API_BASE="https://autoduck-api-va.tiktok-row.net"
DEFAULT_TTAT_API_BASE_PROD="https://autoduck-api-va.byteintl.net"
DEFAULT_TTAT_TOS_BASE="https://autoduck-tos-us.tiktok-row.net"
DEFAULT_TTAT_TOS_BASE_PROD="https://autoduck-tos-us.byteintl.net"
DEFAULT_UI_BASE="https://ttat-us.byteintl.net"

usage() {
  cat <<'USAGE'
Fetch and parse TTAT remote execution results for api-test Python cases.

Commands:
  fetch            Fetch TTAT task detail, suites, per-case report json, and log attachments.
  parse            Parse fetched TTAT artifacts into JSON and Markdown report outputs.
  fetch-and-parse  Run fetch first, then parse.

Common options:
  --api-base <url>     Override TTAT API base URL.
  --tos-base <url>     Override TTAT TOS/report base URL.
  --prod               Use prod TTAT API/TOS base URLs.
  --user-token <tok>   X-Custom-Token. Defaults to $TTAT_USER_TOKEN.
  --output-dir <dir>   Output directory. Default: ./ttat_report_output
  -h, --help           Show help.

fetch options:
  --plan-id <id>          TTAT plan id.
  --task-id <id>          TTAT task id.
  --wait-seconds <n>      Max seconds to wait for sub_task completion. Default: 600.
  --poll-interval <n>     Poll interval seconds. Default: 10.

parse options:
  --proto <http|rpc>      Log parsing protocol. Default: http.
  --result-dir <dir>      Result directory created by fetch. Defaults to --output-dir.
  --report-file <path>    Markdown report output path. Default: <result-dir>/test_report.md
  --json-file <path>      Parsed JSON output path. Default: <result-dir>/parsed_results.json

Examples:
  ttat_report.sh fetch \
    --plan-id 123 \
    --task-id 456 \
    --output-dir ./artifacts \
    --user-token "$TTAT_USER_TOKEN"

  ttat_report.sh parse \
    --result-dir ./artifacts \
    --proto http

  ttat_report.sh fetch-and-parse \
    --plan-id 123 \
    --task-id 456 \
    --output-dir ./artifacts \
    --proto http \
    --user-token "$TTAT_USER_TOKEN"
USAGE
}

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*" >&2
}

die() {
  log "ERROR: $*"
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

json_get() {
  local file="$1"
  local query="$2"
  jq -r "$query" "$file"
}

call_api() {
  local method="$1"
  local url="$2"
  local token="$3"
  local output_file="$4"
  local http_code
  http_code=$(curl -sS -X "$method" \
    -H "X-Custom-Token: $token" \
    -o "$output_file" \
    -w '%{http_code}' \
    "$url")
  if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
    log "HTTP request failed with code $http_code for $url"
    cat "$output_file" >&2 || true
    return 1
  fi
}

validate_base_resp() {
  local file="$1"
  local status_code
  status_code=$(jq -r '.base_resp.status_code // empty' "$file")
  [[ "$status_code" == "200" ]] || return 1
}

ensure_dir() {
  mkdir -p "$1"
}

fetch_task_detail() {
  local api_base="$1"
  local token="$2"
  local task_id="$3"
  local out_file="$4"
  local url="${api_base}/ttat/test/api-test/tasks/${task_id}"
  call_api GET "$url" "$token" "$out_file"
  validate_base_resp "$out_file" || die "Task detail base_resp.status_code != 200"
}

wait_for_sub_task() {
  local task_detail_file="$1"
  local api_base="$2"
  local token="$3"
  local task_id="$4"
  local wait_seconds="$5"
  local poll_interval="$6"

  local started now elapsed
  started=$(date +%s)

  while true; do
    local sub_task_id sub_task_status
    sub_task_id=$(jq -r '.task.sub_tasks[0].id // empty' "$task_detail_file")
    sub_task_status=$(jq -r '.task.sub_tasks[0].task_status // empty' "$task_detail_file")

    if [[ -n "$sub_task_id" && ( "$sub_task_status" == "succeeded" || "$sub_task_status" == "failed" ) ]]; then
      printf '%s\t%s\n' "$sub_task_id" "$sub_task_status"
      return 0
    fi

    now=$(date +%s)
    elapsed=$((now - started))
    if [[ "$elapsed" -ge "$wait_seconds" ]]; then
      die "Timed out waiting for TTAT sub_task completion for task_id=${task_id}"
    fi

    sleep "$poll_interval"
    fetch_task_detail "$api_base" "$token" "$task_id" "$task_detail_file"
  done
}

fetch_suites() {
  local tos_base="$1"
  local token="$2"
  local plan_id="$3"
  local task_id="$4"
  local sub_task_id="$5"
  local out_file="$6"
  local url="${tos_base}/api_test_faas_execution_results/${plan_id}/${task_id}/${sub_task_id}/allure_report_files/data/suites.json"
  call_api GET "$url" "$token" "$out_file"
}

fetch_case_report() {
  local tos_base="$1"
  local token="$2"
  local plan_id="$3"
  local task_id="$4"
  local sub_task_id="$5"
  local uid="$6"
  local out_file="$7"
  local url="${tos_base}/api_test_faas_execution_results/${plan_id}/${task_id}/${sub_task_id}/allure_report_files/data/test-cases/${uid}.json"
  call_api GET "$url" "$token" "$out_file"
}

fetch_attachment() {
  local tos_base="$1"
  local token="$2"
  local plan_id="$3"
  local task_id="$4"
  local sub_task_id="$5"
  local filename="$6"
  local out_file="$7"
  local url="${tos_base}/api_test_faas_execution_results/${plan_id}/${task_id}/${sub_task_id}/allure_report_files/data/attachments/${filename}"
  call_api GET "$url" "$token" "$out_file"
}

build_manifest() {
  local suites_file="$1"
  local manifest_file="$2"
  jq -c '
    .children[]? as $suite
    | $suite.children[]? as $test_file
    | $test_file.children[]? as $test_class
    | $test_class.children[]?
    | {
        suite_name: ($suite.name // ""),
        test_file_name: ($test_file.name // ""),
        class_name: ($test_class.name // ""),
        case_name: (.name // ""),
        uid: (.uid // ""),
        status: (.status // "unknown")
      }
  ' "$suites_file" > "$manifest_file"
}

parse_log_content() {
  local proto="$1"
  local log_file="$2"
  python3 - "$proto" "$log_file" <<'PY'
import ast
import json
import re
import sys
from pathlib import Path

proto = sys.argv[1].lower()
log_path = Path(sys.argv[2])
text = log_path.read_text(encoding='utf-8', errors='ignore')
result = {"parse_success": False, "resp_data": None}

try:
    if proto == 'http':
        marker = '"resp": '
        start = text.find(marker)
        end = text.rfind('"X-backend"')
        if start >= 0 and end > start:
            resp_text = text[start + len(marker):end].strip()
            if resp_text.endswith(','):
                resp_text = resp_text[:-1]
            loaded = json.loads(resp_text)
            if isinstance(loaded, str):
                evaluated = eval(loaded)
                if isinstance(evaluated, (bytes, bytearray)):
                    evaluated = evaluated.decode('utf-8', errors='ignore')
                loaded = json.loads(evaluated)
            result = {"parse_success": True, "resp_data": loaded}
    else:
        m = re.search(r"Response:\s*(\{.+?\})\s*(?:INFO|\Z)", text, re.DOTALL)
        if m:
            resp_dict = ast.literal_eval(m.group(1))
            result = {"parse_success": True, "resp_data": resp_dict}
except Exception as e:
    result["error"] = str(e)

print(json.dumps(result, ensure_ascii=False))
PY
}

normalize_reason() {
  local status="$1"
  local error_trace="$2"
  local parse_success="$3"
  local attachment_source="$4"
  if [[ "$status" == "passed" ]]; then
    printf '%s\n' '-'
  elif [[ -n "$error_trace" ]]; then
    printf '%s\n' "$error_trace" | head -n 1
  elif [[ "$attachment_source" == "" || "$attachment_source" == "null" ]]; then
    printf '%s\n' '日志附件缺失'
  elif [[ "$parse_success" != "true" ]]; then
    printf '%s\n' '响应解析失败'
  else
    printf 'TTAT status=%s\n' "$status"
  fi
}

status_label() {
  case "$1" in
    passed) printf '✅ **PASS**' ;;
    failed) printf '❌ **FAIL**' ;;
    broken) printf '⚠️ **ERROR**' ;;
    skipped) printf '⏭️ **SKIP**' ;;
    *) printf '⚠️ **ERROR**' ;;
  esac
}

run_fetch() {
  local api_base="$1"
  local tos_base="$2"
  local token="$3"
  local plan_id="$4"
  local task_id="$5"
  local output_dir="$6"
  local wait_seconds="$7"
  local poll_interval="$8"

  ensure_dir "$output_dir/raw/test-cases"
  ensure_dir "$output_dir/raw/attachments"
  ensure_dir "$output_dir/meta"

  local task_detail_file="$output_dir/raw/task_detail.json"
  local suites_file="$output_dir/raw/suites.json"
  local manifest_file="$output_dir/meta/cases.jsonl"
  local metadata_file="$output_dir/meta/metadata.json"

  fetch_task_detail "$api_base" "$token" "$task_id" "$task_detail_file"
  local sub_task_info sub_task_id sub_task_status
  sub_task_info=$(wait_for_sub_task "$task_detail_file" "$api_base" "$token" "$task_id" "$wait_seconds" "$poll_interval")
  sub_task_id=${sub_task_info%%$'\t'*}
  sub_task_status=${sub_task_info#*$'\t'}

  fetch_suites "$tos_base" "$token" "$plan_id" "$task_id" "$sub_task_id" "$suites_file"
  build_manifest "$suites_file" "$manifest_file"

  jq -n \
    --arg plan_id "$plan_id" \
    --arg task_id "$task_id" \
    --arg sub_task_id "$sub_task_id" \
    --arg sub_task_status "$sub_task_status" \
    --arg execution_url "${DEFAULT_UI_BASE}/api/test_plans/${plan_id}/jobs/${task_id}" \
    '{plan_id:$plan_id, ttat_task_id:$task_id, sub_task_id:$sub_task_id, sub_task_status:$sub_task_status, execution_url:$execution_url}' \
    > "$metadata_file"

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    local uid
    uid=$(jq -r '.uid' <<<"$line")
    local report_file attachment_source attachment_path
    report_file="$output_dir/raw/test-cases/${uid}.json"
    fetch_case_report "$tos_base" "$token" "$plan_id" "$task_id" "$sub_task_id" "$uid" "$report_file"
    attachment_source=$(jq -r '.testStage.attachments[0].source // empty' "$report_file")
    if [[ -n "$attachment_source" ]]; then
      attachment_path="$output_dir/raw/attachments/${attachment_source}"
      fetch_attachment "$tos_base" "$token" "$plan_id" "$task_id" "$sub_task_id" "$attachment_source" "$attachment_path"
    fi
  done < "$manifest_file"

  printf 'TTAT_PLAN_ID=%s\n' "$plan_id"
  printf 'TTAT_TASK_ID=%s\n' "$task_id"
  printf 'TTAT_SUB_TASK_ID=%s\n' "$sub_task_id"
  printf 'TTAT_RESULT_DIR=%s\n' "$output_dir"
  printf 'TTAT_EXECUTION_URL=%s/api/test_plans/%s/jobs/%s\n' "$DEFAULT_UI_BASE" "$plan_id" "$task_id"
}

run_parse() {
  local result_dir="$1"
  local proto="$2"
  local report_file="$3"
  local json_file="$4"

  local manifest_file="$result_dir/meta/cases.jsonl"
  local metadata_file="$result_dir/meta/metadata.json"
  [[ -f "$manifest_file" ]] || die "Missing manifest file: $manifest_file"
  [[ -f "$metadata_file" ]] || die "Missing metadata file: $metadata_file"

  local tmp_jsonl
  tmp_jsonl=$(mktemp)

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    local uid report_json_file attachment_source attachment_path error_trace parse_json parse_success failure_reason
    uid=$(jq -r '.uid' <<<"$line")
    report_json_file="$result_dir/raw/test-cases/${uid}.json"
    [[ -f "$report_json_file" ]] || die "Missing case report json: $report_json_file"

    attachment_source=$(jq -r '.testStage.attachments[0].source // empty' "$report_json_file")
    error_trace=$(jq -r '.testStage.statusTrace // empty' "$report_json_file")
    local parse_success_value='false'
    local resp_data_json='null'

    if [[ -n "$attachment_source" && -f "$result_dir/raw/attachments/${attachment_source}" ]]; then
      attachment_path="$result_dir/raw/attachments/${attachment_source}"
      parse_json=$(parse_log_content "$proto" "$attachment_path")
      parse_success_value=$(jq -r '.parse_success' <<<"$parse_json")
      resp_data_json=$(jq -c '.resp_data' <<<"$parse_json")
    fi

    failure_reason=$(normalize_reason "$(jq -r '.status' <<<"$line")" "$error_trace" "$parse_success_value" "$attachment_source")

    jq -n \
      --argjson manifest "$line" \
      --arg attachment_source "$attachment_source" \
      --arg error_trace "$error_trace" \
      --arg failure_reason "$failure_reason" \
      --argjson parse_success "$parse_success_value" \
      --argjson resp_data "$resp_data_json" \
      '$manifest + {
        attachment_source: ($attachment_source // ""),
        parse_success: $parse_success,
        resp_data: $resp_data,
        error_trace: ($error_trace // ""),
        failure_reason: ($failure_reason // "")
      }' >> "$tmp_jsonl"
  done < "$manifest_file"

  jq -s '.' "$tmp_jsonl" > "$json_file"
  rm -f "$tmp_jsonl"

  local total passed failed skipped errored execution_time execution_url
  total=$(jq 'length' "$json_file")
  passed=$(jq '[.[] | select(.status=="passed")] | length' "$json_file")
  failed=$(jq '[.[] | select(.status=="failed")] | length' "$json_file")
  skipped=$(jq '[.[] | select(.status=="skipped")] | length' "$json_file")
  errored=$(jq '[.[] | select(.status=="broken" or (.status != "passed" and .status != "failed" and .status != "skipped"))] | length' "$json_file")
  execution_time=$(date '+%Y-%m-%d %H:%M:%S')
  execution_url=$(jq -r '.execution_url // ""' "$metadata_file")

  {
    printf '# 测试执行报告\n'
    printf '**执行时间**：%s\n\n' "$execution_time"
    printf '**执行链接**：%s\n\n' "$execution_url"
    printf '## 执行概况\n\n'
    printf '| 总数 | 通过 | 失败 | 跳过 | 错误 |\n'
    printf '| :---: | :---: | :---: | :---: | :---: |\n'
    printf '| %s | %s | %s | %s | %s |\n\n' "$total" "$passed" "$failed" "$skipped" "$errored"
    printf '## 结果详情\n\n'
    printf '| 状态 | 测试类 | 用例名 | UID | 日志附件 | 响应解析 | 失败原因 |\n'
    printf '| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n'

    jq -c '.[]' "$json_file" | while IFS= read -r item; do
      local status class_name case_name uid attachment parse_success failure_reason
      status=$(jq -r '.status' <<<"$item")
      class_name=$(jq -r '.class_name' <<<"$item")
      case_name=$(jq -r '.case_name' <<<"$item")
      uid=$(jq -r '.uid' <<<"$item")
      attachment=$(jq -r '.attachment_source // "-"' <<<"$item")
      parse_success=$(jq -r '.parse_success' <<<"$item")
      failure_reason=$(jq -r '.failure_reason' <<<"$item" | sed ':a;N;$!ba;s/\n/<br>/g' | sed 's/|/\\|/g')
      class_name=${class_name//|/\\|}
      case_name=${case_name//|/\\|}
      attachment=${attachment//|/\\|}
      printf '| %s | %s | %s | `%s` | `%s` | %s | %s |\n' \
        "$(status_label "$status")" \
        "$class_name" \
        "$case_name" \
        "$uid" \
        "${attachment:--}" \
        "$([[ "$parse_success" == "true" ]] && printf '成功' || printf '失败')" \
        "$failure_reason"
    done
  } > "$report_file"

  printf 'REPORT_JSON_PATH=%s\n' "$json_file"
  printf 'REPORT_MD_PATH=%s\n' "$report_file"
}

main() {
  require_cmd curl
  require_cmd python3
  require_cmd jq

  local command="${1:-}"
  [[ -n "$command" ]] || { usage; exit 1; }
  shift || true

  local api_base=""
  local tos_base=""
  local use_prod="false"
  local token="${TTAT_USER_TOKEN:-}"
  local output_dir="./ttat_report_output"

  case "$command" in
    fetch)
      local plan_id=""
      local task_id=""
      local wait_seconds="600"
      local poll_interval="10"
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --api-base) api_base="$2"; shift 2 ;;
          --tos-base) tos_base="$2"; shift 2 ;;
          --prod) use_prod="true"; shift ;;
          --user-token) token="$2"; shift 2 ;;
          --output-dir) output_dir="$2"; shift 2 ;;
          --plan-id) plan_id="$2"; shift 2 ;;
          --task-id) task_id="$2"; shift 2 ;;
          --wait-seconds) wait_seconds="$2"; shift 2 ;;
          --poll-interval) poll_interval="$2"; shift 2 ;;
          -h|--help) usage; exit 0 ;;
          *) die "Unknown option for fetch: $1" ;;
        esac
      done
      [[ -n "$plan_id" ]] || die "--plan-id is required"
      [[ -n "$task_id" ]] || die "--task-id is required"
      [[ -n "$token" ]] || die "User token is required via --user-token or TTAT_USER_TOKEN"
      [[ -n "$api_base" ]] || api_base=$([[ "$use_prod" == "true" ]] && printf '%s' "$DEFAULT_TTAT_API_BASE_PROD" || printf '%s' "$DEFAULT_TTAT_API_BASE")
      [[ -n "$tos_base" ]] || tos_base=$([[ "$use_prod" == "true" ]] && printf '%s' "$DEFAULT_TTAT_TOS_BASE_PROD" || printf '%s' "$DEFAULT_TTAT_TOS_BASE")
      run_fetch "$api_base" "$tos_base" "$token" "$plan_id" "$task_id" "$output_dir" "$wait_seconds" "$poll_interval"
      ;;

    parse)
      local result_dir=""
      local proto="http"
      local report_file=""
      local json_file=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --output-dir) output_dir="$2"; shift 2 ;;
          --result-dir) result_dir="$2"; shift 2 ;;
          --proto) proto="$2"; shift 2 ;;
          --report-file) report_file="$2"; shift 2 ;;
          --json-file) json_file="$2"; shift 2 ;;
          -h|--help) usage; exit 0 ;;
          *) die "Unknown option for parse: $1" ;;
        esac
      done
      [[ -n "$result_dir" ]] || result_dir="$output_dir"
      [[ -n "$report_file" ]] || report_file="$result_dir/test_report.md"
      [[ -n "$json_file" ]] || json_file="$result_dir/parsed_results.json"
      run_parse "$result_dir" "$proto" "$report_file" "$json_file"
      ;;

    fetch-and-parse)
      local plan_id=""
      local task_id=""
      local wait_seconds="600"
      local poll_interval="10"
      local proto="http"
      local report_file=""
      local json_file=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --api-base) api_base="$2"; shift 2 ;;
          --tos-base) tos_base="$2"; shift 2 ;;
          --prod) use_prod="true"; shift ;;
          --user-token) token="$2"; shift 2 ;;
          --output-dir) output_dir="$2"; shift 2 ;;
          --plan-id) plan_id="$2"; shift 2 ;;
          --task-id) task_id="$2"; shift 2 ;;
          --wait-seconds) wait_seconds="$2"; shift 2 ;;
          --poll-interval) poll_interval="$2"; shift 2 ;;
          --proto) proto="$2"; shift 2 ;;
          --report-file) report_file="$2"; shift 2 ;;
          --json-file) json_file="$2"; shift 2 ;;
          -h|--help) usage; exit 0 ;;
          *) die "Unknown option for fetch-and-parse: $1" ;;
        esac
      done
      [[ -n "$plan_id" ]] || die "--plan-id is required"
      [[ -n "$task_id" ]] || die "--task-id is required"
      [[ -n "$token" ]] || die "User token is required via --user-token or TTAT_USER_TOKEN"
      [[ -n "$api_base" ]] || api_base=$([[ "$use_prod" == "true" ]] && printf '%s' "$DEFAULT_TTAT_API_BASE_PROD" || printf '%s' "$DEFAULT_TTAT_API_BASE")
      [[ -n "$tos_base" ]] || tos_base=$([[ "$use_prod" == "true" ]] && printf '%s' "$DEFAULT_TTAT_TOS_BASE_PROD" || printf '%s' "$DEFAULT_TTAT_TOS_BASE")
      [[ -n "$report_file" ]] || report_file="$output_dir/test_report.md"
      [[ -n "$json_file" ]] || json_file="$output_dir/parsed_results.json"
      run_fetch "$api_base" "$tos_base" "$token" "$plan_id" "$task_id" "$output_dir" "$wait_seconds" "$poll_interval"
      run_parse "$output_dir" "$proto" "$report_file" "$json_file"
      ;;

    -h|--help|help)
      usage
      ;;

    *)
      die "Unknown command: $command"
      ;;
  esac
}

main "$@"
