#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的图片生成测试脚本
用于快速验证API功能
"""

import base64
import requests
import time
from pathlib import Path
from loguru import logger


def save_base64_image(b64_data: str, output_path: str):
    """保存base64图片到文件"""
    try:
        # 移除data:image前缀（如果存在）
        if b64_data.startswith('data:image'):
            b64_data = b64_data.split(',')[1]
        
        # 解码并保存
        image_data = base64.b64decode(b64_data)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"✅ 图片已保存: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 保存图片失败: {e}")
        return False


def test_generate_image():
    """测试图片生成"""
    api_url = "http://localhost:8812"
    
    # 检查服务状态
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API服务未启动，请先运行: python start_api_server.py")
            return
        print("✅ API服务正常运行")
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        print("请先运行: python start_api_server.py")
        return
    
    # 测试文本生成
    print("\n🎨 开始测试图片生成...")
    
    test_prompt = "画一个穿着宇航服的宇航员，站在地球上，卡通风格，色彩鲜艳"
    
    request_data = {
        "prompt": test_prompt
    }
    
    print(f"📝 提示词: {test_prompt}")
    print("⏳ 正在生成图片，请稍候...")
    
    try:
        # 发送生成请求
        response = requests.post(
            f"{api_url}/generate",
            json=request_data,
            timeout=120  # 2分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print("🎉 图片生成成功！")
                print(f"📋 任务ID: {result.get('task_id')}")
                
                # 显示AI回复
                ai_response = result.get("ai_text_response")
                if ai_response:
                    print(f"🤖 AI回复: {ai_response}")
                
                # 保存生成的图片
                images = result.get("generated_images", [])
                if images:
                    print(f"📸 生成了 {len(images)} 张图片")
                    for i, img_b64 in enumerate(images):
                        output_path = f"generated_simple_test_{i+1}.png"
                        save_base64_image(img_b64, output_path)
                else:
                    print("⚠️ 未生成图片")
            else:
                print(f"❌ 生成失败: {result.get('message')}")
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时，生成可能需要更长时间")
    except Exception as e:
        print(f"❌ 请求异常: {e}")


def main():
    """主函数"""
    print("🎨 AI Studio 图片生成简单测试")
    print("=" * 40)
    
    # 配置日志
    logger.remove()
    
    try:
        test_generate_image()
        
        print("\n" + "=" * 40)
        print("✅ 测试完成！")
        print("📁 请检查当前目录中的生成图片")
        
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")


if __name__ == "__main__":
    main()
