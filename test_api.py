#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("1. 导入模块...")
    from dca_portfolio_manager import PortfolioManager
    from dca_stop_profit import StopProfitManager
    
    print("2. 初始化持仓管理器...")
    pm = PortfolioManager()
    print(f"   持仓数量: {len(pm.holdings)}")
    
    print("3. 初始化止盈管理器...")
    spm = StopProfitManager(pm)
    
    print("4. 获取价格...")
    prices = spm.get_prices()
    print(f"   价格数据: {prices}")
    
    print("5. 检查止盈信号...")
    signals = spm.check_stop_profit_signals(prices)
    print(f"   信号数量: {len(signals)}")
    
    print("6. 计算类别配比...")
    cat_alloc = spm.calc_category_allocation()
    print(f"   类别配比: {cat_alloc}")
    
except Exception as e:
    import traceback
    print("\n错误:", str(e))
    print("\n堆栈追踪:")
    traceback.print_exc()
