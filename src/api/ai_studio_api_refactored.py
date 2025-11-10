#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio 生图自动化API服务（重构版）
基于FastAPI封装，提供图片生成接口
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from loguru import logger
import uvicorn

from src.api.base_image_api import BaseImageGenerator, create_image_api_app
from src.core.service_browser_manager import ai_studio_browser_manager
from src.core.interactive_ai_studio import AIStudioInteractiveClient


class AIStudioImageGenerator(BaseImageGenerator):
    """AI Studio图片生成器"""
    
    def __init__(self):
        super().__init__("AI Studio", ai_studio_browser_manager)
    
    async def _generate_image_impl(self, client, prompt: str, reference_images_b64: Optional[List[str]], aspect_ratio: str, task_id: str) -> Dict[str, Any]:
        """AI Studio具体的图片生成实现"""
        try:
            # 确保页面处于生图初始状态
            logger.info("确保页面处于生图初始状态...")
            if not await client.navigate_to_new_image_chat(check_initial_page=False):
                logger.warning("刷新到生图页面失败，但继续执行")
            else:
                # 刷新后需要重新查找输入元素
                if not await client.find_input_elements():
                    logger.warning("刷新后查找输入元素失败")
            
            # 设置图片比例（如果需要）
            if aspect_ratio != "Auto":
                logger.info(f"设置图片比例为: {aspect_ratio}")
                if not await client.set_aspect_ratio(aspect_ratio):
                    logger.warning("设置图片比例失败，但继续执行")
            
            # 处理参考图片上传（支持单个或多个）
            images_to_upload = []
            if reference_images_b64:
                images_to_upload.extend(reference_images_b64)
            
            if images_to_upload:
                logger.info(f"检测到 {len(images_to_upload)} 张参考图片，开始上传...")
                if not await self._upload_reference_images(images_to_upload, client, task_id):
                    return {
                        "success": False,
                        "message": "参考图片上传失败"
                    }
            
            # 发送提示词
            logger.info("发送提示词到AI Studio...")
            if not await client.send_message(prompt):
                return {
                    "success": False,
                    "message": "发送提示词失败"
                }
            
            # 等待并解析响应
            logger.info("等待AI响应...")
            result = await self._wait_for_response(client, timeout=300)
            
            return result
            
        except Exception as e:
            logger.error(f"AI Studio生成图片时出错: {e}")
            return {
                "success": False,
                "message": f"生成图片时出错: {str(e)}"
            }
    
    async def _cleanup_after_task(self, client):
        """任务完成后的清理工作"""
        try:
            # AI Studio特定的清理逻辑
            await client.cleanup_after_task()
        except Exception as e:
            logger.warning(f"AI Studio任务清理失败: {e}")
    
    async def _upload_single_image(self, client, image_path: str) -> bool:
        """上传单个图片到AI Studio"""
        try:
            return await client.upload_image_and_text(image_path)
        except Exception as e:
            logger.error(f"上传图片到AI Studio失败: {e}")
            return False


# 全局生成器实例
generator = AIStudioImageGenerator()

# 创建FastAPI应用
app = create_image_api_app(
    generator=generator,
    title="AI Studio 图片生成API",
    description="基于Google AI Studio的图片生成自动化服务"
)


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭AI Studio服务...")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 配置日志
    logger.remove()
    logger.add(
        "data/logs/ai_studio_api_{time:YYYY-MM-DD}.log",
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
            "ai_studio_api_refactored:app",
            host="0.0.0.0",
            port=8812,
            reload=False,  # 关闭reload避免复杂的进程管理
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("AI Studio服务被用户中断")
    except Exception as e:
        logger.error(f"AI Studio服务运行失败: {e}")
    finally:
        logger.info("AI Studio服务已退出")
