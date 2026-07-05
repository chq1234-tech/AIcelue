#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投系统启动脚本 - 保持服务器持续运行
"""

import subprocess
import sys
import os
import time

def main():
    os.chdir(r'D:\temp\红利ETF')
    
    print("=" * 60)
    print("平衡型定投系统 - 启动脚本")
    print("=" * 60)
    
    # 检查是否已有服务器运行
    try:
        import urllib.request
        response = urllib.request.urlopen('http://127.0.0.1:8080', timeout=3)
        if response.status == 200:
            print("[WARN] 检测到定投系统已在运行")
            print("[INFO] 访问地址: http://127.0.0.1:8080")
            input("按回车键退出...")
            return
    except:
        pass
    
    print("[INFO] 启动定投系统 Web 服务器...")
    print("[INFO] 访问地址: http://127.0.0.1:8080")
    print("[INFO] 按 Ctrl+C 停止服务器")
    print("-" * 60)
    
    # 启动服务器
    while True:
        try:
            server = subprocess.Popen(
                [sys.executable, 'dca_web.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # 实时输出日志
            while server.poll() is None:
                line = server.stdout.readline()
                if line:
                    print(line.strip())
                    # 检查是否启动成功
                    if 'Running on http://127.0.0.1:8080' in line:
                        print("[OK] 服务器启动成功!")
            
            # 如果服务器意外退出，自动重启
            if server.returncode != 0:
                print(f"[WARN] 服务器意外退出 (代码: {server.returncode})")
                print("[INFO] 5秒后自动重启...")
                time.sleep(5)
            else:
                print("[INFO] 服务器正常停止")
                break
                
        except KeyboardInterrupt:
            print("\n[INFO] 用户手动停止")
            if 'server' in locals():
                server.terminate()
            break
        except Exception as e:
            print(f"[ERROR] 启动失败: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()