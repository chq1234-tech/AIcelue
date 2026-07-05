#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复7月定投数据问题：
1. 补投中证500ETF（确保每只ETF至少买1手）
2. 调整其他ETF股数，腾出钱来买中证500
3. 修正 total_invested 为 9000 元（3个月 × 3000元/月）
4. 同步更新持仓、现金余额、交易历史
"""
import os
import sys
import json
import copy
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from dca_config import DCA_CONFIG, ETF_PORTFOLIO

DATA_FILE = os.path.join(SCRIPT_DIR, 'dca_portfolio_data.json')

COMMISSION_RATE = DCA_CONFIG.get('commission_rate', 0.00025)
MIN_COMMISSION = DCA_CONFIG.get('min_commission', 0.1)


def calc_commission(trade_amount):
    return max(round(trade_amount * COMMISSION_RATE, 2), MIN_COMMISSION)


def main():
    print("=" * 80)
    print("【修复7月定投数据】")
    print("=" * 80)

    # 1. 加载当前数据
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    holdings = data['holdings']
    trades = data['trade_history']

    print(f"\n[1] 当前状态:")
    print(f"    total_invested: {data.get('total_invested', 0):.2f}")
    print(f"    cash_balance: {data.get('cash_balance', 0):.2f}")
    print(f"    last_run_month: {data.get('last_run_month', '')}")
    print(f"    交易记录总数: {len(trades)}")

    # 2. 分离7月交易和其他交易
    july_trades = [t for t in trades if t.get('date', '').startswith('2026-07')]
    other_trades = [t for t in trades if not t.get('date', '').startswith('2026-07')]

    print(f"\n[2] 7月原交易 ({len(july_trades)}笔):")
    july_old_total_cost = 0
    july_old_planned = 0
    for t in july_trades:
        print(f"    {t['code']} {t['name']}: {t['shares']}股 × ¥{t['price']:.4f} "
              f"= ¥{t['trade_amount']:.2f} (总成本¥{t['total_cost']:.2f}, "
              f"planned¥{t.get('planned_amount', 0):.2f})")
        july_old_total_cost += t['total_cost']
        july_old_planned += t.get('planned_amount', 0)
    print(f"    原总成本: ¥{july_old_total_cost:.2f}, 原planned合计: ¥{july_old_planned:.2f}")

    # 3. 重新分配7月3000元，确保每只ETF至少1手
    # 7月1日价格
    july_prices = {
        '515080': 1.460,
        '510300': 4.870,
        '510500': 8.880,
        '512760': 1.390,
        '512010': 0.362,
        '513100': 2.160,
    }

    total_budget = 3000.0
    allocations = {}  # code -> shares

    # 第一轮：每只至少1手
    for etf in ETF_PORTFOLIO:
        code = etf['code']
        price = july_prices[code]
        allocations[code] = 100  # 至少1手

    # 计算第一轮花费
    first_round_cost = 0
    for code, shares in allocations.items():
        trade_amount = shares * july_prices[code]
        comm = calc_commission(trade_amount)
        first_round_cost += trade_amount + comm

    remaining = round(total_budget - first_round_cost, 2)
    print(f"\n[3] 第一轮(每只1手)花费: ¥{first_round_cost:.2f}, 剩余: ¥{remaining:.2f}")

    # 第二轮：按配置比例补投，找缺口最大且买得起1手的
    max_iterations = 50
    iteration = 0
    while remaining > 10 and iteration < max_iterations:
        iteration += 1
        best_code = None
        best_gap = -1

        for etf in ETF_PORTFOLIO:
            code = etf['code']
            price = july_prices[code]
            lot_cost = price * 100
            need = lot_cost + calc_commission(lot_cost)

            if need <= remaining:
                theoretical = total_budget * etf['allocation']
                current_cost = allocations[code] * price
                gap = theoretical - current_cost
                if gap > best_gap:
                    best_gap = gap
                    best_code = (code, price, need)

        if best_code is None:
            break

        code, price, need = best_code
        allocations[code] += 100
        remaining -= need
        remaining = round(remaining, 2)

    print(f"    第二轮补投后剩余: ¥{remaining:.2f}")

    # 4. 生成新的7月交易记录
    new_july_trades = []
    new_july_total_cost = 0
    new_july_planned = 0

    print(f"\n[4] 新7月交易:")
    for etf in ETF_PORTFOLIO:
        code = etf['code']
        name = etf['name']
        category = etf['category']
        price = july_prices[code]
        shares = allocations[code]
        trade_amount = round(shares * price, 2)
        commission = calc_commission(trade_amount)
        total_cost = round(trade_amount + commission, 2)
        planned = round(total_budget * etf['allocation'], 2)

        new_july_total_cost += total_cost
        new_july_planned += planned

        trade = {
            'success': True,
            'type': 'dca',
            'code': code,
            'name': name,
            'category': category,
            'price': price,
            'price_source': 'sina',
            'is_fallback': False,
            'date': '2026-07-01',
            'shares': shares,
            'trade_amount': trade_amount,
            'commission': commission,
            'total_cost': total_cost,
            'planned_amount': planned,
            'actual_amount': trade_amount,
            'timestamp': '2026-07-01 09:41:23',
            'note': '7月定投'
        }
        new_july_trades.append(trade)
        print(f"    {code} {name}: {shares}股 × ¥{price:.4f} = ¥{trade_amount:.2f} "
              f"(佣金¥{commission:.2f}, 合计¥{total_cost:.2f}, planned¥{planned:.2f})")

    print(f"    新总成本: ¥{new_july_total_cost:.2f}")
    print(f"    新planned合计: ¥{new_july_planned:.2f}")
    print(f"    现金余额: ¥{remaining:.2f}")

    # 5. 重建持仓（从5月+6月交易重新计算，再加7月新交易）
    # 先获取5月+6月的持仓状态
    # 我们可以直接用当前持仓减去7月的旧交易，再加7月的新交易
    print(f"\n[5] 重建持仓...")

    # 减去7月旧交易的影响
    for t in july_trades:
        code = t['code']
        shares = t['shares']
        trade_amount = t['trade_amount']
        commission = t['commission']
        total_cost = trade_amount + commission

        h = holdings[code]
        old_shares = h['shares']
        old_total_cost = h['total_cost']

        # 减去买入
        new_shares = old_shares - shares
        if new_shares < 0:
            new_shares = 0
            new_total_cost = 0
        else:
            # 按比例减少成本
            if old_shares > 0:
                new_total_cost = old_total_cost * (new_shares / old_shares)
            else:
                new_total_cost = 0

        h['shares'] = new_shares
        h['total_cost'] = round(new_total_cost, 2)
        h['avg_cost'] = round(h['total_cost'] / h['shares'], 4) if h['shares'] > 0 else 0

    print(f"    减去7月旧交易后持仓:")
    for code, h in holdings.items():
        if h['shares'] > 0:
            print(f"      {code} {h['name']}: {h['shares']}股, 成本{h['avg_cost']:.4f}")

    # 加上7月新交易
    for t in new_july_trades:
        code = t['code']
        shares = t['shares']
        trade_amount = t['trade_amount']
        commission = t['commission']
        total_cost = trade_amount + commission

        h = holdings[code]
        old_shares = h['shares']
        old_cost = h['total_cost']
        new_shares = old_shares + shares
        new_cost = old_cost + total_cost

        h['shares'] = new_shares
        h['total_cost'] = round(new_cost, 2)
        h['avg_cost'] = round(h['total_cost'] / h['shares'], 4) if h['shares'] > 0 else 0

    print(f"\n    加上7月新交易后持仓:")
    for code, h in holdings.items():
        if h['shares'] > 0:
            print(f"      {code} {h['name']}: {h['shares']}股, 成本{h['avg_cost']:.4f}, 总成本{h['total_cost']:.2f}")

    # 6. 更新交易历史
    data['trade_history'] = other_trades + new_july_trades

    # 7. 更新现金余额
    # 每月3000元投入，7月实际花了 new_july_total_cost，剩余 remaining
    # 现金余额应该是剩余的钱（约 remaining）
    old_cash = data.get('cash_balance', 0)
    # 旧现金 = 6月末现金 + 7月3000 - 7月实际花费
    # 我们需要先算出6月末的现金，然后重新计算7月末现金
    # 旧数据中7月现金 = 6月现金 + 3000 - july_old_total_cost
    # 新数据中7月现金 = 6月现金 + 3000 - new_july_total_cost
    # 6月现金 = old_cash - 3000 + july_old_total_cost
    june_cash = old_cash - 3000 + july_old_total_cost
    new_cash = june_cash + 3000 - new_july_total_cost
    data['cash_balance'] = round(new_cash, 2)

    print(f"\n[6] 现金余额:")
    print(f"    6月末现金: ¥{june_cash:.2f}")
    print(f"    7月投入: ¥3000.00")
    print(f"    7月实际花费: ¥{new_july_total_cost:.2f}")
    print(f"    7月末现金: ¥{data['cash_balance']:.2f}")

    # 8. 修正 total_invested = 每月3000 × 3个月 = 9000
    data['total_invested'] = 9000.00
    print(f"\n[7] total_invested 修正为: ¥{data['total_invested']:.2f}")

    # 9. 更新 last_run_month（保持不变）
    # data['last_run_month'] 已经是 2026-07

    # 10. 保存数据
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[8] 数据已保存到: {DATA_FILE}")

    # 11. 最终验证
    print(f"\n[9] 最终验证:")
    print(f"    total_invested: ¥{data['total_invested']:.2f}")
    print(f"    cash_balance: ¥{data['cash_balance']:.2f}")
    print(f"    last_run_month: {data.get('last_run_month', '')}")
    print(f"    交易记录总数: {len(data['trade_history'])}")

    # 按月统计
    from collections import defaultdict
    monthly = defaultdict(list)
    for t in data['trade_history']:
        month = t.get('date', '')[:7]
        monthly[month].append(t)

    print(f"\n    按月统计:")
    for month in sorted(monthly.keys()):
        m_trades = monthly[month]
        planned_sum = sum(t.get('planned_amount', 0) for t in m_trades)
        cost_sum = sum(t.get('total_cost', 0) for t in m_trades)
        print(f"      {month}: {len(m_trades)}笔, planned=¥{planned_sum:.2f}, 总成本=¥{cost_sum:.2f}")

    # 检查所有ETF是否都有7月交易
    july_codes = set(t['code'] for t in data['trade_history'] if t.get('date', '').startswith('2026-07'))
    all_codes = set(etf['code'] for etf in ETF_PORTFOLIO)
    missing = all_codes - july_codes
    if missing:
        print(f"\n    ⚠️ 7月缺失的ETF: {missing}")
    else:
        print(f"\n    ✓ 7月所有ETF都有交易记录")

    # 检查每只ETF持仓是否都>0
    all_positive = all(holdings[etf['code']]['shares'] > 0 for etf in ETF_PORTFOLIO)
    if all_positive:
        print(f"    ✓ 所有ETF持仓均大于0")
    else:
        zero_holdings = [etf['code'] for etf in ETF_PORTFOLIO if holdings[etf['code']]['shares'] == 0]
        print(f"    ⚠️ 持仓为0的ETF: {zero_holdings}")

    print(f"\n{'=' * 80}")
    print(f"修复完成")
    print(f"{'=' * 80}")
    return True


if __name__ == '__main__':
    main()
