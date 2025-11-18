#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grok视频生成交互客户端
用于与Grok视频生成页面交互，发送提示词并获取生成的视频
"""

import asyncio
import json
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
from .crawler_framework import CrawlerFramework, CrawlerConfig
import sys


class GrokVideoInteractiveClient:
    """Grok视频生成交互客户端类"""
    
    def __init__(self):
        self.framework = CrawlerFramework()
        self.instance_id = "grok_video_interactive"
        self.instance = None
        self.api_responses = []
        self.waiting_for_response = False
        
        # DOM选择器 - 基于Grok视频生成的DOM结构
        # 注意：这些选择器需要根据实际页面结构调整
        self.selectors = {
            # 登录检测相关
            "login_modal": '[data-testid="login"]',
            "login_button": 'button:has-text("Sign in")',
            
            # 输入框相关
            "input_container": 'textarea[placeholder*="prompt"], textarea[placeholder*="message"]',
            "text_input": 'textarea[data-testid="composer-text-input"], textarea[role="textbox"]',
            "send_button": 'button[data-testid="send-button"], button[aria-label*="Send"]',
            
            # 视频生成相关
            "video_generation_button": 'button:has-text("Generate"), button[data-testid="generate-video"]',
            "video_settings": '[data-testid="video-settings"]',
            
            # 文件上传
            "file_input": 'input[type="file"]',
        }
    
    async def setup(self):
        """初始化设置"""
        try:
            logger.info("初始化Grok视频生成交互客户端...")
            
            # 创建配置
            config = CrawlerConfig()
            config.headless = False  # 显示浏览器窗口
            config.timeout = 30000
            
            # 创建实例
            self.instance = self.framework.create_instance(self.instance_id, config)
            await self.instance.start()
            
            # 设置网络监听
            await self.setup_network_listener()
            
            # 加载已保存的cookies
            await self.load_cookies()
            
            logger.success("初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def load_cookies(self):
        """加载保存的cookies"""
        try:
            # 使用实例ID作为cookies文件名
            cookies_file = Path("data/cookies") / f"{self.instance_id}_session.json"
            if cookies_file.exists():
                logger.info(f"发现已保存的登录状态，正在加载... ({self.instance_id})")
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.instance.context.add_cookies(cookies)
                logger.success(f"登录状态加载成功 ({self.instance_id})")
            else:
                logger.info(f"未找到保存的登录状态 ({self.instance_id})")
        except Exception as e:
            logger.warning(f"加载登录状态失败 ({self.instance_id}): {e}")
    
    async def save_cookies(self):
        """保存当前cookies"""
        try:
            cookies_dir = Path("data/cookies")
            cookies_dir.mkdir(exist_ok=True)
            
            cookies = await self.instance.context.cookies()
            # 使用实例ID作为cookies文件名
            cookies_file = cookies_dir / f"{self.instance_id}_session.json"
            
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            logger.success(f"登录状态已保存到: {cookies_file}")
        except Exception as e:
            logger.error(f"保存登录状态失败: {e}")
    
    async def navigate_to_grok(self):
        """导航到Grok页面"""
        try:
            logger.info("正在访问Grok页面...")
            
            # 导航到Grok主页
            try:
                await self.instance.page.goto("https://grok.com/", 
                                            wait_until="domcontentloaded", 
                                            timeout=15000)
                logger.success("页面导航成功")
            except Exception as nav_e:
                logger.warning(f"导航可能超时，检查页面状态: {nav_e}")
                
                # 检查页面是否实际已经加载
                try:
                    current_url = self.instance.page.url
                    if "grok.com" in current_url:
                        logger.info(f"页面已加载，当前URL: {current_url}")
                    else:
                        # 如果URL不对，再尝试一次
                        logger.info("尝试重新导航...")
                        await self.instance.page.goto("https://grok.com/", 
                                                    wait_until="load", 
                                                    timeout=10000)
                except Exception as retry_e:
                    logger.error(f"重试导航失败: {retry_e}")
                    return False
            
            # 等待页面稳定
            await asyncio.sleep(3)
            
            # 检查页面是否可用
            try:
                # 尝试查找页面的基本元素
                await self.instance.page.wait_for_selector('body', timeout=5000)
                logger.success("页面基本元素已加载")
            except Exception as e:
                logger.warning(f"等待页面元素超时，但继续执行: {e}")
            
            # 尝试截图
            try:
                await self.instance.screenshot("grok_home.png")
            except Exception as e:
                logger.warning(f"截图失败，跳过: {e}")
            
            logger.success("成功访问Grok页面")
            return True
            
        except Exception as e:
            logger.error(f"访问Grok页面失败: {e}")
            return False
    
    async def check_login_required(self):
        """检测是否出现登录弹窗"""
        try:
            # 检查登录弹窗是否存在
            login_modal = await self.instance.page.query_selector(self.selectors["login_modal"])
            if login_modal and await login_modal.is_visible():
                logger.error("检测到登录弹窗，需要用户登录")
                return True
            
            # 检查登录按钮
            login_button = await self.instance.page.query_selector(self.selectors["login_button"])
            if login_button and await login_button.is_visible():
                logger.error("检测到登录按钮，需要用户登录")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"检测登录状态失败: {e}")
            return False
    
    async def ensure_video_skill_ready(self):
        """确保视频生成功能已准备就绪"""
        try:
            logger.info("确保视频生成功能已准备就绪...")
            
            # 检查是否在正确的页面
            current_url = self.instance.page.url
            if "grok.com" not in current_url:
                logger.warning("不在Grok页面，尝试导航...")
                if not await self.navigate_to_grok():
                    return False
            
            # 等待页面加载完成
            await asyncio.sleep(2)
            
            # 查找输入框
            text_input = await self.instance.page.query_selector(self.selectors["text_input"])
            if not text_input:
                # 尝试备用选择器
                text_input = await self.instance.page.query_selector('textarea')
            
            if text_input and await text_input.is_visible():
                logger.success("视频生成功能已就绪")
                return True
            else:
                logger.warning("未找到输入框，但继续执行")
                return True  # 即使找不到也继续，可能页面结构不同
                
        except Exception as e:
            logger.error(f"确保视频生成功能就绪失败: {e}")
            return False
    
    async def upload_reference_image(self, image_path: str) -> bool:
        """上传参考图片"""
        try:
            logger.info(f"开始上传参考图片: {image_path}")
            
            # 检查图片文件是否存在
            image_file = Path(image_path)
            if not image_file.exists():
                logger.error(f"未找到图片文件: {image_path}")
                return False
            
            # 确保视频生成功能已准备就绪
            if not await self.ensure_video_skill_ready():
                logger.warning("视频生成功能未就绪，但继续尝试上传")
            
            # 等待一下让界面稳定
            await asyncio.sleep(1)
            
            # 方法1：直接查找页面中的文件输入元素
            try:
                file_input = await self.instance.page.query_selector(self.selectors["file_input"])
                if file_input:
                    logger.info("找到文件输入元素，开始上传...")
                    await file_input.set_input_files(str(image_file.resolve()))
                    await asyncio.sleep(2)
                    logger.success("参考图片上传成功")
                    return True
            except Exception as direct_e:
                logger.warning(f"直接方法失败: {direct_e}")
            
            # 方法2：尝试查找所有文件输入元素
            try:
                file_inputs = await self.instance.page.query_selector_all('input[type="file"]')
                if file_inputs:
                    logger.info(f"找到 {len(file_inputs)} 个文件输入元素，使用第一个")
                    await file_inputs[0].set_input_files(str(image_file.resolve()))
                    await asyncio.sleep(2)
                    logger.success("参考图片上传成功（备用方法）")
                    return True
            except Exception as backup_e:
                logger.warning(f"备用方法失败: {backup_e}")
            
            logger.warning("未能找到文件输入元素，图片上传可能失败")
            return False
            
        except Exception as e:
            logger.error(f"上传参考图片失败: {e}")
            return False
    
    async def send_message(self, message: str):
        """发送消息"""
        try:
            logger.info(f"正在发送消息: {message}")
            
            # 确保视频生成功能已准备就绪
            if not await self.ensure_video_skill_ready():
                logger.error("视频生成功能未就绪")
                return False
            
            # 清空之前的响应
            self.api_responses.clear()
            
            # 查找输入框
            text_input = await self.instance.page.query_selector(self.selectors["text_input"])
            if not text_input:
                text_input = await self.instance.page.query_selector('textarea')
            
            if text_input and await text_input.is_visible():
                # 点击输入框获得焦点
                await text_input.click()
                await asyncio.sleep(0.5)
                
                # 清空输入框
                await text_input.fill("")
                await asyncio.sleep(0.3)
                
                # 输入消息
                await text_input.fill(message)
                await asyncio.sleep(1)
                
                logger.success(f"文本已填充到输入框")
                
                # 查找发送按钮
                send_button = await self.instance.page.query_selector(self.selectors["send_button"])
                if not send_button:
                    # 尝试通过Enter键发送
                    await text_input.press("Enter")
                    logger.info("使用Enter键发送消息")
                else:
                    await send_button.click()
                    logger.info("点击发送按钮")
                
                # 设置等待响应标志
                self.waiting_for_response = True
                
                # 等待一下让请求发送
                await asyncio.sleep(2)
                
                logger.success("消息已发送")
                return True
            else:
                logger.error("未找到输入框")
                return False
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.waiting_for_response = False
            return False
    
    async def setup_network_listener(self):
        """设置网络监听器，监听API请求和响应（模仿doubao方案）"""
        try:
            logger.info("设置Grok视频生成网络监听器...")
            
            # 监听网络响应 - 监听Grok视频生成API
            async def handle_response(response):
                """处理网络响应"""
                try:
                    url = response.url
                    
                    # 监听Grok的API响应
                    if "grok.com" in url and ("api" in url.lower() or "generate" in url.lower() or "video" in url.lower() or "chat" in url.lower()):
                        logger.info(f"检测到Grok API响应: {url}")
                        await self.handle_api_response(response)
                        
                except Exception as e:
                    logger.debug(f"处理响应时出错: {e}")
            
            # 监听网络请求 - 监听Grok视频生成API请求
            async def handle_request(request):
                """处理网络请求"""
                try:
                    url = request.url
                    
                    # 监听Grok视频生成API请求
                    if "grok.com" in url and ("api" in url.lower() or "generate" in url.lower() or "video" in url.lower() or "chat" in url.lower()):
                        logger.info(f"检测到Grok API请求: {url}")
                        try:
                            # 获取请求数据
                            post_data = request.post_data
                            if post_data:
                                logger.info("Grok视频生成请求数据已发送")
                                self.waiting_for_response = True
                                
                                # 解析请求数据以获取提示词
                                try:
                                    request_data = json.loads(post_data)
                                    # 尝试提取提示词
                                    if isinstance(request_data, dict):
                                        # 查找常见的提示词字段
                                        prompt_fields = ["prompt", "message", "text", "content", "input"]
                                        for field in prompt_fields:
                                            if field in request_data:
                                                prompt = request_data[field]
                                                if isinstance(prompt, str) and prompt.strip():
                                                    logger.info(f"📝 发送的提示词: {prompt[:100]}...")
                                                    break
                                        # 如果是消息数组结构
                                        if "messages" in request_data and isinstance(request_data["messages"], list):
                                            for msg in request_data["messages"]:
                                                if isinstance(msg, dict) and "content" in msg:
                                                    content = msg["content"]
                                                    if isinstance(content, str):
                                                        logger.info(f"📝 发送的提示词: {content[:100]}...")
                                                        break
                                except Exception as parse_e:
                                    logger.debug(f"解析请求数据失败: {parse_e}")
                        except Exception as e:
                            logger.debug(f"处理Grok API请求时出错: {e}")
                            
                except Exception as e:
                    logger.debug(f"处理请求时出错: {e}")
            
            # 绑定事件监听器
            self.instance.page.on("response", handle_response)
            self.instance.page.on("request", handle_request)
            
            logger.success("Grok视频生成网络监听器设置完成")
            
        except Exception as e:
            logger.error(f"设置网络监听器失败: {e}")
    
    async def handle_api_response(self, response):
        """处理API响应"""
        try:
            url = response.url
            status = response.status
            
            if status != 200:
                logger.debug(f"收到非200响应: {url} (状态: {status})")
                return
            
            # 尝试解析响应
            try:
                response_data = await response.json()
                logger.info(f"收到JSON响应: {url}")
                
                # 保存响应
                self.api_responses.append({
                    "url": url,
                    "status": status,
                    "data": response_data,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # 检查是否包含视频信息
                if self._extract_video_info(response_data):
                    self.waiting_for_response = False
                    logger.success("检测到视频生成完成")
                    
            except Exception as json_error:
                # 如果不是JSON，可能是SSE流
                try:
                    content_type = response.headers.get("content-type", "")
                    if "text/event-stream" in content_type or "text/plain" in content_type:
                        logger.info("检测到SSE流响应，开始实时解析...")
                        await self.handle_sse_stream(response)
                    else:
                        # 尝试读取文本
                        text = await response.text()
                        if text:
                            logger.info("收到文本响应，尝试解析...")
                            # 检查是否是SSE格式
                            if "data: " in text:
                                await self.handle_sse_stream(response, text)
                except Exception as text_error:
                    logger.debug(f"解析响应失败: {json_error}, {text_error}")
                    
        except Exception as e:
            logger.error(f"处理API响应失败: {e}")
    
    def _extract_video_info(self, data: Dict[str, Any]) -> bool:
        """从响应数据中提取视频信息"""
        try:
            # 根据Grok的响应结构提取视频URL
            # 这里需要根据实际API响应结构调整
            if isinstance(data, dict):
                # 查找常见的视频字段
                video_fields = ["video", "video_url", "videoUrl", "url", "output", "result"]
                
                for field in video_fields:
                    if field in data:
                        value = data[field]
                        if isinstance(value, str) and ("http" in value or ".mp4" in value or ".webm" in value):
                            logger.success(f"找到视频URL: {value}")
                            return True
                        elif isinstance(value, dict):
                            if self._extract_video_info(value):
                                return True
                
                # 递归查找嵌套结构
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        if self._extract_video_info(value if isinstance(value, dict) else {"items": value}):
                            return True
            
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and self._extract_video_info(item):
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"提取视频信息失败: {e}")
            return False
    
    async def handle_sse_stream(self, response, text: str = None):
        """处理SSE流响应 - 读取完整响应数据（模仿doubao方案）"""
        try:
            logger.info("开始处理Grok视频生成SSE流...")
            
            found_videos = []
            video_urls = []
            collected_text = []  # 收集文本内容
            
            # 如果没有提供text，从response读取
            if text is None:
                try:
                    response_text = await response.text()
                except Exception as e:
                    logger.warning(f"无法读取响应文本: {e}")
                    response_text = ""
            else:
                response_text = text
            
            logger.info(f"收到SSE响应，长度: {len(response_text)}")
            
            # 按照SSE格式解析事件
            events = response_text.split('\n\n')
            logger.info(f"拆分出 {len(events)} 个事件")
            
            for i, event in enumerate(events):
                if not event.strip():
                    continue
                
                # 检查是否是错误事件
                if 'event: error' in event or 'event: gateway-error' in event:
                    error_match = event.split('data: ')
                    if len(error_match) > 1:
                        try:
                            error_data = json.loads(error_match[1].split('\n')[0])
                            logger.error(f"服务器错误: {error_data}")
                            print(f"\n❌ 服务器返回错误: {error_data.get('message', '未知错误')}")
                            return
                        except:
                            print(f"\n❌ 服务器返回错误")
                            return
                
                # 查找data行
                lines = event.strip().split('\n')
                data_line = None
                for line in lines:
                    if line.startswith('data: '):
                        data_line = line[6:]  # 去掉"data: "前缀
                        break
                
                if not data_line:
                    continue
                
                try:
                    # 解析事件数据
                    event_data = json.loads(data_line)
                    
                    # 提取文本内容
                    text_content = self._extract_text_from_event(event_data)
                    if text_content:
                        collected_text.append(text_content)
                        logger.debug(f"提取到文本: {text_content[:50]}...")
                    
                    # 提取视频信息
                    video_info = self._extract_video_from_event(event_data)
                    if video_info:
                        if isinstance(video_info, str):
                            if video_info.startswith("http://") or video_info.startswith("https://"):
                                if video_info not in video_urls:
                                    video_urls.append(video_info)
                                    logger.success(f"✅ 找到视频URL: {video_info}")
                            else:
                                # 可能是base64编码的视频
                                found_videos.append(video_info)
                                logger.success("✅ 找到base64视频数据")
                        elif isinstance(video_info, list):
                            for v in video_info:
                                if isinstance(v, str):
                                    if v.startswith("http://") or v.startswith("https://"):
                                        if v not in video_urls:
                                            video_urls.append(v)
                                            logger.success(f"✅ 找到视频URL: {v}")
                                    else:
                                        found_videos.append(v)
                    
                    # 检查是否包含视频信息（完成标志）
                    if self._extract_video_info(event_data):
                        logger.info("检测到视频生成完成标志")
                        # 不立即break，继续处理其他事件以获取完整信息
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"解析事件失败: {e}")
                    continue
            
            # 显示收集到的文本内容
            if collected_text:
                full_text = "".join(collected_text)
                logger.info(f"🤖 Grok回复: {full_text[:100]}...")
            
            # 显示找到的视频
            if video_urls or found_videos:
                logger.success(f"📹 Grok生成了 {len(video_urls)} 个视频URL, {len(found_videos)} 个base64视频")
                
                # 保存视频信息到响应
                self.api_responses.append({
                    "url": response.url,
                    "status": response.status,
                    "video_urls": video_urls,
                    "videos": found_videos,
                    "text": "".join(collected_text) if collected_text else "",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                self.waiting_for_response = False
                logger.success("视频生成完成")
            elif collected_text:
                # 只有文本，没有视频
                self.api_responses.append({
                    "url": response.url,
                    "status": response.status,
                    "text": "".join(collected_text),
                    "timestamp": asyncio.get_event_loop().time()
                })
                logger.warning("收到文本回复，但没有视频")
            else:
                logger.warning("未从SSE流中提取到内容")
                    
        except Exception as e:
            logger.error(f"处理SSE流失败: {e}")
            print(f"\n❌ 处理Grok SSE流失败: {e}")
    
    def _extract_text_from_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """从事件数据中提取文本内容"""
        try:
            if isinstance(event_data, dict):
                # 查找常见的文本字段
                text_fields = ["text", "content", "message", "reply", "answer", "output"]
                for field in text_fields:
                    if field in event_data:
                        value = event_data[field]
                        if isinstance(value, str) and value.strip():
                            return value.strip()
                        elif isinstance(value, dict):
                            # 递归查找
                            text = self._extract_text_from_event(value)
                            if text:
                                return text
                
                # 查找嵌套结构
                if "data" in event_data:
                    text = self._extract_text_from_event(event_data["data"])
                    if text:
                        return text
                
                # 查找消息数组
                if "messages" in event_data and isinstance(event_data["messages"], list):
                    texts = []
                    for msg in event_data["messages"]:
                        if isinstance(msg, dict):
                            text = self._extract_text_from_event(msg)
                            if text:
                                texts.append(text)
                    if texts:
                        return "".join(texts)
            
            elif isinstance(event_data, list):
                texts = []
                for item in event_data:
                    text = self._extract_text_from_event(item)
                    if text:
                        texts.append(text)
                if texts:
                    return "".join(texts)
            
            return None
        except Exception as e:
            logger.debug(f"提取文本失败: {e}")
            return None
    
    def _extract_video_from_event(self, event_data: Dict[str, Any]) -> Optional[Any]:
        """从事件数据中提取视频信息"""
        try:
            if isinstance(event_data, dict):
                # 查找常见的视频字段
                video_fields = ["video", "video_url", "videoUrl", "url", "output", "result", "video_urls", "videos"]
                for field in video_fields:
                    if field in event_data:
                        value = event_data[field]
                        if isinstance(value, str):
                            if "http" in value or ".mp4" in value or ".webm" in value or ".mov" in value:
                                return value
                        elif isinstance(value, list):
                            videos = []
                            for v in value:
                                if isinstance(v, str) and ("http" in v or ".mp4" in v or ".webm" in v or ".mov" in v):
                                    videos.append(v)
                            if videos:
                                return videos
                        elif isinstance(value, dict):
                            # 递归查找
                            video = self._extract_video_from_event(value)
                            if video:
                                return video
                
                # 查找嵌套结构
                if "data" in event_data:
                    video = self._extract_video_from_event(event_data["data"])
                    if video:
                        return video
            
            elif isinstance(event_data, list):
                for item in event_data:
                    video = self._extract_video_from_event(item)
                    if video:
                        return video
            
            return None
        except Exception as e:
            logger.debug(f"提取视频失败: {e}")
            return None
    
    async def cleanup(self):
        """清理资源"""
        try:
            logger.info("清理Grok视频生成客户端资源...")
            
            if self.instance:
                await self.instance.stop()
                self.instance = None
            
            logger.success("资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    async def run_interactive_session(self):
        """运行交互会话"""
        try:
            logger.info("启动Grok视频生成交互会话...")
            
            # 初始化
            if not await self.setup():
                logger.error("初始化失败")
                return
            
            # 导航到Grok
            if not await self.navigate_to_grok():
                logger.error("导航到Grok失败")
                return
            
            # 检查登录状态
            if await self.check_login_required():
                logger.warning("需要登录，请手动登录后继续")
                input("按Enter键继续（确保已登录）...")
            
            print("\n" + "=" * 50)
            print("🎬 Grok视频生成交互会话已启动")
            print("=" * 50)
            print("提示：")
            print("  - 输入提示词生成视频")
            print("  - 输入 'quit' 或 'exit' 退出")
            print("  - 输入 'screenshot' 截图")
            print("  - 输入 'save' 保存登录状态")
            print("=" * 50)
            
            # 开始交互循环
            while True:
                try:
                    # 获取用户输入
                    user_input = input("\n👤 请输入提示词: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # 检查退出命令
                    if user_input.lower() in ['quit', 'exit', '退出']:
                        print("💾 正在保存登录状态...")
                        await self.save_cookies()
                        print("👋 再见！")
                        break
                    
                    # 检查截图命令
                    if user_input.lower() == 'screenshot':
                        screenshot_path = await self.instance.screenshot()
                        print(f"📸 截图已保存: {screenshot_path}")
                        continue
                    
                    # 检查保存登录状态命令
                    if user_input.lower() in ['save', '保存']:
                        await self.save_cookies()
                        print("💾 登录状态已保存")
                        continue
                    
                    # 发送消息
                    if await self.send_message(user_input):
                        print("✅ 消息已发送，等待响应...")
                        
                        # 等待响应（最多5分钟）
                        for i in range(300):
                            if not self.waiting_for_response:
                                break
                            await asyncio.sleep(1)
                        
                        if self.api_responses:
                            print(f"📹 收到 {len(self.api_responses)} 个响应")
                            for i, resp in enumerate(self.api_responses, 1):
                                print(f"  响应 {i}: {resp.get('url', 'N/A')}")
                        else:
                            print("⚠️  未收到响应")
                    else:
                        print("❌ 发送消息失败")
                    
                except KeyboardInterrupt:
                    print("\n\n👋 会话被中断")
                    break
                except Exception as e:
                    logger.error(f"交互循环出错: {e}")
                    print(f"❌ 出错: {e}")
            
        except Exception as e:
            logger.error(f"交互会话失败: {e}")
        finally:
            await self.cleanup()


if __name__ == "__main__":
    client = GrokVideoInteractiveClient()
    asyncio.run(client.run_interactive_session())

