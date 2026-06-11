#!/usr/bin/env bash
# run_api_test.sh — 在任意位置调用 api_test 仓库里的命令。
#
# 背景：api_test 的 pyproject.toml、conftest.py、顶层 import
# (state / constants / clients / common / tools)、以及部分 shell 脚本都假定
# cwd == api_test 仓库根，否则 pytest rootdir、import、日志目录都可能出错。
# 本脚本统一先切到 api_test 仓库，再透传命令。
#
# Usage:
#   scripts/run_api_test.sh                                  # 显示用法
#   scripts/run_api_test.sh --api-test-dir /path/to/api_test pytest <args>
#   API_TEST_REPO=/path/to/api_test scripts/run_api_test.sh test <case_path>
#   scripts/run_api_test.sh pytest <args>                    # 兼容旧方式：若脚本位于外层仓库 scripts/ 且 ../tests/api_test 存在
#   scripts/run_api_test.sh manage <args>                    # poetry run python manage.py <args>
#   scripts/run_api_test.sh python <args>                    # poetry run python <args>
#   scripts/run_api_test.sh poetry <args>                    # poetry <args>（不进 venv）
#   scripts/run_api_test.sh shell                            # 启子 shell，cwd=api_test，激活 .venv
#   scripts/run_api_test.sh -- <cmd> [args...]               # 任意命令透传到 poetry run
#
# Options:
#   --api-test-dir, --api-test-repo <dir>    显式指定 api_test 仓库根目录
#
# Env:
#   API_TEST_REPO / API_TEST_DIR             指定 api_test 仓库根目录
#
# 例子：
#   scripts/run_api_test.sh --api-test-dir /repo/tests/api_test pytest tests/content_discovery/.../test_xxx.py -k some_case
#   API_TEST_REPO=/repo/tests/api_test scripts/run_api_test.sh test tests/content_discovery/search/cases/tiktok/tiktok_function_allure/api_vertical/test_tiktok_music_middle_page.py
#   scripts/run_api_test.sh --api-test-dir /repo/tests/api_test python tests/content_discovery/.../scripts/create_test_plan_ttat_http.py
#   scripts/run_api_test.sh --api-test-dir /repo/tests/api_test -- python -m pytest tests/...

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_TEST_DIR_INPUT="${API_TEST_REPO:-${API_TEST_DIR:-}}"
API_TEST_DIR=""
API_TEST_DIR_SOURCE=""

resolve_api_test_dir() {
    local candidate=""
    if [[ -n "$API_TEST_DIR_INPUT" ]]; then
        candidate="$API_TEST_DIR_INPUT"
        API_TEST_DIR_SOURCE="explicit"
    elif [[ -d "$SCRIPT_DIR/../tests/api_test" ]]; then
        candidate="$SCRIPT_DIR/../tests/api_test"
        API_TEST_DIR_SOURCE="legacy_outer_repo"
    elif [[ -f "$SCRIPT_DIR/../pyproject.toml" ]]; then
        candidate="$SCRIPT_DIR/.."
        API_TEST_DIR_SOURCE="script_parent"
    else
        echo "[ERR] api_test repo not specified." >&2
        echo "      请通过 '--api-test-dir /path/to/api_test'，或环境变量 'API_TEST_REPO=/path/to/api_test' 指定。" >&2
        exit 1
    fi

    if [[ ! -d "$candidate" ]]; then
        echo "[ERR] api_test repo not found at $candidate" >&2
        exit 1
    fi

    API_TEST_DIR="$(cd "$candidate" && pwd)"

    if [[ ! -f "$API_TEST_DIR/pyproject.toml" ]]; then
        echo "[ERR] $API_TEST_DIR/pyproject.toml missing — 指定目录看起来不是完整的 api_test 仓库" >&2
        exit 1
    fi
}

usage() {
    sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    echo
    if [[ -n "$API_TEST_DIR_INPUT" ]] || [[ -d "$SCRIPT_DIR/../tests/api_test" ]] || [[ -f "$SCRIPT_DIR/../pyproject.toml" ]]; then
        resolve_api_test_dir
        echo "[INFO] api_test repo: $API_TEST_DIR (source=$API_TEST_DIR_SOURCE)"
        if [[ -d "$API_TEST_DIR/.venv" ]]; then
            echo "[INFO] in-project venv detected: $API_TEST_DIR/.venv"
        else
            echo "[WARN] $API_TEST_DIR/.venv not found — 先在 api_test 仓库里跑 'poetry install'"
        fi
    else
        echo "[INFO] api_test repo: unresolved"
    fi
}

# Preflight: warn about missing env vars that historically caused SKIP / crash.
# 想关掉就 export RUN_API_TEST_QUIET=1。
preflight_env_warn() {
    [[ -n "${RUN_API_TEST_QUIET:-}" ]] && return 0
    local missing=()
    [[ -z "${TEST_ENV:-}" ]] && \
        missing+=("TEST_ENV — 不设会兜底成 boei18n，duck-sdk 读 testdata 时常找不到对应顶层 region key → 全部 SKIPPED（参考值: sg_prod / va_prod / ttp_prod 等）")
    [[ -z "${IDC_ENV:-}" ]] && \
        missing+=("IDC_ENV — 不设时 downgrade_sdk() 会拿到空字符串，host_list.get('') 返回 None 直接 TypeError（参考值: my / sg / va）")
    [[ -z "${DUCK_AUTH_TOKEN:-}" && -z "${SECRET_KEY_TOKEN:-}" ]] && \
        missing+=("DUCK_AUTH_TOKEN — TTAT API 鉴权，缺则 read_test_data / 上传脚本会失败（从 https://ttat-us.byteintl.net/api/auth 拿）")
    if [[ ${#missing[@]} -gt 0 ]]; then
        {
            echo
            echo "[run_api_test.sh] WARN 以下环境变量未设置，常见后果如下："
            for m in "${missing[@]}"; do echo "  - $m"; done
            echo
            echo "  本地常用一键设置："
            echo "    export TEST_ENV=sg_prod IDC_ENV=my TAG_ENV=prod DUCK_AUTH_TOKEN=<your-token>"
            echo "  关掉本提示：export RUN_API_TEST_QUIET=1"
            echo
        } >&2
    fi
}

while [[ $# -gt 0 ]]; do
    case "${1:-}" in
        --api-test-dir|--api-test-repo)
            if [[ $# -lt 2 ]]; then
                echo "[ERR] $1 需要一个目录参数" >&2
                exit 2
            fi
            API_TEST_DIR_INPUT="$2"
            shift 2
            ;;
        --api-test-dir=*|--api-test-repo=*)
            API_TEST_DIR_INPUT="${1#*=}"
            shift
            ;;
        -h|--help|help)
            usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

resolve_api_test_dir
cd "$API_TEST_DIR"

cmd="$1"; shift

# poetry/shell 这两个子命令本身不进 case 执行体（poetry 仅做依赖管理；shell 让用户进去再 export），
# 跳过 preflight 以免噪音；其余命令（pytest/test/manage/python/--/默认透传）都会真正跑 case，做预检。
case "$cmd" in
    poetry|shell) ;;
    *) preflight_env_warn ;;
esac

case "$cmd" in
    pytest|python|poetry)
        if [[ "$cmd" == "poetry" ]]; then
            exec poetry "$@"
        fi
        exec poetry run "$cmd" "$@"
        ;;
    test)
        # 便捷别名：pytest -v
        exec poetry run pytest -v "$@"
        ;;
    manage)
        exec poetry run python manage.py "$@"
        ;;
    shell)
        if [[ -f .venv/bin/activate ]]; then
            exec bash --rcfile <(cat <<'EOF'
[[ -f ~/.bashrc ]] && source ~/.bashrc
source .venv/bin/activate
echo "[run_api_test.sh] entered api_test venv (cwd=$PWD)"
EOF
)
        else
            echo "[WARN] .venv 不存在，启动普通子 shell（先去子仓里跑 poetry install）" >&2
            exec "${SHELL:-bash}"
        fi
        ;;
    --)
        if [[ $# -eq 0 ]]; then
            echo "[ERR] '--' 后面要带要执行的命令" >&2
            exit 2
        fi
        exec poetry run "$@"
        ;;
    *)
        # 默认透传给 poetry run，便于 `scripts/run_api_test.sh allure ...` 这种
        exec poetry run "$cmd" "$@"
        ;;
esac
