#!/bin/bash

# macOS Python SSL 证书修复脚本

echo "=========================================="
echo "macOS Python SSL 证书修复工具"
echo "=========================================="
echo ""

# 方法1: 查找并运行 Python 自带的证书安装脚本
echo "方法 1: 运行 Python 自带的证书安装脚本"
echo "----------------------------------------"

CERT_SCRIPT=$(find /Applications -name "Install Certificates.command" 2>/dev/null | head -n 1)

if [ -n "$CERT_SCRIPT" ]; then
    echo "找到证书安装脚本: $CERT_SCRIPT"
    echo "正在运行..."
    bash "$CERT_SCRIPT"
    echo "✓ 证书安装完成"
else
    echo "✗ 未找到 Python 证书安装脚本"
    echo ""
    echo "方法 2: 使用 certifi 包"
    echo "----------------------------------------"

    # 方法2: 使用 certifi
    python3 -m pip install --upgrade certifi --trusted-host pypi.org --trusted-host files.pythonhosted.org

    if [ $? -eq 0 ]; then
        echo "✓ certifi 安装成功"

        # 创建符号链接
        CERT_PATH=$(python3 -m certifi)
        SSL_CERT_FILE="$CERT_PATH"
        export SSL_CERT_FILE

        echo "✓ SSL 证书路径已设置: $SSL_CERT_FILE"
        echo ""
        echo "请将以下行添加到您的 ~/.bash_profile 或 ~/.zshrc:"
        echo "export SSL_CERT_FILE=$(python3 -m certifi)"
    else
        echo "✗ certifi 安装失败"
    fi
fi

echo ""
echo "方法 3: 绕过 SSL 验证（临时方案）"
echo "----------------------------------------"
echo "如果上述方法都失败，您可以使用 --trusted-host 选项："
echo "pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org"
echo ""
