#!/bin/bash
# 开启严格模式
set -e

# ================= 1. 定义核心变量 =================
ARCH=$(uname -m)
KVER=$(uname -r)

# CentOS 6 必须使用 Vault (存档) 源，官方镜像站已关闭
# 注意：CentOS 6 的 debuginfo 路径通常在 /6.x/ 中，这里我们直接锁定 6.10
ALIYUN_BASE="https://mirrors.aliyun.com/centos-vault/6.10/debuginfo/${ARCH}"
COMMON_RPM="kernel-debuginfo-common-${ARCH}-${KVER}.rpm"
CORE_RPM="kernel-debuginfo-${KVER}.rpm"

# CentOS 6 的 vmlinux 默认安装路径
VMLINUX_PATH="/usr/lib/debug/lib/modules/${KVER}/vmlinux"

# 统一输出文件名
OUT_XZ="centos6_${KVER}.json.xz"

# ================= 2. SCP 目标配置 =================
REMOTE_HOST="192.168.0.188"
REMOTE_USER="root"
REMOTE_DIR="/root/json"
# REMOTE_PASS="你的188服务器密码"

echo "========== [1/5] 下载调试依赖包 (CentOS 6 Vault) =========="
# CentOS 6 wget 版本较低，可能需要 --no-check-certificate
WGET_OPTS="--no-check-certificate -c"
wget $WGET_OPTS "${ALIYUN_BASE}/${COMMON_RPM}" || { echo "无法下载 Common RPM"; exit 1; }
wget $WGET_OPTS "${ALIYUN_BASE}/${CORE_RPM}" || { echo "无法下载 Core RPM"; exit 1; }

echo "========== [2/5] 安装调试依赖包 =========="
# CentOS 6 使用 rpm 直接安装，忽略依赖检查(有时debug包会报依赖循环)
rpm -q "kernel-debuginfo-common" &>/dev/null || rpm -ivh "${COMMON_RPM}"
rpm -q "kernel-debuginfo" &>/dev/null || rpm -ivh "${CORE_RPM}"

echo "========== [3/5] 准备 dwarf2json 工具 =========="
if [ ! -x "dwarf2json" ]; then
    echo "正在下载 dwarf2json..."
    # 使用 GitHub Proxy 提高下载速度
    wget $WGET_OPTS "https://gh-proxy.com/https://github.com/volatilityfoundation/dwarf2json/releases/latest/download/dwarf2json-linux-amd64" -O dwarf2json
    chmod +x dwarf2json
fi

echo "========== [4/5] 提取并压缩符号表 =========="
if [ -f "${VMLINUX_PATH}" ]; then
    echo "正在提取 DWARF 信息，请稍候..."
    # CentOS 6 默认可能没装 xz，如果没有则改为 gzip
    if command -v xz &>/dev/null; then
        ./dwarf2json linux --elf "${VMLINUX_PATH}" | xz -c -9 > "${OUT_XZ}"
    else
        echo "⚠️ 找不到 xz，改用 gzip 压缩"
        ./dwarf2json linux --elf "${VMLINUX_PATH}" | gzip -c > "${OUT_XZ/xz/gz}"
        OUT_XZ="${OUT_XZ/xz/gz}"
    fi
    echo "✅ 符号表已生成：${OUT_XZ}"
else
    echo "❌ 致命错误：找不到内核调试文件 ${VMLINUX_PATH}"
    exit 1
fi

echo "========== [5/5] 远程传输与清理 =========="
if [ -n "${REMOTE_PASS}" ]; then
    if ! command -v sshpass &> /dev/null; then
        echo "正在尝试安装 sshpass..."
        yum install -y epel-release && yum install -y sshpass || echo "无法安装 sshpass，请手动输入密码"
    fi
    if command -v sshpass &> /dev/null; then
        sshpass -p "${REMOTE_PASS}" scp -o StrictHostKeyChecking=no "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    else
        scp "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    fi
else
    scp "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
fi

# 清理
rm -f "${COMMON_RPM}" "${CORE_RPM}"
echo "🧹 清理完成。"
