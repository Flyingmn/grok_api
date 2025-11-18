#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grok视频生成自动化API服务
基于FastAPI封装，提供视频生成接口
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from loguru import logger
import uvicorn

from src.api.base_video_api import BaseVideoGenerator, create_video_api_app
from src.core.service_browser_manager import grok_browser_manager
from src.core.interactive_grok_video import GrokVideoInteractiveClient


class GrokVideoGenerator(BaseVideoGenerator):
    """Grok视频生成器"""
    
    def __init__(self):
        super().__init__("grok", grok_browser_manager)
    
    async def _generate_video_impl(self, client, prompt: str, reference_images_b64: Optional[List[str]], task_id: str) -> Dict[str, Any]:
        """Grok具体的视频生成实现"""
        try:
            # 检查是否需要导航到Grok页面
            current_url = client.instance.page.url if client.instance and client.instance.page else ""
            logger.info(f"当前页面URL: {current_url}")
            
            if "https://grok.com" not in current_url:
                logger.info("当前不在Grok聊天页面，开始导航...")
                if not await client.navigate_to_grok():
                    logger.warning("导航到Grok页面失败，但继续执行")
            else:
                logger.info("已在Grok聊天页面，跳过导航")
            
            # 确保视频生成功能就绪
            if not await client.ensure_video_skill_ready():
                logger.warning("视频生成功能准备失败，但继续执行")
            
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
            logger.info("发送提示词到Grok...")
            if not await client.send_message(prompt):
                return {
                    "success": False,
                    "message": "发送提示词失败"
                }
            
            # 等待并解析响应 - Grok视频生成专用处理
            logger.info("等待Grok AI视频生成响应...")
            result = await self._wait_for_grok_response(client, timeout=600)  # 视频生成可能需要更长时间
            
            return result
            
        except Exception as e:
            logger.error(f"Grok生成视频时出错: {e}")
            return {
                "success": False,
                "message": f"生成视频时出错: {str(e)}"
            }
    
    async def _cleanup_after_task(self, client):
        """任务完成后的清理工作"""
        try:
            # Grok特定的清理逻辑
            # Grok客户端暂时没有特定的清理方法，可以在这里添加
            logger.info("Grok任务清理完成")
        except Exception as e:
            logger.warning(f"Grok任务清理失败: {e}")
    
    async def _upload_single_image(self, client, image_path: str) -> bool:
        """上传单个图片到Grok"""
        try:
            return await client.upload_reference_image(image_path)
        except Exception as e:
            logger.error(f"上传图片到Grok失败: {e}")
            return False
    
    async def _wait_for_grok_response(self, client, timeout: int = 600) -> Dict[str, Any]:
        """等待Grok AI视频生成响应并解析结果（视频生成需要更长时间）"""
        try:
            # 等待响应（默认最多10分钟，视频生成通常比图片生成需要更长时间）
            for i in range(timeout * 2):  # 每0.5秒检查一次
                if not client.waiting_for_response:
                    break
                await asyncio.sleep(0.5)
            
            if client.waiting_for_response:
                return {
                    "success": False,
                    "message": "等待Grok AI视频生成响应超时"
                }
            
            # 解析最新的API响应
            if not client.api_responses:
                return {
                    "success": False,
                    "message": "未收到Grok API响应"
                }
            
            latest_response = client.api_responses[-1]
            return await self._parse_grok_response(latest_response)
            
        except Exception as e:
            logger.error(f"等待Grok视频生成响应时出错: {e}")
            return {
                "success": False,
                "message": f"等待Grok响应时出错: {str(e)}"
            }
    
    async def _parse_grok_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析Grok响应，提取视频URL（支持SSE流和JSON响应）"""
        try:
            logger.info("开始解析Grok视频生成响应...")
            
            # 提取文本回复
            response_data = api_response.get("data", {})
            ai_text = ""
            
            # 优先从响应的text字段获取（SSE流中提取的）
            if "text" in api_response:
                ai_text = api_response["text"]
            elif response_data:
                ai_text = self._extract_ai_response(response_data) if response_data else ""
            
            # 提取视频URL或视频数据
            video_urls = []
            base64_videos = []
            
            # 优先从响应的video_urls和videos字段获取（SSE流中提取的）
            if "video_urls" in api_response and isinstance(api_response["video_urls"], list):
                video_urls.extend(api_response["video_urls"])
                logger.info(f"从响应中提取到 {len(api_response['video_urls'])} 个视频URL")
            
            if "videos" in api_response and isinstance(api_response["videos"], list):
                base64_videos.extend(api_response["videos"])
                logger.info(f"从响应中提取到 {len(api_response['videos'])} 个base64视频")
            
            # 从响应数据中提取视频信息（JSON响应）
            if response_data:
                base64_vids, urls = self._extract_videos_from_response(response_data)
                video_urls.extend(urls)
                base64_videos.extend(base64_vids)
            
            # 也检查响应中的其他字段
            if "video" in api_response:
                video = api_response["video"]
                if isinstance(video, str):
                    if video.startswith("http://") or video.startswith("https://"):
                        if video not in video_urls:
                            video_urls.append(video)
                elif isinstance(video, list):
                    for v in video:
                        if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                            if v not in video_urls:
                                video_urls.append(v)
            
            if "video_url" in api_response:
                video_url = api_response["video_url"]
                if isinstance(video_url, str) and (video_url.startswith("http://") or video_url.startswith("https://")):
                    if video_url not in video_urls:
                        video_urls.append(video_url)
            
            # 去重
            video_urls = list(dict.fromkeys(video_urls))  # 保持顺序的去重
            base64_videos = list(dict.fromkeys(base64_videos))
            
            if not video_urls and not base64_videos and not ai_text:
                return {
                    "success": False,
                    "message": "Grok响应中没有视频或文本内容"
                }
            
            logger.success(f"Grok生成了 {len(video_urls)} 个视频URL, {len(base64_videos)} 个base64视频")
            
            return {
                "success": True,
                "message": "Grok视频生成成功",
                "generated_videos": base64_videos,
                "video_urls": video_urls,
                "ai_text_response": ai_text
            }
            
        except Exception as e:
            logger.error(f"解析Grok视频生成响应失败: {e}")
            return {
                "success": False,
                "message": f"解析Grok响应失败: {str(e)}"
            }
    


# 全局生成器实例
generator = GrokVideoGenerator()

# 创建FastAPI应用
app = create_video_api_app(
    generator=generator,
    title="Grok 视频生成API",
    description="基于Grok的视频生成自动化服务"
)


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭Grok视频服务...")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 配置日志
    logger.remove()
    logger.add(
        "data/logs/grok_api_{time:YYYY-MM-DD}.log",
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
            "grok_api:app",
            host="0.0.0.0",
            port=8816,  # 使用不同的端口避免冲突
            reload=False,  # 关闭reload避免复杂的进程管理
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Grok视频服务被用户中断")
    except Exception as e:
        logger.error(f"Grok视频服务运行失败: {e}")
    finally:
        logger.info("Grok视频服务已退出")
