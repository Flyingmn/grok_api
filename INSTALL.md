# Camoufox Crawler 项目安装指南

本项目是一个基于 Camoufox 和 Playwright 的网页爬虫框架，支持 AI Studio 和豆包的图片生成自动化。

## 📋 系统要求

- **Python**: 3.11 或更高版本
- **操作系统**: macOS 或 Windows
- **内存**: 建议 4GB 以上
- **磁盘空间**: 建议 2GB 以上（包含浏览器文件）

## 🚀 快速安装

### 方式一：使用 Conda（推荐）

#### macOS
```bash
# 克隆项目
git clone <your-repo-url>
cd crawler_py

# 运行安装脚本
./install_conda_mac.sh
```

#### Windows
```cmd
# 克隆项目
git clone <your-repo-url>
cd crawler_py

# 运行安装脚本
install_conda_windows.bat
```

### 方式二：使用 Pip 直接安装

#### macOS
```bash
# 克隆项目
git clone <your-repo-url>
cd crawler_py

# 运行安装脚本
./install_pip_mac.sh
```

#### Windows
```cmd
# 克隆项目
git clone <your-repo-url>
cd crawler_py

# 运行安装脚本
install_pip_windows.bat
```

## 📦 依赖包说明

### 核心依赖
- **camoufox**: 反检测浏览器引擎
- **playwright**: 浏览器自动化框架
- **loguru**: 日志记录
- **pydantic**: 数据验证
- **python-dotenv**: 环境变量管理

### Web 服务依赖
- **fastapi**: Web API 框架
- **uvicorn**: ASGI 服务器
- **aiohttp**: 异步 HTTP 客户端
- **requests**: HTTP 请求库

### 工具依赖
- **aiofiles**: 异步文件操作

## 🔧 手动安装（高级用户）

如果自动安装脚本遇到问题，可以手动安装：

### 1. 创建虚拟环境
```bash
# 使用 conda
conda create -n camoufox-crawler python=3.11
conda activate camoufox-crawler

# 或使用 venv
python -m venv camoufox-crawler-env
source camoufox-crawler-env/bin/activate  # macOS/Linux
# camoufox-crawler-env\Scripts\activate.bat  # Windows
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 安装浏览器
```bash
playwright install
playwright install-deps  # macOS/Linux only
```

### 4. 创建目录
```bash
mkdir -p data/logs data/cookies data/screenshots
```

## 🎯 验证安装

安装完成后，可以运行以下命令验证：

```bash
# 激活环境（如果使用虚拟环境）
conda activate camoufox-crawler
# 或
source camoufox-crawler-env/bin/activate

# 运行测试
python -c "import camoufox, playwright; print('✅ 安装成功!')"
```

## 🚦 启动服务

### AI Studio 服务
```bash
python main.py
```
- API 服务: http://localhost:8812
- 管理界面: http://localhost:8813

### 豆包服务
```bash
python doubao_main.py
```
- API 服务: http://localhost:8814
- 管理界面: http://localhost:8815

## 📚 示例代码

查看 `examples/` 目录下的示例文件：
- `start_interactive_test.py`: AI Studio 交互测试
- `start_doubao_image_test.py`: 豆包图片生成测试
- `test_api_with_aspect_ratio.py`: API 调用示例

## 🐛 常见问题

### 1. Playwright 浏览器下载失败
```bash
# 手动安装浏览器
playwright install chromium
```

### 2. 权限问题 (macOS)
```bash
# 给脚本执行权限
chmod +x install_conda_mac.sh install_pip_mac.sh
```

### 3. Python 版本问题
确保使用 Python 3.11 或更高版本：
```bash
python --version
```

### 4. 网络问题
如果下载速度慢，可以设置镜像源：
```bash
# pip 镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# conda 镜像
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
```

## 📖 更多文档

- [API 使用指南](docs/API_USAGE_GUIDE.md)
- [多实例服务指南](docs/MULTI_INSTANCE_GUIDE.md)
- [交互测试指南](docs/INTERACTIVE_TEST_GUIDE.md)
- [豆包图片生成指南](docs/DOUBAO_IMAGE_GUIDE.md)

## 💡 技术支持

如果遇到问题，请：
1. 检查 `data/logs/` 目录下的日志文件
2. 确认所有依赖都已正确安装
3. 查看项目文档获取更多帮助

---

**注意**: 首次运行时，Playwright 会下载浏览器文件，可能需要几分钟时间，请耐心等待。
