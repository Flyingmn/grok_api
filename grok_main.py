#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grok多实例服务主启动脚本
同时启动Grok视频生成API和浏览器管理界面
"""

import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.grok_api import app as grok_api_app
from src.api.grok_management_api import grok_management_app
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
            "grok": {
                "api_port": 8816,
                "management_port": 8817,
                "service_name": "grok"
            }
        }

# 加载配置
config = load_config()
grok_config = config.get("grok", {})

print(f"🔧 Grok服务配置:")
print(f"   API端口: {grok_config.get('api_port', 8816)}")
print(f"   管理端口: {grok_config.get('management_port', 8817)}")
print(f"   服务名称: {grok_config.get('service_name', 'grok')}")

# 创建主函数
main = create_main_function(
    service_name=grok_config.get("service_name", "grok"),
    api_app=grok_api_app,
    management_app=grok_management_app,
    api_port=grok_config.get("api_port", 8816),
    management_port=grok_config.get("management_port", 8817),
    log_prefix="grok_multi_instance_server"
)

if __name__ == "__main__":
    main()
