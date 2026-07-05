#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投策略回测模块 - dca_backtest.py
基于历史 K 线数据，模拟定投策略的历史表现。

功能：
1. 验证当前定投方案的历史表现
2. 对比不同参数组合的效果（每月金额/配比/止盈阈值）
3. 计算总收益率/年化收益/夏普比率/最大回撤

用法：
  python dca_backtest.py                           # 默认回测（近2年）
  python dca_backtest.py --start 2024-01-01        # 自定义开始日期
  python dca_backtest.py --grid-search             # 参数网格搜索
"""

import sys
import os
import json
import math
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from copy import deepcopy

import numpy as np

# 默认配置（与 dca_config.py 一致）
DEFAULT_CONFIG = {
    'monthly_amount': 3000,
    'commission_rate': 0.0001,
    'stop_profit_threshold': 0.20,
    'allocation': {
        '515080': 0.20,   # 中证红利
        '510300': 0.20,   # 沪深300
        '510500': 0.20,   # 中证500
        '512760': 0.125,  # 芯片
        '512010': 0.125,  # 医药
        '513100': 0.15,   # 纳指
    },
}

ETF_NAMES = {
    '515080': '中证红利ETF',
    '510300': '沪深300ETF',
    '510500': '中证500ETF',
    '512760': '芯片ETF',
    '512010': '医药ETF',
    '513100': '纳指ETF',
}


def get_local_kline(code: str, max_days: int = 500) -> List[Dict]:
    """
    从本地缓存或数据源获取历史 K 线数据

    尝试多个数据源：mootdx（首选，最快） → akshare → 本地缓存
    Returns: [{date, open, high, low, close, volume}, ...]
    """
    # 方法1：mootdx 日K线（最快，本地协议）
    try:
        from dca_data_sources import get_daily_history
        # 多拉一些以防不足
        bars = get_daily_history(code, days=max_days + 30)
        if bars:
            # mootdx 已返回标准化字段（date/open/high/low/close/volume/amount）
            return bars[-max_days:] if len(bars) > max_days else bars
    except Exception as e:
        print(f"  [mootdx] {code} K线获取失败: {e}")

    # 方法2：akshare 兜底（前复权日线）
    try:
        import akshare as ak
        prefix = 'sh' if code.startswith('5') or code.startswith('6') else 'sz'
        df = ak.fund_etf_hist_em(symbol=f"{prefix}{code}", period="daily",
                                  start_date="20200101", end_date=datetime.now().strftime("%Y%m%d"),
                                  adjust="qfq")
        if df is not None and not df.empty:
            bars = []
            for _, row in df.iterrows():
                try:
                    bars.append({
                        'date': str(row['日期']),
                        'open': float(row['开盘']),
                        'high': float(row['最高']),
                        'low': float(row['最低']),
                        'close': float(row['收盘']),
                        'volume': float(row['成交量']),
                    })
                except (ValueError, KeyError):
                    continue
            return bars[-max_days:] if len(bars) > max_days else bars
    except ImportError:
        pass
    except Exception:
        pass

    # 方法3：从本地 data 目录加载缓存
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(script_dir, 'data')
    cache_file = os.path.join(cache_dir, f'kline_{code}.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)[-max_days:]

    return []


def _reinvest_low_weight_category(cash: float, holdings: Dict, codes: List[str],
                                    allocation: Dict, kline_data: Dict, dca_date: str,
                                    config: dict) -> float:
    """
    止盈资金按"低配类别优先"轮动再投（与 dca_stop_profit.py 逻辑一致）
    计算每只 ETF 当前实际权重 vs 目标权重的偏差，优先买入低配的 ETF。
    返回剩余未投的现金。
    """
    # 计算当前总市值
    total_value = cash
    for c in codes:
        h = holdings[c]
        if h['shares'] > 0:
            kd = kline_data.get(c, {})
            if dca_date in kd:
                total_value += kd[dca_date]['close'] * h['shares']
            else:
                total_value += h['total_cost']

    if total_value <= 0:
        return cash

    # 计算每只 ETF 的权重偏差
    deviations = []
    for c in codes:
        h = holdings[c]
        # 跳过冻结期 ETF
        if h.get('freeze_until', '') >= dca_date:
            continue
        kd = kline_data.get(c, {})
        if dca_date not in kd:
            continue
        cur_value = kd[dca_date]['close'] * h['shares']
        cur_weight = cur_value / total_value
        target_weight = allocation.get(c, 0)
        deviation = target_weight - cur_weight  # 正=低配（应买入）
        deviations.append((c, deviation, kd[dca_date]['close']))

    # 按偏差降序（最低配的优先）
    deviations.sort(key=lambda x: x[1], reverse=True)

    remaining_cash = cash
    for code, dev, price in deviations:
        if remaining_cash < price * 100:  # 不足买1手
            continue
        # 投入金额 = 当前可用资金 * 该ETF的低配比例
        # 简化：把剩余资金按偏差比例分配
        total_pos_dev = sum(max(d, 0) for _, d, _ in deviations)
        if total_pos_dev <= 0:
            # 全部均衡，按目标权重分配
            alloc_ratio = allocation.get(code, 0) / sum(allocation.values())
        else:
            alloc_ratio = max(dev, 0) / total_pos_dev
        invest_amount = remaining_cash * alloc_ratio

        shares = int(invest_amount / price / 100) * 100
        if shares <= 0:
            continue

        cost = shares * price
        commission = cost * config.get('commission_rate', 0.0001)
        total_cost = cost + commission

        if total_cost > remaining_cash:
            # 重新计算
            shares = int((remaining_cash * 0.99) / price / 100) * 100
            if shares <= 0:
                continue
            cost = shares * price
            commission = cost * config.get('commission_rate', 0.0001)
            total_cost = cost + commission

        h = holdings[code]
        if h['shares'] > 0:
            total_shares = h['shares'] + shares
            h['avg_cost'] = (h['total_cost'] + total_cost) / total_shares
        else:
            h['avg_cost'] = price
        h['shares'] += shares
        h['total_cost'] += total_cost
        remaining_cash -= total_cost

    return remaining_cash


def simulate_monthly_dca(config: dict, start_date: str, end_date: str) -> dict:
    """
    模拟每月定投策略的历史表现

    Args:
        config: 配置参数（含 monthly_amount, allocation, stop_profit_threshold 等）
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD

    Returns:
        { total_invested, final_value, total_return_pct, annual_return_pct,
          max_drawdown_pct, sharpe_ratio, trade_count, stop_profit_count, ... }
    """
    allocation = config['allocation']
    codes = list(allocation.keys())
    monthly_amount = config['monthly_amount']
    stop_threshold = config.get('stop_profit_threshold', 0.20)

    # 加载所有 ETF 的 K 线数据
    kline_data = {}
    for code in codes:
        bars = get_local_kline(code)
        if not bars:
            print(f"  [WARN] {code} {ETF_NAMES.get(code, '')} 无 K 线数据")
            continue
        # 建立日期映射
        date_map = {}
        for b in bars:
            date_map[b['date']] = b
        kline_data[code] = date_map

    if len(kline_data) < len(codes):
        print(f"  [WARN] 只有 {len(kline_data)}/{len(codes)} 只 ETF 有数据")

    # 构建定投日期序列（每月1号）
    dca_dates = []
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = start.replace(day=1)
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        # 检查是否有任何 K 线数据覆盖该日期
        if any(date_str in kd for kd in kline_data.values()):
            dca_dates.append(date_str)
        # 下个月1号
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    print(f"\n  回测期间: {start_date} ~ {end_date}")
    print(f"  定投次数: {len(dca_dates)} 次")

    if len(dca_dates) < 3:
        return {"error": "定投次数不足3次"}

    # 模拟持仓
    holdings: Dict[str, Dict] = {}
    for code in codes:
        holdings[code] = {'shares': 0, 'total_cost': 0, 'avg_cost': 0, 'freeze_until': ''}
    total_invested = 0
    cash_balance = 0
    daily_values: List[Tuple[str, float]] = []  # (date, total_value)
    stop_profit_count = 0

    for dca_date in dca_dates:
        # 计算当月定投金额（等权重分配到有数据的 ETF）
        available = 0
        for code in codes:
            kd = kline_data.get(code, {})
            if dca_date in kd:
                available += 1

        if available == 0:
            continue

        # 按配置分配资金
        for code in codes:
            kd = kline_data.get(code, {})
            if dca_date not in kd:
                continue

            bar = kd[dca_date]
            price = bar['close']
            target_amount = monthly_amount * allocation[code]
            # 加上现金余额的等比例再投
            if cash_balance > 0:
                target_amount += cash_balance * allocation[code]
            target_amount = max(target_amount, price * 100)  # 至少买1手

            shares = int(target_amount / price / 100) * 100
            if shares <= 0:
                continue

            cost = shares * price
            commission = cost * config.get('commission_rate', 0.0001)
            total_cost = cost + commission

            # 更新持仓
            h = holdings[code]
            if h['shares'] > 0:
                total_shares = h['shares'] + shares
                h['avg_cost'] = (h['total_cost'] + total_cost) / total_shares
            else:
                h['avg_cost'] = price
            h['shares'] += shares
            h['total_cost'] += total_cost

            total_invested += total_cost

        cash_balance = 0  # 全额定投

        # 每月定投日检查止盈（与真实 dca_stop_profit.py 逻辑对齐）
        for code in codes:
            h = holdings[code]
            if h['shares'] <= 0:
                continue
            # 检查冻结期
            if h.get('freeze_until', '') >= dca_date:
                continue
            kd = kline_data.get(code, {})
            if dca_date not in kd:
                continue
            price = kd[dca_date]['close']
            current_value = price * h['shares']
            profit_pct = (current_value / h['total_cost'] - 1) if h['total_cost'] > 0 else 0
            if profit_pct >= stop_threshold:
                # 止盈卖出（sell_ratio=1.0，全部卖出）
                sell_value = current_value
                commission = sell_value * config.get('commission_rate', 0.0001)
                net_cash = sell_value - commission
                cash_balance += net_cash
                h['shares'] = 0
                h['total_cost'] = 0
                h['avg_cost'] = 0
                h['freeze_until'] = (
                    datetime.strptime(dca_date, '%Y-%m-%d') + timedelta(days=30)
                ).strftime('%Y-%m-%d')
                stop_profit_count += 1

        # 止盈资金按"低配类别优先"立即轮动再投（与 dca_stop_profit.py 一致）
        if cash_balance > 100:
            cash_balance = _reinvest_low_weight_category(
                cash_balance, holdings, codes, allocation, kline_data, dca_date, config
            )

        # 记录每月末总市值（用于计算回撤和夏普）
        month_end_value = cash_balance
        for code in codes:
            h = holdings[code]
            if h['shares'] > 0:
                kd = kline_data.get(code, {})
                if dca_date in kd:
                    month_end_value += kd[dca_date]['close'] * h['shares']
                else:
                    month_end_value += h['total_cost']
        daily_values.append((dca_date, month_end_value))

    # 计算期末持仓市值
    final_date = dca_dates[-1] if dca_dates else end_date
    final_value = cash_balance

    for code in codes:
        h = holdings[code]
        if h['shares'] <= 0:
            continue
        kd = kline_data.get(code, {})
        # 找最接近期末日期的价格
        if final_date in kd:
            price = kd[final_date]['close']
        else:
            # 取最后一个可用价格
            dates_with_data = sorted(kd.keys())
            last_date = dates_with_data[-1] if dates_with_data else ''
            price = kd[last_date]['close'] if last_date else h['avg_cost']
        final_value += price * h['shares']

    # 计算绩效指标
    total_return = final_value - total_invested
    total_return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0

    # 年化收益率
    n_months = len(dca_dates)
    annual_return_pct = 0
    if n_months >= 3:
        annual_return_pct = ((final_value / total_invested) ** (12 / n_months) - 1) * 100

    # 最大回撤：基于每月末总市值序列
    max_dd = 0.0
    peak = 0.0
    for date_str, value in daily_values:
        if value > peak:
            peak = value
        if peak > 0:
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

    # 夏普比率：用相邻月份总市值的真实月度收益率序列
    sharpe = 0.0
    if len(daily_values) >= 3:
        # 计算每月投入和市值的"真实收益率"
        # 月度收益 = (月末市值 - 月初投入) / 月初总投入
        monthly_rets = []
        prev_total_invested = 0
        cum_invested = 0
        for i, (date_str, value) in enumerate(daily_values):
            # 当月投入 = 该月定投金额（假设每月定投3000）
            cum_invested += config['monthly_amount']
            if i > 0 and prev_total_invested > 0:
                # 月度收益率 = (本月市值 - 上月市值 - 本月新投入) / 上月市值
                prev_value = daily_values[i-1][1]
                monthly_ret = (value - prev_value - config['monthly_amount']) / max(prev_value, 1)
                monthly_rets.append(monthly_ret)
            prev_total_invested = cum_invested

        if len(monthly_rets) >= 2:
            import numpy as np
            avg_ret = float(np.mean(monthly_rets))
            std_ret = max(float(np.std(monthly_rets)), 0.001)
            sharpe = round(avg_ret / std_ret * math.sqrt(12), 2)

    result = {
        "config": {
            "monthly_amount": monthly_amount,
            "allocation": allocation,
            "stop_profit_threshold": stop_threshold,
            "start_date": start_date,
            "end_date": end_date,
        },
        "total_invested": round(total_invested, 2),
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "annual_return_pct": round(annual_return_pct, 2),
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": round(max_dd, 2),
        "dca_count": n_months,
        "stop_profit_count": stop_profit_count,
        "final_cash": round(cash_balance, 2),
        "holdings": {c: {'shares': h['shares'],
                         'avg_cost': round(h['avg_cost'], 4),
                         'total_cost': round(h['total_cost'], 2),
                         'market_value': round(_holding_market_value(h, kline_data.get(c, {}), final_date), 2)}
                     for c, h in holdings.items()},
    }

    return result


def _holding_market_value(h: Dict, kd: Dict, final_date: str) -> float:
    """计算单只ETF持仓的期末市值（kd = kline_data[code]）"""
    if h['shares'] <= 0:
        return 0.0
    if final_date in kd:
        return kd[final_date]['close'] * h['shares']
    dates_with_data = sorted(kd.keys())
    if dates_with_data:
        return kd[dates_with_data[-1]]['close'] * h['shares']
    return h['total_cost']


def simulate_value_averaging(config: dict, start_date: str, end_date: str) -> dict:
    """
    价值平均法（Value Averaging, VA）回测
    核心思想：每月持仓目标市值按固定金额增长
      - 第1月目标 = monthly_amount
      - 第2月目标 = 2 × monthly_amount
      - 第N月目标 = N × monthly_amount
    操作：
      - 需买入 = 目标 - 当前市值（>0 时买入，<0 时止盈卖出）

    与定投 DCA 对比：VA 自动实现"跌多买多、涨多卖出"，长期收益率通常更高
    """
    allocation = config['allocation']
    codes = list(allocation.keys())
    monthly_amount = config['monthly_amount']
    stop_threshold = config.get('stop_profit_threshold', 0.20)

    # 加载K线（与 simulate_monthly_dca 一致）
    kline_data = {}
    for code in codes:
        bars = get_local_kline(code)
        if not bars:
            continue
        kline_data[code] = {b['date']: b for b in bars}

    # 构建定投日期
    dca_dates = []
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = start.replace(day=1)
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        if any(date_str in kd for kd in kline_data.values()):
            dca_dates.append(date_str)
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    if len(dca_dates) < 3:
        return {"error": "定投次数不足3次"}

    # 模拟持仓
    holdings: Dict[str, Dict] = {c: {'shares': 0, 'total_cost': 0, 'avg_cost': 0, 'freeze_until': ''}
                                  for c in codes}
    total_invested = 0.0
    cash_balance = 0.0
    daily_values: List[Tuple[str, float]] = []
    stop_profit_count = 0
    trade_count = 0  # VA 模式下交易次数（包括卖出）

    for month_idx, dca_date in enumerate(dca_dates, 1):
        # 月初：注入本月定投资金
        cash_balance += monthly_amount
        total_invested += monthly_amount  # 累计投入（按注入计）

        # 计算当前持仓总市值（含现金）
        cur_value = cash_balance
        for c in codes:
            h = holdings[c]
            if h['shares'] > 0:
                kd = kline_data.get(c, {})
                if dca_date in kd:
                    cur_value += kd[dca_date]['close'] * h['shares']
                else:
                    cur_value += h['total_cost']

        # 目标市值 = month_idx × monthly_amount
        target_value = month_idx * monthly_amount
        diff = target_value - cur_value  # >0 需要买入，<0 需要卖出

        if diff > monthly_amount * 0.05 and cash_balance > 100:
            # 需要买入，实际投入不超过当前现金
            actual_invest = min(diff, cash_balance * 0.98)  # 留点佣金余量
            # 按 allocation 比例分配买入
            for c in codes:
                kd = kline_data.get(c, {})
                if dca_date not in kd:
                    continue
                h = holdings[c]
                if h.get('freeze_until', '') >= dca_date:
                    continue
                price = kd[dca_date]['close']
                invest_amount = actual_invest * allocation.get(c, 0)
                if invest_amount < price * 100:
                    continue
                shares = int(invest_amount / price / 100) * 100
                if shares <= 0:
                    continue
                cost = shares * price
                commission = cost * config.get('commission_rate', 0.0001)
                total_cost = cost + commission
                if h['shares'] > 0:
                    total_shares = h['shares'] + shares
                    h['avg_cost'] = (h['total_cost'] + total_cost) / total_shares
                else:
                    h['avg_cost'] = price
                h['shares'] += shares
                h['total_cost'] += total_cost
                cash_balance -= total_cost  # 现金被消耗
                trade_count += 1

        elif diff < -monthly_amount * 0.05:  # 需要止盈卖出
            # 卖出超出的部分，按 allocation 比例
            sell_value = -diff
            for c in codes:
                h = holdings[c]
                if h['shares'] <= 0:
                    continue
                kd = kline_data.get(c, {})
                if dca_date not in kd:
                    continue
                price = kd[dca_date]['close']
                sell_amount = sell_value * allocation.get(c, 0)
                sell_shares = int(sell_amount / price / 100) * 100
                if sell_shares <= 0:
                    continue
                if sell_shares > h['shares']:
                    sell_shares = int(h['shares'] / 100) * 100
                if sell_shares <= 0:
                    continue
                sell_proceeds = sell_shares * price
                commission = sell_proceeds * config.get('commission_rate', 0.0001)
                net = sell_proceeds - commission
                ratio = sell_shares / h['shares']
                h['total_cost'] *= (1 - ratio)
                h['shares'] -= sell_shares
                if h['shares'] == 0:
                    h['avg_cost'] = 0
                    h['total_cost'] = 0
                cash_balance += net
                trade_count += 1
                stop_profit_count += 1

        # 检查止盈阈值（20%）单独止盈
        for c in codes:
            h = holdings[c]
            if h['shares'] <= 0:
                continue
            if h.get('freeze_until', '') >= dca_date:
                continue
            kd = kline_data.get(c, {})
            if dca_date not in kd:
                continue
            price = kd[dca_date]['close']
            current_value_c = price * h['shares']
            profit_pct = (current_value_c / h['total_cost'] - 1) if h['total_cost'] > 0 else 0
            if profit_pct >= stop_threshold:
                sell_value_c = current_value_c
                commission = sell_value_c * config.get('commission_rate', 0.0001)
                net = sell_value_c - commission
                cash_balance += net
                h['shares'] = 0
                h['total_cost'] = 0
                h['avg_cost'] = 0
                h['freeze_until'] = (datetime.strptime(dca_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
                stop_profit_count += 1

        # 止盈资金按低配类别轮动
        if cash_balance > monthly_amount * 0.5:
            cash_balance = _reinvest_low_weight_category(
                cash_balance, holdings, codes, allocation, kline_data, dca_date, config
            )

        # 记录月末市值
        month_end_value = cash_balance
        for c in codes:
            h = holdings[c]
            if h['shares'] > 0:
                kd = kline_data.get(c, {})
                if dca_date in kd:
                    month_end_value += kd[dca_date]['close'] * h['shares']
                else:
                    month_end_value += h['total_cost']
        daily_values.append((dca_date, month_end_value))

    # 期末市值
    final_date = dca_dates[-1]
    final_value = cash_balance
    for c in codes:
        h = holdings[c]
        if h['shares'] <= 0:
            continue
        kd = kline_data.get(c, {})
        if final_date in kd:
            final_value += kd[final_date]['close'] * h['shares']
        else:
            dates_with_data = sorted(kd.keys())
            last_date = dates_with_data[-1] if dates_with_data else ''
            price = kd[last_date]['close'] if last_date else h['avg_cost']
            final_value += price * h['shares']

    # 绩效指标
    total_return = final_value - total_invested
    total_return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0
    n_months = len(dca_dates)
    annual_return_pct = ((final_value / total_invested) ** (12 / n_months) - 1) * 100 if n_months >= 3 and total_invested > 0 else 0

    # 最大回撤
    max_dd = 0.0
    peak = 0.0
    for _, v in daily_values:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak * 100
            if dd > max_dd:
                max_dd = dd

    # 夏普比率
    sharpe = 0.0
    if len(daily_values) >= 3:
        monthly_rets = []
        for i in range(1, len(daily_values)):
            prev_value = daily_values[i-1][1]
            cur_value = daily_values[i][1]
            monthly_ret = (cur_value - prev_value - config['monthly_amount']) / max(prev_value, 1)
            monthly_rets.append(monthly_ret)
        if len(monthly_rets) >= 2:
            import numpy as np
            avg_ret = float(np.mean(monthly_rets))
            std_ret = max(float(np.std(monthly_rets)), 0.001)
            sharpe = round(avg_ret / std_ret * math.sqrt(12), 2)

    return {
        "config": {
            "monthly_amount": monthly_amount,
            "allocation": allocation,
            "stop_profit_threshold": stop_threshold,
            "start_date": start_date,
            "end_date": end_date,
            "strategy": "value_averaging",
        },
        "total_invested": round(total_invested, 2),
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 2),
        "total_return_pct": round(total_return_pct, 2),
        "annual_return_pct": round(annual_return_pct, 2),
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": round(max_dd, 2),
        "dca_count": n_months,
        "stop_profit_count": stop_profit_count,
        "trade_count": trade_count,
        "final_cash": round(cash_balance, 2),
        "strategy": "value_averaging",
        "holdings": {c: {'shares': h['shares'],
                         'avg_cost': round(h['avg_cost'], 4),
                         'total_cost': round(h['total_cost'], 2),
                         'market_value': round(_holding_market_value(h, kline_data.get(c, {}), final_date), 2)}
                     for c, h in holdings.items()},
    }


def compare_strategies(config: dict, start_date: str, end_date: str):
    """对比 DCA vs VA 策略"""
    print(f"\n{'='*70}")
    print(f"  📊 策略对比回测: DCA vs Value Averaging")
    print(f"{'='*70}")
    print(f"  回测区间: {start_date} ~ {end_date}")
    print(f"  每月金额: ¥{config['monthly_amount']}")
    print(f"  止盈阈值: {config['stop_profit_threshold']*100:.0f}%\n")

    dca_result = simulate_monthly_dca(config, start_date, end_date)
    va_result = simulate_value_averaging(config, start_date, end_date)

    if 'error' in dca_result or 'error' in va_result:
        print("  ❌ 回测失败")
        return None

    # 对比表
    print(f"{'='*70}")
    print(f"  {'指标':<20} {'DCA 定投':>18} {'VA 价值平均':>18} {'差异':>12}")
    print(f"{'='*70}")
    metrics = [
        ('总投入', 'total_invested', '¥{:,.2f}'),
        ('期末价值', 'final_value', '¥{:,.2f}'),
        ('总收益', 'total_return', '¥{:+,.2f}'),
        ('总收益率', 'total_return_pct', '{:+.2f}%'),
        ('年化收益率', 'annual_return_pct', '{:+.2f}%'),
        ('夏普比率', 'sharpe_ratio', '{:.2f}'),
        ('最大回撤', 'max_drawdown_pct', '{:.2f}%'),
        ('止盈次数', 'stop_profit_count', '{}'),
    ]
    for name, key, fmt in metrics:
        dca_v = dca_result.get(key, 0)
        va_v = va_result.get(key, 0)
        try:
            dca_str = fmt.format(dca_v)
            va_str = fmt.format(va_v)
            if isinstance(dca_v, (int, float)) and isinstance(va_v, (int, float)):
                diff = va_v - dca_v
                diff_str = f"{diff:+.2f}" if key in ('total_return_pct', 'annual_return_pct', 'sharpe_ratio', 'max_drawdown_pct') else ''
            else:
                diff_str = ''
        except Exception:
            dca_str = str(dca_v)
            va_str = str(va_v)
            diff_str = ''
        print(f"  {name:<20} {dca_str:>18} {va_str:>18} {diff_str:>12}")

    # 给出建议
    print(f"\n{'='*70}")
    if va_result['total_return_pct'] > dca_result['total_return_pct'] + 2:
        print(f"  ✅ VA 价值平均法收益率领先 {va_result['total_return_pct'] - dca_result['total_return_pct']:.2f}%")
        print(f"     建议：在波动较大的 ETF 池中可考虑切换到 VA 策略")
    elif dca_result['total_return_pct'] > va_result['total_return_pct'] + 2:
        print(f"  ✅ DCA 定投收益率领先 {dca_result['total_return_pct'] - va_result['total_return_pct']:.2f}%")
        print(f"     建议：当前市场下 DCA 更优，保持现有策略")
    else:
        print(f"  ➡️  两种策略效果接近，DCA 更简单稳定，VA 更激进")

    return {'dca': dca_result, 'va': va_result}


def grid_search(start_date: str, end_date: str):
    """
    参数网格搜索：寻找最优定投参数组合
    """
    print("\n" + "=" * 60)
    print("  定投策略参数网格搜索")
    print("=" * 60)

    # 搜索空间
    search_space = {
        'monthly_amount': [1000, 2000, 3000, 5000],
        'stop_profit_threshold': [0.10, 0.15, 0.20, 0.25, 0.30],
    }

    # 不同配比方案
    allocation_plans = {
        '平衡型(20-40-25-15)': {
            '515080': 0.20, '510300': 0.20, '510500': 0.20,
            '512760': 0.125, '512010': 0.125, '513100': 0.15,
        },
        '红利偏重(40-30-15-15)': {
            '515080': 0.40, '510300': 0.15, '510500': 0.15,
            '512760': 0.10, '512010': 0.05, '513100': 0.15,
        },
        '宽基偏重(10-50-25-15)': {
            '515080': 0.10, '510300': 0.25, '510500': 0.25,
            '512760': 0.125, '512010': 0.125, '513100': 0.15,
        },
        '成长激进(10-30-45-15)': {
            '515080': 0.10, '510300': 0.15, '510500': 0.15,
            '512760': 0.25, '512010': 0.20, '513100': 0.15,
        },
    }

    all_results = []

    for plan_name, allocation in allocation_plans.items():
        for amount in search_space['monthly_amount']:
            for threshold in search_space['stop_profit_threshold']:
                config = {
                    'monthly_amount': amount,
                    'commission_rate': 0.0001,
                    'stop_profit_threshold': threshold,
                    'allocation': allocation,
                }
                result = simulate_monthly_dca(config, start_date, end_date)
                if 'error' in result:
                    continue
                result['plan_name'] = plan_name
                result['allocation_name'] = plan_name
                all_results.append(result)
                print(f"  {plan_name:<16} ¥{amount:<5} TP={threshold:.0%} → "
                      f"收益={result['total_return_pct']:+.1f}% "
                      f"年化={result['annual_return_pct']:+.1f}% "
                      f"夏普={result['sharpe_ratio']:.2f}")

    # 按夏普比率排序
    all_results.sort(key=lambda r: r['sharpe_ratio'], reverse=True)

    print(f"\n{'='*60}")
    print(f"  🏆 最优参数组合 (Top 5)")
    print(f"{'='*60}")
    for i, r in enumerate(all_results[:5]):
        print(f"  {i+1}. {r['plan_name']:<16} "
              f"每月¥{r['config']['monthly_amount']:<5} "
              f"止盈{r['config']['stop_profit_threshold']:.0%} → "
              f"收益{r['total_return_pct']:+.1f}% "
              f"年化{r['annual_return_pct']:+.1f}% "
              f"夏普{r['sharpe_ratio']:.2f}")

    return all_results[:5]


def main():
    parser = argparse.ArgumentParser(description="定投策略回测模块")
    parser.add_argument('--start', default='2024-06-01', help='回测开始日期')
    parser.add_argument('--end', default=datetime.now().strftime('%Y-%m-%d'), help='回测结束日期')
    parser.add_argument('--grid-search', action='store_true', help='参数网格搜索')
    parser.add_argument('--amount', type=int, default=3000, help='每月定投金额')
    parser.add_argument('--threshold', type=float, default=0.20, help='止盈阈值')
    parser.add_argument('--strategy', choices=['dca', 'va', 'compare'], default='dca',
                        help='策略：dca=定投（默认），va=价值平均法，compare=两者对比')
    args = parser.parse_args()

    if args.grid_search:
        print(f"\n📊 参数网格搜索: {args.start} ~ {args.end}")
        grid_search(args.start, args.end)
        return

    config = {
        'monthly_amount': args.amount,
        'commission_rate': 0.0001,
        'stop_profit_threshold': args.threshold,
        'allocation': DEFAULT_CONFIG['allocation'],
    }

    if args.strategy == 'compare':
        compare_strategies(config, args.start, args.end)
        return

    strategy_name = 'DCA 定投' if args.strategy == 'dca' else 'VA 价值平均法'
    print(f"\n📊 {strategy_name}策略回测: {args.start} ~ {args.end}")

    if args.strategy == 'va':
        result = simulate_value_averaging(config, args.start, args.end)
    else:
        result = simulate_monthly_dca(config, args.start, args.end)

    if 'error' in result:
        print(f"\n  ❌ {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"  📋 回测结果（{strategy_name}）")
    print(f"{'='*60}")
    print(f"  总投入:        ¥{result['total_invested']:>10,.2f}")
    print(f"  期末价值:      ¥{result['final_value']:>10,.2f}")
    print(f"  总收益:        ¥{result['total_return']:>+10,.2f}")
    print(f"  总收益率:      {result['total_return_pct']:>+9.2f}%")
    print(f"  年化收益率:    {result['annual_return_pct']:>+9.2f}%")
    print(f"  夏普比率:      {result['sharpe_ratio']:>9.2f}")
    print(f"  最大回撤:      {result['max_drawdown_pct']:>8.2f}%")
    print(f"  定投次数:      {result['dca_count']:>10}")
    print(f"  止盈触发次数:  {result['stop_profit_count']:>10}")
    if 'trade_count' in result:
        print(f"  总交易次数:    {result['trade_count']:>10}")


if __name__ == '__main__':
    main()
