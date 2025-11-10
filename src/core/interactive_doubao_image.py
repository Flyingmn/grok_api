#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包生图交互测试程序
用户可以在终端输入文本，自动填充到豆包生图并发送，监听响应
"""

import asyncio
import json
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
from .crawler_framework import CrawlerFramework, CrawlerConfig
import sys


class DoubaoImageInteractiveClient:
    """豆包生图交互测试类"""
    
    def __init__(self):
        self.framework = CrawlerFramework()
        self.instance_id = "doubao_image_interactive"
        self.instance = None
        self.api_responses = []
        self.waiting_for_response = False
        
        # DOM选择器 - 基于豆包生图的DOM结构
        self.selectors = {
            # 登录检测相关
            "login_modal": '[data-testid="login_content"]',
            "login_modal_alt": '.semi-modal-content:has([data-testid="login_content"])',
            
            # 输入框相关
            "input_container": '[data-testid="chat_input"]',
            "text_input": '[data-testid="chat_input_input"]',
            "send_button": '[data-testid="chat_input_send_button"]',
            
            # 技能选择相关 - 使用不依赖中文文本的选择器
            "skill_indicator": '[data-testid="skill_bar_button_3"][aria-pressed="true"]',  # 图像生成技能已激活
            "skill_indicator_alt": '.flex.items-center.s-font-base-em.text-s-color-brand-primary-default.select-none',  # 备用选择器
            "skill_exit_button": '[data-testid="skill_input_exit_button"]',
            "skill_bar_image_button": '[data-testid="skill_bar_button_3"]',
            "skill_button": '[data-testid="chat-input-all-skill-button"]',
            "skill_modal_image_button": 'button[data-testid="skill_bar_button_3"]',
            
            # 图像生成工具
            "reference_image_button": '[data-testid="image-creation-chat-input-picture-reference-button"]',
            "model_button": '[data-testid="image-creation-chat-input-picture-model-button"]',
            "ratio_button": '[data-testid="image-creation-chat-input-picture-ration-button"]',
            "style_button": '[data-testid="image-creation-chat-input-picture-style-button"]',
            
            # 文件上传
            "file_input": 'input[type="file"].input-QqWhqy',
            "reference_container": '.btn-xXZk0v',  # 简化选择器
        }
    
    async def setup(self):
        """初始化设置"""
        try:
            logger.info("初始化豆包生图交互测试...")
            
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
    
    async def navigate_to_doubao(self):
        """导航到豆包聊天页面"""
        try:
            logger.info("正在访问豆包聊天页面...")
            
            # 尝试直接导航，使用更短的超时时间和更宽松的等待条件
            try:
                await self.instance.page.goto("https://www.doubao.com/chat/", 
                                            wait_until="domcontentloaded", 
                                            timeout=15000)
                logger.success("页面导航成功")
            except Exception as nav_e:
                logger.warning(f"导航可能超时，检查页面状态: {nav_e}")
                
                # 检查页面是否实际已经加载
                try:
                    current_url = self.instance.page.url
                    if "doubao.com" in current_url:
                        logger.info(f"页面已加载，当前URL: {current_url}")
                    else:
                        # 如果URL不对，再尝试一次
                        logger.info("尝试重新导航...")
                        await self.instance.page.goto("https://www.doubao.com/chat/", 
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
            
            # 尝试截图，如果失败就跳过
            try:
                await self.instance.screenshot("doubao_home.png")
            except Exception as e:
                logger.warning(f"截图失败，跳过: {e}")
            
            logger.success("成功访问豆包聊天页面")
            
            # 主动触发个人资料检查以验证登录状态
            await self.trigger_profile_check()
            
            return True
            
        except Exception as e:
            logger.error(f"访问豆包聊天页面失败: {e}")
            return False
    
    async def check_login_required(self):
        """检测是否出现登录弹窗"""
        try:
            # 检查登录弹窗是否存在
            login_modal = await self.instance.page.query_selector(self.selectors["login_modal"])
            if login_modal and await login_modal.is_visible():
                logger.error("检测到登录弹窗，需要用户登录")
                return True
            
            # 备用检查
            login_modal_alt = await self.instance.page.query_selector(self.selectors["login_modal_alt"])
            if login_modal_alt and await login_modal_alt.is_visible():
                logger.error("检测到登录弹窗（备用检测），需要用户登录")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"检测登录状态失败: {e}")
            return False
    
    async def trigger_profile_check(self):
        """主动触发个人资料检查以验证登录状态"""
        try:
            logger.info("主动检查用户登录状态...")
            
            # 通过JavaScript触发个人资料API调用
            await self.instance.page.evaluate("""
                fetch('/alice/profile/self?version_code=20800&language=zh&device_platform=web&aid=497858&real_aid=497858&pkg_type=release_version&samantha_web=1&use-olympus-account=1', {
                    method: 'GET',
                    credentials: 'include'
                }).catch(() => {});
            """)
            
            # 等待一下让网络监听器处理响应
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"触发个人资料检查失败: {e}")
    
    async def check_image_skill_selected(self):
        """检查输入框是否已经选择了图像生成技能"""
        try:
            logger.info("检查图像生成技能是否已选择...")
            
            # 方法1: 检查技能按钮的激活状态
            skill_button = await self.instance.page.query_selector(self.selectors["skill_bar_image_button"])
            if skill_button:
                # 检查按钮是否有激活状态的属性
                aria_pressed = await skill_button.get_attribute("aria-pressed")
                if aria_pressed == "true":
                    logger.success("图像生成技能已选择")
                    return True
            
            # 方法2: 检查是否存在图像生成相关的工具按钮
            reference_button = await self.instance.page.query_selector(self.selectors["reference_image_button"])
            ratio_button = await self.instance.page.query_selector(self.selectors["ratio_button"])
            
            if (reference_button and await reference_button.is_visible()) or \
               (ratio_button and await ratio_button.is_visible()):
                logger.success("图像生成技能已选择")
                return True
            
            # 方法3: 备用检查 - 检查技能指示器
            skill_indicator = await self.instance.page.query_selector(self.selectors["skill_indicator_alt"])
            if skill_indicator and await skill_indicator.is_visible():
                # 检查文本内容是否包含图像相关关键词
                text_content = await skill_indicator.text_content()
                if text_content and ("图" in text_content or "image" in text_content.lower()):
                    logger.success("图像生成技能已选择")
                    return True
            
            logger.info("图像生成技能未选择")
            return False
                
        except Exception as e:
            logger.error(f"检查图像生成技能状态失败: {e}")
            return False
    
    async def select_image_generation_skill(self):
        """选择图像生成技能"""
        try:
            logger.info("开始选择图像生成技能...")
            
            current_url = self.instance.page.url
            logger.info(f"当前页面URL: {current_url}")
            
            # 分支1: 如果在主聊天页面 (https://www.doubao.com/chat/)
            if current_url == "https://www.doubao.com/chat/":
                logger.info("当前在主聊天页面，查找技能栏中的图像生成按钮")
                
                # 查找页面内的图像生成技能按钮
                skill_button = await self.instance.page.query_selector(self.selectors["skill_bar_image_button"])
                
                if skill_button and await skill_button.is_visible():
                    logger.info("找到图像生成技能按钮，点击选择")
                    await skill_button.click()
                    await asyncio.sleep(2)  # 等待技能切换完成
                    logger.success("图像生成技能选择成功")
                    return True
                else:
                    logger.error("未找到图像生成技能按钮")
                    return False
            
            # 分支2: 如果在会话页面 (带有会话ID)
            elif "/chat/" in current_url and current_url != "https://www.doubao.com/chat/":
                logger.info("当前在会话页面，需要通过技能按钮切换")
                
                # 点击技能按钮打开技能选择弹窗
                skill_button = await self.instance.page.query_selector(self.selectors["skill_button"])
                
                if skill_button and await skill_button.is_visible():
                    logger.info("找到技能按钮，点击打开技能选择")
                    await skill_button.click()
                    await asyncio.sleep(2)  # 等待弹窗出现
                    
                    # 在弹窗中选择图像生成技能
                    modal_image_button = await self.instance.page.query_selector(self.selectors["skill_modal_image_button"])
                    
                    if modal_image_button and await modal_image_button.is_visible():
                        logger.info("在弹窗中找到图像生成按钮，点击选择")
                        await modal_image_button.click()
                        await asyncio.sleep(2)  # 等待技能切换完成
                        logger.success("图像生成技能选择成功")
                        return True
                    else:
                        logger.error("在弹窗中未找到图像生成按钮")
                        return False
                else:
                    logger.error("未找到技能按钮")
                    return False
            else:
                logger.warning(f"未识别的页面URL: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"选择图像生成技能失败: {e}")
            return False
    
    async def ensure_image_skill_ready(self):
        """确保图像生成技能已准备就绪"""
        try:
            logger.info("确保图像生成技能已准备就绪...")
            
            # 检查是否已选择图像生成技能
            if await self.check_image_skill_selected():
                logger.success("图像生成技能已就绪")
                return True
            
            # 如果未选择，则选择图像生成技能
            if await self.select_image_generation_skill():
                # 再次检查是否选择成功
                await asyncio.sleep(1)
                if await self.check_image_skill_selected():
                    logger.success("图像生成技能选择并验证成功")
                    return True
                else:
                    logger.error("图像生成技能选择后验证失败")
                    return False
            else:
                logger.error("选择图像生成技能失败")
                return False
                
        except Exception as e:
            logger.error(f"确保图像生成技能就绪失败: {e}")
            return False
    
    async def set_aspect_ratio(self, ratio: str = "1:1"):
        """设置图片比例"""
        try:
            logger.info(f"设置图片比例为: {ratio}")
            
            # 点击比例按钮
            ratio_button = await self.instance.page.query_selector(self.selectors["ratio_button"])
            
            if ratio_button and await ratio_button.is_visible():
                await ratio_button.click()
                await asyncio.sleep(1)
                logger.info("已点击比例按钮")
                
                # 根据比例选择对应的选项 - 使用下拉菜单项
                ratio_index_mapping = {
                    "1:1": 0,    # 第1个选项
                    "2:3": 1,    # 第2个选项
                    "4:3": 2,    # 第3个选项
                    "9:16": 3,   # 第4个选项
                    "16:9": 4    # 第5个选项
                }
                
                ratio_index = ratio_index_mapping.get(ratio)
                if ratio_index is not None:
                    try:
                        # 等待下拉菜单出现
                        await self.instance.page.wait_for_selector('[data-testid="dropdown-menu-item"]', timeout=5000)
                        
                        # 获取所有下拉菜单项
                        menu_items = await self.instance.page.query_selector_all('[data-testid="dropdown-menu-item"]')
                        
                        if len(menu_items) > ratio_index:
                            # 点击对应索引的菜单项
                            await menu_items[ratio_index].click()
                            logger.success(f"成功设置图片比例为: {ratio}")
                            
                            # 点击其他地方关闭比例弹出框
                            await asyncio.sleep(0.5)
                            await self.instance.page.click('body', force=True)
                            await asyncio.sleep(1)
                            logger.info("已关闭比例选择弹窗")
                            
                            return True
                        else:
                            logger.error(f"比例选项索引超出范围: {ratio_index}, 实际选项数: {len(menu_items)}")
                            return False
                            
                    except Exception as e:
                        logger.warning(f"选择比例选项失败: {e}")
                        
                        # 备用方法：尝试使用SVG图标来识别选项
                        try:
                            ratio_svg_mapping = {
                                "1:1": "ic_ratio_1_1.svg",
                                "2:3": "ic_ratio_2_3.svg", 
                                "4:3": "ic_ratio_4_3.svg",
                                "9:16": "ic_ratio_9_16.svg",
                                "16:9": "ic_ratio_16_9.svg"
                            }
                            
                            svg_name = ratio_svg_mapping.get(ratio)
                            if svg_name:
                                # 通过SVG图标选择选项
                                svg_selector = f'img[src*="{svg_name}"]'
                                await self.instance.page.wait_for_selector(svg_selector, timeout=3000)
                                
                                # 点击包含该SVG的菜单项
                                svg_element = await self.instance.page.query_selector(svg_selector)
                                if svg_element:
                                    # 找到父级菜单项并点击
                                    menu_item = await svg_element.evaluate_handle('el => el.closest("[data-testid=\\"dropdown-menu-item\\"]")')
                                    if menu_item:
                                        await menu_item.click()
                                        logger.success(f"成功设置图片比例为: {ratio} (通过SVG)")
                                        
                                        # 点击其他地方关闭比例弹出框
                                        await asyncio.sleep(0.5)
                                        await self.instance.page.click('body', force=True)
                                        await asyncio.sleep(1)
                                        logger.info("已关闭比例选择弹窗")
                                        
                                        return True
                        except Exception as svg_e:
                            logger.warning(f"SVG备用方法也失败: {svg_e}")
                        
                        return False
                else:
                    logger.error(f"不支持的比例: {ratio}")
                    return False
            else:
                logger.warning("未找到比例按钮")
                return False
                
        except Exception as e:
            logger.error(f"设置图片比例失败: {e}")
            return False
    
    async def upload_reference_image(self, image_path: str = None):
        """上传参考图片"""
        try:
            logger.info("开始上传参考图片...")
            
            # 如果没有指定路径，使用默认的test.png
            if image_path is None:
                image_path = "test.png"
            
            # 检查图片文件是否存在
            image_file = Path(image_path)
            if not image_file.exists():
                logger.error(f"未找到图片文件: {image_path}")
                return False
            
            # 首先确保图像生成技能已选择
            if not await self.ensure_image_skill_ready():
                logger.error("图像生成技能未就绪，无法上传参考图")
                return False
            
            # 等待一下让技能界面稳定
            await asyncio.sleep(2)
            
            # 方法1：直接查找页面中的文件输入元素（最简单直接）
            try:
                file_inputs = await self.instance.page.query_selector_all('input[type="file"].input-QqWhqy')
                if file_inputs:
                    logger.info(f"找到 {len(file_inputs)} 个文件输入元素，使用第一个")
                    await file_inputs[0].set_input_files(str(image_file.resolve()))
                    await asyncio.sleep(2)
                    logger.success("参考图片上传成功（直接方法）")
                    return True
            except Exception as direct_e:
                logger.warning(f"直接方法失败: {direct_e}")
            
            # 方法2：查找参考图容器
            try:
                reference_container = await self.instance.page.query_selector('.btn-xXZk0v')
                if reference_container and await reference_container.is_visible():
                    logger.info("找到参考图容器")
                    
                    # 在容器内查找文件输入元素
                    file_input = await reference_container.query_selector('input[type="file"]')
                    if file_input:
                        logger.info("在容器内找到文件输入元素")
                        await file_input.set_input_files(str(image_file.resolve()))
                        await asyncio.sleep(2)
                        logger.success("参考图片上传成功（容器方法）")
                        return True
            except Exception as container_e:
                logger.warning(f"容器方法失败: {container_e}")
            
            # 方法3：点击按钮触发文件选择器
            try:
                # 查找包含"参考图"文本的按钮
                reference_buttons = await self.instance.page.query_selector_all('button')
                for button in reference_buttons:
                    try:
                        text_content = await button.text_content()
                        if text_content and "参考图" in text_content:
                            logger.info("找到参考图按钮，尝试点击")
                            
                            async with self.instance.page.expect_file_chooser() as fc_info:
                                await button.click()
                            
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(str(image_file.resolve()))
                            await asyncio.sleep(2)
                            logger.success("参考图片上传成功（按钮方法）")
                            return True
                    except:
                        continue
            except Exception as button_e:
                logger.warning(f"按钮方法失败: {button_e}")
            
            logger.error("所有上传方法都失败了")
            return False
                
        except Exception as e:
            logger.error(f"上传参考图片失败: {e}")
            return False
    
    async def send_message(self, message: str):
        """发送消息"""
        try:
            logger.info(f"正在发送消息: {message}")
            
            # 确保图像生成技能已准备就绪
            if not await self.ensure_image_skill_ready():
                logger.error("图像生成技能未就绪")
                return False
            
            # 清空之前的响应
            self.api_responses.clear()
            
            # 填充文本到输入框 - 追加到现有内容后面，不清空技能和比例设置
            text_input = await self.instance.page.query_selector(self.selectors["text_input"])
            
            if text_input and await text_input.is_visible():
                # 获取写入前的内容用于验证
                original_content = await self.instance.page.evaluate("""
                    () => {
                        const editor = document.querySelector('[data-testid="chat_input_input"]');
                        return editor ? editor.textContent || editor.innerText || '' : '';
                    }
                """)
                logger.info(f"写入前输入框内容: '{original_content}'")
                
                success = False
                
                # 直接使用键盘输入方法（最可靠的方式）
                try:
                    logger.info("使用键盘输入方法...")
                    
                    # 确保编辑器获得焦点
                    await text_input.click()
                    await asyncio.sleep(0.5)
                    
                    # 使用End键移动到最末尾
                    await self.instance.page.keyboard.press("End")
                    await asyncio.sleep(0.3)
                    
                    # 逐字符输入，确保每个字符都触发正确的事件
                    logger.info(f"开始逐字符输入: '{message}'")
                    for char in message:
                        await self.instance.page.keyboard.type(char)
                        await asyncio.sleep(0.05)  # 短暂延迟模拟真实输入
                    
                    await asyncio.sleep(1)
                    
                    # 验证是否写入成功
                    new_content = await self.instance.page.evaluate("""
                        () => {
                            const editor = document.querySelector('[data-testid="chat_input_input"]');
                            return editor ? editor.textContent || editor.innerText || '' : '';
                        }
                    """)
                    
                    if message in new_content:
                        success = True
                        logger.success(f"文本已追加到输入框（键盘方法），当前内容: '{new_content}'")
                    else:
                        logger.error(f"键盘输入后验证失败，期望包含: '{message}'，实际内容: '{new_content}'")
                    
                except Exception as type_error:
                    logger.error(f"键盘输入方法失败: {type_error}")
                
                # 方法2: 如果键盘输入失败，使用强制填充
                if not success:
                    try:
                        logger.info("尝试强制填充方法...")
                        
                        # 先清空再填充完整内容（包含技能标签）
                        await text_input.fill("")
                        await asyncio.sleep(0.5)
                        
                        # 重新设置技能和比例，然后添加文本
                        await self.ensure_image_skill_ready()
                        await asyncio.sleep(1)
                        
                        # 再次尝试填充文本
                        await text_input.fill(message)
                        await asyncio.sleep(1)
                        
                        # 验证
                        final_content = await self.instance.page.evaluate("""
                            () => {
                                const editor = document.querySelector('[data-testid="chat_input_input"]');
                                return editor ? editor.textContent || editor.innerText || '' : '';
                            }
                        """)
                        
                        if message in final_content:
                            success = True
                            logger.success(f"文本已填充到输入框（强制方法），当前内容: '{final_content}'")
                        else:
                            logger.error(f"强制填充后验证失败，期望包含: '{message}'，实际内容: '{final_content}'")
                        
                    except Exception as fill_error:
                        logger.error(f"强制填充方法失败: {fill_error}")
                
                if not success:
                    logger.error("所有文本写入方法都失败了")
                    return False
                    
            else:
                logger.error("未找到文本输入框")
                return False
            
            # 点击发送按钮
            send_button = await self.instance.page.query_selector(self.selectors["send_button"])
            
            if send_button and await send_button.is_visible():
                # 检查按钮是否可用
                is_disabled = await send_button.get_attribute("disabled")
                if is_disabled:
                    logger.warning("发送按钮当前被禁用，等待启用...")
                    # 等待按钮启用
                    for i in range(10):
                        await asyncio.sleep(0.5)
                        is_disabled = await send_button.get_attribute("disabled")
                        if not is_disabled:
                            break
                    
                    if is_disabled:
                        logger.error("发送按钮仍然被禁用")
                        return False
                
                await send_button.click()
                logger.success("已点击发送按钮")
                
                # 等待一下，然后检测是否出现登录弹窗
                await asyncio.sleep(2)
                if await self.check_login_required():
                    logger.error("发送消息后出现登录弹窗，请先登录豆包账号")
                    return False
                
                # 等待响应
                print("⏳ 等待豆包响应...")
                self.waiting_for_response = True
                
                # 等待响应（最多5分钟）
                for i in range(600):  # 5分钟，每0.5秒检查一次
                    if not self.waiting_for_response:
                        break
                    await asyncio.sleep(0.5)
                
                if self.waiting_for_response:
                    logger.warning("等待响应超时")
                    self.waiting_for_response = False
                
                return True
            else:
                logger.error("未找到发送按钮")
                return False
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    async def setup_network_listener(self):
        """设置网络请求监听器"""
        try:
            # 监听网络响应 - 监听豆包生图API和用户登录状态
            async def handle_response(response):
                url = response.url
                
                # 监听用户个人资料接口，检测登录状态
                if "/alice/profile/self" in url:
                    logger.info(f"检测到用户个人资料API调用: {url}")
                    try:
                        response_text = await response.text()
                        response_data = json.loads(response_text)
                        
                        # 检查是否成功获取用户信息
                        if (response_data.get("code") == 0 and 
                            response_data.get("data") and 
                            response_data["data"].get("profile_brief")):
                            
                            user_info = response_data["data"]["profile_brief"]
                            nickname = user_info.get("nickname", "未知用户")
                            user_id = user_info.get("id", "")
                            
                            logger.success(f"检测到用户已登录: {nickname} (ID: {user_id})")
                            print(f"\n✅ 检测到用户登录: {nickname}")
                            
                            # 触发保存cookies
                            try:
                                await self.save_cookies()
                                logger.success("已自动保存登录状态")
                                print("💾 已自动保存登录状态")
                            except Exception as save_e:
                                logger.error(f"自动保存cookies失败: {save_e}")
                        
                    except Exception as e:
                        logger.warning(f"解析用户个人资料响应失败: {e}")
                
                # 监听豆包生图的completion API
                elif "/samantha/chat/completion" in url:
                    logger.info(f"检测到豆包生图API调用: {url}")
                    try:
                        # 豆包生图返回的是SSE流，需要特殊处理
                        content_type = response.headers.get("content-type", "")
                        if "text/plain" in content_type or "text/event-stream" in content_type:
                            logger.info("检测到SSE流响应，开始实时解析...")
                            await self.handle_sse_stream(response)
                        else:
                            # 普通JSON响应
                            response_text = await response.text()
                            logger.info("收到普通API响应")
                            
                            try:
                                response_data = json.loads(response_text)
                                self.api_responses.append({
                                    "url": url,
                                    "status": response.status,
                                    "data": response_data,
                                    "timestamp": asyncio.get_event_loop().time()
                                })
                                
                                # 提取AI回复内容
                                ai_response = self.extract_ai_response(response_data)
                                if ai_response:
                                    print(f"\n🤖 豆包回复: {ai_response}")
                                
                            except json.JSONDecodeError:
                                logger.warning("响应不是有效的JSON格式")
                                print(f"\n⚠️  响应格式错误，内容长度: {len(response_text)}")
                        
                        self.waiting_for_response = False
                        
                    except Exception as e:
                        logger.error(f"处理豆包API响应时出错: {e}")
                        self.waiting_for_response = False
            
            # 监听网络请求
            async def handle_request(request):
                url = request.url
                
                # 监听用户个人资料请求
                if "/alice/profile/self" in url:
                    logger.info(f"检测到用户个人资料API请求: {url}")
                
                # 监听豆包生图API请求
                elif "/samantha/chat/completion" in url:
                    logger.info(f"检测到豆包生图API请求: {url}")
                    try:
                        # 获取请求数据
                        post_data = request.post_data
                        if post_data:
                            logger.info("豆包生图请求数据已发送")
                            self.waiting_for_response = True
                            
                            # 解析请求数据以获取提示词
                            try:
                                request_data = json.loads(post_data)
                                if request_data.get("messages") and len(request_data["messages"]) > 0:
                                    message = request_data["messages"][0]
                                    if message.get("content"):
                                        content = json.loads(message["content"])
                                        prompt = content.get("text", "")
                                        if prompt:
                                            print(f"\n📝 发送的提示词: {prompt}")
                            except:
                                pass
                    except Exception as e:
                        logger.error(f"处理豆包API请求时出错: {e}")
            
            # 绑定事件监听器
            self.instance.page.on("response", handle_response)
            self.instance.page.on("request", handle_request)
            
            logger.success("豆包生图网络监听器设置完成")
            
        except Exception as e:
            logger.error(f"设置网络监听器失败: {e}")
    
    async def handle_sse_stream(self, response):
        """处理SSE流响应 - 读取完整响应数据"""
        try:
            logger.info("开始处理豆包生图SSE流...")
            
            found_images = []
            collected_text = []  # 收集文本内容
            
            # 读取完整响应文本
            response_text = await response.text()
            logger.info(f"收到SSE响应，长度: {len(response_text)}")
            
            # 按照server.js的逻辑，根据"\n\n"拆分完整事件
            events = response_text.split('\n\n')
            logger.info(f"拆分出 {len(events)} 个事件")
            
            for i, event in enumerate(events):
                if not event.strip():
                    continue
                
                # 检查是否是网关错误
                if 'event: gateway-error' in event:
                    error_match = event.split('data: ')
                    if len(error_match) > 1:
                        try:
                            error_data = json.loads(error_match[1].split('\n')[0])
                            logger.error(f"服务器网关错误: {error_data}")
                            print(f"\n❌ 服务器返回网关错误: {error_data.get('message', '未知错误')}")
                            return
                        except:
                            print(f"\n❌ 服务器返回网关错误")
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
                    # 解析外层事件对象
                    event_obj = json.loads(data_line)
                    event_type = event_obj.get("event_type")
                    
                    # 处理event_type为2001的事件
                    if event_type == 2001:
                        event_data = event_obj.get("event_data")
                        if event_data:
                            try:
                                inner_data = json.loads(event_data)
                                message = inner_data.get("message")
                                
                                if message:
                                    content_type = message.get("content_type")
                                    
                                    # 处理文本消息 (content_type 10000)
                                    if content_type == 10000:
                                        content = json.loads(message.get("content", "{}"))
                                        text = content.get("text", "")
                                        if text:
                                            collected_text.append(text)
                                            # 实时打印文本
                                            sys.stdout.write(text)
                                            sys.stdout.flush()
                                    
                                    # 处理图片消息 (content_type 2074)
                                    elif content_type == 2074:
                                        logger.info("找到图片载体消息 (content_type 2074)")
                                        
                                        content = json.loads(message.get("content", "{}"))
                                        creations = content.get("creations", [])
                                        
                                        logger.info(f"找到 {len(creations)} 张图片信息，状态: {[c.get('image', {}).get('status', 'unknown') for c in creations]}")
                                        
                                        found_status_2 = False
                                        for i, creation in enumerate(creations):
                                            image_info = creation.get("image", {})
                                            status = image_info.get("status")
                                            
                                            # 只处理status为2的完成图片
                                            if status == 2:
                                                # 按优先级获取图片URL (无水印优先)
                                                image_url = (
                                                    image_info.get("image_ori_raw", {}).get("url") or
                                                    image_info.get("image_ori", {}).get("url") or
                                                    image_info.get("image_preview", {}).get("url") or
                                                    image_info.get("image_thumb", {}).get("url")
                                                )
                                                
                                                if image_url:
                                                    logger.success(f"✅ 找到第{i+1}张图片URL (status=2): {image_url}")
                                                    found_images.append(image_url)
                                                    found_status_2 = True
                                            else:
                                                logger.debug(f"图片 {i+1} 状态为 {status}，跳过...")
                                        
                                        # 如果找到了完成的图片，继续处理其他事件以获取完整文本
                                        if found_status_2:
                                            logger.info("找到有效图片，继续处理文本内容")
                                
                                # 检查生成进度
                                if "step" in inner_data:
                                    progress = int(inner_data["step"] * 100)
                                    print(f"🎨 生成进度: {progress}%")
                                    
                            except json.JSONDecodeError as e:
                                logger.debug(f"解析内层事件数据失败: {e}")
                    
                    # 处理流结束事件
                    elif event_type == 2003:
                        logger.info("收到流结束事件 (2003)")
                        break
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"解析事件失败: {e}")
            
            # 显示收集到的文本内容
            if collected_text:
                full_text = "".join(collected_text)
                print(f"\n🤖 豆包回复: {full_text}")
            
            # 显示找到的图片
            if found_images:
                print(f"\n🖼️  豆包生成了 {len(found_images)} 张图片:")
                for i, url in enumerate(found_images, 1):
                    print(f"   {i}. {url}")
                    # 显示图片类型（根据URL判断是否为无水印版本）
                    if "image_ori_raw" in url or "image_ori" in url:
                        print(f"      📸 无水印原图")
                    elif "image_preview" in url:
                        print(f"      🖼️  预览图")
                    elif "image_thumb" in url:
                        print(f"      🔍 缩略图")
                
                # 保存图片信息
                self.api_responses.append({
                    "url": response.url,
                    "status": response.status,
                    "images": found_images,
                    "text": "".join(collected_text) if collected_text else "",
                    "timestamp": asyncio.get_event_loop().time()
                })
            elif collected_text:
                # 只有文本，没有图片
                self.api_responses.append({
                    "url": response.url,
                    "status": response.status,
                    "text": "".join(collected_text),
                    "timestamp": asyncio.get_event_loop().time()
                })
            else:
                print("\n⚠️  未从SSE流中提取到内容")
            
        except Exception as e:
            logger.error(f"处理SSE流失败: {e}")
            print(f"\n❌ 处理豆包SSE流失败: {e}")
    
    def extract_ai_response(self, response_data) -> Optional[str]:
        """从API响应中提取AI回复文本"""
        try:
            logger.debug(f"开始解析响应数据: {type(response_data)}")
            
            # 根据豆包的响应结构解析
            if isinstance(response_data, dict):
                # 查找常见的文本字段
                text_fields = ["text", "content", "message", "reply", "answer", "result"]
                
                for field in text_fields:
                    if field in response_data and response_data[field]:
                        return str(response_data[field])
                
                # 递归查找嵌套结构中的文本
                return self._find_text_in_dict(response_data)
            
            elif isinstance(response_data, list) and len(response_data) > 0:
                # 如果是列表，查找第一个包含文本的项
                for item in response_data:
                    if isinstance(item, dict):
                        text = self._find_text_in_dict(item)
                        if text:
                            return text
                    elif isinstance(item, str) and item.strip():
                        return item.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"提取AI响应失败: {e}")
            return None
    
    def _find_text_in_dict(self, data: dict, depth: int = 0) -> Optional[str]:
        """在字典中递归查找文本内容"""
        if depth > 5:  # 防止无限递归
            return None
        
        for key, value in data.items():
            if isinstance(value, str) and value.strip() and len(value) > 10:
                # 过滤掉看起来像ID或token的字符串
                if not any(char in value for char in ["://", "token", "id", "uuid"]):
                    return value.strip()
            elif isinstance(value, dict):
                result = self._find_text_in_dict(value, depth + 1)
                if result:
                    return result
            elif isinstance(value, list) and len(value) > 0:
                for item in value:
                    if isinstance(item, str) and item.strip() and len(item) > 10:
                        return item.strip()
                    elif isinstance(item, dict):
                        result = self._find_text_in_dict(item, depth + 1)
                        if result:
                            return result
        
        return None
    
    async def run_interactive_session(self):
        """运行交互会话"""
        try:
            print("🚀 启动豆包生图交互测试")
            print("=" * 50)
            
            # 初始化
            if not await self.setup():
                return False
            
            # 导航到豆包聊天页面
            if not await self.navigate_to_doubao():
                return False
            
            print("\n✅ 初始化完成！现在可以开始对话了")
            print("💡 可用命令:")
            print("  • 'quit' 或 'exit' - 退出程序并保存登录状态")
            print("  • 'screenshot' - 截图当前页面")
            print("  • 'save' - 手动保存登录状态")
            print("  • '上传图片' - 上传test.png作为参考图")
            print("  • '设置比例 [比例]' - 设置图片比例（如：设置比例 16:9）")
            print("  • 直接输入文本 - 发送给豆包生图")
            print("💾 登录状态会自动保存为cookies文件")
            print("📸 确保test.png文件在当前目录中")
            print("📐 支持的比例: 1:1, 2:3, 4:3, 9:16, 16:9")
            print("=" * 50)
            
            # 开始交互循环
            while True:
                try:
                    # 获取用户输入
                    user_input = input("\n👤 请输入消息: ").strip()
                    
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
                    
                    # 检查上传图片命令
                    if user_input.lower() in ['上传图片', 'upload', 'upload image']:
                        success = await self.upload_reference_image()
                        if success:
                            print("✅ 参考图片上传成功")
                        else:
                            print("❌ 参考图片上传失败")
                        continue
                    
                    # 检查设置比例命令
                    if user_input.lower().startswith('设置比例') or user_input.lower().startswith('set ratio'):
                        parts = user_input.split()
                        if len(parts) >= 2:
                            ratio = parts[1]
                            success = await self.set_aspect_ratio(ratio)
                            if success:
                                print(f"✅ 图片比例已设置为: {ratio}")
                            else:
                                print(f"❌ 设置图片比例失败: {ratio}")
                        else:
                            print("❌ 请指定比例，例如：设置比例 16:9")
                        continue
                    
                    # 发送消息
                    success = await self.send_message(user_input)
                    if not success:
                        print("❌ 发送消息失败，请重试")
                        continue
                    
                except KeyboardInterrupt:
                    print("\n\n💾 正在保存登录状态...")
                    await self.save_cookies()
                    print("👋 程序被用户中断，正在退出...")
                    break
                except Exception as e:
                    logger.error(f"交互过程中出错: {e}")
                    print("❌ 出现错误，请重试")
            
            return True
            
        except Exception as e:
            logger.error(f"运行交互会话失败: {e}")
            return False
        finally:
            # 清理资源
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        try:
            logger.info(f"正在清理资源... ({self.instance_id})")
            
            # 保存cookies（如果有的话）
            try:
                await self.save_cookies()
                logger.info(f"已保存cookies ({self.instance_id})")
            except Exception as e:
                logger.warning(f"保存cookies失败 ({self.instance_id}): {e}")
            
            # 关闭浏览器框架
            if self.framework:
                try:
                    await self.framework.close_all()
                    logger.info(f"已关闭浏览器框架 ({self.instance_id})")
                except Exception as e:
                    logger.warning(f"关闭浏览器框架失败 ({self.instance_id}): {e}")
                finally:
                    self.framework = None
            
            # 清理实例引用
            self.instance = None
            
            logger.success(f"资源清理完成 ({self.instance_id})")
            
        except Exception as e:
            logger.error(f"清理资源失败 ({self.instance_id}): {e}")


async def main():
    """主函数"""
    client = DoubaoImageInteractiveClient()
    await client.run_interactive_session()


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
