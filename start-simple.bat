@echo off
chcp 65001 >nul
title 股票交易系统 - 简化启动
color 0A

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    股票交易系统启动程序                        ║
echo ║                      简化版本                                  ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/4] 强制清理所有进程...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] 清理端口占用...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%i >nul 2>&1
)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING 2^>nul') do (
    taskkill /f /pid %%i >nul 2>&1
)

echo [3/4] 启动API服务器...
start "API服务器" cmd /c "title API服务器 && color 0B && apps\api\venv\Scripts\python.exe apps\api\main.py && pause"
timeout /t 5 /nobreak >nul

echo [4/4] 启动前端界面...
cd apps\ui
start "前端界面" cmd /c "title 前端界面 && color 0E && npm run dev && pause"
cd ..\..

echo.
echo ✅ 启动完成！
echo   API服务器: http://localhost:8001
echo   前端界面: http://localhost:3001
echo.
echo 服务在新窗口运行，可关闭此窗口
pause >nul  
start "前端界面" cmd /k npm run dev
cd ..\..

echo.
echo ✅ 服务启动完成！
echo.
echo 🌐 前端: http://localhost:3000
echo 🔌 后端: http://localhost:8001
echo.
echo 按任意键打开前端页面...
pause >nul

start http://localhost:3000

echo.
echo 提示：保持两个命令窗口打开以维持服务运行
echo API: http://localhost:8000
echo Frontend: Check the opened windows
echo.
pause