#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio 生图自动化API服务
基于FastAPI封装，提供图片生成接口
"""

import asyncio
import base64
import json
import uuid
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from io import BytesIO
import threading

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
import uvicorn

from src.core.interactive_ai_studio import AIStudioInteractiveClient
from src.core.browser_manager import browser_manager


class ImageGenerationRequest(BaseModel):
    """图片生成请求模型"""
    prompt: str  # 文本提示词
    reference_images_b64: Optional[List[str]] = None  # 多个参考图片的base64编码列表
    aspect_ratio: Optional[str] = "Auto"  # 图片比例，默认Auto


class ImageGenerationResponse(BaseModel):
    """图片生成响应模型"""
    success: bool
    task_id: str
    message: str
    generated_images: Optional[List[str]] = None  # base64编码的生成图片列表
    ai_text_response: Optional[str] = None  # AI的文本回复


class AIStudioImageGenerator:
    """AI Studio图片生成器（支持多实例并发）"""
    
    def __init__(self):
        self.is_initialized = False
        self.task_lock = threading.Lock()
        self.active_tasks = {}  # 记录活跃任务
        
    async def initialize(self):
        """初始化浏览器管理器（不再直接启动浏览器）"""
        if self.is_initialized:
            return True
            
        try:
            logger.info("初始化AI Studio图片生成器（多实例模式）...")
            
            # 检查是否有可用的浏览器实例
            running_instances = browser_manager.get_running_instances()
            if len(running_instances) == 0:
                logger.warning("当前没有运行中的浏览器实例")
                logger.info("请通过管理界面启动至少一个浏览器实例")
                # 不返回False，允许API启动，但生成任务会等待实例
            
            self.is_initialized = True
            logger.success(f"AI Studio图片生成器初始化完成，当前有 {len(running_instances)} 个可用实例")
            return True
            
        except Exception as e:
            logger.error(f"初始化AI Studio图片生成器失败: {e}")
            return False
    
    async def generate_image(self, prompt: str, reference_images_b64: Optional[List[str]] = None, aspect_ratio: str = "Auto") -> Dict[str, Any]:
        """生成图片（支持并发）"""
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 获取可用的浏览器实例
        available_instance = browser_manager.get_available_instance()
        if not available_instance:
            return {
                "success": False,
                "message": "当前没有可用的浏览器实例，请通过管理界面启动浏览器实例",
                "task_id": task_id
            }
        
        # 标记实例为忙碌状态
        browser_manager.set_instance_busy(available_instance.instance_id, True)
        
        with self.task_lock:
            self.active_tasks[task_id] = available_instance.instance_id
        
        try:
            logger.info(f"开始生成图片任务: {task_id} (实例: {available_instance.name})")
            logger.info(f"提示词: {prompt}")
            
            # 获取实例的AI Studio客户端
            ai_studio = available_instance.client
            if not ai_studio:
                raise Exception("浏览器实例客户端不可用")
            
            # 确保页面处于生图初始状态
            logger.info("确保页面处于生图初始状态...")
            if not await ai_studio.navigate_to_new_image_chat(check_initial_page=False):
                logger.warning("刷新到生图页面失败，但继续执行")
            else:
                # 刷新后需要重新查找输入元素
                if not await ai_studio.find_input_elements():
                    logger.warning("刷新后查找输入元素失败")
            
            # 设置图片比例（如果需要）
            if aspect_ratio != "Auto":
                logger.info(f"设置图片比例为: {aspect_ratio}")
                if not await ai_studio.set_aspect_ratio(aspect_ratio):
                    logger.warning("设置图片比例失败，但继续执行")
            
            # 处理参考图片上传（支持单个或多个）
            images_to_upload = []
            if reference_images_b64:
                images_to_upload.extend(reference_images_b64)
            
            if images_to_upload:
                logger.info(f"检测到 {len(images_to_upload)} 张参考图片，开始上传...")
                if not await self._upload_reference_images(images_to_upload, ai_studio):
                    return {
                        "success": False,
                        "message": "参考图片上传失败",
                        "task_id": task_id
                    }
            
            # 发送提示词
            logger.info("发送提示词到AI Studio...")
            if not await ai_studio.send_message(prompt):
                return {
                    "success": False,
                    "message": "发送提示词失败",
                    "task_id": task_id
                }
            
            # 等待并解析响应
            logger.info("等待AI响应...")
            result = await self._wait_for_response(ai_studio, timeout=300)
            
            if result["success"]:
                logger.success(f"图片生成任务完成: {task_id}")
                
                # 任务完成后进行清理工作
                logger.info("开始任务完成后的清理工作...")
                try:
                    await ai_studio.cleanup_after_task()
                    logger.info("任务完成后的清理工作完成")
                except Exception as e:
                    logger.warning(f"任务完成后的清理工作失败: {e}")
            else:
                logger.error(f"图片生成任务失败: {task_id}")
            
            result["task_id"] = task_id
            return result
            
        except Exception as e:
            logger.error(f"生成图片时出错: {e}")
            return {
                "success": False,
                "message": f"生成图片时出错: {str(e)}",
                "task_id": task_id
            }
        finally:
            # 释放实例和清理任务记录
            browser_manager.set_instance_busy(available_instance.instance_id, False)
            with self.task_lock:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    async def _upload_reference_images(self, images_b64: List[str], ai_studio) -> bool:
        """上传多个参考图片"""
        temp_files = []
        # 使用任务ID确保文件名唯一性，避免并发冲突
        task_unique_id = str(uuid.uuid4())[:8]
        
        try:
            # 为每张图片创建临时文件
            for i, image_b64 in enumerate(images_b64):
                # 使用UUID确保并发安全的文件名
                temp_image_path = Path(f"temp_reference_{task_unique_id}_{i}.png")
                temp_files.append(temp_image_path)
                
                # 解码base64图片
                if image_b64.startswith('data:image'):
                    # 移除data:image/png;base64,前缀
                    image_b64 = image_b64.split(',')[1]
                
                image_data = base64.b64decode(image_b64)
                
                # 保存临时文件
                with open(temp_image_path, 'wb') as f:
                    f.write(image_data)
            
            # 逐个上传图片
            for i, temp_path in enumerate(temp_files):
                logger.info(f"正在上传第 {i+1}/{len(temp_files)} 张参考图片...")
                success = await ai_studio.upload_image_and_text(str(temp_path))
                if not success:
                    logger.error(f"第 {i+1} 张参考图片上传失败")
                    return False
                
                # 在多个图片上传之间稍作等待
                if i < len(temp_files) - 1:
                    await asyncio.sleep(1)
            
            logger.success(f"成功上传 {len(images_b64)} 张参考图片")
            return True
            
        except Exception as e:
            logger.error(f"上传参考图片失败: {e}")
            return False
        finally:
            # 无论成功还是失败，都要清理临时文件
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        logger.debug(f"已清理临时文件: {temp_file}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败 {temp_file}: {cleanup_error}")
    
    async def _upload_reference_image(self, image_b64: str, ai_studio) -> bool:
        """上传单个参考图片（向后兼容）"""
        return await self._upload_reference_images([image_b64], ai_studio)
    
    async def _wait_for_response(self, ai_studio, timeout: int = 300) -> Dict[str, Any]:
        """等待AI响应并解析结果"""
        try:
            # 等待响应（默认最多5分钟）
            for i in range(timeout * 2):  # 每0.5秒检查一次
                if not ai_studio.waiting_for_response:
                    break
                await asyncio.sleep(0.5)
            
            if ai_studio.waiting_for_response:
                return {
                    "success": False,
                    "message": "等待AI响应超时"
                }
            
            # 解析最新的API响应
            if not ai_studio.api_responses:
                return {
                    "success": False,
                    "message": "未收到API响应"
                }
            
            latest_response = ai_studio.api_responses[-1]
            return self._parse_generation_response(latest_response)
            
        except Exception as e:
            logger.error(f"等待响应时出错: {e}")
            return {
                "success": False,
                "message": f"等待响应时出错: {str(e)}"
            }
    
    def _parse_generation_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析生成响应，提取图片和文本"""
        try:
            logger.info("开始解析生成响应...")
            
            response_data = api_response.get("data")
            if not response_data:
                return {
                    "success": False,
                    "message": "响应数据为空"
                }
            
            # 提取文本回复 - 使用通用方法
            ai_text = self._extract_ai_response(response_data)
            
            # 提取图片数据
            generated_images = self._extract_images_from_response(response_data)
            
            # 过滤掉文本中的图片标识
            if ai_text:
                ai_text = ai_text.replace("image/png", "").strip()
            
            return {
                "success": True,
                "message": "图片生成成功",
                "generated_images": generated_images,
                "ai_text_response": ai_text
            }
            
        except Exception as e:
            logger.error(f"解析生成响应失败: {e}")
            return {
                "success": False,
                "message": f"解析响应失败: {str(e)}"
            }
    
    def _extract_ai_response(self, response_data) -> Optional[str]:
        """从API响应中提取AI回复文本"""
        try:
            logger.debug(f"开始解析响应数据: {type(response_data)}")
            
            # 根据响应结构解析
            if isinstance(response_data, list) and len(response_data) > 0:
                texts = []
                # 查找所有包含"model"标识的结构
                self._find_model_responses(response_data, texts)
                
                if texts:
                    result = "".join(texts)
                    logger.debug(f"提取到文本: {result}")
                    return result
                else:
                    logger.warning("未能从响应中提取到文本内容")
                    return None
            return None
        except Exception as e:
            logger.error(f"提取AI响应失败: {e}")
            return None
    
    def _find_model_responses(self, data, texts: list, depth=0):
        """递归查找包含'model'标识的响应文本"""
        if depth > 15:  # 防止无限递归
            return
            
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list) and len(item) >= 2:
                    # 检查是否是 [..., "model"] 结构
                    if item[1] == "model":
                        # 找到model结构，提取第一个元素中的文本
                        logger.debug(f"找到model结构: {item}")
                        self._extract_text_from_model_structure(item[0], texts)
                    else:
                        # 继续递归查找
                        self._find_model_responses(item, texts, depth + 1)
                elif isinstance(item, list):
                    # 继续递归查找
                    self._find_model_responses(item, texts, depth + 1)
    
    def _extract_text_from_model_structure(self, data, texts: list, depth=0):
        """从model结构中提取文本内容"""
        if depth > 10:  # 防止无限递归
            return
            
        if isinstance(data, str) and data.strip():
            # 过滤掉那些看起来像token的字符串和图片标识
            if (not data.startswith("v1:") and 
                len(data) < 1000 and 
                data != "image/png" and 
                not data.startswith("iVBORw0KGgo")):  # PNG base64开头
                texts.append(data)
                logger.debug(f"提取到文本片段: {data}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, list) and len(item) >= 2:
                    # 查找 [null, "文本内容"] 结构
                    if item[0] is None and isinstance(item[1], str):
                        text = item[1].strip()
                        if (text and 
                            not text.startswith("v1:") and 
                            text != "image/png" and 
                            not text.startswith("iVBORw0KGgo")):
                            texts.append(text)
                            logger.debug(f"提取到文本: {text}")
                    # 查找 ["image/png", base64_data] 结构但不提取到文本中
                    elif item[0] == "image/png":
                        logger.debug("检测到图片数据，跳过文本提取")
                        continue
                    else:
                        self._extract_text_from_model_structure(item, texts, depth + 1)
                else:
                    self._extract_text_from_model_structure(item, texts, depth + 1)

    def _extract_images_from_response(self, response_data) -> List[str]:
        """从响应数据中提取base64编码的图片"""
        try:
            images = []
            self._find_images_recursive(response_data, images)
            
            logger.info(f"提取到 {len(images)} 张图片")
            return images
            
        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            return []
    
    def _find_images_recursive(self, data, images: List[str], depth=0):
        """递归查找响应中的图片数据"""
        if depth > 20:  # 防止无限递归
            return
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list) and len(item) >= 2:
                    # 查找 ["image/png", base64_data] 结构
                    if item[0] == "image/png" and isinstance(item[1], str):
                        # 验证是否为有效的base64图片数据
                        if self._is_valid_base64_image(item[1]):
                            images.append(item[1])
                            logger.debug("找到图片数据")
                    else:
                        self._find_images_recursive(item, images, depth + 1)
                elif isinstance(item, list):
                    self._find_images_recursive(item, images, depth + 1)
        elif isinstance(data, dict):
            for value in data.values():
                self._find_images_recursive(value, images, depth + 1)
    
    def _is_valid_base64_image(self, data: str) -> bool:
        """验证是否为有效的base64图片数据"""
        try:
            if len(data) < 100:  # 太短不可能是图片
                return False
            
            # 尝试解码base64
            decoded = base64.b64decode(data)
            
            # 检查是否以PNG文件头开始
            return decoded.startswith(b'\x89PNG\r\n\x1a\n')
            
        except Exception:
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.ai_studio:
                await self.ai_studio.cleanup()
            logger.info("AI Studio图片生成器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局生成器实例
generator = AIStudioImageGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动AI Studio图片生成API服务（多实例模式）...")
    
    # 初始化生成器（不启动浏览器）
    if await generator.initialize():
        logger.success("AI Studio生成器初始化完成")
    else:
        logger.error("AI Studio生成器初始化失败")
    
    logger.info("浏览器实例管理:")
    logger.info("- 通过管理界面 (http://localhost:8813) 创建和管理浏览器实例")
    logger.info("- 生图任务的并发数 = 运行中的浏览器实例数")
    
    logger.success("API服务启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭AI Studio图片生成API服务...")
    await browser_manager.cleanup_all()
    logger.success("API服务已关闭")


# FastAPI应用
app = FastAPI(
    title="AI Studio 图片生成API",
    description="基于Google AI Studio的图片生成自动化服务",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Studio 图片生成API服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    running_instances = browser_manager.get_running_instances()
    available_instances = [i for i in running_instances if not i.is_busy]
    
    return {
        "status": "healthy",
        "ai_studio_initialized": generator.is_initialized,
        "browser_instances": {
            "total": len(browser_manager.instances),
            "running": len(running_instances),
            "available": len(available_instances),
            "busy": len(running_instances) - len(available_instances)
        },
        "concurrency_capacity": len(running_instances),
        "active_tasks": len(generator.active_tasks),
        "timestamp": datetime.now().isoformat(),
        "message": f"系统就绪，当前有 {len(running_instances)} 个浏览器实例运行中"
    }


@app.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """生成图片接口"""
    try:
        logger.info(f"收到图片生成请求: {request.prompt[:50]}...")
        
        # 调用生成器
        result = await generator.generate_image(
            prompt=request.prompt,
            reference_images_b64=request.reference_images_b64,
            aspect_ratio=request.aspect_ratio
        )
        
        return ImageGenerationResponse(
            success=result["success"],
            task_id=result["task_id"],
            message=result["message"],
            generated_images=result.get("generated_images"),
            ai_text_response=result.get("ai_text_response")
        )
        
    except Exception as e:
        logger.error(f"处理生成请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@app.post("/generate-with-file")
async def generate_image_with_file(
    prompt: str = Form(...),
    reference_images: Optional[List[UploadFile]] = File(None),
    aspect_ratio: str = Form("Auto")
):
    """使用文件上传的图片生成接口（支持多个文件）"""
    try:
        reference_images_b64 = None
        
        # 处理上传的参考图片
        if reference_images:
            logger.info(f"收到 {len(reference_images)} 张参考图片")
            reference_images_b64 = []
            
            for i, reference_image in enumerate(reference_images):
                logger.info(f"处理第 {i+1} 张图片: {reference_image.filename}")
                
                # 读取文件内容
                image_content = await reference_image.read()
                
                # 转换为base64
                image_b64 = base64.b64encode(image_content).decode('utf-8')
                image_b64 = f"data:image/png;base64,{image_b64}"
                reference_images_b64.append(image_b64)
        
        # 调用生成器
        result = await generator.generate_image(
            prompt=prompt,
            reference_images_b64=reference_images_b64,
            aspect_ratio=aspect_ratio
        )
        
        return ImageGenerationResponse(
            success=result["success"],
            task_id=result["task_id"],
            message=result["message"],
            generated_images=result.get("generated_images"),
            ai_text_response=result.get("ai_text_response")
        )
        
    except Exception as e:
        logger.error(f"处理文件上传生成请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    return {
        "task_id": task_id,
        "status": "completed" if generator.current_task != task_id else "running",
        "message": "任务状态查询"
    }


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭服务...")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 配置日志
    logger.remove()
    logger.add(
        "logs/ai_studio_api_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}\n"
    )
    
    try:
        # 启动服务
        uvicorn.run(
            "ai_studio_api:app",
            host="0.0.0.0",
            port=8812,
            reload=False,  # 关闭reload避免复杂的进程管理
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("服务被用户中断")
    except Exception as e:
        logger.error(f"服务运行失败: {e}")
    finally:
        logger.info("服务已退出")
