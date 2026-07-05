#!/usr/bin/env python3
"""一次性修复：给 dca_portfolio_data.json 添加 cash_balance 字段"""
import json, os, re

FILE = r"D:\temp\红利ETF\dca_portfolio_data.json"
CONFIG = r"D:\temp\红利ETF\dca_config.py"

with open(FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 计算总投入
total_invested = sum(
    h.get('total_cost', 0) for h in data.get('holdings', {}).values()
    if isinstance(h, dict)
)

# 从 config 推算 initial_cash（没有 explicit 值就用 monthly_amount × 推测月份数）
initial_cash = 0
if os.path.exists(CONFIG):
    with open(CONFIG, 'r', encoding='utf-8') as f:
        config = f.read()
    m = re.search(r'initial_cash\s*=\s*(\d+)', config)
    if m:
        initial_cash = float(m.group(1))
    else:
        m = re.search(r'monthly_amount\s*=\s*(\d+)', config)
        if m:
            # 估算: monthly × 12个月 × 2年 = 72000
            initial_cash = float(m.group(1)) * 24

cash = data.get('cash_balance', 0)
if cash <= 0 and initial_cash > 0:
    cash = max(0, initial_cash - total_invested)

data['cash_balance'] = round(cash, 2)
data['total_invested'] = round(total_invested, 2)

print(f"total_invested: {total_invested:.2f}")
print(f"initial_cash (推算): {initial_cash:.2f}")
print(f"cash_balance: {cash:.2f}")

with open(FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n✅ 已写入 {FILE}")
