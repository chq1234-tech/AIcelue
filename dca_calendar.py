#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易日判断模块
判断当前是否为每月第一个交易日
"""

# ---- 测试用临时开关 ----
# 设为True后，today_date会被视为首交易日（仅用于测试，生产环境应设为False）
TEST_MODE = False

from datetime import datetime, timedelta

try:
    import chinese_calendar as cc
    HAS_CHINESE_CALENDAR = True
except ImportError:
    HAS_CHINESE_CALENDAR = False

try:
    from dca_config import ETF_PORTFOLIO
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

def get_trading_days(year, month):
    """
    获取指定月份的交易日列表
    优先级：mootdx K线推断 → akshare 交易日历 → 硬编码节假日备用
    :param year: 年份
    :param month: 月份
    :return: 交易日列表
    """
    # 方法1：mootdx K线推断（最快，无需 akshare/pandas）
    try:
        from dca_data_sources import get_trading_days_from_kline
        days = get_trading_days_from_kline(year, month)
        if days:
            return days
    except Exception as e:
        print(f"mootdx 获取交易日失败: {e}")

    # 方法2：akshare 交易日历（备用）
    try:
        import akshare as ak

        # 获取交易日历
        start_date = f"{year}0101"
        end_date = f"{year}1231"

        df = ak.tool_trade_date_hist_sina()

        if df is not None and not df.empty:
            # 筛选指定月份的交易日
            import pandas as pd  # 延迟导入，避免启动时加载 pandas
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            month_start = datetime(year, month, 1)

            # 计算月份最后一天
            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(days=1)

            month_trading_days = df[
                (df['trade_date'] >= month_start) &
                (df['trade_date'] <= month_end)
            ]['trade_date'].tolist()

            return [d.strftime('%Y-%m-%d') for d in month_trading_days]

    except Exception as e:
        print(f"获取交易日历失败: {e}")

    # 方法3：使用备用方案（中国正常工作日 + 硬编码节假日）
    fallback_days = get_chinese_trading_days_fallback(year, month)
    if not fallback_days:
        # 最基础的备用：所有工作日
        fallback_days = []
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1) - timedelta(days=1)
        current = month_start
        while current <= month_end:
            if current.weekday() < 5:  # 周一到周五
                fallback_days.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
    return fallback_days

def get_chinese_trading_days_fallback(year, month):
    """
    备用方案：获取中国交易日（排除周末和节假日）
    :param year: 年份
    :param month: 月份
    :return: 交易日列表
    """
    trading_days = []

    # 计算月份第一天和最后一天
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1) - timedelta(days=1)

    current = month_start
    while current <= month_end:
        # 排除周末
        if current.weekday() < 5:  # 0-4 表示周一到周五
            # 排除中国法定节假日（简单版）
            date_str = current.strftime('%Y-%m-%d')

            # 排除主要节假日（需要更新为中国实际节假日）
            if not is_holiday(current):
                trading_days.append(date_str)

        current += timedelta(days=1)

    return trading_days

def is_holiday(date):
    """
    判断是否为节假日
    优先级：chinese_calendar 库 → 硬编码备用

    注：A股节假日指非交易日（含周末和法定假），但 chinese_calendar.is_holiday()
    返回值包含周末。如需排除周末，需额外判断 weekday < 5。
    此函数设计为在 get_chinese_trading_days_fallback 中调用，
    该函数已先排除了周末，所以这里只需判断法定假。
    :param date: datetime对象
    :return: True如果是节假日
    """
    # 优先使用 chinese_calendar 库（准确，自动处理调休）
    if HAS_CHINESE_CALENDAR:
        try:
            # is_workday() 返回 True 如果是工作日（含调休上班日）
            # is_holiday() 返回 True 如果是节假日（含调休放假）
            return cc.is_holiday(date)
        except Exception:
            pass  # 降级到硬编码

    # 备用：硬编码节假日（仅覆盖主要节日）
    month = date.month
    day = date.day

    # 元旦（每年1月1日）
    if month == 1 and day == 1:
        return True

    # 春节（简化：春节期间大致日期 - 仅作降级备用，chinese_calendar 更准）
    if month == 1 and day >= 28:
        return True
    if month == 2 and day <= 4:
        return True

    # 清明节
    if month == 4 and 4 <= day <= 6:
        return True

    # 劳动节（5月1-5日，涵盖调休情况）
    if month == 5 and 1 <= day <= 5:
        return True

    # 国庆节（10月1-7日）
    if month == 10 and 1 <= day <= 7:
        return True

    return False

def is_first_trading_day(date=None):
    """
    判断当前是否为指定月份的第一个交易日
    :param date: datetime对象，默认当前时间
    :return: True如果是第一个交易日
    """
    if TEST_MODE:
        print("  [测试模式] 强制认定今日为首交易日")
        return True

    if date is None:
        date = datetime.now()

    year = date.year
    month = date.month

    # 获取当月所有交易日
    trading_days = get_trading_days(year, month)

    if not trading_days:
        return False

    # 获取第一个交易日
    first_trading_day = trading_days[0]

    # 判断今天是否为第一个交易日
    today_str = date.strftime('%Y-%m-%d')

    return today_str == first_trading_day

def is_trading_day(date):
    """
    判断指定日期是否为交易日
    :param date: datetime对象
    :return: True如果是交易日
    """
    year = date.year
    month = date.month
    trading_days = get_trading_days(year, month)
    date_str = date.strftime('%Y-%m-%d')
    return date_str in trading_days


def get_next_trading_day(date=None):
    """
    获取下一个交易日
    :param date: datetime对象，默认当前时间
    :return: 下一个交易日的日期字符串
    """
    if date is None:
        date = datetime.now()

    current = date
    for _ in range(10):  # 最多检查10天
        current += timedelta(days=1)

        if is_trading_day(current):
            return current.strftime('%Y-%m-%d')

    return None

def is_safe_trading_time():
    """
    判断当前时间是否适合下单（避开开盘/收盘极端波动）
    A股交易时间:
      9:15-9:25  集合竞价（不可撤单）
      9:30-11:30 连续竞价
      13:00-14:57 连续竞价（上交所）
      14:57-15:00 收盘集合竞价
    安全窗口:
      9:40-11:25  （避开开盘前10分钟）
      13:10-14:50  （避开收盘前10分钟）
    :return: (is_safe, reason_string)
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=周一, 6=周日

    # 周末不交易
    if weekday >= 5:
        return False, f"周末（周{['一','二','三','四','五','六','日'][weekday]}）不接受新订单"

    current_time = now.time()
    from datetime import time as dt_time

    # 盘前：9:15之前
    if current_time < dt_time(9, 15):
        return False, f"盘前（{current_time.strftime('%H:%M')}），未开盘"

    # 集合竞价阶段：9:15-9:30（不可撤单，波动大）
    if dt_time(9, 15) <= current_time <= dt_time(9, 30):
        return False, f"集合竞价阶段（{current_time.strftime('%H:%M')}），请等待9:40后下单"

    # 开盘极端波动期：9:30-9:40
    if dt_time(9, 30) <= current_time < dt_time(9, 40):
        return False, f"开盘波动期（{current_time.strftime('%H:%M')}），建议9:40后下单"

    # 上午收盘前：11:25-11:30
    if dt_time(11, 25) <= current_time <= dt_time(11, 30):
        return False, f"上午收盘前（{current_time.strftime('%H:%M')}），建议下午13:10后下单"

    # 午休
    if dt_time(11, 30) < current_time < dt_time(13, 0):
        return False, f"午休时间（{current_time.strftime('%H:%M')}），未开盘"

    # 下午开盘极端波动期：13:00-13:10
    if dt_time(13, 0) <= current_time < dt_time(13, 10):
        return False, f"下午开盘波动期（{current_time.strftime('%H:%M')}），建议13:10后下单"

    # 收盘极端波动期：14:50-15:00
    if dt_time(14, 50) <= current_time <= dt_time(15, 0):
        return False, f"收盘波动期（{current_time.strftime('%H:%M')}），建议14:50前下单"

    return True, f"安全交易时间（{current_time.strftime('%H:%M')}）"

def get_current_month_info():
    """
    获取当前月份的交易日信息
    :return: dict包含月份信息
    """
    now = datetime.now()
    year = now.year
    month = now.month

    trading_days = get_trading_days(year, month)

    if not trading_days:
        return {
            'year': year,
            'month': month,
            'trading_days': [],
            'first_trading_day': None,
            'last_trading_day': None,
            'total_trading_days': 0,
            'is_first_day': False
        }

    first_day = trading_days[0]
    last_day = trading_days[-1]
    today_str = now.strftime('%Y-%m-%d')

    return {
        'year': year,
        'month': month,
        'trading_days': trading_days,
        'first_trading_day': first_day,
        'last_trading_day': last_day,
        'total_trading_days': len(trading_days),
        'is_first_day': today_str == first_day,
        'today': today_str
    }

def print_month_trading_info():
    """打印当月交易日信息"""
    info = get_current_month_info()

    print("\n" + "=" * 70)
    print(f"{info['year']}年{info['month']}月交易日信息")
    print("=" * 70)
    print(f"首交易日: {info['first_trading_day']}")
    print(f"末交易日: {info['last_trading_day']}")
    print(f"交易日总数: {info['total_trading_days']}天")
    print(f"今日日期: {info['today']}")
    print(f"是否为当月首个交易日: {'是' if info['is_first_day'] else '否'}")
    print("=" * 70)

    if info['trading_days']:
        print("\n交易日列表：")
        for i, day in enumerate(info['trading_days'], 1):
            marker = " <-- 今日" if day == info['today'] else (" <-- 首个" if i == 1 else "")
            print(f"  {i:2d}. {day}{marker}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    print_month_trading_info()

    print("\n测试是否为第一个交易日...")
    print(f"当前日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"是否为当月首交易日: {is_first_trading_day()}")
