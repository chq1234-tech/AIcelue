#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

# 清除所有Python缓存
print("清除Python缓存...")
cache_dirs = ['__pycache__', '.pytest_cache']
for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print(f"  已删除: {cache_dir}")

# 清除.pyc文件
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc') or file.endswith('.pyo'):
            os.remove(os.path.join(root, file))
            print(f"  已删除: {os.path.join(root, file)}")

print("\n测试dca_main.py...")
result = subprocess.run([sys.executable, 'dca_main.py', 'check'], 
                       capture_output=True, text=True, encoding='utf-8', errors='ignore')

print("标准输出:")
print(result.stdout)

if result.stderr:
    print("\n错误输出:")
    print(result.stderr)

print(f"\n返回码: {result.returncode}")

if result.returncode == 0:
    print("\n测试成功！")
else:
    print("\n测试失败！")