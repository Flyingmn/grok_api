# 纯生图业务流程使用指南

## 概述

根据`纯生图业务.txt`中的需求，我们实现了完整的生图业务流程，包括导航、删除对话、设置比例等功能。

## 重要流程说明

### ⚠️ 正确的业务流程顺序

**错误做法（会误删用户对话）：**
```
开始任务 → 删除当前对话 → 生成图片
```

**正确做法（保护用户对话）：**
```
开始任务 → 检查页面URL → 如需要则跳转到生图页面 → 设置比例 → 生成图片 → 任务完成后删除对话 → 准备下次任务
```

### 🔍 自动页面刷新

系统会在每次任务开始时自动刷新页面到生图初始状态：
- **目标URL**: `https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image`
- **刷新原因**: 首次画图时URL可能不变，但页面已有对话内容，需要刷新到初始状态
- **刷新后**: 重新查找输入元素，确保功能正常

## 新增的方法

### 1. 导航相关

#### `navigate_to_new_image_chat()`
- **功能**: 导航到新的生图对话页面
- **URL**: `https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image`
- **使用场景**: 需要开始新的生图会话时

```python
success = await client.navigate_to_new_image_chat()
```

### 2. 对话管理

#### `delete_current_conversation()`
- **功能**: 删除当前对话的完整流程
- **步骤**: 
  1. 点击更多操作按钮 (`more_vert`)
  2. 点击删除按钮
  3. 确认删除
- **使用场景**: 任务完成后清理

```python
success = await client.delete_current_conversation()
```

### 3. 比例设置

#### `set_aspect_ratio(ratio: str = "Auto")`
- **功能**: 设置图片生成比例
- **支持的比例**: Auto, 1:1, 9:16, 16:9, 3:4, 4:3, 3:2, 2:3, 5:4, 4:5, 21:9
- **使用场景**: 根据需求设置不同的图片比例

```python
success = await client.set_aspect_ratio("16:9")
```

### 4. 页面检查

#### `ensure_on_image_generation_page()`
- **功能**: 确保当前页面是生图页面并刷新到初始状态
- **逻辑**: 总是导航到生图页面，确保页面处于初始状态（不比较URL）
- **使用场景**: 在发送消息或上传图片前自动调用

```python
success = await client.ensure_on_image_generation_page()
```

### 5. 组合流程

#### `prepare_new_image_session(aspect_ratio: str = "Auto")`
- **功能**: 准备新的生图会话（不删除当前对话）
- **步骤**:
  1. 导航到新的生图对话页面
  2. 设置图片比例
  3. 重新查找输入元素
- **使用场景**: 开始新任务时的准备工作

```python
success = await client.prepare_new_image_session("16:9")
```

#### `cleanup_after_task()`
- **功能**: 任务完成后的清理工作
- **步骤**:
  1. 删除当前对话
  2. 导航到新的生图对话页面
- **使用场景**: 任务完成后为下次任务做准备

```python
success = await client.cleanup_after_task()
```

## API 使用

### 请求参数

新增了 `aspect_ratio` 参数，默认值为 "Auto"：

```json
{
    "prompt": "一只可爱的小猫",
    "aspect_ratio": "16:9",
    "reference_image_b64": "base64编码的图片（可选）"
}
```

### 文件上传接口

```python
import requests

files = {'reference_image': ('image.png', open('image.png', 'rb'), 'image/png')}
data = {
    'prompt': '生成一张图片',
    'aspect_ratio': '1:1'
}

response = requests.post('http://localhost:8812/generate-with-file', files=files, data=data)
```

## 交互式命令

在交互式客户端中，新增了以下命令：

- `新会话` - 导航到新的生图页面并设置比例（不删除当前对话）
- `删除对话` - 删除当前对话
- `设置比例 [比例]` - 设置图片比例（如：设置比例 16:9）
- `任务清理` - 删除当前对话并导航到新页面（任务完成后使用）

## 完整的业务流程示例

### API 自动化流程

```python
# 1. 初始化
generator = AIStudioImageGenerator()
await generator.initialize()

# 2. 生成图片（会自动检查页面URL、设置比例）
result = await generator.generate_image(
    prompt="一只可爱的小猫",
    aspect_ratio="16:9"
)

# 3. 任务完成后自动清理（在 generate_image 内部完成）
# - 删除当前对话
# - 导航到新页面准备下次任务
```

**自动处理流程**：
1. 刷新页面到生图初始状态（不比较URL，总是刷新）
2. 设置指定的图片比例
3. 上传参考图片（如果有）
4. 发送提示词生成图片
5. 任务完成后尝试删除对话（如果删除按钮被禁用则跳过）
6. 导航到新页面准备下次任务

### 手动交互流程

```python
# 1. 开始新任务
await client.prepare_new_image_session("16:9")

# 2. 发送消息生成图片
await client.send_message("生成一只可爱的小猫")

# 3. 任务完成后清理
await client.cleanup_after_task()
```

## 注意事项

1. **保护用户对话**: 不要在任务开始时删除对话，避免误删用户正在进行的对话
2. **任务完成后清理**: 只在任务成功完成后才进行清理工作
3. **比例设置**: 支持多种比例，根据实际需求选择
4. **错误处理**: 所有方法都有完善的错误处理和日志记录
5. **首次画图处理**: 首次画图时删除按钮可能被禁用，系统会自动跳过删除直接刷新页面
6. **页面刷新**: 每次任务开始都会刷新页面到初始状态，确保干净的开始环境

## 测试

运行测试脚本验证功能：

```bash
# 测试业务流程方法
python examples/test_new_workflow.py

# 测试API比例配置
python examples/test_api_with_aspect_ratio.py
```
