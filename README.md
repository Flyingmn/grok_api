# AI 图片生成自动化项目

基于Google AI Studio和豆包生图的图片生成自动化服务，提供REST API接口和交互式客户端。

## 项目结构

```
crawler_py/
├── src/                    # 源代码
│   ├── api/               # API服务模块
│   │   ├── __init__.py
│   │   └── ai_studio_api.py
│   ├── core/              # 核心功能模块
│   │   ├── __init__.py
│   │   ├── crawler_framework.py
│   │   ├── interactive_ai_studio.py
│   │   └── interactive_doubao_image.py
│   └── utils/             # 工具模块
├── tests/                 # 测试文件
│   ├── test_api_client.py
│   └── simple_test.py
├── scripts/               # 脚本文件
│   ├── start_api_server.py
│   ├── run_image_generation.py
│   └── setup_conda_env.sh
├── config/                # 配置文件
│   ├── requirements.txt
│   ├── environment.yml
│   └── config.json.example
├── docs/                  # 文档
│   ├── API_USAGE_GUIDE.md
│   ├── PERSISTENT_BROWSER_GUIDE.md
│   └── DOUBAO_IMAGE_GUIDE.md
├── data/                  # 数据目录
│   ├── logs/             # 日志文件
│   ├── screenshots/      # 截图文件
│   └── cookies/          # Cookie文件
├── examples/              # 示例代码
│   ├── start_interactive_test.py
│   └── start_doubao_image_test.py
├── main.py               # 主启动脚本
└── test.py               # 快速测试脚本
```

## 快速开始

### 1. 环境准备

```bash
# 激活conda环境
conda activate camoufox-crawler

# 安装依赖
pip install -r config/requirements.txt
```

### 2. 启动服务

#### Google AI Studio API服务
```bash
# 启动API服务
python main.py
```

服务将在 `http://localhost:8812` 启动

#### 豆包生图交互客户端
```bash
# 启动豆包生图交互测试
python examples/start_doubao_image_test.py
```

### 3. 测试服务

```bash
# 快速测试API服务
python test.py

# 测试豆包生图功能
python tests/test_doubao_image.py
```

### 4. 访问API文档

打开浏览器访问: `http://localhost:8812/docs`

## API接口

### 生成图片

```http
POST /generate
Content-Type: application/json

{
  "prompt": "画一只可爱的小猫咪，卡通风格",
  "reference_image_b64": "data:image/png;base64,...", // 可选
  "aspect_ratio": "16:9"
}
```

### 健康检查

```http
GET /health
```

## 功能特性

### Google AI Studio API服务
- ✅ 纯文本提示词生成图片
- ✅ 支持参考图片的图片生成
- ✅ 自动解析AI响应，提取生成的图片和文本
- ✅ 防止并发执行，确保任务顺序处理
- ✅ 完整的错误处理和日志记录
- ✅ 支持base64图片编码传输

### 豆包生图交互客户端
- ✅ 自动导航到豆包聊天页面
- ✅ 智能选择图像生成技能
- ✅ 支持文本输入和参考图片上传
- ✅ 支持图片比例设置（1:1, 2:3, 4:3, 9:16, 16:9）
- ✅ 实时监听和显示AI响应
- ✅ 自动保存和加载登录状态
- ✅ 终端交互式操作界面

## 开发说明

### 目录说明

- `src/api/`: FastAPI服务相关代码
- `src/core/`: 核心爬虫框架和AI Studio交互逻辑
- `tests/`: 测试代码和测试客户端
- `scripts/`: 各种辅助脚本
- `config/`: 配置文件和依赖文件
- `docs/`: 项目文档
- `data/`: 运行时数据（日志、截图、cookies等）

### 开发模式

```bash
# 开发模式启动（带重载）
uvicorn src.api.ai_studio_api:app --reload --host 0.0.0.0 --port 8812
```

## 注意事项

### Google AI Studio
1. 首次使用需要手动登录Google AI Studio
2. 登录状态会自动保存在 `data/cookies/` 目录
3. 同时只能处理一个生成任务
4. 生成的图片会以base64格式返回

### 豆包生图
1. 首次使用需要手动登录豆包账户
2. 程序会自动检测和选择图像生成技能
3. 支持参考图片上传（需要test.png文件）
4. 支持多种图片比例设置

## 故障排除

- Google AI Studio API: 请参考 `docs/API_USAGE_GUIDE.md`
- 豆包生图交互: 请参考 `docs/DOUBAO_IMAGE_GUIDE.md`
