#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带有比例配置的API调用
演示如何使用新增的aspect_ratio参数
"""

import requests
import json
import base64
from pathlib import Path


def test_api_with_aspect_ratio():
    """测试API的比例配置功能"""
    
    # API服务地址
    api_url = "http://localhost:8812"
    
    print("🚀 测试AI Studio API的新比例配置功能")
    print("=" * 50)
    
    # 1. 健康检查
    print("\n1️⃣ 检查API服务状态...")
    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ API服务正常运行")
            print(f"   📊 AI Studio初始化状态: {health_data.get('ai_studio_initialized')}")
            print(f"   🌐 浏览器状态: {health_data.get('browser_ready')}")
        else:
            print(f"   ❌ API服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 无法连接到API服务: {e}")
        print("   💡 请确保API服务已启动: python scripts/start_api_server.py")
        return False
    
    # 2. 测试不同比例的图片生成
    test_cases = [
        {
            "prompt": "一只可爱的小猫在花园里玩耍",
            "aspect_ratio": "Auto",
            "description": "自动比例"
        },
        {
            "prompt": "现代城市的夜景，霓虹灯闪烁",
            "aspect_ratio": "16:9",
            "description": "宽屏比例"
        },
        {
            "prompt": "一朵美丽的玫瑰花特写",
            "aspect_ratio": "1:1",
            "description": "正方形比例"
        },
        {
            "prompt": "高耸的山峰和云海",
            "aspect_ratio": "9:16",
            "description": "竖屏比例"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ 测试{test_case['description']} ({test_case['aspect_ratio']})")
        print(f"   提示词: {test_case['prompt']}")
        
        # 构建请求数据
        request_data = {
            "prompt": test_case["prompt"],
            "aspect_ratio": test_case["aspect_ratio"]
        }
        
        try:
            # 发送生成请求
            print("   📤 发送生成请求...")
            response = requests.post(
                f"{api_url}/generate",
                json=request_data,
                timeout=300  # 5分钟超时
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    print(f"   ✅ 生成成功!")
                    print(f"   🆔 任务ID: {result['task_id']}")
                    
                    # 检查生成的图片
                    if result.get("generated_images"):
                        print(f"   🖼️  生成了 {len(result['generated_images'])} 张图片")
                        
                        # 保存第一张图片作为示例
                        if result["generated_images"]:
                            try:
                                image_data = base64.b64decode(result["generated_images"][0])
                                output_path = Path(f"generated_image_{test_case['aspect_ratio'].replace(':', '_')}.png")
                                with open(output_path, 'wb') as f:
                                    f.write(image_data)
                                print(f"   💾 图片已保存: {output_path}")
                            except Exception as e:
                                print(f"   ⚠️  保存图片失败: {e}")
                    
                    # 显示AI文本回复
                    if result.get("ai_text_response"):
                        print(f"   💬 AI回复: {result['ai_text_response'][:100]}...")
                else:
                    print(f"   ❌ 生成失败: {result['message']}")
            else:
                print(f"   ❌ API请求失败: {response.status_code}")
                print(f"   📄 响应内容: {response.text}")
                
        except requests.exceptions.Timeout:
            print("   ⏰ 请求超时，生成可能需要更长时间")
        except Exception as e:
            print(f"   ❌ 请求出错: {e}")
    
    print(f"\n🎉 API比例配置测试完成!")
    print("💡 支持的比例选项:")
    print("   Auto, 1:1, 9:16, 16:9, 3:4, 4:3, 3:2, 2:3, 5:4, 4:5, 21:9")


def test_file_upload_with_aspect_ratio():
    """测试文件上传接口的比例配置"""
    
    api_url = "http://localhost:8812"
    
    print("\n📁 测试文件上传接口的比例配置...")
    
    # 检查是否有测试图片
    test_image_path = Path("test.png")
    if not test_image_path.exists():
        print("   ⚠️  未找到test.png，跳过文件上传测试")
        return
    
    try:
        # 准备文件和数据
        with open(test_image_path, 'rb') as f:
            files = {'reference_image': ('test.png', f, 'image/png')}
            data = {
                'prompt': '基于这张图片，生成一个更加艺术化的版本',
                'aspect_ratio': '4:3'
            }
            
            print("   📤 发送文件上传请求...")
            response = requests.post(
                f"{api_url}/generate-with-file",
                files=files,
                data=data,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    print(f"   ✅ 文件上传生成成功!")
                    print(f"   🆔 任务ID: {result['task_id']}")
                    if result.get("generated_images"):
                        print(f"   🖼️  生成了 {len(result['generated_images'])} 张图片")
                else:
                    print(f"   ❌ 文件上传生成失败: {result['message']}")
            else:
                print(f"   ❌ 文件上传请求失败: {response.status_code}")
                
    except Exception as e:
        print(f"   ❌ 文件上传测试出错: {e}")


if __name__ == "__main__":
    print("🎯 AI Studio API 比例配置测试")
    print("📋 确保API服务已启动: python scripts/start_api_server.py")
    print("🔍 API会自动检查当前页面，如果不是生图页面会自动跳转")
    print("=" * 60)
    
    # 测试基本API
    test_api_with_aspect_ratio()
    
    # 测试文件上传API
    test_file_upload_with_aspect_ratio()
    
    print("\n✨ 所有测试完成!")
