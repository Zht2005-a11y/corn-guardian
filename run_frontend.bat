@echo off
rem corn-guardian frontend
rem   usage: run_frontend.bat [backend_port]     default 8010

setlocal
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8010"
set "VITE_API_TARGET=http://127.0.0.1:%PORT%"

title corn-guardian frontend (Port: 5173)

echo =======================================================
echo   Corn leaf disease decision console - frontend
echo   URL       : http://localhost:5173
echo   API proxy : %VITE_API_TARGET%
echo =======================================================

cd /d "%~dp0frontend"
call npm run dev
pause
