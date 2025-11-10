#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio浏览器管理API
提供网页界面管理AI Studio浏览器实例
"""

from src.api.base_management_api import create_management_app
from src.core.service_browser_manager import ai_studio_browser_manager

# 创建AI Studio浏览器管理API应用
ai_studio_management_app = create_management_app(
    service_name="AI Studio",
    service_title="AI Studio",
    api_port=8812,
    browser_manager=ai_studio_browser_manager
)
