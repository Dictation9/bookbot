# Book Bot Windows PowerShell Installation Script
# Run this script with: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [switch]$Force
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "Installing Book Bot for Windows..." -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as administrator. Some features may not work properly." -ForegroundColor Yellow
    Write-Host "Consider running PowerShell as Administrator for full functionality." -ForegroundColor Yellow
    Write-Host ""
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Git is installed
try {
    $gitVersion = git --version 2>&1
    Write-Host "Found Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Clone or update the repository
$repoPath = "..\bookbot"
if (Test-Path $repoPath) {
    Write-Host "Updating existing Book Bot installation..." -ForegroundColor Yellow
    Set-Location ..
    git pull origin main
} else {
    Write-Host "Cloning Book Bot repository..." -ForegroundColor Yellow
    Set-Location ..
    git clone https://github.com/Dictation9/bookbot
    Set-Location bookbot
}

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r requirements.txt

# Remove gpiozero for Windows compatibility
Write-Host "Removing Raspberry Pi specific dependencies..." -ForegroundColor Yellow
pip uninstall gpiozero -y

# Create Windows batch files
Write-Host "Creating Windows batch files..." -ForegroundColor Yellow

# Create run.bat
@"
@echo off
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
python bookbot.py
pause
"@ | Out-File -FilePath "windows\run.bat" -Encoding ASCII

# Create run_gui.bat
@"
@echo off
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
python gui.py
pause
"@ | Out-File -FilePath "windows\run_gui.bat" -Encoding ASCII

# Create send_report.bat
@"
@echo off
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
python email_handlers\send_full_report.py
pause
"@ | Out-File -FilePath "windows\send_report.bat" -Encoding ASCII

# Create update.bat
@"
@echo off
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
git pull origin main
pip install -r requirements.txt --upgrade
pip uninstall gpiozero -y
echo Update complete!
pause
"@ | Out-File -FilePath "windows\update.bat" -Encoding ASCII

# Create desktop shortcut
Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Book Bot.lnk")
$Shortcut.TargetPath = "$PWD\windows\run_gui.bat"
$Shortcut.WorkingDirectory = $PWD
$Shortcut.Description = "Book Bot GUI"
$Shortcut.Save()

# Setup Windows Task Scheduler - DISABLED
# Write-Host "Setting up Windows Task Scheduler..." -ForegroundColor Yellow
# if (Test-Path "windows\windows_task_scheduler.py") {
#     python windows\windows_task_scheduler.py
# } else {
#     Write-Host "WARNING: windows\windows_task_scheduler.py not found. Skipping Task Scheduler setup." -ForegroundColor Yellow
# }

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run the bot using:" -ForegroundColor Cyan
Write-Host "  - windows\run.bat (command line interface)" -ForegroundColor White
Write-Host "  - windows\run_gui.bat (graphical user interface)" -ForegroundColor White
Write-Host "  - Double-click the 'Book Bot' icon on your desktop" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Edit config.ini to add your Reddit API and email credentials." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
