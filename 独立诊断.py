#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立诊断脚本 - 不依赖项目模块
"""

import sys
import os

# 打印基本信息
print("=" * 70)
print("独立诊断脚本 v1.0")
print("=" * 70)

print(f"\nPython版本: {sys.version}")
print(f"Python可执行文件: {sys.executable}")

# 切换到脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"工作目录: {os.getcwd()}")

# 1. 检查文件
print("\n【1. 检查核心文件】")
files = {
    'dca_config.py': '配置文件',
    'dca_calendar.py': '日历模块',
    'dca_trading.py': '交易模块',
    'dca_portfolio_manager.py': '持仓管理',
    'dca_main.py': '主程序'
}

all_files_exist = True
for filename, desc in files.items():
    exists = os.path.exists(filename)
    status = "✓" if exists else "✗"
    print(f"  {status} {filename} ({desc})")
    if not exists:
        all_files_exist = False

if not all_files_exist:
    print("\n[错误] 部分核心文件缺失！")
    print(f"请确保所有文件都在: {os.getcwd()}")
    input("\n按回车键退出...")
    sys.exit(1)

# 2. 检查依赖库
print("\n【2. 检查Python依赖库】")
dependencies = [
    ('pandas', '数据分析'),
    ('akshare', '金融数据获取'),
    ('docx', 'Word文档处理'),
    ('schedule', '定时任务'),
    ('chinese_calendar', '中国日历'),
]

missing_libs = []
for lib_name, desc in dependencies:
    try:
        __import__(lib_name)
        print(f"  ✓ {lib_name} ({desc}) - 已安装")
    except ImportError:
        print(f"  ✗ {lib_name} ({desc}) - 未安装")
        missing_libs.append(lib_name)
    except Exception as e:
        print(f"  ? {lib_name} ({desc}) - 异常: {e}")

if missing_libs:
    print(f"\n[警告] 发现 {len(missing_libs)} 个缺失的依赖库")
    print("\n正在尝试安装...")
    import subprocess
    for lib in missing_libs:
        print(f"  安装 {lib}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib, '-q'])
            print(f"    ✓ {lib} 安装成功")
        except Exception as e:
            print(f"    ✗ {lib} 安装失败: {e}")

# 3. 测试模块导入
print("\n【3. 测试模块导入】")

# 临时添加当前目录到路径
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 测试各个模块
modules_to_test = [
    'dca_config',
    'dca_calendar',
    'dca_portfolio_manager',
    'dca_trading',
]

import_errors = []
for module_name in modules_to_test:
    try:
        # 移除已导入的模块（如果有）
        if module_name in sys.modules:
            del sys.modules[module_name]

        # 重新导入
        module = __import__(module_name)
        print(f"  ✓ {module_name} - 导入成功")
    except Exception as e:
        print(f"  ✗ {module_name} - 导入失败")
        print(f"    错误类型: {type(e).__name__}")
        print(f"    错误信息: {str(e)}")
        import_errors.append((module_name, str(e)))

# 4. 测试配置
print("\n【4. 测试配置加载】")
if 'dca_config' not in import_errors:
    try:
        from dca_config import DCA_CONFIG, ETF_PORTFOLIO, print_portfolio_info

        print(f"  ✓ 配置加载成功")
        print(f"    每月定投金额: {DCA_CONFIG['monthly_amount']}元")
        print(f"    ETF数量: {len(ETF_PORTFOLIO)}只")
        print(f"    交易佣金: {DCA_CONFIG['commission_rate'] * 100}%")

        # 显示ETF列表
        print("\n  ETF配置列表:")
        for i, etf in enumerate(ETF_PORTFOLIO, 1):
            print(f"    {i}. {etf['code']} {etf['name']} - {etf['monthly_amount']}元/月")

    except Exception as e:
        print(f"  ✗ 配置加载失败: {e}")
        import_errors.append(('dca_config', str(e)))
else:
    print("  [跳过] 因为模块导入失败")

# 5. 测试日历
print("\n【5. 测试日历功能】")
if 'dca_calendar' not in import_errors:
    try:
        from dca_calendar import get_current_month_info, is_first_trading_day

        info = get_current_month_info()
        print(f"  ✓ 日历功能正常")
        print(f"    当前月份: {info['year']}年{info['month']}月")
        print(f"    交易日总数: {info['total_trading_days']}天")
        print(f"    首交易日: {info['first_trading_day']}")
        print(f"    是否为首交易日: {'是' if info['is_first_day'] else '否'}")

    except Exception as e:
        print(f"  ✗ 日历功能失败: {e}")
        import_errors.append(('dca_calendar', str(e)))
else:
    print("  [跳过] 因为模块导入失败")

# 6. 测试持仓管理
print("\n【6. 测试持仓管理】")
if 'dca_portfolio_manager' not in import_errors:
    try:
        from dca_portfolio_manager import PortfolioManager

        pm = PortfolioManager()
        print(f"  ✓ 持仓管理器初始化成功")
        print(f"    持仓记录数: {len(pm.holdings)}")
        print(f"    交易历史数: {len(pm.trade_history)}")

    except Exception as e:
        print(f"  ✗ 持仓管理器失败: {e}")
        import_errors.append(('dca_portfolio_manager', str(e)))
else:
    print("  [跳过] 因为模块导入失败")

# 总结
print("\n" + "=" * 70)
print("诊断结果")
print("=" * 70)

if not import_errors:
    print("\n✓ 所有测试通过！系统可以正常运行。")
    print("\n现在您可以：")
    print("  1. 双击『定投系统_改进版.bat』运行主程序")
    print("  2. 或者直接运行: python dca_main.py check")
else:
    print(f"\n✗ 发现 {len(import_errors)} 个错误:")
    for i, (module, error) in enumerate(import_errors, 1):
        print(f"\n  错误{i}: {module}")
        print(f"  详情: {error}")

    print("\n【解决方案】")
    print("  1. 安装缺失的依赖库:")
    print("     pip install akshare pandas python-docx schedule chinese-calendar")
    print()
    print("  2. 或者在命令提示符中运行:")
    print("     cd /d d:\\temp\\红利ETF")
    print("     pip install akshare pandas python-docx schedule chinese-calendar")
    print()
    print("  3. 安装完成后重新运行此诊断脚本")

print("\n" + "=" * 70)

input("\n按回车键退出...")
