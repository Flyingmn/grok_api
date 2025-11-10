#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio导航测试脚本
用于测试AI Studio客户端的导航功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.core.interactive_ai_studio import AIStudioInteractiveClient


async def test_ai_studio_navigation():
    """测试AI Studio导航功能"""
    print("🔍 测试AI Studio导航功能")
    print("=" * 50)
    
    client = None
    try:
        # 创建客户端
        print("📋 创建AI Studio客户端...")
        client = AIStudioInteractiveClient()
        client.instance_id = "test_navigation"
        
        # 初始化
        print("📋 初始化客户端...")
        if not await client.setup():
            print("❌ 客户端初始化失败")
            return False
        
        print("✅ 客户端初始化成功")
        
        # 导航到AI Studio
        print("📋 导航到AI Studio...")
        if not await client.navigate_to_ai_studio():
            print("❌ 导航到AI Studio失败")
            return False
        
        print("✅ 导航到AI Studio成功")
        
        # 查找输入元素
        print("📋 查找输入元素...")
        if not await client.find_input_elements():
            print("⚠️  未找到输入元素")
        else:
            print("✅ 找到输入元素")
        
        # 等待一段时间让用户观察
        print("📋 等待5秒钟...")
        await asyncio.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        logger.error(f"AI Studio导航测试失败: {e}")
        return False
    
    finally:
        # 清理资源
        if client:
            try:
                print("📋 清理资源...")
                await client.cleanup()
                print("✅ 资源清理完成")
            except Exception as e:
                print(f"⚠️  清理资源时出错: {e}")


def main():
    """主函数"""
    print("🚀 AI Studio导航测试程序")
    print("=" * 50)
    print("📋 测试目标:")
    print("  • 测试AI Studio客户端初始化")
    print("  • 测试导航到AI Studio页面")
    print("  • 测试查找输入元素")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_ai_studio_navigation())
        if result:
            print("\n🎉 AI Studio导航测试通过！")
        else:
            print("\n❌ AI Studio导航测试失败")
            return 1
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"❌ 测试运行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    sys.exit(main())
