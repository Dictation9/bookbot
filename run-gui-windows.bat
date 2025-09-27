@echo off
REM Book Bot Windows GUI Launcher
REM This script launches the Windows GUI version of Book Bot

echo Book Bot Windows GUI Launcher
echo =============================
echo(

REM Check if windows folder exists
if not exist "windows" (
    echo ERROR: Windows installation files not found!
    echo Please run install-windows.bat first to set up the Windows version.
    pause
    exit /b 1
)

REM Launch the Windows GUI script
call windows\run_gui.bat
