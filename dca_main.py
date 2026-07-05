#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投主程序
整合所有模块，提供完整的定投功能
"""

import sys
import os
from datetime import datetime
from dca_config import DCA_CONFIG, ETF_PORTFOLIO
from dca_trading import execute_monthly_dca, get_etf_price, execute_dca_optimized, execute_dca_with_analysis
from dca_portfolio_manager import PortfolioManager
from dca_calendar import is_first_trading_day, get_current_month_info, print_month_trading_info, is_safe_trading_time
from dca_dividend_fetcher import fetch_all_portfolio_dividends

class DCASystem:
    """定投系统主类"""

    def __init__(self):
        """初始化定投系统"""
        self.portfolio_manager = PortfolioManager()
        self.last_run_date = None
        self._last_result = None
        # 当前策略：dca=普通定投，va=价值平均法
        self.strategy = self.portfolio_manager.strategy

    def generate_html_report(self, action="每日检查"):
        """
        生成持仓状态 HTML 报告
        :param action: 本次操作名称
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(script_dir, 'dca_report.html')

        prices = {}
        for etf in ETF_PORTFOLIO:
            price_info = get_etf_price(etf['code'])
            if price_info['success']:
                prices[etf['code']] = {
                    'price': price_info['price'],
                    'source': price_info.get('source', '?')
                }

        pm = self.portfolio_manager
        total_cost = 0
        total_market = 0
        holdings = []
        
        for etf in ETF_PORTFOLIO:
            holding = pm.holdings.get(etf['code'])
            if holding and holding['shares'] > 0:
                current_price = prices.get(etf['code'], {}).get('price', 0)
                cost = holding['total_cost']
                market_value = current_price * holding['shares']
                total_cost += cost
                total_market += market_value
                holdings.append({
                    'code': etf['code'],
                    'name': etf['name'],
                    'shares': holding['shares'],
                    'avg_cost': holding['avg_cost'],
                    'current_price': current_price,
                    'cost': cost,
                    'market_value': market_value,
                    'profit': market_value - cost,
                    'profit_pct': ((market_value - cost) / cost * 100) if cost > 0 else 0
                })

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>定投报告 - {action}</title>
    <style>
        body {{ font-family: Microsoft YaHei, Arial; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
        .summary-item {{ text-align: center; padding: 20px; background: #f5f5f5; border-radius: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        th {{ background-color: #4CAF50; color: white; }}
        .positive {{ color: red; }}
        .negative {{ color: green; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>红利ETF定投报告</h1>
        <p>{action} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="summary">
        <div class="summary-item">
            <div style="font-size: 24px;">¥{total_cost:.2f}</div>
            <div>累计投入</div>
        </div>
        <div class="summary-item">
            <div style="font-size: 24px;">¥{total_market:.2f}</div>
            <div>当前市值</div>
        </div>
        <div class="summary-item">
            <div style="font-size: 24px;" class="{'positive' if (total_market-total_cost)>=0 else 'negative'}">
                ¥{(total_market-total_cost):.2f}
            </div>
            <div>总盈亏</div>
        </div>
        <div class="summary-item">
            <div style="font-size: 24px;" class="{'positive' if (total_market-total_cost)>=0 else 'negative'}">
                {((total_market-total_cost)/total_cost*100 if total_cost>0 else 0):.2f}%
            </div>
            <div>收益率</div>
        </div>
    </div>
    <h2>持仓明细</h2>
    <table>
        <tr><th>代码</th><th>名称</th><th>持仓</th><th>成本价</th><th>现价</th><th>市值</th><th>盈亏</th><th>收益率</th></tr>
        {''.join([f'<tr><td>{h["code"]}</td><td>{h["name"]}</td><td>{h["shares"]}</td><td>{h["avg_cost"]:.4f}</td><td>{h["current_price"]:.4f}</td><td>¥{h["market_value"]:.2f}</td><td class="{"positive" if h["profit"]>=0 else "negative"}">¥{h["profit"]:.2f}</td><td class="{"positive" if h["profit_pct"]>=0 else "negative"}">{h["profit_pct"]:.2f}%</td></tr>' for h in holdings])}
    </table>
</body>
</html>"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[报告已生成] {report_path}")
        return report_path

    def run_dca_cycle(self, force=False, smart_mode=False):
        """
        执行一轮定投
        :param force: 是否强制执行
        :param smart_mode: 是否使用智能模式（根据分析结果调整分配）
        :return: 执行结果
        """
        print("\n" + "=" * 80)
        if smart_mode:
            print("开始智能定投周期（基于分析结果自动调整）")
        else:
            print("开始定投周期")
        print("=" * 80)

        if not force and not is_first_trading_day():
            print("\n今日不是当月第一个交易日，跳过定投")
            print_month_trading_info()
            self.generate_html_report(action="今日跳过（非首交易日）")
            return {'success': False, 'message': '非首交易日'}

        today = datetime.now()
        current_month = today.strftime('%Y-%m')
        if not force and self.portfolio_manager.last_run_month == current_month:
            print(f"\n本月({current_month})已完成定投，跳过")
            self.generate_html_report(action="本月已执行，跳过")
            return {'success': False, 'message': '本月已执行'}

        is_safe, time_reason = is_safe_trading_time()
        if not is_safe:
            print(f"\n当前时间不适合下单: {time_reason}")
            self.generate_html_report(action=f"跳过（{time_reason}）")
            return {'success': False, 'message': f'时间不适合: {time_reason}'}

        # 根据当前策略选择执行方式
        if self.strategy == 'va':
            return self._execute_va_cycle(current_month)
        elif self.strategy == 'rebalance':
            return self._execute_rebalance_cycle(current_month)
        else:
            return self._execute_trade_cycle(current_month, smart_mode)

    def switch_strategy(self, strategy: str) -> bool:
        """
        切换策略
        :param strategy: 'dca' / 'va' / 'rebalance'
        :return: 是否成功
        """
        if strategy not in ('dca', 'va', 'rebalance'):
            return False
        self.strategy = strategy
        self.portfolio_manager.strategy = strategy
        self.portfolio_manager.save_data()
        names = {'dca': '普通定投 (DCA)', 'va': '价值平均法 (VA)', 'rebalance': '百分比再平衡'}
        print(f"\n  策略已切换为: {names[strategy]}")
        return True

    def _execute_va_cycle(self, current_month: str) -> dict:
        """执行价值平均法 VA 月度循环"""
        from dca_value_averaging import execute_va_month, count_elapsed_months

        # 自动分红检查（与 DCA 一致）
        print("\n[自动分红检查] 正在获取最新分红信息...")
        dividend_amount = fetch_all_portfolio_dividends(
            self.portfolio_manager, ETF_PORTFOLIO
        )
        if dividend_amount > 0:
            self.portfolio_manager.save_data()
            print(f"  分红已自动入账: {dividend_amount:.2f}元")

        # 计算已执行月数
        elapsed = count_elapsed_months(self.portfolio_manager)

        # 执行 VA
        result = execute_va_month(
            self.portfolio_manager,
            ETF_PORTFOLIO,
            DCA_CONFIG['monthly_amount'],
            elapsed,
            get_etf_price,
        )

        if not result.get('success'):
            return result

        self.last_run_date = datetime.now().strftime('%Y-%m-%d')
        self.portfolio_manager.last_run_month = current_month

        # 打印持仓概览
        prices = {}
        for etf in ETF_PORTFOLIO:
            price_info = get_etf_price(etf['code'])
            if price_info.get('success'):
                prices[etf['code']] = price_info['price']

        self.portfolio_manager.print_portfolio_summary(prices)

        self.generate_html_report(action=f"VA策略执行完成 - 第{elapsed+1}月")
        self._last_result = result
        return result

    def _execute_rebalance_cycle(self, current_month: str) -> dict:
        """执行百分比再平衡策略月度循环"""
        from dca_value_averaging import execute_rebalance_month

        # 自动分红检查
        print("\n[自动分红检查] 正在获取最新分红信息...")
        dividend_amount = fetch_all_portfolio_dividends(
            self.portfolio_manager, ETF_PORTFOLIO
        )
        if dividend_amount > 0:
            self.portfolio_manager.save_data()
            print(f"  分红已自动入账: {dividend_amount:.2f}元")

        # 执行再平衡
        result = execute_rebalance_month(
            self.portfolio_manager,
            ETF_PORTFOLIO,
            DCA_CONFIG['monthly_amount'],
            get_etf_price,
        )

        if not result.get('success'):
            return result

        self.last_run_date = datetime.now().strftime('%Y-%m-%d')
        self.portfolio_manager.last_run_month = current_month

        # 打印持仓概览
        prices = {}
        for etf in ETF_PORTFOLIO:
            price_info = get_etf_price(etf['code'])
            if price_info.get('success'):
                prices[etf['code']] = price_info['price']

        self.portfolio_manager.print_portfolio_summary(prices)
        self.generate_html_report(action="百分比再平衡执行完成")
        self._last_result = result
        return result

    def _execute_trade_cycle(self, current_month, smart_mode=False):
        """执行交易循环"""
        print("\n[自动分红检查] 正在获取最新分红信息...")
        dividend_amount = fetch_all_portfolio_dividends(
            self.portfolio_manager, ETF_PORTFOLIO
        )
        if dividend_amount > 0:
            self.portfolio_manager.save_data()
            print(f"  分红已自动入账: {dividend_amount:.2f}元")

        print("\n正在获取ETF行情...")
        prices = {}
        for etf in ETF_PORTFOLIO:
            price_info = get_etf_price(etf['code'])
            if price_info['success']:
                prices[etf['code']] = price_info['price']
                print(f"  {etf['code']} ({etf['name']}): {price_info['price']:.4f}元")
            else:
                print(f"  {etf['code']} 获取行情失败")

        if not prices:
            print("\n无法获取任何ETF行情，取消本次定投")
            return {'success': False, 'message': '无法获取行情'}

        # 根据模式选择执行方式
        if smart_mode:
            trade_results = execute_dca_with_analysis(prices, self.portfolio_manager)
        else:
            trade_results = execute_dca_optimized(prices)

        success_trades = [r for r in trade_results if r['success']]
        if success_trades:
            for result in success_trades:
                self.portfolio_manager.add_trade(result)

        actual_spent = sum(r['total_cost'] for r in success_trades)
        self.portfolio_manager.cash_balance = round(DCA_CONFIG['monthly_amount'] - actual_spent, 2)
        print(f"\n  实际花费: {actual_spent:.2f}元, 现金余额: {self.portfolio_manager.cash_balance:.2f}元")

        if self.portfolio_manager.cash_balance > 200:
            re_results = self.portfolio_manager.invest_cash_balance(
                ETF_PORTFOLIO, get_etf_price
            )
            for r in re_results:
                print(f"  再投成功: {r['code']} {r['shares']}股")

        self.portfolio_manager.save_data()

        self.last_run_date = datetime.now().strftime('%Y-%m-%d')
        self.portfolio_manager.last_run_month = current_month

        self.portfolio_manager.print_portfolio_summary(prices)
        self.portfolio_manager.print_trade_history(limit=5)

        result = {
            'success': True,
            'date': self.last_run_date,
            'trades': success_trades,
            'prices': prices
        }
        self._last_result = result
        self.generate_trade_confirm(success_trades, prices)
        self.generate_html_report(action="定投执行完成")
        return result

    def generate_trade_confirm(self, trades, prices=None):
        """生成交易确认单"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        confirm_path = os.path.join(script_dir, f'trade_confirm_{datetime.now().strftime("%Y%m%d")}.html')

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>交易确认单 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Microsoft YaHei, Arial; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        th {{ background-color: #2196F3; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>红利ETF定投交易确认单</h1>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <h2>成交明细</h2>
    <table>
        <tr><th>代码</th><th>名称</th><th>成交数量</th><th>成交价格</th><th>成交金额</th><th>佣金</th><th>费用合计</th></tr>
        {''.join([f'<tr><td>{t["code"]}</td><td>{t["name"]}</td><td>{t["shares"]}股</td><td>¥{t["price"]:.4f}</td><td>¥{t["total_cost"]:.2f}</td><td>¥{t["commission"]:.2f}</td><td>¥{t["total_cost"]:.2f}</td></tr>' for t in trades])}
    </table>
    <p style="text-align: right; margin-top: 20px;">合计投入: ¥{sum(t['total_cost'] for t in trades):.2f}</p>
</body>
</html>"""

        with open(confirm_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[交易确认单已生成] {confirm_path}")
        return confirm_path

    def check_status(self):
        """检查系统状态"""
        print("\n" + "=" * 80)
        print("定投系统状态检查")
        print("=" * 80)
        
        month_info = get_current_month_info()
        print(f"\n当前月份: {month_info.get('year')}年{month_info.get('month')}月")
        print(f"本月交易日: {month_info.get('total_trading_days')}天")
        print(f"首交易日: {month_info.get('first_trading_day')}")
        print(f"今日是否首交易日: {'是' if month_info.get('is_first_day') else '否'}")
        
        print("\n持仓概览:")
        self.portfolio_manager.print_portfolio_summary()
        
        print("\n本月定投状态:")
        if self.portfolio_manager.last_run_month == datetime.now().strftime('%Y-%m'):
            print("  ✓ 本月已完成定投")
        else:
            print("  ✗ 本月尚未定投")

    def run_daily_check(self):
        """
        每日例行检查：交易日判断 + 价格监控 + 持仓状态输出
        由 dca_scheduler.py 每日 09:25 调用
        """
        print("\n" + "=" * 80)
        print(f"【每日检查】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 检查是否交易日
        from dca_calendar import is_holiday
        from datetime import date as _date
        today_d = _date.today()
        if is_holiday(today_d) or today_d.weekday() >= 5:
            print("  ℹ️ 今日非交易日，跳过检查")
            return

        # 检查是否本月首日（触发定投）
        if is_first_trading_day():
            print("  📢 今日是本月首个交易日！")
            current_month = datetime.now().strftime('%Y-%m')
            if self.portfolio_manager.last_run_month != current_month:
                print("  ℹ️ 本月尚未定投，请在 09:30 后执行定投")

        # 获取实时价格
        print("\n  [价格快照]")
        for etf in ETF_PORTFOLIO:
            from dca_trading import get_etf_price
            price_info = get_etf_price(etf['code'])
            if price_info['success']:
                holding = self.portfolio_manager.holdings.get(etf['code'])
                cost_str = f"成本{holding['avg_cost']:.4f}" if holding and holding['shares'] > 0 else "无持仓"
                print(f"    {etf['code']} {etf['name']}: {price_info['price']:.4f} ({cost_str})")
            else:
                print(f"    {etf['code']} {etf['name']}: 获取失败")

        # 持仓概览
        print("\n  [持仓快照]")
        self.portfolio_manager.print_portfolio_summary()
        self.generate_html_report(action="每日检查")

    def check_portfolio_status(self):
        """
        检查投资组合整体状态（用于周报）
        由 dca_scheduler.py 每周五 15:30 调用
        """
        print("\n" + "=" * 80)
        print(f"【投资组合状态】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 获取价格
        prices = {}
        for etf in ETF_PORTFOLIO:
            from dca_trading import get_etf_price
            price_info = get_etf_price(etf['code'])
            if price_info['success']:
                prices[etf['code']] = price_info['price']

        # 打印详细持仓
        total_cost = 0
        total_market = 0
        print(f"\n  {'代码':<8} {'名称':<12} {'持仓':<6} {'成本价':<10} {'现价':<10} {'市值':<10} {'盈亏':<10} {'收益率':<8}")
        print(f"  {'-'*74}")
        for etf in ETF_PORTFOLIO:
            holding = self.portfolio_manager.holdings.get(etf['code'])
            if holding and holding['shares'] > 0:
                cur_price = prices.get(etf['code'], 0)
                cost = holding['total_cost']
                mv = cur_price * holding['shares']
                pnl = mv - cost
                pnl_pct = (pnl / cost * 100) if cost > 0 else 0
                total_cost += cost
                total_market += mv
                print(f"  {etf['code']:<8} {etf['name']:<12} {holding['shares']:<6} {holding['avg_cost']:<10.4f} {cur_price:<10.4f} {mv:<10.2f} {pnl:<+10.2f} {pnl_pct:<+7.2f}%")
            else:
                print(f"  {etf['code']:<8} {etf['name']:<12} {'-':<6} {'-':<10} {'-':<10} {'-':<10} {'-':<10} {'-':<8}")

        pnl_total = total_market - total_cost
        pnl_pct_total = (pnl_total / total_cost * 100) if total_cost > 0 else 0
        print(f"  {'-'*74}")
        print(f"  {'合计':>26} {total_cost:<10.2f} {total_market:<10.2f} {pnl_total:<+10.2f} {pnl_pct_total:<+7.2f}%")
        print(f"  累计投入: {self.portfolio_manager.total_invested:.2f}")
        print(f"  现金余额: {self.portfolio_manager.cash_balance:.2f}")

        # 计算绩效指标
        metrics = self.portfolio_manager.calculate_metrics()
        if metrics:
            print(f"\n  [绩效指标]")
            print(f"    总收益率: {metrics['total_return_pct']:+.2f}%")
            print(f"    年化收益率: {metrics['annual_return_pct']:+.2f}%")
            print(f"    最大回撤: {metrics['max_drawdown_pct']:.2f}%")
            print(f"    夏普比率: {metrics['sharpe_ratio']:.2f}")

        self.generate_html_report(action="投资组合状态")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python dca_main.py [command]")
        print("命令:")
        print("  check       - 检查系统状态")
        print("  run         - 执行定投")
        print("  force       - 强制执行定投（忽略时间检查）")
        print("  stop_profit - 执行止盈轮动检查")
        print("  full        - 执行完整周期（定投+止盈轮动）")
        print("  web         - 启动Web服务并打开浏览器")
        return

    command = sys.argv[1]
    dca = DCASystem()

    if command == 'check':
        dca.check_status()
    elif command == 'run':
        dca.run_dca_cycle()
    elif command == 'force':
        dca.run_dca_cycle(force=True)
    elif command == 'stop_profit':
        from dca_stop_profit import run_stop_profit_check
        result = run_stop_profit_check(dca.portfolio_manager)
        dca.generate_html_report(action="止盈轮动检查")
    elif command == 'full':
        # 完整周期：先定投，再止盈轮动
        dca_result = dca.run_dca_cycle()
        from dca_stop_profit import run_stop_profit_check
        sp_result = run_stop_profit_check(dca.portfolio_manager)
        dca.generate_html_report(action="完整周期（定投+止盈轮动）")
        print("\n完整周期完成！")
    elif command == 'web':
        # 启动Web服务（转发到 dca_web.run）
        from dca_web import run as run_web
        run_web()
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()