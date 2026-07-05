#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投止盈轮动模块 - dca_stop_profit.py
功能：
1. 检查各ETF持仓是否达到止盈阈值（20%）
2. 执行止盈卖出
3. 止盈后资金按"低配类别优先"策略再投资
4. 生成止盈轮动报告
"""

import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Windows GBK 编码兼容：stdout 遇到 emoji 不崩溃
if sys.stdout.encoding and sys.stdout.encoding.upper() in ('GBK', 'CP936', 'GB2312'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from dca_config import STOP_PROFIT_ROTATION_CONFIG, CATEGORY_TARGETS, ETF_PORTFOLIO
    STOP_PROFIT_CONFIG = STOP_PROFIT_ROTATION_CONFIG.copy()
except ImportError:
    STOP_PROFIT_CONFIG = {
        'threshold': 0.20,
        'use_dynamic_threshold': False,
        'dynamic_threshold_config': {
            'market_volatility_factor': 0.5,
            'min_threshold': 0.15,
            'max_threshold': 0.30,
            'lookback_days': 20,
        },
        'per_etf_thresholds': {},
        'sell_ratio': 1.0,
        'reinvest_priority': 'underweight_category',
        'min_hold_days': 30,
        'commission_rate': 0.0001,
        'min_commission': 0.2,
        'min_shares': 100,
        'freeze_days': 30,
    }

try:
    from dca_config import CATEGORY_TARGETS, ETF_PORTFOLIO
except ImportError:
    CATEGORY_TARGETS = {
        '红利': 0.20,
        '宽基': 0.40,
        '行业': 0.25,
        '海外': 0.15,
    }

try:
    from dca_config import ETF_PORTFOLIO
    ETF_TARGETS = {}
    for etf in ETF_PORTFOLIO:
        ETF_TARGETS[etf['code']] = {
            'name': etf['name'],
            'category': etf['category'],
            'target': etf.get('allocation', 0.2)
        }
except ImportError:
    ETF_TARGETS = {
        '515080': {'name': '中证红利ETF', 'category': '红利', 'target': 0.20},
        '510300': {'name': '沪深300ETF', 'category': '宽基', 'target': 0.20},
        '510500': {'name': '中证500ETF', 'category': '宽基', 'target': 0.20},
        '512760': {'name': '芯片ETF', 'category': '行业', 'target': 0.125},
        '512010': {'name': '医药ETF', 'category': '行业', 'target': 0.125},
        '513100': {'name': '纳指ETF', 'category': '海外', 'target': 0.15},
    }


class StopProfitManager:
    """止盈轮动管理器"""

    def __init__(self, portfolio_manager, data_dir=None):
        """
        :param portfolio_manager: PortfolioManager 实例
        :param data_dir: 数据存储目录
        """
        self.pm = portfolio_manager
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = script_dir
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, 'stop_profit_history.json')
        self.frozen_etfs: Dict[str, str] = {}  # {code: unfreeze_date}
        self.history: List[dict] = []
        self.load_history()

    def load_history(self):
        """加载止盈历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('history', [])
                    self.frozen_etfs = data.get('frozen_etfs', {})
            except Exception as e:
                print(f"[止盈] 加载历史失败: {e}")
                self.history = []
                self.frozen_etfs = {}

    def save_history(self):
        """保存止盈历史"""
        data = {
            'history': self.history,
            'frozen_etfs': self.frozen_etfs,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[止盈] 保存历史失败: {e}")

    def get_prices(self) -> Dict[str, dict]:
        """获取所有持仓的价格 —— 改为读价格缓存，不再实时调行情"""
        from dca_price_cache import get_all_cached_prices, refresh_prices

        cache = get_all_cached_prices()
        if cache:
            # 有当天缓存 → 直接用
            return {code: {"code": code, "price": p, "success": True, "source": "cache"}
                    for code, p in cache.items()
                    if code in self.pm.holdings and self.pm.holdings[code]['shares'] > 0}
        else:
            # 无缓存 → 自动刷新一次（兜底）
            print("  [止盈] 价格缓存为空，执行一次行情刷新...")
            refresh_prices()
            cache = get_all_cached_prices()
            return {code: {"code": code, "price": p, "success": True, "source": "cache"}
                    for code, p in cache.items()
                    if code in self.pm.holdings and self.pm.holdings[code]['shares'] > 0}

    def calculate_dynamic_threshold(self, etf_code: str) -> float:
        """
        计算单个ETF的动态止盈阈值
        :param etf_code: ETF代码
        :return: 动态计算的止盈阈值
        """
        base_threshold = STOP_PROFIT_CONFIG.get('threshold', 0.20)
        per_etf = STOP_PROFIT_CONFIG.get('per_etf_thresholds', {})
        if etf_code in per_etf:
            return per_etf[etf_code]

        if not STOP_PROFIT_CONFIG.get('use_dynamic_threshold', False):
            return base_threshold

        config = STOP_PROFIT_CONFIG.get('dynamic_threshold_config', {})
        lookback_days = config.get('lookback_days', 20)
        min_th = config.get('min_threshold', 0.15)
        max_th = config.get('max_threshold', 0.30)
        vol_factor = config.get('market_volatility_factor', 0.5)

        volatility = self._calculate_etf_volatility(etf_code, lookback_days)

        dynamic_threshold = base_threshold + (volatility - 0.15) * vol_factor
        dynamic_threshold = max(min_th, min(max_th, dynamic_threshold))

        return round(dynamic_threshold, 4)

    def _calculate_etf_volatility(self, etf_code: str, lookback_days: int) -> float:
        """
        计算ETF的历史波动率（基于日收益率标准差）
        :param etf_code: ETF代码
        :param lookback_days: 回溯天数
        :return: 年化波动率
        """
        try:
            import numpy as np
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=lookback_days * 2)).strftime('%Y%m%d')

            import akshare as ak
            try:
                df = ak.fund_etf_hist_em(symbol=etf_code, period='daily',
                                        start_date=start_date, end_date=end_date)
            except Exception:
                return 0.15

            if df is None or df.empty or '收盘' not in df.columns:
                return 0.15

            df = df.tail(lookback_days)
            if len(df) < 5:
                return 0.15

            prices = df['收盘'].values
            returns = np.diff(prices) / prices[:-1]
            daily_vol = np.std(returns)
            annual_vol = daily_vol * np.sqrt(252)

            return float(annual_vol)
        except Exception as e:
            print(f"  [止盈] 计算{etf_code}波动率失败: {e}")
            return 0.15

    def get_threshold_info(self) -> Dict[str, dict]:
        """
        获取所有持仓ETF的止盈阈值信息
        :return: {code: {'base_threshold': float, 'dynamic_threshold': float, 'volatility': float}}
        """
        info = {}
        lookback = STOP_PROFIT_CONFIG.get('dynamic_threshold_config', {}).get('lookback_days', 20)

        for code in self.pm.holdings:
            if self.pm.holdings[code]['shares'] <= 0:
                continue
            volatility = self._calculate_etf_volatility(code, lookback)
            dynamic_th = self.calculate_dynamic_threshold(code)
            info[code] = {
                'base_threshold': STOP_PROFIT_CONFIG.get('threshold', 0.20),
                'dynamic_threshold': dynamic_th,
                'volatility': round(volatility, 4),
                'name': self.pm.holdings[code].get('name', ETF_TARGETS.get(code, {}).get('name', code))
            }
        return info

    def check_stop_profit_signals(self, prices: Dict[str, dict]) -> List[dict]:
        """
        检查止盈信号（支持动态阈值）
        :param prices: {code: {'price': float, ...}}
        :return: 止盈信号列表 [{code, name, profit_pct, shares, market_value, ...}]
        """
        signals = []
        today = datetime.now().strftime('%Y-%m-%d')

        threshold_info = self.get_threshold_info() if STOP_PROFIT_CONFIG.get('use_dynamic_threshold', False) else {}

        for code, holding in self.pm.holdings.items():
            if holding['shares'] <= 0:
                continue
            if code not in prices:
                continue
            # 检查是否在冻结期
            if code in self.frozen_etfs:
                unfreeze_date = self.frozen_etfs[code]
                if today < unfreeze_date:
                    continue
                else:
                    del self.frozen_etfs[code]

            current_price = prices[code]['price']
            avg_cost = holding['avg_cost']
            if avg_cost <= 0:
                continue

            profit_pct = (current_price - avg_cost) / avg_cost
            market_value = holding['shares'] * current_price
            cost_total = holding['total_cost']
            profit_amount = market_value - cost_total

            effective_threshold = STOP_PROFIT_CONFIG['threshold']
            if code in threshold_info:
                effective_threshold = threshold_info[code]['dynamic_threshold']

            if profit_pct >= effective_threshold:
                signals.append({
                    'code': code,
                    'name': holding.get('name', ETF_TARGETS.get(code, {}).get('name', code)),
                    'category': holding.get('category', ETF_TARGETS.get(code, {}).get('category', '')),
                    'profit_pct': round(profit_pct * 100, 2),
                    'profit_amount': round(profit_amount, 2),
                    'shares': holding['shares'],
                    'avg_cost': round(avg_cost, 4),
                    'current_price': round(current_price, 4),
                    'market_value': round(market_value, 2),
                    'cost_total': round(cost_total, 2),
                    'threshold': effective_threshold * 100,
                    'is_dynamic': code in threshold_info,
                })

        # 按收益率降序排列
        signals.sort(key=lambda s: s['profit_pct'], reverse=True)
        return signals

    def execute_stop_profit(self, signal: dict) -> Optional[dict]:
        """
        执行止盈卖出
        :param signal: 止盈信号
        :return: 交易记录或None
        """
        code = signal['code']
        shares_to_sell = int(signal['shares'] * STOP_PROFIT_CONFIG['sell_ratio'])
        shares_to_sell = int(shares_to_sell / STOP_PROFIT_CONFIG['min_shares']) * STOP_PROFIT_CONFIG['min_shares']

        if shares_to_sell <= 0:
            print(f"  [止盈] {code} 卖出份额为0，跳过")
            return None

        price = signal['current_price']
        trade_amount = shares_to_sell * price
        commission = max(trade_amount * STOP_PROFIT_CONFIG.get('commission_rate', 0.0001),
                        STOP_PROFIT_CONFIG.get('min_commission', 0.2))
        net_amount = trade_amount - commission

        # 更新持仓
        holding = self.pm.holdings[code]
        if shares_to_sell >= holding['shares']:
            # 全部卖出
            net_amount = holding['shares'] * price - commission
            holding['shares'] = 0
            holding['total_cost'] = 0
            holding['avg_cost'] = 0
        else:
            # 部分卖出
            sell_ratio = shares_to_sell / holding['shares']
            cost_reduced = holding['total_cost'] * sell_ratio
            holding['shares'] -= shares_to_sell
            holding['total_cost'] = round(holding['total_cost'] - cost_reduced, 2)
            if holding['shares'] > 0:
                holding['avg_cost'] = round(holding['total_cost'] / holding['shares'], 4)
            else:
                holding['avg_cost'] = 0

        # 加入现金余额
        self.pm.cash_balance += net_amount

        # 冻结该ETF（避免马上再投回来）
        unfreeze_date = (datetime.now() + timedelta(days=STOP_PROFIT_CONFIG['freeze_days'])).strftime('%Y-%m-%d')
        self.frozen_etfs[code] = unfreeze_date

        trade_record = {
            'success': True,
            'code': code,
            'name': signal['name'],
            'type': 'stop_profit',
            'price': round(price, 4),
            'shares': shares_to_sell,
            'trade_amount': round(trade_amount, 2),
            'commission': round(commission, 2),
            'total_cost': round(trade_amount + commission, 2),  # 卖出总成本=金额+佣金
            'net_amount': round(net_amount, 2),
            'profit_pct': signal['profit_pct'],
            'profit_amount': signal['profit_amount'],
            'remaining_shares': holding['shares'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': f"止盈卖出（盈利{signal['profit_pct']}%）",
            'planned_amount': net_amount,
        }
        self.pm.trade_history.append(trade_record)

        return trade_record

    def calc_category_allocation(self) -> Dict[str, dict]:
        """
        计算当前各类别的实际配比与目标配比偏差
        :return: {category: {'current_pct': float, 'target_pct': float, 'deviation': float, 'status': str}}
        """
        total_value = 0
        category_values = {cat: 0.0 for cat in CATEGORY_TARGETS}

        # 获取当前价格（用于计算市值）
        prices = self.get_prices()

        for code, holding in self.pm.holdings.items():
            if code not in ETF_TARGETS:
                continue
            cat = ETF_TARGETS[code]['category']
            current_price = prices.get(code, {}).get('price', holding['avg_cost'])
            value = holding['shares'] * current_price
            category_values[cat] += value
            total_value += value

        # 加上现金余额
        total_value += self.pm.cash_balance

        result = {}
        for cat, current_val in category_values.items():
            target_pct = CATEGORY_TARGETS[cat]
            current_pct = current_val / total_value if total_value > 0 else 0
            deviation = current_pct - target_pct
            result[cat] = {
                'current_value': round(current_val, 2),
                'current_pct': round(current_pct * 100, 2),
                'target_pct': round(target_pct * 100, 2),
                'deviation': round(deviation * 100, 2),
                'status': '低配' if deviation < -0.01 else ('超配' if deviation > 0.01 else '均衡')
            }

        return result

    def find_reinvest_targets(self, freed_capital: float) -> List[dict]:
        """
        按"低配类别优先"策略筛选再投资目标
        :param freed_capital: 止盈释放的资金
        :return: 再投资目标列表 [{code, name, category, amount, reason}, ...]
        """
        if freed_capital <= 0:
            return []

        # 计算类别偏差
        cat_alloc = self.calc_category_allocation()

        # 按偏差升序排列（最负的=最需要补的排最前）
        sorted_cats = sorted(cat_alloc.items(), key=lambda x: x[1]['deviation'])

        targets = []
        remaining_capital = freed_capital

        for cat_name, cat_info in sorted_cats:
            if remaining_capital <= 10:  # 资金太少不值得分
                break
            if cat_info['deviation'] >= -1:  # 偏差在-1%以内视为均衡
                # 如果所有类别都均衡，按目标配比均匀分配
                if all(c['deviation'] >= -1 for _, c in sorted_cats):
                    # 按各ETF目标占比分配
                    for code, etf in ETF_TARGETS.items():
                        if code in self.frozen_etfs:
                            continue
                        if code not in self.pm.holdings:
                            continue
                        holding = self.pm.holdings.get(code, {})
                        price = self.get_prices().get(code, {}).get('price', 0)
                        if price <= 0:
                            continue
                        amount = round(freed_capital * etf['target'], 2)
                        if amount >= 10:
                            targets.append({
                                'code': code,
                                'name': etf['name'],
                                'category': etf['category'],
                                'amount': amount,
                                'current_price': price,
                                'avg_cost': holding.get('avg_cost', price),
                                'reason': '均衡分配'
                            })
                            remaining_capital -= amount
                    break

            # 获取该类别下未被冻结的ETF
            cat_etfs = []
            for code, etf in ETF_TARGETS.items():
                if etf['category'] == cat_name:
                    if code not in self.frozen_etfs:
                        holding = self.pm.holdings.get(code, {})
                        price = self.get_prices().get(code, {}).get('price', 0)
                        if price > 0:
                            # 计算该ETF当前的估值便宜度（简单用PE/当前价vs成本）
                            cat_etfs.append({
                                'code': code,
                                'name': etf['name'],
                                'category': cat_name,
                                'target': etf['target'],
                                'current_price': price,
                                'avg_cost': holding.get('avg_cost', price),
                            })

            if not cat_etfs:
                continue

            # 该类别的资金额度 = freed_capital * 该类别目标占比 / 未分配类别目标占比总和
            unallocated_cats = [cat for cat, c in sorted_cats if c['deviation'] < -1]
            unallocated_total = sum(CATEGORY_TARGETS[cat] for cat, c in sorted_cats if c['deviation'] < -1)
            if unallocated_total > 0:
                cat_amount = round(freed_capital * CATEGORY_TARGETS[cat_name] / unallocated_total, 2)
            else:
                cat_amount = round(freed_capital * CATEGORY_TARGETS[cat_name], 2)

            cat_amount = min(cat_amount, remaining_capital)

            # 按该类内ETF目标配比分
            cat_total_target = sum(etf['target'] for etf in cat_etfs)
            for etf in cat_etfs:
                etf_amount = round(cat_amount * etf['target'] / cat_total_target, 2)
                if etf_amount >= 10:
                    targets.append({
                        'code': etf['code'],
                        'name': etf['name'],
                        'category': etf['category'],
                        'amount': etf_amount,
                        'current_price': etf['current_price'],
                        'avg_cost': etf['avg_cost'],
                        'reason': f"低配类别·{cat_name}（偏差{cat_info['deviation']}%）"
                    })

            remaining_capital -= cat_amount

        return targets

    def execute_reinvest(self, targets: List[dict]) -> List[dict]:
        """
        执行再投资交易
        :param targets: 再投资目标列表
        :return: 交易结果列表
        """
        results = []

        for target in targets:
            if target['amount'] < 10:
                continue

            price = target['current_price']
            min_shares = STOP_PROFIT_CONFIG['min_shares']

            # 计算可买手数
            shares = int(target['amount'] / price / min_shares) * min_shares
            if shares <= 0:
                print(f"  [再投] {target['code']} 金额不足1手，跳过")
                continue

            trade_amount = shares * price
            commission = max(trade_amount * STOP_PROFIT_CONFIG.get('commission_rate', 0.0001),
                        STOP_PROFIT_CONFIG.get('min_commission', 0.2))
            total_cost = trade_amount + commission

            if total_cost > self.pm.cash_balance:
                # 调整股数以适应当前现金
                affordable = self.pm.cash_balance - commission
                shares = int(affordable / price / min_shares) * min_shares
                if shares <= 0:
                    continue
                trade_amount = shares * price

            # 更新持仓
            code = target['code']
            if code not in self.pm.holdings:
                self.pm.holdings[code] = {
                    'shares': 0, 'avg_cost': 0, 'total_cost': 0,
                    'name': target['name'], 'category': target['category']
                }

            holding = self.pm.holdings[code]
            new_shares = holding['shares'] + shares
            new_total_cost = holding['total_cost'] + trade_amount
            holding['shares'] = new_shares
            holding['total_cost'] = round(new_total_cost, 2)
            holding['avg_cost'] = round(new_total_cost / new_shares, 4) if new_shares > 0 else 0

            # 扣减现金
            self.pm.cash_balance = round(self.pm.cash_balance - trade_amount, 2)

            result = {
                'success': True,
                'code': code,
                'name': target['name'],
                'type': 'reinvest',
                'price': round(price, 4),
                'shares': shares,
                'trade_amount': round(trade_amount, 2),
                'commission': round(commission, 2),
                'total_cost': round(trade_amount + commission, 2),
                'planned_amount': target['amount'],
                'reason': target.get('reason', '低配类别优先'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'note': f"止盈再投·{target['reason']}"
            }
            self.pm.trade_history.append(result)
            self.pm.total_invested += trade_amount
            results.append(result)

        return results

    def run_daily_check(self, prices: Dict[str, dict] = None) -> dict:
        """
        每日止盈轮动检查
        :param prices: 可选，预获取的价格数据
        :return: 执行结果摘要
        """
        print("\n" + "=" * 80)
        print("止盈轮动检查")
        print("=" * 80)

        # 1. 获取价格
        if prices is None:
            prices = self.get_prices()
        if not prices:
            print("  无法获取任何ETF价格，跳过止盈检查")
            return {'success': False, 'message': '无法获取价格'}

        print(f"\n  当前持仓状态:")
        for code, holding in self.pm.holdings.items():
            if holding['shares'] > 0 and code in prices:
                current_price = prices[code]['price']
                profit_pct = (current_price - holding['avg_cost']) / holding['avg_cost'] * 100 if holding['avg_cost'] > 0 else 0
                print(f"    {code} ({holding['name']}): "
                      f"持仓{holding['shares']}股, "
                      f"成本{holding['avg_cost']:.4f}, "
                      f"现价{current_price:.4f}, "
                      f"盈亏{profit_pct:+.2f}%")

        # 2. 检查止盈信号
        signals = self.check_stop_profit_signals(prices)
        print(f"\n  止盈信号检查: 发现{len(signals)}个止盈信号")

        stop_profit_trades = []
        total_freed = 0

        for signal in signals:
            print(f"    [!] {signal['code']} ({signal['name']}): "
                  f"盈利{signal['profit_pct']}% >= {signal['threshold']}%"
                  f"{' [动态]' if signal.get('is_dynamic') else ''}")
            trade = self.execute_stop_profit(signal)
            if trade:
                stop_profit_trades.append(trade)
                total_freed += trade['net_amount']
                print(f"      [OK] 止盈执行: 卖出{trade['shares']}股, 价格{trade['price']:.4f}, "
                      f"净收入{trade['net_amount']:.2f}元")

        # 3. 再投资
        reinvest_trades = []
        if total_freed > 0:
            print(f"\n  止盈释放资金: {total_freed:.2f}元")
            targets = self.find_reinvest_targets(total_freed)
            print(f"  再投资目标: {len(targets)}个")

            for t in targets:
                print(f"    → {t['code']} ({t['name']}): {t['amount']:.2f}元 [{t['reason']}]")

            reinvest_trades = self.execute_reinvest(targets)
            print(f"\n  再投资执行: {len(reinvest_trades)}笔成交")
            for rt in reinvest_trades:
                print(f"    [OK] {rt['code']} ({rt['name']}): "
                      f"买入{rt['shares']}股, 价格{rt['price']:.4f}, 金额{rt['trade_amount']:.2f}元")
        else:
            print(f"\n  无止盈信号，无需再投资")

        # 4. 保存
        if stop_profit_trades or reinvest_trades:
            self.history.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'stop_profit_trades': stop_profit_trades,
                'reinvest_trades': reinvest_trades,
                'total_freed': round(total_freed, 2),
                'total_reinvested': round(sum(r['trade_amount'] for r in reinvest_trades), 2),
            })
            self.save_history()
            self.pm.save_data()

        # 5. 生成结果摘要
        result = {
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'signals_count': len(signals),
            'stop_profit_count': len(stop_profit_trades),
            'reinvest_count': len(reinvest_trades),
            'total_freed': round(total_freed, 2),
            'total_reinvested': round(sum(r['trade_amount'] for r in reinvest_trades), 2),
            'cash_remaining': round(self.pm.cash_balance, 2),
            'stop_profit_trades': stop_profit_trades,
            'reinvest_trades': reinvest_trades,
            'category_allocation': self.calc_category_allocation(),
        }

        # 打印汇总
        print(f"\n  {'=' * 60}")
        print(f"  止盈轮动结果汇总")
        print(f"  {'=' * 60}")
        print(f"  止盈信号数:    {len(signals)}")
        print(f"  止盈执行数:    {len(stop_profit_trades)}")
        print(f"  释放资金:      {total_freed:.2f}元")
        print(f"  再投资笔数:    {len(reinvest_trades)}")
        print(f"  再投金额:      {sum(r['trade_amount'] for r in reinvest_trades):.2f}元")
        print(f"  剩余现金:      {self.pm.cash_balance:.2f}元")

        # 打印类别偏差
        print(f"\n  类别配比偏差:")
        cat_alloc = result['category_allocation']
        for cat, info in cat_alloc.items():
            marker = '[低]' if info['status'] == '低配' else ('[高]' if info['status'] == '超配' else '[=]')
            print(f"    {marker} {cat}: 实际{info['current_pct']}% vs 目标{info['target_pct']}% "
                  f"（偏差{info['deviation']:+.2f}%）")

        return result

    def generate_html_report(self, result: dict = None) -> str:
        """生成止盈轮动HTML报告"""
        if result is None:
            result = {}

        script_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(script_dir, 'stop_profit_report.html')

        # 类别偏差表
        cat_rows = ""
        cat_alloc = result.get('category_allocation', {})
        for cat, info in cat_alloc.items():
            color = '#e74c3c' if info['status'] == '低配' else ('#f39c12' if info['status'] == '超配' else '#27ae60')
            cat_rows += f"""<tr>
                <td>{cat}</td>
                <td>{info['current_pct']}%</td>
                <td>{info['target_pct']}%</td>
                <td style="color:{color}">{info['deviation']:+.2f}%</td>
                <td style="color:{color}">{info['status']}</td>
            </tr>"""

        # 止盈交易表
        sp_rows = ""
        sp_trades = result.get('stop_profit_trades', [])
        for t in sp_trades:
            sp_rows += f"""<tr>
                <td>{t['code']}</td>
                <td>{t['name']}</td>
                <td>{t['shares']}股</td>
                <td>¥{t['price']:.4f}</td>
                <td style="color:red">¥{t['net_amount']:.2f}</td>
                <td style="color:red">{t['profit_pct']}%</td>
            </tr>"""

        # 再投交易表
        ri_rows = ""
        ri_trades = result.get('reinvest_trades', [])
        for t in ri_trades:
            ri_rows += f"""<tr>
                <td>{t['code']}</td>
                <td>{t['name']}</td>
                <td>{t['shares']}股</td>
                <td>¥{t['price']:.4f}</td>
                <td style="color:green">¥{t['trade_amount']:.2f}</td>
                <td>{t.get('reason', '')}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>止盈轮动报告 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Microsoft YaHei, Arial; margin: 20px; background: #f8f9fa; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.9; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .summary {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
        .summary-item {{ text-align: center; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); min-width: 150px; }}
        .summary-item .value {{ font-size: 28px; font-weight: bold; color: #667eea; }}
        .summary-item .label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
        th {{ background-color: #667eea; color: white; }}
        .no-data {{ text-align: center; color: #999; padding: 20px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔁 止盈轮动报告</h1>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 阈值: {STOP_PROFIT_CONFIG['threshold']*100}%止盈</p>
    </div>

    <div class="summary">
        <div class="summary-item">
            <div class="value">{result.get('signals_count', 0)}</div>
            <div class="label">止盈信号</div>
        </div>
        <div class="summary-item">
            <div class="value">¥{result.get('total_freed', 0):.2f}</div>
            <div class="label">释放资金</div>
        </div>
        <div class="summary-item">
            <div class="value">¥{result.get('total_reinvested', 0):.2f}</div>
            <div class="label">再投金额</div>
        </div>
        <div class="summary-item">
            <div class="value">¥{result.get('cash_remaining', 0):.2f}</div>
            <div class="label">剩余现金</div>
        </div>
    </div>

    <div class="card">
        <h2>📊 类别配比偏差</h2>
        <table>
            <tr><th>类别</th><th>实际占比</th><th>目标占比</th><th>偏差</th><th>状态</th></tr>
            {cat_rows if cat_rows else '<tr><td colspan="5" class="no-data">暂无数据</td></tr>'}
        </table>
    </div>

    <div class="card">
        <h2>💰 止盈卖出</h2>
        <table>
            <tr><th>代码</th><th>名称</th><th>卖出量</th><th>价格</th><th>净收入</th><th>盈利率</th></tr>
            {sp_rows if sp_rows else '<tr><td colspan="6" class="no-data">今日无止盈卖出</td></tr>'}
        </table>
    </div>

    <div class="card">
        <h2>📈 再投资买入（低配类别优先）</h2>
        <table>
            <tr><th>代码</th><th>名称</th><th>买入量</th><th>价格</th><th>金额</th><th>原因</th></tr>
            {ri_rows if ri_rows else '<tr><td colspan="6" class="no-data">今日无再投资</td></tr>'}
        </table>
    </div>

    <div class="footer">
        <p>⚠️ 以上内容由自动化系统生成，仅供参考，不构成任何投资建议。投资有风险，决策需谨慎。</p>
        <p>策略: {STOP_PROFIT_CONFIG['threshold']*100}%止盈 → 低配类别优先再投 | 冻结期{STOP_PROFIT_CONFIG['freeze_days']}天</p>
    </div>
</body>
</html>"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n[止盈轮动报告] {report_path}")
        return report_path


def run_stop_profit_check(portfolio_manager):
    """一键执行止盈轮动检查"""
    spm = StopProfitManager(portfolio_manager)
    result = spm.run_daily_check()
    spm.generate_html_report(result)
    return result
