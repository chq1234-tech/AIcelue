@echo off
chcp 65001 > nul
title Auto DCA Investment

cd /d "%~dp0"

echo.
echo ================================================================
echo         Auto DCA Investment System - One Click Start
echo ================================================================
echo.

echo [1/3] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed or not in PATH
    echo Please install Python 3.x and add to PATH
    pause
    exit /b 1
)
echo OK: Python ready
echo.

echo [2/3] Running monthly DCA investment...
echo ================================================================
python dca_main.py run
echo ================================================================
echo.

echo [3/3] Starting Web server...
echo Web server: http://localhost:8080
echo.

start "" python dca_web.py

echo Waiting for server...
timeout /t 3 /nobreak >nul

echo Opening browser...
start http://localhost:8080

echo.
echo ================================================================
echo Done! Web page opened.
echo Press any key to close...
pause >nul