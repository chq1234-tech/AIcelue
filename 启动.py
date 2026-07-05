import subprocess
import time
import webbrowser
import sys
import os

# 切换到程序目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("执行月度定投...")
# 使用正确的编码处理
result = subprocess.run([sys.executable, "dca_main.py", "run"], 
                       capture_output=True, text=True, encoding='gbk', errors='ignore')
print(result.stdout)
if result.stderr:
    print("错误:", result.stderr)

print("\n启动Web服务...")
# 不捕获输出，避免编码问题
web_process = subprocess.Popen([sys.executable, "dca_web.py"])

# 等待服务器启动
time.sleep(5)

print("打开Web页面...")
webbrowser.open("http://127.0.0.1:8080")

print("完成！")