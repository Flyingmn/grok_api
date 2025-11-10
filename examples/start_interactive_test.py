#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动Google AI Studio交互测试的简化脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.interactive_ai_studio import AIStudioInteractiveClient
from loguru import logger


def main():
    """主函数"""
    print("🤖 Google AI Studio 交互测试程序")
    print("=" * 50)
    print("📋 功能说明:")
    print("  • 自动打开Google AI Studio")
    print("  • 在终端输入文本，自动填充到AI Studio")
    print("  • 监听API响应，显示AI回复")
    print("  • 支持连续对话")
    print("=" * 50)
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG",  # 改为DEBUG级别以显示更多调试信息
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    # 运行交互测试
    test = AIStudioInteractiveClient()
    
    try:
        asyncio.run(test.run_interactive_session())
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，再见！")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        print(f"\n❌ 程序运行失败: {e}")
        print("请检查网络连接和浏览器环境")


if __name__ == "__main__":
    main()
