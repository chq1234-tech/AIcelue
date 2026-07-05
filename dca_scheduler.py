#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投定时任务模块
自动执行定投的定时调度
"""

import time
import schedule
from datetime import datetime
from dca_main import DCASystem
from dca_calendar import print_month_trading_info

def job_daily_check():
    """每日检查任务"""
    print("\n" + "=" * 80)
    print(f"【每日检查】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    dca = DCASystem()
    dca.run_daily_check()


def job_refresh_prices():
    """开市/收市：更新价格缓存"""
    print("\n" + "=" * 80)
    print(f"【价格缓存刷新】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    from dca_price_cache import refresh_prices
    n = refresh_prices()
    print(f"价格缓存更新完毕，{n} 个ETF")

def job_monthly_dca():
    """每月定投任务（智能模式）"""
    print("\n" + "=" * 80)
    print(f"【月度定投(智能模式)】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    dca = DCASystem()
    result = dca.run_dca_cycle(smart_mode=True)

    if result['success']:
        print("\n定投执行成功！")
    else:
        print(f"\n定投未执行: {result.get('message', '未知原因')}")

def job_weekly_report():
    """每周报告任务"""
    print("\n" + "=" * 80)
    print(f"【每周报告】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    dca = DCASystem()
    dca.check_portfolio_status()

def start_scheduler():
    """启动定时调度"""
    print("\n" + "=" * 80)
    print("启动定投定时任务调度器")
    print("=" * 80)
    print("\n定时任务配置:")
    print("  - 每日09:25 自动检查（交易日判断）")
    print("  - 每日09:30 更新价格缓存（开市价）")
    print("  - 每日15:05 更新价格缓存（收市价）")
    print("  - 每周五15:30 生成周报")
    print("  - 每月第一个交易日09:30 执行定投")
    print("\n按 Ctrl+C 停止调度...")
    print("=" * 80)

    # 设置定时任务
    # 每日09:25检查（考虑集合竞价）
    schedule.every().day.at("09:25").do(job_daily_check)

    # 每日09:30刷新价格缓存（开市后）
    schedule.every().day.at("09:30").do(job_refresh_prices)

    # 每日15:05刷新价格缓存（收市后）
    schedule.every().day.at("15:05").do(job_refresh_prices)

    # 每周五15:30生成周报（收盘后）
    schedule.every().friday.at("15:30").do(job_weekly_report)

    # 每月第一个交易日09:30执行定投（收盘前）
    # 注意：实际的交易日判断在job_daily_check中进行

    # 持续运行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        print("\n\n定时任务已停止")
        print("=" * 80)

def run_once(mode='check'):
    """运行一次任务"""
    dca = DCASystem()

    if mode == 'check':
        dca.run_daily_check()
    elif mode == 'dca':
        dca.run_dca_cycle()
    elif mode == 'report':
        dca.check_portfolio_status()
    else:
        print(f"未知模式: {mode}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'start':
            # 启动定时调度
            start_scheduler()
        elif command == 'daily':
            # 运行每日检查
            job_daily_check()
        elif command == 'monthly':
            # 运行月度定投
            job_monthly_dca()
        elif command == 'weekly':
            # 运行每周报告
            job_weekly_report()
        else:
            print(f"未知命令: {command}")
            print("\n可用命令:")
            print("  start   - 启动定时调度")
            print("  daily   - 运行每日检查")
            print("  monthly - 运行月度定投")
            print("  weekly  - 运行每周报告")
    else:
        # 默认：运行每日检查
        run_once('check')
