@echo off
title Griffiths BACKEND - ne zakryvayte eto okno!
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Oshibka: net papki .venv. Snachala: pip install -r requirements.txt
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo.
echo ============================================
echo   BACKEND zapuskaetsya na portu 8080
echo   NE ZAKRYVAYTE eto okno!
echo   Proverka: http://localhost:8080/health
echo ============================================
echo.

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8080

echo.
echo Backend ostanovlen. Nazhmite lyubuyu klavishu...
pause >nul
