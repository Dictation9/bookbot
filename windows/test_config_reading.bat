@echo off
setlocal enabledelayedexpansion
echo Testing config reading...

REM Read debug setting from config.ini
set "DEBUG_MODE=false"
for /f "usebackq tokens=1,2 delims==" %%a in ("config.ini") do (
    if /i "%%a"=="debug" (
        set "DEBUG_MODE=%%b"
        set "DEBUG_MODE=!DEBUG_MODE: =!"
    )
)

echo Debug mode is: !DEBUG_MODE!

if /i "!DEBUG_MODE!"=="true" (
    echo DEBUG: About to read config.ini line by line...
    for /f "usebackq tokens=1,2 delims==" %%a in ("config.ini") do (
        echo DEBUG: Processing line: %%a=%%b
        if /i "%%a"=="double_check_times" (
            echo DEBUG: Found double_check_times, value is: %%b
            set "SCHEDULE=%%b"
        )
    )
    echo DEBUG: Final SCHEDULE value: !SCHEDULE!
)

echo Test completed successfully.
pause
