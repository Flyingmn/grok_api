@echo off
REM =============================================================================
REM Camoufox Crawler 项目 - Pip 直接安装脚本 (Windows)
REM =============================================================================

echo 🚀 开始安装 Camoufox Crawler 项目环境 (Windows - pip)
echo ==================================================

REM 检查 Python 是否安装
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python
    echo 请先安装 Python 3.11 或更高版本:
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 显示 Python 版本
echo 🐍 检测到 Python 版本:
python --version

REM 检查 requirements.txt 文件是否存在
if not exist "requirements.txt" (
    echo ❌ 错误: 未找到 requirements.txt 文件
    echo 请确保在项目根目录下运行此脚本
    pause
    exit /b 1
)

echo 📋 正在读取依赖配置文件...

REM 询问是否创建虚拟环境
echo 💡 建议创建虚拟环境以避免依赖冲突
set /p create_venv="是否创建虚拟环境? (Y/n): "
if /i "%create_venv%" neq "n" (
    echo 🔧 创建虚拟环境: camoufox-crawler-env
    python -m venv camoufox-crawler-env
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    
    echo 🔄 激活虚拟环境...
    call camoufox-crawler-env\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo ❌ 激活虚拟环境失败
        pause
        exit /b 1
    )
    
    echo ⬆️  升级 pip...
    python -m pip install --upgrade pip
)

REM 安装依赖
echo 📦 安装 Python 依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 安装依赖失败
    pause
    exit /b 1
)

REM 安装 Playwright 浏览器
echo 🌐 安装 Playwright 浏览器...
call playwright install
if %errorlevel% neq 0 (
    echo ⚠️  Playwright 浏览器安装可能有问题，但继续执行...
)

REM 创建必要的目录
echo 📁 创建项目目录...
if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\cookies" mkdir data\cookies
if not exist "data\screenshots" mkdir data\screenshots

echo.
echo 🎉 安装完成!
echo ==================================================
echo 📋 使用说明:
if /i "%create_venv%" neq "n" (
    echo   1. 激活虚拟环境: camoufox-crawler-env\Scripts\activate.bat
    echo   2. 运行 AI Studio 服务: python main.py
    echo   3. 运行豆包服务: python doubao_main.py
    echo   4. 查看示例: dir examples\
    echo   5. 停用虚拟环境: deactivate
) else (
    echo   1. 运行 AI Studio 服务: python main.py
    echo   2. 运行豆包服务: python doubao_main.py
    echo   3. 查看示例: dir examples\
)
echo.
echo 🌐 服务地址:
echo   • AI Studio API: http://localhost:8812
echo   • AI Studio 管理界面: http://localhost:8813
echo   • 豆包 API: http://localhost:8814
echo   • 豆包管理界面: http://localhost:8815
echo.
echo 📚 更多文档请查看 docs\ 目录
echo ==================================================
pause
