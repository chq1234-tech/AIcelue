#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标的物检讨模块
分析各ETF表现，尤其关注行业ETF（芯片、医药）是否需要调整
"""

from datetime import datetime, timedelta
from dca_config import ETF_PORTFOLIO, DCA_CONFIG

def get_etf_category(etf):
    """获取ETF归类"""
    cat = etf.get('category', '')
    if cat == '红利': return '红利'
    if cat == '宽基': return '宽基'
    if cat in ['行业']: return '行业'
    if cat == '海外': return '海外'
    return '其他'

def get_category_configs():
    """按类别分组配置"""
    categories = {}
    for etf in ETF_PORTFOLIO:
        cat = get_etf_category(etf)
        if cat not in categories:
            categories[cat] = {'target_pct': 0, 'etfs': []}
        categories[cat]['target_pct'] += etf['allocation'] * 100
        categories[cat]['etfs'].append(etf)
    return categories

def analyze_industry_etfs(pm, prices):
    """
    行业ETF专题分析
    关注芯片ETF(512760)和医药ETF(512010)
    """
    industry_codes = {'512760': '芯片ETF', '512010': '医药ETF'}
    results = []

    for code, name in industry_codes.items():
        holding = pm.holdings.get(code, {})
        shares = holding.get('shares', 0)

        # 获取当前价格
        current_price = prices.get(code, 0)

        item = {
            'code': code,
            'name': name,
            'shares': shares,
            'avg_cost': holding.get('avg_cost', 0),
            'current_price': current_price,
            'total_cost': holding.get('total_cost', 0),
            'current_value': shares * current_price if current_price > 0 else 0,
            'status': 'normal'
        }

        if shares > 0 and current_price > 0:
            item['return_pct'] = round((item['current_value'] - item['total_cost']) / item['total_cost'] * 100, 2)
            # 状态判断
            if item['return_pct'] < -15:
                item['status'] = 'danger'
                item['suggestion'] = f"⚠️ 亏损超过15%，建议关注基本面是否变化，可考虑止损或补仓摊平"
            elif item['return_pct'] < -8:
                item['status'] = 'warn'
                item['suggestion'] = f"⚡ 亏损{abs(item['return_pct']):.1f}%，行业ETF波动较大，建议持续定投摊低成本"
            elif item['return_pct'] < -3:
                item['status'] = 'normal'
                item['suggestion'] = f"小幅亏损，行业轮动正常范围，维持定投"
            elif item['return_pct'] < 5:
                item['status'] = 'normal'
                item['suggestion'] = "微盈，保持定投节奏"
            elif item['return_pct'] < 15:
                item['status'] = 'good'
                item['suggestion'] = f"✅ 盈利{item['return_pct']:.1f}%，可考虑部分止盈"
            else:
                item['status'] = 'danger'
                item['suggestion'] = f"🔥 盈利超过15%，建议分批止盈锁定利润"
        elif shares == 0:
            item['status'] = 'empty'
            item['suggestion'] = "暂无持仓，按定投计划执行即可"
        else:
            item['status'] = 'unknown'
            item['suggestion'] = "价格数据不可用"

        results.append(item)

    return results

def analyze_category_balance(pm):
    """
    类别配置平衡分析
    检查实际持仓比例与目标比例的偏差
    """
    categories = get_category_configs()
    actual_pct = {}

    # 计算总市值
    total_value = sum(
        h['shares'] * h.get('avg_cost', 0) or 1
        for h in pm.holdings.values()
    )
    if total_value == 0:
        return [{'category': cat, 'target_pct': data['target_pct'],
                 'actual_pct': 0, 'deviation': -data['target_pct'],
                 'pct_deviation': -100, 'verdict': 'warning',
                 'suggestion': '暂无持仓'} for cat, data in categories.items()]

    # 计算各类别实际市值
    cat_values = {cat: 0 for cat in categories}
    for code, h in pm.holdings.items():
        est_value = h['shares'] * h.get('avg_cost', 0)
        for cat, data in categories.items():
            if any(e['code'] == code for e in data['etfs']):
                cat_values[cat] += est_value
                break

    results = []
    for cat, data in categories.items():
        target = data['target_pct']
        actual = round(cat_values[cat] / total_value * 100, 1) if total_value > 0 else 0
        deviation = round(actual - target, 1)

        if abs(deviation) < 3:
            verdict = 'ok'
            suggestion = f'比例适中（偏差{deviation:+.1f}%），无需调整'
        elif deviation > 0:
            verdict = 'over'
            suggestion = f'超配{deviation:.1f}%，建议暂停对新资金投入该类别'
        else:
            verdict = 'under'
            suggestion = f'低配{abs(deviation):.1f}%，后续定投可适当倾斜'

        results.append({
            'category': cat,
            'target_pct': target,
            'actual_pct': actual,
            'deviation': deviation,
            'verdict': verdict,
            'suggestion': suggestion
        })

    return results

def run_full_review(pm, prices):
    """执行完整的标的检讨"""
    review = {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'industry': analyze_industry_etfs(pm, prices),
        'balance': analyze_category_balance(pm),
        'summary': ''
    }

    # 生成综述
    issues = []
    for ind in review['industry']:
        if ind['status'] in ['danger', 'warn']:
            issues.append(f"{ind['name']}({ind['code']}): {ind['suggestion']}")

    for bal in review['balance']:
        if bal['verdict'] != 'ok':
            issues.append(f"{bal['category']}: {bal['suggestion']}")

    if issues:
        review['summary'] = '⚠️ 以下标的需关注：\n' + '\n'.join(f'• {s}' for s in issues)
    else:
        review['summary'] = '✅ 各标的运行正常，维持当前定投计划'

    return review

if __name__ == '__main__':
    # 测试
    from dca_portfolio_manager import PortfolioManager
    pm = PortfolioManager()
    review = run_full_review(pm, {})
    print(review['summary'])
    for ind in review['industry']:
        print(f"\n{ind['name']}: {ind['status']}")
        print(f"  成本: {ind['avg_cost']:.4f} | 现价: {ind['current_price']:.4f} | {ind['suggestion']}")
