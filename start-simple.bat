@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo Starting API Server...
cd apps\api
start cmd /k python main.py
cd ..\..

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo Starting Frontend UI...
cd apps\ui  
start cmd /k npm run dev
cd ..\..

echo.
echo Both services are starting...
echo API: http://localhost:8000
echo Frontend: Check the opened windows
echo.
pause