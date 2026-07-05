@echo off
cd /d D:\temp\红利ETF
echo Step 1: Execute DCA investment
python dca_main.py run
echo.
echo Step 2: Start web server and open browser
python dca_main.py web
pause