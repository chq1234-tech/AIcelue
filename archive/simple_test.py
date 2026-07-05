import subprocess
import time
import urllib.request

# 启动服务器
print("启动Web服务器...")
web_process = subprocess.Popen(['python', 'dca_web.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
time.sleep(3)

# 测试API
print("\n测试API:")
try:
    url = 'http://127.0.0.1:8080/api/status'
    print(f"请求: {url}")
    response = urllib.request.urlopen(url, timeout=5)
    status_code = response.status
    print(f"状态码: {status_code}")
    
    content = response.read()
    print(f"响应长度: {len(content)} 字节")
    print(f"响应内容: {content[:200].decode('utf-8', errors='ignore')}...")
    
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")

# 停止服务器
web_process.terminate()
print("\n测试完成！")