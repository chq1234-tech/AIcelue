bat_content = '''@echo off
echo Test batch file
python dca_main.py run
python dca_main.py web
pause
'''

with open('SimpleDCA.bat', 'w', encoding='utf-8') as f:
    f.write(bat_content)
print('SimpleDCA.bat created successfully')