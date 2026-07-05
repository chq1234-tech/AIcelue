@echo off
cd /d "d:\temp\红利ETF"
echo Testing calendar module...
"C:\Users\18502\AppData\Local\Programs\Python\Python312\python.exe" -c "
import sys
sys.path.insert(0, '.')
from datetime import datetime
from dca_calendar import get_trading_days, is_first_trading_day

today = datetime.now()
year = today.year
month = today.month

print(f'Today: {today.strftime(\"%Y-%m-%d\")} ({today.strftime(\"%A\")})')
print(f'Year: {year}, Month: {month}')
print()

# Get trading days
days = get_trading_days(year, month)
print(f'Trading days this month: {len(days)}')
if days:
    print(f'First trading day: {days[0]}')
    print(f'Last trading day: {days[-1]}')
print()

# Check if today is first trading day
is_first = is_first_trading_day()
print(f'Is today the first trading day? {is_first}')
print(f'Is today in trading days? {today.strftime(\"%Y-%m-%d\") in days}')
"
pause
