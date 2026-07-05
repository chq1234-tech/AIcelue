#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试交易日判断"""

from dca_calendar import is_first_trading_day, is_safe_trading_time, get_trading_days
from datetime import datetime

print(f'今天日期: {datetime.now().strftime("%Y-%m-%d %A")}')
print(f'is_first_trading_day: {is_first_trading_day()}')
safe, reason = is_safe_trading_time()
print(f'is_safe_trading_time: {safe} - {reason}')
trading_days = get_trading_days(2026, 6)
print(f'6月交易日总数: {len(trading_days)}')
print(f'6月前5个交易日: {trading_days[:5]}')
if trading_days:
    print(f'6月第一个交易日: {trading_days[0]}')
