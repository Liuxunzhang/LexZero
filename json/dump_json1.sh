#!/bin/bash
# 开启严格模式：遇到任何错误立刻终止运行
set -e

# ================= 1. 定义核心变量 =================
ARCH=$(uname -m)
KVER=$(uname -r)
COMMON_RPM="kernel-debuginfo-common-${ARCH}-${KVER}.rpm"
CORE_RPM="kernel-debuginfo-${KVER}.rpm"
VMLINUX_PATH="/usr/lib/debug/lib/modules/${KVER}/vmlinux"
OUT_XZ="centos8_${KVER}.json.xz"

# ================= 2. SCP 目标配置 =================
REMOTE_HOST="192.168.0.188"
REMOTE_USER="root"
REMOTE_DIR="/root/json"
# REMOTE_PASS="你的188服务器密码"

echo "========== [1/5] 智能匹配 CentOS 8 历史存档 (Vault) =========="
# 提取 el8 后面的子版本号来精确匹配 Vault 目录
if [[ "$KVER" == *"el8_0"* ]]; then VAULT_VER="8.0.1905"
elif [[ "$KVER" == *"el8_1"* ]]; then VAULT_VER="8.1.1911"
elif [[ "$KVER" == *"el8_2"* ]]; then VAULT_VER="8.2.2004"
elif [[ "$KVER" == *"el8_3"* ]]; then VAULT_VER="8.3.2011"
elif [[ "$KVER" == *"el8_4"* ]]; then VAULT_VER="8.4.2105"
elif [[ "$KVER" == *"el8_5"* ]]; then VAULT_VER="8.5.2111"
else VAULT_VER="8.5.2111" # 兜底版本
fi
echo "🎯 检测到内核为 ${KVER}，对应存档版本为: ${VAULT_VER}"

# 定义一个强健的下载函数，自动遍历多个源
download_rpm() {
    local rpm_name=$1
    local urls=(
        "https://mirrors.aliyun.com/centos-vault/${VAULT_VER}/BaseOS/${ARCH}/debug/tree/Packages/${rpm_name}"
        "http://debuginfo.centos.org/8/${ARCH}/Packages/${rpm_name}"
        "https://vault.centos.org/${VAULT_VER}/BaseOS/${ARCH}/debug/tree/Packages/${rpm_name}"
    )
    
    for url in "${urls[@]}"; do
        echo "⏳ 尝试下载: $url"
        if wget -c "$url"; then
            echo "✅ 下载成功: $rpm_name"
            return 0
        else
            echo "⚠️ 此源未找到，尝试下一个..."
        fi
    done
    
    echo "❌ 致命错误: 所有镜像源均已下线 ${rpm_name}，包太古老了！"
    exit 1
}

echo "========== [2/5] 开始下载调试依赖包 =========="
download_rpm "${COMMON_RPM}"
download_rpm "${CORE_RPM}"

echo "========== [3/5] 安装调试依赖包 =========="
rpm -q "kernel-debuginfo-common-${ARCH}-${KVER}" &>/dev/null || sudo rpm -ivh "${COMMON_RPM}"
rpm -q "kernel-debuginfo-${KVER}" &>/dev/null || sudo rpm -ivh "${CORE_RPM}"

echo "========== [4/5] 准备工具并提取符号表 =========="
if [ ! -x "dwarf2json" ]; then
    wget -c "https://gh-proxy.com/https://github.com/volatilityfoundation/dwarf2json/releases/latest/download/dwarf2json-linux-amd64" -O dwarf2json
    chmod +x dwarf2json
fi

if [ -f "${VMLINUX_PATH}" ]; then
    echo "⏳ 正在提取并压缩符号表..."
    ./dwarf2json linux --elf "${VMLINUX_PATH}" | xz -c -9 > "${OUT_XZ}"
    echo "✅ 符号表已生成并极致压缩为：${OUT_XZ}"
else
    echo "❌ 致命错误：找不到内核调试文件 ${VMLINUX_PATH}"
    exit 1
fi

echo "========== [5/5] 远程传输与清理 =========="
if [ -n "${REMOTE_PASS}" ]; then
    echo "🔑 启用全自动免密传输..."
    if ! command -v sshpass &> /dev/null; then
        sudo dnf install -y epel-release sshpass
    fi
    sshpass -p "${REMOTE_PASS}" scp -o StrictHostKeyChecking=no "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
else
    echo "🔒 将使用标准手动验证传输..."
    scp "${OUT_XZ}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
fi

rm -f "${COMMON_RPM}" "${CORE_RPM}"
echo "🧹 临时安装包已清理完毕，服务器保持整洁。"
