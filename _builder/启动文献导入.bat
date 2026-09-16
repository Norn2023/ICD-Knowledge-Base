@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   医学文献导入工具
echo ========================================
echo.
echo 1) PubMed 搜索导入
echo 2) 导入本地 PDF 文件夹
echo 3) 查看文献统计
echo 4) 导出文献 JSON
echo 5) 退出
echo.

:menu
set /p choice="请选择 (1-5): "
if "%choice%"=="1" goto pubmed
if "%choice%"=="2" goto pdf
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto export
if "%choice%"=="5" goto end
goto menu

:pubmed
set /p query="输入 PubMed 搜索词: "
set /p max="最多获取多少篇 (默认20): "
if "%max%"=="" set max=20
python import_literature.py pubmed --query "%query%" --max %max%
echo.
pause
goto menu

:pdf
set /p dir="拖入 PDF 文件夹路径: "
python import_literature.py pdf --dir "%dir%"
echo.
pause
goto menu

:stats
python import_literature.py stats
echo.
pause
goto menu

:export
python import_literature.py export --out ./literature
echo.
pause
goto menu

:end