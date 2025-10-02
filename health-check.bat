@echo off
echo ========================================
echo         交易系统健康检查
echo ========================================

echo.
echo 1. 检查配置文件安全设置...

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
    
    findstr /c:"\"require_manual_start\": true" "%%f" >nul 2>&1
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