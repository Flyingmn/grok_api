# 豆包生图交互测试程序使用指南

## 功能概述

这个程序可以让你在终端中输入文本，自动填充到豆包生图页面并发送，同时监听API响应并显示AI的回复。

## 主要特性

- 🚀 自动打开并导航到豆包聊天页面
- 🎨 智能选择图像生成技能
- 💬 终端交互式输入
- 📸 支持参考图片上传
- 📐 支持图片比例设置
- 🤖 自动填充文本到豆包输入框
- 📡 监听豆包API调用
- 🔄 实时显示AI响应
- 🍪 自动加载和保存Cookies

## 使用方法

### 1. 快速启动

```bash
python examples/start_doubao_image_test.py
```

### 2. 直接运行主程序

```bash
python src/core/interactive_doubao_image.py
```

## 程序流程

1. **初始化阶段**
   - 启动浏览器
   - 设置网络监听器
   - 自动加载已保存的Cookies（保持登录状态）

2. **导航阶段**
   - 自动访问 https://www.doubao.com/chat/
   - 智能检测页面状态
   - 自动选择图像生成技能

3. **交互阶段**
   - 等待用户在终端输入
   - 自动填充到豆包输入框
   - 点击发送按钮
   - 监听API响应并显示结果
   - 自动保存登录状态

## 支持的命令

在交互模式下，你可以使用以下命令：

- **普通文本**: 直接输入要发送给豆包的图片描述文本
- **`上传图片`**: 上传test.png作为参考图片
- **`设置比例 [比例]`**: 设置图片比例（如：设置比例 16:9）
- **`screenshot`**: 截图当前页面
- **`save`**: 手动保存登录状态
- **`quit` 或 `exit`**: 退出程序并自动保存登录状态

## 支持的图片比例

- **1:1** - 正方形，头像
- **2:3** - 社交媒体, 自拍
- **4:3** - 文章配图，插画
- **9:16** - 手机壁纸，人像
- **16:9** - 桌面壁纸，风景

## 技能选择逻辑

程序会根据当前页面URL自动选择合适的策略：

### 分支1: 主聊天页面 (https://www.doubao.com/chat/)
- 检查输入框是否已选择图像生成技能
- 如果未选择，在页面技能栏中点击"图像生成"按钮

### 分支2: 会话页面 (带有会话ID)
- 检查输入框是否已选择图像生成技能
- 如果未选择，点击"技能"按钮打开技能选择弹窗
- 在弹窗中选择"图像生成"技能

## 技术实现

### 网络监听机制

程序专门监听豆包生图的API调用：

- **API端点**: `/samantha/chat/completion`
- **响应格式**: SSE (Server-Sent Events) 流
- **事件类型**: 
  - `event_type: 2001` - 消息事件
  - `event_type: 2003` - 流结束事件
- **图片消息**: `content_type: 2074`
- **图片状态**: 只处理 `status: 2` 的完成图片

### 图片URL优先级

按照以下优先级获取无水印图片：

1. **image_ori_raw** - 原始无水印图片 (最高优先级)
2. **image_ori** - 原图
3. **image_preview** - 预览图
4. **image_thumb** - 缩略图

## DOM选择器

程序使用以下选择器来定位页面元素：

```python
selectors = {
    # 输入框相关
    "input_container": '[data-testid="chat_input"]',
    "text_input": '[data-testid="chat_input_input"]',
    "send_button": '[data-testid="chat_input_send_button"]',
    
    # 技能选择相关
    "skill_indicator": '.flex.items-center.s-font-base-em.text-s-color-brand-primary-default.select-none:has-text("图像生成")',
    "skill_bar_image_button": '[data-testid="skill_bar_button_3"]',
    "skill_button": '[data-testid="chat-input-all-skill-button"]',
    
    # 图像生成工具
    "reference_image_button": '[data-testid="image-creation-chat-input-picture-reference-button"]',
    "ratio_button": '[data-testid="image-creation-chat-input-picture-ration-button"]',
    "style_button": '[data-testid="image-creation-chat-input-picture-style-button"]',
}
```

## 使用示例

### 基本文本生图
```
👤 请输入消息: 一只可爱的小猫在花园里玩耍
```

### 设置比例后生图
```
👤 请输入消息: 设置比例 16:9
✅ 图片比例已设置为: 16:9

👤 请输入消息: 美丽的日落风景
```

### 上传参考图后生图
```
👤 请输入消息: 上传图片
✅ 参考图片上传成功

👤 请输入消息: 根据参考图生成类似风格的图片
```

## 注意事项

1. **登录状态**: 首次使用需要手动登录豆包账户，程序会自动保存登录状态
2. **参考图片**: 确保项目根目录下有test.png文件用于参考图上传
3. **网络监听**: 程序会监听豆包的API调用来获取响应
4. **页面状态**: 程序会自动检测和切换到图像生成技能

## 文件结构

```
src/core/interactive_doubao_image.py  # 主程序文件
examples/start_doubao_image_test.py   # 启动脚本
docs/DOUBAO_IMAGE_GUIDE.md           # 使用指南
data/cookies/                        # 保存的登录状态
data/screenshots/                    # 截图文件
```

## 故障排除

### 常见问题

1. **无法找到输入框**
   - 检查是否已登录豆包账户
   - 确认页面已完全加载
   - 尝试刷新页面

2. **技能选择失败**
   - 检查当前页面URL
   - 确认图像生成技能是否可用
   - 手动点击技能按钮后重试

3. **图片上传失败**
   - 确认test.png文件存在
   - 检查文件格式和大小
   - 确认已选择图像生成技能

4. **无法获取响应**
   - 检查网络连接
   - 确认豆包服务正常
   - 查看控制台日志信息

### 调试模式

如需查看详细日志，可以修改日志级别：

```python
logger.add(sys.stderr, level="DEBUG")
```

## 更新日志

- v1.0.0: 初始版本，支持基本的文本生图功能
- 支持智能技能选择
- 支持参考图片上传
- 支持图片比例设置
- 支持网络监听和响应处理
