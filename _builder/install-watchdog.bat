@echo off
chcp 65001 >nul
title 安装服务看门狗 - 开机自启
cd /d "%~dp0"

echo ========================================
echo   ICD 知识库服务看门狗 - 安装向导
echo ========================================
echo.

:: ── 1. 创建启动脚本（避免 PowerShell 执行策略限制） ──
set "VBS=%TEMP%\start_watchdog.vbs"
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS%"
echo WshShell.Run "python """%~dp0watchdog.py"" --daemon", 0, False >> "%VBS%"
echo Set WshShell = Nothing >> "%VBS%"
echo WshShell = "" >> "%VBS%"

:: ── 2. 添加到「启动」文件夹 ──
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /Y "%VBS%" "%STARTUP%\ICD知识库看门狗.vbs" >nul
echo [1/3] ✅ 已添加到「启动」文件夹

:: ── 3. 可选：添加到任务计划程序（更可靠） ──
schtasks /Create /SC ONLOGON /TN "ICD-KB-Watchdog" /TR "wscript.exe \"%STARTUP%\ICD知识库看门狗.vbs\"" /F /DELAY 0000:30 >nul 2>&1
echo [2/3] ✅ 已添加到任务计划程序（开机登录后30秒启动）

:: ── 4. 立即启动看门狗 ──
echo [3/3] 🔄 正在启动看门狗...
wscript.exe "%VBS%"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   ✅ 安装完成！
echo.
echo   看门狗已在后台运行。
echo   下次开机时将自动启动所有服务。
echo.
echo   日志文件：%~dp0logs\watchdog.log
echo ========================================
echo.
pause
