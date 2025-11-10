#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google AI Studio 交互测试程序
用户可以在终端输入文本，自动填充到AI Studio并发送，监听API响应
"""

import asyncio
import json
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
from .crawler_framework import CrawlerFramework, CrawlerConfig
import sys


class AIStudioInteractiveClient:
    """AI Studio交互测试类"""
    
    def __init__(self):
        self.framework = CrawlerFramework()
        self.instance_id = "ai_studio_interactive"
        self.instance = None
        self.api_responses = []
        self.waiting_for_response = False
        
        # DOM选择器 - 更兼容的选择器
        self.selectors = {
            "textarea": 'textarea[placeholder="Start typing a prompt"]',
            "run_button": 'button[aria-label="Run"]',
            "alternative_textarea": 'textarea.textarea',
            "alternative_run_button": 'button.run-button'
        }
    
    async def setup(self):
        """初始化设置"""
        try:
            logger.info("初始化AI Studio交互测试...")
            
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
    

    async def dismiss_menu(self):
        """
        检测菜单是否存在，如果存在，则通过点击透明遮罩层 (backdrop) 来关闭它。
        """
        MENU_PANEL_SELECTOR = '.mat-mdc-menu-panel'
        BACKDROP_SELECTOR = '.cdk-overlay-backdrop.cdk-overlay-backdrop-showing'
        
        print("🔍 检查上传菜单面板是否存在...")
        
        try:
            # 1. 检查菜单面板是否在合理时间内可见
            await self.instance.page.wait_for_selector(MENU_PANEL_SELECTOR, state='visible', timeout=1000)
            
            print("❗ 检测到菜单面板，尝试点击透明遮罩层 (Backdrop) 关闭...")
            
            # 2. 确保遮罩层可见并点击它。
            # 菜单通常通过点击遮罩层关闭，即使它是透明的。
            await self.instance.page.wait_for_selector(BACKDROP_SELECTOR, state='visible', timeout=1000)
            
            # 强制点击遮罩层的中心点，以确保点击成功，即使它可能不是一个传统的“按钮”
            await self.instance.page.click(BACKDROP_SELECTOR)
            
            # 等待短暂时间，确保菜单关闭
            await asyncio.sleep(0.5)
            
            # 3. 再次检查菜单面板是否不再可见，确认关闭成功
            await self.instance.page.wait_for_selector(MENU_PANEL_SELECTOR, state='hidden', timeout=1000)
            
            print("✅ 菜单已通过点击遮罩层成功关闭。")
            return True
            
        except TimeoutError:
            # 如果任何一个 wait_for_selector 超时，都视为失败/不存在，并继续执行
            print("ℹ️ 菜单未出现，或未能成功关闭。继续执行。")
            return False
        except Exception as e:
            print(f"❌ 关闭菜单时发生错误: {e}")
            return False

    async def handle_autosave_dialog(self):
        """检测并关闭自动保存功能弹窗"""
        try:
            logger.info("检查是否存在自动保存功能弹窗...")
            
            # 检查弹窗容器
            dialog_selectors = [
                'ms-autosave-enabled-by-default-dialog',
                '.mat-mdc-dialog-container',
                '[class*="autosave"]'
            ]
            
            dialog_found = False
            for selector in dialog_selectors:
                try:
                    dialog = await self.instance.page.query_selector(selector)
                    if dialog and await dialog.is_visible():
                        logger.info(f"找到自动保存弹窗: {selector}")
                        dialog_found = True
                        break
                except:
                    continue
            
            if not dialog_found:
                logger.debug("未发现自动保存弹窗")
                return True
            
            # 查找"Got it"按钮
            got_it_selectors = [
                'button:has-text("Got it")',
                'button.ms-button-primary:has-text("Got it")',
                '[class*="ms-button-primary"]:has-text("Got it")',
                'mat-dialog-actions button'
            ]
            
            for selector in got_it_selectors:
                try:
                    button = await self.instance.page.query_selector(selector)
                    if button and await button.is_visible():
                        logger.info("点击'Got it'按钮关闭自动保存弹窗")
                        await button.click()
                        await asyncio.sleep(2)  # 等待弹窗关闭
                        logger.success("自动保存弹窗已关闭")
                        return True
                except Exception as e:
                    logger.debug(f"点击按钮失败 {selector}: {e}")
                    continue
            
            # 如果找不到按钮，尝试点击遮罩层关闭
            try:
                backdrop = await self.instance.page.query_selector('.cdk-overlay-backdrop')
                if backdrop:
                    logger.info("尝试点击遮罩层关闭弹窗")
                    await backdrop.click()
                    await asyncio.sleep(2)
                    logger.success("通过遮罩层关闭弹窗")
                    return True
            except Exception as e:
                logger.debug(f"点击遮罩层失败: {e}")
            
            logger.warning("无法关闭自动保存弹窗")
            return False
            
        except Exception as e:
            logger.error(f"处理自动保存弹窗失败: {e}")
            return False

    async def handle_copyright_acknowledgement(self):
        """检测并点击版权确认按钮以关闭弹出窗口。"""
        # 您提供的DOM按钮的XPath选择器
        ACKNOWLEDGEMENT_BUTTON_SELECTOR = '//button[contains(@aria-label, "Agree to the copyright acknowledgement") and contains(@class, "ms-button-primary")]'
        
        logger.info("检查是否存在版权确认弹窗...")
        
        try:
            # 使用 page.wait_for_selector 检查按钮是否在合理时间内出现 (例如 5 秒)
            # timeout 设置为较短时间，如果按钮不存在，程序不会等待太久。
            await self.instance.page.wait_for_selector(ACKNOWLEDGEMENT_BUTTON_SELECTOR, timeout=5000)
            
            # 如果找到按钮，则点击它
            await self.instance.page.click(ACKNOWLEDGEMENT_BUTTON_SELECTOR)
            logger.success("成功点击版权确认按钮！弹窗已关闭。")
            
            # 点击后等待短暂时间，让弹窗关闭动画完成
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            # 如果超时或元素未找到，捕获异常，视为弹窗不存在，继续执行后续步骤
            logger.debug("未检测到版权确认弹窗或点击失败，继续执行下一步。")
            return False

    async def upload_image_and_text(self, image_path: str = None):
        """上传图片并输入文字（不发送）"""
        try:
            print("📸 开始上传图片和输入文字...")
            
            # 确保在正确的页面上
            if not await self.ensure_on_image_generation_page():
                print("⚠️ 无法确保在正确的生图页面上")
            
            # 如果没有指定路径，使用默认的test.png
            if image_path is None:
                image_path = "test.png"
            
            # 检查图片文件是否存在
            image_file = Path(image_path)
            if not image_file.exists():
                print(f"❌ 未找到图片文件: {image_path}")
                return False
            
            # 获取输入框选择器
            textarea_selector = self.selectors.get("active_textarea")
            if not textarea_selector:
                print("❌ 未找到输入框，请先运行程序并找到输入元素")
                return False
            
            print("📤 正在上传图片...")
            
            # 方法1: 尝试使用文件输入
            success = await self.try_file_input_upload(str(image_file.resolve()))
            
            # 方法2: 尝试文件选择器监听
            if not success and not await self.check_image_uploaded():
                print("🔄 尝试文件选择器监听...")
                success = await self.try_file_chooser_upload(str(image_file.resolve()))
            
            # 方法3: 尝试拖拽上传
            if not success and not await self.check_image_uploaded():
                print("🔄 尝试拖拽上传...")
                await self.try_drag_drop_upload(str(image_file.resolve()), textarea_selector)
            
            # 等待上传完成
            await asyncio.sleep(2)
            
            await self.handle_copyright_acknowledgement() # **新增的调用**

            # 输入文字到输入框
            # text_to_input = "请描述这张图片中的人物"
            # print(f"✏️ 正在输入文字: {text_to_input}")
            
            # await self.instance.page.fill(textarea_selector, text_to_input)
            
            #关闭上传菜单
            await self.dismiss_menu()

            await asyncio.sleep(2) # 等待2秒，确保版权确认完成

            print("✅ 图片上传和文字输入完成！")
            print("💡 现在你可以手动点击发送按钮，或者输入其他命令")
            
            return True
            
        except Exception as e:
            logger.error(f"上传图片失败: {e}")
            print(f"❌ 上传图片失败: {e}")
            return False
    
    async def try_file_input_upload(self, image_path: str):
        """尝试通过文件输入上传图片"""
        try:
            # 查找文件输入元素
            file_input_selectors = [
                'input[type="file"]',
                'input[accept*="image"]',
                '[data-testid="file-input"]',
                '.file-input'
            ]
            
            for selector in file_input_selectors:
                try:
                    file_input = await self.instance.page.query_selector(selector)
                    if file_input:
                        print(f"📁 找到文件输入: {selector}")
                        await file_input.set_input_files(image_path)
                        print("✅ 通过文件输入上传成功")
                        return True
                except Exception as e:
                    logger.debug(f"文件输入选择器 {selector} 失败: {e}")
                    continue
            
            # 尝试点击上传按钮触发文件选择 - 基于新的DOM结构
            upload_button_selectors = [
                # 新的AI Studio结构
                'ms-add-chunk-menu button',
                'button[aria-label*="Insert assets"]',
                'button[iconname="add_circle"]',
                'button:has(.material-symbols-outlined)',
                # 旧的选择器保持兼容
                'button[aria-label*="add"]',
                'button[aria-label*="upload"]',
                'button[aria-label*="attach"]',
                '.material-symbols-outlined:has-text("add_circle")',
                '.upload-button',
                '[data-testid="upload-button"]'
            ]
            
            for selector in upload_button_selectors:
                try:
                    button = await self.instance.page.query_selector(selector)
                    if button and await button.is_visible():
                        print(f"🔘 找到上传按钮: {selector}")
                        await button.click()
                        await asyncio.sleep(1)
                        
                        # 再次尝试查找文件输入
                        file_input = await self.instance.page.query_selector('input[type="file"]')
                        if file_input:
                            await file_input.set_input_files(image_path)
                            print("✅ 通过点击按钮上传成功")
                            return True
                except Exception as e:
                    logger.debug(f"上传按钮 {selector} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"文件输入上传失败: {e}")
            return False
    
    async def try_file_chooser_upload(self, image_path: str):
        """尝试通过文件选择器监听上传图片"""
        try:
            print("📁 设置文件选择器监听...")
            
            # 设置文件选择器监听
            async def handle_file_chooser(file_chooser):
                await file_chooser.set_files(image_path)
                print("✅ 通过文件选择器上传成功")
                return True
            
            # 监听文件选择器
            self.instance.page.on("filechooser", handle_file_chooser)
            
            # 尝试点击可能触发文件选择的按钮
            trigger_selectors = [
                'button[aria-label*="Insert assets"]',
                'ms-add-chunk-menu button',
                'button:has(.material-symbols-outlined)',
                'button[iconname="add_circle"]'
            ]
            
            for selector in trigger_selectors:
                try:
                    button = await self.instance.page.query_selector(selector)
                    if button and await button.is_visible():
                        print(f"🔘 点击触发按钮: {selector}")
                        await button.click()
                        
                        # 等待文件选择器出现
                        await asyncio.sleep(2)
                        
                        # 检查是否上传成功
                        if await self.check_image_uploaded():
                            return True
                            
                except Exception as e:
                    logger.debug(f"触发按钮 {selector} 失败: {e}")
                    continue
            
            # 移除监听器
            self.instance.page.remove_listener("filechooser", handle_file_chooser)
            return False
            
        except Exception as e:
            logger.debug(f"文件选择器监听失败: {e}")
            return False
    
    async def try_drag_drop_upload(self, image_path: str, target_selector: str):
        """尝试通过拖拽上传图片"""
        try:
            print("🖱️ 模拟拖拽上传...")
            
            # 获取目标元素
            target_element = await self.instance.page.query_selector(target_selector)
            if not target_element:
                print("❌ 未找到拖拽目标元素")
                return False
            
            # 获取元素位置
            box = await target_element.bounding_box()
            if not box:
                print("❌ 无法获取元素位置")
                return False
            
            # 计算拖拽目标位置
            target_x = box['x'] + box['width'] / 2
            target_y = box['y'] + box['height'] / 2
            
            # 模拟拖拽事件
            await self.instance.page.evaluate("""
                async (args) => {
                    const { imagePath, targetX, targetY } = args;
                    
                    try {
                        // 创建模拟文件
                        const file = new File([''], 'test.png', { type: 'image/png' });
                        
                        // 创建拖拽事件
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        
                        // 获取目标元素
                        const target = document.elementFromPoint(targetX, targetY);
                        if (!target) {
                            console.log('未找到目标元素');
                            return false;
                        }
                        
                        // 触发拖拽事件序列
                        const dragEnterEvent = new DragEvent('dragenter', {
                            bubbles: true,
                            cancelable: true,
                            dataTransfer: dataTransfer
                        });
                        
                        const dragOverEvent = new DragEvent('dragover', {
                            bubbles: true,
                            cancelable: true,
                            dataTransfer: dataTransfer
                        });
                        
                        const dropEvent = new DragEvent('drop', {
                            bubbles: true,
                            cancelable: true,
                            dataTransfer: dataTransfer
                        });
                        
                        // 依次触发事件
                        target.dispatchEvent(dragEnterEvent);
                        target.dispatchEvent(dragOverEvent);
                        target.dispatchEvent(dropEvent);
                        
                        console.log('拖拽事件已触发');
                        return true;
                        
                    } catch (error) {
                        console.log('拖拽事件触发失败:', error);
                        return false;
                    }
                }
            """, {
                "imagePath": image_path,
                "targetX": target_x,
                "targetY": target_y
            })
            
            print("✅ 拖拽事件已触发")
            return True
            
        except Exception as e:
            logger.debug(f"拖拽上传失败: {e}")
            return False
    
    async def check_image_uploaded(self):
        """检查图片是否已上传"""
        try:
            # 查找图片预览元素
            image_preview_selectors = [
                'img[src*="blob:"]',
                'img[src*="data:image"]',
                '.image-preview',
                '[data-testid="image-preview"]',
                '.uploaded-image'
            ]
            
            for selector in image_preview_selectors:
                try:
                    element = await self.instance.page.query_selector(selector)
                    if element and await element.is_visible():
                        print("✅ 检测到图片预览")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"检查图片上传状态失败: {e}")
            return False
    
    async def setup_network_listener(self):
        """设置网络请求监听器"""
        try:
            # 监听网络响应
            async def handle_response(response):
                url = response.url
                if "GenerateContent" in url:
                    logger.info(f"检测到GenerateContent API调用: {url}")
                    try:
                        # 获取响应内容
                        response_text = await response.text()
                        logger.info("收到API响应")
                        
                        # 尝试解析JSON响应
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
                                print(f"\n🤖 AI回复: {ai_response}")
                            else:
                                print(f"\n⚠️  未能提取AI回复，响应长度: {len(str(response_data))}")
                                # 显示响应的前500个字符用于调试
                                response_preview = str(response_data)[:500]
                                logger.debug(f"响应预览: {response_preview}...")
                            
                        except json.JSONDecodeError:
                            logger.warning("响应不是有效的JSON格式")
                            print(f"\n⚠️  响应格式错误，内容长度: {len(response_text)}")
                            self.api_responses.append({
                                "url": url,
                                "status": response.status,
                                "data": response_text,
                                "timestamp": asyncio.get_event_loop().time()
                            })
                        
                        self.waiting_for_response = False
                        
                    except Exception as e:
                        logger.error(f"处理API响应时出错: {e}")
            
            # 监听网络请求
            async def handle_request(request):
                url = request.url
                if "GenerateContent" in url:
                    logger.info(f"检测到GenerateContent API请求: {url}")
                    try:
                        # 获取请求数据
                        post_data = request.post_data
                        if post_data:
                            logger.info("请求数据已发送")
                            self.waiting_for_response = True
                    except Exception as e:
                        logger.error(f"处理API请求时出错: {e}")
            
            # 绑定事件监听器
            self.instance.page.on("response", handle_response)
            self.instance.page.on("request", handle_request)
            
            logger.success("网络监听器设置完成")
            
        except Exception as e:
            logger.error(f"设置网络监听器失败: {e}")
    
    def extract_ai_response(self, response_data) -> Optional[str]:
        """从API响应中提取AI回复文本"""
        try:
            logger.debug(f"开始解析响应数据: {type(response_data)}")
            
            # 根据dom.txt中的响应结构解析
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
                    # 打印响应结构的前500字符用于调试
                    response_str = str(response_data)[:500]
                    logger.debug(f"响应结构预览: {response_str}...")
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
    
    def extract_images_from_response(self, response_data) -> list:
        """从API响应中提取base64编码的图片"""
        try:
            images = []
            self._find_images_recursive(response_data, images)
            
            logger.info(f"提取到 {len(images)} 张图片")
            return images
            
        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            return []
    
    def _find_images_recursive(self, data, images: list, depth=0):
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
            import base64
            decoded = base64.b64decode(data)
            
            # 检查是否以PNG文件头开始
            return decoded.startswith(b'\x89PNG\r\n\x1a\n')
            
        except Exception:
            return False
    
    async def navigate_to_ai_studio(self):
        """导航到AI Studio并等待用户登录"""
        try:
            logger.info("正在访问Google AI Studio...")
            success = await self.instance.goto("https://aistudio.google.com/")
            
            if not success:
                logger.error("访问AI Studio失败")
                return False
            
            # 等待页面加载
            await asyncio.sleep(5)
            
            # 尝试截图，如果失败就跳过
            try:
                await self.instance.screenshot("ai_studio_home.png")
            except Exception as e:
                logger.warning(f"截图失败，跳过: {e}")
            
            logger.success("成功访问AI Studio")
            
            # 检查登录状态和页面类型
            await self.check_page_status()
            
            return True
            
        except Exception as e:
            logger.error(f"访问AI Studio失败: {e}")
            return False
    
    async def check_login_status(self):
        """检查登录状态"""
        try:
            # 检查页面内容中是否包含邮箱地址
            page_content = await self.instance.page.content()
            
            # 检查是否包含Gmail邮箱地址
            import re
            email_pattern = r'[a-zA-Z0-9._%+-]+@gmail\.com'
            emails = re.findall(email_pattern, page_content)
            
            if emails:
                logger.success(f"检测到已登录账户: {emails[0]}")
                return True
            
            # 检查特定的登录元素
            login_indicators = [
                # 账户切换器容器
                '.account-switcher-container',
                'alkali-accountswitcher',
                # Google账户头像
                'connect-avatar img',
                'img.avatar',
                # 包含邮箱的span
                '.account-switcher-text',
                # Google账户按钮
                '.account-switcher-button'
            ]
            
            for selector in login_indicators:
                try:
                    element = await self.instance.page.query_selector(selector)
                    if element:
                        # 获取元素文本内容
                        try:
                            text_content = await element.inner_text()
                            if text_content and ("@gmail.com" in text_content or "@googlemail.com" in text_content):
                                logger.success(f"检测到已登录账户: {text_content.strip()}")
                                return True
                        except:
                            pass
                        
                        # 检查图片alt属性
                        try:
                            if await element.get_attribute("alt"):
                                alt_text = await element.get_attribute("alt")
                                if alt_text and ("@gmail.com" in alt_text or "@googlemail.com" in alt_text or "赵建" in alt_text):
                                    logger.success(f"检测到已登录账户: {alt_text}")
                                    return True
                        except:
                            pass
                        
                        # 检查图片src属性（Google头像通常包含googleusercontent）
                        try:
                            if await element.get_attribute("src"):
                                src = await element.get_attribute("src")
                                if src and "googleusercontent.com" in src:
                                    logger.success("检测到Google账户头像")
                                    return True
                        except:
                            pass
                        
                        logger.debug(f"找到登录相关元素: {selector}")
                        
                except Exception as e:
                    logger.debug(f"检查登录指标失败 {selector}: {e}")
                    continue
            
            # 检查是否有Google账户相关的aria-label
            try:
                google_account_elements = await self.instance.page.query_selector_all('[aria-label*="Google 账号"]')
                if google_account_elements:
                    logger.success("检测到Google账号元素")
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    async def check_page_status(self):
        """检查页面状态并自动处理"""
        try:
            logger.info("检查页面状态...")
            
            # 检查登录状态
            is_logged_in = await self.check_login_status()
            
            if is_logged_in:
                logger.success("检测到已登录状态")
                
                # 处理自动保存弹窗
                await self.handle_autosave_dialog()
                
                # 保存登录状态
                logger.info("保存登录状态...")
                await self.save_cookies()
                
                # 自动导航到生图页面
                logger.info("自动导航到生图页面...")
                target_url = "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image"
                
                success = await self.instance.goto(target_url)
                if success:
                    logger.success("成功导航到生图页面")
                    await asyncio.sleep(3)  # 等待页面加载
                    return True
                else:
                    logger.error("导航到生图页面失败")
                    return False
            else:
                logger.warning("未检测到登录状态，需要手动登录")
                logger.info("请在浏览器中登录Google账户，系统会自动检测登录状态")
                
                # 等待登录，每5秒检查一次
                max_wait_time = 300  # 最多等待5分钟
                check_interval = 5   # 每5秒检查一次
                
                for i in range(max_wait_time // check_interval):
                    await asyncio.sleep(check_interval)
                    
                    if await self.check_login_status():
                        logger.success("检测到登录成功！")
                        
                        # 处理自动保存弹窗
                        await self.handle_autosave_dialog()
                        
                        # 保存登录状态
                        logger.info("保存登录状态...")
                        await self.save_cookies()
                        
                        # 自动导航到生图页面
                        logger.info("自动导航到生图页面...")
                        target_url = "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image"
                        
                        success = await self.instance.goto(target_url)
                        if success:
                            logger.success("成功导航到生图页面")
                            await asyncio.sleep(3)  # 等待页面加载
                            return True
                        else:
                            logger.error("导航到生图页面失败")
                            return False
                
                logger.error("等待登录超时")
                return False
            
        except Exception as e:
            logger.error(f"检查页面状态失败: {e}")
            return False
    
    async def find_input_elements(self, max_attempts=3):
        """智能查找输入框和发送按钮"""
        try:
            logger.info("正在智能查找输入元素...")
            
            for attempt in range(max_attempts):
                logger.info(f"尝试查找元素 (第{attempt + 1}次)")
                
                # 先截图查看当前页面状态
                try:
                    await self.instance.screenshot(f"element_search_attempt_{attempt + 1}.png")
                except Exception as e:
                    logger.debug(f"截图失败: {e}")
                
                textarea_found = False
                button_found = False
                
                # 扩展的输入框选择器列表 - 基于新的DOM结构
                textarea_selectors = [
                    # 新的AI Studio结构
                    'ms-autosize-textarea textarea',
                    'ms-text-chunk textarea',
                    'textarea.textarea',
                    'textarea[aria-label*="Type something"]',
                    'textarea[aria-label*="tab to choose"]',
                    # 旧的选择器保持兼容
                    'textarea[placeholder*="prompt"]',
                    'textarea[placeholder*="Start typing"]',
                    'textarea[placeholder*="输入"]',
                    'textarea[aria-label*="prompt"]',
                    'textarea[aria-label*="输入"]',
                    # 通用选择器
                    'textarea',
                    'input[type="text"]',
                    '[contenteditable="true"]',
                    '[role="textbox"]'
                ]
                
                # 扩展的按钮选择器列表 - 基于新的DOM结构
                button_selectors = [
                    # 新的AI Studio结构
                    'ms-run-button button',
                    'button.run-button',
                    'button[aria-label="Run"]',
                    'button[type="submit"]',
                    # 旧的选择器保持兼容
                    'button[aria-label*="发送"]',
                    'button[aria-label*="Send"]',
                    'button:has-text("Run")',
                    'button:has-text("发送")',
                    'button:has-text("Send")',
                    '.send-button',
                    '.submit-button'
                ]
                
                # 查找输入框
                for selector in textarea_selectors:
                    try:
                        element = await self.instance.page.query_selector(selector)
                        if element:
                            # 检查元素是否可见和可用
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            
                            if is_visible and is_enabled:
                                logger.success(f"找到可用输入框: {selector}")
                                self.selectors["active_textarea"] = selector
                                textarea_found = True
                                break
                            else:
                                logger.debug(f"输入框不可用: {selector} (visible: {is_visible}, enabled: {is_enabled})")
                    except Exception as e:
                        logger.debug(f"检查输入框选择器失败 {selector}: {e}")
                        continue
                
                # 查找发送按钮
                for selector in button_selectors:
                    try:
                        element = await self.instance.page.query_selector(selector)
                        if element:
                            # 检查元素是否可见
                            is_visible = await element.is_visible()
                            
                            if is_visible:
                                logger.success(f"找到可见按钮: {selector}")
                                self.selectors["active_button"] = selector
                                button_found = True
                                break
                            else:
                                logger.debug(f"按钮不可见: {selector}")
                    except Exception as e:
                        logger.debug(f"检查按钮选择器失败 {selector}: {e}")
                        continue
                
                if textarea_found and button_found:
                    logger.success("成功找到所有必需元素")
                    return True
                
                # 如果常规方法没找到，尝试智能检测
                if not textarea_found or not button_found:
                    logger.info("常规方法未找到元素，尝试智能检测...")
                    if await self.find_elements_by_smart_detection():
                        logger.success("智能检测成功找到所有必需元素")
                        return True
                
                # 如果没找到，等待页面加载并重试
                if attempt < max_attempts - 1:
                    missing_elements = []
                    if not textarea_found:
                        missing_elements.append("输入框")
                    if not button_found:
                        missing_elements.append("发送按钮")
                    
                    logger.warning(f"未找到: {', '.join(missing_elements)}")
                    logger.info(f"等待页面加载，{3}秒后重试...")
                    
                    # 等待页面加载
                    await asyncio.sleep(3)
                    
                    # 尝试刷新页面
                    if attempt == max_attempts - 2:  # 最后一次尝试前刷新页面
                        logger.info("最后一次尝试前刷新页面...")
                        await self.instance.page.reload()
                        await asyncio.sleep(5)
            
            # 最终检查失败
            logger.error("无法找到必需的页面元素")
            logger.error("可能的原因：页面未完全加载、未登录或登录已过期、不在正确的对话页面、页面结构发生变化")
            
            return False
            
        except Exception as e:
            logger.error(f"查找输入元素失败: {e}")
            return False
    
    async def find_elements_by_smart_detection(self):
        """智能检测输入框和按钮"""
        try:
            logger.info("使用智能检测查找输入元素...")
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            # 使用JavaScript查找所有可能的输入框
            textarea_info = await self.instance.page.evaluate("""
                () => {
                    const textareas = [];
                    
                    // 查找所有textarea元素
                    document.querySelectorAll('textarea').forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 && 
                                        window.getComputedStyle(el).display !== 'none' &&
                                        window.getComputedStyle(el).visibility !== 'hidden';
                        
                        if (isVisible) {
                            textareas.push({
                                index: index,
                                tagName: el.tagName,
                                className: el.className,
                                placeholder: el.placeholder,
                                ariaLabel: el.getAttribute('aria-label'),
                                id: el.id,
                                disabled: el.disabled,
                                readonly: el.readOnly,
                                selector: `textarea:nth-of-type(${index + 1})`
                            });
                        }
                    });
                    
                    return textareas;
                }
            """)
            
            # 查找所有可能的按钮
            button_info = await self.instance.page.evaluate("""
                () => {
                    const buttons = [];
                    
                    // 查找所有button元素
                    document.querySelectorAll('button').forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 && 
                                        window.getComputedStyle(el).display !== 'none' &&
                                        window.getComputedStyle(el).visibility !== 'hidden';
                        
                        const text = el.textContent.trim().toLowerCase();
                        const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        
                        // 检查是否可能是运行/发送按钮
                        const isRunButton = text.includes('run') || text.includes('发送') || 
                                          ariaLabel.includes('run') || ariaLabel.includes('发送') ||
                                          el.type === 'submit';
                        
                        if (isVisible && isRunButton) {
                            buttons.push({
                                index: index,
                                tagName: el.tagName,
                                className: el.className,
                                textContent: el.textContent.trim(),
                                ariaLabel: el.getAttribute('aria-label'),
                                id: el.id,
                                disabled: el.disabled,
                                type: el.type,
                                selector: `button:nth-of-type(${index + 1})`
                            });
                        }
                    });
                    
                    return buttons;
                }
            """)
            
            logger.info(f"智能检测找到 {len(textarea_info)} 个输入框，{len(button_info)} 个按钮")
            
            # 选择最合适的输入框
            best_textarea = None
            for textarea in textarea_info:
                if not textarea['disabled'] and not textarea['readonly']:
                    best_textarea = textarea
                    break
            
            # 选择最合适的按钮
            best_button = None
            for button in button_info:
                if not button['disabled']:
                    best_button = button
                    break
            
            if best_textarea:
                self.selectors["active_textarea"] = best_textarea['selector']
                logger.success(f"智能检测找到输入框: {best_textarea['selector']}")
                
            if best_button:
                self.selectors["active_button"] = best_button['selector']
                logger.success(f"智能检测找到按钮: {best_button['selector']}")
            
            return best_textarea is not None and best_button is not None
            
        except Exception as e:
            logger.error(f"智能检测失败: {e}")
            return False
    
    async def ensure_on_image_generation_page(self):
        """确保当前页面是生图页面并刷新到初始状态"""
        try:
            logger.info("确保页面处于生图初始状态...")
            
            # 总是导航到生图页面，确保页面处于初始状态
            # 因为首次画图时URL可能不变，但页面内容已经有对话了
            if await self.navigate_to_new_image_chat():
                # 跳转后重新查找输入元素
                await self.find_input_elements()
                logger.info("页面已刷新到生图初始状态")
                return True
            else:
                logger.warning("刷新到生图页面失败")
                return False
                
        except Exception as e:
            logger.error(f"确保页面状态失败: {e}")
            return False

    async def send_message(self, message: str):
        """发送消息"""
        try:
            logger.info(f"正在发送消息: {message}")
            
            # 确保在正确的页面上
            if not await self.ensure_on_image_generation_page():
                logger.warning("无法确保在正确的生图页面上，但继续执行")
            
            # 清空之前的响应
            self.api_responses.clear()
            
            # 填充文本到输入框
            textarea_selector = self.selectors.get("active_textarea")
            if not textarea_selector:
                logger.error("未找到活动的输入框选择器")
                return False
            
            # 清空输入框并填充新文本
            await self.instance.page.fill(textarea_selector, "")
            await asyncio.sleep(0.5)
            await self.instance.page.fill(textarea_selector, message)
            await asyncio.sleep(1)
            
            logger.success(f"文本已填充到输入框")
            
            # 点击发送按钮
            button_selector = self.selectors.get("active_button")
            if not button_selector:
                logger.error("未找到活动的发送按钮选择器")
                return False
            
            # 检查按钮是否可用
            button_element = await self.instance.page.query_selector(button_selector)
            if button_element:
                is_disabled = await button_element.get_attribute("disabled")
                if is_disabled:
                    logger.warning("发送按钮当前被禁用，等待启用...")
                    # 等待按钮启用
                    for i in range(10):
                        await asyncio.sleep(0.5)
                        is_disabled = await button_element.get_attribute("disabled")
                        if not is_disabled:
                            break
                    
                    if is_disabled:
                        logger.error("发送按钮仍然被禁用")
                        return False
            
            await self.instance.page.click(button_selector)
            logger.success("已点击发送按钮")
            
            # 等待API响应
            print("⏳ 等待AI响应...")
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
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    async def run_interactive_session(self):
        """运行交互会话"""
        try:
            print("🚀 启动Google AI Studio交互测试")
            print("=" * 50)
            
            # 初始化
            if not await self.setup():
                return False
            
            # 导航到AI Studio
            if not await self.navigate_to_ai_studio():
                return False
            
            # 查找输入元素
            if not await self.find_input_elements():
                logger.error("无法找到必要的输入元素，请检查页面是否正确加载")
                return False
            
            print("\n✅ 初始化完成！现在可以开始对话了")
            print("💡 可用命令:")
            print("  • 'quit' 或 'exit' - 退出程序并保存登录状态")
            print("  • 'screenshot' - 截图当前页面")
            print("  • 'save' - 手动保存登录状态")
            print("  • '上传图片' - 上传test.png并输入描述文字")
            print("  • '新会话' - 导航到新的生图页面并设置比例（不删除当前对话）")
            print("  • '删除对话' - 删除当前对话")
            print("  • '设置比例 [比例]' - 设置图片比例（如：设置比例 16:9）")
            print("  • '任务清理' - 删除当前对话并导航到新页面（任务完成后使用）")
            print("  • 直接输入文本 - 发送给AI")
            print("💾 登录状态会自动保存为cookies文件")
            print("📸 确保test.png文件在当前目录中")
            print("📐 支持的比例: Auto, 1:1, 9:16, 16:9, 3:4, 4:3, 3:2, 2:3, 5:4, 4:5, 21:9")
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
                        await self.upload_image_and_text()
                        continue
                    
                    # 检查新会话命令
                    if user_input.lower() in ['新会话', 'new session', 'new']:
                        success = await self.prepare_new_image_session()
                        if success:
                            print("✅ 新会话准备完成")
                        else:
                            print("❌ 新会话准备失败")
                        continue
                    
                    # 检查删除对话命令
                    if user_input.lower() in ['删除对话', 'delete conversation', 'delete']:
                        success = await self.delete_current_conversation()
                        if success:
                            print("✅ 对话删除成功")
                        else:
                            print("❌ 对话删除失败")
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
                    
                    # 检查任务清理命令
                    if user_input.lower() in ['任务清理', 'cleanup', 'task cleanup']:
                        success = await self.cleanup_after_task()
                        if success:
                            print("✅ 任务清理完成")
                        else:
                            print("❌ 任务清理失败")
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
    
    async def navigate_to_new_image_chat(self, check_initial_page: bool = True):
        """导航到新的生图对话页面"""
        try:
            logger.info("导航到新的生图对话页面...")
            target_url = "https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image"
            
            # 检查当前页面是否已经是目标页面
            current_url = self.instance.page.url
            if check_initial_page and target_url in current_url:
                logger.info("当前页面已经是目标页面")
                # 即使是目标页面，也要检查弹窗
                await self.handle_autosave_dialog()
                return True
            
            # 导航到目标页面
            success = await self.instance.goto(target_url)
            if not success:
                logger.error("导航到新的生图对话页面失败")
                return False
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 处理可能出现的自动保存弹窗
            await self.handle_autosave_dialog()
            
            logger.success("成功导航到新的生图对话页面")
            return True
            
        except Exception as e:
            logger.error(f"导航到新的生图对话页面失败: {e}")
            return False
    
    async def delete_current_conversation(self):
        """删除当前对话的完整流程"""
        try:
            logger.info("开始删除当前对话...")
            
            # 步骤1: 点击更多操作按钮
            more_button_selector = 'button[aria-label="View more actions"][iconname="more_vert"]'
            
            try:
                await self.instance.page.wait_for_selector(more_button_selector, timeout=5000)
                await self.instance.page.click(more_button_selector)
                logger.info("已点击更多操作按钮")
                await asyncio.sleep(2)  # 等待2秒让菜单完全展开
            except Exception as e:
                logger.warning(f"点击更多操作按钮失败: {e}")
                return False
            
            # 步骤2: 检查删除按钮状态并点击
            delete_button_selector = 'button[data-test-delete=""]'
            
            try:
                await self.instance.page.wait_for_selector(delete_button_selector, timeout=5000)
                
                # 检查删除按钮是否被禁用
                delete_button = await self.instance.page.query_selector(delete_button_selector)
                is_disabled = await delete_button.get_attribute("disabled")
                
                if is_disabled:
                    logger.info("删除按钮被禁用，可能是首次对话或没有对话内容")
                    return False
                
                await self.instance.page.click(delete_button_selector)
                logger.info("已点击删除按钮")
                await asyncio.sleep(2)  # 等待2秒让确认对话框出现
            except Exception as e:
                logger.warning(f"点击删除按钮失败: {e}")
                return False
            
            # 步骤3: 确认删除
            confirm_delete_selector = 'button.ms-button-primary:has-text("Delete")'
            
            try:
                await self.instance.page.wait_for_selector(confirm_delete_selector, timeout=5000)
                await self.instance.page.click(confirm_delete_selector)
                logger.info("已确认删除")
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"确认删除失败: {e}")
                return False
            
            logger.success("成功删除当前对话")
            return True
            
        except Exception as e:
            logger.error(f"删除当前对话失败: {e}")
            return False
    
    async def set_aspect_ratio(self, ratio: str = "Auto"):
        """设置图片比例"""
        try:
            logger.info(f"设置图片比例为: {ratio}")
            
            # 点击比例设置区域
            aspect_ratio_selector = 'div[mattooltip="Aspect ratio of the generated images"]'
            
            try:
                await self.instance.page.wait_for_selector(aspect_ratio_selector, timeout=5000)
                await self.instance.page.click(aspect_ratio_selector)
                logger.info("已点击比例设置区域")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"点击比例设置区域失败: {e}")
                return False
            
            # 选择对应的比例选项
            ratio_option_selector = f'mat-option:has-text("{ratio}")'
            
            try:
                await self.instance.page.wait_for_selector(ratio_option_selector, timeout=5000)
                await self.instance.page.click(ratio_option_selector)
                logger.info(f"已选择比例: {ratio}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"选择比例失败: {e}")
                return False
            
            logger.success(f"成功设置图片比例为: {ratio}")
            return True
            
        except Exception as e:
            logger.error(f"设置图片比例失败: {e}")
            return False
    
    async def prepare_new_image_session(self, aspect_ratio: str = "Auto"):
        """准备新的生图会话（不删除当前对话）"""
        try:
            logger.info("开始准备新的生图会话...")
            
            # 1. 导航到新的生图对话页面
            if not await self.navigate_to_new_image_chat():
                return False
            
            # 2. 设置图片比例
            if not await self.set_aspect_ratio(aspect_ratio):
                logger.warning("设置图片比例失败，但继续执行")
            
            # 3. 重新查找输入元素
            if not await self.find_input_elements():
                logger.error("无法找到输入元素")
                return False
            
            logger.success("新的生图会话准备完成")
            return True
            
        except Exception as e:
            logger.error(f"准备新的生图会话失败: {e}")
            return False
    
    async def cleanup_after_task(self):
        """任务完成后的清理工作"""
        try:
            logger.info("开始任务完成后的清理工作...")
            
            # 1. 尝试删除当前对话
            delete_success = await self.delete_current_conversation()
            if delete_success:
                logger.info("当前对话已删除")
            else:
                logger.info("删除当前对话失败（可能是首次对话或按钮被禁用），直接跳转到新页面")
            
            # 2. 无论删除是否成功，都导航到新的生图对话页面刷新状态
            logger.info("导航到新的生图页面，刷新到初始状态...")
            if await self.navigate_to_new_image_chat(check_initial_page=False):
                logger.info("已导航到新的生图页面，为下次任务做准备")
                
                # 重新查找输入元素，确保页面功能正常
                if await self.find_input_elements():
                    logger.info("页面元素重新定位成功")
                else:
                    logger.warning("页面元素重新定位失败")
            else:
                logger.warning("导航到新页面失败")
            
            logger.success("任务完成后的清理工作完成")
            return True
            
        except Exception as e:
            logger.error(f"任务完成后的清理工作失败: {e}")
            return False
    
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
    test = AIStudioInteractiveClient()
    await test.run_interactive_session()


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
