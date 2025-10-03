@echo off
title 稳定版交易系统API服务器
echo ================================
echo    稳定版交易系统API服务器
echo ================================
echo.

REM 确保在正确的目录
cd /d "%~dp0"

REM 检查Python环境
echo [1/6] 检查Python环境...
if not exist "apps\api\venv\Scripts\python.exe" (
    echo ❌ 错误：未找到虚拟环境，请先运行 create-venv.bat
    pause
    exit /b 1
)

REM 清理之前的进程
echo [2/6] 清理之前的API进程...
tasklist | findstr python.exe >nul
if %errorlevel% == 0 (
    echo 发现运行中的Python进程，正在清理...
    taskkill /f /im python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM 清理网络连接
echo [3/6] 清理WebSocket连接...
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %errorlevel% == 0 (
    echo 端口8001被占用，正在清理...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
        taskkill /f /pid %%i >nul 2>&1
    )
    timeout /t 3 /nobreak >nul
)

REM 清理日志文件锁定
echo [4/6] 清理日志文件...
if exist "logs\runtime.log.lock" del "logs\runtime.log.lock"

REM 确保日志目录存在
if not exist "logs" mkdir logs

REM 设置环境变量
echo [5/6] 设置环境变量...
set PYTHONPATH=%CD%
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

REM 启动API服务器（稳定模式）
echo [6/6] 启动API服务器（稳定模式）...
echo.
echo 🚀 启动中...
echo 📡 WebSocket日志: ws://localhost:8001/ws/logs
echo 🌐 API接口: http://localhost:8001/api
echo 📊 健康检查: http://localhost:8001/api/health
echo.
echo 按 Ctrl+C 停止服务器
echo ================================
echo.

REM 启动服务器，加入重启机制
:restart
echo [%date% %time%] 启动API服务器...
apps\api\venv\Scripts\python.exe apps\api\main.py

REM 如果异常退出，询问是否重启
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  API服务器异常退出 (错误代码: %errorlevel%)
    echo.
    choice /c YN /m "是否重新启动API服务器? (Y/N)"
    if %errorlevel% == 1 (
        echo 正在重新启动...
        timeout /t 2 /nobreak >nul
        goto restart
    )
)

echo.
echo API服务器已停止
pause