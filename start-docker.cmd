@echo off
title Griffiths — Docker Compose
cd /d "%~dp0"

if not exist ".env" (
    echo Net fajla .env — kopiruyu iz .env.example
    copy /Y ".env.example" ".env" >nul
    echo Zapolnite .env ^(JWT_SECRET, NORDROUTER_API_KEY i dr.^) i zapustite snova.
    pause
    exit /b 1
)

where docker >nul 2>&1
if errorlevel 1 (
    echo Oshibka: Docker ne najden. Ustanovite Docker Desktop.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Griffiths — docker compose up --build
echo   Sajt:    http://localhost:5173
echo   API:     http://localhost:8080/health
echo   Docs:    http://localhost:8080/docs
echo   Ostanovka: Ctrl+C, zatem docker compose down
echo ============================================
echo.

docker compose up --build

pause
