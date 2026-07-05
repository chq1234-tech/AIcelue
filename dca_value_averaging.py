#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值平均法（Value Averaging, VA）策略模块

核心原理：
  - 每月目标总市值 = 已完成月数 × 每月基准金额
  - 月初注入本月基准金额到现金池
  - 计算当前总市值（股票+现金）与目标的差额
  - 差额为正（低于目标）：用现金买入，优先配置低配类别
  - 差额为负（高于目标）：卖出超出部分，优先卖出高配类别

与 DCA 的区别：
  - DCA：每月固定金额买入，不管涨跌
  - VA：自动"跌多买多、涨多卖出"，波动越大效果越好
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Tuple


def calculate_current_total(pm, prices: Dict[str, float]) -> Tuple[float, float, Dict[str, float]]:
    """
    计算当前总资产
    Returns: (total_value, holdings_value, per_etf_value)
    """
    holdings_value = 0.0
    per_etf_value = {}
    for code, holding in pm.holdings.items():
        if holding.get('shares', 0) <= 0:
            continue
        price = prices.get(code, holding.get('avg_cost', 0))
        val = price * holding['shares']
        holdings_value += val
        per_etf_value[code] = val
    total_value = holdings_value + pm.cash_balance
    return total_value, holdings_value, per_etf_value


def calculate_target_value(monthly_amount: float, elapsed_months: int,
                           extra_cash: float = 0) -> float:
    """
    计算本月目标总市值
    VA 标准公式：目标 = 月份数 × 每月基准金额 + 额外现金
    月初会注入 monthly_amount 到现金池，所以目标 = (elapsed_months+1) × monthly_amount？
    这里的定义：
      - elapsed_months = 已执行的月数（第1次执行时为0）
      - 本月目标 = (elapsed_months + 1) × monthly_amount
    """
    # 现金已在 execute_va_month 中提前注入（pm.cash_balance += monthly_amount），
    # 所以目标 = elapsed_months × monthly，不再加1（避免双计）
    # 第1次(elapsed_months=0)目标=0，此时系统无持仓可卖，自动跳过
    return elapsed_months * monthly_amount + extra_cash


def calculate_va_allocations(pm, prices: Dict[str, float],
                              etf_portfolio: List[dict],
                              target_total: float,
                              diff_amount: float) -> List[dict]:
    """
    根据 VA 差额和目标配比，计算每只 ETF 的买入/卖出金额

    Args:
        pm: PortfolioManager 实例
        prices: 各 ETF 当前价格 {code: price}
        etf_portfolio: ETF 配置列表
        target_total: 目标总市值
        diff_amount: 需要投入的金额（正=买入，负=卖出）
    Returns:
        [{code, action('buy'/'sell'), amount, shares, price}, ...]
    """
    # 计算每只 ETF 的目标市值
    total_alloc = sum(etf.get('allocation', etf.get('monthly_amount', 500) / 3000)
                       for etf in etf_portfolio)
    allocations = {}
    for etf in etf_portfolio:
        allocations[etf['code']] = etf.get('allocation',
                                            etf.get('monthly_amount', 500) / 3000) / total_alloc

    # 当前各 ETF 市值
    _, _, current_vals = calculate_current_total(pm, prices)

    # 计算每只 ETF 的目标市值 = target_total × allocation
    # 与当前的差异 = 目标 - 当前
    # 差异为正 → 应该买入；差异为负 → 应该卖出
    diffs = []  # (code, diff_value, is_frozen)
    for etf in etf_portfolio:
        code = etf['code']
        target_val = target_total * allocations.get(code, 0)
        current_val = current_vals.get(code, 0)
        diff = target_val - current_val
        is_frozen = pm.holdings.get(code, {}).get('freeze_until', '') >= datetime.now().strftime('%Y-%m-%d')
        diffs.append({
            'code': code,
            'target_value': target_val,
            'current_value': current_val,
            'diff': diff,  # 正=需买入，负=需卖出
            'allocation': allocations.get(code, 0),
            'frozen': is_frozen,
        })

    trades = []
    min_shares = 100  # 最小交易单位
    commission_rate = 0.0001

    if diff_amount > 0:
        # 需要买入：优先买差异最大的（最需要补仓的）
        buy_targets = sorted(
            [d for d in diffs if d['diff'] > 0 and not d['frozen']],
            key=lambda x: x['diff'],
            reverse=True
        )
        remaining = diff_amount
        total_buy_diff = sum(d['diff'] for d in buy_targets)

        for d in buy_targets:
            if remaining < 100:
                break
            # 按差异比例分配买入金额
            if total_buy_diff > 0:
                alloc_amount = remaining * (d['diff'] / total_buy_diff)
            else:
                alloc_amount = remaining / len(buy_targets)

            price = prices.get(d['code'], 0)
            if price <= 0:
                continue

            # 最多买 min(分配金额, 目标差异金额)
            max_amount = min(alloc_amount, d['diff'])
            shares = int(max_amount / price / min_shares) * min_shares
            if shares <= 0:
                continue

            cost = shares * price
            commission = max(cost * commission_rate, 0.2)
            total_cost = cost + commission

            if total_cost > remaining:
                shares = int(remaining * 0.99 / price / min_shares) * min_shares
                if shares <= 0:
                    continue
                cost = shares * price
                commission = max(cost * commission_rate, 0.2)
                total_cost = cost + commission

            trades.append({
                'code': d['code'],
                'action': 'buy',
                'shares': shares,
                'price': price,
                'cost': total_cost,
                'commission': commission,
            })
            remaining -= total_cost

    elif diff_amount < 0:
        # 需要卖出：优先卖差异最负的（超配最多的）
        sell_amount = -diff_amount
        sell_targets = sorted(
            [d for d in diffs if d['diff'] < 0 and not d['frozen']],
            key=lambda x: x['diff'],  # 最负的排前面
        )
        remaining_to_sell = sell_amount

        for d in sell_targets:
            if remaining_to_sell < 100:
                break
            price = prices.get(d['code'], 0)
            if price <= 0:
                continue
            holding = pm.holdings.get(d['code'], {})
            current_shares = holding.get('shares', 0)
            if current_shares <= 0:
                continue

            # 卖出 min(超配部分, 还需卖出金额)
            max_sell_value = min(-d['diff'], remaining_to_sell)
            sell_shares = int(max_sell_value / price / min_shares) * min_shares
            if sell_shares <= 0:
                continue
            if sell_shares > current_shares:
                sell_shares = int(current_shares / min_shares) * min_shares
            if sell_shares <= 0:
                continue

            proceeds = sell_shares * price
            commission = max(proceeds * commission_rate, 0.2)
            net_proceeds = proceeds - commission

            trades.append({
                'code': d['code'],
                'action': 'sell',
                'shares': sell_shares,
                'price': price,
                'proceeds': net_proceeds,
                'commission': commission,
            })
            remaining_to_sell -= net_proceeds

    return trades


def execute_va_month(pm, etf_portfolio: List[dict],
                     monthly_amount: float,
                     elapsed_months: int,
                     get_price_func) -> dict:
    """
    执行一个月的 VA 策略

    Args:
        pm: PortfolioManager 实例
        etf_portfolio: ETF 配置列表
        monthly_amount: 每月基准金额
        elapsed_months: 已执行月数（第1次为0）
        get_price_func: 价格获取函数 (code) -> {'price': ..., 'success': bool}
    Returns:
        执行结果 dict
    """
    print("\n" + "=" * 70)
    print(f"【价值平均法 VA】第 {elapsed_months + 1} 个月执行")
    print("=" * 70)

    # 1. 月初注入本月基准金额
    pm.cash_balance += monthly_amount
    print(f"\n  注入本月金额: ¥{monthly_amount:.2f}")
    print(f"  现金余额: ¥{pm.cash_balance:.2f}")

    # 2. 获取所有 ETF 当前价格
    prices = {}
    for etf in etf_portfolio:
        price_info = get_price_func(etf['code'])
        if price_info.get('success'):
            prices[etf['code']] = price_info['price']

    if not prices:
        return {'success': False, 'message': '无法获取行情', 'trades': []}

    # 3. 计算当前总市值和目标
    current_total, _, _ = calculate_current_total(pm, prices)
    target_total = calculate_target_value(monthly_amount, elapsed_months)
    diff = target_total - current_total  # 正=需买入，负=需卖出

    print(f"\n  当前总市值: ¥{current_total:.2f}")
    print(f"  目标总市值: ¥{target_total:.2f}")
    print(f"  差额: {'+' if diff >= 0 else ''}¥{diff:.2f} "
          f"({'需买入' if diff >= 0 else '需卖出'})")

    # 4. 计算交易计划
    trades = calculate_va_allocations(pm, prices, etf_portfolio, target_total, diff)

    if not trades:
        print("\n  无需交易（差异太小或全部冻结）")
        return {'success': True, 'trades': [], 'diff': diff,
                'current_total': current_total, 'target_total': target_total}

    # 5. 执行交易
    print(f"\n  交易计划: {len(trades)} 笔")
    executed = []

    for t in trades:
        code = t['code']
        etf_info = next((e for e in etf_portfolio if e['code'] == code), {})

        if t['action'] == 'buy':
            cost = t['cost']
            if cost > pm.cash_balance:
                print(f"    ⚠ {code} {etf_info.get('name','')} 现金不足，跳过")
                continue
            # 买入
            pm.cash_balance -= cost
            holding = pm.holdings.get(code, {
                'shares': 0, 'total_cost': 0, 'avg_cost': 0,
                'name': etf_info.get('name', ''),
                'category': etf_info.get('category', ''),
                'frozen_until': '',
            })
            if holding.get('shares', 0) > 0:
                new_shares = holding['shares'] + t['shares']
                new_cost = holding['total_cost'] + cost
                holding['shares'] = new_shares
                holding['total_cost'] = round(new_cost, 2)
                holding['avg_cost'] = round(new_cost / new_shares, 4)
            else:
                holding['shares'] = t['shares']
                holding['total_cost'] = round(cost, 2)
                holding['avg_cost'] = round(t['price'], 4)
                holding['name'] = etf_info.get('name', '')
                holding['category'] = etf_info.get('category', '')
            pm.holdings[code] = holding

            result = {
                'type': 'va_buy',
                'code': code,
                'name': etf_info.get('name', ''),
                'category': etf_info.get('category', ''),
                'action': 'buy',
                'shares': t['shares'],
                'price': t['price'],
                'total_cost': round(cost, 2),
                'commission': round(t['commission'], 2),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'planned_amount': round(diff, 2),
                'actual_amount': round(cost, 2),
            }
            pm.add_trade(result)
            executed.append(result)
            print(f"    买入 {code} {etf_info.get('name','')}: "
                  f"{t['shares']}股 × ¥{t['price']:.4f} = ¥{cost:.2f}")

        else:  # sell
            holding = pm.holdings.get(code, {})
            if holding.get('shares', 0) < t['shares']:
                print(f"    ⚠ {code} {etf_info.get('name','')} 持仓不足，跳过")
                continue

            proceeds = t['proceeds']
            pm.cash_balance += proceeds
            ratio = t['shares'] / holding['shares']
            holding['total_cost'] = round(holding['total_cost'] * (1 - ratio), 2)
            holding['shares'] -= t['shares']
            if holding['shares'] == 0:
                holding['avg_cost'] = 0
                holding['total_cost'] = 0
                holding['freeze_until'] = (datetime.now()
                                            .strftime('%Y-%m-%d'))  # 当天不回购
            pm.holdings[code] = holding

            result = {
                'type': 'va_sell',
                'code': code,
                'name': etf_info.get('name', ''),
                'category': etf_info.get('category', ''),
                'action': 'sell',
                'shares': t['shares'],
                'price': t['price'],
                'total_cost': round(proceeds, 2),
                'commission': round(t['commission'], 2),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'planned_amount': round(diff, 2),
                'actual_amount': round(proceeds, 2),
            }
            pm.add_trade(result)
            executed.append(result)
            print(f"    卖出 {code} {etf_info.get('name','')}: "
                  f"{t['shares']}股 × ¥{t['price']:.4f} = ¥{proceeds:.2f} (净)")

    # 6. 止盈资金立即轮动（低配类别优先）
    if pm.cash_balance > monthly_amount * 0.3 and diff > 0:
        print(f"\n  剩余现金 ¥{pm.cash_balance:.2f}，按低配轮动再投...")
        re_trades = pm.invest_cash_balance(etf_portfolio, get_price_func)
        executed.extend(re_trades)

    pm.save_data()

    # 7. 打印总结
    final_total, _, _ = calculate_current_total(pm, prices)
    buy_count = sum(1 for t in executed if t.get('action') == 'buy')
    sell_count = sum(1 for t in executed if t.get('action') == 'sell')

    print(f"\n  --- 本月 VA 执行总结 ---")
    print(f"  买入 {buy_count} 笔, 卖出 {sell_count} 笔")
    print(f"  执行后总市值: ¥{final_total:.2f}")
    print(f"  目标完成度: {final_total/target_total*100:.1f}%")
    print(f"  现金余额: ¥{pm.cash_balance:.2f}")

    return {
        'success': True,
        'trades': executed,
        'diff': round(diff, 2),
        'current_total': round(current_total, 2),
        'target_total': round(target_total, 2),
        'final_total': round(final_total, 2),
    }


def count_elapsed_months(pm) -> int:
    """
    根据交易记录统计已执行的 VA 月数
    统计所有 type 为 'dca' 或 'va_buy' 的月数（去重月份）
    """
    months = set()
    for trade in pm.trade_history:
        ts = trade.get('timestamp', '')[:7]  # YYYY-MM
        if ts:
            months.add(ts)
    return len(months)


# ============================================================
# 百分比再平衡定投策略
# ============================================================

def execute_rebalance_month(pm, etf_portfolio: List[dict],
                            monthly_amount: float,
                            get_price_func,
                            rebalance_threshold: float = 0.03) -> dict:
    """
    百分比再平衡定投

    **核心思想**：
      每月注入月供后，以总资产为分母，按目标配比逐只计算每只ETF的应持市值。
      超配的卖，低配的买，资金先卖后买循环使用。
      无论牛熊、无论涨跌——每月必投，且自动高抛低吸。

    **和 VA 的本质区别**：
      VA：看「总市值 vs 绝对值目标」，涨了全不买，跌了全加仓
      再平衡：看「单只 vs 自身配比」，涨多了卖它、跌多了买它，互不干扰

    Args:
        pm: PortfolioManager 实例
        etf_portfolio: ETF 配置列表（需含 allocation 配比）
        monthly_amount: 每月基准金额
        get_price_func: 价格获取函数 (code) -> {'price': ..., 'success': bool}
        rebalance_threshold: 触发再平衡的偏离阈值，默认3%（0.03）

    Returns:
        执行结果 dict
    """
    from datetime import datetime
    min_shares = 100
    commission_rate = 0.0001

    print("\n" + "=" * 70)
    print(f"【百分比再平衡定投】本月执行")
    print("=" * 70)

    # 1. 注入本月基准金额
    pm.cash_balance += monthly_amount
    print(f"\n  注入本月金额: ¥{monthly_amount:.2f}")
    print(f"  当前现金余额: ¥{pm.cash_balance:.2f}")

    # 2. 获取所有 ETF 当前价格
    prices = {}
    for etf in etf_portfolio:
        price_info = get_price_func(etf['code'])
        if price_info.get('success'):
            prices[etf['code']] = price_info['price']

    if not prices:
        return {'success': False, 'message': '无法获取行情', 'trades': []}

    # 3. 计算总资产和各ETF当前市值
    total_asset = pm.cash_balance
    current_values = {}  # code -> 市值
    for etf in etf_portfolio:
        code = etf['code']
        price = prices.get(code, 0)
        if price <= 0:
            current_values[code] = 0.0
            continue
        shares = pm.holdings.get(code, {}).get('shares', 0)
        value = shares * price
        current_values[code] = value
        total_asset += value

    print(f"\n  总资产: ¥{total_asset:.2f}")
    print(f"  其中现金: ¥{pm.cash_balance:.2f} ({pm.cash_balance/total_asset*100:.1f}%)")
    print()

    # 4. 逐只计算差异
    #    先扫一遍，标记哪些要卖、哪些要买
    overs = []   # (code, sell_amount, 当前市值, 目标市值)
    unders = []  # (code, buy_amount, 当前市值, 目标市值)
    target_values = {}

    for etf in etf_portfolio:
        code = etf['code']
        ratio = etf.get('allocation', 0)
        target_value = total_asset * ratio
        target_values[code] = target_value
        current_value = current_values.get(code, 0)

        if target_value == 0:
            continue

        deviation = (current_value - target_value) / target_value  # +超配 -低配
        threshold_value = target_value * rebalance_threshold

        print(f"  {etf['name']:<8} 当前¥{current_value:>8.0f} "
              f"目标¥{target_value:>8.0f} "
              f"偏离{deviation*100:+.1f}%", end="")

        if deviation > rebalance_threshold and current_value > 0:
            # 超配 → 卖
            sell_amount = current_value - target_value
            overs.append((code, sell_amount, current_value, target_value))
            print(f" → 超配, 卖¥{sell_amount:.0f}")
        elif deviation < -rebalance_threshold:
            # 低配 → 买
            buy_amount = target_value - current_value
            unders.append((code, buy_amount, current_value, target_value))
            print(f" → 低配, 买¥{buy_amount:.0f}")
        else:
            print(f" → 在阈值±{rebalance_threshold*100:.0f}%内, 不动")

    # 5. 先执行卖出（回收现金，供后续买入使用）
    all_trades = []
    total_sell_proceeds = 0.0

    print(f"\n  ——— 执行卖出一览 ———")
    for code, sell_amount, cur_val, tgt_val in overs:
        price = prices.get(code, 0)
        if price <= 0:
            continue
        holding = pm.holdings.get(code, {})
        current_shares = holding.get('shares', 0)
        if current_shares <= 0:
            continue

        # 最多卖超配部分
        sell_shares = int(sell_amount / price / min_shares) * min_shares
        if sell_shares <= 0:
            continue
        if sell_shares > current_shares:
            sell_shares = int(current_shares / min_shares) * min_shares
        if sell_shares <= 0:
            continue

        proceeds = sell_shares * price
        commission = max(proceeds * commission_rate, 0.2)
        net_proceeds = proceeds - commission

        # 更新持仓
        ratio_sold = sell_shares / current_shares
        holding['total_cost'] = round(holding['total_cost'] * (1 - ratio_sold), 2)
        holding['shares'] -= sell_shares
        if holding['shares'] == 0:
            holding['avg_cost'] = 0
            holding['total_cost'] = 0
        pm.holdings[code] = holding
        pm.cash_balance += net_proceeds

        etf_name = next((e['name'] for e in etf_portfolio if e['code'] == code), code)
        total_sell_proceeds += net_proceeds

        trade_record = {
            'type': 'rebalance_sell',
            'code': code, 'name': etf_name,
            'action': 'sell', 'shares': sell_shares,
            'price': price, 'proceeds': round(proceeds, 2),
            'commission': round(commission, 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        pm.trade_history.append(trade_record)
        all_trades.append(trade_record)

        print(f"    卖出 {etf_name} {sell_shares}股 × ¥{price:.4f} = ¥{proceeds:.2f}")

    # 6. 再执行买入
    print(f"\n  ——— 执行买入一览 ———")
    total_buy_cost = 0.0

    for code, buy_amount, cur_val, tgt_val in unders:
        available = pm.cash_balance
        if available < 100:
            print(f"    现金不足({available:.0f})，剩余买入计划跳过")
            break

        price = prices.get(code, 0)
        if price <= 0:
            continue

        # 买入 min(低配差额, 可用现金)
        actual_buy = min(buy_amount, available * 0.99)  # 留点余量给佣金
        buy_shares = int(actual_buy / price / min_shares) * min_shares
        if buy_shares <= 0:
            continue

        cost = buy_shares * price
        commission = max(cost * commission_rate, 0.2)
        total_cost = cost + commission

        if total_cost > pm.cash_balance:
            buy_shares = int(pm.cash_balance * 0.99 / price / min_shares) * min_shares
            if buy_shares <= 0:
                continue
            cost = buy_shares * price
            commission = max(cost * commission_rate, 0.2)
            total_cost = cost + commission

        # 更新持仓
        pm.cash_balance -= total_cost
        holding = pm.holdings.get(code, {
            'shares': 0, 'total_cost': 0, 'avg_cost': 0,
            'name': '', 'category': '',
        })
        etf_info = next((e for e in etf_portfolio if e['code'] == code), {})
        if holding['shares'] > 0:
            new_shares = holding['shares'] + buy_shares
            new_cost = holding['total_cost'] + cost
            holding['shares'] = new_shares
            holding['total_cost'] = round(new_cost, 2)
            holding['avg_cost'] = round(new_cost / new_shares, 4)
        else:
            holding['shares'] = buy_shares
            holding['total_cost'] = round(cost, 2)
            holding['avg_cost'] = round(price, 4)
            holding['name'] = etf_info.get('name', '')
            holding['category'] = etf_info.get('category', '')
        pm.holdings[code] = holding
        total_buy_cost += total_cost

        etf_name = etf_info.get('name', code)
        trade_record = {
            'type': 'rebalance_buy',
            'code': code, 'name': etf_name,
            'action': 'buy', 'shares': buy_shares,
            'price': price, 'total_cost': round(cost, 2),
            'commission': round(commission, 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        pm.trade_history.append(trade_record)
        all_trades.append(trade_record)

        print(f"    买入 {etf_name} {buy_shares}股 × ¥{price:.4f} = ¥{cost:.2f}")

    # 7. 剩余现金按配比摊入
    if pm.cash_balance > monthly_amount * 0.1:
        print(f"\n  剩余现金 ¥{pm.cash_balance:.2f}，按配比摊入...")
        remaining_trades = pm.invest_cash_balance(etf_portfolio, get_price_func)
        all_trades.extend(remaining_trades)

    pm.save_data()

    # 8. 打印总结
    final_prices = {code: prices.get(code, 0) for code in prices}
    total_cash = pm.cash_balance
    total_holdings = 0.0
    for etf in etf_portfolio:
        code = etf['code']
        price = final_prices.get(code, 0)
        shares = pm.holdings.get(code, {}).get('shares', 0)
        total_holdings += shares * price
    final_total = total_cash + total_holdings

    buy_count = sum(1 for t in all_trades if t.get('action') == 'buy')
    sell_count = sum(1 for t in all_trades if t.get('action') == 'sell')

    print(f"\n  --- 再平衡执行总结 ---")
    print(f"  买入 {buy_count} 笔, 卖出 {sell_count} 笔")
    print(f"  执行后总资产: ¥{final_total:.2f}")
    print(f"  现金余额: ¥{pm.cash_balance:.2f} ({pm.cash_balance/final_total*100:.1f}%)")

    return {
        'success': True,
        'trades': all_trades,
        'final_total': round(final_total, 2),
        'cash_balance': round(pm.cash_balance, 2),
    }


if __name__ == '__main__':
    # 简单自测
    print("VA 模块已加载")
    print(f"测试: calculate_target_value(3000, 3) = {calculate_target_value(3000, 3)}")
