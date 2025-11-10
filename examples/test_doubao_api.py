#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包API测试脚本
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


async def test_doubao_api():
    """测试豆包API"""
    base_url = "http://localhost:8814"
    
    async with aiohttp.ClientSession() as session:
        # 1. 测试健康检查
        print("🔍 测试健康检查...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ 健康检查通过: {health_data['message']}")
                    print(f"   浏览器实例: {health_data['browser_instances']}")
                else:
                    print(f"❌ 健康检查失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 无法连接到豆包API服务: {e}")
            print("💡 请确保豆包API服务已启动 (python doubao_main.py)")
            return False
        
        # 2. 测试图片生成
        print("\n🎨 测试图片生成...")
        try:
            test_request = {
                "prompt": "一只可爱的小猫咪，卡通风格",
                "aspect_ratio": "1:1"
            }
            
            async with session.post(
                f"{base_url}/generate",
                json=test_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result["success"]:
                        print(f"✅ 图片生成请求成功")
                        print(f"   任务ID: {result['task_id']}")
                        print(f"   消息: {result['message']}")
                        if result.get("generated_images"):
                            print(f"   生成图片数量: {len(result['generated_images'])}")
                        if result.get("ai_text_response"):
                            print(f"   AI回复: {result['ai_text_response']}")
                    else:
                        print(f"⚠️  图片生成失败: {result['message']}")
                else:
                    print(f"❌ 图片生成请求失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ 图片生成测试失败: {e}")
        
        print("\n📋 测试完成")
        return True


def main():
    """主函数"""
    print("🚀 豆包API测试程序")
    print("=" * 50)
    print("📋 测试项目:")
    print("  • 健康检查")
    print("  • 图片生成接口")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_doubao_api())
        if result:
            print("\n✅ 所有测试完成")
        else:
            print("\n❌ 测试失败")
            return 1
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"❌ 测试运行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
