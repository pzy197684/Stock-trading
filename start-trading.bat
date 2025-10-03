@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Stock Trading System - Startup Script
color 0A

echo =================REM Start API server
echo [1/2] Starting API server...
start "API Server" cmd /c "title API Server - Backend Service && color 0B && echo Starting API server... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo API server stopped && pause"
echo Waiting for API server to start...

REM Wait and verify API server startup with more retries
set API_READY=0
for /L %%i in (1,1,15) do (
    timeout /t 2 /nobreak >nul
    netstat -ano | findstr ":8001" | findstr "LISTENING" >nul 2>&1
    if !errorlevel! == 0 (
        set API_READY=1
        echo OK: API server started successfully on attempt %%i
        goto :api_ready
    ) else (
        echo Waiting for API server... (%%i/15)
    )
)

:api_ready
if %API_READY%==0 (
    echo Warning: API server may have failed to start properly
    echo Please check the API server window for error messages
) else (
    echo API server is ready and listening on port 8001
)=================================
echo                    Stock Trading System
echo                      Startup Script
echo ================================================================
echo.

REM Enter script directory
cd /d "%~dp0"

echo ================================================================
echo                      Environment Check
echo ================================================================
echo.

REM Check Python virtual environment
echo [1/3] Checking Python virtual environment...
if not exist "apps\api\venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found!
    echo Please run: python -m venv apps\api\venv
    echo Then install dependencies: apps\api\venv\Scripts\pip install -r apps\api\requirements.txt
    echo.
    pause
    exit /b 1
)
echo OK: Python virtual environment check passed

REM Check Node.js environment
echo [2/3] Checking Node.js environment...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js not found!
    echo Please install Node.js: https://nodejs.org
    echo.
    pause
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: npm not found!
    echo Please ensure Node.js is correctly installed
    echo.
    pause
    exit /b 1
)
echo OK: Node.js and npm environment check passed

REM Check frontend dependencies
echo [3/3] Checking frontend dependencies...
if not exist "apps\ui\node_modules" (
    echo Warning: Frontend dependencies not installed, installing automatically...
    cd apps\ui
    echo Executing: npm install
    call npm install
    cd ..\..
    if %errorlevel% neq 0 (
        echo Error: Frontend dependencies installation failed
        echo.
        pause
        exit /b 1
    )
    echo OK: Frontend dependencies installation completed
) else (
    echo OK: Frontend dependencies already installed
)

echo.
echo ================================================================
echo                     Process and Port Cleanup
echo ================================================================
echo.

REM Clean Python processes
echo [1/4] Cleaning Python processes...
tasklist | findstr python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo Found running Python processes, stopping...
    taskkill /f /im python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo OK: Python processes cleaned
) else (
    echo OK: No Python processes found
)

REM Clean Node.js processes
echo [2/4] Cleaning Node.js processes...
tasklist | findstr node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo Found running Node.js processes, stopping...
    taskkill /f /im node.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo OK: Node.js processes cleaned
) else (
    echo OK: No Node.js processes found
)

REM Clean port 8001 (API server)
echo [3/4] Cleaning port 8001 occupation...
netstat -ano | findstr :8001 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo Found port 8001 occupied, cleaning...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
        echo   Terminating process PID: %%i
        taskkill /f /pid %%i >nul 2>&1
    )
    echo OK: Port 8001 cleaned
) else (
    echo OK: Port 8001 not occupied
)

REM Clean port 3000 (frontend interface)
echo [4/4] Cleaning port 3000 occupation...
netstat -ano | findstr :3000 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo Found port 3000 occupied, cleaning...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
        echo   Terminating process PID: %%i
        taskkill /f /pid %%i >nul 2>&1
    )
    echo OK: Port 3000 cleaned
) else (
    echo OK: Port 3000 not occupied
)

REM Wait for cleanup completion
echo Waiting for cleanup completion...
timeout /t 2 /nobreak >nul

echo.
echo ================================================================
echo                          Start Services
echo ================================================================
echo.

REM Start API server
echo [1/2] Starting API server...
start "API Server" cmd /c "title API Server - Backend Service && color 0B && echo Starting API server... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo API server stopped && pause"
echo Waiting for API server to start...
timeout /t 5 /nobreak >nul

REM Verify API server startup
echo Checking API server status...
netstat -ano | findstr :8001 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo OK: API server started successfully
) else (
    echo Warning: API server may have failed to start, but continuing with frontend...
)

REM Start frontend server
echo [2/2] Starting frontend interface...
cd apps\ui
start "Frontend Interface" cmd /c "title Frontend Interface - UI Service && color 0E && echo Starting frontend interface... && npm run dev && echo Frontend interface stopped && pause"
cd ..\..
echo Waiting for frontend server to start...
timeout /t 8 /nobreak >nul

REM Verify frontend server startup
echo Checking frontend server status...
netstat -ano | findstr :3000 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo OK: Frontend server started successfully
) else (
    echo Warning: Frontend server may have failed to start
)

echo.
echo ================================================================
echo                         Startup Complete!
echo ================================================================
echo.
echo Service Information:
echo   API Server: http://localhost:8001
echo   Frontend Interface: http://localhost:3000  
echo   WebSocket Logs: ws://localhost:8001/ws/logs
echo.
echo Usage Instructions:
echo   - Frontend interface will open automatically in browser
echo   - Both services run in separate windows
echo   - Closing this window will not affect running services
echo   - To stop services, close the corresponding service windows
echo.
echo Troubleshooting:
echo   - Check if firewall is blocking connections
echo   - Ensure ports 8001 and 3000 are not occupied by other programs
echo   - Check error messages in service windows
echo.

REM Try to automatically open browser
echo Attempting to open browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000 >nul 2>&1

echo Press any key to exit this window...
pause >nul
    echo 🧹 端口8001被占用，正在清理...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
        taskkill /f /pid %%i >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo ✅ 端口8001已清理
) else (
    echo ✅ 端口8001空闲
)

REM 清理3001端口（前端服务器）
netstat -ano | findstr :3001 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo 🧹 端口3001被占用，正在清理...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
        taskkill /f /pid %%i >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo ✅ 端口3001已清理
) else (
    echo ✅ 端口3001空闲
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo                           服务启动
echo ══════════════════════════════════════════════════════════════════
echo.
echo.
echo 🚀 正在启动后端API服务器...
echo    - 服务地址: http://localhost:8001
echo    - WebSocket: ws://localhost:8001/ws/logs
echo    - 健康检查: http://localhost:8001/health
echo.

start "股票交易系统-API服务器" cmd /c "title 股票交易系统-API服务器 && color 0B && echo 🚀 启动API服务器... && apps\api\venv\Scripts\python.exe apps\api\main.py && echo 📴 API服务器已停止 && pause"

REM 等待API服务器启动
echo 等待API服务器启动...
echo 正在检查API服务器状态...
timeout /t 5 /nobreak >nul

REM 简单的启动检查
set /a wait_count=0
:wait_api
set /a wait_count+=1
if %wait_count% gtr 20 (
    echo ⚠️  API服务器启动时间较长，可能遇到问题
    echo 请检查API服务器窗口是否有错误信息
    echo.
    choice /c YN /m "是否继续等待? (Y/N)"
    if %errorlevel% == 2 (
        echo 用户选择跳过等待
        goto skip_api_check
    )
    set /a wait_count=0
)

powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8001/health' -TimeoutSec 2 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo 继续等待API服务器启动... (%wait_count%/20)
    timeout /t 2 /nobreak >nul
    goto wait_api
)

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