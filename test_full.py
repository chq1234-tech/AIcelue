#!/usr/bin/env python3
import subprocess
import time
import urllib.request
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 测试1: 检查dca_main.py是否正常工作
print("=" * 60)
print("测试1: 检查主程序")
print("=" * 60)
try:
    from dca_main import DCASystem
    print("[OK] dca_main.py 导入成功")
    dca = DCASystem()
    print("[OK] DCASystem 初始化成功")
except Exception as e:
    print("[FAIL] 失败:", str(e).encode('utf-8', errors='replace').decode('gbk', errors='replace'))

# 测试2: 检查Web服务器
print("\n" + "=" * 60)
print("测试2: 检查Web服务器")
print("=" * 60)

# 启动服务器
print("\n启动Web服务器...")
web_process = subprocess.Popen(['python', 'dca_web.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
time.sleep(3)

# 检查服务器是否启动
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
if s.connect_ex(('127.0.0.1', 8080)) == 0:
    print("[OK] Web服务器已启动")
else:
    print("[FAIL] Web服务器未启动")
    web_process.terminate()
    exit(1)
s.close()

# 测试API
print("\n测试API端点:")
endpoints = ['/', '/api/status', '/api/config', '/api/system-params']

for endpoint in endpoints:
    try:
        url = f'http://127.0.0.1:8080{endpoint}'
        print("\n请求:", url)
        response = urllib.request.urlopen(url, timeout=5)
        status = response.status
        content = response.read()
        print("状态码:", status)
        print("内容长度:", len(content))
        
        if endpoint != '/':
            try:
                data = json.loads(content)
                print("JSON数据:", json.dumps(data, ensure_ascii=False)[:150], "...")
            except:
                print("非JSON响应")
        else:
            print("HTML内容:", content[:100].decode('utf-8', errors='ignore'), "...")
        
        print("[OK] 成功")
        
    except Exception as e:
        print("[FAIL] 失败:", type(e).__name__, str(e))

# 停止服务器
web_process.terminate()
print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)