#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月度定投执行脚本
每月第一个交易日自动执行定投
"""

import sys
import os
from datetime import date
from chinese_calendar import is_workday, get_holiday_name

def is_first_trading_day(year_month=None):
    """
    判断是否为该月第一个交易日
    """
    if year_month is None:
        today = date.today()
        year_month = (today.year, today.month)

    year, month = year_month

    # 遍历该月所有日期，找到第一个工作日
    day = 1
    while True:
        try:
            check_date = date(year, month, day)
        except ValueError:
            return False

        if is_workday(check_date):
            # 检查是否是今天
            return check_date == date.today()

        day += 1
        if day > 31:
            return False

def run_monthly_dca():
    """执行月度定投"""
    today = date.today()

    if not is_first_trading_day():
        print(f"[{today}] 不是本月第一个交易日，跳过定投")
        return False

    print(f"[{today}] 正在执行月度定投...")

    # 导入并执行
    from dca_trading import execute_monthly_dca
    results = execute_monthly_dca()

    success = sum(1 for r in results if r.get('success', False))
    print(f"定投完成: {success}/{len(results)} 只ETF")

    return True

if __name__ == '__main__':
    run_monthly_dca()
