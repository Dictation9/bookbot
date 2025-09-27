@echo off
REM Book Bot GUI Windows Launcher Script

REM Get the directory where this script is located and go to parent directory
cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first to set up the environment.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the GUI application
echo Launching Book Bot GUI...
python gui.py

echo GUI closed.
pause
