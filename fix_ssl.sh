#!/bin/bash

# macOS Python SSL 证书修复脚本

echo "=========================================="
echo "macOS Python SSL 证书修复工具"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/venv"

# 激活虚拟环境
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

# 方法1: 使用 certifi（推荐）
echo "方法 1: 使用 certifi 包配置 SSL"
echo "----------------------------------------"

CERT_PATH=$(python3 -c "import certifi; print(certifi.where())" 2>/dev/null)

if [ -n "$CERT_PATH" ] && [ -f "$CERT_PATH" ]; then
    echo "✓ 找到 certifi 证书: $CERT_PATH"
    echo ""
    echo "请将以下行添加到您的 ~/.zshrc 或 ~/.bash_profile:"
    echo ""
    echo "export SSL_CERT_FILE=$CERT_PATH"
    echo "export REQUESTS_CA_BUNDLE=$CERT_PATH"
    echo ""
    echo "然后运行: source ~/.zshrc"
    echo ""

    # 当前 shell 临时生效
    export SSL_CERT_FILE="$CERT_PATH"
    export REQUESTS_CA_BUNDLE="$CERT_PATH"
    echo "✓ 当前 shell 已临时配置 SSL 证书"
else
    echo "✗ certifi 未安装或证书不存在"
    echo ""
    echo "方法 2: 运行 Python 自带的证书安装脚本"
    echo "----------------------------------------"

    CERT_SCRIPT=$(find /Applications -name "Install Certificates.command" 2>/dev/null | head -n 1)

    if [ -n "$CERT_SCRIPT" ]; then
        echo "找到证书安装脚本: $CERT_SCRIPT"
        echo "正在运行..."
        bash "$CERT_SCRIPT"
        echo "✓ 证书安装完成"
    else
        echo "✗ 未找到 Python 证书安装脚本"
    fi
fi

echo ""
echo "方法 3: 绕过 SSL 验证（临时方案）"
echo "----------------------------------------"
echo "如果上述方法都失败，您可以使用 --trusted-host 选项："
echo "pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org"
echo ""
