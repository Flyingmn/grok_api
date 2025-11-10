# Google AI Studio 交互测试程序使用指南

## 功能概述

这个程序可以让你在终端中输入文本，自动填充到Google AI Studio的输入框并发送，同时监听API响应并显示AI的回复。

## 主要特性

- 🚀 自动打开并导航到Google AI Studio
- 💬 终端交互式输入
- 🤖 自动填充文本到AI Studio输入框
- 📡 监听GenerateContent API调用
- 🔄 实时显示AI响应
- 📸 支持截图功能
- 🍪 自动加载和保存Cookies

## 使用方法

### 1. 快速启动

```bash
python start_interactive_test.py
```

### 2. 直接运行主程序

```bash
python interactive_ai_studio_test.py
```

## 程序流程

1. **初始化阶段**
   - 启动Camoufox浏览器
   - 设置网络监听器
   - 自动加载已保存的Cookies（保持登录状态）

2. **导航阶段**
   - 自动访问 https://aistudio.google.com/
   - 智能检测页面状态（登录页面/对话页面）
   - 提供用户指导和等待确认

3. **用户交互阶段**
   - 如果需要登录：等待用户手动登录
   - 如果需要导航：等待用户导航到对话页面
   - 用户确认后继续

4. **元素检测阶段**
   - 智能查找输入框和发送按钮
   - 支持多种选择器和重试机制
   - 验证元素可见性和可用性

5. **对话阶段**
   - 等待用户在终端输入
   - 自动填充到AI Studio输入框
   - 点击发送按钮
   - 监听API响应并显示结果
   - 自动保存登录状态

## 支持的命令

在交互模式下，你可以使用以下命令：

- **普通文本**: 直接输入要发送给AI的文本
- **`screenshot`**: 截图当前页面
- **`save`**: 手动保存登录状态
- **`quit` 或 `exit`**: 退出程序并自动保存登录状态

## 技术实现

### DOM元素选择器

程序会尝试以下选择器来查找输入框：
```python
textarea_selectors = [
    'textarea[placeholder="Start typing a prompt"]',
    'textarea.textarea',
    'textarea',
    'input[type="text"]',
    '[contenteditable="true"]'
]
```

发送按钮选择器：
```python
button_selectors = [
    'button[aria-label="Run"]',
    'button.run-button',
    'button:has-text("Run")',
    'button:has-text("Send")',
    'button[type="submit"]'
]
```

### API监听

程序监听以下API端点：
```
https://alkalimakersuite-pa.clients6.google.com/$rpc/google.internal.alkali.applications.makersuite.v1.MakerSuiteService/GenerateContent
```

### 响应解析

根据实际的API响应结构，程序会递归解析JSON数据，提取AI的回复文本。

## 配置选项

### CrawlerConfig 设置

```python
config = CrawlerConfig()
config.headless = False          # 显示浏览器窗口
config.timeout = 30000          # 30秒超时
config.cookies_file = "google_ai_studio_cookies.json"  # Cookies文件
```

### 自定义选择器

如果页面结构发生变化，你可以修改 `AIStudioInteractiveTest` 类中的 `selectors` 字典：

```python
self.selectors = {
    "textarea": 'textarea[placeholder="Start typing a prompt"]',
    "run_button": 'button[aria-label="Run"]',
    # 添加更多选择器...
}
```

## 故障排除

### 常见问题

1. **找不到输入框或按钮**
   - 检查页面是否完全加载
   - 确认是否需要登录Google账户
   - 查看截图确认页面状态

2. **API响应监听失败**
   - 确认网络连接正常
   - 检查是否被防火墙阻止
   - 验证API端点是否发生变化

3. **浏览器启动失败**
   - 确认Camoufox和Playwright已正确安装
   - 检查系统权限设置
   - 查看日志文件获取详细错误信息

### 调试模式

程序会自动生成以下文件帮助调试：

- **截图文件**: `screenshots/` 目录下
- **日志文件**: `logs/` 目录下
- **Cookies文件**: `cookies/` 目录下

### 日志级别

你可以修改日志级别来获取更多调试信息：

```python
logger.add(
    sys.stderr,
    level="DEBUG",  # 改为DEBUG获取更多信息
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
)
```

## 示例会话

```
🚀 启动Google AI Studio交互测试
==================================================
📋 功能说明:
  • 自动打开Google AI Studio
  • 智能检测登录状态和页面类型
  • 在终端输入文本，自动填充到AI Studio
  • 监听API响应，显示AI回复
  • 自动保存登录状态
==================================================

🔐 检测到登录页面
📋 请按以下步骤操作：
  1. 在浏览器中登录您的Google账户
  2. 登录成功后，导航到AI Studio对话页面
  3. 确保页面显示输入框和发送按钮
  4. 回到终端，按Enter键继续...

⏳ 请完成上述步骤后按Enter键继续...

✅ 初始化完成！现在可以开始对话了
💡 可用命令:
  • 'quit' 或 'exit' - 退出程序并保存登录状态
  • 'screenshot' - 截图当前页面
  • 'save' - 手动保存登录状态
  • 直接输入文本 - 发送给AI
==================================================

👤 请输入消息: 你好，请介绍一下自己

⏳ 等待AI响应...
🤖 AI回复: 你好！我是Gemini，一个由Google开发的大型语言模型。我可以帮助你回答问题、进行对话、协助写作、解释概念等等。有什么我可以帮助你的吗？

👤 请输入消息: save
💾 登录状态已保存

👤 请输入消息: screenshot
📸 截图已保存: screenshots/screenshot_ai_studio_interactive_1698765432.png

👤 请输入消息: quit
💾 正在保存登录状态...
👋 再见！
```

## 扩展功能

你可以基于这个框架扩展以下功能：

1. **批量测试**: 从文件读取多个测试用例
2. **结果保存**: 将对话历史保存到文件
3. **性能监控**: 记录响应时间和成功率
4. **多模态支持**: 支持图片上传测试
5. **自动化测试**: 集成到CI/CD流程中

## 注意事项

- 确保你有有效的Google账户并已登录AI Studio
- 程序需要网络连接来访问AI Studio
- 首次运行可能需要手动登录Google账户
- 请遵守Google AI Studio的使用条款和限制
