import subprocess
import time
import urllib.request
import json
import socket
import os

def test_web_server():
    """测试Web服务器"""
    print("=" * 60)
    print("测试Web服务")
    print("=" * 60)
    
    # 检查端口
    port = 8080
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    if s.connect_ex(('localhost', port)) == 0:
        print(f"端口 {port} 已打开")
    else:
        print(f"端口 {port} 未打开，启动服务器...")
        subprocess.Popen(['python', 'dca_web.py'])
        time.sleep(3)
    
    # 测试首页
    print("\n测试首页:")
    try:
        response = urllib.request.urlopen('http://localhost:8080/', timeout=5)
        content = response.read()
        print(f"  状态码: {response.status}")
        print(f"  内容长度: {len(content)}")
        print("  ✓ 首页正常")
    except Exception as e:
        print(f"  ✗ 首页失败: {e}")
    
    # 测试API
    print("\n测试API:")
    endpoints = ['/api/status', '/api/config', '/api/system-params']
    
    for endpoint in endpoints:
        try:
            response = urllib.request.urlopen(f'http://localhost:8080{endpoint}', timeout=5)
            data = response.read().decode('utf-8')
            print(f"  ✓ {endpoint}: 正常")
            # 尝试解析JSON
            try:
                json_data = json.loads(data)
                print(f"    响应数据: {json.dumps(json_data, ensure_ascii=False)[:100]}...")
            except:
                print(f"    响应不是JSON")
        except Exception as e:
            print(f"  ✗ {endpoint}: {e}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    test_web_server()