#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据源适配层
按优先级降级：mootdx（主） → akshare → sina/tencent HTTP（兜底）

设计目标：
1. mootdx 走通达信本地协议，启动快、批量报价、稳定
2. akshare 作为分红数据源（mootdx 不提供）
3. sina/tencent HTTP 作为最后兜底
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time


# ---- mootdx 客户端单例（懒加载） ----
_client_lock = threading.Lock()
_client = None
_client_last_check = 0.0
_CLIENT_RECONNECT_INTERVAL = 600  # 10分钟检测一次连接是否还活着


def _get_mootdx_client():
    """获取 mootdx 客户端单例（线程安全）"""
    global _client, _client_last_check
    now = time.time()
    if _client is not None and (now - _client_last_check) < _CLIENT_RECONNECT_INTERVAL:
        return _client
    with _client_lock:
        if _client is not None and (now - _client_last_check) < _CLIENT_RECONNECT_INTERVAL:
            return _client
        try:
            from mootdx.quotes import Quotes
            _client = Quotes.factory(market='std')
            _client_last_check = now
            return _client
        except Exception as e:
            print(f"[data_sources] mootdx 客户端创建失败: {e}")
            _client = None
            return None


def get_realtime_prices_batch(codes: List[str]) -> Dict[str, dict]:
    """
    批量获取实时价格（mootdx 优先，单次调用拿全部）

    Args:
        codes: ETF 代码列表

    Returns:
        {code: {'price': float, 'last_close': float, 'open': float, 'high': float,
                'low': float, 'volume': int, 'amount': float, 'servertime': str,
                'source': 'mootdx', 'success': True}}
        失败的 code 不会出现在返回 dict 中
    """
    client = _get_mootdx_client()
    if client is None:
        return {}

    try:
        df = client.quotes(symbol=codes)
        if df is None or len(df) == 0:
            return {}

        result = {}
        for _, row in df.iterrows():
            code = row.get('code')
            price = row.get('price')
            if code and price and price > 0:
                result[code] = {
                    'price': float(price),
                    'last_close': float(row.get('last_close', 0)),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'volume': int(row.get('vol', 0)),
                    'amount': float(row.get('amount', 0)),
                    'servertime': str(row.get('servertime', '')),
                    'source': 'mootdx',
                    'success': True,
                }
        return result
    except Exception as e:
        print(f"[data_sources] mootdx 批量获取失败: {e}")
        return {}


def get_realtime_price_single(code: str) -> Optional[dict]:
    """单只 ETF 实时价格（mootdx → sina/tencent/akshare 兜底链）"""
    # 1. mootdx
    result = get_realtime_prices_batch([code])
    if code in result:
        return result[code]

    # 2. 走原 dca_trading.get_etf_price 的 HTTP 兜底链（sina → tencent → akshare → daily）
    try:
        from dca_trading import get_etf_price as _legacy_get
        info = _legacy_get_etf_price_safe(_legacy_get, code)
        if info and info.get('success'):
            return {
                'price': float(info['price']),
                'source': info.get('source', 'http'),
                'success': True,
            }
    except Exception as e:
        print(f"[data_sources] HTTP 兜底失败 {code}: {e}")

    return None


def _legacy_get_etf_price_safe(legacy_fn, code):
    """安全调用旧版 get_etf_price（隔离异常）"""
    try:
        return legacy_fn(code)
    except Exception:
        return None


def get_daily_history(code: str, days: int = 30) -> List[dict]:
    """
    获取日K线历史（mootdx 主，akshare 兜底）

    Returns:
        [{'date': 'YYYY-MM-DD', 'open': float, 'close': float, 'high': float,
          'low': float, 'volume': int, 'amount': float}, ...]
    """
    # 1. mootdx 日K线（frequency=9 表示日线）
    client = _get_mootdx_client()
    if client is not None:
        try:
            df = client.bars(symbol=code, frequency=9, offset=days)
            if df is not None and len(df) > 0:
                result = []
                for _, row in df.iterrows():
                    dt_str = str(row.get('datetime', ''))
                    # mootdx datetime 格式可能是 '2026-07-03 15:00' 或 '2026-07-03 15:00:00'
                    date_str = dt_str.split(' ')[0] if ' ' in dt_str else dt_str[:10]
                    result.append({
                        'date': date_str,
                        'open': float(row.get('open', 0)),
                        'close': float(row.get('close', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'volume': int(row.get('volume', 0) or row.get('vol', 0)),
                        'amount': float(row.get('amount', 0)),
                    })
                return result
        except Exception as e:
            print(f"[data_sources] mootdx K线获取失败 {code}: {e}")

    # 2. akshare 兜底
    try:
        import akshare as ak
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days + 60)).strftime('%Y%m%d')
        # 优先 fund_etf_hist_em
        try:
            df = ak.fund_etf_hist_em(symbol=code, period='daily',
                                     start_date=start_date, end_date=end_date)
        except Exception:
            df = ak.sht_etf_hist_em(symbol=code, period='daily',
                                    start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            result = []
            for _, row in df.iterrows():
                result.append({
                    'date': str(row.get('日期', ''))[:10],
                    'open': float(row.get('开盘', 0)),
                    'close': float(row.get('收盘', 0)),
                    'high': float(row.get('最高', 0)),
                    'low': float(row.get('最低', 0)),
                    'volume': int(row.get('成交量', 0)),
                    'amount': float(row.get('成交额', 0)),
                })
            return result
    except Exception as e:
        print(f"[data_sources] akshare K线兜底失败 {code}: {e}")

    return []


def get_trading_days_from_kline(year: int, month: int) -> List[str]:
    """
    通过 mootdx 获取某月所有交易日（用 510300 沪深300ETF 的K线推断交易日）
    mootdx 没有直接的交易日历接口，但日K线的日期即为交易日

    Args:
        year: 年份
        month: 月份

    Returns:
        ['YYYY-MM-DD', ...] 该月所有交易日（升序）
    """
    # 拉取约 60 个交易日的数据，足以覆盖一个月
    bars = get_daily_history('510300', days=60)
    if not bars:
        return []

    month_prefix = f"{year:04d}-{month:02d}"
    trading_days = []
    seen = set()
    for bar in bars:
        date_str = bar['date']
        if date_str.startswith(month_prefix) and date_str not in seen:
            seen.add(date_str)
            trading_days.append(date_str)
    trading_days.sort()
    return trading_days


if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("测试 mootdx 批量实时报价")
    print("=" * 60)
    codes = ['515080', '510880', '510310', '510300', '511260', '510500']
    t0 = time.time()
    result = get_realtime_prices_batch(codes)
    elapsed = time.time() - t0
    print(f"耗时: {elapsed:.3f}s, 获取 {len(result)}/{len(codes)} 只")
    for code, info in result.items():
        print(f"  {code}: {info['price']:.4f} (source={info['source']})")

    print("\n测试日K线推断交易日:")
    days = get_trading_days_from_kline(2026, 7)
    print(f"  2026-07 共 {len(days)} 个交易日")
    for d in days:
        print(f"    {d}")
