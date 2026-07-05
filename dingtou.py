#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红利ETF定投系统 - 一键定投
自动执行定投并打开Web页面
"""

import subprocess
import time
import webbrowser
import sys
import os

def main():
    print("=" * 60)
    print("      红利ETF定投系统 - 一键定投")
    print("=" * 60)
    print()
    
    # 确保在正确的目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Step 1: Execute DCA investment
    print("[步骤1/3] 执行月度定投...")
    print("=" * 60)
    result = subprocess.run([sys.executable, "dca_main.py", "run"], 
                           capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("错误信息:", result.stderr)
    print("=" * 60)
    print()
    
    # Step 2: Start web server in background
    print("[步骤2/3] 启动Web服务器...")
    web_process = subprocess.Popen([sys.executable, "dca_web.py"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("等待Web服务器启动...")
    time.sleep(3)
    
    # Step 3: Open browser
    print("[步骤3/3] 打开Web页面...")
    url = "http://localhost:8080"
    webbrowser.open(url)
    
    print()
    print("=" * 60)
    print("定投执行完成！")
    print(f"Web页面已打开: {url}")
    print("按 Enter 键退出...")
    input()
    
    # Clean up
    web_process.terminate()

if __name__ == "__main__":
    main()