@echo off
cd /d D:\temp\红利ETF

echo ================================================================
echo           Dividend ETF DCA System - One Click Investment
echo ================================================================
echo.

echo Step 1: Check Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed or not in PATH
    echo Please install Python 3.x and add to system PATH
    pause
    exit /b 1
)
echo OK: Python environment is ready
echo.

echo Step 2: Execute monthly DCA investment...
python dca_main.py run
echo.

echo Step 3: Start web server and open browser...
python dca_main.py web
echo.

echo ================================================================
echo Process completed.
pause