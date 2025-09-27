@echo off
REM Book Bot Send Report Windows Script

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

REM Run the email report script
echo Sending full report...
python email_handlers\send_full_report.py

echo Report sent.
pause
