@echo off
REM Book Bot Windows Installation Launcher
REM This script launches the Windows installation from the windows/ folder

echo Book Bot Windows Installation
echo =============================
echo(

REM Check if windows folder exists
if not exist "windows" (
    echo ERROR: Windows installation files not found!
    echo Please make sure you're in the Book Bot directory and the windows/ folder exists.
    pause
    exit /b 1
)

REM Launch the Windows installation script
echo Starting Windows installation...
call windows\install.bat
