#!/usr/bin/env python3
import subprocess
import time
import urllib.request
import json
import socket

print("启动Web服务器...")
web_process = subprocess.Popen(['python', 'dca_web.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)

# 等待服务器启动
for i in range(10):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex(('127.0.0.1', 8080)) == 0:
            print(f"服务器已启动")
            s.close()
            break
        s.close()
    except:
        pass
    time.sleep(1)

time.sleep(2)

# 测试第一次加载（需要获取价格）
print("\n测试第一次加载（需要获取价格）:")
start_time = time.time()
try:
    response = urllib.request.urlopen('http://127.0.0.1:8080/api/portfolio', timeout=30)
    data = json.loads(response.read())
    elapsed = time.time() - start_time
    print(f"✓ 成功，耗时: {elapsed:.2f}秒")
    print(f"  持仓数量: {len(data.get('holdings', []))}")
except Exception as e:
    print(f"✗ 失败: {e}")

# 测试第二次加载（使用缓存）
print("\n测试第二次加载（使用缓存）:")
start_time = time.time()
try:
    response = urllib.request.urlopen('http://127.0.0.1:8080/api/portfolio', timeout=30)
    data = json.loads(response.read())
    elapsed = time.time() - start_time
    print(f"✓ 成功，耗时: {elapsed:.2f}秒")
    print(f"  持仓数量: {len(data.get('holdings', []))}")
except Exception as e:
    print(f"✗ 失败: {e}")

web_process.terminate()
print("\n测试完成！")