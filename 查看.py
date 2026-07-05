import subprocess
import time
import webbrowser

print("启动Web服务...")
subprocess.Popen(['python', 'dca_web.py'])
time.sleep(3)

print("打开浏览器...")
webbrowser.open("http://127.0.0.1:8080")

print("完成！")