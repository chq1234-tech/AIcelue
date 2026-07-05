content = '''@echo off
chcp 65001 > nul
title 红利ETF定投系统

cd /d "%~dp0"

echo.
echo ================================================================
echo              红利ETF定投系统 - 一键定投
echo ================================================================
echo.

echo [步骤1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到系统PATH
    echo 请安装Python 3.x并添加到PATH
    pause
    exit /b 1
)
echo [成功] Python环境正常
echo.

echo [步骤2/3] 执行月度定投...
python dca_main.py run
echo.

echo [步骤3/3] 启动Web服务...
start "" python dca_web.py

timeout /t 3 /nobreak >nul

echo 打开Web页面...
start http://localhost:8080

echo.
echo 定投完成！Web页面已打开。
pause >nul
'''
with open('一键定投.bat', 'w', encoding='utf-8') as f:
    f.write(content)
print('BAT file created successfully')