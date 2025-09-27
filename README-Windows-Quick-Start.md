# 📚 Book Bot - Windows 11 Quick Start Guide

This is a quick start guide for running Book Bot on Windows 11. All Windows-specific components are organized in the `windows/` folder.

## 🚀 Quick Installation

1. **Prerequisites**: Make sure you have Python 3.8+ and Git installed
2. **Install**: Double-click `install-windows.bat` or run it from Command Prompt
3. **Configure**: Edit `config.ini` with your Reddit API and email credentials
4. **Run**: Use `run-gui-windows.bat` for the GUI or `run-windows.bat` for command line

## 📁 Windows Components

All Windows-specific files are in the `windows/` folder:

- **`windows/install.bat`** - Main Windows installation script
- **`windows/run.bat`** - Command line launcher
- **`windows/run_gui.bat`** - GUI launcher
- **`windows/send_report.bat`** - Email report sender
- **`windows/update.bat`** - Update script
- **`windows/uninstall.bat`** - Uninstall script
- **`windows/windows_task_scheduler.py`** - Task Scheduler integration
- **`windows/README-Windows.md`** - Full Windows documentation

## 🎯 Easy Access

For convenience, these launcher scripts are in the root directory:

- **`install-windows.bat`** - Launches Windows installation
- **`run-windows.bat`** - Launches Windows command line version
- **`run-gui-windows.bat`** - Launches Windows GUI version

## 📖 Full Documentation

For complete Windows documentation, see: `windows/README-Windows.md`

## 🔧 What's Different on Windows

- Uses Windows Task Scheduler instead of cron
- Windows batch files (`.bat`) instead of shell scripts (`.sh`)
- Windows-specific paths and file handling
- No Raspberry Pi GPIO dependencies
- Desktop shortcuts for easy access

## 🆘 Troubleshooting

If you encounter issues:

1. Run `windows/test_windows_install.bat` to verify your installation
2. Check `windows/README-Windows.md` for detailed troubleshooting
3. Make sure you're running as Administrator for Task Scheduler setup

## 🎉 Ready to Go!

Once installed, you can:
- Double-click the "Book Bot" desktop shortcut
- Use `run-gui-windows.bat` for the modern GUI interface
- Use `run-windows.bat` for command line operation
- Configure scheduled tasks through the GUI or `config.ini`
