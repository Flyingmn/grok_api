#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Studio 多实例服务主启动脚本（重构版）
同时启动图片生成API和浏览器管理界面
"""

import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.ai_studio_api_refactored import app as ai_studio_api_app
from src.api.ai_studio_management_api import ai_studio_management_app
from src.api.base_multi_instance_server import create_main_function

def load_config():
    """加载服务器配置"""
    config_file = Path(__file__).parent / "config" / "server_config.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        print(f"配置文件路径: {config_file}")
        # 使用默认配置
        return {
            "ai_studio": {
                "api_port": 8812,
                "management_port": 8813,
                "service_name": "AI Studio"
            }
        }

# 加载配置
config = load_config()
ai_studio_config = config.get("ai_studio", {})

print(f"🔧 AI Studio 服务配置:")
print(f"   API端口: {ai_studio_config.get('api_port', 8812)}")
print(f"   管理端口: {ai_studio_config.get('management_port', 8813)}")
print(f"   服务名称: {ai_studio_config.get('service_name', 'AI Studio')}")

# 创建主函数
main = create_main_function(
    service_name=ai_studio_config.get("service_name", "AI Studio"),
    api_app=ai_studio_api_app,
    management_app=ai_studio_management_app,
    api_port=ai_studio_config.get("api_port", 8812),
    management_port=ai_studio_config.get("management_port", 8813),
    log_prefix="ai_studio_multi_instance_server"
)

if __name__ == "__main__":
    main()
