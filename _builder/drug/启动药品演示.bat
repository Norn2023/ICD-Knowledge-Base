@echo off
title 医保药物目录演示
echo ===================================
echo   医保药物目录 · 2025版
echo   西药 + 中成药 + 医保审核规则
echo ===================================
echo.
echo 启动服务器...
start http://localhost:8766
python server.py
pause
