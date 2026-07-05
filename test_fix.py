#!/usr/bin/env python3
import sys
import os

# 清除缓存
cache_dir = os.path.join(os.path.dirname(__file__), '__pycache__')
if os.path.exists(cache_dir):
    import shutil
    shutil.rmtree(cache_dir)
    print("已清除Python缓存")

# 测试导入
print("测试导入dca_main...")
try:
    from dca_main import DCASystem
    print("导入成功")
    
    # 测试初始化
    dca = DCASystem()
    print("DCASystem初始化成功")
    
    # 测试生成报告
    print("测试生成报告...")
    dca.generate_html_report(action="测试")
    print("报告生成成功")
    
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()