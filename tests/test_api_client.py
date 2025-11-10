#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio 图片生成API测试客户端
用于测试图片生成服务的功能
"""

import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Optional

import aiohttp
import requests
from loguru import logger


class AIStudioAPIClient:
    """AI Studio API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8812"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片文件编码为base64字符串"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 编码为base64
            b64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64_data}"
            
        except Exception as e:
            logger.error(f"编码图片失败: {e}")
            return None
    
    def save_base64_image(self, b64_data: str, output_path: str):
        """将base64图片数据保存为文件"""
        try:
            # 移除data:image/png;base64,前缀（如果存在）
            if b64_data.startswith('data:image'):
                b64_data = b64_data.split(',')[1]
            
            # 解码base64数据
            image_data = base64.b64decode(b64_data)
            
            # 保存文件
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            logger.success(f"图片已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            return False
    
    async def check_health(self) -> bool:
        """检查API服务健康状态"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"API服务状态: {data}")
                    return True
                else:
                    logger.error(f"健康检查失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"健康检查异常: {e}")
            return False
    
    async def generate_image_async(self, prompt: str, reference_image_path: Optional[str] = None) -> dict:
        """异步生成图片"""
        try:
            # 准备请求数据
            request_data = {
                "prompt": prompt
            }
            
            # 如果有参考图片，编码为base64
            if reference_image_path and Path(reference_image_path).exists():
                logger.info(f"编码参考图片: {reference_image_path}")
                reference_b64 = self.encode_image_to_base64(reference_image_path)
                if reference_b64:
                    request_data["reference_image_b64"] = reference_b64
                else:
                    logger.warning("参考图片编码失败，将只使用文本提示")
            
            logger.info(f"发送生成请求: {prompt[:50]}...")
            
            # 发送请求
            async with self.session.post(
                f"{self.base_url}/generate",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=120)  # 2分钟超时
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.success("图片生成请求成功")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"生成请求失败: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "message": f"HTTP {response.status}: {error_text}"
                    }
                    
        except asyncio.TimeoutError:
            logger.error("请求超时")
            return {
                "success": False,
                "message": "请求超时"
            }
        except Exception as e:
            logger.error(f"生成请求异常: {e}")
            return {
                "success": False,
                "message": f"请求异常: {str(e)}"
            }
    
    def generate_image_sync(self, prompt: str, reference_image_path: Optional[str] = None) -> dict:
        """同步生成图片（使用requests）"""
        try:
            # 准备请求数据
            request_data = {
                "prompt": prompt
            }
            
            # 如果有参考图片，编码为base64
            if reference_image_path and Path(reference_image_path).exists():
                logger.info(f"编码参考图片: {reference_image_path}")
                reference_b64 = self.encode_image_to_base64(reference_image_path)
                if reference_b64:
                    request_data["reference_image_b64"] = reference_b64
                else:
                    logger.warning("参考图片编码失败，将只使用文本提示")
            
            logger.info(f"发送生成请求: {prompt[:50]}...")
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/generate",
                json=request_data,
                timeout=120  # 2分钟超时
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.success("图片生成请求成功")
                return result
            else:
                logger.error(f"生成请求失败: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("请求超时")
            return {
                "success": False,
                "message": "请求超时"
            }
        except Exception as e:
            logger.error(f"生成请求异常: {e}")
            return {
                "success": False,
                "message": f"请求异常: {str(e)}"
            }


async def test_async_api():
    """测试异步API调用"""
    logger.info("=== 开始异步API测试 ===")
    
    async with AIStudioAPIClient() as client:
        # 1. 健康检查
        logger.info("1. 检查API服务状态...")
        if not await client.check_health():
            logger.error("API服务不可用，请先启动服务")
            return
        
        # # 2. 测试纯文本生成
        # logger.info("2. 测试纯文本生成...")
        # result = await client.generate_image_async(
        #     prompt="画一只可爱的小猫咪，卡通风格，彩色"
        # )
        
        # if result.get("success"):
        #     logger.success(f"任务ID: {result.get('task_id')}")
        #     logger.info(f"AI回复: {result.get('ai_text_response')}")
            
        #     # 保存生成的图片
        #     images = result.get("generated_images", [])
        #     for i, img_b64 in enumerate(images):
        #         output_path = f"generated_image_text_only_{i+1}.png"
        #         client.save_base64_image(img_b64, output_path)
        # else:
        #     logger.error(f"生成失败: {result.get('message')}")
        
        # # 等待一段时间再进行下一个测试
        # await asyncio.sleep(5)
        
        # 3. 测试带参考图片的生成
        logger.info("3. 测试带参考图片的生成...")
        reference_image = "test.png"
        
        if Path(reference_image).exists():
            result = await client.generate_image_async(
                prompt="参考这张图片风格，生成一个男孩的图片",
                reference_image_path=reference_image
            )
            
            if result.get("success"):
                logger.success(f"任务ID: {result.get('task_id')}")
                logger.info(f"AI回复: {result.get('ai_text_response')}")
                
                # 保存生成的图片
                images = result.get("generated_images", [])
                for i, img_b64 in enumerate(images):
                    output_path = f"generated_image_with_reference_{i+1}.png"
                    client.save_base64_image(img_b64, output_path)
            else:
                logger.error(f"生成失败: {result.get('message')}")
        else:
            logger.warning(f"参考图片 {reference_image} 不存在，跳过测试")


def test_sync_api():
    """测试同步API调用"""
    logger.info("=== 开始同步API测试 ===")
    
    client = AIStudioAPIClient()
    
    # 测试纯文本生成
    logger.info("测试纯文本生成...")
    result = client.generate_image_sync(
        prompt="画一朵美丽的玫瑰花，写实风格"
    )
    
    if result.get("success"):
        logger.success(f"任务ID: {result.get('task_id')}")
        logger.info(f"AI回复: {result.get('ai_text_response')}")
        
        # 保存生成的图片
        images = result.get("generated_images", [])
        for i, img_b64 in enumerate(images):
            output_path = f"generated_image_sync_{i+1}.png"
            client.save_base64_image(img_b64, output_path)
    else:
        logger.error(f"生成失败: {result.get('message')}")


def main():
    """主函数"""
    print("🤖 AI Studio 图片生成API测试客户端")
    print("=" * 50)
    print("📋 测试功能:")
    print("  • API服务健康检查")
    print("  • 纯文本图片生成")
    print("  • 带参考图片的生成")
    print("  • 生成图片保存到本地")
    print("=" * 50)
    
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}\n"
    )
    
    try:
        # 选择测试模式
        print("\n请选择测试模式:")
        print("1. 异步测试 (推荐)")
        print("2. 同步测试")
        print("3. 两种都测试")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            asyncio.run(test_async_api())
        elif choice == "2":
            test_sync_api()
        elif choice == "3":
            asyncio.run(test_async_api())
            print("\n" + "="*50)
            test_sync_api()
        else:
            print("无效选择，默认运行异步测试")
            asyncio.run(test_async_api())
        
        print("\n✅ 测试完成！")
        print("📸 请检查当前目录中生成的图片文件")
        
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")


if __name__ == "__main__":
    main()
