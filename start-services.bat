@echo off
echo ========================================
echo  启动股票交易系统服务
echo ========================================

echo.
echo 检查并清理已占用的端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    if not "%%a"=="0" (
        echo 停止占用端口8001的进程 %%a
        taskkill /PID %%a /F >nul 2>&1
    )
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    if not "%%a"=="0" (
        echo 停止占用端口3000的进程 %%a
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo.
echo 启动后端API服务器...
start "API Server" cmd /c "cd /d %~dp0 && python apps\api\main.py"
timeout /t 5 /nobreak >nul

echo.
echo 启动前端开发服务器...
start "Frontend Server" cmd /c "cd /d %~dp0\apps\ui && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ✅ 服务启动完成！
echo.
echo 🌐 前端地址: http://localhost:3000 或 http://localhost:3001
echo 🔌 API地址: http://localhost:8001
echo.
echo 按任意键打开前端页面...
pause >nul

start http://localhost:3000

echo.
echo 提示：关闭此窗口将停止所有服务
echo 按任意键退出...
pause >nul