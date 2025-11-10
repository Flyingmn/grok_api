#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的生图业务流程
演示如何使用新增的业务方法
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.interactive_ai_studio import AIStudioInteractiveClient
from loguru import logger


async def test_workflow():
    """测试新的业务流程"""
    client = AIStudioInteractiveClient()
    
    try:
        # 初始化
        logger.info("初始化AI Studio客户端...")
        if not await client.setup():
            logger.error("初始化失败")
            return False
        
        # 导航到AI Studio
        logger.info("导航到AI Studio...")
        if not await client.navigate_to_ai_studio():
            logger.error("导航失败")
            return False
        
        # 演示业务流程
        print("\n🎯 演示新的业务流程方法:")
        print("=" * 50)
        
        # 1. 准备新的生图会话（不删除当前对话）
        print("\n1️⃣ 测试准备新的生图会话（导航+设置比例，不删除对话）")
        success = await client.prepare_new_image_session("16:9")
        print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 2. 单独测试设置比例
        print("\n2️⃣ 测试设置图片比例为 1:1")
        success = await client.set_aspect_ratio("1:1")
        print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 3. 测试导航到新的生图对话页面
        print("\n3️⃣ 测试导航到新的生图对话页面")
        success = await client.navigate_to_new_image_chat()
        print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 4. 测试删除当前对话
        print("\n4️⃣ 测试删除当前对话")
        success = await client.delete_current_conversation()
        print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 5. 测试任务完成后的清理工作
        print("\n5️⃣ 测试任务完成后的清理工作（删除对话+导航到新页面）")
        success = await client.cleanup_after_task()
        print(f"   结果: {'✅ 成功' if success else '❌ 失败'}")
        
        print("\n🎉 所有业务流程测试完成！")
        print("💡 正确的使用流程:")
        print("   1. 开始任务时：只设置比例，不删除对话")
        print("   2. 任务完成后：调用cleanup_after_task()删除对话并准备下次任务")
        print("   3. 这样可以避免误删用户正在进行的对话")
        
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        return False
    finally:
        # 清理资源
        await client.cleanup()


async def main():
    """主函数"""
    print("🚀 启动新业务流程测试")
    print("📋 这个测试将演示以下新功能:")
    print("  • navigate_to_new_image_chat() - 导航到新的生图对话页面")
    print("  • delete_current_conversation() - 删除当前对话")
    print("  • set_aspect_ratio() - 设置图片比例")
    print("  • prepare_new_image_session() - 准备新的生图会话（不删除对话）")
    print("  • cleanup_after_task() - 任务完成后的清理工作（删除对话+准备下次）")
    print("=" * 60)
    
    await test_workflow()


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
