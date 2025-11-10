#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包浏览器管理API
提供网页界面管理豆包浏览器实例
"""

from src.api.base_management_api import create_management_app
from src.core.service_browser_manager import doubao_browser_manager

# 创建豆包浏览器管理API应用
doubao_management_app = create_management_app(
    service_name="豆包",
    service_title="豆包",
    api_port=8814,
    browser_manager=doubao_browser_manager
)
