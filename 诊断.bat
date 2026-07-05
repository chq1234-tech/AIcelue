@echo off
chcp 65001 > nul
title 定投系统诊断

echo.
echo ================================================================
echo                  定投系统诊断工具
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    echo.
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit
)
python --version
echo [OK] Python环境正常
echo.

echo [2/5] 检查依赖库...
python -c "import pandas; print('pandas', pandas.__version__)" >nul 2>&1
if errorlevel 1 (
    echo [警告] pandas未安装，正在安装...
    pip install pandas -q
    if errorlevel 1 (
        echo [错误] pandas安装失败
        pause
        exit
    )
)
echo [OK] pandas已安装

python -c "import akshare" >nul 2>&1
if errorlevel 1 (
    echo [警告] akshare未安装，正在安装...
    pip install akshare -q
    if errorlevel 1 (
        echo [错误] akshare安装失败
        echo.
        echo 请尝试手动安装:
        echo   pip install akshare
        pause
        exit
    )
)
echo [OK] akshare已安装

python -c "import docx" >nul 2>&1
if errorlevel 1 (
    echo [警告] python-docx未安装，正在安装...
    pip install python-docx -q
)
echo [OK] python-docx已安装
echo.

echo [3/5] 检查核心文件...
set missing=0
for %%f in (dca_config.py dca_calendar.py dca_trading.py dca_portfolio_manager.py dca_main.py) do (
    if not exist "%%f" (
        echo [错误] 缺失文件: %%f
        set missing=1
    )
)
if %missing%==1 (
    echo.
    echo [错误] 部分核心文件缺失！
    echo 请确保所有dca_*.py文件都在同一目录下
    pause
    exit
)
echo [OK] 所有核心文件存在
echo.

echo [4/5] 测试模块导入...
python -c "import dca_config; print('dca_config OK')" >temp_test.txt 2>&1
type temp_test.txt
if errorlevel 1 goto import_error

python -c "import dca_calendar; print('dca_calendar OK')" >temp_test.txt 2>&1
type temp_test.txt
if errorlevel 1 goto import_error

python -c "import dca_portfolio_manager; print('dca_portfolio_manager OK')" >temp_test.txt 2>&1
type temp_test.txt
if errorlevel 1 goto import_error

python -c "import dca_trading; print('dca_trading OK')" >temp_test.txt 2>&1
type temp_test.txt
if errorlevel 1 goto import_error

python -c "import dca_main; print('dca_main OK')" >temp_test.txt 2>&1
type temp_test.txt
if errorlevel 1 goto import_error

del temp_test.txt >nul 2>&1
echo [OK] 所有模块导入成功
echo.

echo [5/5] 测试日历功能...
python -c "from dca_calendar import get_current_month_info; info=get_current_month_info(); print(f\"月份: {info['year']}年{info['month']}月\"); print(f\"交易日: {info['total_trading_days']}天\")" >temp_test.txt 2>&1
type temp_test.txt
if errorlevel 1 goto calendar_error

del temp_test.txt >nul 2>&1
echo [OK] 日历功能正常
echo.

echo ================================================================
echo                    所有检查通过！
echo ================================================================
echo.
echo 现在您可以运行主程序了：
echo.
echo   方案1: 双击『定投系统_改进版.bat』
echo   方案2: 运行 python dca_main.py check
echo.
echo ================================================================
echo.
pause
exit

:import_error
echo.
echo [错误] 模块导入失败！
echo.
echo 错误信息:
type temp_test.txt
echo.
echo 请将上述错误信息发送给开发者获取帮助
echo.
echo 或者尝试重新安装依赖:
echo   pip install akshare pandas python-docx schedule
echo.
del temp_test.txt >nul 2>&1
pause
exit

:calendar_error
echo.
echo [错误] 日历模块测试失败！
echo.
echo 错误信息:
type temp_test.txt
echo.
echo 请检查网络连接后重试
echo.
del temp_test.txt >nul 2>&1
pause
exit
