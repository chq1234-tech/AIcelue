#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本 - 检查系统环境和依赖
"""

import sys
import os

print("=" * 70)
print("定投系统诊断工具")
print("=" * 70)

# 1. 检查Python环境
print("\n【1. Python环境】")
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print(f"工作目录: {os.getcwd()}")

# 2. 检查工作目录
print("\n【2. 检查文件结构】")
target_dir = r"d:\temp\红利ETF"
print(f"目标目录: {target_dir}")
print(f"目录存在: {os.path.exists(target_dir)}")

if os.path.exists(target_dir):
    # 切换到目标目录
    os.chdir(target_dir)
    print(f"已切换到: {os.getcwd()}")

    # 检查核心文件
    files_to_check = [
        'dca_config.py',
        'dca_calendar.py',
        'dca_trading.py',
        'dca_portfolio_manager.py',
        'dca_main.py'
    ]

    print("\n核心文件检查:")
    for filename in files_to_check:
        exists = os.path.exists(filename)
        status = "✓" if exists else "✗"
        print(f"  {status} {filename}")

# 3. 测试导入
print("\n【3. 测试模块导入】")

try:
    import dca_config
    print("  ✓ dca_config 导入成功")
except Exception as e:
    print(f"  ✗ dca_config 导入失败: {e}")

try:
    import dca_calendar
    print("  ✓ dca_calendar 导入成功")
except Exception as e:
    print(f"  ✗ dca_calendar 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_portfolio_manager
    print("  ✓ dca_portfolio_manager 导入成功")
except Exception as e:
    print(f"  ✗ dca_portfolio_manager 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_trading
    print("  ✓ dca_trading 导入成功")
except Exception as e:
    print(f"  ✗ dca_trading 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    import dca_main
    print("  ✓ dca_main 导入成功")
except Exception as e:
    print(f"  ✗ dca_main 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 检查依赖库
print("\n【4. 检查依赖库】")

dependencies = [
    ('pandas', 'pandas'),
    ('akshare', 'akshare'),
    ('docx', 'python-docx'),
    ('schedule', 'schedule'),
    ('chinese_calendar', 'chinese-calendar'),
]

for module_name, package_name in dependencies:
    try:
        __import__(module_name)
        print(f"  ✓ {package_name} 已安装")
    except ImportError:
        print(f"  ✗ {package_name} 未安装")
    except Exception as e:
        print(f"  ? {package_name} 安装但有问题: {e}")

# 5. 测试配置
print("\n【5. 测试配置加载】")
try:
    from dca_config import DCA_CONFIG, ETF_PORTFOLIO
    print(f"  ✓ 配置加载成功")
    print(f"    每月定投金额: {DCA_CONFIG['monthly_amount']}元")
    print(f"    ETF数量: {len(ETF_PORTFOLIO)}只")
except Exception as e:
    print(f"  ✗ 配置加载失败: {e}")
    import traceback
    traceback.print_exc()

# 6. 测试日历模块
print("\n【6. 测试日历模块】")
try:
    from dca_calendar import get_current_month_info
    info = get_current_month_info()
    print(f"  ✓ 日历模块工作正常")
    print(f"    当前月份: {info['year']}年{info['month']}月")
    print(f"    交易日总数: {info['total_trading_days']}天")
    print(f"    首交易日: {info['first_trading_day']}")
except Exception as e:
    print(f"  ✗ 日历模块失败: {e}")
    import traceback
    traceback.print_exc()

# 7. 测试持仓管理
print("\n【7. 测试持仓管理】")
try:
    from dca_portfolio_manager import PortfolioManager
    pm = PortfolioManager()
    print(f"  ✓ 持仓管理器初始化成功")
except Exception as e:
    print(f"  ✗ 持仓管理器失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("诊断完成！")
print("=" * 70)
print("\n如果上面显示 ✗ 错误，请根据错误信息安装缺失的依赖：")
print("  pip install pandas akshare python-docx schedule chinese-calendar")
