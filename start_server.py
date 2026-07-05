#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dca_web import app

print("=" * 70)
print("平衡型定投系统 Web版 v1.1")
print("=" * 70)
print("\nWeb server starting at: http://127.0.0.1:8080")

app.run(host='0.0.0.0', port=8080, debug=False)
