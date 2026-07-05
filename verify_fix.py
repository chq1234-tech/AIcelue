#!/usr/bin/env python3
import os

file_path = os.path.join(os.path.dirname(__file__), 'dca_main.py')

print(f"检查文件: {file_path}")
print()

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 检查第49行（索引48）
line_49 = lines[48].strip()
print(f"第49行: {line_49}")

if 'pm.get_holding' in line_49:
    print("错误: 仍然使用 pm.get_holding")
elif 'pm.holdings.get' in line_49:
    print("正确: 使用 pm.holdings.get")
else:
    print(f"未知: {line_49}")

# 检查整个文件中是否还有 get_holding
print()
print("检查整个文件...")
has_get_holding = False
for i, line in enumerate(lines, 1):
    if 'pm.get_holding' in line:
        print(f"第{i}行: {line.strip()}")
        has_get_holding = True

if not has_get_holding:
    print("没有发现 pm.get_holding 调用")
else:
    print(f"发现 {sum(1 for line in lines if 'pm.get_holding' in line)} 处 pm.get_holding 调用")