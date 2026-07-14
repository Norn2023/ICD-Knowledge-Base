@echo off
echo ========================================
echo   Codex Obsi 知识库服务启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 启动 ICD编码知识库 (8765)...
start "ICD-DIP-Web" cmd /c "cd /d _builder\web && python server_gzip.py"
echo        http://localhost:8765

echo [2/3] 启动 医保药物目录 (8766)...
start "Drug-Directory" cmd /c "cd /d _builder\drug && python server.py"
echo        http://localhost:8766

echo [3/3] 启动 价格立项指南映射 (8768)...
start "4Way-Mapping" cmd /c "cd /d _builder\4way-mapping && python server.py"
echo        http://localhost:8768

echo.
echo ========================================
echo   全部启动完成！按任意键关闭此窗口
echo ========================================
pause >nul
