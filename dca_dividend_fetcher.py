#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF分红自动抓取模块
自动从东方财富获取ETF分红信息，计算分红款加入资金池
"""

from __future__ import annotations  # 让类型注解惰性求值，避免顶层加载 pandas
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class ETFDividendFetcher:
    """ETF分红数据抓取器"""

    def __init__(self, portfolio_codes: List[str], data_file: str = None):
        self.portfolio_codes = portfolio_codes
        self.data_file = data_file or 'dividend_check_records.json'
        self.checked_records = self._load_checked_records()

    def _load_checked_records(self) -> Dict:
        """加载已检查记录"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_checked_records(self):
        """保存检查记录"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.checked_records, f, ensure_ascii=False, indent=2)

    def fetch_dividend_info(self, code: str) -> Optional[pd.DataFrame]:
        """获取单只ETF的分红信息"""
        try:
            import akshare as ak  # 延迟导入，避免启动时加载 akshare
            # 东方财富基金分红数据
            df = ak.fund_fh_em(symbol=code)
            return df
        except Exception as e:
            print(f"  获取 {code} 分红信息失败: {e}")
            return None

    def check_new_dividends(self, holdings: Dict) -> List[Dict]:
        """
        检查新的分红信息，返回待入账的分红列表
        holdings: {code: {'shares': int, 'name': str}}
        """
        new_dividends = []
        today = datetime.now()
        month_ago = today - timedelta(days=35)  # 检查最近35天

        import pandas as pd  # 延迟导入，避免启动时加载 pandas

        print("\n" + "=" * 60)
        print("检查ETF分红信息...")
        print("=" * 60)

        for code in self.portfolio_codes:
            if code not in holdings or holdings[code]['shares'] <= 0:
                continue

            df = self.fetch_dividend_info(code)
            if df is None or df.empty:
                continue

            # 打印原始数据列名（调试用）
            # print(f"  {code} 分红数据列: {df.columns.tolist()}")

            # 查找最近的分红记录
            for _, row in df.iterrows():
                try:
                    # 尝试解析除息日
                    ex_date = None
                    dividend_per_share = None

                    # 东方财富分红数据列：基金代码、简称、权益登记日、除息日、派息日、每股分红金额
                    for col in df.columns:
                        col_val = str(col).strip()
                        val = str(row[col]) if pd.notna(row[col]) else ''

                        if '登记' in col_val:
                            continue
                        if '除息' in col_val and val and val != 'nan':
                            ex_date = val[:10] if len(val) > 10 else val
                        if '派息' in col_val and val and val != 'nan':
                            # 派息日
                            pay_date = val[:10] if len(val) > 10 else val
                            if ex_date is None:
                                ex_date = pay_date
                        if '每股' in col_val or '分红' in col_val:
                            try:
                                dividend_per_share = float(val)
                            except:
                                pass

                    if ex_date is None or dividend_per_share is None or dividend_per_share <= 0:
                        continue

                    # 解析日期
                    try:
                        ex_date_obj = datetime.strptime(ex_date, '%Y-%m-%d')
                    except:
                        try:
                            ex_date_obj = datetime.strptime(ex_date.split()[0], '%Y-%m-%d')
                        except:
                            continue

                    # 只处理最近35天内的分红
                    if ex_date_obj < month_ago:
                        continue
                    if ex_date_obj > today + timedelta(days=5):
                        continue

                    # 检查是否已记录
                    record_key = f"{code}_{ex_date}"
                    if record_key in self.checked_records:
                        continue

                    # 计算分红金额
                    shares = holdings[code]['shares']
                    dividend_amount = round(shares * dividend_per_share, 2)

                    dividend_info = {
                        'code': code,
                        'name': holdings[code]['name'],
                        'ex_date': ex_date,
                        'shares': shares,
                        'dividend_per_share': dividend_per_share,
                        'dividend_amount': dividend_amount,
                        'record_key': record_key
                    }
                    new_dividends.append(dividend_info)
                    print(f"  发现新分红: {code}({holdings[code]['name']}) "
                          f"除息日{ex_date} 每份{dividend_per_share}元 "
                          f"{shares}股×{dividend_per_share}={dividend_amount}元")

                except Exception as e:
                    continue

        return new_dividends

    def mark_dividend_recorded(self, record_key: str):
        """标记分红已记录"""
        self.checked_records[record_key] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save_checked_records()


def fetch_all_portfolio_dividends(portfolio_manager, etf_portfolio: List[Dict]) -> float:
    """
    检查并获取所有持仓ETF的最新分红，加入资金池
    返回: 新增的分红总金额
    """
    # 构建持仓字典
    holdings = {}
    for code, holding in portfolio_manager.holdings.items():
        if holding['shares'] > 0:
            holdings[code] = {
                'shares': holding['shares'],
                'name': holding['name']
            }

    if not holdings:
        print("  暂无持仓，跳过分红检查")
        return 0

    # 创建抓取器
    fetcher = ETFDividendFetcher(
        portfolio_codes=list(holdings.keys()),
        data_file='dividend_check_records.json'
    )

    # 检查新分红
    new_dividends = fetcher.check_new_dividends(holdings)

    total_dividend = 0
    for div in new_dividends:
        # 添加到资金池
        portfolio_manager.cash_balance += div['dividend_amount']
        total_dividend += div['dividend_amount']

        # 记录到分红历史
        record = {
            'date': div['ex_date'],
            'code': div['code'],
            'name': div['name'],
            'shares': div['shares'],
            'dividend_per_share': div['dividend_per_share'],
            'dividend_amount': div['dividend_amount'],
            'source': 'auto_fetch',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        portfolio_manager.dividend_history.append(record)

        # 标记已记录
        fetcher.mark_dividend_recorded(div['record_key'])

    if total_dividend > 0:
        print(f"\n  自动分红合计: {total_dividend:.2f}元 已加入现金余额")
        print(f"  当前现金余额: {portfolio_manager.cash_balance:.2f}元")

    return total_dividend


if __name__ == '__main__':
    # 独立测试
    print("测试ETF分红抓取功能...")

    # 测试获取单只ETF的分红
    fetcher = ETFDividendFetcher(['515080', '510300'])
    df = fetcher.fetch_dividend_info('515080')

    if df is not None:
        print(f"\n515080 分红数据:")
        print(df.head(10).to_string())
    else:
        print("获取分红数据失败")
