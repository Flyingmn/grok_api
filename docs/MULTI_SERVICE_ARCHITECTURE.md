# 多服务架构说明

## 概述

本项目现在支持多个AI图片生成服务，每个服务都有独立的API和管理界面，支持多浏览器实例并发处理。

## 架构设计

### 基础组件

1. **BaseImageGenerator** (`src/api/base_image_api.py`)
   - 抽象基类，定义图片生成器的通用接口
   - 处理浏览器实例管理、任务调度、响应解析等通用逻辑
   - 子类只需实现具体的生成逻辑

2. **ServiceBrowserManager** (`src/core/service_browser_manager.py`)
   - 服务专用浏览器管理器基类
   - 每个服务有独立的浏览器实例管理
   - 支持不同类型的客户端（AI Studio、豆包等）

3. **create_management_app** (`src/api/base_management_api.py`)
   - 通用浏览器管理界面生成器
   - 提供统一的Web管理界面
   - 支持实例创建、启动、停止、删除等操作

4. **BaseMultiInstanceServer** (`src/api/base_multi_instance_server.py`)
   - 多实例服务器基础类
   - 统一的服务启动和管理逻辑
   - 支持同时启动API服务和管理界面

### 服务实现

#### AI Studio 服务

- **API服务**: `src/api/ai_studio_api_refactored.py` (端口: 8812)
- **管理界面**: `src/api/ai_studio_management_api.py` (端口: 8813)
- **启动脚本**: `main_refactored.py`

#### 豆包服务

- **API服务**: `src/api/doubao_api.py` (端口: 8814)
- **管理界面**: `src/api/doubao_management_api.py` (端口: 8815)
- **启动脚本**: `doubao_main.py`

## 使用方法

### 启动AI Studio服务

```bash
# 启动完整的AI Studio多实例服务（API + 管理界面）
python main_refactored.py

# 或者单独启动API服务
python -m src.api.ai_studio_api_refactored
```

访问地址：
- API服务: http://localhost:8812
- 管理界面: http://localhost:8813
- API文档: http://localhost:8812/docs

### 启动豆包服务

```bash
# 启动完整的豆包多实例服务（API + 管理界面）
python doubao_main.py

# 或者单独启动API服务
python scripts/start_doubao_api_server.py
```

访问地址：
- API服务: http://localhost:8814
- 管理界面: http://localhost:8815
- API文档: http://localhost:8814/docs

## API接口

所有服务都提供相同的API接口：

### 生成图片

**POST** `/generate`

```json
{
    "prompt": "一只可爱的小猫",
    "reference_images_b64": ["data:image/png;base64,..."],
    "aspect_ratio": "1:1"
}
```

**响应**:
```json
{
    "success": true,
    "task_id": "uuid",
    "message": "图片生成成功",
    "generated_images": ["base64_image_data"],
    "ai_text_response": "AI的文本回复"
}
```

### 文件上传生成

**POST** `/generate-with-file`

支持直接上传图片文件作为参考图。

### 健康检查

**GET** `/health`

返回服务状态和浏览器实例信息。

## 浏览器实例管理

每个服务都有独立的浏览器实例管理：

1. **独立管理**: AI Studio和豆包使用各自的浏览器管理器
2. **创建实例**: 在管理界面创建新的浏览器实例
3. **启动实例**: 启动浏览器并导航到对应服务页面
4. **任务分配**: API自动将任务分配给可用的实例
5. **并发处理**: 支持多个实例同时处理不同的生成任务
6. **数据隔离**: 不同服务的实例数据分别存储

## 扩展新服务

要添加新的AI服务支持，只需：

1. **创建浏览器管理器类**:
```python
class NewServiceBrowserManager(ServiceBrowserManager):
    def __init__(self):
        from .interactive_new_service import NewServiceInteractiveClient
        super().__init__("NewService", NewServiceInteractiveClient)
    
    async def _initialize_client(self, client) -> bool:
        # 实现客户端初始化逻辑
        if not await client.setup():
            return False
        if not await client.navigate_to_service():
            return False
        return True
```

2. **创建生成器类**:
```python
class NewServiceGenerator(BaseImageGenerator):
    def __init__(self):
        super().__init__("新服务名称", new_service_browser_manager)
    
    async def _generate_image_impl(self, client, prompt, reference_images_b64, aspect_ratio, task_id):
        # 实现具体的生成逻辑
        pass
    
    async def _cleanup_after_task(self, client):
        # 实现清理逻辑
        pass
    
    async def _upload_single_image(self, client, image_path):
        # 实现图片上传逻辑
        pass
```

3. **创建API应用**:
```python
from src.api.base_image_api import create_image_api_app

generator = NewServiceGenerator()
app = create_image_api_app(
    generator=generator,
    title="新服务 图片生成API",
    description="新服务的图片生成自动化服务"
)
```

4. **创建管理界面**:
```python
from src.api.base_management_api import create_management_app

management_app = create_management_app(
    service_name="新服务",
    service_title="新服务",
    api_port=8816,  # 新的端口
    browser_manager=new_service_browser_manager
)
```

5. **创建启动脚本**:
```python
from src.api.base_multi_instance_server import create_main_function

main = create_main_function(
    service_name="新服务",
    api_app=app,
    management_app=management_app,
    api_port=8816,
    management_port=8817
)
```

## 优势

1. **代码复用**: 通用逻辑抽象到基础类，减少重复代码
2. **易于扩展**: 新增服务只需实现少量特定逻辑
3. **统一接口**: 所有服务提供相同的API接口
4. **独立部署**: 每个服务可以独立启动和管理
5. **并发支持**: 每个服务都支持多实例并发处理
6. **易于维护**: 清晰的架构分层，便于维护和调试

## 注意事项

1. 确保不同服务使用不同的端口避免冲突
2. 每个服务的浏览器实例是独立管理的
3. 日志文件按服务分别存储
4. Cookie和会话状态按服务分别保存
