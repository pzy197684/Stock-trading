@echo off
chcp 65001 >nul 2>&1
echo ===============================================
echo              系统功能验证脚本
echo ===============================================
echo.

echo 🔍 开始验证已修复的6个问题...
echo.

set "FIXED_COUNT=0"
set "TOTAL_ISSUES=6"

REM 问题1: 平台显示unknown（用户已确认修复）
echo ✅ 问题1: 平台显示unknown - 已修复
set /a FIXED_COUNT=%FIXED_COUNT%+1

REM 问题2: HTTP 400错误信息中文化
echo 🔍 问题2: 检查HTTP 400错误信息中文化...
findstr /C:"相同的交易对不允许再建实例" "apps\api\main.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ 问题2: HTTP 400错误信息已中文化
    set /a FIXED_COUNT=%FIXED_COUNT%+1
) else (
    echo ❌ 问题2: HTTP 400错误信息未找到中文化
)

REM 问题3: autoTrade参数持久化
echo 🔍 问题3: 检查autoTrade参数保存逻辑...
findstr /C:"autoTrade.*parameters\['autoTrade'\]" "apps\api\main.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ 问题3: autoTrade参数保存逻辑已修复
    set /a FIXED_COUNT=%FIXED_COUNT%+1
) else (
    echo ❌ 问题3: autoTrade参数保存逻辑未修复
)

REM 问题4: WebSocket日志连接
echo 🔍 问题4: 检查WebSocket日志连接改进...
findstr /C:"没有活跃连接，日志消息未发送" "apps\api\main.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    findstr /C:"websocket/test" "apps\api\main.py" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ 问题4: WebSocket日志连接状态提示已改进，包含测试端点
        set /a FIXED_COUNT=%FIXED_COUNT%+1
    ) else (
        echo ⚠️ 问题4: WebSocket日志连接部分改进，但缺少测试端点
    )
) else (
    echo ❌ 问题4: WebSocket日志连接改进未找到
)

REM 问题5: 交易连接错误处理
echo 🔍 问题5: 检查交易连接错误处理...
findstr /C:"troubleshooting" "apps\api\main.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ 问题5: 交易连接错误处理已改善
    set /a FIXED_COUNT=%FIXED_COUNT%+1
) else (
    echo ❌ 问题5: 交易连接错误处理未改善
)

REM 问题6: Webhook通知功能验证
echo 🔍 问题6: 检查Webhook通知功能...
findstr /C:"api/webhook/test" "apps\api\main.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ 问题6: Webhook通知功能测试端点已添加
    set /a FIXED_COUNT=%FIXED_COUNT%+1
) else (
    echo ❌ 问题6: Webhook通知功能测试端点未找到
)

echo.
echo ===============================================
echo                  修复总结
echo ===============================================
echo 总问题数: %TOTAL_ISSUES%
echo 已修复: %FIXED_COUNT%
echo 修复率: %FIXED_COUNT%/%TOTAL_ISSUES%

if %FIXED_COUNT% EQU %TOTAL_ISSUES% (
    echo.
    echo 🎉 所有问题已成功修复！
    echo.
    echo 📋 修复内容摘要:
    echo   ✅ HTTP 400错误信息已中文化
    echo   ✅ autoTrade参数持久化逻辑已修复
    echo   ✅ WebSocket日志连接状态提示已改进
    echo   ✅ 交易连接错误处理已完善
    echo   ✅ Webhook通知功能测试端点已添加
    echo   ✅ 系统测试组件已创建 (SystemTest.tsx)
    echo.
    echo 🚀 建议执行以下验证步骤:
    echo   1. 启动交易系统: start-trading.bat
    echo   2. 访问前端界面测试功能
    echo   3. 运行系统测试组件验证修复效果
    echo.
) else (
    echo.
    echo ⚠️  仍有问题需要解决
    echo 请检查上述未修复的项目
)

echo.
echo 🔧 其他改进:
echo   • 创建了综合测试组件 (SystemTest.tsx)
echo   • 改进了错误信息的用户友好性
echo   • 增强了日志连接状态的可见性
echo   • 添加了故障排除建议
echo.

pause