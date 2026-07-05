import subprocess
import time
import urllib.request

# 启动Web服务器
print("启动Web服务器...")
web_process = subprocess.Popen(['python', 'dca_web.py'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)

# 等待启动
time.sleep(3)

# 测试API
print("\n测试API端点...")
try:
    response = urllib.request.urlopen('http://localhost:8080/api/status', timeout=5)
    data = response.read().decode('utf-8')
    print("API /api/status: 正常")
    print(f"响应: {data[:200]}...")
except Exception as e:
    print(f"API /api/status: 失败 - {e}")

try:
    response = urllib.request.urlopen('http://localhost:8080/api/config', timeout=5)
    data = response.read().decode('utf-8')
    print("API /api/config: 正常")
    print(f"响应: {data[:200]}...")
except Exception as e:
    print(f"API /api/config: 失败 - {e}")

try:
    response = urllib.request.urlopen('http://localhost:8080/', timeout=5)
    data = response.read().decode('utf-8')
    print("首页: 正常")
    print(f"内容长度: {len(data)} 字符")
except Exception as e:
    print(f"首页: 失败 - {e}")

# 停止服务器
web_process.terminate()
print("\n测试完成！")