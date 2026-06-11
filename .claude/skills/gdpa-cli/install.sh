#!/usr/bin/env bash

# ==========================================
# GDPA CLI 安装脚本
# 下载最新版本的 gdpa-cli 并安装到 ~/.local/bin/
# ==========================================

set -e

TOOL_NAME="gdpa-cli"
BINARY_BASE_URL="https://cdn-tos-cn.bytedance.net/obj/archi/gdpa_agents"
INSTALL_DIR="${HOME}/.local/bin"

# ==========================================
# 工具函数
# ==========================================

# 获取平台后缀
get_platform_suffix() {
    local os_type arch
    os_type="$(uname -s)"
    arch="$(uname -m)"

    case "$os_type" in
        CYGWIN*|MINGW*|MSYS*|Windows*)
            echo "[Error] Windows is not supported." >&2
            exit 1
            ;;
        Darwin)
            case "$arch" in
                x86_64) echo "darwin-amd64" ;;
                arm64)  echo "darwin-arm64" ;;
                *)
                    echo "[Error] Unsupported architecture: $arch on macOS" >&2
                    exit 1
                    ;;
            esac
            ;;
        Linux)
            case "$arch" in
                x86_64)  echo "linux-amd64" ;;
                aarch64) echo "linux-arm64" ;;
                *)
                    echo "[Error] Unsupported architecture: $arch on Linux" >&2
                    exit 1
                    ;;
            esac
            ;;
        *)
            echo "[Error] Unsupported platform: $os_type $arch" >&2
            exit 1
            ;;
    esac
}

# ==========================================
# 主逻辑
# ==========================================

main() {
    local suffix
    suffix=$(get_platform_suffix) || exit 1

    local binary_filename="${TOOL_NAME}-${suffix}"
    local download_url="${BINARY_BASE_URL}/${binary_filename}"

    # 创建安装目录
    mkdir -p "$INSTALL_DIR"

    local dest_path="${INSTALL_DIR}/${TOOL_NAME}"
    local tmp_path="${dest_path}.tmp.$$"

    # 清理可能存在的旧临时文件
    rm -f "$tmp_path" 2>/dev/null

    echo "正在下载 ${TOOL_NAME}..."

    if command -v curl &>/dev/null; then
        curl -fsSL --connect-timeout 10 --max-time 300 -o "$tmp_path" "$download_url"
    elif command -v wget &>/dev/null; then
        wget -q --timeout=300 -O "$tmp_path" "$download_url"
    else
        echo "[Error] Neither curl nor wget is available." >&2
        exit 1
    fi

    # 检查下载的文件是否有效
    if [[ ! -s "$tmp_path" ]]; then
        echo "[Error] Downloaded file is empty" >&2
        rm -f "$tmp_path" 2>/dev/null
        exit 1
    fi

    # 设置执行权限并安装
    chmod 755 "$tmp_path"
    mv -f "$tmp_path" "$dest_path"

    echo "✅ ${TOOL_NAME} 已安装到 ${dest_path}"

    # 检查安装目录是否在 PATH 中
    if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
        echo ""
        echo "⚠️  ${INSTALL_DIR} 不在 PATH 中，请将以下内容添加到 shell 配置文件（~/.bashrc 或 ~/.zshrc）："
        echo ""
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        echo "然后执行: source ~/.bashrc  (或 source ~/.zshrc)"
    fi

    echo ""
    echo "安装完成。运行 '${TOOL_NAME} --version' 查看版本信息。"
}

main "$@"
