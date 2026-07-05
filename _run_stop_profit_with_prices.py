#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用预获取价格执行止盈轮动检查（绕过网络请求）"""
import os, sys, json
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dca_portfolio_manager import PortfolioManager
from dca_stop_profit import StopProfitManager, STOP_PROFIT_CONFIG

# 预获取的实时价格（来自 westock-data @ 2026-05-25 09:35）
PRICES = {
    '515080': {'code': '515080', 'price': 1.565, 'date': '2026-05-25', 'source': 'westock', 'success': True},
    '510300': {'code': '510300', 'price': 4.891, 'date': '2026-05-25', 'source': 'westock', 'success': True},
    '510500': {'code': '510500', 'price': 8.706, 'date': '2026-05-25', 'source': 'westock', 'success': True},
    '512760': {'code': '512760', 'price': 1.216, 'date': '2026-05-25', 'source': 'westock', 'success': True},
    '512010': {'code': '512010', 'price': 0.342, 'date': '2026-05-25', 'source': 'westock', 'success': True},
    '513100': {'code': '513100', 'price': 2.205, 'date': '2026-05-25', 'source': 'westock', 'success': True},
}

print("=" * 80)
print("每日止盈轮动检查（westock-data 实时价格）")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"止盈阈值: {STOP_PROFIT_CONFIG['threshold']*100}%")
print(f"数据源: 腾讯自选股 westock-data")
print("=" * 80)

# 加载持仓
print("\n[1] 加载持仓数据...")
pm = PortfolioManager()
pm.print_portfolio_summary()

# 创建止盈管理器
spm = StopProfitManager(pm)

# 执行检查（传入预获取价格，跳过网络请求）
print("\n[2] 执行止盈轮动检查...")
result = spm.run_daily_check(prices=PRICES)

# 生成报告
print("\n[3] 生成HTML报告...")
report_path = spm.generate_html_report(result)

# 汇总
print("\n" + "=" * 80)
print("止盈轮动检查完成")
print(f"  止盈信号: {result.get('signals_count', 0)}个")
print(f"  止盈执行: {result.get('stop_profit_count', 0)}笔")
print(f"  释放资金: ¥{result.get('total_freed', 0):.2f}")
print(f"  再投资:   {result.get('reinvest_count', 0)}笔")
print(f"  再投金额: ¥{result.get('total_reinvested', 0):.2f}")
print(f"  剩余现金: ¥{result.get('cash_remaining', 0):.2f}")
print(f"  报告路径: {report_path}")
print("=" * 80)

# 保存持仓数据（即使没有交易也更新 last_updated）
pm.last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
pm.save_data()
print(f"\n[4] 持仓数据已保存 (last_updated: {pm.last_updated})")

print("\nDone.")
