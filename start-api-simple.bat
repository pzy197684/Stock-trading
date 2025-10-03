@echo off
cd /d "%~dp0"

REM Kill existing Python processes
taskkill /f /im python.exe >nul 2>&1

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start API server
echo Starting API server...
apps\api\venv\Scripts\python.exe apps\api\main.py