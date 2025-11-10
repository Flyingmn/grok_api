#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包多实例服务主启动脚本
同时启动豆包图片生成API和浏览器管理界面
"""

import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.doubao_api import app as doubao_api_app
from src.api.doubao_management_api import doubao_management_app
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
            "doubao": {
                "api_port": 8814,
                "management_port": 8815,
                "service_name": "豆包"
            }
        }

# 加载配置
config = load_config()
doubao_config = config.get("doubao", {})

print(f"🔧 豆包服务配置:")
print(f"   API端口: {doubao_config.get('api_port', 8814)}")
print(f"   管理端口: {doubao_config.get('management_port', 8815)}")
print(f"   服务名称: {doubao_config.get('service_name', '豆包')}")

# 创建主函数
main = create_main_function(
    service_name=doubao_config.get("service_name", "豆包"),
    api_app=doubao_api_app,
    management_app=doubao_management_app,
    api_port=doubao_config.get("api_port", 8814),
    management_port=doubao_config.get("management_port", 8815),
    log_prefix="doubao_multi_instance_server"
)

if __name__ == "__main__":
    main()
