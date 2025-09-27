@echo off
REM Book Bot Update Script for Windows

REM Get the directory where this script is located and go to parent directory
cd /d "%~dp0\.."

echo Book Bot Update Script
echo =====================
echo.

REM Check if we're in a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo ERROR: Not a git repository!
    echo Please make sure you're in the Book Bot directory.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first to set up the environment.
    pause
    exit /b 1
)

echo Updating Book Bot...
echo.

REM Backup important files
echo Creating backup of current configuration...
if not exist "backups" mkdir backups
set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
if exist "config.ini" copy "config.ini" "backups\config_%timestamp%.ini" >nul

REM Update from git
echo Pulling latest changes from repository...
git pull origin main

REM Activate virtual environment and update dependencies
echo Updating Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt --upgrade

REM Remove gpiozero for Windows compatibility
pip uninstall gpiozero -y

echo.
echo Update complete!
echo Your configuration has been backed up to: backups\config_%timestamp%.ini
echo.
pause
