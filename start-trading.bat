@echo off
title Stock Trading System Launcher
color 0A

echo ================================================================
echo                 Stock Trading System Launcher
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/4] Environment Check...
if not exist "apps\api\venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found!
    echo Please run: python -m venv apps\api\venv
    echo Then install: apps\api\venv\Scripts\pip install -r apps\api\requirements.txt
    pause
    exit /b 1
)
echo OK: Python virtual environment found

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not installed!
    echo Please download: https://nodejs.org
    pause
    exit /b 1
)
echo OK: Node.js found

echo [2/4] Install Dependencies...
if not exist "apps\ui\node_modules" (
    echo Installing frontend dependencies...
    cd apps\ui
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        cd ..\..
        exit /b 1
    )
    cd ..\..
)
echo OK: Dependencies ready

echo [3/4] Clean Processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
echo OK: Processes cleaned

echo [4/4] Starting Services...
echo Starting API Server on port 8001...
start "API-Server" cmd /c "title API-Server && apps\api\venv\Scripts\python.exe apps\api\main.py && pause"
timeout /t 5 /nobreak >nul

echo Starting Frontend Server on port 3001...
cd apps\ui
start "Frontend-Server" cmd /c "title Frontend-Server && npm run dev && pause"
cd ..\..

echo.
echo ================================================================
echo                        STARTUP COMPLETE!
echo ================================================================
echo.
echo Services:
echo   Frontend: http://localhost:3001
echo   API:      http://localhost:8001
echo   Docs:     http://localhost:8001/docs
echo.

timeout /t 3 /nobreak >nul
start http://localhost:3001 >nul 2>&1

echo Press any key to exit...
pause >nul
