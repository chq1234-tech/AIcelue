import socket
import time
import subprocess

# 启动服务器
print("启动Web服务器...")
web_process = subprocess.Popen(['python', 'dca_web.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)

# 检查端口
for i in range(10):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 8080))
        if result == 0:
            print(f"端口8080已打开 (尝试 {i+1}/10)")
            s.close()
            break
        else:
            print(f"端口8080未打开 (尝试 {i+1}/10)")
        s.close()
    except Exception as e:
        print(f"检查端口时出错: {e}")
    time.sleep(1)
else:
    print("服务器启动失败")
    web_process.terminate()
    exit(1)

# 尝试连接
print("\n尝试连接API...")
try:
    import urllib.request
    import urllib.error
    
    url = 'http://127.0.0.1:8080/api/status'
    print(f"请求: {url}")
    
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request, timeout=10)
    
    print(f"状态码: {response.status}")
    content = response.read()
    print(f"响应长度: {len(content)}")
    print(f"响应内容: {content[:200]}")
    
except urllib.error.URLError as e:
    print(f"URL错误: {e}")
    print(f"原因: {e.reason}")
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")

web_process.terminate()
print("\n测试完成！")