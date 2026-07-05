#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

with open('dca_portfolio_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trade_history', [])
print(f"总交易记录: {len(trades)}")
print(f"total_invested (文件中): {data.get('total_invested', 0):.2f}")

# 按月份分组
from collections import defaultdict
monthly = defaultdict(list)
for t in trades:
    month = t.get('date', '')[:7]
    monthly[month].append(t)

print(f"\n按月份统计:")
total_planned_all = 0
total_actual_all = 0
for month in sorted(monthly.keys()):
    month_trades = monthly[month]
    planned_sum = sum(t.get('planned_amount', 0) for t in month_trades)
    actual_sum = sum(t.get('trade_amount', 0) for t in month_trades)
    total_cost_sum = sum(t.get('total_cost', 0) for t in month_trades)
    total_planned_all += planned_sum
    total_actual_all += actual_sum
    print(f"  {month}: {len(month_trades)}笔, planned={planned_sum:.2f}, 交易额={actual_sum:.2f}, 总成本={total_cost_sum:.2f}")

print(f"\nplanned总和: {total_planned_all:.2f}")
print(f"交易金额总和: {total_actual_all:.2f}")
print(f"差额: {3000*3 - data.get('total_invested', 0):.2f}")

# 检查每笔交易的 planned_amount
print(f"\n各ETF计划金额详情 (7月):")
july = [t for t in trades if t.get('date', '').startswith('2026-07')]
for t in july:
    print(f"  {t['code']} {t['name']}: planned={t.get('planned_amount', 0):.2f}, 实际={t['trade_amount']:.2f}, 总成本={t['total_cost']:.2f}")

print(f"\n5月交易:")
may = [t for t in trades if t.get('date', '').startswith('2026-05')]
for t in may:
    print(f"  {t['code']} {t['name']}: planned={t.get('planned_amount', 0):.2f}, 实际={t['trade_amount']:.2f}")

print(f"\n6月交易:")
jun = [t for t in trades if t.get('date', '').startswith('2026-06')]
for t in jun:
    print(f"  {t['code']} {t['name']}: planned={t.get('planned_amount', 0):.2f}, 实际={t['trade_amount']:.2f}")

# 510500 中证500 是否有交易
print(f"\n510500 中证500ETF 交易记录:")
zz500 = [t for t in trades if t['code'] == '510500']
for t in zz500:
    print(f"  {t['date']}: {t['shares']}股 × ¥{t['price']:.4f} = ¥{t['trade_amount']:.2f}")
