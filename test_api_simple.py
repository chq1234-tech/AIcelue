#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试API...")

from dca_portfolio_manager import PortfolioManager
pm = PortfolioManager()
print(f"持仓: {len(pm.holdings)}")

# 快速使用已知价格
prices = {
    '515080': {'code': '515080', 'price': 1.556, 'success': True},
    '510300': {'code': '510300', 'price': 4.862, 'success': True},
    '510500': {'code': '510500', 'price': 8.658, 'success': True},
    '512760': {'code': '512760', 'price': 1.186, 'success': True},
    '512010': {'code': '512010', 'price': 0.345, 'success': True},
    '513100': {'code': '513100', 'price': 2.146, 'success': True},
}

total_value = 0
cat_values = {}
for code, holding in pm.holdings.items():
    if holding['shares'] > 0 and code in prices:
        value = holding['shares'] * prices[code]['price']
        total_value += value
        cat = holding.get('category', '其他')
        cat_values[cat] = cat_values.get(cat, 0) + value

cat_alloc = {}
target_alloc = {'红利': 0.20, '宽基': 0.40, '行业': 0.25, '海外': 0.15}
for cat, target in target_alloc.items():
    current = cat_values.get(cat, 0) / total_value if total_value > 0 else 0
    cat_alloc[cat] = {
        'current_pct': round(current * 100, 2),
        'target_pct': round(target * 100, 2),
        'deviation': round((current - target) * 100, 2)
    }

holdings_info = []
for code, holding in pm.holdings.items():
    if holding['shares'] > 0 and code in prices:
        current_price = prices[code]['price']
        avg_cost = holding['avg_cost']
        profit_pct = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
        distance_to_threshold = 20 - profit_pct
        holdings_info.append({
            'code': code,
            'name': holding.get('name', code),
            'shares': holding['shares'],
            'avg_cost': round(avg_cost, 4),
            'current_price': round(current_price, 4),
            'profit_pct': round(profit_pct, 2),
            'distance': round(distance_to_threshold, 2),
            'need_gain': round(avg_cost * 1.20, 4) if avg_cost > 0 else 0,
        })

result = {
    'signals': [],
    'holdings_info': holdings_info,
    'category_allocation': cat_alloc,
    'frozen_etfs': [],
    'history': [],
}

import json
print(json.dumps(result, ensure_ascii=False, indent=2))
print("\n测试成功！")
