#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易逻辑模块
处理ETF购买逻辑，包括：
- 行情获取
- 交易计算（股数、金额、佣金）
- 交易执行
"""

from datetime import datetime
from dca_config import DCA_CONFIG, ETF_PORTFOLIO

def get_etf_price(code, fallback_to_cost=True, cost_price=None):
    """
    获取ETF实时价格（优化版：增强容错机制）
    优先新浪财经（首选），腾讯备用，akshare备用，华泰备用（额度有限），日线数据最后备用

    Args:
        code: ETF代码
        fallback_to_cost: 价格获取失败时是否返回成本价作为备选
        cost_price: 持仓成本价（可选）

    Returns:
        dict: {
            'code': str,
            'price': float,
            'date': str,
            'source': str,  # ht/sina/tencent/akshare/daily_close/fallback/cost
            'success': bool,
            'note': str (可选),
            'error': str (可选，失败时记录错误原因)
        }
    """
    import requests
    import re
    import traceback

    last_error = None

    # 方法0：mootdx 实时报价（首选，本地协议最快）
    try:
        from dca_data_sources import get_realtime_price_single
        info = get_realtime_price_single(code)
        if info and info.get('success') and info.get('price', 0) > 0:
            return {
                'code': code,
                'price': float(info['price']),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'mootdx',
                'success': True
            }
        else:
            last_error = "mootdx 未返回价格"
    except Exception as e:
        last_error = f"mootdx 异常: {str(e)[:50]}"

    # 方法1：新浪财经实时行情（HTTP 兜底）
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    retry_configs = [(2, 1), (1.5, 1)]  # (timeout, retries)

    for timeout, retries in retry_configs:
        for attempt in range(retries):
            try:
                prefix = 'sh' if code.startswith('5') or code.startswith('6') else 'sz'
                url = f"http://hq.sinajs.cn/list={prefix}{code}"
                response = session.get(url, timeout=timeout)
                response.encoding = 'gbk'
                if response.status_code == 200:
                    data = re.search(r'"([^"]*)"', response.text)
                    if data:
                        quote = data.group(1).split(',')
                        if len(quote) > 3 and quote[3]:
                            return {
                                'code': code,
                                'price': float(quote[3]),
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'source': 'sina',
                                'success': True
                            }
            except requests.exceptions.Timeout:
                last_error = f"新浪财经超时 (timeout={timeout}s)"
                if attempt < retries - 1:
                    continue
                break
            except requests.exceptions.ConnectionError as e:
                last_error = f"新浪财经连接失败: {str(e)[:50]}"
                break
            except Exception as e:
                last_error = f"新浪财经未知错误: {str(e)[:50]}"
                break

    # 方法2：腾讯财经实时行情（备用）
    try:
        prefix = 'sh' if code.startswith('5') or code.startswith('6') else 'sz'
        url = f"https://qt.gtimg.cn/q={prefix}{code}"
        session.headers.update({'Referer': 'https://finance.qq.com'})
        response = session.get(url, timeout=6)
        response.encoding = 'gbk'
        if response.status_code == 200:
            content = response.text
            if 'v_' in content:
                parts = content.split('="')[1].split('"')[0].split('~')
                if len(parts) > 4 and parts[3]:
                    return {
                        'code': code,
                        'price': float(parts[3]),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'tencent',
                        'success': True
                    }
                else:
                    last_error = "腾讯财经返回数据格式异常"
    except requests.exceptions.Timeout:
        last_error = "腾讯财经超时 (timeout=6s)"
    except requests.exceptions.ConnectionError as e:
        last_error = f"腾讯财经连接失败: {str(e)[:50]}"
    except Exception as e:
        last_error = f"腾讯财经未知错误: {str(e)[:50]}"

    # 方法3：akshare 实时行情（仅在新浪/腾讯失败时尝试，给5秒超时）
    try:
        import akshare as ak
        import threading

        result_holder = [None]
        error_holder = [None]

        def fetch_etf():
            try:
                df = ak.fund_etf_spot_em()
                row = df[df['代码'] == code]
                if not row.empty:
                    price = float(row.iloc[0]['最新价'])
                    result_holder[0] = price
            except Exception as e:
                error_holder[0] = f"akshare数据处理错误: {str(e)[:50]}"

        thread = threading.Thread(target=fetch_etf)
        thread.daemon = True
        thread.start()
        thread.join(timeout=5)

        if thread.is_alive():
            last_error = f"akshare获取{code}超时(5秒)"
        elif result_holder[0]:
            return {
                'code': code,
                'price': result_holder[0],
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'akshare',
                'success': True
            }
        elif error_holder[0]:
            last_error = error_holder[0]

    except ImportError:
        last_error = "akshare模块未安装"
    except Exception as e:
        last_error = f"akshare未知错误: {str(e)[:50]}"

    # 方法4：华泰证券行情（备用，配额有限）
    try:
        from ht_paper_trading_wrapper import HtPaperTrader
        trader = HtPaperTrader()
        exchange = 'SH' if code.startswith('5') or code.startswith('6') else 'SZ'
        result = trader.get_quote(code, exchange)
        if result:
            price = result.get('currentPrice') or result.get('prevClose')
            if price and price > 0:
                return {
                    'code': code,
                    'price': float(price),
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'ht',
                    'success': True
                }
    except Exception as e:
        last_error = f"华泰证券获取失败: {str(e)[:50]}"

    # 方法5：mootdx 日K线（首选日线源，比 akshare 快）
    try:
        from dca_data_sources import get_daily_history
        bars = get_daily_history(code, days=10)
        if bars:
            latest = bars[-1]
            if latest.get('close', 0) > 0:
                return {
                    'code': code,
                    'price': float(latest['close']),
                    'date': latest.get('date', ''),
                    'source': 'mootdx_daily',
                    'success': True,
                    'note': 'mootdx 日K线收盘价（可能为昨日）',
                    'warning': last_error
                }
        else:
            last_error = "mootdx 日K线为空"
    except Exception as e:
        last_error = f"mootdx 日K线获取失败: {str(e)[:50]}"

    # 方法6：akshare 日线数据（最后备用，非实时）- 带超时机制
    try:
        import akshare as ak
        import threading

        result_holder = [None]
        error_holder = [None]

        def fetch_daily():
            try:
                df = ak.sht_etf_hist_em(symbol=code, period="daily", start_date="20260101", end_date="20261231")
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    result_holder[0] = {
                        'code': code,
                        'price': float(latest['收盘']),
                        'date': str(latest['日期']),
                        'source': 'daily_close',
                        'success': True,
                        'note': '昨日收盘价（非实时）',
                        'warning': last_error
                    }
                else:
                    error_holder[0] = "日线数据为空"
            except Exception as e:
                error_holder[0] = f"日线数据获取失败: {str(e)[:50]}"

        thread = threading.Thread(target=fetch_daily)
        thread.daemon = True
        thread.start()
        thread.join(timeout=8)  # 8秒超时

        if thread.is_alive():
            last_error = f"日线数据获取{code}超时(8秒)"
        elif result_holder[0]:
            return result_holder[0]
        elif error_holder[0]:
            last_error = error_holder[0]

    except ImportError:
        pass
    except Exception as e:
        last_error = f"日线数据获取失败: {str(e)[:50]}"

    # 方法7：通达信行情缓存兜底（通过WorkBuddy自动刷新）
    try:
        from pathlib import Path
        import json as _json, time as _time
        _tdx_cache = Path(__file__).parent / "data" / "tdx_cache.json"
        if _tdx_cache.exists():
            with open(_tdx_cache, "r", encoding="utf-8") as f:
                tdx_data = _json.load(f)
            entry = tdx_data.get(code)
            if entry and isinstance(entry, dict):
                price = entry.get("price", 0)
                cache_time = entry.get("time", 0)
                if (price or 0) > 0 and (_time.time() - cache_time) < 120:
                    return {
                        'code': code,
                        'price': price,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'tdx',
                        'success': True,
                        'note': '通达信行情（缓存）',
                    }
    except Exception as _e:
        last_error = f"通达信缓存读取失败: {str(_e)[:50]}"

    # 所有方法都失败时的最终处理
    if fallback_to_cost and cost_price is not None and cost_price > 0:
        return {
            'code': code,
            'price': cost_price,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'cost',
            'success': True,
            'note': '使用持仓成本价（行情获取失败）',
            'error': last_error
        }

    return {
        'code': code,
        'price': 0,
        'date': '',
        'source': None,
        'success': False,
        'error': last_error or '所有行情获取方法均失败'
    }

def calculate_shares(etf_code, amount, price):
    """
    计算可购买的股数（100的整数倍）
    :param etf_code: ETF代码
    :param amount: 可用金额（元）
    :param price: 当前价格（元）
    :return: 可购买的股数
    """
    if price <= 0:
        return 0

    # 计算理论股数
    raw_shares = amount / price

    # 向下取整到100的整数倍
    shares = int(raw_shares / DCA_CONFIG['min_shares']) * DCA_CONFIG['min_shares']

    return shares

def calculate_trade_cost(shares, price):
    """
    计算交易成本
    :param shares: 股数
    :param price: 单价
    :return: (交易金额, 佣金, 总成本)
    """
    trade_amount = shares * price  # 交易金额
    commission = trade_amount * DCA_CONFIG['commission_rate']  # 佣金

    # 佣金最低限制（券商通常有最低佣金限制）
    min_commission = DCA_CONFIG.get('min_commission', 5.0)
    if commission < min_commission:
        commission = min_commission

    total_cost = trade_amount + commission  # 总成本

    return trade_amount, commission, total_cost

def execute_dca_trade(etf_code, monthly_amount, cost_price=None):
    """
    执行单只ETF的定投交易
    :param etf_code: ETF代码
    :param monthly_amount: 本月定投金额
    :param cost_price: 持仓成本价（可选，用于价格获取失败时的备选）
    :return: 交易结果字典
    """
    price_info = get_etf_price(etf_code, fallback_to_cost=True, cost_price=cost_price)

    if not price_info['success'] or price_info['price'] <= 0:
        return {
            'success': False,
            'code': etf_code,
            'message': f'无法获取{etf_code}行情',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    price = price_info['price']
    price_source = price_info.get('source', 'unknown')

    # 计算可购买的股数
    shares = calculate_shares(etf_code, monthly_amount, price)

    if shares == 0:
        return {
            'success': False,
            'code': etf_code,
            'message': f'金额不足，无法购买{etf_code}',
            'price': price,
            'price_source': price_source,
            'monthly_amount': monthly_amount,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # 计算交易成本
    trade_amount, commission, total_cost = calculate_trade_cost(shares, price)

    # 获取ETF信息（直接从配置中查找）
    etf_info = next((etf for etf in ETF_PORTFOLIO if etf['code'] == etf_code), {})

    result = {
        'success': True,
        'type': 'dca',
        'code': etf_code,
        'name': etf_info['name'] if etf_info else '',
        'category': etf_info['category'] if etf_info else '',
        'price': price,
        'price_source': price_source,
        'is_fallback': price_source in ('cost', 'daily_close'),
        'date': price_info['date'],
        'shares': shares,
        'trade_amount': round(trade_amount, 2),
        'commission': round(commission, 2),
        'total_cost': round(total_cost, 2),
        'planned_amount': monthly_amount,
        'actual_amount': round(trade_amount, 2),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if price_source in ('cost', 'daily_close'):
        result['warning'] = f'价格来源于{price_source}（非实时）'

    return result

def execute_monthly_dca():
    """
    执行每月定投
    :return: 所有ETF交易结果列表
    """
    print("\n" + "=" * 70)
    print(f"开始执行月度定投 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = []

    # 遍历所有ETF执行定投
    for etf in ETF_PORTFOLIO:
        code = etf['code']
        monthly_amount = etf['monthly_amount']

        print(f"\n正在处理: {etf['name']}（{code}）...")
        result = execute_dca_trade(code, monthly_amount)

        if result['success']:
            print(f"  价格: {result['price']:.4f}元")
            print(f"  股数: {result['shares']}股")
            print(f"  交易金额: {result['trade_amount']:.2f}元")
            print(f"  佣金: {result['commission']:.2f}元")
            print(f"  总成本: {result['total_cost']:.2f}元")
        else:
            print(f"  失败: {result['message']}")

        results.append(result)

    # 汇总统计
    success_count = sum(1 for r in results if r['success'])
    total_invested = sum(r.get('total_cost', 0) for r in results if r['success'])
    total_shares = sum(r.get('shares', 0) for r in results if r['success'])
    total_commission = sum(r.get('commission', 0) for r in results if r['success'])

    print("\n" + "-" * 70)
    print("定投执行汇总：")
    print(f"  成功交易: {success_count}/{len(results)}只ETF")
    print(f"  总投入金额: {total_invested:.2f}元")
    print(f"  总购买股数: {total_shares}股")
    print(f"  总佣金支出: {total_commission:.2f}元")
    print("=" * 70)

    return results

def print_trade_result(result):
    """打印单笔交易结果"""
    if result['success']:
        print(f"\n{'='*50}")
        print(f"交易成功！")
        print(f"{'='*50}")
        print(f"ETF代码: {result['code']}")
        print(f"ETF名称: {result['name']}")
        print(f"类别: {result['category']}")
        print(f"交易价格: {result['price']:.4f}元")
        print(f"购买股数: {result['shares']}股")
        print(f"交易金额: {result['trade_amount']:.2f}元")
        print(f"佣金: {result['commission']:.2f}元")
        print(f"总成本: {result['total_cost']:.2f}元")
        print(f"计划金额: {result['planned_amount']:.2f}元")
        print(f"执行时间: {result['timestamp']}")
        print(f"{'='*50}\n")
    else:
        print(f"\n交易失败 - {result['code']}: {result['message']}")

def execute_dca_with_analysis(prices, portfolio_manager):
    """
    根据分析结果自动调整资金分配的定投执行
    先执行类别配置分析，然后根据低配/超配情况调整分配比例
    :param prices: dict {code: price} 已获取的实时价格
    :param portfolio_manager: PortfolioManager实例
    :return: 交易结果列表
    """
    from dca_config import DCA_CONFIG, ETF_PORTFOLIO
    from dca_review import analyze_category_balance
    
    total_amount = DCA_CONFIG['monthly_amount']

    print("\n" + "=" * 70)
    print(f"【智能定投】总金额 {total_amount:.0f}元，根据分析结果动态调整分配")
    print("=" * 70)

    # 执行类别配置分析
    print("\n[步骤1] 执行类别配置分析...")
    balance_analysis = analyze_category_balance(portfolio_manager)
    
    print("\n类别配置分析结果:")
    for cat in balance_analysis:
        print(f"  {cat['category']}: 目标{cat['target_pct']}% | 实际{cat['actual_pct']}% | 偏差{cat['deviation']:+.1f}% | {cat['suggestion']}")

    # 根据分析结果调整分配比例
    print("\n[步骤2] 根据分析结果调整分配比例...")
    adjusted_allocations = adjust_allocation_by_analysis(balance_analysis, ETF_PORTFOLIO)

    # 按调整后的比例执行定投
    print("\n[步骤3] 按调整后的比例分配资金...")
    return execute_dca_with_adjusted_ratios(prices, adjusted_allocations, total_amount)


def adjust_allocation_by_analysis(balance_analysis, etfs):
    """
    根据分析结果调整各ETF的分配比例
    - 低配类别：增加分配比例
    - 超配类别：减少分配比例
    - 均衡类别：保持原比例
    """
    from dca_config import get_category_configs
    
    categories = get_category_configs()
    
    # 计算调整系数
    adjustment_factors = {}
    total_factor = 0
    underweight_count = 0
    overweight_count = 0
    
    for cat in balance_analysis:
        cat_name = cat['category']
        deviation = cat['deviation']
        
        if cat['verdict'] == 'under':  # 低配，增加分配
            # 低配越多，增加越多（最多增加50%）
            factor = 1 + min(abs(deviation) / 10, 0.5)
            underweight_count += 1
        elif cat['verdict'] == 'over':  # 超配，减少分配
            # 超配越多，减少越多（最多减少50%）
            factor = 1 - min(deviation / 10, 0.5)
            overweight_count += 1
        else:  # 均衡，保持不变
            factor = 1
        
        adjustment_factors[cat_name] = factor
        total_factor += categories[cat_name]['target_pct'] * factor
        print(f"  {cat_name}: 调整系数 {factor:.2f}")

    # 归一化调整后的比例
    adjusted_etf_ratios = {}
    for etf in etfs:
        cat_name = etf['category']
        original_ratio = etf['allocation']
        adjusted_ratio = original_ratio * adjustment_factors.get(cat_name, 1) / total_factor
        adjusted_etf_ratios[etf['code']] = adjusted_ratio
        print(f"    {etf['code']} {etf['name']}: {original_ratio*100:.0f}% -> {adjusted_ratio*100:.1f}%")

    return adjusted_etf_ratios


def execute_dca_with_adjusted_ratios(prices, adjusted_ratios, total_amount):
    """
    使用调整后的比例执行定投
    :param prices: dict {code: price}
    :param adjusted_ratios: dict {code: ratio} 调整后的分配比例
    :param total_amount: 总金额
    :return: 交易结果列表
    """
    from dca_config import DCA_CONFIG, ETF_PORTFOLIO
    
    # 按价格降序分配
    sorted_etfs = sorted(ETF_PORTFOLIO, key=lambda x: prices.get(x['code'], 999), reverse=True)
    allocations = []
    total_used = 0

    for etf in sorted_etfs:
        code = etf['code']
        if code not in prices:
            print(f"  {etf['name']}({code}) 无行情，跳过")
            continue
        if code not in adjusted_ratios:
            print(f"  {etf['name']}({code}) 无调整比例，跳过")
            continue
            
        price = prices[code]
        ratio = adjusted_ratios[code]
        theoretical = total_amount * ratio
        shares = int(theoretical / price / DCA_CONFIG['min_shares']) * DCA_CONFIG['min_shares']

        if shares <= 0:
            print(f"  {etf['name']}({code}): {theoretical:.0f}元不够买1手(100股×{price:.4f})，跳过")
            continue

        trade_amount = shares * price
        commission = max(trade_amount * DCA_CONFIG['commission_rate'], DCA_CONFIG.get('min_commission', 0))
        total_cost = trade_amount + commission

        allocations.append({
            'code': code,
            'name': etf['name'],
            'category': etf['category'],
            'price': price,
            'shares': shares,
            'trade_amount': trade_amount,
            'commission': commission,
            'total_cost': total_cost,
            'actual_amount': trade_amount,
            'monthly_amount': theoretical,
            'original_ratio': etf['allocation'],
            'adjusted_ratio': ratio
        })
        total_used += total_cost
        print(f"  {etf['name']}({code}): {shares}股 × {price:.4f} = {trade_amount:.2f}元 (计划{theoretical:.0f})")

    # 第二轮：剩余资金分配给"差额最小"的ETF
    remaining = round(total_amount - total_used, 2)
    print(f"\n首轮已分配: {total_used:.2f}元，剩余: {remaining:.2f}元")

    while remaining > 10:
        best = None
        best_gap = -1

        for etf in ETF_PORTFOLIO:
            code = etf['code']
            if code not in prices or code not in adjusted_ratios:
                continue
            price = prices[code]
            lot_cost = price * 100
            need = lot_cost + max(lot_cost * DCA_CONFIG['commission_rate'], 0)

            if need <= remaining:
                existing = next((a for a in allocations if a['code'] == code), None)
                gap = total_amount * adjusted_ratios[code] - (existing['total_cost'] if existing else 0)
                if gap > best_gap:
                    best_gap = gap
                    best = (code, price, etf['name'], etf['category'], need)

        if best is None:
            break

        code, price, name, category, need = best
        shares = 100
        trade_amount = shares * price
        commission = max(trade_amount * DCA_CONFIG['commission_rate'], DCA_CONFIG.get('min_commission', 0))
        total_cost = trade_amount + commission

        existing = next((a for a in allocations if a['code'] == code), None)
        if existing:
            existing['shares'] += shares
            existing['trade_amount'] += trade_amount
            existing['commission'] += commission
            existing['total_cost'] += total_cost
            existing['actual_amount'] += trade_amount
        else:
            allocations.append({
                'code': code, 'name': name, 'category': category,
                'price': price, 'shares': shares,
                'trade_amount': trade_amount, 'commission': commission,
                'total_cost': total_cost, 'actual_amount': trade_amount,
                'monthly_amount': total_amount * adjusted_ratios.get(code, 0),
                'original_ratio': etf['allocation'],
                'adjusted_ratio': adjusted_ratios.get(code, 0)
            })

        remaining -= need
        total_used += total_cost
        print(f"  剩余补投: {name}({code}) +{shares}股, 花{total_cost:.2f}元, 仍剩{remaining:.2f}元")

    # 生成交易结果
    results = []
    for a in allocations:
        result = {
            'success': True,
            'type': 'dca',
            'code': a['code'],
            'name': a['name'],
            'category': a['category'],
            'price': a['price'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'shares': a['shares'],
            'trade_amount': round(a['trade_amount'], 2),
            'commission': round(a['commission'], 2),
            'total_cost': round(a['total_cost'], 2),
            'planned_amount': round(a['monthly_amount'], 2),
            'actual_amount': round(a['actual_amount'], 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '智能分配(基于分析)'
        }
        results.append(result)

    print("\n" + "-" * 70)
    total_trade = sum(r['trade_amount'] for r in results)
    total_commission = sum(r['commission'] for r in results)
    print(f"交易完成: {len(results)}只ETF, 成交金额{total_trade:.2f}元, 佣金{total_commission:.2f}元")
    print("-" * 70)

    return results


def execute_dca_optimized(prices):
    """
    优化版定投分配：先获取实时价格，再按比例分配整手股数
    解决固定金额分配导致大量剩余现金的问题
    :param prices: dict {code: price} 已获取的实时价格
    :return: 交易结果列表（格式与 execute_monthly_dca 一致）
    """
    from dca_config import DCA_CONFIG, ETF_PORTFOLIO
    total_amount = DCA_CONFIG['monthly_amount']

    print("\n" + "=" * 70)
    print(f"【优化分配】总金额 {total_amount:.0f}元，按实时价格动态分配")
    print("=" * 70)

    # 第一轮：按配置比例计算各ETF理论金额，取整到100股
    # 按价格降序分配（高价ETF先分配，减少零头）
    sorted_etfs = sorted(ETF_PORTFOLIO, key=lambda x: prices.get(x['code'], 999), reverse=True)
    allocations = []
    total_used = 0

    for etf in sorted_etfs:
        code = etf['code']
        if code not in prices:
            print(f"  {etf['name']}({code}) 无行情，跳过")
            continue
        price = prices[code]
        theoretical = total_amount * etf['allocation']
        shares = int(theoretical / price / DCA_CONFIG['min_shares']) * DCA_CONFIG['min_shares']

        if shares <= 0:
            print(f"  {etf['name']}({code}): {theoretical:.0f}元不够买1手(100股×{price:.4f})，跳过")
            continue

        trade_amount = shares * price
        commission = max(trade_amount * DCA_CONFIG['commission_rate'], DCA_CONFIG.get('min_commission', 0))
        total_cost = trade_amount + commission

        allocations.append({
            'code': code,
            'name': etf['name'],
            'category': etf['category'],
            'price': price,
            'shares': shares,
            'trade_amount': trade_amount,
            'commission': commission,
            'total_cost': total_cost,
            'actual_amount': trade_amount,
            'monthly_amount': theoretical
        })
        total_used += total_cost
        print(f"  {etf['name']}({code}): {shares}股 × {price:.4f} = {trade_amount:.2f}元 (理论{theoretical:.0f})")

    # 第二轮：剩余资金分配给"差额最小"的ETF（差一手最近的）
    remaining = round(total_amount - total_used, 2)
    print(f"\n首轮已分配: {total_used:.2f}元，剩余: {remaining:.2f}元")

    while remaining > 10:
        # 找"差额最小"的ETF：理论金额 - 实花金额 最大的，且能多买一手
        best = None
        best_gap = -1

        for etf in ETF_PORTFOLIO:
            code = etf['code']
            if code not in prices:
                continue
            price = prices[code]
            lot_cost = price * 100  # 一手的价格
            need = lot_cost + max(lot_cost * DCA_CONFIG['commission_rate'], 0)

            if need <= remaining:
                # 找理论剩余最多的ETF
                existing = next((a for a in allocations if a['code'] == code), None)
                gap = total_amount * etf['allocation'] - (existing['total_cost'] if existing else 0)
                if gap > best_gap:
                    best_gap = gap
                    best = (code, price, etf['name'], etf['category'], need)

        if best is None:
            break

        code, price, name, category, need = best
        shares = 100
        trade_amount = shares * price
        commission = max(trade_amount * DCA_CONFIG['commission_rate'], DCA_CONFIG.get('min_commission', 0))
        total_cost = trade_amount + commission

        existing = next((a for a in allocations if a['code'] == code), None)
        if existing:
            existing['shares'] += shares
            existing['trade_amount'] += trade_amount
            existing['commission'] += commission
            existing['total_cost'] += total_cost
            existing['actual_amount'] += trade_amount
        else:
            allocations.append({
                'code': code, 'name': name, 'category': category,
                'price': price, 'shares': shares,
                'trade_amount': trade_amount, 'commission': commission,
                'total_cost': total_cost, 'actual_amount': trade_amount,
                'monthly_amount': total_amount * next(e['allocation'] for e in ETF_PORTFOLIO if e['code'] == code)
            })

        remaining -= need
        total_used += total_cost
        print(f"  剩余补投: {name}({code}) +{shares}股, 花{total_cost:.2f}元, 仍剩{remaining:.2f}元")

    # 生成交易结果（兼容格式）
    results = []
    for a in allocations:
        result = {
            'success': True,
            'type': 'dca',
            'code': a['code'],
            'name': a['name'],
            'category': a['category'],
            'price': a['price'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'shares': a['shares'],
            'trade_amount': round(a['trade_amount'], 2),
            'commission': round(a['commission'], 2),
            'total_cost': round(a['total_cost'], 2),
            'planned_amount': round(a['monthly_amount'], 2),
            'actual_amount': round(a['actual_amount'], 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': '优化分配'
        }
        results.append(result)

    # 汇总
    print("\n" + "-" * 70)
    total_invested = sum(r['total_cost'] for r in results)
    print(f"优化分配汇总：")
    print(f"  总投入: {total_amount:.0f}元")
    print(f"  实花: {total_invested:.2f}元")
    print(f"  剩余现金: {remaining:.2f}元")
    print(f"  资金利用率: {(total_invested/total_amount*100):.1f}%")
    print("=" * 70)

    return results

if __name__ == "__main__":
    # 测试单只ETF
    print("测试获取ETF价格...")
    test_code = "515080"
    price_info = get_etf_price(test_code)
    print(f"{test_code} 当前价格: {price_info}")

    # 测试计算购买股数
    print("\n测试计算购买股数...")
    shares = calculate_shares("515080", 600, price_info['price'] if price_info['success'] else 1.5)
    print(f"可用金额600元，价格{price_info['price'] if price_info['success'] else 1.5}元，可购买 {shares} 股")
