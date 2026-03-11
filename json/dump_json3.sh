#!/bin/bash
# 开启严格模式
set -e

# ================= 1. 定义核心变量 =================
ARCH=$(uname -m)
KVER=$(uname -r)

# 代理配置：187 服务器的 10808 端口
PROXY_URL="http://192.168.0.187:10808"
export http_proxy="$PROXY_URL"
export https_proxy="$PROXY_URL"

# 官方 CentOS 8 Debuginfo 存档根路径
# CentOS 8 的包结构通常是：根目录/Packages/字母开头的目录/包名
# 或者直接在根目录下。我们使用 --glob 或直接定位。
OFFICIAL_BASE="http://debuginfo.centos.org/8/${ARCH}/Packages"

COMMON_RPM="kernel-debuginfo-common-${ARCH}-${KVER}.rpm"
CORE_RPM="kernel-debuginfo-${KVER}.rpm"
VMLINUX_PATH="/usr/lib/debug/lib/modules/${KVER}/vmlinux"

# 统一输出文件名
OUT_XZ="centos8_${KVER}.json.xz"

# ================= 2. SCP 目标配置 =================
REMOTE_HOST="192.168.0.188"
REMOTE_USER="root"
REMOTE_DIR="/root/json"
# REMOTE_PASS="你的188服务器密码"

echo "========== [1/5] 使用代理下载调试包 (CentOS 8 官方存档) =========="
echo "代理服务器: $PROXY_URL"

# 定义 wget 强制代理参数
WGET_OPTS="-c --no-check-certificate -e use_proxy=on -e http_proxy=$PROXY_URL -e https_proxy=$PROXY_URL"

# 尝试下载。注意：官方源有些包可能在子目录下（如 /k/kernel...），这里先尝试直接下载
wget $WGET_OPTS "${OFFICIAL_BASE}/${COMMON_RPM}" || \
wget $WGET_OPTS "${OFFICIAL_BASE}/k/${COMMON_RPM}"

wget $WGET_OPTS "${OFFICIAL_BASE}/${CORE_RPM}" || \
wget $WGET_OPTS "${OFFICIAL_BASE}/k/${CORE_RPM}"

echo "========== [2/5] 安装调试依赖包 =========="
# 使用 dnf 或 rpm 安装。dnf 会自动处理 localinstall 的依赖
if command -v dnf &> /dev/null; then
    sudo dnf localinstall -y "${COMMON_RPM}" "${CORE_RPM}"
else
    sudo rpm -ivh "${COMMON_RPM}" "${CORE_RPM}" --nodeps --force
fi

echo "========== [3/5] 准备 dwarf2json 工具 =========="
if [ ! -x "dwarf2json" ]; then
    echo "正在下载 dwarf2json (通过代理)..."
    wget $WGET_OPTS "https://github.com/volatilityfoundation/dwarf2json/releases/latest/download/dwarf2json-linux-amd64" -O dwarf2json
    chmod +x dwarf2json
fi

echo "========== [4/5] 提取并压缩符号表 =========="
if [ -f "${VMLINUX_PATH}" ]; then
    echo "正在转换 DWARF 为 JSON (边转换边极致压缩)..."
    ./dwarf2json linux --elf "${VMLINUX_PATH}" | xz -c -9 > "${OUT_XZ}"
    echo "✅ 符号表生成成功: ${OUT_XZ}"
else
    echo "❌ 错误：未找到 vmlinux 文件，请检查安装步骤。"
    exit 1
fi

echo "========== [5/5] 远程传输与清理 =========="
# 传输至内网 188 机器，必须取消代理设置，否则 scp 会尝试走 187 代理导致失败
unset http_proxy
unset https_proxy

if [ -n "${REMOTE_PASS}" ]; then
    if ! command -v sshpass &> /dev/null; then
        sudo dnf install -y epel-release && sudo dnf install -y sshpass || true
    fi
    sshpass -p "${REMOTE_PASS}" scp -o StrictHostKeyChecking=no "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
else
    scp "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
fi

# 打扫战场
rm -f "${COMMON_RPM}" "${CORE_RPM}"
echo "✨ 流程完成，临时文件已清理。"
