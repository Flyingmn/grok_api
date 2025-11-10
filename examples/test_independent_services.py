#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立服务测试脚本
验证AI Studio和豆包服务的独立性
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


async def test_service_independence():
    """测试服务独立性"""
    print("🔍 测试AI Studio和豆包服务的独立性")
    print("=" * 60)
    
    # 测试AI Studio服务
    print("\n📋 测试AI Studio服务...")
    ai_studio_healthy = await test_service_health("AI Studio", "http://localhost:8812")
    
    # 测试豆包服务
    print("\n📋 测试豆包服务...")
    doubao_healthy = await test_service_health("豆包", "http://localhost:8814")
    
    # 测试浏览器实例独立性
    print("\n🔍 测试浏览器实例独立性...")
    if ai_studio_healthy and doubao_healthy:
        await test_browser_instance_independence()
    else:
        print("⚠️  部分服务不可用，跳过实例独立性测试")
    
    print("\n📊 测试总结:")
    print(f"  • AI Studio服务: {'✅ 正常' if ai_studio_healthy else '❌ 异常'}")
    print(f"  • 豆包服务: {'✅ 正常' if doubao_healthy else '❌ 异常'}")
    
    return ai_studio_healthy and doubao_healthy


async def test_service_health(service_name: str, base_url: str) -> bool:
    """测试单个服务的健康状态"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ {service_name}服务正常")
                    print(f"   状态: {health_data['status']}")
                    print(f"   浏览器实例: {health_data['browser_instances']}")
                    print(f"   并发能力: {health_data['concurrency_capacity']}")
                    return True
                else:
                    print(f"❌ {service_name}服务异常: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ 无法连接到{service_name}服务: {e}")
        return False


async def test_browser_instance_independence():
    """测试浏览器实例独立性"""
    try:
        async with aiohttp.ClientSession() as session:
            # 获取AI Studio实例列表
            async with session.get("http://localhost:8813/api/instances") as response:
                if response.status == 200:
                    ai_studio_data = await response.json()
                    ai_studio_instances = ai_studio_data.get("instances", [])
                    print(f"📊 AI Studio实例数量: {len(ai_studio_instances)}")
                else:
                    print("❌ 无法获取AI Studio实例列表")
                    return
            
            # 获取豆包实例列表
            async with session.get("http://localhost:8815/api/instances") as response:
                if response.status == 200:
                    doubao_data = await response.json()
                    doubao_instances = doubao_data.get("instances", [])
                    print(f"📊 豆包实例数量: {len(doubao_instances)}")
                else:
                    print("❌ 无法获取豆包实例列表")
                    return
            
            # 检查实例ID是否重复
            ai_studio_ids = {instance["instance_id"] for instance in ai_studio_instances}
            doubao_ids = {instance["instance_id"] for instance in doubao_instances}
            
            overlap = ai_studio_ids & doubao_ids
            if overlap:
                print(f"⚠️  发现重复的实例ID: {overlap}")
            else:
                print("✅ 实例ID完全独立，无重复")
            
            # 检查服务类型
            ai_studio_types = {instance.get("service_type", "unknown") for instance in ai_studio_instances}
            doubao_types = {instance.get("service_type", "unknown") for instance in doubao_instances}
            
            print(f"📊 AI Studio实例类型: {ai_studio_types}")
            print(f"📊 豆包实例类型: {doubao_types}")
            
            if "AI_Studio" in ai_studio_types and "Doubao" in doubao_types:
                print("✅ 服务类型标识正确")
            else:
                print("⚠️  服务类型标识可能有问题")
                
    except Exception as e:
        print(f"❌ 测试浏览器实例独立性失败: {e}")


async def test_concurrent_requests():
    """测试并发请求处理"""
    print("\n🚀 测试并发请求处理...")
    
    # 创建测试请求
    ai_studio_request = {
        "prompt": "AI Studio测试：一只可爱的小猫",
        "aspect_ratio": "1:1"
    }
    
    doubao_request = {
        "prompt": "豆包测试：一只可爱的小狗",
        "aspect_ratio": "1:1"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 同时发送请求到两个服务
            tasks = [
                send_generate_request(session, "AI Studio", "http://localhost:8812", ai_studio_request),
                send_generate_request(session, "豆包", "http://localhost:8814", doubao_request)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                service_name = ["AI Studio", "豆包"][i]
                if isinstance(result, Exception):
                    print(f"❌ {service_name}请求失败: {result}")
                else:
                    print(f"✅ {service_name}请求成功: {result['message']}")
                    
    except Exception as e:
        print(f"❌ 并发请求测试失败: {e}")


async def send_generate_request(session, service_name: str, base_url: str, request_data: dict):
    """发送生成请求"""
    async with session.post(
        f"{base_url}/generate",
        json=request_data,
        headers={"Content-Type": "application/json"}
    ) as response:
        if response.status == 200:
            result = await response.json()
            return {
                "service": service_name,
                "success": result["success"],
                "task_id": result["task_id"],
                "message": result["message"]
            }
        else:
            raise Exception(f"HTTP {response.status}")


def main():
    """主函数"""
    print("🚀 独立服务测试程序")
    print("=" * 60)
    print("📋 测试目标:")
    print("  • 验证AI Studio和豆包服务独立运行")
    print("  • 检查浏览器实例管理独立性")
    print("  • 测试并发请求处理")
    print("=" * 60)
    
    try:
        result = asyncio.run(test_service_independence())
        if result:
            print("\n🎉 所有独立性测试通过！")
            print("💡 提示: 可以尝试运行并发测试")
            # asyncio.run(test_concurrent_requests())
        else:
            print("\n❌ 部分测试失败")
            print("💡 请确保两个服务都已启动:")
            print("   - AI Studio: python main_refactored.py")
            print("   - 豆包: python doubao_main.py")
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
