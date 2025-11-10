#!/bin/bash
# =============================================================================
# Camoufox Crawler 项目 - Conda 环境安装脚本 (macOS)
# =============================================================================

set -e  # 遇到错误时退出

echo "🚀 开始安装 Camoufox Crawler 项目环境 (macOS)"
echo "=============================================="

# 检查是否安装了 conda
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到 conda 命令"
    echo "请先安装 Anaconda 或 Miniconda:"
    echo "  Anaconda: https://www.anaconda.com/products/distribution"
    echo "  Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ 检测到 conda 已安装"

# 检查 environment.yml 文件是否存在
if [ ! -f "environment.yml" ]; then
    echo "❌ 错误: 未找到 environment.yml 文件"
    echo "请确保在项目根目录下运行此脚本"
    exit 1
fi

echo "📋 正在读取环境配置文件..."

# 创建 conda 环境
echo "🔧 创建 conda 环境: camoufox-crawler"
conda env create -f environment.yml

# 激活环境
echo "🔄 激活环境..."
eval "$(conda shell.bash hook)"
conda activate camoufox-crawler

# 安装 Playwright 浏览器
echo "🌐 安装 Playwright 浏览器..."
playwright install

# 安装 Playwright 系统依赖 (macOS)
echo "📦 安装 Playwright 系统依赖..."
playwright install-deps

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p data/logs
mkdir -p data/cookies
mkdir -p data/screenshots

# 设置权限
chmod +x *.py 2>/dev/null || true

echo ""
echo "🎉 安装完成!"
echo "=============================================="
echo "📋 使用说明:"
echo "  1. 激活环境: conda activate camoufox-crawler"
echo "  2. 运行 AI Studio 服务: python main.py"
echo "  3. 运行豆包服务: python doubao_main.py"
echo "  4. 查看示例: ls examples/"
echo ""
echo "🌐 服务地址:"
echo "  • AI Studio API: http://localhost:8812"
echo "  • AI Studio 管理界面: http://localhost:8813"
echo "  • 豆包 API: http://localhost:8814"
echo "  • 豆包管理界面: http://localhost:8815"
echo ""
echo "📚 更多文档请查看 docs/ 目录"
echo "=============================================="
