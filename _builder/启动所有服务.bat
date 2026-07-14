@echo off
REM 一键启动所有医疗数据服务，自动等待就绪
chcp 65001 >nul 2>&1
setlocal

echo [1/4] 启动 8765 ICD编码知识库...
start /B "" cmd /c "cd /d "%~dp0" && python3 web/server_gzip.py"
timeout /t 3 /nobreak >nul

echo [2/4] 启动 8766 药品目录...
start /B "" cmd /c "cd /d "%~dp0" && python3 drug/server.py"
timeout /t 8 /nobreak >nul

echo [3/4] 启动 8767 编码转换...
start /B "" cmd /c "cd /d "%~dp0" && python3 code-converter/server.py"
timeout /t 3 /nobreak >nul

echo [4/4] 启动 8768 四方映射...
start /B "" cmd /c "cd /d "%~dp0" && python3 4way-mapping/server.py"
timeout /t 5 /nobreak >nul

echo.
echo 等待服务就绪...
set /a waited=0
:wait_loop
if !waited! GEQ 15 goto :all_ready
curl -s -o nul http://localhost:8765/ >nul 2>&1
curl -s -o nul http://localhost:8766/ >nul 2>&1
curl -s -o nul http://localhost:8767/ >nul 2>&1
curl -s -o nul http://localhost:8768/ >nul 2>&1
timeout /t 2 /nobreak >nul
set /a waited+=2
goto :wait_loop

:all_ready
echo.
echo ========================================
echo   8765  ICD编码知识库  http://localhost:8765
echo   8766  药品目录      http://localhost:8766
echo   8767  编码转换      http://localhost:8767
echo   8768  四方映射      http://localhost:8768
echo ========================================
echo.
echo 全部就绪。关闭此窗口可停止服务。
