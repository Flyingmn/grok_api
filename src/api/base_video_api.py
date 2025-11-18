#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频生成API基础类
提供通用的视频生成API接口和实现
"""

import asyncio
import base64
import json
import uuid
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

class VideoGenerationRequest(BaseModel):
    """视频生成请求模型"""
    prompt: str  # 文本提示词
    reference_images_b64: Optional[List[str]] = None  # 多个参考图片的base64编码列表（可选）


class VideoGenerationResponse(BaseModel):
    """视频生成响应模型"""
    success: bool
    task_id: str
    message: str
    generated_videos: Optional[List[str]] = None  # base64编码的生成视频列表或视频URL列表
    video_urls: Optional[List[str]] = None  # 视频URL列表（如果视频太大，返回URL而不是base64）
    ai_text_response: Optional[str] = None  # AI的文本回复


class BaseVideoGenerator(ABC):
    """视频生成器基础类"""
    
    def __init__(self, service_name: str, browser_manager):
        self.service_name = service_name
        self.browser_manager = browser_manager
        self.is_initialized = False
        self.task_lock = threading.Lock()
        self.active_tasks = {}  # 记录活跃任务
        
    async def initialize(self):
        """初始化浏览器管理器（不再直接启动浏览器）"""
        if self.is_initialized:
            return True
            
        try:
            logger.info(f"初始化{self.service_name}视频生成器（多实例模式）...")
            
            # 检查是否有可用的浏览器实例
            running_instances = self.browser_manager.get_running_instances()
            if len(running_instances) == 0:
                logger.warning("当前没有运行中的浏览器实例")
                logger.info("请通过管理界面启动至少一个浏览器实例")
                # 不返回False，允许API启动，但生成任务会等待实例
            
            self.is_initialized = True
            logger.success(f"{self.service_name}视频生成器初始化完成，当前有 {len(running_instances)} 个可用实例")
            return True
            
        except Exception as e:
            logger.error(f"初始化{self.service_name}视频生成器失败: {e}")
            return False
    
    async def generate_video(self, prompt: str, reference_images_b64: Optional[List[str]] = None) -> Dict[str, Any]:
        """生成视频（支持并发）"""
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 获取可用的浏览器实例
        available_instance = self.browser_manager.get_available_instance()
        if not available_instance:
            return {
                "success": False,
                "message": "当前没有可用的浏览器实例，请通过管理界面启动浏览器实例",
                "task_id": task_id
            }
        
        # 标记实例为忙碌状态
        self.browser_manager.set_instance_busy(available_instance.instance_id, True)
        
        with self.task_lock:
            self.active_tasks[task_id] = available_instance.instance_id
        
        try:
            logger.info(f"开始生成视频任务: {task_id} (实例: {available_instance.name})")
            logger.info(f"提示词: {prompt}")
            
            # 获取实例的客户端
            client = available_instance.client
            if not client:
                raise Exception("浏览器实例客户端不可用")
            
            # 调用具体实现的生成方法
            result = await self._generate_video_impl(client, prompt, reference_images_b64, task_id)
            
            if result["success"]:
                logger.success(f"视频生成任务完成: {task_id}")
                
                # 任务完成后进行清理工作
                logger.info("开始任务完成后的清理工作...")
                try:
                    await self._cleanup_after_task(client)
                    logger.info("任务完成后的清理工作完成")
                except Exception as e:
                    logger.warning(f"任务完成后的清理工作失败: {e}")
            else:
                logger.error(f"视频生成任务失败: {task_id}")
            
            result["task_id"] = task_id
            return result
            
        except Exception as e:
            logger.error(f"生成视频时出错: {e}")
            return {
                "success": False,
                "message": f"生成视频时出错: {str(e)}",
                "task_id": task_id
            }
        finally:
            # 释放实例和清理任务记录
            self.browser_manager.set_instance_busy(available_instance.instance_id, False)
            with self.task_lock:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    @abstractmethod
    async def _generate_video_impl(self, client, prompt: str, reference_images_b64: Optional[List[str]], task_id: str) -> Dict[str, Any]:
        """具体的视频生成实现（子类需要实现）"""
        pass
    
    @abstractmethod
    async def _cleanup_after_task(self, client):
        """任务完成后的清理工作（子类需要实现）"""
        pass
    
    async def _upload_reference_images(self, images_b64: List[str], client, task_id: str) -> bool:
        """上传多个参考图片"""
        temp_files = []
        # 使用任务ID确保文件名唯一性，避免并发冲突
        task_unique_id = task_id[:8]
        
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
                success = await self._upload_single_image(client, str(temp_path))
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
    
    @abstractmethod
    async def _upload_single_image(self, client, image_path: str) -> bool:
        """上传单个图片（子类需要实现）"""
        pass
    
    async def _wait_for_response(self, client, timeout: int = 600) -> Dict[str, Any]:
        """等待AI响应并解析结果（视频生成可能需要更长时间）"""
        try:
            # 等待响应（默认最多10分钟，视频生成通常比图片生成需要更长时间）
            for i in range(timeout * 2):  # 每0.5秒检查一次
                if not client.waiting_for_response:
                    break
                await asyncio.sleep(0.5)
            
            if client.waiting_for_response:
                return {
                    "success": False,
                    "message": "等待AI响应超时"
                }
            
            # 解析最新的API响应
            if not client.api_responses:
                return {
                    "success": False,
                    "message": "未收到API响应"
                }
            
            latest_response = client.api_responses[-1]
            return self._parse_generation_response(latest_response)
            
        except Exception as e:
            logger.error(f"等待响应时出错: {e}")
            return {
                "success": False,
                "message": f"等待响应时出错: {str(e)}"
            }
    
    def _parse_generation_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析生成响应，提取视频和文本"""
        try:
            logger.info("开始解析生成响应...")
            
            response_data = api_response.get("data")
            if not response_data:
                return {
                    "success": False,
                    "message": "响应数据为空"
                }
            
            # 提取文本回复
            ai_text = self._extract_ai_response(response_data)
            
            # 提取视频数据
            generated_videos, video_urls = self._extract_videos_from_response(response_data)
            
            # 过滤掉文本中的视频标识
            if ai_text:
                ai_text = ai_text.replace("video/mp4", "").strip()
            
            return {
                "success": True,
                "message": "视频生成成功",
                "generated_videos": generated_videos,
                "video_urls": video_urls,
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
            # 过滤掉那些看起来像token的字符串和视频标识
            if (not data.startswith("v1:") and 
                len(data) < 1000 and 
                data != "video/mp4" and 
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
                            text != "video/mp4" and 
                            not text.startswith("iVBORw0KGgo")):
                            texts.append(text)
                            logger.debug(f"提取到文本: {text}")
                    # 查找视频数据但不提取到文本中
                    elif item[0] == "video/mp4" or item[0] == "video/webm":
                        logger.debug("检测到视频数据，跳过文本提取")
                        continue
                    else:
                        self._extract_text_from_model_structure(item, texts, depth + 1)
                else:
                    self._extract_text_from_model_structure(item, texts, depth + 1)

    def _extract_videos_from_response(self, response_data) -> tuple[List[str], List[str]]:
        """从响应数据中提取视频URL或base64编码的视频"""
        try:
            video_urls = []
            base64_videos = []
            self._find_videos_recursive(response_data, video_urls, base64_videos)
            
            logger.info(f"提取到 {len(video_urls)} 个视频URL, {len(base64_videos)} 个base64视频")
            return base64_videos, video_urls
            
        except Exception as e:
            logger.error(f"提取视频失败: {e}")
            return [], []
    
    def _find_videos_recursive(self, data, video_urls: List[str], base64_videos: List[str], depth=0):
        """递归查找响应中的视频数据"""
        if depth > 20:  # 防止无限递归
            return
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list) and len(item) >= 2:
                    # 查找 ["video/mp4", base64_data] 或 ["video/webm", base64_data] 结构
                    if item[0] in ["video/mp4", "video/webm"] and isinstance(item[1], str):
                        # 检查是URL还是base64
                        if item[1].startswith("http://") or item[1].startswith("https://"):
                            video_urls.append(item[1])
                            logger.debug("找到视频URL")
                        else:
                            # 可能是base64编码的视频
                            base64_videos.append(item[1])
                            logger.debug("找到base64视频数据")
                    else:
                        self._find_videos_recursive(item, video_urls, base64_videos, depth + 1)
                elif isinstance(item, list):
                    self._find_videos_recursive(item, video_urls, base64_videos, depth + 1)
        elif isinstance(data, dict):
            # 查找常见的视频字段
            video_fields = ["video", "video_url", "videoUrl", "url", "output", "result", "video_urls"]
            for field in video_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        if value.startswith("http://") or value.startswith("https://"):
                            if value not in video_urls:
                                video_urls.append(value)
                                logger.debug(f"从字段 {field} 找到视频URL: {value}")
                    elif isinstance(value, list):
                        for v in value:
                            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                                if v not in video_urls:
                                    video_urls.append(v)
                                    logger.debug(f"从字段 {field} 找到视频URL: {v}")
            # 递归查找嵌套结构
            for value in data.values():
                self._find_videos_recursive(value, video_urls, base64_videos, depth + 1)
    
    async def cleanup(self):
        """清理资源"""
        try:
            logger.info(f"{self.service_name}视频生成器资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


def create_video_api_app(generator: BaseVideoGenerator, title: str, description: str) -> FastAPI:
    """创建视频生成API应用"""
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """应用生命周期管理"""
        # 启动时执行
        logger.info(f"启动{generator.service_name}视频生成API服务（多实例模式）...")
        
        # 初始化生成器（不启动浏览器）
        if await generator.initialize():
            logger.success(f"{generator.service_name}生成器初始化完成")
        else:
            logger.error(f"{generator.service_name}生成器初始化失败")
        
        logger.info("浏览器实例管理:")
        logger.info("- 通过管理界面创建和管理浏览器实例")
        logger.info("- 视频生成任务的并发数 = 运行中的浏览器实例数")
        
        logger.success("API服务启动完成")
        
        yield
        
        # 关闭时执行
        logger.info(f"正在关闭{generator.service_name}视频生成API服务...")
        await generator.browser_manager.cleanup_all()
        logger.success("API服务已关闭")

    # FastAPI应用
    app = FastAPI(
        title=title,
        description=description,
        version="1.0.0",
        lifespan=lifespan
    )

    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": f"{generator.service_name} 视频生成API服务",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        """健康检查"""
        running_instances = generator.browser_manager.get_running_instances()
        available_instances = [i for i in running_instances if not i.is_busy]
        
        return {
            "status": "healthy",
            "generator_initialized": generator.is_initialized,
            "browser_instances": {
                "total": len(generator.browser_manager.instances),
                "running": len(running_instances),
                "available": len(available_instances),
                "busy": len(running_instances) - len(available_instances)
            },
            "concurrency_capacity": len(running_instances),
            "active_tasks": len(generator.active_tasks),
            "timestamp": datetime.now().isoformat(),
            "message": f"系统就绪，当前有 {len(running_instances)} 个浏览器实例运行中"
        }

    @app.post("/generate", response_model=VideoGenerationResponse)
    async def generate_video(request: VideoGenerationRequest):
        """生成视频接口"""
        try:
            logger.info(f"收到视频生成请求: {request.prompt[:50]}...")
            
            # 调用生成器
            result = await generator.generate_video(
                prompt=request.prompt,
                reference_images_b64=request.reference_images_b64
            )
            
            return VideoGenerationResponse(
                success=result["success"],
                task_id=result["task_id"],
                message=result["message"],
                generated_videos=result.get("generated_videos"),
                video_urls=result.get("video_urls"),
                ai_text_response=result.get("ai_text_response")
            )
            
        except Exception as e:
            logger.error(f"处理生成请求失败: {e}")
            raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

    @app.post("/generate-with-file")
    async def generate_video_with_file(
        prompt: str = Form(...),
        reference_images: Optional[List[UploadFile]] = File(None)
    ):
        """使用文件上传的视频生成接口（支持多个文件）"""
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
            result = await generator.generate_video(
                prompt=prompt,
                reference_images_b64=reference_images_b64
            )
            
            return VideoGenerationResponse(
                success=result["success"],
                task_id=result["task_id"],
                message=result["message"],
                generated_videos=result.get("generated_videos"),
                video_urls=result.get("video_urls"),
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
            "status": "completed" if task_id not in generator.active_tasks else "running",
            "message": "任务状态查询"
        }

    return app

