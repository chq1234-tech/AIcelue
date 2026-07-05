"""
红利ETF资料收集脚本 v2
使用东方财富公开API收集沪深市场红利ETF的资料
包含：名称、代码、净值、分红、年度收益率等
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time

def get_etf_list_from_eastmoney():
    """从东方财富获取所有ETF列表，筛选红利ETF"""
    print("正在从东方财富获取ETF列表...")
    
    # 东方财富ETF列表API
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    
    params = {
        'pn': '1',
        'pz': '5000',
        'po': '1',
        'np': '1',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2',
        'invt': '2',
        'fid': 'f3',
        'fs': 'b:BK0465',  # ETF板块
        'fields': 'f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data and 'data' in data and 'diff' in data['data']:
            etf_list = data['data']['diff']
            
            # 转换为DataFrame
            df = pd.DataFrame(etf_list)
            
            # 重命名列
            df = df.rename(columns={
                'f12': '代码',
                'f14': '名称',
                'f2': '最新价',
                'f3': '涨跌幅(%)',
                'f4': '涨跌额',
                'f5': '成交量',
                'f6': '成交额'
            })
            
            # 筛选名称中包含"红利"的ETF
            dividend_etf = df[df['名称'].str.contains('红利', na=False)]
            
            print(f"找到 {len(dividend_etf)} 只红利ETF")
            return dividend_etf
        else:
            print("API返回数据格式异常")
            return None
    except Exception as e:
        print(f"获取ETF列表失败: {e}")
        return None

def get_etf_nav_history(code):
    """获取ETF历史净值数据"""
    print(f"  获取 {code} 历史净值...")
    
    # 天天基金网API (适用于场内ETF)
    # 注意：场内ETF用新浪财经API更合适
    
    # 使用新浪财经API获取ETF历史数据
    url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    params = {
        'symbol': f'sz{code}' if code.startswith('1') else f'sh{code}',
        'scale': '240',  # 日线
        'ma': 'no',
        'datalen': '300'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data and len(data) > 0:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['day'])
            df['close'] = df['close'].astype(float)
            df = df.sort_values('date')
            
            return df
        return None
    except Exception as e:
        print(f"    获取历史数据失败: {e}")
        return None

def calculate_returns(nav_df):
    """计算收益率"""
    if nav_df is None or len(nav_df) == 0:
        return None
    
    try:
        latest_price = nav_df.iloc[-1]['close']
        
        # 年度收益率（近一年）
        if len(nav_df) > 0:
            year_ago_idx = max(0, len(nav_df) - 252)  # 约252个交易日=1年
            year_ago_price = nav_df.iloc[year_ago_idx]['close']
            annual_return = ((latest_price - year_ago_price) / year_ago_price * 100)
        else:
            annual_return = 0
        
        # 今年以来收益率
        this_year_data = nav_df[nav_df['date'].dt.year == datetime.now().year]
        if len(this_year_data) > 0:
            ytd_price = this_year_data.iloc[0]['close']
            ytd_return = ((latest_price - ytd_price) / ytd_price * 100)
        else:
            ytd_return = 0
        
        return {
            '最新净值': round(latest_price, 3),
            '年度收益率(%)': round(annual_return, 2),
            '今年以来收益率(%)': round(ytd_return, 2)
        }
    except Exception as e:
        print(f"    计算收益率失败: {e}")
        return None

def get_preset_dividend_etfs():
    """预设的红利ETF列表（作为备选）"""
    return [
        {'代码': '510880', '名称': '华泰柏瑞上证红利ETF', '市场': '上海'},
        {'代码': '159905', '名称': '工银深证红利ETF', '市场': '深圳'},
        {'代码': '515450', '名称': '招商中证红利ETF', '市场': '上海'},
        {'代码': '512530', '名称': '建信沪深300红利ETF', '市场': '上海'},
        {'代码': '515080', '名称': '中证红利低波动ETF', '市场': '上海'},
        {'代码': '159758', '名称': '红利50ETF', '市场': '深圳'},
        {'代码': '515100', '名称': '红利低波100ETF', '市场': '上海'},
        {'代码': '512890', '名称': '红利低波ETF', '市场': '上海'},
        {'代码': '515300', '名称': '嘉实沪深300红利低波动ETF', '市场': '上海'},
        {'代码': '159546', '名称': '红利ETF', '市场': '深圳'}
    ]

def main():
    print("=" * 70)
    print("红利ETF资料收集工具 v2")
    print("数据来源：东方财富、新浪财经")
    print("=" * 70)
    
    # 1. 尝试从API获取红利ETF列表
    print("\n[1/4] 获取红利ETF列表...")
    dividend_etf = get_etf_list_from_eastmoney()
    
    if dividend_etf is None or len(dividend_etf) == 0:
        print("⚠ API获取失败，使用预设红利ETF列表...")
        etf_list = get_preset_dividend_etfs()
    else:
        etf_list = dividend_etf.to_dict('records')
    
    print(f"✓ 共 {len(etf_list)} 只红利ETF需要分析")
    
    # 2. 收集详细信息
    print("\n[2/4] 收集详细数据...")
    results = []
    
    for i, etf in enumerate(etf_list, 1):
        code = etf['代码']
        name = etf['名称']
        
        print(f"\n  ({i}/{len(etf_list)}) 处理 {code} - {name}")
        
        # 获取历史净值
        nav_df = get_etf_nav_history(code)
        
        # 计算收益率
        returns = calculate_returns(nav_df)
        
        # 构建结果
        result = {
            '代码': code,
            '名称': name,
            '最新净值(元)': returns['最新净值'] if returns else 'N/A',
            '年度收益率(%)': returns['年度收益率(%)'] if returns else 'N/A',
            '今年以来收益率(%)': returns['今年以来收益率(%)'] if returns else 'N/A',
            '备注': '数据获取成功' if returns else '数据获取失败'
        }
        
        results.append(result)
        time.sleep(0.3)  # 避免请求过快
    
    # 3. 保存结果
    print("\n" + "=" * 70)
    print("[3/4] 保存结果...")
    
    df = pd.DataFrame(results)
    
    # 保存到Excel
    output_file = r'd:\temp\红利ETF\红利ETF资料汇总.xlsx'
    df.to_excel(output_file, index=False, sheet_name='红利ETF')
    print(f"✓ Excel报告已保存: {output_file}")
    
    # 保存到CSV
    output_csv = r'd:\temp\红利ETF\红利ETF资料汇总.csv'
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"✓ CSV报告已保存: {output_csv}")
    
    # 4. 打印汇总
    print("\n" + "=" * 70)
    print("[4/4] 红利ETF汇总信息:")
    print("=" * 70)
    print(df.to_string(index=False))
    
    # 统计信息
    print("\n" + "=" * 70)
    print("统计信息:")
    print(f"  总ETF数量: {len(results)}")
    success_count = sum(1 for r in results if r['备注'] == '数据获取成功')
    print(f"  成功获取: {success_count}")
    print(f"  失败: {len(results) - success_count}")
    
    return df

if __name__ == '__main__':
    try:
        result_df = main()
        print("\n" + "=" * 70)
        print("✓ 所有资料收集完成！")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
