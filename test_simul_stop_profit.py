#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟止盈轮动测试脚本
- 使用临时数据文件副本，不影响真实数据
- 注入假价格(盈利≥20%)触发止盈信号
- 验证止盈轮动流程是否报错
"""

import os
import sys
import json
import shutil
import tempfile
from datetime import datetime

# 确保使用项目根目录的模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from dca_portfolio_manager import PortfolioManager
from dca_stop_profit import StopProfitManager, STOP_PROFIT_CONFIG, ETF_TARGETS


def main():
    print("=" * 80)
    print("【模拟测试】止盈轮动功能")
    print("=" * 80)

    src_data = os.path.join(SCRIPT_DIR, 'dca_portfolio_data.json')

    # 1) 创建临时目录，复制真实数据作为测试数据
    test_dir = tempfile.mkdtemp(prefix='simul_stop_profit_')
    test_data_file = os.path.join(test_dir, 'dca_portfolio_data.json')
    shutil.copy2(src_data, test_data_file)
    print(f"\n[1] 临时测试目录: {test_dir}")
    print(f"    测试数据文件: {test_data_file}")

    # 2) 构造 PortfolioManager，指向临时数据
    pm = PortfolioManager(data_file=test_data_file)
    pm.load_data()

    print(f"\n[2] 初始持仓快照:")
    total_mv = 0
    for code, h in pm.holdings.items():
        if h['shares'] > 0:
            print(f"    {code} {h.get('name','')}: {h['shares']}股, 成本{h['avg_cost']:.4f}, 总成本{h['total_cost']:.2f}")
    print(f"    现金余额: {pm.cash_balance:.2f}")
    print(f"    累计投入: {pm.total_invested:.2f}")

    # 3) 构造假价格：让所有持仓盈利≥25%（超过20%阈值）
    #    515080 成本1.5966 → 涨到2.05 (盈利28.4%)
    #    510300 成本4.8912 → 涨到6.20 (盈利26.7%)
    #    510500 成本8.5594 → 涨到11.00 (盈利28.5%)
    #    512760 成本1.0895 → 涨到1.40 (盈利28.5%)
    #    512010 成本0.357  → 涨到0.46 (盈利28.8%)
    #    513100 成本2.1591 → 涨到2.80 (盈利29.7%)
    fake_prices = {
        '515080': {'code': '515080', 'price': 2.05, 'success': True, 'source': 'simul'},
        '510300': {'code': '510300', 'price': 6.20, 'success': True, 'source': 'simul'},
        '510500': {'code': '510500', 'price': 11.00, 'success': True, 'source': 'simul'},
        '512760': {'code': '512760', 'price': 1.40, 'success': True, 'source': 'simul'},
        '512010': {'code': '512010', 'price': 0.46, 'success': True, 'source': 'simul'},
        '513100': {'code': '513100', 'price': 2.80, 'success': True, 'source': 'simul'},
    }

    print(f"\n[3] 注入模拟价格(均超过20%止盈阈值):")
    for code, p in fake_prices.items():
        h = pm.holdings.get(code, {})
        cost = h.get('avg_cost', 0)
        profit_pct = (p['price'] - cost) / cost * 100 if cost > 0 else 0
        print(f"    {code}: 模拟价{p['price']:.4f} vs 成本{cost:.4f} → 盈利{profit_pct:+.2f}%")

    # 4) 创建 StopProfitManager，使用临时目录作为 data_dir
    spm = StopProfitManager(pm, data_dir=test_dir)

    # 5) 执行止盈轮动检查（注入假价格）
    print(f"\n[4] 开始执行止盈轮动（使用模拟价格）...")
    try:
        result = spm.run_daily_check(prices=fake_prices)
        print(f"\n[5] 止盈轮动执行完成，无异常")
    except Exception as e:
        print(f"\n[5][错误] 止盈轮动执行过程中抛出异常:")
        import traceback
        traceback.print_exc()
        # 即使异常也继续，输出测试后状态
        result = {'success': False, 'error': str(e)}

    # 6) 验证：检查执行后的状态
    print(f"\n[6] 执行后持仓与现金状态:")
    print(f"    现金余额: {pm.cash_balance:.2f}")
    for code, h in pm.holdings.items():
        if h['shares'] > 0:
            print(f"    {code} {h.get('name','')}: {h['shares']}股, 成本{h['avg_cost']:.4f}, 总成本{h['total_cost']:.2f}")
        else:
            print(f"    {code} {h.get('name','')}: 已全部卖出")

    # 7) 检查现金非负
    print(f"\n[7] 数据完整性检查:")
    issues = []
    if pm.cash_balance < 0:
        issues.append(f"现金余额为负: {pm.cash_balance}")
    for code, h in pm.holdings.items():
        if h['shares'] < 0:
            issues.append(f"{code} 持仓为负: {h['shares']}")
        if h['shares'] > 0 and h['avg_cost'] <= 0:
            issues.append(f"{code} 持仓>0但成本≤0: avg_cost={h['avg_cost']}")
        if h['shares'] > 0 and h['total_cost'] <= 0:
            issues.append(f"{code} 持仓>0但总成本≤0: total_cost={h['total_cost']}")
    if issues:
        print(f"    [发现{len(issues)}个问题]:")
        for iss in issues:
            print(f"      - {iss}")
    else:
        print(f"    [OK] 现金非负、持仓非负、成本合理")

    # 8) 检查交易历史
    sp_trades = [t for t in pm.trade_history if t.get('type') == 'stop_profit']
    rein_trades = [t for t in pm.trade_history if t.get('type') == 'reinvest']
    print(f"\n[8] 交易历史:")
    print(f"    止盈卖出笔数: {len(sp_trades)}")
    print(f"    再投资买入笔数: {len(rein_trades)}")
    total_freed = sum(t.get('net_amount', 0) for t in sp_trades)
    total_reinv = sum(t.get('trade_amount', 0) for t in rein_trades)
    print(f"    释放资金合计: {total_freed:.2f}")
    print(f"    再投金额合计: {total_reinv:.2f}")

    # 9) 检查 stop_profit_history.json 是否正确生成
    hist_file = os.path.join(test_dir, 'stop_profit_history.json')
    if os.path.exists(hist_file):
        with open(hist_file, 'r', encoding='utf-8') as f:
            hist_data = json.load(f)
        print(f"\n[9] 止盈历史文件已生成:")
        print(f"    路径: {hist_file}")
        print(f"    历史记录数: {len(hist_data.get('history', []))}")
        print(f"    冻结ETF数: {len(hist_data.get('frozen_etfs', {}))}")
        for code, unfreeze in hist_data.get('frozen_etfs', {}).items():
            print(f"      冻结 {code} 直到 {unfreeze}")
    else:
        print(f"\n[9] [警告] 止盈历史文件未生成")

    # 10) 检查冻结是否阻止立即再投
    print(f"\n[10] 冻结期校验:")
    if spm.frozen_etfs:
        for code, unfreeze in spm.frozen_etfs.items():
            print(f"    {code}: 冻结至 {unfreeze}")
            if code in [t['code'] for t in rein_trades]:
                print(f"    [警告] {code} 在冻结期内却被再投资！")
    else:
        print(f"    无冻结ETF")

    # 11) 生成HTML报告
    print(f"\n[11] 生成止盈轮动HTML报告...")
    try:
        # 注意：HTML报告生成在 SCRIPT_DIR，可能会覆盖真实报告
        # 这里改为在测试目录生成
        report_path = os.path.join(test_dir, 'stop_profit_report.html')
        html = spm.generate_html_report(result)
        # 移动到测试目录
        if os.path.exists(html):
            shutil.move(html, report_path)
            print(f"    报告已生成: {report_path}")
    except Exception as e:
        print(f"    [错误] 生成HTML报告失败: {e}")
        import traceback
        traceback.print_exc()

    # 12) 汇总
    print(f"\n" + "=" * 80)
    print(f"【模拟测试汇总】")
    print(f"=" * 80)
    print(f"  执行成功: {result.get('success', False)}")
    print(f"  止盈信号数: {result.get('signals_count', 0)}")
    print(f"  止盈执行数: {result.get('stop_profit_count', 0)}")
    print(f"  再投笔数:   {result.get('reinvest_count', 0)}")
    print(f"  释放资金:   ¥{result.get('total_freed', 0):.2f}")
    print(f"  再投金额:   ¥{result.get('total_reinvested', 0):.2f}")
    print(f"  剩余现金:   ¥{result.get('cash_remaining', 0):.2f}")

    # 13) 清理提示
    print(f"\n[清理] 测试目录保留供检查: {test_dir}")
    print(f"       真实数据文件未受影响: {src_data}")

    return result


if __name__ == '__main__':
    main()
