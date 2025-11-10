"""
核心模块 - 爬虫框架和AI Studio交互
"""

from .crawler_framework import CrawlerFramework, CrawlerConfig, CrawlerInstance
from .interactive_ai_studio import AIStudioInteractiveClient

__all__ = ["CrawlerFramework", "CrawlerConfig", "CrawlerInstance", "AIStudioInteractiveClient"]
