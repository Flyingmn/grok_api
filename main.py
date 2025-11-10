#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio 多实例服务主启动脚本
同时启动图片生成API和浏览器管理界面
"""

import sys
import signal
import threading
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
import uvicorn
from src.api.ai_studio_api import app as api_app
from src.api.browser_management_api import management_app


class MultiInstanceServer:
    """多实例服务器"""
    
    def __init__(self):
        self.running = False
        self.management_thread = None
    
    def start_management_server(self):
        """启动管理界面服务器"""
        try:
            logger.info("启动浏览器管理界面 (端口: 8813)...")
            uvicorn.run(
                management_app,
                host="0.0.0.0",
                port=8813,
                log_level="warning"  # 减少日志输出
            )
        except Exception as e:
            logger.error(f"管理界面启动失败: {e}")
    
    def start_api_server(self):
        """启动API服务器"""
        try:
            logger.info("启动图片生成API服务器 (端口: 8812)...")
            uvicorn.run(
                api_app,
                host="0.0.0.0",
                port=8812,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"API服务器启动失败: {e}")
    
    def start(self):
        """启动所有服务"""
        logger.info("🚀 启动AI Studio多实例服务")
        logger.info("=" * 60)
        logger.info("📋 服务说明:")
        logger.info("  • 图片生成API: http://localhost:8812")
        logger.info("  • 浏览器管理界面: http://localhost:8813")
        logger.info("  • 健康检查: http://localhost:8812/health")
        logger.info("=" * 60)
        
        self.running = True
        
        # 在单独的线程中启动管理界面
        self.management_thread = threading.Thread(
            target=self.start_management_server,
            daemon=True
        )
        self.management_thread.start()
        
        # 等待一下让管理界面先启动
        time.sleep(2)
        
        # 在主线程中启动API服务器
        self.start_api_server()
    
    def stop(self):
        """停止所有服务"""
        logger.info("正在停止所有服务...")
        self.running = False


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭服务...")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 配置日志
    logger.remove()
    logger.add(
        "data/logs/multi_instance_server_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}\n"
    )
    
    # 创建数据目录
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data/cookies").mkdir(parents=True, exist_ok=True)
    
    try:
        server = MultiInstanceServer()
        server.start()
    except KeyboardInterrupt:
        logger.info("服务被用户中断")
    except Exception as e:
        logger.error(f"服务运行失败: {e}")
    finally:
        logger.info("服务已退出")


if __name__ == "__main__":
    main()
