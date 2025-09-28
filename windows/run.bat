@echo off
setlocal enabledelayedexpansion
REM Book Bot Windows Launcher Script

REM Get the directory where this script is located and go to parent directory
cd /d "%~dp0\.."

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Generate timestamp for log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

REM Redirect all output to log file
call :main > "logs\cmd_run_%timestamp%.log" 2>&1
goto :eof

:main

echo ========================================
echo Book Bot Windows Run Log
echo Started: %date% %time%
echo ========================================
echo(

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first to set up the environment.
    pause
    exit /b 1
)

REM Check if config.ini exists
if not exist "config.ini" (
    echo ERROR: config.ini not found!
    echo Please copy config.example.ini to config.ini and edit it with your settings.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set console to UTF-8 encoding for proper Unicode support
chcp 65001 >nul

REM Scheduled tasks setup disabled for now
REM if exist "windows\windows_task_scheduler.py" (
REM     echo Setting up scheduled tasks...
REM     python windows\windows_task_scheduler.py
REM )

echo(
echo Book Bot - Windows Version
echo =========================
echo(
echo DEBUG: About to read config file...

REM Read schedule from config.ini
echo DEBUG: Reading schedule from config.ini...
set "SCHEDULE="
echo DEBUG: About to read config.ini line by line...
for /f "usebackq tokens=1,2 delims==" %%a in ("config.ini") do (
    echo DEBUG: Processing line: %%a=%%b
    if /i "%%a"=="double_check_times" (
        echo DEBUG: Found double_check_times, setting SCHEDULE to: %%b
        set "SCHEDULE=%%b"
        goto :schedule_found
    )
)
:schedule_found
echo DEBUG: SCHEDULE variable is now: !SCHEDULE!
if defined SCHEDULE (
    set "SCHEDULE=!SCHEDULE: =!"
    echo DEBUG: After trimming spaces: !SCHEDULE!
    if "!SCHEDULE!"=="" (
        echo No schedule found in config.ini (double_check_times is empty).
    ) else (
        echo Automated tasks are scheduled to run at: !SCHEDULE!
    )
) else (
    echo No schedule found in config.ini (double_check_times is empty).
)

echo(
echo DEBUG: Config reading completed successfully.
echo The bot will now perform a one-time scan of the subreddit.
echo DEBUG: About to prompt user for input...
set /p user_input="Type 'start' and press Enter to begin: "
echo DEBUG: User input received: !user_input!

echo DEBUG: Checking user input...
if not "!user_input!"=="start" (
    echo DEBUG: User input was not 'start', aborting...
    echo Aborted by user. Exiting.
    pause
    exit /b 0
)
echo DEBUG: User input was 'start', continuing...

REM Backup config.ini if it exists
if exist "config.ini" (
    copy "config.ini" "config.ini.bak" >nul
)

REM Run the main bot
echo(
echo Starting bot...
python bookbot.py

REM Restore config.ini if it was overwritten
if exist "config.ini.bak" (
    move "config.ini.bak" "config.ini" >nul
)

echo(
echo Bot run finished.
echo(
echo All output has been logged to: logs\cmd_run_%timestamp%.log
echo(
echo Press any key to view the log file, or close this window to exit.
pause >nul
type "logs\cmd_run_%timestamp%.log"
echo(
echo Press any key to exit.
pause >nul
