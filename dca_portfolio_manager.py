#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理模块
管理定投组合的持仓、收益计算、资金记录等
"""

from datetime import datetime
from dca_config import ETF_PORTFOLIO
import json
import os

class PortfolioManager:
    """持仓管理器"""

    def __init__(self, data_file=None):
        self.data_file = data_file
        if data_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_file = os.path.join(script_dir, 'dca_portfolio_data.json')
        self.holdings = {}
        self.trade_history = []
        self.cash_balance = 0
        self.total_invested = 0
        self.dividend_history = []
        self.last_run_month = None  # 持久化的上次执行月份
        self.strategy = 'dca'  # 当前策略：dca / va
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.holdings = data.get('holdings', {})
                    self.trade_history = data.get('trade_history', [])
                    self.cash_balance = data.get('cash_balance', 0)
                    self.total_invested = data.get('total_invested', 0)
                    self.dividend_history = data.get('dividend_history', [])
                    self.last_run_month = data.get('last_run_month', None)  # 加载上次执行月份
                    self.strategy = data.get('strategy', 'dca')  # 加载当前策略
                print(f"已从 {self.data_file} 加载数据")
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.init_empty_portfolio()
        else:
            self.init_empty_portfolio()

    def save_data(self):
        data = {
            'holdings': self.holdings,
            'trade_history': self.trade_history,
            'cash_balance': self.cash_balance,
            'total_invested': self.total_invested,
            'dividend_history': self.dividend_history,
            'last_run_month': self.last_run_month,  # 保存上次执行月份
            'strategy': self.strategy,  # 保存当前策略
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到 {self.data_file}")
        except Exception as e:
            print(f"保存数据失败: {e}")

    def init_empty_portfolio(self):
        self.holdings = {}
        for etf in ETF_PORTFOLIO:
            self.holdings[etf['code']] = {
                'shares': 0, 'avg_cost': 0, 'total_cost': 0,
                'name': etf['name'], 'category': etf['category']
            }
        self.cash_balance = 0
        self.total_invested = 0
        self.dividend_history = []

    def add_trade(self, trade_result):
        if not trade_result['success']:
            return
        code = trade_result['code']
        shares = trade_result['shares']
        trade_amount = trade_result['trade_amount']
        commission = trade_result['commission']
        planned_amount = trade_result.get('planned_amount', trade_amount + commission)

        # 定投剩余资金加入现金余额
        remaining = round(planned_amount - trade_amount - commission, 2)
        if remaining > 0:
            self.cash_balance += remaining
            print(f"  剩余资金 {remaining:.2f}元 已加入现金余额（当前余额: {self.cash_balance:.2f}元）")

        if code not in self.holdings:
            self.holdings[code] = {
                'shares': 0, 'avg_cost': 0, 'total_cost': 0,
                'name': trade_result.get('name', ''),
                'category': trade_result.get('category', '')
            }

        cur_shares = self.holdings[code]['shares']
        cur_cost = self.holdings[code]['total_cost']
        new_shares = cur_shares + shares
        new_cost = cur_cost + trade_amount + commission

        self.holdings[code]['shares'] = new_shares
        self.holdings[code]['avg_cost'] = round(new_cost / new_shares, 4) if new_shares > 0 else 0
        self.holdings[code]['total_cost'] = round(new_cost, 2)
        self.trade_history.append(trade_result)
        self.total_invested += planned_amount  # 使用计划金额，而不是实际交易金额
        print(f"已更新 {code} 持仓: {new_shares}股, 平均成本 {self.holdings[code]['avg_cost']:.4f}元")

    def add_dividend(self, code, dividend_per_share, ex_dividend_date=None):
        """记录分红并加入现金余额（用于再投）"""
        if code not in self.holdings:
            print(f"  {code} 无持仓，分红忽略")
            return
        shares = self.holdings[code]['shares']
        if shares <= 0:
            return
        dividend_amount = round(shares * dividend_per_share, 2)
        self.cash_balance += dividend_amount
        date_str = ex_dividend_date or datetime.now().strftime('%Y-%m-%d')
        record = {
            'date': date_str, 'code': code,
            'name': self.holdings[code].get('name', ''),
            'shares': shares, 'dividend_per_share': dividend_per_share,
            'dividend_amount': dividend_amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.dividend_history.append(record)
        print(f"  分红到账: {code} {shares}股 × {dividend_per_share}元 = {dividend_amount:.2f}元")
        print(f"  现金余额增加至: {self.cash_balance:.2f}元")

    def invest_cash_balance(self, etf_portfolio, get_price_func):
        """将现金余额按配置比例再投资到ETF"""
        if self.cash_balance <= 0:
            print("  现金余额为0，无需再投")
            return []
        print(f"\n  使用现金余额 {self.cash_balance:.2f}元 进行再投资...")
        results = []
        for etf in etf_portfolio:
            code = etf['code']
            allocation = etf.get('allocation', 0)
            amount = round(self.cash_balance * allocation, 2)
            if amount < 1:
                continue
            price_info = get_price_func(code)
            if not price_info.get('success'):
                print(f"  {code} 获取价格失败，跳过")
                continue
            price = price_info['price']
            min_shares = 100
            shares = int(amount / price / min_shares) * min_shares
            if shares <= 0:
                print(f"  {code} 金额不足购买1手，跳过")
                continue
            trade_amount = shares * price
            commission = max(trade_amount * 0.0001, 5)
            total_cost = trade_amount + commission
            if code not in self.holdings:
                self.holdings[code] = {
                    'shares': 0, 'avg_cost': 0, 'total_cost': 0,
                    'name': etf.get('name', ''), 'category': etf.get('category', '')
                }
            cur_cost = self.holdings[code]['total_cost']
            new_shares = self.holdings[code]['shares'] + shares
            new_cost = cur_cost + total_cost
            self.holdings[code]['shares'] = new_shares
            self.holdings[code]['avg_cost'] = round(new_cost / new_shares, 4) if new_shares > 0 else 0
            self.holdings[code]['total_cost'] = round(new_cost, 2)
            result = {
                'success': True, 'code': code, 'name': etf.get('name', ''),
                'price': price, 'shares': shares,
                'trade_amount': round(trade_amount, 2),
                'commission': round(commission, 2),
                'total_cost': round(total_cost, 2),
                'planned_amount': amount,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'note': '现金余额再投'
            }
            results.append(result)
            self.trade_history.append(result)
            self.total_invested += total_cost
            print(f"  {code} 再投: {shares}股, 成本{round(total_cost, 2)}元")
        # 计算实际再投总金额，剩余的保留在现金余额
        actual_invested = sum(r.get('total_cost', 0) for r in results)
        self.cash_balance = round(self.cash_balance - actual_invested, 2)
        if self.cash_balance < 0:
            self.cash_balance = 0
        print(f"  再投完成: 投入{actual_invested:.2f}元, 剩余现金{self.cash_balance:.2f}元")
        return results

    def print_portfolio_summary(self, prices=None):
        print("\n" + "=" * 80)
        print("定投组合持仓汇总")
        print("=" * 80)
        if not self.holdings:
            print("暂无持仓")
            return
        print(f"\n{'代码':<8} {'名称':<12} {'类别':<6} {'股数':>8} {'平均成本':>10} "
              f"{'当前价':>10} {'市值':>12} {'盈亏':>10} {'收益率':>8}")
        print("-" * 80)
        holdings_value = 0
        total_cost = 0
        for code, holding in self.holdings.items():
            if holding['shares'] > 0:
                current_price = prices.get(code, 0) if prices else 0
                current_value = holding['shares'] * current_price if current_price > 0 else holding['total_cost']
                profit = current_value - holding['total_cost']
                return_rate = (profit / holding['total_cost'] * 100) if holding['total_cost'] > 0 else 0
                print(f"{code:<8} {holding['name']:<12} {holding['category']:<6} "
                      f"{holding['shares']:>8} {holding['avg_cost']:>10.4f} "
                      f"{current_price:>10.4f} {current_value:>12.2f} "
                      f"{profit:>+10.2f} {return_rate:>+8.2f}%")
                holdings_value += current_value
                total_cost += holding['total_cost']
        print("-" * 80)
        total_profit = holdings_value - total_cost
        total_return = (total_profit / total_cost * 100) if total_cost > 0 else 0
        print(f"{'合计':<28} {'':<6} {'':<8} {'':<10} {holdings_value:>12.2f} "
              f"{total_profit:>+10.2f} {total_return:>+8.2f}%")
        print("=" * 80)
        print(f"\n总投入金额: {self.total_invested:.2f}元")
        print(f"当前市值: {holdings_value:.2f}元")
        print(f"总盈亏: {total_profit:+.2f}元")
        print(f"总收益率: {total_return:+.2f}%")
        print(f"现金余额: {self.cash_balance:.2f}元（将用于再投）")
        if self.dividend_history:
            print(f"累计分红次数: {len(self.dividend_history)}次")

    def calculate_metrics(self) -> dict:
        """
        计算投资组合绩效指标
        
        Returns:
            {
                "total_invested": float,
                "current_value": float,
                "total_return_pct": float,
                "annual_return_pct": float,
                "max_drawdown_pct": float,
                "sharpe_ratio": float,
                "trade_count": int,
                "dividend_count": int,
                "month_count": int,
            }
            如果数据不足返回空 dict
        """
        if not self.trade_history or len(self.trade_history) < 2:
            return {}

        # 获取最近的价格
        import numpy as _np

        # 总投入和当前价值
        total_invested = self.total_invested
        # 计算当前持仓市值（使用最后已知价格或成本价）
        current_value = 0
        for code, holding in self.holdings.items():
            if holding['shares'] > 0:
                current_value += holding['total_cost']  # 用成本价作为保守估计
        current_value += self.cash_balance

        # 总收益率
        total_return_pct = ((current_value / total_invested) - 1) * 100 if total_invested > 0 else 0

        # 从交易记录提取月度数据点
        monthly_balances = {}
        for t in self.trade_history:
            ts = t.get('timestamp', '')
            month_key = ts[:7] if len(ts) >= 7 else ''
            if month_key:
                if month_key not in monthly_balances:
                    monthly_balances[month_key] = 0
                monthly_balances[month_key] += t.get('total_cost', 0)

        # 年化收益率
        months = len(monthly_balances)
        n_months = max(months, 1)
        annual_return_pct = ((current_value / total_invested) ** (12 / n_months) - 1) * 100 if total_invested > 0 else 0

        # 最大回撤（基于每月投入的简化版）
        cumulative = 0
        peak = 0
        max_dd = 0
        for month_key in sorted(monthly_balances.keys()):
            cumulative += monthly_balances[month_key]
            # 保守假设：投入后价值不变（无回撤数据时用此替代）
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = round(dd, 2)

        # 夏普比率（简化版：用月度收益计算）
        monthly_returns = []
        prev_cum = 0
        for month_key in sorted(monthly_balances.keys()):
            invested_this_month = monthly_balances[month_key]
            cum_now = prev_cum + invested_this_month
            if prev_cum > 0 and invested_this_month > 0:
                # 保守估计：当月投入立即获得 (current_value/total_invested) 的整体收益率
                month_ret = (current_value / total_invested) - 1  # 统一用整体收益
                monthly_returns.append(month_ret)
            prev_cum = cum_now

        sharpe = 0.0
        if len(monthly_returns) >= 3:
            avg_ret = _np.mean(monthly_returns)
            std_ret = _np.std(monthly_returns)
            if std_ret > 0:
                sharpe = round(avg_ret / std_ret * _np.sqrt(12), 2)  # 年化夏普

        return {
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annual_return_pct": round(annual_return_pct, 2),
            "max_drawdown_pct": max_dd,
            "sharpe_ratio": sharpe,
            "trade_count": len(self.trade_history),
            "dividend_count": len(self.dividend_history),
            "month_count": n_months,
        }

    def print_trade_history(self, limit=10):
        print("\n" + "=" * 80)
        print("最近交易历史")
        print("=" * 80)
        if not self.trade_history:
            print("暂无交易记录")
            return
        recent = self.trade_history[-limit:] if len(self.trade_history) > limit else self.trade_history
        print(f"\n{'日期时间':<20} {'代码':<8} {'名称':<12} {'价格':>8} "
              f"{'股数':>8} {'金额':>10} {'佣金':>8} {'总成本':>10}")
        print("-" * 80)
        for trade in recent:
            print(f"{trade['timestamp']:<20} {trade['code']:<8} {trade.get('name', ''):<12} "
                  f"{trade['price']:>8.4f} {trade['shares']:>8} "
                  f"{trade['trade_amount']:>10.2f} {trade['commission']:>8.2f} "
                  f"{trade['total_cost']:>10.2f}")
        print("-" * 80)
        print(f"交易记录总数: {len(self.trade_history)}条")

    def export_to_csv(self, filename='dca_trade_history.csv'):
        if not self.trade_history:
            print("没有交易记录可导出")
            return
        import pandas as pd  # 延迟导入，避免启动时加载 pandas
        df = pd.DataFrame(self.trade_history)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"交易历史已导出到: {filename}")
        return filename

if __name__ == "__main__":
    pm = PortfolioManager()
    pm.print_portfolio_summary()
    pm.print_trade_history()
