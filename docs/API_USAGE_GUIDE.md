# AI Studio 图片生成API使用指南

## 概述

这是一个基于Google AI Studio的图片生成自动化服务，封装了复杂的浏览器交互逻辑，提供简单的REST API接口。

## 功能特性

- ✅ 纯文本提示词生成图片
- ✅ 支持参考图片的图片生成
- ✅ 自动解析AI响应，提取生成的图片和文本
- ✅ 防止并发执行，确保任务顺序处理
- ✅ 完整的错误处理和日志记录
- ✅ 支持base64图片编码传输

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn aiohttp requests loguru playwright
```

### 2. 启动服务

```bash
python start_api_server.py
```

服务将在 `http://localhost:8812` 启动

### 3. 访问API文档

打开浏览器访问: `http://localhost:8812/docs`

## API接口

### 健康检查

```http
GET /health
```

返回服务状态和初始化信息。

### 生成图片 (JSON)

```http
POST /generate
Content-Type: application/json

{
  "prompt": "画一只可爱的小猫咪，卡通风格",
  "reference_image_b64": "data:image/png;base64,iVBORw0KGgo..." // 可选
}
```

### 生成图片 (文件上传)

```http
POST /generate-with-file
Content-Type: multipart/form-data

prompt: 画一只可爱的小猫咪，卡通风格
reference_image: [文件] // 可选
```

### 响应格式

```json
{
  "success": true,
  "task_id": "uuid-string",
  "message": "图片生成成功",
  "generated_images": [
    "base64-encoded-image-1",
    "base64-encoded-image-2"
  ],
  "ai_text_response": "AI的文本回复"
}
```

## 使用测试客户端

### 运行测试

```bash
python test_api_client.py
```

测试客户端会：
1. 检查API服务状态
2. 测试纯文本生成
3. 测试带参考图片的生成
4. 自动保存生成的图片到本地

### 测试文件要求

确保当前目录有 `test.png` 文件作为参考图片。

## 重要说明

### 初始化过程

首次使用时，服务会：
1. 自动打开浏览器访问Google AI Studio
2. 需要用户手动登录Google账户
3. 导航到AI Studio对话页面
4. 系统会自动保存登录状态

### 并发限制

- 同时只能处理一个生成任务
- 新任务会等待当前任务完成
- 避免浏览器资源冲突

### 错误处理

常见错误及解决方案：

1. **初始化失败**: 检查网络连接，确保能访问Google AI Studio
2. **登录过期**: 删除 `cookies/` 目录，重新登录
3. **生成超时**: 增加超时时间或检查网络状况
4. **图片解析失败**: 检查AI Studio页面是否正常加载

## 目录结构

```
crawler_py/
├── ai_studio_api.py              # FastAPI服务主文件
├── interactive_ai_studio_test.py # AI Studio交互核心逻辑
├── crawler_framework.py          # 爬虫框架
├── start_api_server.py           # 服务启动脚本
├── test_api_client.py            # 测试客户端
├── cookies/                      # 登录状态保存目录
├── logs/                         # 日志文件目录
└── test.png                      # 测试参考图片
```

## 开发说明

### 扩展功能

1. **添加新的生成参数**: 修改 `ImageGenerationRequest` 模型
2. **增强响应解析**: 修改 `_parse_generation_response` 方法
3. **添加新的API端点**: 在 `ai_studio_api.py` 中添加新路由

### 调试技巧

1. 启用DEBUG日志级别查看详细信息
2. 检查 `screenshots/` 目录中的页面截图
3. 查看 `logs/` 目录中的详细日志

## 故障排除

### 常见问题

1. **浏览器无法启动**
   - 检查Playwright是否正确安装
   - 运行 `playwright install` 安装浏览器

2. **API响应解析失败**
   - 检查AI Studio页面结构是否变化
   - 更新响应解析逻辑

3. **图片上传失败**
   - 确保图片文件格式正确
   - 检查文件大小限制

### 联系支持

如遇到问题，请检查：
1. 日志文件中的错误信息
2. 浏览器截图
3. 网络连接状态

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的图片生成功能
- 完整的API接口和测试客户端
