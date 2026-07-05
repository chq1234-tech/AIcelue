#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日止盈轮动检查脚本
可配置为定时任务，每日9:30后自动执行
用法: python daily_stop_profit_check.py [--force]
"""

import sys
import os
from datetime import datetime

# 确保在脚本所在目录运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dca_portfolio_manager import PortfolioManager
from dca_stop_profit import StopProfitManager, STOP_PROFIT_CONFIG
from dca_config import STOP_PROFIT_ROTATION_CONFIG, ETF_PORTFOLIO
from dca_calendar import is_safe_trading_time
from dca_price_cache import refresh_prices


def main():
    force = '--force' in sys.argv
    no_open = '--no-open' in sys.argv
    
    print("=" * 80)
    print("每日止盈轮动检查")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"止盈阈值: {STOP_PROFIT_CONFIG['threshold']*100}%")
    print(f"再投策略: 低配类别优先")
    print("=" * 80)

    # 1. 检查是否启用
    if not STOP_PROFIT_ROTATION_CONFIG.get('enabled', True):
        print("\n止盈轮动功能已关闭，跳过")
        return

    # 2. 检查交易时间（非强制模式下）
    if not force:
        is_safe, reason = is_safe_trading_time()
        if not is_safe:
            print(f"\n当前时间不适合交易: {reason}")
            print("提示: 使用 --force 强制执行（仅在测试时使用）")
            if not no_open:
                _open_report()
            return

    # 3. 加载持仓
    print("\n[1] 加载持仓数据...")
    pm = PortfolioManager()
    pm.print_portfolio_summary()

    # 3b. 刷新价格缓存（开市/收市只用一趟行情）
    print("\n[1b] 刷新价格缓存...")
    n = refresh_prices()
    print(f"  {n} 个ETF价格已更新")

    # 4. 创建止盈管理器
    spm = StopProfitManager(pm)

    # 5. 执行检查
    print("\n[2] 执行止盈轮动检查...")
    result = spm.run_daily_check()

    # 6. 生成报告
    print("\n[3] 生成HTML报告...")
    report_path = spm.generate_html_report(result)

    # 7. 总结
    print("\n" + "=" * 80)
    print("止盈轮动检查完成")
    print(f"  止盈信号: {result.get('signals_count', 0)}个")
    print(f"  止盈执行: {result.get('stop_profit_count', 0)}笔")
    print(f"  释放资金: ¥{result.get('total_freed', 0):.2f}")
    print(f"  再投资:   {result.get('reinvest_count', 0)}笔")
    print(f"  再投金额: ¥{result.get('total_reinvested', 0):.2f}")
    print(f"  报告路径: {report_path}")
    print("=" * 80)

    # 8. 自动打开报告（除非 --no-open）
    if not no_open:
        _open_report()

    return result


def _open_report():
    """自动打开止盈轮动报告页面"""
    try:
        import webbrowser
        import time
        script_dir = os.path.dirname(os.path.abspath(__file__))
        report_file = os.path.join(script_dir, 'stop_profit_report.html')
        if os.path.exists(report_file):
            url = f'file:///{report_file.replace(os.sep, "/")}'
            print(f"\n  自动打开报告: {report_file}")
            time.sleep(0.5)
            webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    main()
