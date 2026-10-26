@echo off
rem corn-guardian backend
rem   usage: run_backend.bat [port]      default port 8010

setlocal
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8010"

title corn-guardian backend (Port: %PORT%)

echo =======================================================
echo   Corn leaf disease recognition system - backend
echo   API   : http://127.0.0.1:%PORT%
echo   Swagger: http://127.0.0.1:%PORT%/docs
echo =======================================================

rem Prefer the original conda env, fall back to the local bundled Python.
set "PYEXE=D:\anaconda\envs\torch_gpu\python.exe"
if not exist "%PYEXE%" set "PYEXE=C:\Users\xu\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
echo Python: %PYEXE%
echo Port  : %PORT%

cd /d "%~dp0model\corn_disease_system_20261021"
"%PYEXE%" -m uvicorn app.api:app --host 127.0.0.1 --port %PORT%
pause
