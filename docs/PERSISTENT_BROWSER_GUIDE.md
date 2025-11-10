# 持续浏览器服务使用指南

## 🎯 概述

持续浏览器服务允许你启动一个浏览器实例（如访问AI Studio），然后通过消息/任务的方式向这个持续运行的浏览器发送操作指令，而不是每次任务都重新启动浏览器。

## 🚀 快速开始

### 1. 启动持续浏览器服务

```bash
# 激活conda环境
conda activate camoufox-crawler

# 启动持续浏览器（会自动访问AI Studio）
python start_persistent_browser.py
```

浏览器将：
- 自动启动Camoufox浏览器
- 访问Google AI Studio
- 保持运行状态等待任务
- 每30秒输出状态信息

### 2. 发送任务到浏览器

在另一个终端中：

```bash
# 激活环境
conda activate camoufox-crawler

# 交互式发送任务
python send_task.py interactive
```

或者发送单个任务：

```bash
# 截图
python send_task.py screenshot my_screenshot.png

# 访问新页面
python send_task.py goto https://example.com

# 获取页面标题
python send_task.py title

# 获取当前URL
python send_task.py url

# 点击元素
python send_task.py click "button[data-testid='login']"

# 填充表单
python send_task.py fill "input[name='username']" "myusername"

# 执行JavaScript
python send_task.py script "document.title"
```

## 📋 可用任务类型

| 任务类型 | 命令格式 | 说明 |
|---------|---------|------|
| 访问页面 | `goto <url>` | 导航到指定URL |
| 点击元素 | `click <selector>` | 点击CSS选择器指定的元素 |
| 填充文本 | `fill <selector> <text>` | 在输入框中填充文本 |
| 截图 | `screenshot [filename]` | 保存页面截图 |
| 获取标题 | `title` | 获取当前页面标题 |
| 获取URL | `url` | 获取当前页面URL |
| 执行脚本 | `script <javascript>` | 执行JavaScript代码 |

## 🎮 交互模式示例

```bash
python send_task.py interactive
```

进入交互模式后：

```
🎯 请输入命令: title
📄 页面标题: {'title': 'Google AI Studio'}

🎯 请输入命令: screenshot ai_studio_current.png
📸 截图结果: {'path': 'screenshots/ai_studio_current.png'}

🎯 请输入命令: goto https://www.google.com
📍 访问结果: {'success': True, 'url': 'https://www.google.com/'}

🎯 请输入命令: quit
👋 客户端已断开
```

## 🔧 编程接口

你也可以在Python代码中使用持续浏览器：

```python
import asyncio
from persistent_browser import create_ai_studio_browser, TaskType
from task_sender import TaskSender

async def main():
    # 创建持续浏览器
    browser = await create_ai_studio_browser("my_browser")
    sender = TaskSender(browser)
    
    try:
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 获取页面信息
        title = await sender.get_title()
        print(f"标题: {title}")
        
        # 截图
        screenshot = await sender.screenshot("my_screenshot.png")
        print(f"截图: {screenshot}")
        
        # 访问其他页面
        result = await sender.goto("https://example.com")
        print(f"访问结果: {result}")
        
    finally:
        await browser.stop()

asyncio.run(main())
```

## 🏗️ 架构说明

### 核心组件

1. **PersistentBrowser**: 持续浏览器服务核心类
   - 管理浏览器实例生命周期
   - 处理任务队列
   - 执行具体任务

2. **TaskSender**: 任务发送器
   - 提供简化的任务发送接口
   - 封装常用操作

3. **BrowserService**: 浏览器服务管理器
   - 管理多个浏览器实例
   - 提供服务级别的操作

### 任务流程

```
用户发送任务 → 任务队列 → 任务处理器 → 浏览器操作 → 结果返回
```

## 🎯 使用场景

### 1. 持续监控
```python
# 启动浏览器访问AI Studio
browser = await create_ai_studio_browser()

# 定期截图监控页面变化
while True:
    await sender.screenshot(f"monitor_{int(time.time())}.png")
    await asyncio.sleep(60)  # 每分钟截图一次
```

### 2. 交互式操作
```python
# 启动浏览器
browser = await create_ai_studio_browser()

# 根据用户输入执行操作
while True:
    action = input("请输入操作: ")
    if action == "login":
        await sender.click("#login-button")
    elif action == "screenshot":
        await sender.screenshot()
```

### 3. 自动化任务序列
```python
browser = await create_ai_studio_browser()

# 执行一系列自动化操作
tasks = [
    ("goto", "https://aistudio.google.com/"),
    ("screenshot", "step1.png"),
    ("click", ".welcome-button"),
    ("screenshot", "step2.png"),
]

for task_type, param in tasks:
    if task_type == "goto":
        await sender.goto(param)
    elif task_type == "screenshot":
        await sender.screenshot(param)
    elif task_type == "click":
        await sender.click(param)
```

## 🛠️ 高级配置

### 自定义浏览器配置

```python
from crawler_framework import CrawlerConfig
from persistent_browser import PersistentBrowser

# 自定义配置
config = CrawlerConfig()
config.headless = True  # 无头模式
config.timeout = 60000  # 60秒超时
config.viewport = {"width": 1366, "height": 768}

# 创建自定义浏览器
browser = PersistentBrowser("custom_browser", config)
await browser.start()

# 手动访问页面
await browser.add_task(TaskType.GOTO, {"url": "https://example.com"})
```

### 多浏览器管理

```python
from persistent_browser import BrowserService

service = BrowserService()

# 创建多个浏览器实例
browser1 = await service.create_browser("ai_studio", config1)
browser2 = await service.create_browser("google", config2)

# 分别操作
await browser1.add_task(TaskType.GOTO, {"url": "https://aistudio.google.com"})
await browser2.add_task(TaskType.GOTO, {"url": "https://google.com"})

# 查看所有浏览器状态
status = service.list_browsers()
print(status)
```

## 🚨 注意事项

1. **资源管理**: 持续浏览器会占用系统资源，使用完毕后记得停止
2. **任务超时**: 长时间运行的任务可能会超时，注意设置合适的超时时间
3. **错误处理**: 任务执行失败时会返回错误信息，注意检查结果
4. **并发限制**: 避免同时发送大量任务，可能会导致浏览器响应缓慢

## 🔍 故障排除

### 浏览器启动失败
```bash
# 检查环境
python setup_and_verify.py

# 重新安装Camoufox
pip install --upgrade camoufox
```

### 任务执行超时
- 增加任务超时时间
- 检查网络连接
- 确认页面元素存在

### 内存占用过高
- 定期重启浏览器服务
- 使用无头模式
- 清理不必要的页面缓存

## 📝 日志和调试

日志文件位置：
- 主服务日志: `logs/persistent_browser_<instance_id>.log`
- 爬虫框架日志: `logs/crawler_<date>.log`

启用调试模式：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 总结

持续浏览器服务提供了一种高效的方式来管理长时间运行的浏览器任务。通过任务队列机制，你可以：

- ✅ 避免重复启动浏览器的开销
- ✅ 保持页面状态和登录信息
- ✅ 灵活发送各种操作任务
- ✅ 支持交互式和编程式操作
- ✅ 适用于监控、自动化、测试等场景

这正是你需要的：**一个浏览器持续运行，通过消息发送任务**！
