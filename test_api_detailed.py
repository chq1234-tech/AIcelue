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
            print("服务器已启动")
            s.close()
            break
        s.close()
    except:
        pass
    time.sleep(1)
else:
    print("服务器启动失败")
    web_process.terminate()
    exit(1)

time.sleep(2)

# 测试所有API
endpoints = [
    '/',
    '/api/status',
    '/api/config',
    '/api/system-params',
    '/api/portfolio',
    '/api/history',
    '/api/calendar',
    '/api/review'
]

print("\n测试API端点:")
for endpoint in endpoints:
    try:
        url = f'http://127.0.0.1:8080{endpoint}'
        print(f"\n请求: {endpoint}")
        response = urllib.request.urlopen(url, timeout=10)
        status = response.status
        content = response.read()
        
        print(f"  状态码: {status}")
        print(f"  内容长度: {len(content)}")
        
        if endpoint != '/':
            try:
                data = json.loads(content)
                if 'error' in data:
                    print(f"  错误: {data['error']}")
                else:
                    print(f"  数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {e}")
                print(f"  原始内容: {content[:100]}")
        
    except urllib.error.URLError as e:
        print(f"  URL错误: {e}")
    except Exception as e:
        print(f"  错误: {type(e).__name__}: {e}")

web_process.terminate()
print("\n测试完成！")