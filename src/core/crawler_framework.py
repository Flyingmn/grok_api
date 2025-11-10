#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Camoufox和Playwright的爬虫框架
支持多实例、多进程、异步操作
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
# 使用Camoufox启动浏览器
from camoufox import AsyncNewBrowser


class CrawlerConfig:
    """爬虫配置类"""
    
    def __init__(self):
        self.headless = False  # 默认有头模式，方便调试
        self.timeout = 30000  # 30秒超时
        self.viewport = None  # 使用浏览器默认尺寸，不强制设置
        self.user_agent = None  # 使用Camoufox默认UA
        self.proxy = None
        self.user_data_dir = None  # 用户数据目录，用于持久化
        self.screenshot_on_error = True
        self.max_retries = 3
        self.retry_delay = 2
    
    def set_viewport(self, width: int, height: int):
        """设置浏览器视窗大小"""
        self.viewport = {"width": width, "height": height}
    
    def set_mobile_viewport(self):
        """设置移动端视窗"""
        self.viewport = {"width": 375, "height": 667}  # iPhone SE
    
    def set_tablet_viewport(self):
        """设置平板视窗"""
        self.viewport = {"width": 768, "height": 1024}  # iPad
    
    def set_desktop_viewport(self):
        """设置桌面视窗"""
        self.viewport = {"width": 1280, "height": 720}  # 标准桌面
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "headless": self.headless,
            "timeout": self.timeout,
            "viewport": self.viewport,
            "user_agent": self.user_agent,
            "proxy": self.proxy,
            "user_data_dir": self.user_data_dir,
            "screenshot_on_error": self.screenshot_on_error,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }


class CrawlerInstance:
    """单个爬虫实例"""
    
    def __init__(self, instance_id: str, config: CrawlerConfig):
        self.instance_id = instance_id
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.is_running = False
        
    async def start(self):
        """启动爬虫实例"""
        try:
            logger.info(f"启动爬虫实例 {self.instance_id}")
            
            # 启动Playwright
            self.playwright = await async_playwright().start()
            
            
            self.browser = await AsyncNewBrowser(
                self.playwright,
                headless=self.config.headless,
                # 添加字符编码相关参数
                args=[
                    '--lang=zh-CN',
                    '--accept-lang=zh-CN,zh;q=0.9,en;q=0.8',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # 创建浏览器上下文
            context_options = {
                "ignore_https_errors": True,
                # 设置语言和编码
                "locale": "zh-CN",
                "extra_http_headers": {
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Charset": "utf-8"
                }
            }
            
            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent
                
            if self.config.proxy:
                context_options["proxy"] = self.config.proxy
                
            self.context = await self.browser.new_context(**context_options)
            
            # 设置默认超时
            self.context.set_default_timeout(self.config.timeout)
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 直接在页面上设置viewport，这种方式更可靠
            if self.config.viewport:
                try:
                    await self.page.set_viewport_size(self.config.viewport)
                    logger.info(f"成功设置页面Viewport: {self.config.viewport}")
                except Exception as e:
                    logger.error(f"设置页面Viewport失败: {e}")
            
            self.is_running = True
            logger.success(f"爬虫实例 {self.instance_id} 启动成功")
            
        except Exception as e:
            logger.error(f"启动爬虫实例 {self.instance_id} 失败: {e}")
            await self.close()
            raise
    
    async def close(self):
        """关闭爬虫实例"""
        try:
            logger.info(f"关闭爬虫实例 {self.instance_id}")
            self.is_running = False
            
            # 强制关闭页面
            if self.page:
                try:
                    await asyncio.wait_for(self.page.close(), timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[{self.instance_id}] 页面关闭超时，强制继续")
                except Exception as e:
                    logger.warning(f"[{self.instance_id}] 页面关闭失败: {e}")
                finally:
                    self.page = None
                
            # 强制关闭上下文
            if self.context:
                try:
                    await asyncio.wait_for(self.context.close(), timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[{self.instance_id}] 上下文关闭超时，强制继续")
                except Exception as e:
                    logger.warning(f"[{self.instance_id}] 上下文关闭失败: {e}")
                finally:
                    self.context = None
                
            # 强制关闭浏览器
            if self.browser:
                try:
                    await asyncio.wait_for(self.browser.close(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[{self.instance_id}] 浏览器关闭超时，强制继续")
                except Exception as e:
                    logger.warning(f"[{self.instance_id}] 浏览器关闭失败: {e}")
                finally:
                    self.browser = None
                
            # 停止Playwright
            if self.playwright:
                try:
                    await asyncio.wait_for(self.playwright.stop(), timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[{self.instance_id}] Playwright停止超时，强制继续")
                except Exception as e:
                    logger.warning(f"[{self.instance_id}] Playwright停止失败: {e}")
                finally:
                    self.playwright = None
                
            logger.success(f"爬虫实例 {self.instance_id} 已关闭")
            
        except Exception as e:
            logger.error(f"关闭爬虫实例 {self.instance_id} 失败: {e}")
            # 确保状态被重置
            self.is_running = False
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
    
    async def goto(self, url: str, wait_until: str = "networkidle") -> bool:
        """访问URL"""
        if not self.page:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"[{self.instance_id}] 访问: {url} (尝试 {attempt + 1}/{self.config.max_retries})")
                
                response = await self.page.goto(url, wait_until=wait_until)
                
                if response and response.ok:
                    logger.success(f"[{self.instance_id}] 成功访问: {url}")
                    return True
                else:
                    logger.warning(f"[{self.instance_id}] 访问失败，状态码: {response.status if response else 'None'}")
                    
            except Exception as e:
                logger.error(f"[{self.instance_id}] 访问 {url} 出错: {e}")
                
                if self.config.screenshot_on_error:
                    await self.screenshot(f"error_{self.instance_id}_{int(time.time())}.png")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    
        return False
    
    async def screenshot(self, filename: str = None) -> str:
        """截图"""
        if not self.page:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        if not filename:
            filename = f"screenshot_{self.instance_id}_{int(time.time())}.png"
            
        screenshot_path = Path("data/screenshots") / filename
        screenshot_path.parent.mkdir(exist_ok=True)
        
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"[{self.instance_id}] 截图保存: {screenshot_path}")
        
        return str(screenshot_path)
    
    async def save_cookies(self, filename: str = None):
        """保存cookies"""
        if not self.context:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        if not filename:
            filename = f"cookies_{self.instance_id}.json"
            
        cookies = await self.context.cookies()
        cookies_path = Path("data/cookies") / filename
        cookies_path.parent.mkdir(exist_ok=True)
        
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
            
        logger.info(f"[{self.instance_id}] Cookies保存: {cookies_path}")
    
    async def load_cookies(self, filename: str = None):
        """加载cookies"""
        if not self.context:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        if not filename:
            filename = self.config.cookies_file or f"cookies_{self.instance_id}.json"
            
        cookies_path = Path("data/cookies") / filename
        
        if cookies_path.exists():
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                await self.context.add_cookies(cookies)
                logger.info(f"[{self.instance_id}] Cookies加载: {cookies_path}")
    
    async def wait_for_selector(self, selector: str, timeout: int = None) -> bool:
        """等待元素出现"""
        if not self.page:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        try:
            await self.page.wait_for_selector(
                selector, 
                timeout=timeout or self.config.timeout
            )
            return True
        except Exception as e:
            logger.error(f"[{self.instance_id}] 等待元素 {selector} 超时: {e}")
            return False
    
    async def click(self, selector: str) -> bool:
        """点击元素"""
        if not self.page:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        try:
            await self.page.click(selector)
            logger.info(f"[{self.instance_id}] 点击元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"[{self.instance_id}] 点击元素 {selector} 失败: {e}")
            return False
    
    async def fill(self, selector: str, text: str) -> bool:
        """填充文本"""
        if not self.page:
            raise RuntimeError(f"爬虫实例 {self.instance_id} 未启动")
        
        try:
            await self.page.fill(selector, text)
            logger.info(f"[{self.instance_id}] 填充文本到 {selector}")
            return True
        except Exception as e:
            logger.error(f"[{self.instance_id}] 填充文本到 {selector} 失败: {e}")
            return False


class CrawlerFramework:
    """爬虫框架主类"""
    
    def __init__(self):
        self.instances: Dict[str, CrawlerInstance] = {}
        self.default_config = CrawlerConfig()
        
        # 配置日志
        logger.add(
            "data/logs/crawler_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def create_instance(self, instance_id: str, config: CrawlerConfig = None) -> CrawlerInstance:
        """创建爬虫实例"""
        if instance_id in self.instances:
            logger.warning(f"实例 {instance_id} 已存在，将覆盖")
        
        config = config or self.default_config
        instance = CrawlerInstance(instance_id, config)
        self.instances[instance_id] = instance
        
        logger.info(f"创建爬虫实例: {instance_id}")
        return instance
    
    async def start_instance(self, instance_id: str):
        """启动指定实例"""
        if instance_id not in self.instances:
            raise ValueError(f"实例 {instance_id} 不存在")
        
        await self.instances[instance_id].start()
    
    async def close_instance(self, instance_id: str):
        """关闭指定实例"""
        if instance_id in self.instances:
            await self.instances[instance_id].close()
            del self.instances[instance_id]
    
    async def close_all(self):
        """关闭所有实例"""
        tasks = []
        for instance_id in list(self.instances.keys()):
            tasks.append(self.close_instance(instance_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_instance(self, instance_id: str) -> Optional[CrawlerInstance]:
        """获取实例"""
        return self.instances.get(instance_id)
    
    def list_instances(self) -> List[str]:
        """列出所有实例ID"""
        return list(self.instances.keys())
    
    async def run_task(self, instance_id: str, task_func: Callable, *args, **kwargs):
        """在指定实例上运行任务"""
        instance = self.get_instance(instance_id)
        if not instance:
            raise ValueError(f"实例 {instance_id} 不存在")
        
        if not instance.is_running:
            await instance.start()
        
        return await task_func(instance, *args, **kwargs)


# 使用示例函数
async def test_google_ai_studio(instance: CrawlerInstance):
    """测试Google AI Studio登录页面"""
    try:
        # 访问Google AI Studio
        success = await instance.goto("https://aistudio.google.com/")
        if not success:
            logger.error("访问Google AI Studio失败")
            return False
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 截图
        await instance.screenshot("google_ai_studio_main.png")
        
        # 检查是否有登录按钮或已登录状态
        login_selectors = [
            "button[data-value='sign-in']",
            "a[href*='signin']",
            ".sign-in",
            "[aria-label*='Sign in']",
            "button:has-text('Sign in')"
        ]
        
        found_login = False
        for selector in login_selectors:
            if await instance.wait_for_selector(selector, timeout=5000):
                logger.success(f"找到登录元素: {selector}")
                found_login = True
                break
        
        if not found_login:
            logger.info("未找到明显的登录按钮，可能已登录或页面结构不同")
        
        # 检查页面标题
        title = await instance.page.title()
        logger.info(f"页面标题: {title}")
        
        # 检查URL
        current_url = instance.page.url
        logger.info(f"当前URL: {current_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试Google AI Studio失败: {e}")
        return False
