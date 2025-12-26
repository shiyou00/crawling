@echo off
REM 新闻采集系统 - Windows 快速设置脚本

echo ==========================================
echo 新闻采集系统 - 环境配置
echo ==========================================
echo.

REM 检查 Python 版本
echo 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.7 或更高版本
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo 当前 Python 版本: %PYTHON_VERSION%
echo.

REM 创建虚拟环境
if exist venv\ (
    echo 虚拟环境已存在，跳过创建步骤
) else (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo × 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo √ 虚拟环境创建成功
)
echo.

REM 激活虚拟环境并安装依赖
echo 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat

echo 升级 pip...
python -m pip install --upgrade pip >nul 2>&1

echo 安装项目依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo × 依赖安装失败
    pause
    exit /b 1
)
echo √ 依赖安装成功
echo.

REM 创建必要的目录
echo 创建输出目录...
if not exist output mkdir output
if not exist logs mkdir logs
echo √ 目录创建完成
echo.

echo ==========================================
echo 环境配置完成！
echo ==========================================
echo.
echo 使用方法:
echo 1. 激活虚拟环境:
echo    venv\Scripts\activate
echo.
echo 2. 运行采集程序:
echo    python main.py
echo.
echo 3. 或运行定时任务:
echo    python scheduler.py --run-now
echo.
echo 4. 退出虚拟环境:
echo    deactivate
echo.

pause
