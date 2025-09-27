# 📚 Book Bot - Windows 11 Edition

A modular and configurable Reddit bot that scans subreddits for book mentions, enriches the data using various web APIs, and provides robust logging and reporting. This version has been adapted to work on Windows 11.

## ✨ Core Concepts

This bot operates in two primary modes:

1. **Manual Scan (`run.bat`):** When you execute `run.bat`, the bot performs a single, immediate scan of the target subreddit based on your `config.ini` settings. This script will also set up or update the Windows Task Scheduler tasks, ensuring your scheduled jobs always match your config.
2. **Scheduled Tasks (`scheduled_check.py`):** This script is designed to be run automatically by Windows Task Scheduler. It handles all recurring maintenance tasks:
   * **Data Enrichment:** Re-scans the CSV to find and fill in any missing book information.
   * **Email Reporting:** Sends the CSV data and log files via email.
   * **Storage Monitoring:** Checks disk space and sends an alert if it's running low.
   * **Auto-Updating:** Pulls the latest version from Git to keep the bot current.

Running `run.bat` is the primary way to interact with the bot, as it handles both manual scans and the configuration of these automated background tasks.

## 🖥️ Graphical User Interface

The bot includes a modern GUI built with CustomTkinter that provides:

- **Dashboard:** Run manual scans, send reports, and view live log output
- **Configuration Editor:** Edit all settings from `config.ini` through a user-friendly form
- **CSV Viewer:** Browse and search your collected book data in a table format
- **Log Viewer:** View bot activity logs directly in the application

### Running the GUI

```cmd
run_gui.bat
```

Or simply double-click the "Book Bot" icon on your desktop (after installation).

## 🛠️ Installation

### Prerequisites

Before installing Book Bot, make sure you have:

1. **Python 3.8 or higher** - Download from [python.org](https://python.org)
2. **Git** - Download from [git-scm.com](https://git-scm.com)
3. **Windows 11** (or Windows 10)

### Quick Install

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to where you want to install Book Bot
3. Run the installation script:

```cmd
curl -sSL https://raw.githubusercontent.com/Dictation9/bookbot/main/install.bat | cmd
```

Or download and run `install.bat` directly.

### Manual Installation

1. Clone the repository:
```cmd
git clone https://github.com/Dictation9/bookbot
cd bookbot
```

2. Run the installer:
```cmd
install.bat
```

The installer will:
- Create a Python virtual environment
- Install all dependencies (excluding Raspberry Pi specific ones)
- Create Windows batch files for easy execution
- Set up Windows Task Scheduler
- Create a desktop shortcut

After installation, you **must** edit the `config.ini` file to add your Reddit API and email credentials.

## ⚙️ Configuration (`config.ini`)

All bot settings are managed in `config.ini`.

```ini
[reddit]
client_id = your_client_id
client_secret = your_client_secret
user_agent = bookbot
# Subreddit(s) to scan. For multiple, use a comma-separated list (e.g., subreddit1,subreddit2).
subreddit = lgbtbooks,mm_RomanceBooks
# Set to None to fetch all posts/comments
limit = 10 

[email]
from = your_email@gmail.com
to = your_email@gmail.com
password = your_app_password
smtp_server = smtp.gmail.com
smtp_port = 587
send_csv_email = true 

[general]
delete_csv_on_start = false
double_check_csv_on_run = false
double_check_mode = missing
double_check_times = 09:00,12:00,18:00
storage_warn_percent = 80
storage_critical_percent = 90
# Path to monitor for disk usage. Default is "C:\", the main drive.
storage_path_to_check = C:\
```

### Configuration Notes for Windows

- **`storage_path_to_check`**: Use Windows paths like `C:\` instead of Unix paths like `/`
- **`double_check_times`**: Supports both HH:MM format (e.g., `09:00,12:00,18:00`) and standard cron format
- **Email**: For Gmail, you'll need to use an "App Password" instead of your regular password

## 📝 Usage

### Command Line Interface

#### Performing a One-Off Scan

This will run the bot once and update the Windows Task Scheduler based on your `config.ini`.

```cmd
run.bat
```

#### Automated Scheduling

The scheduled tasks are managed by Windows Task Scheduler. When you run `run.bat`, the script reads the `double_check_times` from your `config.ini` and automatically creates the necessary scheduled tasks. You can change the schedule at any time by editing the config file and re-running `run.bat`.

#### Manually Sending a Full Report

If you want an immediate email report with the CSV and all log files, you can run:

```cmd
send_report.bat
```

This script will automatically split large log files into multiple emails to avoid attachment size limits.

### Graphical User Interface

Launch the GUI for a more user-friendly experience:

```cmd
run_gui.bat
```

The GUI provides:
- **One-click scanning** with live progress updates
- **Easy configuration editing** without touching text files
- **Real-time log viewing** to monitor bot activity
- **CSV data browsing** with search and sort capabilities

## 🔄 Updating

To update the bot to the latest version from GitHub without losing your configuration:

```cmd
update.bat
```

This script pulls the latest code, restores your `config.ini`, and runs `pip install --upgrade` to ensure any new dependencies are added efficiently.

## 📂 File Structure

* `bookbot.py`: The main application entry point for manual scans.
* `scheduled_check.py`: The script executed by Windows Task Scheduler for all automated tasks.
* `run.bat`: The recommended script for running the bot and setting up scheduled tasks.
* `run_gui.bat`: Launches the graphical user interface.
* `gui.py`: The main GUI application code.
* `install.bat`: The initial installation script.
* `windows_task_scheduler.py`: Windows Task Scheduler integration.
* `config.ini`: Your private configuration and API keys.
* `book_mentions.csv`: The master CSV where all collected data is stored.
* `logs/`: Contains `bot.log` (activity log), `comment_data.log` (raw comment data for debugging), and `cron.log` (output from scheduled tasks).
* `handlers/`: Contains the logic for parsing different comment formats and for fetching data from web sources.
* `email_handlers/`: Contains all scripts related to sending emails, including the utility for splitting large files.

## 🛠️ Troubleshooting

- **`ValueError: invalid literal for int()`:** You likely have an inline comment (`#`) in your `config.ini` on the same line as a value. All comments must be on their own line.
- **Authentication Errors:** Double-check all credentials in `config.ini`. Ensure you are using an "App Password" for your email if using Gmail.
- **Task Scheduler Not Running:**
  - Open Windows Task Scheduler and look for "BookBot Scheduled Tasks"
  - Check `logs/cron.log` for any error messages from the scheduled runs
  - Make sure the task is enabled and the schedule is correct
- **Permission Denied:** Run Command Prompt as Administrator when installing or setting up scheduled tasks
- **GUI Not Starting:** Make sure `customtkinter` is installed by running `pip install customtkinter` in your virtual environment
- **Desktop Shortcut Not Working:** Verify the path in the shortcut matches your actual installation directory

## 🆚 Windows vs Linux Differences

### What's Different on Windows

1. **Scheduling**: Uses Windows Task Scheduler instead of cron
2. **File Paths**: Uses Windows path separators (`\` instead of `/`)
3. **Scripts**: Uses `.bat` files instead of `.sh` scripts
4. **GPIO**: Raspberry Pi GPIO functionality is disabled (not available on Windows)
5. **System Monitoring**: Limited system temperature/fan monitoring (Windows doesn't expose this like Linux)

### What's the Same

- All core bot functionality (Reddit scanning, book enrichment, email reporting)
- GUI interface and features
- Configuration system
- CSV data storage and processing
- Email handlers and reporting

## 🛡️ License

MIT License

## 🧩 Modular Bot Handlers

The bot uses a modular structure for handling different Reddit bots. Each bot handler is in its own file, making it easy to add, update, or test support for new bots.

### Adding a New Bot Handler

1. **Copy the template:**
   - Use `bot_handler_template.py` as a starting point for your new bot handler.
2. **Implement detection and handling:**
   - Implement `is_<yourbot>_bot(comment)` and `handle_<yourbot>_bot_comment(comment, seen)` in your new file.
3. **Register the handler in `bookbot.py`:**
   - Import your handler and add it to the `process_comments` logic.

## 🦋 Bluesky Scanning (Optional)

Book Bot can also scan the Bluesky social network for book mentions, in addition to Reddit.

### Enabling Bluesky Scanning

1. Open your `config.ini` file and add or edit the `[bluesky]` section:

```ini
[bluesky]
# Bluesky username (handle)
username = yourname.bsky.social
# Bluesky app password (see Bluesky settings)
app_password = your_app_password
# Comma-separated list of Bluesky feeds to scan (e.g., feed1,feed2). Leave blank to scan the home timeline.
feeds = 
# Optionally, scan for posts containing these hashtags (comma-separated, without #). If feeds are blank, this will be used.
hashtags = 
# Set to true to enable Bluesky scanning
scan_enabled = true
```

- You must create an [App Password](https://bsky.app/settings/app-passwords) in your Bluesky account settings.
- You can scan specific feeds, or leave `feeds` blank and specify hashtags to search for.

### How It Works

- When enabled, Book Bot will scan Bluesky for posts mentioning books in the format `{Title by Author}`.
- Book mentions are enriched and added to the same `book_mentions.csv` as Reddit results (no duplicates).
- The scan can be run from the command line or from the GUI.

### Using the GUI Bluesky Dashboard

- The GUI includes a **Bluesky Dashboard** tab for running and monitoring Bluesky scans.
- The dashboard shows:
  - Number of posts to process
  - Duplicates found
  - Books added to CSV
  - Books ignored (already in CSV)
- You can run or stop Bluesky scans independently of Reddit scans.

### Command Line Only Bluesky Scan

To run only the Bluesky scan from the command line:

```cmd
python bookbot.py --bluesky-only
```

This will process Bluesky posts according to your config and update the CSV/logs.
