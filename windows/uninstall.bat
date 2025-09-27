@echo off
REM Book Bot Uninstall Script for Windows

echo Book Bot Uninstall Script
echo =========================
echo.

REM Get the directory where this script is located and go to parent directory
cd /d "%~dp0\.."

set /p confirm="Are you sure you want to uninstall Book Bot? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Uninstalling Book Bot...

REM Remove Windows Task Scheduler task
echo Removing scheduled tasks...
if exist "windows_task_scheduler.py" (
    python windows_task_scheduler.py remove
)

REM Remove desktop shortcut
echo Removing desktop shortcut...
if exist "%USERPROFILE%\Desktop\Book Bot.lnk" (
    del "%USERPROFILE%\Desktop\Book Bot.lnk"
)

REM Ask if user wants to keep data
echo.
set /p keep_data="Do you want to keep your data (config.ini, book_mentions.csv, logs)? (Y/n): "
if /i "%keep_data%"=="n" (
    echo Removing all data...
    if exist "config.ini" del "config.ini"
    if exist "book_mentions.csv" del "book_mentions.csv"
    if exist "logs" rmdir /s /q "logs"
    if exist "backups" rmdir /s /q "backups"
) else (
    echo Keeping data files...
)

REM Remove virtual environment
echo Removing virtual environment...
if exist "venv" rmdir /s /q "venv"

REM Remove Windows batch files
echo Removing Windows batch files...
if exist "run.bat" del "run.bat"
if exist "run_gui.bat" del "run_gui.bat"
if exist "send_report.bat" del "send_report.bat"
if exist "update.bat" del "update.bat"
if exist "manual_check.bat" del "manual_check.bat"
if exist "install.bat" del "install.bat"
if exist "uninstall.bat" del "uninstall.bat"
if exist "setup_task_scheduler.bat" del "setup_task_scheduler.bat"

REM Remove Windows-specific files
if exist "windows_task_scheduler.py" del "windows_task_scheduler.py"
if exist "requirements-windows.txt" del "requirements-windows.txt"
if exist "README-Windows.md" del "README-Windows.md"

echo.
echo Uninstall complete!
echo.
if /i not "%keep_data%"=="n" (
    echo Your data files have been preserved.
    echo You can delete the entire folder if you want to remove everything.
)
echo.
pause
