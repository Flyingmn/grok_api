#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包生图交互程序测试
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.interactive_doubao_image import DoubaoImageInteractiveClient
from loguru import logger


async def test_basic_functionality():
    """测试基本功能"""
    print("🧪 开始测试豆包生图交互程序基本功能")
    
    client = DoubaoImageInteractiveClient()
    
    try:
        # 测试初始化
        print("1. 测试初始化...")
        success = await client.setup()
        if success:
            print("✅ 初始化成功")
        else:
            print("❌ 初始化失败")
            return False
        
        # 测试导航
        print("2. 测试页面导航...")
        success = await client.navigate_to_doubao()
        if success:
            print("✅ 页面导航成功")
        else:
            print("❌ 页面导航失败")
            return False
        
        # 测试技能检查
        print("3. 测试技能状态检查...")
        skill_selected = await client.check_image_skill_selected()
        print(f"📊 图像生成技能状态: {'已选择' if skill_selected else '未选择'}")
        
        # 测试技能选择
        if not skill_selected:
            print("4. 测试技能选择...")
            success = await client.select_image_generation_skill()
            if success:
                print("✅ 技能选择成功")
            else:
                print("❌ 技能选择失败")
        
        print("✅ 基本功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False
    
    finally:
        # 清理资源
        await client.cleanup()


async def test_selectors():
    """测试选择器配置"""
    print("🧪 测试选择器配置")
    
    client = DoubaoImageInteractiveClient()
    
    # 检查选择器配置
    required_selectors = [
        "input_container",
        "text_input", 
        "send_button",
        "skill_indicator",
        "skill_bar_image_button",
        "reference_image_button",
        "ratio_button"
    ]
    
    missing_selectors = []
    for selector_name in required_selectors:
        if selector_name not in client.selectors:
            missing_selectors.append(selector_name)
    
    if missing_selectors:
        print(f"❌ 缺少选择器: {missing_selectors}")
        return False
    else:
        print("✅ 所有必需的选择器都已配置")
        return True


def main():
    """主测试函数"""
    print("🚀 豆包生图交互程序测试套件")
    print("=" * 50)
    
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    try:
        # 运行测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 测试选择器配置
        selector_test_result = loop.run_until_complete(test_selectors())
        
        if selector_test_result:
            print("\n继续进行功能测试...")
            print("⚠️  注意: 功能测试需要网络连接和浏览器环境")
            
            user_input = input("是否继续进行功能测试? (y/N): ").strip().lower()
            
            if user_input in ['y', 'yes']:
                # 测试基本功能
                basic_test_result = loop.run_until_complete(test_basic_functionality())
                
                if basic_test_result:
                    print("\n🎉 所有测试通过!")
                    return 0
                else:
                    print("\n❌ 功能测试失败")
                    return 1
            else:
                print("\n✅ 选择器测试通过，跳过功能测试")
                return 0
        else:
            print("\n❌ 选择器测试失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        return 1
    finally:
        loop.close()


if __name__ == "__main__":
    sys.exit(main())
