#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投系统测试脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """测试导入模块"""
    print("\n测试1: 导入模块...")
    try:
        from dca_config import DCA_CONFIG, ETF_PORTFOLIO
        print("  [OK] dca_config 导入成功")
    except Exception as e:
        print(f"  [FAIL] dca_config 导入失败: {e}")
        return False

    try:
        from dca_calendar import is_first_trading_day, get_current_month_info
        print("  [OK] dca_calendar 导入成功")
    except Exception as e:
        print(f"  [FAIL] dca_calendar 导入失败: {e}")
        return False

    try:
        from dca_portfolio_manager import PortfolioManager
        print("  [OK] dca_portfolio_manager 导入成功")
    except Exception as e:
        print(f"  [FAIL] dca_portfolio_manager 导入失败: {e}")
        return False

    return True

def test_config():
    """测试配置"""
    print("\n测试2: 测试配置...")
    try:
        from dca_config import DCA_CONFIG, ETF_PORTFOLIO

        print(f"  每月定投金额: {DCA_CONFIG['monthly_amount']}元")
        print(f"  交易佣金: {DCA_CONFIG['commission_rate'] * 100}%")
        print(f"  ETF数量: {len(ETF_PORTFOLIO)}只")

        # 验证金额总和
        total = sum(etf['monthly_amount'] for etf in ETF_PORTFOLIO)
        print(f"  配置金额总和: {total}元")

        if total == DCA_CONFIG['monthly_amount']:
            print("  [OK] 金额配置正确")
            return True
        else:
            print("  [FAIL] 金额配置有误")
            return False

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        return False

def test_trading_calculation():
    """测试交易计算"""
    print("\n测试3: 测试交易计算...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        # 注意：这里需要先修改import路径
        import importlib.util
        spec = importlib.util.spec_from_file_location("dca_trading", "dca_trading.py")
        dca_trading = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dca_trading)

        # 测试计算股数
        shares = dca_trading.calculate_shares("515080", 600, 1.5746)
        print(f"  600元, 价格1.5746元 -> 可购买 {shares}股")

        if shares % 100 == 0 and shares <= 600 / 1.5746:
            print("  [OK] 股数计算正确")
        else:
            print("  [FAIL] 股数计算有误")
            return False

        # 测试成本计算
        trade_amount, commission, total_cost = dca_trading.calculate_trade_cost(shares, 1.5746)
        print(f"  交易金额: {trade_amount:.2f}元, 佣金: {commission:.2f}元, 总成本: {total_cost:.2f}元")

        return True

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_manager():
    """测试持仓管理"""
    print("\n测试4: 测试持仓管理...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dca_portfolio_manager", "dca_portfolio_manager.py")
        dca_pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dca_pm)

        pm = dca_pm.PortfolioManager('test_portfolio.json')
        print("  [OK] 持仓管理器初始化成功")

        # 测试打印配置
        pm.print_portfolio_summary({})
        print("  [OK] 持仓汇总打印成功")

        # 清理测试文件
        if os.path.exists('test_portfolio.json'):
            os.remove('test_portfolio.json')

        return True

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("=" * 70)
    print("定投系统测试")
    print("=" * 70)

    results = []

    results.append(("模块导入", test_imports()))
    results.append(("配置测试", test_config()))
    results.append(("交易计算", test_trading_calculation()))
    results.append(("持仓管理", test_portfolio_manager()))

    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    all_passed = True
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{name:20s}: {status}")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n所有测试通过！系统可以正常使用。")
    else:
        print("\n部分测试失败，请检查错误信息。")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
