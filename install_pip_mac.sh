#!/bin/bash
# =============================================================================
# Camoufox Crawler 项目 - Pip 直接安装脚本 (macOS)
# =============================================================================

set -e  # 遇到错误时退出

echo "🚀 开始安装 Camoufox Crawler 项目环境 (macOS - pip)"
echo "=================================================="

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

echo "🐍 检测到 Python 版本: $python_version"

# 简单的版本比较
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "⚠️  警告: 推荐使用 Python 3.11 或更高版本"
    echo "当前版本: $python_version"
    read -p "是否继续安装? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 1
    fi
fi

# 检查 requirements.txt 文件是否存在
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 未找到 requirements.txt 文件"
    echo "请确保在项目根目录下运行此脚本"
    exit 1
fi

echo "📋 正在读取依赖配置文件..."

# 建议创建虚拟环境
echo "💡 建议创建虚拟环境以避免依赖冲突"
read -p "是否创建虚拟环境? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "🔧 创建虚拟环境: camoufox-crawler-env"
    python3 -m venv camoufox-crawler-env
    
    echo "🔄 激活虚拟环境..."
    source camoufox-crawler-env/bin/activate
    
    echo "⬆️  升级 pip..."
    pip install --upgrade pip
fi

# 安装依赖
echo "📦 安装 Python 依赖包..."
pip install -r requirements.txt

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
echo "=================================================="
echo "📋 使用说明:"
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "  1. 激活虚拟环境: source camoufox-crawler-env/bin/activate"
    echo "  2. 运行 AI Studio 服务: python main.py"
    echo "  3. 运行豆包服务: python doubao_main.py"
    echo "  4. 查看示例: ls examples/"
    echo "  5. 停用虚拟环境: deactivate"
else
    echo "  1. 运行 AI Studio 服务: python3 main.py"
    echo "  2. 运行豆包服务: python3 doubao_main.py"
    echo "  3. 查看示例: ls examples/"
fi
echo ""
echo "🌐 服务地址:"
echo "  • AI Studio API: http://localhost:8812"
echo "  • AI Studio 管理界面: http://localhost:8813"
echo "  • 豆包 API: http://localhost:8814"
echo "  • 豆包管理界面: http://localhost:8815"
echo ""
echo "📚 更多文档请查看 docs/ 目录"
echo "=================================================="
