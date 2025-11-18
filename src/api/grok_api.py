#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grok生图自动化API服务
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
from src.core.service_browser_manager import grok_browser_manager
from src.core.interactive_grok_image import GrokImageInteractiveClient


class GrokImageGenerator(BaseImageGenerator):
    """Grok图片生成器"""
    
    def __init__(self):
        super().__init__("grok", grok_browser_manager)
    
    async def _generate_image_impl(self, client, prompt: str, reference_images_b64: Optional[List[str]], aspect_ratio: str, task_id: str) -> Dict[str, Any]:
        """Grok具体的图片生成实现"""
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
            
            # 确保选择了图像生成技能
            if not await client.ensure_image_skill_ready():
                logger.warning("选择图像生成技能失败，但继续执行")
            
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
            logger.info("发送提示词到Grok...")
            if not await client.send_message(prompt):
                return {
                    "success": False,
                    "message": "发送提示词失败"
                }
            
            # 等待并解析响应 - Grok专用处理
            logger.info("等待Grok AI响应...")
            result = await self._wait_for_grok_response(client, timeout=300)
            
            return result
            
        except Exception as e:
            logger.error(f"Grok生成图片时出错: {e}")
            return {
                "success": False,
                "message": f"生成图片时出错: {str(e)}"
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
    
    async def _wait_for_grok_response(self, client, timeout: int = 300) -> Dict[str, Any]:
        """等待Grok AI响应并解析结果"""
        try:
            # 等待响应（默认最多5分钟）
            for i in range(timeout * 2):  # 每0.5秒检查一次
                if not client.waiting_for_response:
                    break
                await asyncio.sleep(0.5)
            
            if client.waiting_for_response:
                return {
                    "success": False,
                    "message": "等待Grok AI响应超时"
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
            logger.error(f"等待Grok响应时出错: {e}")
            return {
                "success": False,
                "message": f"等待Grok响应时出错: {str(e)}"
            }
    
    async def _parse_grok_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析Grok响应，提取图片URL并转换为base64"""
        try:
            logger.info("开始解析Grok生成响应...")
            
            # 提取文本回复
            ai_text = api_response.get("text", "")
            
            # 提取图片URL
            image_urls = api_response.get("images", [])
            
            if not image_urls and not ai_text:
                return {
                    "success": False,
                    "message": "Grok响应中没有图片或文本内容"
                }
            
            # 下载图片并转换为base64
            generated_images = []
            if image_urls:
                logger.info(f"Grok生成了 {len(image_urls)} 张图片，开始下载转换...")
                base64_images = await self._download_and_convert_images(image_urls)
                if base64_images:
                    generated_images = base64_images
                    logger.success(f"成功转换 {len(base64_images)} 张图片为base64")
                else:
                    logger.error("图片下载转换失败")
                    return {
                        "success": False,
                        "message": "图片下载转换失败"
                    }
            
            return {
                "success": True,
                "message": "Grok图片生成成功",
                "generated_images": generated_images,
                "ai_text_response": ai_text
            }
            
        except Exception as e:
            logger.error(f"解析Grok生成响应失败: {e}")
            return {
                "success": False,
                "message": f"解析Grok响应失败: {str(e)}"
            }
    
    async def _download_and_convert_images(self, image_urls: List[str]) -> List[str]:
        """下载图片并转换为base64 - 使用requests库提高成功率"""
        import requests
        import base64
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        base64_images = []
        
        # 构建完整的请求头，模拟真实浏览器
        headers = {
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Referer': 'https://grok.com/'
        }
        
        def download_single_image(url, index):
            """下载单个图片的同步函数"""
            success = False
            last_error = None
            
            # 重试机制：最多重试3次
            for retry_count in range(3):
                try:
                    if retry_count > 0:
                        # 重试前等待，避免频繁请求
                        wait_time = retry_count * 2  # 2秒, 4秒
                        logger.info(f"第 {retry_count + 1} 次重试下载第 {index+1} 张图片，等待 {wait_time} 秒...")
                        import time
                        time.sleep(wait_time)
                    else:
                        logger.info(f"下载第 {index+1}/{len(image_urls)} 张图片: {url}")
                    
                    # 使用requests下载（测试证明100%成功率）
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        # 转换为base64
                        base64_data = base64.b64encode(response.content).decode('utf-8')
                        logger.success(f"第 {index+1} 张图片下载转换成功")
                        return base64_data
                    else:
                        last_error = f"状态码: {response.status_code}"
                        if retry_count < 2:  # 不是最后一次重试
                            logger.warning(f"下载第 {index+1} 张图片失败，{last_error}，准备重试...")
                        else:
                            logger.error(f"下载第 {index+1} 张图片失败，{last_error}，已达到最大重试次数")
                            
                except Exception as e:
                    last_error = str(e)
                    if retry_count < 2:  # 不是最后一次重试
                        logger.warning(f"下载第 {index+1} 张图片时出错: {e}，准备重试...")
                    else:
                        logger.error(f"下载第 {index+1} 张图片时出错: {e}，已达到最大重试次数")
            
            logger.error(f"第 {index+1} 张图片下载失败，最终错误: {last_error}")
            return None
        
        # 使用线程池并发下载图片
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 提交所有下载任务
            future_to_index = {
                executor.submit(download_single_image, url, i): i 
                for i, url in enumerate(image_urls)
            }
            
            # 等待所有任务完成
            for future in future_to_index:
                try:
                    result = future.result()
                    if result:
                        base64_images.append(result)
                except Exception as e:
                    logger.error(f"下载任务执行失败: {e}")
        
        return base64_images


# 全局生成器实例
generator = GrokImageGenerator()

# 创建FastAPI应用
app = create_image_api_app(
    generator=generator,
    title="Grok 图片生成API",
    description="基于Grok的图片生成自动化服务"
)


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭Grok服务...")
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
        logger.info("Grok服务被用户中断")
    except Exception as e:
        logger.error(f"Grok服务运行失败: {e}")
    finally:
        logger.info("Grok服务已退出")
