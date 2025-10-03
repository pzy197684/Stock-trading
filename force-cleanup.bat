@echo off
chcp 65001 >nul
title 股票交易系统 - 强制清理工具
color 0C

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                      强制清理所有进程                          ║
echo ║                   Force Clean All Processes                   ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo 正在执行强力清理...
echo.

REM 第一轮：按进程名清理
echo [1/6] 按进程名清理...
echo 清理Python进程：
tasklist /fi "imagename eq python.exe" /fo table /nh 2>nul | findstr python.exe
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python进程已清理
) else (
    echo ℹ️  无Python进程需要清理
)

echo 清理Node.js进程：
tasklist /fi "imagename eq node.exe" /fo table /nh 2>nul | findstr node.exe
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Node.js进程已清理
) else (
    echo ℹ️  无Node.js进程需要清理
)

REM 第二轮：清理相关CMD窗口
echo [2/6] 清理相关CMD窗口...
powershell -Command "Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -match 'API服务器|前端界面|Trading|股票交易' } | Stop-Process -Force" >nul 2>&1
echo ✅ 相关CMD窗口已清理

REM 第三轮：清理PowerShell窗口
echo [3/6] 清理相关PowerShell窗口...
powershell -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -match 'API|前端|Trading|股票' } | Where-Object { $_.Id -ne $PID } | Stop-Process -Force" >nul 2>&1
echo ✅ 相关PowerShell窗口已清理

REM 第四轮：按端口清理
echo [4/6] 按端口清理进程...
echo 清理8001端口占用：
netstat -ano | findstr :8001 2>nul
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    echo   终止PID: %%i
    taskkill /f /pid %%i >nul 2>&1
)

echo 清理3001端口占用：
netstat -ano | findstr :3001 2>nul
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING 2^>nul') do (
    echo   终止PID: %%i
    taskkill /f /pid %%i >nul 2>&1
)

echo 清理3000端口占用：
netstat -ano | findstr :3000 2>nul
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    echo   终止PID: %%i
    taskkill /f /pid %%i >nul 2>&1
)

REM 第五轮：清理uvicorn和fastapi相关
echo [5/6] 清理Web服务器进程...
powershell -Command "Get-Process | Where-Object { $_.ProcessName -match 'uvicorn|fastapi|gunicorn' } | Stop-Process -Force" >nul 2>&1
echo ✅ Web服务器进程已清理

REM 第六轮：等待和最终验证
echo [6/6] 等待清理完成并验证...
timeout /t 3 /nobreak >nul

echo.
echo ═══════════════════════════════════════════════════════════════════
echo 最终验证结果：
echo.

echo 检查Python进程：
tasklist | findstr python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ⚠️  仍有Python进程存在：
    tasklist | findstr python.exe
) else (
    echo ✅ 无Python进程
)

echo.
echo 检查Node.js进程：
tasklist | findstr node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ⚠️  仍有Node.js进程存在：
    tasklist | findstr node.exe
) else (
    echo ✅ 无Node.js进程
)

echo.
echo 检查端口占用：
netstat -ano | findstr ":8001\|:3001\|:3000" | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo ⚠️  仍有端口被占用：
    netstat -ano | findstr ":8001\|:3001\|:3000" | findstr LISTENING
) else (
    echo ✅ 相关端口已清理
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                        清理完成！                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 现在可以安全启动交易系统了
echo.
pause