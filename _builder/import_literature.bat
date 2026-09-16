@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   Literature Import Tool
echo ========================================
echo.
echo 1) Search and import from PubMed (auto)
echo 2) Import local PDF files
echo 3) Show literature stats
echo 4) Export JSON for web
echo 5) Exit
echo.

:menu
set /p choice="Choice (1-5): "
if "%choice%"=="1" goto pubmed
if "%choice%"=="2" goto pdf
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto export
if "%choice%"=="5" goto end
goto menu

:pubmed
set /p query="PubMed search query: "
set /p max="Max results (default 20): "
if "%max%"=="" set max=20
python import_literature.py pubmed --query "%query%" --max %max%
echo.
pause
goto menu

:pdf
set /p dir="Drag and drop PDF folder path: "
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