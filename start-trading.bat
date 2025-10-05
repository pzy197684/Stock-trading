@echo off@echo off@echo off

chcp 65001 >nul

title 股票交易系统启动器setlocal enabledelayedexpansionsetlocal enabledelayedexpansion

color 0A

chcp 65001 >nulchcp 65001 >nul

echo ================================================================

echo                    股票交易系统启动器title 股票交易系统 - 启动脚本title Stock Trading System - Startup Script

echo                   Stock Trading System

echo ================================================================color 0Acolor 0A

echo.



cd /d "%~dp0"

echo ╔════════════════════════════════════════════════════════════════╗echo =================REM Start API server

echo [1/4] 环境检查...

if not exist "apps\api\venv\Scripts\python.exe" (echo ║                        股票交易系统                           ║echo [1/2] Starting API server...

    echo 错误: Python虚拟环境不存在！

    echo 请先运行: python -m venv apps\api\venvecho ║                      Stock Trading System                      ║start "API Server" cmd /c "title API Server - Backend Service && color 0B && echo Starting API server... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo API server stopped && pause"

    pause

    exit /b 1echo ╚════════════════════════════════════════════════════════════════╝echo Waiting for API server to start...

)

echo.

where node >nul 2>&1

if %errorlevel% neq 0 (REM Wait and verify API server startup with more retries

    echo 错误: Node.js未安装！

    pauseREM 进入脚本所在目录set API_READY=0

    exit /b 1

)cd /d "%~dp0"for /L %%i in (1,1,15) do (



echo [2/4] 清理进程...    timeout /t 2 /nobreak >nul

taskkill /f /im python.exe >nul 2>&1

taskkill /f /im node.exe >nul 2>&1echo ══════════════════════════════════════════════════════════════════    netstat -ano | findstr ":8001" | findstr "LISTENING" >nul 2>&1

timeout /t 2 /nobreak >nul

echo                           环境检查    if !errorlevel! == 0 (

echo [3/4] 启动API服务器...

start "API服务器" cmd /c "title API服务器 && apps\api\venv\Scripts\python.exe apps\api\main.py && pause"echo ══════════════════════════════════════════════════════════════════        set API_READY=1

timeout /t 5 /nobreak >nul

echo.        echo OK: API server started successfully on attempt %%i

echo [4/4] 启动前端服务器...

cd apps\ui        goto :api_ready

start "前端服务器" cmd /c "title 前端服务器 && npm run dev && pause"

cd ..\..REM 检查Python虚拟环境    ) else (



echo.echo [1/3] 检查Python虚拟环境...        echo Waiting for API server... (%%i/15)

echo ================================================================

echo 启动完成！if not exist "apps\api\venv\Scripts\python.exe" (    )

echo.

echo 服务地址:    echo ❌ Python虚拟环境不存在！)

echo   前端: http://localhost:3001

echo   API:  http://localhost:8001    echo 请运行: python -m venv apps\api\venv

echo ================================================================

echo.    echo 然后安装依赖: apps\api\venv\Scripts\pip install -r apps\api\requirements.txt:api_ready



timeout /t 3 /nobreak >nul    echo.if %API_READY%==0 (

start http://localhost:3001 >nul 2>&1

    pause    echo Warning: API server may have failed to start properly

echo 按任意键退出...

pause >nul    exit /b 1    echo Please check the API server window for error messages

)) else (

echo ✅ Python虚拟环境检查通过    echo API server is ready and listening on port 8001

)=================================

REM 检查Node.js环境echo                    Stock Trading System

echo [2/3] 检查Node.js环境...echo                      Startup Script

where node >nul 2>&1echo ================================================================

if %errorlevel% neq 0 (echo.

    echo ❌ Node.js未找到！

    echo 请安装Node.js: https://nodejs.orgREM Enter script directory

    echo.cd /d "%~dp0"

    pause

    exit /b 1echo ================================================================

)echo                      Environment Check

echo ================================================================

where npm >nul 2>&1echo.

if %errorlevel% neq 0 (

    echo ❌ npm未找到！REM Check Python virtual environment

    echo 请确保Node.js正确安装echo [1/3] Checking Python virtual environment...

    echo.if not exist "apps\api\venv\Scripts\python.exe" (

    pause    echo Error: Python virtual environment not found!

    exit /b 1    echo Please run: python -m venv apps\api\venv

)    echo Then install dependencies: apps\api\venv\Scripts\pip install -r apps\api\requirements.txt

echo ✅ Node.js和npm环境检查通过    echo.

    pause

REM 检查前端依赖    exit /b 1

echo [3/3] 检查前端依赖...)

if not exist "apps\ui\node_modules" (echo OK: Python virtual environment check passed

    echo 🔄 前端依赖未安装，自动安装中...

    cd apps\uiREM Check Node.js environment

    echo 执行: npm installecho [2/3] Checking Node.js environment...

    call npm installwhere node >nul 2>&1

    cd ..\..if %errorlevel% neq 0 (

    if %errorlevel% neq 0 (    echo Error: Node.js not found!

        echo ❌ 前端依赖安装失败    echo Please install Node.js: https://nodejs.org

        echo.    echo.

        pause    pause

        exit /b 1    exit /b 1

    ))

    echo ✅ 前端依赖安装完成

) else (where npm >nul 2>&1

    echo ✅ 前端依赖已安装if %errorlevel% neq 0 (

)    echo Error: npm not found!

    echo Please ensure Node.js is correctly installed

echo.    echo.

echo ══════════════════════════════════════════════════════════════════    pause

echo                         进程和端口清理    exit /b 1

echo ══════════════════════════════════════════════════════════════════)

echo.echo OK: Node.js and npm environment check passed



REM 清理Python进程REM Check frontend dependencies

echo [1/4] 清理Python进程...echo [3/3] Checking frontend dependencies...

tasklist | findstr python.exe >nul 2>&1if not exist "apps\ui\node_modules" (

if %errorlevel% == 0 (    echo Warning: Frontend dependencies not installed, installing automatically...

    echo 🧹 发现运行中的Python进程，正在停止...    cd apps\ui

    taskkill /f /im python.exe >nul 2>&1    echo Executing: npm install

    timeout /t 2 /nobreak >nul    call npm install

    echo ✅ Python进程已清理    cd ..\..

) else (    if %errorlevel% neq 0 (

    echo ✅ 无Python进程运行        echo Error: Frontend dependencies installation failed

)        echo.

        pause

REM 清理Node.js进程        exit /b 1

echo [2/4] 清理Node.js进程...    )

tasklist | findstr node.exe >nul 2>&1    echo OK: Frontend dependencies installation completed

if %errorlevel% == 0 () else (

    echo 🧹 发现运行中的Node.js进程，正在停止...    echo OK: Frontend dependencies already installed

    taskkill /f /im node.exe >nul 2>&1)

    timeout /t 2 /nobreak >nul

    echo ✅ Node.js进程已清理echo.

) else (echo ================================================================

    echo ✅ 无Node.js进程运行echo                     Process and Port Cleanup

)echo ================================================================

echo.

REM 清理端口8001（API服务器）

echo [3/4] 清理端口8001占用...REM Clean Python processes

netstat -ano | findstr :8001 | findstr LISTENING >nul 2>&1echo [1/4] Cleaning Python processes...

if %errorlevel% == 0 (tasklist | findstr python.exe >nul 2>&1

    echo 🧹 端口8001被占用，正在清理...if %errorlevel% == 0 (

    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (    echo Found running Python processes, stopping...

        echo   终止进程PID: %%i    taskkill /f /im python.exe >nul 2>&1

        taskkill /f /pid %%i >nul 2>&1    timeout /t 2 /nobreak >nul

    )    echo OK: Python processes cleaned

    echo ✅ 端口8001已清理) else (

) else (    echo OK: No Python processes found

    echo ✅ 端口8001空闲)

)

REM Clean Node.js processes

REM 清理端口3001（前端服务器）echo [2/4] Cleaning Node.js processes...

echo [4/4] 清理端口3001占用...tasklist | findstr node.exe >nul 2>&1

netstat -ano | findstr :3001 | findstr LISTENING >nul 2>&1if %errorlevel% == 0 (

if %errorlevel% == 0 (    echo Found running Node.js processes, stopping...

    echo 🧹 端口3001被占用，正在清理...    taskkill /f /im node.exe >nul 2>&1

    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (    timeout /t 2 /nobreak >nul

        echo   终止进程PID: %%i    echo OK: Node.js processes cleaned

        taskkill /f /pid %%i >nul 2>&1) else (

    )    echo OK: No Node.js processes found

    echo ✅ 端口3001已清理)

) else (

    echo ✅ 端口3001空闲REM Clean port 8001 (API server)

)echo [3/4] Cleaning port 8001 occupation...

netstat -ano | findstr :8001 | findstr LISTENING >nul 2>&1

REM 等待清理完成if %errorlevel% == 0 (

echo 等待清理完成...    echo Found port 8001 occupied, cleaning...

timeout /t 2 /nobreak >nul    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (

        echo   Terminating process PID: %%i

echo.        taskkill /f /pid %%i >nul 2>&1

echo ══════════════════════════════════════════════════════════════════    )

echo                           启动服务    echo OK: Port 8001 cleaned

echo ══════════════════════════════════════════════════════════════════) else (

echo.    echo OK: Port 8001 not occupied

)

REM 启动API服务器

echo [1/2] 启动API服务器...REM Clean port 3000 (frontend interface)

echo.echo [4/4] Cleaning port 3000 occupation...

echo 🚀 正在启动后端API服务器...netstat -ano | findstr :3000 | findstr LISTENING >nul 2>&1

echo    - 服务地址: http://localhost:8001if %errorlevel% == 0 (

echo    - WebSocket: ws://localhost:8001/ws/logs    echo Found port 3000 occupied, cleaning...

echo    - 健康检查: http://localhost:8001/health    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (

echo.        echo   Terminating process PID: %%i

        taskkill /f /pid %%i >nul 2>&1

start "股票交易系统-API服务器" cmd /c "title 股票交易系统-API服务器 && color 0B && echo 🚀 启动API服务器... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo 📴 API服务器已停止 && pause"    )

    echo OK: Port 3000 cleaned

REM 等待API服务器启动) else (

echo 等待API服务器启动...    echo OK: Port 3000 not occupied

echo 正在检查API服务器状态...)



set /a wait_count=0REM Wait for cleanup completion

:wait_apiecho Waiting for cleanup completion...

set /a wait_count+=1timeout /t 2 /nobreak >nul

if %wait_count% gtr 15 (

    echo ⚠️  API服务器启动时间较长，可能遇到问题echo.

    echo 请检查API服务器窗口是否有错误信息echo ================================================================

    goto continue_frontendecho                          Start Services

)echo ================================================================

echo.

timeout /t 2 /nobreak >nul

powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8001/health' -TimeoutSec 2 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1REM Start API server

if %errorlevel% neq 0 (echo [1/2] Starting API server...

    echo 继续等待API服务器启动... (%wait_count%/15)start "API Server" cmd /c "title API Server - Backend Service && color 0B && echo Starting API server... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo API server stopped && pause"

    goto wait_apiecho Waiting for API server to start...

)timeout /t 5 /nobreak >nul



echo ✅ API服务器启动成功REM Verify API server startup

echo Checking API server status...

:continue_frontendnetstat -ano | findstr :8001 | findstr LISTENING >nul 2>&1

if %errorlevel% == 0 (

REM 启动前端服务器    echo OK: API server started successfully

echo [2/2] 启动前端服务器...) else (

echo.    echo Warning: API server may have failed to start, but continuing with frontend...

echo 🌐 正在启动前端界面...)

echo    - 前端地址: http://localhost:3001

echo    - 开发模式: Vite热重载REM Start frontend server

echo.echo [2/2] Starting frontend interface...

cd apps\ui

cd apps\uistart "Frontend Interface" cmd /c "title Frontend Interface - UI Service && color 0E && echo Starting frontend interface... && npm run dev && echo Frontend interface stopped && pause"

start "股票交易系统-前端界面" cmd /c "title 股票交易系统-前端界面 && color 0E && echo 🌐 启动前端服务器... && npm run dev && echo 📴 前端服务器已停止 && pause"cd ..\..

cd ..\..echo Waiting for frontend server to start...

timeout /t 8 /nobreak >nul

REM 等待前端服务器启动

echo 等待前端服务器启动...REM Verify frontend server startup

echo 前端服务器正在启动，这可能需要几秒钟...echo Checking frontend server status...

timeout /t 8 /nobreak >nulnetstat -ano | findstr :3000 | findstr LISTENING >nul 2>&1

if %errorlevel% == 0 (

echo.    echo OK: Frontend server started successfully

echo ╔════════════════════════════════════════════════════════════════╗) else (

echo ║                        启动完成！                             ║    echo Warning: Frontend server may have failed to start

echo ╚════════════════════════════════════════════════════════════════╝)

echo.

echo 🎉 服务启动状态:echo.

echo    ✅ API服务器: http://localhost:8001echo ================================================================

echo    ✅ 前端界面: http://localhost:3001echo                         Startup Complete!

echo    ✅ WebSocket日志: ws://localhost:8001/ws/logsecho ================================================================

echo.echo.

echo 📋 管理面板:echo Service Information:

echo    📊 仪表板: http://localhost:3001echo   API Server: http://localhost:8001

echo    📈 实时监控: http://localhost:3001/monitorecho   Frontend Interface: http://localhost:3000  

echo    🔧 系统设置: http://localhost:3001/settingsecho   WebSocket Logs: ws://localhost:8001/ws/logs

echo.echo.

echo 🛠️  调试工具:echo Usage Instructions:

echo    🔍 API文档: http://localhost:8001/docsecho   - Frontend interface will open automatically in browser

echo    📝 WebSocket测试: http://localhost:8001/websocket-test.htmlecho   - Both services run in separate windows

echo    💾 日志文件: logs\runtime.logecho   - Closing this window will not affect running services

echo.echo   - To stop services, close the corresponding service windows

echo.

REM 提供操作选项echo Troubleshooting:

echo ══════════════════════════════════════════════════════════════════echo   - Check if firewall is blocking connections

echo 请选择操作:echo   - Ensure ports 8001 and 3000 are not occupied by other programs

echo   [1] 打开交易系统前端echo   - Check error messages in service windows

echo   [2] 打开API文档echo.

echo   [3] 查看系统状态

echo   [4] 查看实时日志REM Try to automatically open browser

echo   [5] 停止所有服务echo Attempting to open browser...

echo   [0] 保持后台运行timeout /t 3 /nobreak >nul

echo ══════════════════════════════════════════════════════════════════start http://localhost:3000 >nul 2>&1

echo.

echo Press any key to exit this window...

:menupause >nul

set /p choice="请输入选择 [0-5]: "    echo 🧹 端口8001被占用，正在清理...

    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (

if "%choice%"=="1" (        taskkill /f /pid %%i >nul 2>&1

    echo 正在打开交易系统前端...    )

    start http://localhost:3001    timeout /t 2 /nobreak >nul

    goto menu    echo ✅ 端口8001已清理

)) else (

    echo ✅ 端口8001空闲

if "%choice%"=="2" ()

    echo 正在打开API文档...

    start http://localhost:8001/docsREM 清理3001端口（前端服务器）

    goto menunetstat -ano | findstr :3001 | findstr LISTENING >nul 2>&1

)if %errorlevel% == 0 (

    echo 🧹 端口3001被占用，正在清理...

if "%choice%"=="3" (    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (

    echo 正在检查系统状态...        taskkill /f /pid %%i >nul 2>&1

    echo.    )

    echo 🔍 端口检查:    timeout /t 2 /nobreak >nul

    netstat -ano | findstr :8001    echo ✅ 端口3001已清理

    netstat -ano | findstr :3001) else (

    echo.    echo ✅ 端口3001空闲

    echo 🔍 WebSocket状态:)

    powershell -Command "try { $status = Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/status' -Method GET; Write-Host '连接数:' $status.websocket_status.total_log_connections; Write-Host '健康状态:' $status.health.is_healthy } catch { Write-Host '无法获取WebSocket状态' }"

    echo.echo.

    goto menuecho ══════════════════════════════════════════════════════════════════

)echo                           服务启动

echo ══════════════════════════════════════════════════════════════════

if "%choice%"=="4" (echo.

    echo 正在打开实时日志...echo.

    if exist "logs\runtime.log" (echo 🚀 正在启动后端API服务器...

        start notepad "logs\runtime.log"echo    - 服务地址: http://localhost:8001

    ) else (echo    - WebSocket: ws://localhost:8001/ws/logs

        echo 日志文件不存在echo    - 健康检查: http://localhost:8001/health

    )echo.

    goto menu

)start "股票交易系统-API服务器" cmd /c "title 股票交易系统-API服务器 && color 0B && echo 🚀 启动API服务器... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo 📴 API服务器已停止 && pause"



if "%choice%"=="5" (REM 等待API服务器启动

    echo 正在停止所有服务...echo 等待API服务器启动...

    taskkill /f /im python.exe >nul 2>&1echo 正在检查API服务器状态...

    taskkill /f /im node.exe >nul 2>&1timeout /t 5 /nobreak >nul

    echo ✅ 所有服务已停止

    echo.REM 简单的启动检查

    pauseset /a wait_count=0

    exit:wait_api

)set /a wait_count+=1

if %wait_count% gtr 20 (

if "%choice%"=="0" (    echo ⚠️  API服务器启动时间较长，可能遇到问题

    echo.    echo 请检查API服务器窗口是否有错误信息

    echo 📴 系统将在后台继续运行    echo.

    echo    - API服务器和前端服务器将保持运行    choice /c YN /m "是否继续等待? (Y/N)"

    echo    - 可随时通过浏览器访问系统    if %errorlevel% == 2 (

    echo    - 要停止服务，请重新运行此脚本并选择 [5]        echo 用户选择跳过等待

    echo.        goto skip_api_check

    echo 🔗 快速访问链接:    )

    echo    前端: http://localhost:3001    set /a wait_count=0

    echo    API:  http://localhost:8001)

    echo.

    pausepowershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8001/health' -TimeoutSec 2 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

    exitif %errorlevel% neq 0 (

)    echo 继续等待API服务器启动... (%wait_count%/20)

    timeout /t 2 /nobreak >nul

echo 无效选择，请重新输入    goto wait_api

goto menu)

echo ✅ API服务器启动成功
goto continue_frontend

:skip_api_check
echo ⚠️  跳过API服务器检查，继续启动前端

:continue_frontend

REM 启动前端服务器
echo [8/8] 启动前端服务器...
echo.
echo 🌐 正在启动前端界面...
echo    - 前端地址: http://localhost:3001
echo    - 开发模式: Vite热重载
echo.

cd apps\ui
start "股票交易系统-前端界面" cmd /c "title 股票交易系统-前端界面 && color 0E && echo 🌐 启动前端服务器... && npm run dev && echo 📴 前端服务器已停止 && pause"
cd ..\..

REM 等待前端服务器启动
echo 等待前端服务器启动...
echo 前端服务器正在启动，这可能需要几秒钟...
timeout /t 10 /nobreak >nul

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                        启动完成！                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🎉 服务启动状态:
echo    ✅ API服务器: http://localhost:8001
echo    ✅ 前端界面: http://localhost:3001
echo    ✅ WebSocket日志: ws://localhost:8001/ws/logs
echo.
echo 📋 管理面板:
echo    📊 仪表板: http://localhost:3001
echo    📈 实时监控: http://localhost:3001/monitor
echo    🔧 系统设置: http://localhost:3001/settings
echo.
echo 🛠️  调试工具:
echo    🔍 API文档: http://localhost:8001/docs
echo    📝 WebSocket测试: http://localhost:8001/websocket-test.html
echo    💾 日志文件: logs\runtime.log
echo.

REM 提供操作选项
echo ══════════════════════════════════════════════════════════════════
echo 请选择操作:
echo   [1] 打开交易系统前端
echo   [2] 打开API文档
echo   [3] 查看系统状态
echo   [4] 查看实时日志
echo   [5] 停止所有服务
echo   [0] 保持后台运行
echo ══════════════════════════════════════════════════════════════════
echo.

:menu
set /p choice="请输入选择 [0-5]: "

if "%choice%"=="1" (
    echo 正在打开交易系统前端...
    start http://localhost:3001
    goto menu
)

if "%choice%"=="2" (
    echo 正在打开API文档...
    start http://localhost:8001/docs
    goto menu
)

if "%choice%"=="3" (
    echo 正在检查系统状态...
    echo.
    echo 🔍 端口检查:
    netstat -ano | findstr :8001
    netstat -ano | findstr :3001
    echo.
    echo 🔍 WebSocket状态:
    powershell -Command "try { $status = Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/status' -Method GET; Write-Host '连接数:' $status.websocket_status.total_log_connections; Write-Host '健康状态:' $status.health.is_healthy } catch { Write-Host '无法获取WebSocket状态' }"
    echo.
    goto menu
)

if "%choice%"=="4" (
    echo 正在打开实时日志...
    if exist "logs\runtime.log" (
        start notepad "logs\runtime.log"
    ) else (
        echo 日志文件不存在
    )
    goto menu
)

if "%choice%"=="5" (
    echo 正在停止所有服务...
    taskkill /f /im python.exe >nul 2>&1
    taskkill /f /im node.exe >nul 2>&1
    echo ✅ 所有服务已停止
    echo.
    pause
    exit
)

if "%choice%"=="0" (
    echo.
    echo 📴 系统将在后台继续运行
    echo    - API服务器和前端服务器将保持运行
    echo    - 可随时通过浏览器访问系统
    echo    - 要停止服务，请重新运行此脚本并选择 [5]
    echo.
    echo 🔗 快速访问链接:
    echo    前端: http://localhost:3001
    echo    API:  http://localhost:8001
    echo.
    pause
    exit
)

echo 无效选择，请重新输入
goto menu