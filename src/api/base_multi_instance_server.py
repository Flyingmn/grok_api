#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多实例服务器基础类
提供通用的多实例服务器启动和管理功能
"""

import sys
import signal
import threading
import time
from pathlib import Path
from typing import Optional

from loguru import logger
import uvicorn
from fastapi import FastAPI


class BaseMultiInstanceServer:
    """多实例服务器基础类"""
    
    def __init__(self, service_name: str, api_app: FastAPI, management_app: FastAPI, 
                 api_port: int = 8812, management_port: int = 8813):
        self.service_name = service_name
        self.api_app = api_app
        self.management_app = management_app
        self.api_port = api_port
        self.management_port = management_port
        self.running = False
        self.management_thread = None
    
    def start_management_server(self):
        """启动管理界面服务器"""
        try:
            logger.info(f"启动{self.service_name}浏览器管理界面 (端口: {self.management_port})...")
            uvicorn.run(
                self.management_app,
                host="0.0.0.0",
                port=self.management_port,
                log_level="warning"  # 减少日志输出
            )
        except Exception as e:
            logger.error(f"{self.service_name}管理界面启动失败: {e}")
    
    def start_api_server(self):
        """启动API服务器"""
        try:
            logger.info(f"启动{self.service_name}API服务器 (端口: {self.api_port})...")
            uvicorn.run(
                self.api_app,
                host="0.0.0.0",
                port=self.api_port,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"{self.service_name}API服务器启动失败: {e}")
    
    def start(self):
        """启动所有服务"""
        logger.info(f"🚀 启动{self.service_name}多实例服务")
        logger.info("=" * 60)
        logger.info("📋 服务说明:")
        logger.info(f"  • API服务: http://localhost:{self.api_port}")
        logger.info(f"  • 浏览器管理界面: http://localhost:{self.management_port}")
        logger.info(f"  • 健康检查: http://localhost:{self.api_port}/health")
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
        logger.info(f"正在停止{self.service_name}所有服务...")
        self.running = False


def create_main_function(service_name: str, api_app: FastAPI, management_app: FastAPI,
                        api_port: int = 8812, management_port: int = 8813,
                        log_prefix: str = "multi_instance_server"):
    """创建主函数"""
    
    def signal_handler(signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭{service_name}服务...")
        sys.exit(0)

    def main():
        """主函数"""
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 配置日志
        logger.remove()
        logger.add(
            f"data/logs/{log_prefix}_{service_name.lower()}_{'{time:YYYY-MM-DD}'}.log",
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
            server = BaseMultiInstanceServer(
                service_name=service_name,
                api_app=api_app,
                management_app=management_app,
                api_port=api_port,
                management_port=management_port
            )
            server.start()
        except KeyboardInterrupt:
            logger.info(f"{service_name}服务被用户中断")
        except Exception as e:
            logger.error(f"{service_name}服务运行失败: {e}")
        finally:
            logger.info(f"{service_name}服务已退出")
    
    return main
