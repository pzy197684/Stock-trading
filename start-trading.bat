@echo off
echo ========================================
echo Stock Trading System Startup
echo ========================================

cd /d "%~dp0"

echo.
echo Starting backend API server...
start "Trading-API" cmd /k "python apps\api\main.py"

echo Waiting 5 seconds for API to start...
timeout /t 5 /nobreak >nul

echo.
echo Starting frontend interface...
cd apps\ui  
start "Trading-UI" cmd /k "npm run dev"
cd ..\..

echo Waiting 5 seconds for UI to start...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Services Started Successfully!
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8001
echo.
echo Press any key to open frontend...
pause >nul

start http://localhost:3000

echo.
echo Services are running in separate windows.
echo Close this window to keep services running.
pause