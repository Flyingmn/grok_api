# 多参考图片功能使用指南

## 概述

AI Studio API现在支持同时上传多个参考图片进行图片生成。这个功能允许您：

- 同时使用多张参考图片来指导AI生成
- 融合多种风格和元素
- 提供更丰富的视觉参考信息

## API变更

### 1. 请求模型更新

`ImageGenerationRequest` 模型新增了以下字段：

```python
class ImageGenerationRequest(BaseModel):
    prompt: str  # 文本提示词
    reference_image_b64: Optional[str] = None  # 单个参考图片（向后兼容）
    reference_images_b64: Optional[List[str]] = None  # 多个参考图片列表
    aspect_ratio: Optional[str] = "Auto"  # 图片比例
```

### 2. 向后兼容性

- 原有的 `reference_image_b64` 字段仍然支持
- 新的 `reference_images_b64` 字段支持多个图片
- 两个字段可以同时使用，系统会合并处理

## 使用方法

### 方法1: JSON API调用

```python
import aiohttp
import asyncio

async def generate_with_multiple_images():
    api_url = "http://localhost:8812/generate"
    
    request_data = {
        "prompt": "根据这些参考图片，生成一个融合风格的新图片",
        "reference_images_b64": [
            "data:image/png;base64,iVBORw0KGgo...",  # 第一张图片
            "data:image/png;base64,iVBORw0KGgo...",  # 第二张图片
            "data:image/png;base64,iVBORw0KGgo..."   # 第三张图片
        ],
        "aspect_ratio": "16:9"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=request_data) as response:
            result = await response.json()
            print(f"任务ID: {result['task_id']}")
            print(f"生成结果: {result['message']}")
```

### 方法2: 文件上传API

```python
import aiohttp

async def generate_with_file_upload():
    api_url = "http://localhost:8812/generate-with-file"
    
    # 准备表单数据
    data = aiohttp.FormData()
    data.add_field('prompt', '根据这些参考图片生成新作品')
    data.add_field('aspect_ratio', '1:1')
    
    # 添加多个图片文件
    image_files = ['image1.png', 'image2.jpg', 'image3.png']
    for image_path in image_files:
        with open(image_path, 'rb') as f:
            data.add_field('reference_images', f.read(), 
                         filename=image_path, 
                         content_type='image/png')
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, data=data) as response:
            result = await response.json()
            print(f"生成结果: {result}")
```

### 方法3: 混合使用（向后兼容）

```python
# 同时使用单个和多个参考图片字段
request_data = {
    "prompt": "生成融合风格的图片",
    "reference_image_b64": "data:image/png;base64,iVBORw0KGgo...",  # 主要参考图
    "reference_images_b64": [
        "data:image/png;base64,iVBORw0KGgo...",  # 辅助参考图1
        "data:image/png;base64,iVBORw0KGgo..."   # 辅助参考图2
    ],
    "aspect_ratio": "Auto"
}
```

## 功能特点

### 1. 智能合并处理

- 系统会自动合并 `reference_image_b64` 和 `reference_images_b64` 中的所有图片
- 按顺序逐个上传到AI Studio
- 每张图片上传之间有适当的间隔，确保稳定性

### 2. 并发安全性

- 使用UUID生成唯一的临时文件名，避免并发冲突
- 每个任务的临时文件完全独立，互不干扰
- 支持多个浏览器实例同时处理不同任务
- 实时状态监控和管理

### 3. 错误处理与资源管理

- 如果任何一张参考图片上传失败，整个任务会停止并返回错误
- 使用 `try-finally` 确保临时文件在任何情况下都会被清理
- 详细的错误日志记录和调试信息
- 防止磁盘空间泄漏

## 最佳实践

### 1. 图片数量建议

- 建议同时使用2-5张参考图片
- 过多的参考图片可能会影响生成效果
- 确保参考图片质量良好且相关性强

### 2. 图片格式要求

- 支持常见格式：PNG, JPG, JPEG, WebP
- 建议图片大小不超过10MB
- Base64编码时注意数据大小限制

### 3. 提示词优化

- 在提示词中明确说明如何使用多个参考图片
- 例如："融合这些参考图片的风格特点"
- 或者："参考第一张图的构图，第二张图的色彩"

## 测试示例

### 基础功能测试

运行基础功能测试脚本：

```bash
cd /Users/zhaojian/pyobj/crawler_py
python examples/test_multiple_reference_images.py
```

测试脚本包含：
- 多个参考图片的JSON API测试
- 多个文件上传的测试
- 向后兼容性测试

### 并发安全性测试

运行并发安全性测试脚本：

```bash
cd /Users/zhaojian/pyobj/crawler_py
python examples/test_concurrent_safety.py
```

并发测试包含：
- 多个并发请求同时执行
- 临时文件冲突检测
- 资源清理验证
- 系统稳定性测试

## 注意事项

1. **浏览器实例要求**: 确保至少有一个浏览器实例在运行
2. **网络稳定性**: 多个图片上传需要稳定的网络连接
3. **处理时间**: 多个参考图片会增加处理时间
4. **资源消耗**: 注意监控系统资源使用情况

## 故障排除

### 常见问题

1. **上传失败**
   - 检查图片格式是否支持
   - 验证Base64编码是否正确
   - 确认网络连接稳定

2. **处理超时**
   - 增加超时时间设置
   - 减少参考图片数量
   - 检查浏览器实例状态

3. **内存不足**
   - 优化图片大小
   - 增加系统内存
   - 减少并发任务数量

如有问题，请查看日志文件：`logs/ai_studio_api_YYYY-MM-DD.log`
