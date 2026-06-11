#!/bin/sh
# telemetry.sh — Self-contained skill telemetry (start + end spans)
# Usage: sh telemetry.sh start | sh telemetry.sh end [status] [message]
# Requires: sh, curl, od, tr, grep, cut, sed, date. No python, no jq, no openssl.
set +e

# ── Args ──────────────────────────────────────────────────────────────────────
MODE="${1:-start}"

# ── Script dir resolution (for meta.json only) ────────────────────────────────
raw_dir="$(dirname "$0")"
skill_dir="${AGENTBUDDY_SKILL_DIR:-}"
if [ -n "$skill_dir" ]; then
  case "$skill_dir" in /*) ;; *) skill_dir="$(pwd)/$skill_dir" ;; esac
fi
if [ -n "$skill_dir" ] && [ -d "$skill_dir/.agentbuddy" ]; then
  SCRIPT_DIR="$skill_dir/.agentbuddy"
elif [ -n "$skill_dir" ] && [ -d "$skill_dir" ]; then
  SCRIPT_DIR="$skill_dir"
else
  case "$raw_dir" in
    /*) SCRIPT_DIR="$raw_dir" ;;
    *) SCRIPT_DIR="$(pwd)/$raw_dir" ;;
  esac
fi

# ── Debug ─────────────────────────────────────────────────────────────────────
dbg() {
  [ "${AGENTBUDDY_DEBUG:-0}" = "1" ] || return 0
  printf '[ai-ext-tel] %s\n' "$*" >&2
  { printf '[ai-ext-tel] [%s] %s\n' "$(date '+%H:%M:%S' 2>/dev/null)" "$*" \
    >> "${AGENTBUDDY_LOG:-${TMPDIR:-/tmp}/.agentbuddy_debug.log}"; } 2>/dev/null
  return 0
}

dbg "telemetry.sh mode=$MODE SCRIPT_DIR=$SCRIPT_DIR"

# ── Portable millisecond timestamp ────────────────────────────────────────────
now_ms() {
  _t=$(date +%s%3N 2>/dev/null)
  case "$_t" in *N*|*%*|"") _t=$(( $(date +%s) * 1000 )) ;; esac
  printf '%s' "$_t"
}

# ── Portable random hex ───────────────────────────────────────────────────────
hex() {
  _out=$(od -An -tx1 -N"$1" /dev/urandom 2>/dev/null | tr -d ' \n\t')
  if [ -z "$_out" ]; then
    _seed=$(( $$ + $(date +%s) ))
    _out=""
    _i=0
    while [ "$_i" -lt "$1" ]; do
      _seed=$(( (_seed * 1103515245 + 12345) % 2147483648 ))
      _out="${_out}$(printf '%02x' "$(( (_seed / 65536) % 256 ))")"
      _i=$(( _i + 1 ))
    done
  fi
  printf '%s' "$_out"
}

# ── UUID v4 ───────────────────────────────────────────────────────────────────
uuid() {
  _h=$(hex 16)
  _u1=$(printf '%s' "$_h" | cut -c1-8)
  _u2=$(printf '%s' "$_h" | cut -c9-12)
  _u3="4$(printf '%s' "$_h" | cut -c14-16)"
  _vc=$(printf '%s' "$_h" | cut -c17)
  case "$_vc" in
    0|4|8|c|C) _vc=8 ;; 1|5|9|d|D) _vc=9 ;;
    2|6|a|A|e|E) _vc=a ;; 3|7|b|B|f|F) _vc=b ;;
  esac
  _u4="${_vc}$(printf '%s' "$_h" | cut -c18-20)"
  _u5=$(printf '%s' "$_h" | cut -c21-32)
  printf '%s-%s-%s-%s-%s' "$_u1" "$_u2" "$_u3" "$_u4" "$_u5"
}

# ── JSON helpers ──────────────────────────────────────────────────────────────
jread() { grep "\"${1}\"[[:space:]]*:" "$META" 2>/dev/null | head -1 | sed 's/.*"'"$1"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'; }

jv() {
  if [ -z "$1" ] || [ "$1" = "null" ]; then printf 'null'
  else printf '"%s"' "$(printf '%s' "$1" | tr '\n\r\t' '   ' | sed 's/\\/\\\\/g; s/"/\\"/g')"; fi
}

jv_str() {
  printf '"%s"' "$(printf '%s' "${1:-null}" | tr '\n\r\t' '   ' | sed 's/\\/\\\\/g; s/"/\\"/g')"
}

# ── POST event ────────────────────────────────────────────────────────────────
send_event() {
  dbg "payload: $1"
  if [ "${AGENTBUDDY_DEBUG:-0}" = "1" ]; then
    curl -s -X POST 'https://mcs.zijieapi.com/list?aid=1009601' \
      -H 'accept: */*' \
      -H 'content-type: application/json; charset=UTF-8' \
      -H 'referer: https://skills.bytedance.net/' \
      --max-time 5 --retry 2 \
      --data-raw "$1" >&2 || true
    printf '\n' >&2
  else
    curl -s -o /dev/null \
      -X POST 'https://mcs.zijieapi.com/list?aid=1009601' \
      -H 'accept: */*' \
      -H 'content-type: application/json; charset=UTF-8' \
      -H 'referer: https://skills.bytedance.net/' \
      --max-time 5 --retry 2 \
      --data-raw "$1" 2>/dev/null || true
  fi
}

# ── Username resolution (inlined) ────────────────────────────────────────────
resolve_username() {
  [ -n "${AGENTBUDDY_USERNAME:-}" ] && return 0

  _run_with_timeout() {
    _secs="$1"; shift
    if command -v timeout >/dev/null 2>&1; then
      timeout "$_secs" "$@" 2>/dev/null
    elif command -v gtimeout >/dev/null 2>&1; then
      gtimeout "$_secs" "$@" 2>/dev/null
    else
      "$@" 2>/dev/null &
      _pid=$!
      ( sleep "$_secs" && kill "$_pid" 2>/dev/null ) &
      _guard=$!
      wait "$_pid" 2>/dev/null
      _rc=$?
      kill "$_guard" 2>/dev/null
      wait "$_guard" 2>/dev/null
      return $_rc
    fi
  }

  _resolved=""

  # Strategy: AgentBuddy credentials
  if [ -z "$_resolved" ] && [ -f "$HOME/.agentbuddy/credentials.json" ]; then
    _resolved=$(grep '"username"[[:space:]]*:' "$HOME/.agentbuddy/credentials.json" 2>/dev/null | head -1 | sed 's/.*"username"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | tr -d ' \t\r\n')
    case "$_resolved" in *[\":]*) _resolved="" ;; esac
  fi

  # Strategy: AIPaaS (legacy)
  if [ -z "$_resolved" ] && [ -f "$HOME/.aipaas/user.yml" ]; then
    _resolved=$(grep -m1 '^username:' "$HOME/.aipaas/user.yml" 2>/dev/null | sed 's/^username:[[:space:]]*//' | sed "s/^[\"']//; s/[\"']$//" | tr -d ' \t\r')
  fi

  # Strategy: bytedcli userinfo
  if [ -z "$_resolved" ] && [ -f "$HOME/.local/share/bytedcli/data/userinfo.json" ]; then
    _resolved=$(grep '"username"[[:space:]]*:' "$HOME/.local/share/bytedcli/data/userinfo.json" 2>/dev/null | head -1 | sed 's/.*"username"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | tr -d ' \t\r\n')
    case "$_resolved" in *[\":]*) _resolved="" ;; esac
  fi

  # Strategy: MIRA env
  if [ -z "$_resolved" ]; then
    _resolved=$(printf '%s' "${MIRA_CURRENT_USERNAME:-}" | tr -d ' \t\r\n')
  fi

  # Strategy: Kerberos
  if [ -z "$_resolved" ]; then
    _out=$(_run_with_timeout 3 /usr/bin/klist 2>/dev/null) && \
    _resolved=$(printf '%s' "$_out" | grep -i '[Pp]rincipal:' | head -1 | sed 's/.*[Pp]rincipal:[[:space:]]*//' | cut -d'@' -f1 | tr -d ' \t\r')
  fi

  # Strategy: Git email
  if [ -z "$_resolved" ]; then
    _out=$(_run_with_timeout 3 git config user.email 2>/dev/null) && \
    _resolved=$(printf '%s' "$_out" | tr -d ' \t\r\n' | grep -oE '[A-Za-z0-9._+-]+@[A-Za-z0-9._+-]+' | head -1 | cut -d'@' -f1)
  fi

  # Strategy: OS fallback
  if [ -z "$_resolved" ]; then
    _resolved=$(id -un 2>/dev/null) || _resolved="unknown"
  fi

  AGENTBUDDY_USERNAME="${_resolved:-unknown}"
  export AGENTBUDDY_USERNAME
  dbg "resolve_username: resolved to '$AGENTBUDDY_USERNAME'"
}

# ── Read metadata ─────────────────────────────────────────────────────────────
META="$SCRIPT_DIR/meta.json"
SKILL_NAME=$(jread name)
SKILL_ID=$(jread identifier)
SKILL_VERSION=$(jread version)
SKILL_NAME="${SKILL_NAME:-null}"
SKILL_ID="${SKILL_ID:-null}"
SKILL_VERSION="${SKILL_VERSION:-null}"
dbg "metadata: name=$SKILL_NAME id=$SKILL_ID version=$SKILL_VERSION"

# ── Resolve username ──────────────────────────────────────────────────────────
resolve_username

# ── Runtime context ───────────────────────────────────────────────────────────
AGENT_NAME="${AGENTBUDDY_AGENT_NAME:-null}"
AGENT_MODEL="${AGENTBUDDY_AGENT_MODEL:-null}"
USERNAME="${AGENTBUDDY_USERNAME:-unknown}"

# ── Session ID ────────────────────────────────────────────────────────────────
if [ -n "${AGENTBUDDY_SESSION_ID:-}" ] && [ "${AGENTBUDDY_SESSION_ID}" != "null" ]; then
  SESSION_ID="$AGENTBUDDY_SESSION_ID"
else
  SESSION_ID=$(uuid)
fi

# ── State dir (TMPDIR itself — no subdirectory) ───────────────────────────────
STATE_DIR="${TMPDIR:-/tmp}"

# ── Mode dispatch ─────────────────────────────────────────────────────────────
case "$MODE" in
  start)
    SPAN_ID="${AGENTBUDDY_SPAN_ID:-$(hex 8)}"
    START_MS=$(now_ms)
    dbg "span_id=$SPAN_ID session_id=$SESSION_ID start_ms=$START_MS"

    # Opportunistic state file write (fail-silent)
    SAFE_SKILL=$(printf '%s' "$SKILL_NAME" | tr -cs 'a-zA-Z0-9_-' '_')
    STATE_FILE="$STATE_DIR/.agentbuddy_${PPID}_${SAFE_SKILL}.env"
    { printf 'SPAN_ID=%s\nSTART_MS=%s\nSKILL_NAME=%s\nSKILL_ID=%s\nSKILL_VERSION=%s\nSESSION_ID=%s\nUSERNAME=%s\nAGENT_NAME=%s\nAGENT_MODEL=%s\n' \
      "$SPAN_ID" "$START_MS" "$SKILL_NAME" "$SKILL_ID" "$SKILL_VERSION" \
      "$SESSION_ID" "$USERNAME" "$AGENT_NAME" "$AGENT_MODEL" \
      > "$STATE_FILE"; } 2>/dev/null
    dbg "state file write attempted: $STATE_FILE"

    # Build and POST start event
    PARAMS=$(printf '{"span_id":%s,"name":"skill.invoke","kind":"CLIENT","start_time_ms":%s,"end_time_ms":null,"attributes__skill__name":%s,"attributes__skill__id":%s,"attributes__skill__version":%s,"attributes__skill__result_status":null,"attributes__skill__result_message":null,"attributes__agent__name":%s,"attributes__agent__model":%s}' \
      "$(jv "$SPAN_ID")" "$START_MS" \
      "$(jv "$SKILL_NAME")" "$(jv "$SKILL_ID")" "$(jv "$SKILL_VERSION")" \
      "$(jv "$AGENT_NAME")" "$(jv "$AGENT_MODEL")")
    PARAMS_ESC=$(printf '%s' "$PARAMS" | sed 's/\\/\\\\/g; s/"/\\"/g')
    PAYLOAD=$(printf '[{"events":[{"event":"ai_extension_custom_event","params":"%s","local_time_ms":%s,"is_bav":1,"session_id":%s}],"user":{"user_unique_id":%s},"header":{"app_id":1009601},"verbose":1}]' \
      "$PARAMS_ESC" "$START_MS" "$(jv "$SESSION_ID")" "$(jv_str "$USERNAME")")
    send_event "$PAYLOAD"
    ;;

  end)
    RESULT_STATUS="${2:-success}"
    RESULT_MESSAGE="${3:-}"
    case "$RESULT_STATUS" in
      success|error|abort|timeout|skipped) ;;
      *) dbg "invalid result_status='$RESULT_STATUS', defaulting to 'error'"
         RESULT_STATUS="error" ;;
    esac

    END_MS=$(now_ms)

    # Tier 0: env vars (pre-populated by runtime)
    SPAN_ID="${AGENTBUDDY_SPAN_ID:-$(hex 8)}"
    START_MS="${AGENTBUDDY_START_MS:-$END_MS}"

    # Tier 1: state file (may not exist — that's OK)
    SAFE_SKILL=$(printf '%s' "$SKILL_NAME" | tr -cs 'a-zA-Z0-9_-' '_')
    STATE_FILE="$STATE_DIR/.agentbuddy_${PPID}_${SAFE_SKILL}.env"
    dbg "looking for state file: $STATE_FILE"

    if [ -f "$STATE_FILE" ]; then
      dbg "state file found, restoring"
      _sv() { grep "^${1}=" "$STATE_FILE" 2>/dev/null | head -1 | cut -d= -f2-; }
      _r=$(_sv SPAN_ID);       [ -n "$_r" ] && SPAN_ID="$_r"
      _r=$(_sv START_MS);      [ -n "$_r" ] && START_MS="$_r"
      _r=$(_sv SKILL_NAME);    [ -n "$_r" ] && SKILL_NAME="$_r"
      _r=$(_sv SKILL_ID);      [ -n "$_r" ] && SKILL_ID="$_r"
      _r=$(_sv SKILL_VERSION); [ -n "$_r" ] && SKILL_VERSION="$_r"
      _r=$(_sv SESSION_ID);    [ -n "$_r" ] && SESSION_ID="$_r"
      _r=$(_sv USERNAME);      [ -n "$_r" ] && USERNAME="$_r"
      _r=$(_sv AGENT_NAME);    [ -n "$_r" ] && AGENT_NAME="$_r"
      _r=$(_sv AGENT_MODEL);   [ -n "$_r" ] && AGENT_MODEL="$_r"
    else
      dbg "state file not found — using env vars / degraded mode"
    fi

    dbg "span_id=$SPAN_ID session_id=$SESSION_ID start=$START_MS end=$END_MS"

    # Build and POST end event
    PARAMS=$(printf '{"span_id":%s,"name":"skill.invoke","kind":"CLIENT","start_time_ms":%s,"end_time_ms":%s,"attributes__skill__name":%s,"attributes__skill__id":%s,"attributes__skill__version":%s,"attributes__skill__result_status":%s,"attributes__skill__result_message":%s,"attributes__agent__name":%s,"attributes__agent__model":%s}' \
      "$(jv "$SPAN_ID")" "$START_MS" "$END_MS" \
      "$(jv "$SKILL_NAME")" "$(jv "$SKILL_ID")" "$(jv "$SKILL_VERSION")" \
      "$(jv "$RESULT_STATUS")" "$(jv "$RESULT_MESSAGE")" \
      "$(jv "$AGENT_NAME")" "$(jv "$AGENT_MODEL")")
    PARAMS_ESC=$(printf '%s' "$PARAMS" | sed 's/\\/\\\\/g; s/"/\\"/g')
    PAYLOAD=$(printf '[{"events":[{"event":"ai_extension_custom_event","params":"%s","local_time_ms":%s,"is_bav":1,"session_id":%s}],"user":{"user_unique_id":%s},"header":{"app_id":1009601},"verbose":1}]' \
      "$PARAMS_ESC" "$END_MS" "$(jv "$SESSION_ID")" "$(jv_str "$USERNAME")")
    send_event "$PAYLOAD"
    ;;

  *)
    dbg "unknown mode: $MODE"
    exit 1
    ;;
esac

dbg "telemetry.sh done (mode=$MODE)"
