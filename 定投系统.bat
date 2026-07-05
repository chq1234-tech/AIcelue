@echo off
chcp 65001 > nul
title 平衡型定投系统 v1.0

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

REM 显示菜单
:menu
echo.
echo 请选择操作:
echo.
echo   [1] 执行月度定投
echo   [2] 检查持仓状态
echo   [3] 显示完整状态
echo   [4] 导出交易历史
echo   [5] 显示交易日历
echo   [6] 启动定时调度
echo   [7] 帮助信息
echo   [0] 退出
echo.
echo ================================================================
echo.

set /p choice=请输入选项 (0-7):

if "%choice%"=="1" goto run_dca
if "%choice%"=="2" goto check_portfolio
if "%choice%"=="3" goto show_status
if "%choice%"=="4" goto export_data
if "%choice%"=="5" goto show_calendar
if "%choice%"=="6" goto start_scheduler
if "%choice%"=="7" goto show_help
if "%choice%"=="0" goto end

echo 无效选项，请重新选择
goto menu

:run_dca
echo.
echo 正在执行月度定投...
echo.
python dca_main.py run
echo.
pause
goto menu

:check_portfolio
echo.
echo 正在检查持仓状态...
echo.
python dca_main.py check
echo.
pause
goto menu

:show_status
echo.
echo 正在显示完整状态...
echo.
python dca_main.py status
echo.
pause
goto menu

:export_data
echo.
echo 正在导出交易历史...
echo.
python dca_main.py export
echo.
pause
goto menu

:show_calendar
echo.
echo 正在显示交易日历...
echo.
python dca_main.py calendar
echo.
pause
goto menu

:start_scheduler
echo.
echo 正在启动定时调度...
echo.
echo 注意: 按 Ctrl+C 可以停止定时调度
echo.
python dca_scheduler.py start
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
echo 投资配置:
echo    - 红利ETF 20%% (515080)     : 600元/月
echo    - 沪深300   20%% (510300)    : 600元/月
echo    - 中证500   20%% (510500)    : 600元/月
echo    - 芯片ETF  12.5%% (512760)   : 400元/月
echo    - 医药ETF  12.5%% (512010)   : 400元/月
echo    - 纳指ETF   15%% (513100)    : 400元/月
echo    ---------------------------------
echo    总计: 3000元/月
echo.
echo ================================================================
pause
goto menu

:end
echo.
echo 感谢使用定投系统！
echo.
exit
