@echo off
title Stock Trading System - Simple Launcher
color 0A

echo ================================================================
echo           Stock Trading System - Simple Launcher
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/3] Clean Conflicting Processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
echo OK: Processes cleaned

echo [2/3] Starting API Server on port 8001...
start "API-Server" cmd /c "title API-Server && apps\api\venv\Scripts\python.exe apps\api\main.py && pause"
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend Server on port 3001...
cd apps\ui
start "Frontend-Server" cmd /c "title Frontend-Server && npm run dev && pause"
cd ..\..

echo.
echo ================================================================
echo                    SERVICES STARTED!
echo ================================================================
echo.
echo Access URLs:
echo   Frontend: http://localhost:3001
echo   API:      http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo.

timeout /t 3 /nobreak >nul
start http://localhost:3001 >nul 2>&1

echo Press any key to exit...
pause >nul