@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=python"
python -c "import torch" >nul 2>&1
if errorlevel 1 (
    if exist "D:\Anaconda3\envs\corn\python.exe" (
        set "PY=D:\Anaconda3\envs\corn\python.exe"
    ) else (
        echo [ERROR] No Python with torch found on this machine.
        echo Please activate your conda env first, for example:
        echo     conda activate corn
        echo     python -m uvicorn app.api:app --host 127.0.0.1 --port 8010
        pause
        exit /b 1
    )
)

echo Starting corn disease recognition service
echo Swagger UI : http://127.0.0.1:8010/docs
echo Home page  : http://127.0.0.1:8010/
"%PY%" -X utf8 -m uvicorn app.api:app --host 127.0.0.1 --port 8010
pause
