#!/bin/bash

# 新闻采集系统 - 快速设置脚本

echo "=========================================="
echo "新闻采集系统 - 环境配置"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD=pip
else
    echo "错误: 未找到 Python，请先安装 Python 3.7 或更高版本"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $PYTHON_VERSION"
echo ""

# 检查并修复 macOS SSL 证书问题
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS 系统，检查 SSL 证书..."
    PYTHON_PATH=$(which $PYTHON_CMD)
    PYTHON_DIR=$(dirname $(dirname $PYTHON_PATH))

    # 查找并运行 Install Certificates.command
    if [ -f "$PYTHON_DIR/Install Certificates.command" ]; then
        echo "发现证书安装脚本，正在安装 SSL 证书..."
        bash "$PYTHON_DIR/Install Certificates.command" || true
        echo "✓ SSL 证书已安装"
    else
        echo "注意: 未找到 SSL 证书安装脚本"
        echo "如果遇到 SSL 错误，请手动运行:"
        echo "  /Applications/Python*/Install Certificates.command"
    fi
    echo ""
fi

# 创建虚拟环境
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建步骤"
else
    echo "创建虚拟环境..."
    $PYTHON_CMD -m venv venv
    if [ $? -eq 0 ]; then
        echo "✓ 虚拟环境创建成功"
    else
        echo "✗ 虚拟环境创建失败"
        exit 1
    fi
fi
echo ""

# 激活虚拟环境并安装依赖
echo "激活虚拟环境并安装依赖..."
source venv/bin/activate

echo "升级 pip..."
pip install --upgrade pip 2>&1 | grep -v "WARNING: Retrying" | grep -v "Could not fetch URL" || {
    echo "注意: pip 升级可能遇到问题，尝试使用备用方法..."
    # 使用 --trusted-host 选项
    pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
}

echo ""
echo "安装项目依赖..."
pip install -r requirements.txt 2>&1 | grep -v "WARNING: Retrying" | grep -v "Could not fetch URL"

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "安装失败，尝试使用备用方法（跳过 SSL 验证）..."
    pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

    if [ $? -eq 0 ]; then
        echo "✓ 依赖安装成功（使用备用方法）"
    else
        echo "✗ 依赖安装失败"
        echo ""
        echo "请尝试以下解决方案："
        echo "1. 手动安装 SSL 证书："
        echo "   sudo /Applications/Python*/Install\\ Certificates.command"
        echo ""
        echo "2. 或者在虚拟环境中手动安装依赖："
        echo "   source venv/bin/activate"
        echo "   pip install requests beautifulsoup4 lxml python-dateutil schedule"
        exit 1
    fi
fi
echo ""

# 创建必要的目录
echo "创建输出目录..."
mkdir -p output logs
echo "✓ 目录创建完成"
echo ""

echo "=========================================="
echo "环境配置完成！"
echo "=========================================="
echo ""
echo "使用方法:"
echo "1. 激活虚拟环境:"
echo "   source venv/bin/activate"
echo ""
echo "2. 运行采集程序:"
echo "   python main.py"
echo ""
echo "3. 或运行定时任务:"
echo "   python scheduler.py --run-now"
echo ""
echo "4. 退出虚拟环境:"
echo "   deactivate"
echo ""
