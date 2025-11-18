#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grok浏览器管理API
提供网页界面管理grok浏览器实例
"""

from src.api.base_management_api import create_management_app
from src.core.service_browser_manager import grok_browser_manager

# 创建grok浏览器管理API应用
grok_management_app = create_management_app(
    service_name="grok",
    service_title="grok",
    api_port=8816,
    browser_manager=grok_browser_manager
)
