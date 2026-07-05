#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick check whether to run DCA today (avoid loading akshare and network requests).
Exit code:
  0 - need to run DCA
  1 - no need to run DCA (weekend / non-trading hours / already done this month)
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dca_portfolio_manager import PortfolioManager


def main():
    pm = PortfolioManager()
    pm.load_data()

    today = datetime.now()
    this_month = today.strftime('%Y-%m')
    weekday = today.weekday()  # 0=Mon, 6=Sun
    week_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Weekend: no trading
    if weekday >= 5:
        print(f"Today: {today.strftime('%Y-%m-%d %H:%M')} ({week_names[weekday]}) - Weekend")
        print(f"Last DCA: {pm.last_run_month or 'None'}")
        print("Need DCA this month: No (weekend)")
        sys.exit(1)

    # Non-trading hours (outside 9:00-15:00)
    if not (9 <= today.hour <= 15):
        print(f"Today: {today.strftime('%Y-%m-%d %H:%M')} ({week_names[weekday]}) - Non-trading hours")
        print(f"Last DCA: {pm.last_run_month or 'None'}")
        print("Need DCA this month: No (non-trading hours)")
        sys.exit(1)

    # Already done this month
    if pm.last_run_month == this_month:
        print(f"Today: {today.strftime('%Y-%m-%d %H:%M')} ({week_names[weekday]})")
        print(f"Last DCA: {pm.last_run_month} - Already done this month")
        print("Need DCA this month: No (already done)")
        sys.exit(1)

    # Need to run
    print(f"Today: {today.strftime('%Y-%m-%d %H:%M')} ({week_names[weekday]})")
    print(f"Last DCA: {pm.last_run_month or 'None'}")
    print("Need DCA this month: Yes")
    sys.exit(0)


if __name__ == '__main__':
    main()
