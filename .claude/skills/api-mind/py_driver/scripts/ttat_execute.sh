#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME=$(basename "$0")
DEFAULT_TTAT_API_BASE="https://autoduck-api-va.tiktok-row.net"
DEFAULT_TTAT_API_BASE_PROD="https://autoduck-api-va.byteintl.net"

usage() {
  cat <<'USAGE'
Trigger or inspect remote api-test execution via TTAT REST APIs.

Commands:
  trigger              Trigger remote execution and print the trigger UUID.
  get-trigger-result   Resolve a trigger UUID into plan_id / task_id.

Common options:
  --api-base <url>     Override the TTAT API base URL.
  --prod               Use the prod TTAT API base URL.
  --user-token <tok>   User token for X-Custom-Token. Defaults to $TTAT_USER_TOKEN.
  -h, --help           Show help.

trigger options:
  --branch <name>              Git branch to run.
  --directory-path <path>      Test directory path in api-test. Repeatable.
  --username <name>            Trigger username / plan owner / notify user.
  --tag-env <tag_env>          runtime_config sent to TTAT.
  --idc <idc>                  IDC sent to TTAT.
  --reruns <n>                 Optional rerun count. Default: 0.
  --disable-parallel           Set disable_parallel=true.
  --resolve                    After trigger, also call get-trigger-result.
  --wait-seconds <n>           Max seconds to wait when --resolve is used. Default: 0.
  --poll-interval <n>          Poll interval seconds for --resolve. Default: 3.

get-trigger-result options:
  --uuid <uuid>                Trigger UUID returned by TTAT.
  --wait-seconds <n>           Poll up to N seconds until plan/task appears. Default: 0.
  --poll-interval <n>          Poll interval seconds. Default: 3.

Examples:
  ttat_execute.sh trigger \
    --branch feat/api-mind \
    --directory-path tests/pipeline_and_release/music_mcs/llm_gen/tiktok_feed_fyp_api \
    --username alice \
    --tag-env prod \
    --idc sg1 \
    --user-token "$TTAT_USER_TOKEN"

  ttat_execute.sh trigger \
    --branch feat/api-mind \
    --directory-path tests/pipeline_and_release/music_mcs/llm_gen/tiktok_feed_fyp_api \
    --username alice \
    --tag-env prod \
    --idc sg1 \
    --resolve --wait-seconds 30

  ttat_execute.sh get-trigger-result \
    --uuid 12345678-abcd-ef00-1234-abcdef123456 \
    --wait-seconds 30
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
  local expr="$2"
  python3 - "$file" "$expr" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expr = sys.argv[2]
data = json.loads(path.read_text(encoding='utf-8'))
value = data
for part in expr.split('.'):
    if part == '':
        continue
    if isinstance(value, list):
        idx = int(part)
        value = value[idx]
    else:
        value = value[part]
if isinstance(value, (dict, list)):
    print(json.dumps(value, ensure_ascii=False))
elif value is None:
    print('')
else:
    print(value)
PY
}

build_trigger_payload() {
  local branch="$1"
  local username="$2"
  local tag_env="$3"
  local idc="$4"
  local reruns="$5"
  local disable_parallel="$6"
  shift 6
  python3 - "$branch" "$username" "$tag_env" "$idc" "$reruns" "$disable_parallel" "$@" <<'PY'
import json
import sys
branch, username, tag_env, idc, reruns, disable_parallel, *directory_paths = sys.argv[1:]
payload = {
    "branch": branch,
    "directory_paths": directory_paths,
    "plan_type": "regular",
    "reruns": int(reruns),
    "notify_users": [username],
    "disable_parallel": disable_parallel.lower() == "true",
    "environment_configuration": [{
        "env_params": {},
        "runtime_config": tag_env,
        "idc": idc,
    }],
    "trigger_by": username,
    "trigger_platform": "manual",
    "plan_owner": username,
    "markers": [],
    "test_names": [],
}
print(json.dumps(payload, ensure_ascii=False))
PY
}

call_api() {
  local method="$1"
  local url="$2"
  local token="$3"
  local output_file="$4"
  local body_file="${5:-}"

  local http_code
  if [[ -n "$body_file" ]]; then
    http_code=$(curl -sS -X "$method" \
      -H "X-Custom-Token: $token" \
      -H 'Content-Type: application/json' \
      --data @"$body_file" \
      -o "$output_file" \
      -w '%{http_code}' \
      "$url")
  else
    http_code=$(curl -sS -X "$method" \
      -H "X-Custom-Token: $token" \
      -o "$output_file" \
      -w '%{http_code}' \
      "$url")
  fi

  if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
    log "HTTP request failed with code $http_code"
    cat "$output_file" >&2 || true
    return 1
  fi
}

print_trigger_result() {
  local file="$1"
  local uuid
  uuid=$(json_get "$file" 'job_infos.0.uuid') || die "Failed to parse trigger uuid"
  printf 'TTAT_TRIGGER_UUID=%s\n' "$uuid"
}

print_plan_result() {
  local file="$1"
  local plan_id task_id
  plan_id=$(json_get "$file" 'execution_info.plan_id') || die "Failed to parse plan_id"
  task_id=$(json_get "$file" 'execution_info.task_id') || die "Failed to parse task_id"
  printf 'TTAT_PLAN_ID=%s\n' "$plan_id"
  printf 'TTAT_TASK_ID=%s\n' "$task_id"
  printf 'TTAT_EXECUTION_URL=%s/api/test_plans/%s/jobs/%s\n' "https://ttat-us.byteintl.net" "$plan_id" "$task_id"
}

validate_base_resp() {
  local file="$1"
  local status_code
  status_code=$(json_get "$file" 'base_resp.status_code') || die "Failed to parse base_resp.status_code"
  if [[ "$status_code" != "200" ]]; then
    log "API returned non-success base_resp.status_code=$status_code"
    cat "$file" >&2 || true
    return 1
  fi
}

resolve_trigger_result() {
  local api_base="$1"
  local token="$2"
  local uuid="$3"
  local wait_seconds="$4"
  local poll_interval="$5"

  local url="${api_base}/ttat/test/api-test/task-from-job/${uuid}"
  local started_at now elapsed
  started_at=$(date +%s)

  while true; do
    local resp_file
    resp_file=$(mktemp)
    if call_api GET "$url" "$token" "$resp_file"; then
      if validate_base_resp "$resp_file"; then
        local plan_id task_id
        plan_id=$(json_get "$resp_file" 'execution_info.plan_id' 2>/dev/null || true)
        task_id=$(json_get "$resp_file" 'execution_info.task_id' 2>/dev/null || true)
        if [[ -n "$plan_id" && -n "$task_id" ]]; then
          print_plan_result "$resp_file"
          rm -f "$resp_file"
          return 0
        fi
      fi
    fi
    rm -f "$resp_file"

    if [[ "$wait_seconds" -le 0 ]]; then
      return 1
    fi

    now=$(date +%s)
    elapsed=$((now - started_at))
    if [[ "$elapsed" -ge "$wait_seconds" ]]; then
      return 1
    fi
    sleep "$poll_interval"
  done
}

main() {
  require_cmd curl
  require_cmd python3

  local command="${1:-}"
  [[ -n "$command" ]] || {
    usage
    exit 1
  }
  shift || true

  local api_base=""
  local use_prod="false"
  local token="${TTAT_USER_TOKEN:-}"

  case "$command" in
    trigger)
      local branch=""
      local username=""
      local tag_env=""
      local idc=""
      local reruns="0"
      local disable_parallel="false"
      local resolve="false"
      local wait_seconds="0"
      local poll_interval="3"
      local -a directory_paths=()

      while [[ $# -gt 0 ]]; do
        case "$1" in
          --api-base) api_base="$2"; shift 2 ;;
          --prod) use_prod="true"; shift ;;
          --user-token) token="$2"; shift 2 ;;
          --branch) branch="$2"; shift 2 ;;
          --directory-path) directory_paths+=("$2"); shift 2 ;;
          --username) username="$2"; shift 2 ;;
          --tag-env) tag_env="$2"; shift 2 ;;
          --idc) idc="$2"; shift 2 ;;
          --reruns) reruns="$2"; shift 2 ;;
          --disable-parallel) disable_parallel="true"; shift ;;
          --resolve) resolve="true"; shift ;;
          --wait-seconds) wait_seconds="$2"; shift 2 ;;
          --poll-interval) poll_interval="$2"; shift 2 ;;
          -h|--help) usage; exit 0 ;;
          *) die "Unknown option for trigger: $1" ;;
        esac
      done

      [[ -n "$branch" ]] || die "--branch is required"
      [[ ${#directory_paths[@]} -gt 0 ]] || die "At least one --directory-path is required"
      [[ -n "$username" ]] || die "--username is required"
      [[ -n "$tag_env" ]] || die "--tag-env is required"
      [[ -n "$idc" ]] || die "--idc is required"
      [[ -n "$token" ]] || die "User token is required via --user-token or TTAT_USER_TOKEN"

      if [[ -z "$api_base" ]]; then
        if [[ "$use_prod" == "true" ]]; then
          api_base="$DEFAULT_TTAT_API_BASE_PROD"
        else
          api_base="$DEFAULT_TTAT_API_BASE"
        fi
      fi

      local payload_file resp_file url uuid
      payload_file=$(mktemp)
      resp_file=$(mktemp)
      build_trigger_payload "$branch" "$username" "$tag_env" "$idc" "$reruns" "$disable_parallel" "${directory_paths[@]}" > "$payload_file"
      url="${api_base}/ttat/test/api-test/trigger"

      call_api POST "$url" "$token" "$resp_file" "$payload_file"
      validate_base_resp "$resp_file"
      print_trigger_result "$resp_file"
      uuid=$(json_get "$resp_file" 'job_infos.0.uuid')

      rm -f "$payload_file"
      rm -f "$resp_file"

      if [[ "$resolve" == "true" ]]; then
        if ! resolve_trigger_result "$api_base" "$token" "$uuid" "$wait_seconds" "$poll_interval"; then
          die "Triggered successfully, but failed to resolve plan/task from uuid=${uuid}"
        fi
      fi
      ;;

    get-trigger-result)
      local uuid=""
      local wait_seconds="0"
      local poll_interval="3"

      while [[ $# -gt 0 ]]; do
        case "$1" in
          --api-base) api_base="$2"; shift 2 ;;
          --prod) use_prod="true"; shift ;;
          --user-token) token="$2"; shift 2 ;;
          --uuid) uuid="$2"; shift 2 ;;
          --wait-seconds) wait_seconds="$2"; shift 2 ;;
          --poll-interval) poll_interval="$2"; shift 2 ;;
          -h|--help) usage; exit 0 ;;
          *) die "Unknown option for get-trigger-result: $1" ;;
        esac
      done

      [[ -n "$uuid" ]] || die "--uuid is required"
      [[ -n "$token" ]] || die "User token is required via --user-token or TTAT_USER_TOKEN"

      if [[ -z "$api_base" ]]; then
        if [[ "$use_prod" == "true" ]]; then
          api_base="$DEFAULT_TTAT_API_BASE_PROD"
        else
          api_base="$DEFAULT_TTAT_API_BASE"
        fi
      fi

      if ! resolve_trigger_result "$api_base" "$token" "$uuid" "$wait_seconds" "$poll_interval"; then
        die "Failed to resolve trigger result for uuid=${uuid}"
      fi
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
