@echo off
@chcp 65001 > nul
@title DCA System

cd /d "%~dp0"

echo.
echo ================================================================
echo           Dividend ETF DCA System - One Click Investment
echo ================================================================
echo.

echo [Step 1/3] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    echo Please install Python 3.x first
    pause
    exit /b 1
)
echo [OK] Python environment is ready
echo.

echo [Step 2/3] Executing monthly DCA investment...
echo ================================================================
python dca_main.py run
echo ================================================================
echo.

echo [Step 3/3] Starting Web server...
echo Web server will start at http://localhost:8080
echo.

start "" python dca_web.py

echo Waiting for web server to start...
timeout /t 3 /nobreak >nul

echo Opening web page...
start http://localhost:8080

echo.
echo ================================================================
echo DCA execution completed! Web page opened.
echo Press any key to close...
pause >nul