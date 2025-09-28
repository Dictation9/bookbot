@echo off
setlocal enabledelayedexpansion
echo Testing config reading...

echo DEBUG: About to read config.ini line by line...
for /f "usebackq tokens=1,2 delims==" %%a in ("config.ini") do (
    echo DEBUG: Processing line: %%a=%%b
    if /i "%%a"=="double_check_times" (
        echo DEBUG: Found double_check_times, value is: %%b
        set "SCHEDULE=%%b"
    )
)

echo DEBUG: Final SCHEDULE value: !SCHEDULE!
if defined SCHEDULE (
    echo Schedule is defined: !SCHEDULE!
) else (
    echo Schedule is not defined
)

echo Test completed successfully.
pause
