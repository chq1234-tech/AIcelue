#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 不依赖其他模块
"""

import sys
import os

print("=" * 70)
print("Python环境测试")
print("=" * 70)

print(f"\nPython版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print(f"工作目录: {os.getcwd()}")

# 测试基本导入
print("\n测试基本模块...")
print(f"✓ sys 模块可用")
print(f"✓ os 模块可用")

# 测试依赖库
print("\n测试依赖库...")

libs = [
    ("pandas", "pandas"),
    ("akshare", "akshare"),
    ("docx", "python-docx"),
    ("schedule", "schedule"),
    ("chinese_calendar", "chinese-calendar"),
]

for lib_name, package_name in libs:
    try:
        __import__(lib_name)
        print(f"  ✓ {package_name} - 已安装")
    except ImportError:
        print(f"  ✗ {package_name} - 未安装")
        print(f"    安装命令: pip install {package_name}")
    except Exception as e:
        print(f"  ? {package_name} - 错误: {e}")

# 测试定投模块
print("\n测试定投模块...")

# 添加当前目录到路径
sys.path.insert(0, os.getcwd())

try:
    import dca_config
    print(f"  ✓ dca_config - 导入成功")
except Exception as e:
    print(f"  ✗ dca_config - 导入失败")
    print(f"    错误: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_calendar
    print(f"  ✓ dca_calendar - 导入成功")
except Exception as e:
    print(f"  ✗ dca_calendar - 导入失败")
    print(f"    错误: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_portfolio_manager
    print(f"  ✓ dca_portfolio_manager - 导入成功")
except Exception as e:
    print(f"  ✗ dca_portfolio_manager - 导入失败")
    print(f"    错误: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_trading
    print(f"  ✓ dca_trading - 导入成功")
except Exception as e:
    print(f"  ✗ dca_trading - 导入失败")
    print(f"    错误: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_main
    print(f"  ✓ dca_main - 导入成功")
except Exception as e:
    print(f"  ✗ dca_main - 导入失败")
    print(f"    错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
print("\n如果上面显示 ✗ 错误，请打开命令提示符运行：")
print("  cd /d d:\\temp\\红利ETF")
print("  pip install akshare pandas python-docx schedule chinese-calendar")
