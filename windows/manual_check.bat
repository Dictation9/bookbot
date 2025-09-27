@echo off
REM Book Bot Manual Check Windows Script
REM Manually check book_mentions.csv for LGBT books and output a summary CSV with an 'is_lgbt' column.

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

REM Check if input file exists
if not exist "book_mentions.csv" (
    echo ERROR: book_mentions.csv not found!
    echo Please run the bot first to generate data.
    pause
    exit /b 1
)

echo Running manual check for LGBT books...
echo.

REM Run the manual enrichment script
python manual_enrich.py

echo.
echo Manual check complete!
pause
