@echo off
title Griffiths FRONTEND - ne zakryvayte eto okno!
cd /d "%~dp0\frontend"

if not exist "node_modules" (
    echo Ustanovka zavisimostey...
    call npm install
)

echo.
echo ============================================
echo   FRONTEND: http://localhost:5173
echo   Snachala dolzhen rabotat start-backend.cmd
echo ============================================
echo.

call npm run dev

pause
