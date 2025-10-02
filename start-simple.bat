@echo off
chcp 65001 >nul
echo ========================================
echo 启动股票交易系统
echo ========================================

cd /d "%~dp0"

echo.
echo 正在启动后端API服务器...
cd apps\api
start "后端API" cmd /k python main.py
cd ..\..

echo 等待3秒...
timeout /t 3 /nobreak >nul

echo.
echo 正在启动前端界面...
cd apps\ui  
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