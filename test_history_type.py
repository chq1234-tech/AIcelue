#!/usr/bin/env python3
import requests

r = requests.get('http://127.0.0.1:8080/api/history')
data = r.json()
print(f'Total trades: {len(data)}')
print('Last 5 trades with type:')
for t in data[-5:]:
    trade_type = t.get('type', 'N/A')
    print(f"  {trade_type:12} {t['timestamp']} {t['code']} {t['name']}")
