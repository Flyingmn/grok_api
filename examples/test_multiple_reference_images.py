#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多个参考图片的API调用示例
"""

import asyncio
import base64
import json
from pathlib import Path
import aiohttp

async def test_multiple_reference_images():
    """测试多个参考图片的生成"""
    
    # API服务地址
    api_url = "http://localhost:8812/generate"
    
    # 准备测试数据
    prompt = "根据这些参考图片，生成一个融合了它们风格特点的新图片"
    
    # 模拟多个参考图片的base64数据（这里使用占位符）
    # 在实际使用中，您需要将真实图片转换为base64
    reference_images = [
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",  # 1x1像素的透明PNG
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="   # 另一个1x1像素的透明PNG
    ]
    
    # 构建请求数据
    request_data = {
        "prompt": prompt,
        "reference_images_b64": reference_images,
        "aspect_ratio": "16:9"
    }
    
    print(f"🚀 开始测试多个参考图片生成...")
    print(f"📝 提示词: {prompt}")
    print(f"🖼️ 参考图片数量: {len(reference_images)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 请求成功!")
                    print(f"📋 任务ID: {result.get('task_id')}")
                    print(f"💬 消息: {result.get('message')}")
                    
                    if result.get('success'):
                        generated_images = result.get('generated_images', [])
                        print(f"🎨 生成图片数量: {len(generated_images)}")
                        
                        ai_response = result.get('ai_text_response')
                        if ai_response:
                            print(f"🤖 AI回复: {ai_response}")
                    else:
                        print(f"❌ 生成失败: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 请求失败 (状态码: {response.status}): {error_text}")
                    
    except Exception as e:
        print(f"❌ 请求异常: {e}")

async def test_file_upload_multiple():
    """测试多个文件上传的生成"""
    
    # API服务地址
    api_url = "http://localhost:8812/generate-with-file"
    
    print(f"🚀 开始测试多个文件上传生成...")
    
    # 创建测试用的小图片文件
    test_images = []
    for i in range(2):
        image_path = Path(f"test_image_{i}.png")
        # 创建一个简单的1x1像素PNG图片
        png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
        with open(image_path, 'wb') as f:
            f.write(png_data)
        test_images.append(image_path)
    
    try:
        # 准备表单数据
        data = aiohttp.FormData()
        data.add_field('prompt', '根据这些参考图片生成新的艺术作品')
        data.add_field('aspect_ratio', '1:1')
        
        # 添加多个图片文件
        for image_path in test_images:
            with open(image_path, 'rb') as f:
                data.add_field('reference_images', f.read(), 
                             filename=image_path.name, 
                             content_type='image/png')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 文件上传请求成功!")
                    print(f"📋 任务ID: {result.get('task_id')}")
                    print(f"💬 消息: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 文件上传请求失败 (状态码: {response.status}): {error_text}")
                    
    except Exception as e:
        print(f"❌ 文件上传请求异常: {e}")
    finally:
        # 清理测试文件
        for image_path in test_images:
            if image_path.exists():
                image_path.unlink()
                print(f"🗑️ 已清理测试文件: {image_path}")

async def test_backward_compatibility():
    """测试向后兼容性（单个参考图片）"""
    
    api_url = "http://localhost:8812/generate"
    
    print(f"🚀 开始测试向后兼容性...")
    
    # 使用旧的单个参考图片字段
    request_data = {
        "prompt": "根据参考图片生成类似风格的新图片",
        "reference_image_b64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "aspect_ratio": "Auto"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 向后兼容性测试成功!")
                    print(f"📋 任务ID: {result.get('task_id')}")
                    print(f"💬 消息: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ 向后兼容性测试失败 (状态码: {response.status}): {error_text}")
                    
    except Exception as e:
        print(f"❌ 向后兼容性测试异常: {e}")

async def main():
    """主函数"""
    print("=" * 60)
    print("🎨 AI Studio 多参考图片API测试")
    print("=" * 60)
    
    # 测试多个参考图片
    await test_multiple_reference_images()
    print("\n" + "-" * 40 + "\n")
    
    # 测试多个文件上传
    await test_file_upload_multiple()
    print("\n" + "-" * 40 + "\n")
    
    # 测试向后兼容性
    await test_backward_compatibility()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
