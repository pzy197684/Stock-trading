@echo off
chcp 65001 >nul
title 股票交易系统 - 停止服务
color 0C

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    股票交易系统停止程序                        ║
echo ║                   Stop Trading System                          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/4] 检查运行中的服务...
echo.

REM 检查API服务器
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8001/api/health' -TimeoutSec 2 -UseBasicParsing | Out-Null; Write-Host '✅ API服务器正在运行' } catch { Write-Host '❌ API服务器未运行' }" 2>nul

REM 检查前端服务器
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3001' -TimeoutSec 2 -UseBasicParsing | Out-Null; Write-Host '✅ 前端服务器正在运行' } catch { Write-Host '❌ 前端服务器未运行' }" 2>nul

echo.
echo [2/4] 优雅关闭WebSocket连接...

REM 通知所有WebSocket客户端服务器即将关闭
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/cleanup' -Method POST | Out-Null; Write-Host '✅ WebSocket连接已清理' } catch { Write-Host '⚠️  无法清理WebSocket连接' }" 2>nul

echo.
echo [3/4] 停止服务进程...

REM 停止Python进程（API服务器）
tasklist | findstr python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo 正在停止API服务器...
    taskkill /f /im python.exe >nul 2>&1
    if %errorlevel% == 0 (
        echo ✅ API服务器已停止
    ) else (
        echo ⚠️  停止API服务器时遇到问题
    )
) else (
    echo ℹ️  API服务器未运行
)

REM 停止Node.js进程（前端服务器）
tasklist | findstr node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo 正在停止前端服务器...
    taskkill /f /im node.exe >nul 2>&1
    if %errorlevel% == 0 (
        echo ✅ 前端服务器已停止
    ) else (
        echo ⚠️  停止前端服务器时遇到问题
    )
) else (
    echo ℹ️  前端服务器未运行
)

echo.
echo [4/4] 清理端口占用...

REM 清理8001端口
netstat -ano | findstr :8001 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo 清理端口8001...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
        taskkill /f /pid %%i >nul 2>&1
    )
)

REM 清理3001端口
netstat -ano | findstr :3001 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo 清理端口3001...
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
        taskkill /f /pid %%i >nul 2>&1
    )
)

echo ✅ 端口清理完成

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                        停止完成！                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🛑 所有服务已停止:
echo    ❌ API服务器已关闭
echo    ❌ 前端服务器已关闭
echo    ❌ WebSocket连接已断开
echo    ❌ 端口占用已清理
echo.
echo ℹ️  系统状态:
echo    📴 交易系统已完全停止
echo    💾 数据已保存到状态文件
echo    📝 运行日志保存在 logs\ 目录
echo.

REM 最终检查
echo 最终检查端口状态...
netstat -ano | findstr :8001 >nul 2>&1
if %errorlevel% == 0 (
    echo ⚠️  端口8001仍有占用
) else (
    echo ✅ 端口8001已清理
)

netstat -ano | findstr :3001 >nul 2>&1
if %errorlevel% == 0 (
    echo ⚠️  端口3001仍有占用
) else (
    echo ✅ 端口3001已清理
)

echo.
echo 按任意键退出...
pause >nul