@echo off
title HongLi ETF DCA System

cd /d "%~dp0"

echo.
echo ================================================================
echo              HongLi ETF DCA System - One Click
echo ================================================================
echo.

echo [Step 1/3] Check Python env...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed or not in PATH
    echo Please install Python 3.x and add to PATH
    pause
    exit /b 1
)
echo [OK] Python env ready
echo.

echo [Step 2/3] Quick check DCA status...
python quick_check.py
if errorlevel 1 (
    echo [SKIP] No need to run DCA today
    echo.
) else (
    echo [NEED] Run DCA check...
    python dca_main.py run
    if errorlevel 1 (
        echo [WARN] DCA run failed, check error above
        echo Continue to start Web service...
    )
)
echo.

echo [Step 3/3] Start Web service...
echo.
echo Web service starting, please wait...
echo Browser will open automatically. Closing this window stops the service.
echo ================================================================
echo.
python dca_main.py web
if errorlevel 1 (
    echo.
    echo [ERROR] Web service start failed, check error above
    pause
    exit /b 1
)

echo.
echo Done!
pause
