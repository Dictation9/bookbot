@echo off
REM Book Bot Windows Installation Test Script

echo Book Bot Windows Installation Test
echo ==================================
echo.

REM Get the directory where this script is located and go to parent directory
cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Check if config.ini exists
if not exist "config.ini" (
    echo ❌ config.ini not found!
    echo Please copy config.example.ini to config.ini and edit it.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo ✅ Virtual environment found
echo ✅ Configuration file found
echo.

REM Test Python imports
echo Testing Python dependencies...
python -c "import praw, requests, rich, beautifulsoup4, customtkinter, atproto, flask, psutil; print('✅ All dependencies imported successfully')" 2>nul
if errorlevel 1 (
    echo ❌ Some dependencies are missing!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Test if gpiozero is NOT installed (should be removed for Windows)
python -c "import gpiozero" 2>nul
if not errorlevel 1 (
    echo ⚠️  WARNING: gpiozero is still installed (Raspberry Pi specific)
    echo This may cause issues on Windows. Consider running: pip uninstall gpiozero -y
)

REM Test Windows Task Scheduler integration - DISABLED
REM if exist "windows_task_scheduler.py" (
REM     echo ✅ Windows Task Scheduler integration found
REM ) else (
REM     echo ❌ Windows Task Scheduler integration not found!
REM )

REM Test batch files
if exist "run.bat" (
    echo ✅ run.bat found
) else (
    echo ❌ run.bat not found!
)

if exist "run_gui.bat" (
    echo ✅ run_gui.bat found
) else (
    echo ❌ run_gui.bat not found!
)

if exist "send_report.bat" (
    echo ✅ send_report.bat found
) else (
    echo ❌ send_report.bat not found!
)

REM Test desktop shortcut
if exist "%USERPROFILE%\Desktop\Book Bot.lnk" (
    echo ✅ Desktop shortcut found
) else (
    echo ⚠️  Desktop shortcut not found
)

echo.
echo Test complete!
echo.
echo If all items show ✅, your Windows installation is ready!
echo If you see ❌ or ⚠️, please address those issues before running the bot.
echo.
pause
