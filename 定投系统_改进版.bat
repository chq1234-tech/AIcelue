@echo off
chcp 65001 > nul
title 平衡型定投系统 v1.0

REM 启用错误显示
setlocal enabledelayedexpansion

echo.
echo ================================================================
echo.
echo                    平衡型定投系统 v1.0
echo.
echo              基于方案2：适合大多数年轻人的定投策略
echo.
echo ================================================================
echo.

REM 切换到程序目录
cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    echo.
    echo 请先安装Python 3.x
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装后请确保添加到系统PATH
    echo.
    pause
    exit /b 1
)

REM 显示Python版本
echo [信息] 检测到Python环境
python --version
echo.

REM 检查必要的Python库
echo [检查] 正在检查依赖库...
python -c "import akshare" >nul 2>&1
if errorlevel 1 (
    echo [警告] akshare未安装
    echo 正在尝试安装...
    pip install akshare pandas python-docx schedule
    if errorlevel 1 (
        echo [错误] 安装依赖失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
)

echo.

REM 显示菜单
:menu
echo.
echo ================================================================
echo 请选择操作:
echo ================================================================
echo.
echo   [1] 执行月度定投
echo   [2] 检查持仓状态
echo   [3] 显示完整状态
echo   [4] 导出交易历史
echo   [5] 显示交易日历
echo   [6] 启动定时调度
echo   [7] 帮助信息
echo   [8] 系统诊断
echo   [0] 退出
echo.
echo ================================================================
echo.

set /p choice=请输入选项 (0-8):

if "%choice%"=="1" goto run_dca
if "%choice%"=="2" goto check_portfolio
if "%choice%"=="3" goto show_status
if "%choice%"=="4" goto export_data
if "%choice%"=="5" goto show_calendar
if "%choice%"=="6" goto start_scheduler
if "%choice%"=="7" goto show_help
if "%choice%"=="8" goto run_diagnose
if "%choice%"=="0" goto end

echo.
echo [错误] 无效选项: %choice%
echo.

goto menu

:run_dca
echo.
echo [操作] 执行月度定投
echo ================================================================
echo.
python dca_main.py run
set error_code=%errorlevel%
echo.
if %error_code% neq 0 (
    echo [错误] 定投执行失败，错误代码: %error_code%
) else (
    echo [成功] 定投执行完成
)
echo.
pause
goto menu

:check_portfolio
echo.
echo [操作] 检查持仓状态
echo ================================================================
echo.
python dca_main.py check
set error_code=%errorlevel%
echo.
pause
goto menu

:show_status
echo.
echo [操作] 显示完整状态
echo ================================================================
echo.
python dca_main.py status
set error_code=%errorlevel%
echo.
pause
goto menu

:export_data
echo.
echo [操作] 导出交易历史
echo ================================================================
echo.
python dca_main.py export
set error_code=%errorlevel%
echo.
pause
goto menu

:show_calendar
echo.
echo [操作] 显示交易日历
echo ================================================================
echo.
python dca_main.py calendar
set error_code=%errorlevel%
echo.
pause
goto menu

:start_scheduler
echo.
echo [操作] 启动定时调度
echo ================================================================
echo.
echo [注意] 按 Ctrl+C 可以停止定时调度
echo.
python dca_scheduler.py start
set error_code=%errorlevel%
echo.
pause
goto menu

:show_help
echo.
echo ================================================================
echo                        帮助信息
echo ================================================================
echo.
echo 1. 执行月度定投
echo    每月第一个交易日自动买入配置的ETF
echo.
echo 2. 检查持仓状态
echo    查看当前持仓、市值、盈亏情况
echo.
echo 3. 显示完整状态
echo    显示月度交易日信息和持仓详情
echo.
echo 4. 导出交易历史
echo    将所有交易记录导出为CSV文件
echo.
echo 5. 显示交易日历
echo    查看当月所有交易日
echo.
echo 6. 启动定时调度
echo    自动在每个交易日执行定投检查
echo.
echo 7. 系统诊断
echo    检查系统环境和依赖是否正常
echo.
echo ================================================================
echo                        投资配置
echo ================================================================
echo.
echo - 红利ETF 20%% (515080)     : 600元/月
echo - 沪深300   20%% (510300)    : 600元/月
echo - 中证500   20%% (510500)    : 600元/月
echo - 芯片ETF  12.5%% (512760)   : 400元/月
echo - 医药ETF  12.5%% (512010)   : 400元/月
echo - 纳指ETF   15%% (513100)    : 400元/月
echo ----------------------------------------
echo 总计: 3000元/月
echo.
echo ================================================================
echo.
pause
goto menu

:run_diagnose
echo.
echo [操作] 运行系统诊断
echo ================================================================
echo.
python 诊断工具.py
set error_code=%errorlevel%
echo.
if %error_code% neq 0 (
    echo [警告] 诊断发现问题，请检查上述错误信息
)
pause
goto menu

:end
echo.
echo ================================================================
echo.
echo              感谢使用定投系统！
echo.
echo ================================================================
echo.
exit
