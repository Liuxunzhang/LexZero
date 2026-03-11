#!/bin/bash
# 开启严格模式：遇到任何错误立刻终止运行
set -e

# ================= 1. 定义核心变量 =================
ARCH=$(uname -m)
KVER=$(uname -r)

# 智能识别 CentOS 8 还是 CentOS Stream 8，适配对应的阿里云源分支
if grep -q "Stream" /etc/os-release 2>/dev/null; then
    OS_VER="8-stream"
else
    OS_VER="8"
fi

# 注意：CentOS 8 的镜像源路径中，多了一层 /Packages/ 目录
ALIYUN_BASE="https://mirrors.aliyun.com/centos-debuginfo/${OS_VER}/${ARCH}/Packages"
COMMON_RPM="kernel-debuginfo-common-${ARCH}-${KVER}.rpm"
CORE_RPM="kernel-debuginfo-${KVER}.rpm"
VMLINUX_PATH="/usr/lib/debug/lib/modules/${KVER}/vmlinux"

# 统一输出文件名
OUT_XZ="centos8_${KVER}.json.xz"

# ================= 2. SCP 目标配置 =================
REMOTE_HOST="192.168.0.188"
REMOTE_USER="root"
REMOTE_DIR="/root/json"

# 【免密自动化开关】: 将下面这行的注释取消，并填入你真实的 188 密码即可实现全自动。
# REMOTE_PASS="你的188服务器密码"


echo "========== [1/5] 下载调试依赖包 (CentOS ${OS_VER}) =========="
# 添加 -c 参数，支持断点续传
wget -c "${ALIYUN_BASE}/${COMMON_RPM}"
wget -c "${ALIYUN_BASE}/${CORE_RPM}"

echo "========== [2/5] 安装调试依赖包 =========="
# 检查是否已经安装过，如果没有安装再执行 rpm，避免重复安装报错
rpm -q "kernel-debuginfo-common-${ARCH}-${KVER}" &>/dev/null || sudo rpm -ivh "${COMMON_RPM}"
rpm -q "kernel-debuginfo-${KVER}" &>/dev/null || sudo rpm -ivh "${CORE_RPM}"

echo "========== [3/5] 准备 dwarf2json 工具 =========="
# 判断当前目录如果没有可执行的 dwarf2json 才去下载
if [ ! -x "dwarf2json" ]; then
    wget -c "https://gh-proxy.com/https://github.com/volatilityfoundation/dwarf2json/releases/latest/download/dwarf2json-linux-amd64" -O dwarf2json
    chmod +x dwarf2json
fi

echo "========== [4/5] 提取并压缩符号表 =========="
if [ -f "${VMLINUX_PATH}" ]; then
    # 核心性能优化：管道符 "|" 边生成边压缩，不落地 JSON，极速且省空间
    ./dwarf2json linux --elf "${VMLINUX_PATH}" | xz -c -9 > "${OUT_XZ}"
    echo "✅ 符号表已生成并极致压缩为：${OUT_XZ}"
else
    echo "❌ 致命错误：找不到内核调试文件 ${VMLINUX_PATH}"
    exit 1
fi

echo "========== [5/5] 远程传输与清理 =========="
# 智能免密传输逻辑
if [ -n "${REMOTE_PASS}" ]; then
    echo "🔑 检测到配置了密码，启用全自动免密传输..."
    # CentOS 8 使用 dnf 安装 sshpass
    if ! command -v sshpass &> /dev/null; then
        echo "正在安装 sshpass 依赖..."
        sudo dnf install -y epel-release
        sudo dnf install -y sshpass
    fi
    # 携带密码并跳过指纹确认进行传输
    sshpass -p "${REMOTE_PASS}" scp -o StrictHostKeyChecking=no "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
else
    echo "🔒 未配置自动密码，将使用标准手动验证传输..."
    scp "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
fi

echo "✅ 压缩包已成功发送至 ${REMOTE_HOST}:${REMOTE_DIR}/"

# 打扫战场，删除临时下载的几百兆 RPM 包
rm -f "${COMMON_RPM}" "${CORE_RPM}"
echo "🧹 临时安装包已清理完毕，服务器保持整洁。"
