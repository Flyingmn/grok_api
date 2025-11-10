#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包生图交互测试启动脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.interactive_doubao_image import DoubaoImageInteractiveClient
from loguru import logger


def main():
    """主函数"""
    print("🚀 启动豆包生图交互测试程序")
    print("=" * 50)
    print("📋 程序功能:")
    print("  • 自动导航到豆包聊天页面")
    print("  • 智能选择图像生成技能")
    print("  • 支持文本输入和图片上传")
    print("  • 实时监听和显示AI响应")
    print("  • 自动保存登录状态")
    print("=" * 50)
    
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    try:
        # 创建客户端并运行
        client = DoubaoImageInteractiveClient()
        asyncio.run(client.run_interactive_session())
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        print(f"❌ 程序运行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
