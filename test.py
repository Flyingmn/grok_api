#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的API测试脚本
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 导入测试模块
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from tests.simple_test import main as run_simple_test


if __name__ == "__main__":
    print("🎨 AI Studio 图片生成API 快速测试")
    print("=" * 50)
    run_simple_test()
