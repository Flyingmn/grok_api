#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试交互组件的基本功能
"""

import asyncio
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.interactive_ai_studio import AIStudioInteractiveClient
from loguru import logger


async def test_initialization():
    """测试初始化功能"""
    print("🧪 测试初始化功能...")
    
    test = AIStudioInteractiveClient()
    
    try:
        # 测试配置创建
        assert test.instance_id == "ai_studio_interactive"
        assert test.selectors is not None
        assert len(test.selectors) > 0
        
        print("✅ 基本配置测试通过")
        
        # 测试选择器配置
        required_selectors = ["textarea", "run_button"]
        for selector in required_selectors:
            assert selector in test.selectors
        
        print("✅ 选择器配置测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
        return False
    finally:
        await test.cleanup()


async def test_response_parsing():
    """测试响应解析功能"""
    print("🧪 测试响应解析功能...")
    
    test = AIStudioInteractiveClient()
    
    try:
        # 模拟API响应数据（基于dom.txt中的结构）
        mock_response = [
            [
                [
                    [
                        [
                            [
                                [
                                    [
                                        None,
                                        "你好"
                                    ]
                                ],
                                "model"
                            ]
                        ]
                    ]
                ]
            ]
        ]
        
        # 测试文本提取
        extracted_text = test.extract_ai_response(mock_response)
        
        if extracted_text:
            print(f"✅ 响应解析测试通过，提取文本: {extracted_text}")
            return True
        else:
            print("❌ 响应解析测试失败，未能提取文本")
            return False
            
    except Exception as e:
        print(f"❌ 响应解析测试失败: {e}")
        return False


async def test_selector_validation():
    """测试选择器验证"""
    print("🧪 测试选择器验证...")
    
    test = AIStudioInteractiveClient()
    
    try:
        # 检查选择器格式
        for name, selector in test.selectors.items():
            assert isinstance(selector, str)
            assert len(selector) > 0
            print(f"  ✓ {name}: {selector}")
        
        print("✅ 选择器验证测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 选择器验证测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始测试交互组件...")
    print("=" * 50)
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        level="WARNING",  # 只显示警告和错误
        format="<red>{level}</red> | {message}"
    )
    
    tests = [
        ("初始化功能", test_initialization),
        ("响应解析功能", test_response_parsing),
        ("选择器验证", test_selector_validation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        try:
            if await test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！程序可以正常使用")
        print("\n💡 使用方法:")
        print("  python start_interactive_test.py")
    else:
        print("⚠️  部分测试失败，请检查环境配置")
    
    return passed == total


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试运行失败: {e}")
        sys.exit(1)
