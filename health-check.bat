@echo off
chcp 65001 >nul
title 股票交易系统 - 健康检查
color 0A

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    股票交易系统健康检查                        ║
echo ║                   System Health Check                          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [系统状态检查] 正在检查各项服务状态...
echo.

REM 检查API服务器
echo [1/8] API服务器状态检查...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/api/health' -Method GET -TimeoutSec 5; Write-Host '✅ API服务器: 正常运行'; Write-Host '   响应时间: OK'; Write-Host '   版本信息:', $response.version } catch { Write-Host '❌ API服务器: 无响应或异常' }" 2>nul

echo.
echo [2/8] 前端服务器状态检查...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3001' -TimeoutSec 5 -UseBasicParsing | Out-Null; Write-Host '✅ 前端服务器: 正常运行' } catch { Write-Host '❌ 前端服务器: 无响应或异常' }" 2>nul

echo.
echo [3/8] WebSocket连接状态检查...
powershell -Command "try { $status = Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/status' -Method GET -TimeoutSec 5; Write-Host '✅ WebSocket服务: 正常运行'; Write-Host '   活跃连接数:', $status.websocket_status.total_log_connections; Write-Host '   健康状态:', $status.health.is_healthy; Write-Host '   容量使用:', $status.health.capacity_usage } catch { Write-Host '❌ WebSocket服务: 无响应或异常' }" 2>nul

echo.
echo [4/8] 端口占用检查...
echo API端口(8001):
netstat -ano | findstr :8001 | findstr LISTENING
if %errorlevel% == 0 (
    echo ✅ 端口8001正常监听
) else (
    echo ❌ 端口8001未监听
)

echo 前端端口(3001):
netstat -ano | findstr :3001 | findstr LISTENING
if %errorlevel% == 0 (
    echo ✅ 端口3001正常监听
) else (
    echo ❌ 端口3001未监听
)

echo.
echo [5/8] 进程状态检查...
tasklist | findstr python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python进程运行中
    tasklist | findstr python.exe
) else (
    echo ❌ Python进程未运行
)

tasklist | findstr node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Node.js进程运行中
    tasklist | findstr node.exe
) else (
    echo ❌ Node.js进程未运行
)

echo.
echo [6/8] 策略实例状态检查...
powershell -Command "try { $instances = Invoke-RestMethod -Uri 'http://localhost:8001/api/running/instances' -Method GET -TimeoutSec 5; Write-Host '✅ 策略实例查询成功'; Write-Host '   运行实例数:', $instances.instances.Count; foreach($instance in $instances.instances) { Write-Host '   -', $instance.instance_id, '(状态:', $instance.status, ')' } } catch { Write-Host '❌ 无法获取策略实例状态' }" 2>nul

echo.
echo [7/8] 日志系统检查...
if exist "logs\runtime.log" (
    echo ✅ 运行日志文件存在
    powershell -Command "$size = (Get-Item 'logs\runtime.log').Length; Write-Host '   文件大小:', ([math]::Round($size/1024, 2)), 'KB'"
) else (
    echo ❌ 运行日志文件不存在
)

if exist "logs\trade.log" (
    echo ✅ 交易日志文件存在
    powershell -Command "$size = (Get-Item 'logs\trade.log').Length; Write-Host '   文件大小:', ([math]::Round($size/1024, 2)), 'KB'"
) else (
    echo ℹ️  交易日志文件不存在（可能尚未有交易）
)

echo.
echo [8/8] 系统资源检查...
echo CPU和内存使用情况:
powershell -Command "Get-Process | Where-Object {$_.ProcessName -eq 'python' -or $_.ProcessName -eq 'node'} | Format-Table ProcessName, Id, CPU, WorkingSet -AutoSize"

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                        检查完成！                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 配置文件安全检查
echo [配置安全] 检查配置文件安全设置...
echo.
echo 检查 Profiles 目录下的配置文件：
for /r "profiles\" %%f in (*.json) do (
    echo 检查: %%f
    findstr /c:"\"autoTrade\"" "%%f" >nul 2>&1
    if errorlevel 1 (
        echo   ✓ 没有发现 autoTrade 设置 ^(安全^)
    ) else (
        echo   ⚠ 发现 autoTrade 设置，需要清理
    )
    
    if errorlevel 1 (
        echo   ⚠ 没有发现手动启动设置
    ) else (
        echo   ✓ 配置了手动启动 ^(安全^)
    )
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                        检查完成！                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 提供快速操作选项
echo 快速操作:
echo   [1] 重启API服务器
echo   [2] 重启前端服务器  
echo   [3] 清理WebSocket连接
echo   [4] 查看最新日志
echo   [5] 测试WebSocket连接
echo   [0] 退出
echo.

:menu
set /p choice="请选择操作 [0-5]: "

if "%choice%"=="1" (
    echo 正在重启API服务器...
    taskkill /f /im python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    start "股票交易系统-API服务器" cmd /c "title 股票交易系统-API服务器 && apps\api\venv\Scripts\python.exe apps\api\main.py"
    echo ✅ API服务器重启命令已执行
    goto menu
)

if "%choice%"=="2" (
    echo 正在重启前端服务器...
    taskkill /f /im node.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    cd apps\ui
    start "股票交易系统-前端界面" cmd /c "title 股票交易系统-前端界面 && npm run dev"
    cd ..\..
    echo ✅ 前端服务器重启命令已执行
    goto menu
)

if "%choice%"=="3" (
    echo 正在清理WebSocket连接...
    powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/cleanup' -Method POST | Out-Null; Write-Host '✅ WebSocket连接已清理' } catch { Write-Host '❌ 清理失败' }"
    goto menu
)

if "%choice%"=="4" (
    echo 正在显示最新日志...
    if exist "logs\runtime.log" (
        powershell -Command "Get-Content 'logs\runtime.log' | Select-Object -Last 20"
    ) else (
        echo 日志文件不存在
    )
    echo.
    goto menu
)

if "%choice%"=="5" (
    echo 正在打开WebSocket测试页面...
    start http://localhost:8001/websocket-test.html
    goto menu
)

if "%choice%"=="0" (
    exit
)

echo 无效选择，请重新输入
goto menu
    if not errorlevel 1 (
        echo   ✓ require_manual_start 设置为 true ^(安全^)
    ) else (
        findstr /c:"require_manual_start" "%%f" >nul 2>&1
        if not errorlevel 1 (
            echo   ✓ 找到 require_manual_start 设置 ^(安全^)
        ) else (
            echo   ⚠ require_manual_start 未设置
        )
    )
    echo.
)

echo.
echo 2. 检查策略插件配置...

echo.
echo 检查策略插件目录下的配置文件：
for /r "core\strategy\" %%f in (*.json) do (
    echo 检查: %%f
    findstr /c:"\"autoTrade\"" "%%f" >nul 2>&1
    if errorlevel 1 (
        echo   ✓ 没有发现 autoTrade 设置 ^(安全^)
    ) else (
        echo   ⚠ 发现 autoTrade 设置，需要清理
    )
    echo.
)

echo.
echo 3. 检查前端应用状态...
echo 检查前端编译状态：
cd apps\ui
if exist "dist\" (
    echo   ✓ 前端已编译
) else (
    echo   ⚠ 前端未编译，需要运行 npm run build
)

if exist "node_modules\" (
    echo   ✓ 依赖已安装
) else (
    echo   ⚠ 依赖未安装，需要运行 npm install
)

cd ..\..

echo.
echo 4. 检查后端API状态...
echo 检查API依赖：
cd apps\api
if exist "__pycache__\" (
    echo   ✓ Python模块已缓存
) else (
    echo   ⚠ Python模块未缓存，首次运行可能较慢
)

cd ..\..

echo.
echo ========================================
echo           健康检查完成
echo ========================================
pause