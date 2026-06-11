#!/usr/bin/env bash

# ==========================================
# API-Mind 安装脚本
# 下载最新版本的 api-mind 并安装到 ~/.local/bin/
# ==========================================

set -e

TOOL_NAME="api-mind"
DOWNLOAD_URL_MACOS="https://cdn-tos-cn.bytedance.net/obj/regression-case-prioritization-cn/api-mind/api-mind"
DOWNLOAD_URL_LINUX="https://cdn-tos-cn.bytedance.net/obj/regression-case-prioritization-cn/api-mind/api-mind-linux"
INSTALL_DIR="${HOME}/.local/bin"

# ==========================================
# 工具函数
# ==========================================

check_platform() {
    local os_type arch
    os_type="$(uname -s)"
    arch="$(uname -m)"

    case "$os_type" in
        Darwin)
            if [[ "$arch" == "arm64" ]]; then
                echo "⚠️  Detected Apple Silicon (arm64)." >&2
                echo "   Note: The binary is x86_64 and will run via Rosetta 2." >&2
            fi
            echo "$DOWNLOAD_URL_MACOS"
            ;;
        Linux)
            echo "$DOWNLOAD_URL_LINUX"
            ;;
        *)
            echo "[Error] Unsupported platform: $os_type" >&2
            echo "This tool only supports macOS (Darwin) and Linux." >&2
            exit 1
            ;;
    esac
}

# ==========================================
# 主逻辑
# ==========================================

main() {
    local download_url
    download_url="$(check_platform)"

    mkdir -p "$INSTALL_DIR"

    local dest_path="${INSTALL_DIR}/${TOOL_NAME}"
    local tmp_path="${dest_path}.tmp.$$"

    rm -f "$tmp_path" 2>/dev/null

    echo "正在下载 ${TOOL_NAME}..."

    local cache_buster="?v=$(date +%s)"
    local final_url="${download_url}${cache_buster}"
    
    echo "Downloading from: ${final_url}"

    if command -v curl &>/dev/null; then
        curl -fsSL --connect-timeout 10 --max-time 300 -o "$tmp_path" "${final_url}"
    elif command -v wget &>/dev/null; then
        wget -q --timeout=300 -O "$tmp_path" "${final_url}"
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
