@echo off
setlocal
cd /d "%~dp0"
call conda activate py313
if errorlevel 1 (
    echo Failed to activate py313. Please run this script from an Anaconda Prompt.
    exit /b 1
)
python agnes_gui.py
endlocal
