@echo off
REM =============================================================================
REM Camoufox Crawler 项目 - Conda 环境安装脚本 (Windows)
REM =============================================================================

echo 🚀 开始安装 Camoufox Crawler 项目环境 (Windows)
echo ==============================================

REM 检查是否安装了 conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 conda 命令
    echo 请先安装 Anaconda 或 Miniconda:
    echo   Anaconda: https://www.anaconda.com/products/distribution
    echo   Miniconda: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo ✅ 检测到 conda 已安装

REM 检查 environment.yml 文件是否存在
if not exist "environment.yml" (
    echo ❌ 错误: 未找到 environment.yml 文件
    echo 请确保在项目根目录下运行此脚本
    pause
    exit /b 1
)

echo 📋 正在读取环境配置文件...

REM 创建 conda 环境
echo 🔧 创建 conda 环境: camoufox-crawler
call conda env create -f environment.yml
if %errorlevel% neq 0 (
    echo ❌ 创建环境失败
    pause
    exit /b 1
)

REM 激活环境
echo 🔄 激活环境...
call conda activate camoufox-crawler
if %errorlevel% neq 0 (
    echo ❌ 激活环境失败
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
echo ==============================================
echo 📋 使用说明:
echo   1. 激活环境: conda activate camoufox-crawler
echo   2. 运行 AI Studio 服务: python main.py
echo   3. 运行豆包服务: python doubao_main.py
echo   4. 查看示例: dir examples\
echo.
echo 🌐 服务地址:
echo   • AI Studio API: http://localhost:8812
echo   • AI Studio 管理界面: http://localhost:8813
echo   • 豆包 API: http://localhost:8814
echo   • 豆包管理界面: http://localhost:8815
echo.
echo 📚 更多文档请查看 docs\ 目录
echo ==============================================
pause
