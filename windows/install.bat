@echo off
echo Installing Book Bot for Windows...
echo.
echo Current directory: %CD%
echo.

REM Check if Python is installed (try multiple commands)
echo Checking for Python installation...
python --version >nul 2>&1
if not errorlevel 1 (
    echo Found Python: 
    python --version
    set PYTHON_CMD=python
    goto :python_found
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    echo Found Python3: 
    python3 --version
    set PYTHON_CMD=python3
    goto :python_found
)

py --version >nul 2>&1
if not errorlevel 1 (
    echo Found py launcher: 
    py --version
    set PYTHON_CMD=py
    goto :python_found
)

echo ERROR: Python is not installed or not in PATH
echo Please install Python 3.8+ from https://python.org
echo Make sure to check "Add Python to PATH" during installation
pause
exit /b 1

:python_found

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com
    pause
    exit /b 1
)

REM Clone or update the repository
if exist "..\bookbot" (
    echo Updating existing Book Bot installation...
    cd ..
    git pull origin main
) else (
    echo Cloning Book Bot repository...
    cd ..
    git clone https://github.com/Dictation9/bookbot
    cd bookbot
)

REM Create virtual environment
echo Creating Python virtual environment...
%PYTHON_CMD% -m venv venv

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

REM Remove gpiozero from requirements for Windows compatibility
pip uninstall gpiozero -y

REM Create Windows batch files
echo Creating Windows batch files...

REM Create Windows batch files in the windows directory
echo Creating Windows batch files...

REM Create run.bat
echo @echo off > windows\run.bat
echo cd /d "%%~dp0\.." >> windows\run.bat
echo call venv\Scripts\activate.bat >> windows\run.bat
echo python bookbot.py >> windows\run.bat
echo pause >> windows\run.bat

REM Create run_gui.bat
echo @echo off > windows\run_gui.bat
echo cd /d "%%~dp0\.." >> windows\run_gui.bat
echo call venv\Scripts\activate.bat >> windows\run_gui.bat
echo python gui.py >> windows\run_gui.bat
echo pause >> windows\run_gui.bat

REM Create send_report.bat
echo @echo off > windows\send_report.bat
echo cd /d "%%~dp0\.." >> windows\send_report.bat
echo call venv\Scripts\activate.bat >> windows\send_report.bat
echo python email_handlers\send_full_report.py >> windows\send_report.bat
echo pause >> windows\send_report.bat

REM Create update.bat
echo @echo off > windows\update.bat
echo cd /d "%%~dp0\.." >> windows\update.bat
echo call venv\Scripts\activate.bat >> windows\update.bat
echo git pull origin main >> windows\update.bat
echo pip install -r requirements.txt --upgrade >> windows\update.bat
echo pip uninstall gpiozero -y >> windows\update.bat
echo echo Update complete! >> windows\update.bat
echo pause >> windows\update.bat

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Book Bot.lnk'); $Shortcut.TargetPath = '%CD%\windows\run_gui.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'Book Bot GUI'; $Shortcut.Save()"

REM Setup Windows Task Scheduler
echo Setting up Windows Task Scheduler...
%PYTHON_CMD% windows\windows_task_scheduler.py

echo.
echo Installation complete!
echo.
echo You can now run the bot using:
echo   - windows\run.bat (command line interface)
echo   - windows\run_gui.bat (graphical user interface)
echo   - Double-click the "Book Bot" icon on your desktop
echo.
echo IMPORTANT: Edit config.ini to add your Reddit API and email credentials.
echo.
pause
