@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Activating conda environment: py313
call conda activate py313
if errorlevel 1 (
    echo Failed to activate py313. Please run this script from an Anaconda Prompt.
    exit /b 1
)

echo [2/3] Running self-test
python agnes_gui.py --self-test
if errorlevel 1 exit /b 1

echo [3/3] Building onefile executable
python -m PyInstaller --noconfirm --clean --onefile --windowed --name AgnesModelTester --icon "assets\agnes-agent.ico" --add-data "assets\agnes-agent.png;assets" --add-data "assets\agnes-agent.ico;assets" agnes_gui.py
if errorlevel 1 exit /b 1

echo.
echo Build completed: %CD%\dist\AgnesModelTester.exe
endlocal
