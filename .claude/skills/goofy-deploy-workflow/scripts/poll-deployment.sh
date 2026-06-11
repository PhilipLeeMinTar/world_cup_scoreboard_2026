#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  poll-deployment.sh --deploy-id <id> [--site <cn|boe>] [--interval <seconds>] [--max-minutes <minutes>]

Examples:
  ./scripts/poll-deployment.sh --deploy-id 25436495 --site cn
  ./scripts/poll-deployment.sh --deploy-id 25436495 --site cn --interval 30 --max-minutes 30
EOF
}

DEPLOY_ID=""
SITE="cn"
INTERVAL_SECONDS="30"
MAX_MINUTES="30"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deploy-id)
      DEPLOY_ID="${2:-}"; shift 2 ;;
    --site)
      SITE="${2:-}"; shift 2 ;;
    --interval)
      INTERVAL_SECONDS="${2:-}"; shift 2 ;;
    --max-minutes)
      MAX_MINUTES="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$DEPLOY_ID" ]]; then
  echo "Missing required --deploy-id" >&2
  usage
  exit 2
fi

if [[ "$SITE" != "cn" && "$SITE" != "boe" ]]; then
  echo "Invalid --site: $SITE (expected cn|boe)" >&2
  exit 2
fi

if ! [[ "$INTERVAL_SECONDS" =~ ^[0-9]+$ ]] || [[ "$INTERVAL_SECONDS" -le 0 ]]; then
  echo "Invalid --interval: $INTERVAL_SECONDS (expected positive integer)" >&2
  exit 2
fi

if ! [[ "$MAX_MINUTES" =~ ^[0-9]+$ ]] || [[ "$MAX_MINUTES" -le 0 ]]; then
  echo "Invalid --max-minutes: $MAX_MINUTES (expected positive integer)" >&2
  exit 2
fi

MAX_POLLS=$(( (MAX_MINUTES * 60) / INTERVAL_SECONDS ))
if [[ "$MAX_POLLS" -lt 1 ]]; then
  MAX_POLLS=1
fi

BYTEDCLI=("env" "NPM_CONFIG_REGISTRY=http://bnpm.byted.org" "npx" "-y" "@bytedance-dev/bytedcli@latest")

for ((i=1; i<=MAX_POLLS; i++)); do
  # bytedcli/network errors are common; do NOT exit the whole script.
  # Capture both stdout/stderr so we can always print something for each poll.
  set +e
  OUT=$(${BYTEDCLI[@]} --json goofy-deploy get-deployment --deploy-id "$DEPLOY_ID" --site "$SITE" 2>&1)
  BYTEDCLI_EXIT_CODE=$?
  set -e

  if [[ "$BYTEDCLI_EXIT_CODE" -ne 0 ]]; then
    DEPLOY_ID="$DEPLOY_ID" SITE="$SITE" python3 -u -c 'import json,os,sys
payload = {
  "type": "deployment_poll",
  "ok": False,
  "error": "bytedcli_failed",
  "deployId": os.environ.get("DEPLOY_ID"),
  "site": os.environ.get("SITE"),
  "exitCode": int(os.environ.get("BYTEDCLI_EXIT_CODE", "-1")),
  "message": sys.stdin.read().strip(),
}
print(json.dumps(payload, ensure_ascii=False))
' BYTEDCLI_EXIT_CODE="$BYTEDCLI_EXIT_CODE" <<<"$OUT"
    sleep "$INTERVAL_SECONDS"
    continue
  fi

  set +e
  DEPLOY_ID="$DEPLOY_ID" SITE="$SITE" python3 -u -c 'import json,sys,os
raw = sys.stdin.read()
try:
  j = json.loads(raw)
except Exception as e:
  payload = {
    "type": "deployment_poll",
    "ok": False,
    "error": "parse_error",
    "message": str(e),
    "deployId": os.environ.get("DEPLOY_ID"),
    "site": os.environ.get("SITE"),
  }
  print(json.dumps(payload, ensure_ascii=False))
  sys.exit(1)

d = (j.get("data") or {}).get("deployment") or {}
scm = ((d.get("configForWebApp") or {}).get("configForScmArtifactSource") or {})

status = d.get("status")
end_time = d.get("endTime")

status_text = None
if isinstance(status, str) and status.strip():
  status_text = status.strip()
elif isinstance(status, int):
  # 以 bytedcli 表格输出为准：已观察到 2=running, 5=cancelled
  status_text = {
    1: "pending",
    2: "running",
    3: "success",
    4: "failed",
    5: "cancelled",
  }.get(status, f"code_{status}")

payload = {
  "type": "deployment_poll",
  "ok": True,
  "deployId": os.environ.get("DEPLOY_ID"),
  "site": os.environ.get("SITE"),
  "status": status_text,
  "endTime": end_time,
  "channelId": d.get("channelId"),
  "scmName": scm.get("scmName"),
  "scmVersion": scm.get("scmVersion"),
  "branch": scm.get("gitBranch"),
  "commit": scm.get("commitHash"),
}

print(json.dumps(payload, ensure_ascii=False))

# 以 endTime 是否存在作为“终态”判定，兼容平台新增的状态枚举（例如 superseded 等）
sys.exit(0 if end_time else 3)
' <<<"$OUT"
  EXIT_CODE=$?
  set -e

  if [[ "$EXIT_CODE" -eq 0 ]]; then
    exit 0
  fi
  sleep "$INTERVAL_SECONDS"
done

DEPLOY_ID="$DEPLOY_ID" SITE="$SITE" python3 -u -c 'import json,os
payload = {
  "type": "deployment_poll",
  "ok": False,
  "error": "timeout",
  "deployId": os.environ.get("DEPLOY_ID"),
  "site": os.environ.get("SITE"),
}
print(json.dumps(payload, ensure_ascii=False))
'
exit 4
