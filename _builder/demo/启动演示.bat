@echo off
title DIP 分值库演示
echo ===================================
echo   DIP 2.0 病种分值库演示
echo   国家 + 广东梅州 + 福建厦门 + 江苏连云港
echo ===================================
echo.
echo 启动服务器...
start http://localhost:8765
python server_gzip.py
pause
