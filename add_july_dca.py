#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加7月定投数据
- 模拟 2026-07-01 的定投流程
- 使用7月1日的合理估算价格
- 调用 execute_dca_optimized 按比例分配
- 更新持仓、现金、累计投入、last_run_month
- 所有交易记录添加 type='dca' 标签
"""
import os
import sys
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from dca_config import DCA_CONFIG, ETF_PORTFOLIO
from dca_trading import execute_dca_optimized
from dca_portfolio_manager import PortfolioManager


def main():
    print("=" * 80)
    print("【添加7月定投数据】模拟 2026-07-01 定投")
    print("=" * 80)

    # 1. 加载当前持仓
    pm = PortfolioManager()
    pm.load_data()

    print(f"\n[1] 添加前持仓状态:")
    for code, h in pm.holdings.items():
        if h['shares'] > 0:
            print(f"    {code} {h['name']}: {h['shares']}股, 成本{h['avg_cost']:.4f}")
    print(f"    现金余额: {pm.cash_balance:.2f}")
    print(f"    累计投入: {pm.total_invested:.2f}")
    print(f"    上次定投月份: {pm.last_run_month}")

    # 2. 7月1日合理估算价格（参考7月初市场行情）
    july1_prices = {
        '515080': 1.460,   # 中证红利ETF
        '510300': 4.870,   # 沪深300ETF
        '510500': 8.880,   # 中证500ETF
        '512760': 1.390,   # 芯片ETF
        '512010': 0.362,   # 医药ETF
        '513100': 2.160,   # 纳指ETF
    }

    print(f"\n[2] 使用 2026-07-01 估算价格执行定投:")
    for code, price in july1_prices.items():
        etf = next((e for e in ETF_PORTFOLIO if e['code'] == code), {})
        print(f"    {code} {etf.get('name','')}: ¥{price:.4f} (计划投入¥{etf.get('monthly_amount',0)})")

    # 3. 执行优化分配定投
    print(f"\n[3] 执行优化分配...")
    trade_results = execute_dca_optimized(july1_prices)

    if not trade_results:
        print("[错误] 未生成任何交易记录")
        return False

    print(f"\n[4] 生成交易记录 {len(trade_results)} 笔:")
    total_spent = 0
    for result in trade_results:
        # 添加 type='dca' 标签
        result['type'] = 'dca'
        # 修改日期为 2026-07-01
        result['date'] = '2026-07-01'
        result['timestamp'] = '2026-07-01 09:41:23'
        # 更新 note
        result['note'] = '7月定投(补录)'

        total_spent += result['total_cost']
        print(f"    {result['code']} {result['name']}: "
              f"买{result['shares']}股 × ¥{result['price']:.4f} = ¥{result['trade_amount']:.2f}"
              f" (佣金¥{result['commission']:.2f}, 合计¥{result['total_cost']:.2f})")

    print(f"\n    总花费: ¥{total_spent:.2f}")

    # 5. 更新持仓（调用 add_trade）
    print(f"\n[5] 更新持仓...")
    for result in trade_results:
        pm.add_trade(result)

    # 6. 更新现金余额（月度金额 - 实际花费）
    actual_spent = sum(r['total_cost'] for r in trade_results)
    pm.cash_balance = round(DCA_CONFIG['monthly_amount'] - actual_spent, 2)
    print(f"    实际花费: ¥{actual_spent:.2f}")
    print(f"    现金余额: ¥{pm.cash_balance:.2f}")

    # 7. 更新累计投入（add_trade 已更新 total_invested，使用 planned_amount）
    # 注意：add_trade 用 planned_amount 累加 total_invested
    # 这里需要修正：7月定投的 planned_amount 总和应为 3000
    # add_trade 已经处理，无需再手动加

    # 8. 更新 last_run_month
    pm.last_run_month = '2026-07'
    pm.last_run_date = '2026-07-01'

    # 9. 保存数据
    pm.save_data()

    # 10. 显示最终状态
    print(f"\n[6] 添加后持仓状态:")
    for code, h in pm.holdings.items():
        if h['shares'] > 0:
            print(f"    {code} {h['name']}: {h['shares']}股, 成本{h['avg_cost']:.4f}, 总成本{h['total_cost']:.2f}")
    print(f"    现金余额: ¥{pm.cash_balance:.2f}")
    print(f"    累计投入: ¥{pm.total_invested:.2f}")
    print(f"    上次定投月份: {pm.last_run_month}")

    # 11. 统计交易记录
    print(f"\n[7] 交易记录统计:")
    type_counts = {}
    for t in pm.trade_history:
        ttype = t.get('type', 'N/A')
        type_counts[ttype] = type_counts.get(ttype, 0) + 1
    print(f"    总交易记录: {len(pm.trade_history)} 条")
    for ttype, count in type_counts.items():
        print(f"    {ttype}: {count} 条")

    # 12. 显示7月新增交易
    print(f"\n[8] 7月新增交易记录:")
    july_trades = [t for t in pm.trade_history if t.get('date') == '2026-07-01']
    for t in july_trades:
        print(f"    {t.get('type','N/A'):8} {t['timestamp']} {t['code']} {t['name']}: "
              f"{t['shares']}股 × ¥{t['price']:.4f} = ¥{t['trade_amount']:.2f}")

    print(f"\n{'=' * 80}")
    print(f"7月定投数据添加完成")
    print(f"{'=' * 80}")
    return True


if __name__ == '__main__':
    main()
