"""
Windows Task Scheduler integration for Book Bot
Replaces the Unix cron functionality with Windows Task Scheduler
"""

import os
import subprocess
import configparser
import tempfile
from pathlib import Path

def setup_windows_scheduler():
    """
    Set up Windows Task Scheduler to run scheduled_check.py
    """
    try:
        # Read config to get schedule
        config = configparser.ConfigParser()
        config_path = "config.ini"
        if not os.path.exists(config_path):
            print(f"❌ {config_path} is missing.")
            return False
        
        config.read(config_path)
        schedule = config.get('general', 'double_check_times', fallback='').strip()
        
        if not schedule:
            print("No schedule found in config.ini (double_check_times is empty).")
            return True
        
        # Get current directory and Python executable
        current_dir = os.getcwd()
        python_exe = os.path.join(current_dir, "venv", "Scripts", "python.exe")
        script_path = os.path.join(current_dir, "scheduled_check.py")
        
        if not os.path.exists(python_exe):
            print(f"❌ Python executable not found: {python_exe}")
            return False
        
        if not os.path.exists(script_path):
            print(f"❌ Scheduled check script not found: {script_path}")
            return False
        
        # Create PowerShell script to set up the task
        ps_script = f"""
$taskName = "BookBot Scheduled Tasks"
$taskDescription = "Runs Book Bot scheduled tasks for data enrichment and reporting"
$scriptPath = "{script_path}"
$pythonPath = "{python_exe}"

# Remove existing task if it exists
try {{
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
}} catch {{}}

# Create the action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`""

# Create triggers based on schedule
$triggers = @()

# Parse schedule - support both HH:MM format and cron format
if ("$schedule" -match ":") {{
    # HH:MM format (comma-separated times)
    $times = "$schedule" -split ","
    foreach ($time in $times) {{
        $time = $time.Trim()
        if ($time -match "^(\d{{1,2}}):(\d{{2}})$") {{
            $hour = [int]$matches[1]
            $minute = [int]$matches[2]
            $trigger = New-ScheduledTaskTrigger -Daily -At $hour:$minute
            $triggers += $trigger
        }}
    }}
}} else {{
    # Standard cron format - convert to daily at 9:00 AM for now
    # TODO: Implement full cron parsing
    $trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
    $triggers += $trigger
}}

# Create the principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType InteractiveToken

# Create the settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description $taskDescription

Write-Host "Task Scheduler setup complete!"
Write-Host "Task name: $taskName"
Write-Host "Schedule: $schedule"
"""
        
        # Write PowerShell script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(ps_script)
            ps_file = f.name
        
        try:
            # Run PowerShell script
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_file
            ], capture_output=True, text=True, cwd=current_dir)
            
            if result.returncode == 0:
                print("✅ Windows Task Scheduler setup complete!")
                print(f"Task name: BookBot Scheduled Tasks")
                print(f"Schedule: {schedule}")
                return True
            else:
                print(f"❌ Failed to set up Task Scheduler: {result.stderr}")
                return False
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(ps_file)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error setting up Windows Task Scheduler: {e}")
        return False

def remove_windows_scheduler():
    """
    Remove the Windows Task Scheduler task
    """
    try:
        ps_script = """
$taskName = "BookBot Scheduled Tasks"
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Task Scheduler task removed successfully!"
} catch {
    Write-Host "No task found to remove or error occurred: $_"
}
"""
        
        # Write PowerShell script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(ps_script)
            ps_file = f.name
        
        try:
            # Run PowerShell script
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Windows Task Scheduler task removed!")
                return True
            else:
                print(f"❌ Failed to remove Task Scheduler task: {result.stderr}")
                return False
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(ps_file)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error removing Windows Task Scheduler task: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "remove":
        remove_windows_scheduler()
    else:
        setup_windows_scheduler()
