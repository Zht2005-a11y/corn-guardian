@echo off
rem corn-guardian one-click launcher
rem   usage: start_all.bat [backend_port]     default 8010
rem   example: start_all.bat 8020    (when 8010 is already taken by another app)

setlocal
cd /d "%~dp0"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8010"

title corn-guardian full stack (API %PORT%)

echo =========================================================
echo   Corn leaf disease decision console - one click launch
echo   [1] Backend API : http://127.0.0.1:%PORT%
echo   [2] Frontend    : http://localhost:5173
echo   [3] API docs    : http://127.0.0.1:%PORT%/docs
echo =========================================================

echo Starting backend on port %PORT% ...
start "corn-guardian-backend-%PORT%" cmd /k run_backend.bat %PORT%

echo Waiting for model warm-up (about 6s) ...
timeout /t 6 /nobreak >nul

echo Starting frontend on port 5173 ...
start "corn-guardian-frontend-5173" cmd /k run_frontend.bat %PORT%

echo Waiting for Vite (about 5s) ...
timeout /t 5 /nobreak >nul

start "" http://localhost:5173
echo All services started.
