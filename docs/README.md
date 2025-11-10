# Camoufox 爬虫框架

基于 Camoufox 和 Playwright 的 Python 爬虫框架，支持多实例、多进程、异步操作。

## 特性

- 🦊 **基于 Camoufox**: 使用 Camoufox 浏览器，更好的反检测能力
- 🎭 **Playwright 集成**: 强大的浏览器自动化功能
- 🚀 **多实例支持**: 支持同时运行多个爬虫实例
- ⚡ **异步/多进程**: 支持异步和多进程并发执行
- 🔧 **灵活配置**: 支持文件和环境变量配置
- 📸 **自动截图**: 错误时自动截图，便于调试
- 🍪 **Cookie 管理**: 自动保存和加载 cookies
- 📝 **详细日志**: 完整的日志记录和错误追踪

## 安装

### 推荐方式：使用Conda环境（推荐）

```bash
# 1. 运行设置脚本（自动创建环境）
./setup_conda_env.sh

# 2. 激活环境
conda activate camoufox-crawler
# 或使用: ./activate_env.sh

# 3. 验证安装
python setup_and_verify.py
```

### 手动安装方式

#### 1. 创建Conda环境
```bash
# 使用environment.yml创建环境
conda env create -f environment.yml

# 激活环境
conda activate camoufox-crawler
```

#### 2. 或者在现有环境中安装
```bash
# 安装 Camoufox
conda install camoufox

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install firefox
```

## 快速开始

### 1. 快速测试

```bash
# 确保已激活conda环境
conda activate camoufox-crawler

# 运行快速测试
python quick_test.py
```

这将启动一个简单的测试，访问 Google AI Studio 验证框架是否正常工作。

### 2. 基本使用

```python
import asyncio
from crawler_framework import CrawlerFramework, CrawlerConfig

async def main():
    # 创建框架实例
    framework = CrawlerFramework()
    
    # 创建配置
    config = CrawlerConfig()
    config.headless = False  # 有头模式
    config.timeout = 30000   # 30秒超时
    
    # 创建爬虫实例
    instance = framework.create_instance("my_crawler", config)
    
    try:
        # 启动实例
        await instance.start()
        
        # 访问网页
        await instance.goto("https://example.com")
        
        # 截图
        await instance.screenshot("example.png")
        
        # 等待元素
        await instance.wait_for_selector("h1")
        
        # 点击元素
        await instance.click("button")
        
        # 填充表单
        await instance.fill("input[name='username']", "myuser")
        
    finally:
        # 清理资源
        await framework.close_all()

# 运行
asyncio.run(main())
```

### 3. 多实例并发

```python
from multi_runner import MultiRunner, TaskBuilder
from crawler_framework import test_google_ai_studio

async def multi_test():
    # 创建任务构建器
    builder = TaskBuilder()
    
    # 添加多个任务
    for i in range(3):
        builder.add_task(
            task_id=f"test_{i}",
            function=test_google_ai_studio,
            config={"headless": True}
        )
    
    # 运行任务
    runner = MultiRunner(max_workers=3)
    results = await runner.run_async_tasks(builder.build())
    
    # 查看结果
    runner.print_results()

asyncio.run(multi_test())
```

## 配置

### 环境变量配置

创建 `.env` 文件：

```env
# 基本配置
CRAWLER_MAX_INSTANCES=5
CRAWLER_LOG_LEVEL=INFO
CRAWLER_HEADLESS=false

# 浏览器配置
CRAWLER_TIMEOUT=30000
CRAWLER_VIEWPORT_WIDTH=1920
CRAWLER_VIEWPORT_HEIGHT=1080
CRAWLER_MAX_RETRIES=3
CRAWLER_RETRY_DELAY=2

# 代理配置（可选）
CRAWLER_PROXY_SERVER=http://proxy.example.com:8080
CRAWLER_PROXY_USERNAME=username
CRAWLER_PROXY_PASSWORD=password

# 目录配置
CRAWLER_COOKIES_DIR=cookies
CRAWLER_SCREENSHOTS_DIR=screenshots
CRAWLER_DATA_DIR=data
```

### JSON 配置文件

创建 `config.json`：

```json
{
  "max_instances": 5,
  "log_level": "INFO",
  "browser": {
    "headless": false,
    "timeout": 30000,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "max_retries": 3,
    "retry_delay": 2,
    "screenshot_on_error": true
  }
}
```

## 项目结构

```
crawler_py/
├── crawler_framework.py    # 核心爬虫框架
├── config.py              # 配置管理
├── multi_runner.py        # 多进程/多线程运行器
├── quick_test.py          # 快速测试脚本
├── setup_conda_env.sh     # Conda环境设置脚本
├── setup_and_verify.py    # 环境验证脚本
├── requirements.txt       # Python 依赖
├── environment.yml        # Conda环境配置
├── config.json.example    # 配置文件示例
├── CONDA_USAGE.md         # Conda使用指南
├── activate_env.sh        # 环境激活脚本(Linux/Mac)
├── activate_env.bat       # 环境激活脚本(Windows)
├── examples/              # 示例代码
│   └── test_google_ai_studio.py
├── logs/                  # 日志目录
├── cookies/               # Cookie 存储
├── screenshots/           # 截图存储
└── data/                  # 数据存储
```

## API 文档

### CrawlerFramework

主要的爬虫框架类。

```python
framework = CrawlerFramework()

# 创建实例
instance = framework.create_instance("instance_id", config)

# 启动实例
await framework.start_instance("instance_id")

# 获取实例
instance = framework.get_instance("instance_id")

# 关闭实例
await framework.close_instance("instance_id")

# 关闭所有实例
await framework.close_all()
```

### CrawlerInstance

单个爬虫实例。

```python
# 启动实例
await instance.start()

# 访问网页
success = await instance.goto("https://example.com")

# 等待元素
found = await instance.wait_for_selector("selector")

# 点击元素
success = await instance.click("selector")

# 填充文本
success = await instance.fill("selector", "text")

# 截图
path = await instance.screenshot("filename.png")

# 保存 cookies
await instance.save_cookies("cookies.json")

# 加载 cookies
await instance.load_cookies("cookies.json")

# 关闭实例
await instance.close()
```

### MultiRunner

多进程/多线程运行器。

```python
runner = MultiRunner(max_workers=3)

# 异步运行任务
results = await runner.run_async_tasks(tasks)

# 多进程运行任务
results = runner.run_process_tasks(tasks)

# 多线程运行任务
results = runner.run_thread_tasks(tasks)

# 获取结果摘要
summary = runner.get_results_summary()

# 打印结果
runner.print_results()
```

## 示例

### Google AI Studio 测试

```bash
# 运行完整测试示例
python examples/test_google_ai_studio.py
```

该示例包含：
- 简单访问测试
- 登录检测和处理
- 多实例并发测试
- 不同配置测试

## 最佳实践

### 1. 错误处理

```python
try:
    await instance.goto("https://example.com")
except Exception as e:
    logger.error(f"访问失败: {e}")
    # 错误时会自动截图（如果启用）
```

### 2. 资源管理

```python
framework = CrawlerFramework()
try:
    # 使用框架
    pass
finally:
    # 确保清理资源
    await framework.close_all()
```

### 3. 配置管理

```python
from config import get_config, get_browser_config

# 获取全局配置
config = get_config()

# 获取浏览器配置
browser_config = get_browser_config()
```

### 4. 多实例使用

```python
# 为不同网站创建不同配置
config_a = CrawlerConfig()
config_a.timeout = 15000

config_b = CrawlerConfig()
config_b.headless = True
config_b.timeout = 30000

# 创建多个实例
instance_a = framework.create_instance("site_a", config_a)
instance_b = framework.create_instance("site_b", config_b)
```

## 故障排除

### 1. Camoufox 未安装

```bash
conda install camoufox
```

### 2. Playwright 浏览器未安装

```bash
playwright install firefox
```

### 3. 依赖问题

```bash
pip install -r requirements.txt --upgrade
```

### 4. 权限问题

确保有足够的权限创建目录和文件。

### 5. 网络问题

检查网络连接，考虑使用代理配置。

## 扩展开发

### 添加新的网站支持

1. 创建专门的任务函数：

```python
async def crawl_my_site(instance: CrawlerInstance, *args):
    # 实现具体的爬取逻辑
    await instance.goto("https://mysite.com")
    # ... 更多操作
    return result
```

2. 使用 TaskBuilder 创建任务：

```python
builder = TaskBuilder()
builder.add_task("my_site", crawl_my_site, args=[arg1, arg2])
```

### 自定义配置

继承 CrawlerConfig 类添加自定义配置：

```python
class MyConfig(CrawlerConfig):
    def __init__(self):
        super().__init__()
        self.custom_setting = "value"
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
