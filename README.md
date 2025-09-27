# 📚 Book Bot

A modular and configurable Reddit bot that scans subreddits for book mentions, enriches the data using various web APIs, and provides robust logging and reporting. It's designed for long-term, autonomous operation with both command-line and graphical interfaces.

## 🖥️ Windows 11 Support

Book Bot now includes full Windows 11 support! All Windows-specific components are organized in the `windows/` folder.

**Quick Start for Windows:**
1. Run `install-windows.bat` to install
2. Edit `config.ini` with your API credentials  
3. Use `run-gui-windows.bat` for the GUI or `run-windows.bat` for command line

See `README-Windows-Quick-Start.md` for a quick guide, or `windows/README-Windows.md` for complete Windows documentation.

## ✨ Core Concepts

This bot operates in two primary modes:

1.  **Manual Scan (`run.sh`):** When you execute `./run.sh`, the bot performs a single, immediate scan of the target subreddit based on your `config.ini` settings. This script will also set up or update the scheduled tasks, ensuring your cron job always matches your config.
2.  **Scheduled Tasks (`scheduled_check.py`):** This script is designed to be run automatically by a scheduler like `cron`. It handles all recurring maintenance tasks:
    *   **Data Enrichment:** Re-scans the CSV to find and fill in any missing book information.
    *   **Email Reporting:** Sends the CSV data and log files via email.
    *   **Storage Monitoring:** Checks disk space and sends an alert if it's running low.
    *   **Auto-Updating:** Pulls the latest version from Git to keep the bot current.

Running `run.sh` is the primary way to interact with the bot, as it handles both manual scans and the configuration of these automated background tasks.

## 🖥️ Graphical User Interface

The bot now includes a modern GUI built with CustomTkinter that provides:

- **Dashboard:** Run manual scans, send reports, and view live log output
- **Configuration Editor:** Edit all settings from `config.ini` through a user-friendly form
- **CSV Viewer:** Browse and search your collected book data in a table format
- **Log Viewer:** View bot activity logs directly in the application

### Running the GUI

```bash
./run_gui.sh
```

Or simply double-click the "Book Bot" icon on your desktop (after installation).

## 🛠️ Installation

### Quick Install (Raspberry Pi)

Copy and paste this command into your Raspberry Pi terminal:

```bash
curl -sSL https://raw.githubusercontent.com/Dictation9/bookbot/main/install.sh | bash
```

### Manual Installation

Installation is handled by a single script. It will create a Python virtual environment, install all dependencies, and set up the necessary files.

```bash
# Make the installer executable
chmod +x install.sh

# Run the installer
./install.sh
```

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
# Path to monitor for disk usage. Default is "/", the root directory.
storage_path_to_check = /
```

#### `[reddit]`

*   `client_id`, `client_secret`: Your Reddit API credentials.
*   `user_agent`: A unique identifier for your bot (e.g., `bookbot-v1 by u/yourusername`).
*   `subreddit`: The subreddit(s) to scan. Supports up to 40 subreddits in a comma-separated list.
*   `limit`: The number of recent posts to scan. Leave this blank or set to `None` to scan all available posts.

#### `[email]`

*   `from`, `to`, `password`, `smtp_server`, `smtp_port`: Your email account details for sending reports. For Gmail, you'll need to use an "App Password".
*   `send_csv_email`: Set to `true` to enable scheduled email reports.

#### `[general]`

*   `delete_csv_on_start`: If `true`, `book_mentions.csv` will be wiped clean every time you run the bot manually. **Warning: This erases all collected data.**
*   `double_check_csv_on_run`: If `true`, the bot will perform a data enrichment pass after every manual scan.
*   `double_check_mode`: Determines what the scheduled enrichment task does. `missing` only fills in incomplete rows; `all` re-checks every book.
*   `double_check_times`: Configures the schedule for the automated tasks. Can be a standard cron expression (e.g., `0 * * * *` for every hour) or a comma-separated list of 24-hour times (e.g., `09:00,12:00,18:00`). Leave blank to disable all scheduled tasks.
*   `storage_warn_percent`, `storage_critical_percent`: The disk usage thresholds (in %) for sending email alerts.
*   `storage_path_to_check`: The disk path to monitor (e.g., `/` for the main disk, or `/mnt/data` for a specific drive).

## 📝 Usage

### Command Line Interface

#### Performing a One-Off Scan

This will run the bot once and update the cron schedule based on your `config.ini`.

```bash
./run.sh
```

#### Automated Scheduling

The scheduled tasks (enrichment, reporting, etc.) are managed by `cron`. When you run `./run.sh`, the script `cron_setup.sh` reads the `double_check_times` from your `config.ini` and automatically creates the necessary cron jobs for you. You can change the schedule at any time by editing the config file and re-running `./run.sh`.

#### Manually Sending a Full Report

If you want an immediate email report with the CSV and all log files, you can run:

```bash
./send_report.sh
```

This script is smart and will automatically split large log files into multiple emails to avoid attachment size limits.

### Graphical User Interface

Launch the GUI for a more user-friendly experience:

```bash
./run_gui.sh
```

The GUI provides:
- **One-click scanning** with live progress updates
- **Easy configuration editing** without touching text files
- **Real-time log viewing** to monitor bot activity
- **CSV data browsing** with search and sort capabilities

## 🔄 Updating

To update the bot to the latest version from GitHub without losing your configuration:

```bash
./manual_update.sh
```

This script pulls the latest code, restores your `config.ini`, and runs `pip install --upgrade` to ensure any new dependencies are added efficiently.

## 📂 File Structure

*   `bookbot.py`: The main application entry point for manual scans.
*   `scheduled_check.py`: The script executed by `cron` for all automated tasks.
*   `run.sh`: The recommended script for running the bot and setting up cron jobs.
*   `run_gui.sh`: Launches the graphical user interface.
*   `gui.py`: The main GUI application code.
*   `install.sh`: The initial installation script.
*   `config.ini`: Your private configuration and API keys.
*   `book_mentions.csv`: The master CSV where all collected data is stored.
*   `logs/`: Contains `bot.log` (activity log), `comment_data.log` (raw comment data for debugging), and `cron.log` (output from scheduled tasks).
*   `handlers/`: Contains the logic for parsing different comment formats (`curly_bracket_handler.py`, `romance_bot_handler.py`) and for fetching data from web sources (`web_search/`).
*   `email_handlers/`: Contains all scripts related to sending emails, including the utility for splitting large files.
*   `windows/`: Windows-specific components including batch files, PowerShell scripts, and Windows Task Scheduler integration.
*   `install-windows.bat`, `run-windows.bat`, `run-gui-windows.bat`: Windows launcher scripts for easy access.

## 🛠️ Troubleshooting

- **`ValueError: invalid literal for int()`:** You likely have an inline comment (`#`) in your `config.ini` on the same line as a value. All comments must be on their own line.
- **Authentication Errors:** Double-check all credentials in `config.ini`. Ensure you are using an "App Password" for your email if using Gmail.
- **Cron Job Not Running:**
    - Run `crontab -l` to see if the jobs were created.
    - Check `logs/cron.log` for any error messages from the scheduled runs.
    - Make sure your system's `cron` daemon is running.
- **Permission Denied:** Ensure all `.sh` scripts are executable by running `chmod +x *.sh`.
- **GUI Not Starting:** Make sure `customtkinter` is installed by running `pip install customtkinter` in your virtual environment.
- **Desktop Shortcut Not Working:** Verify the path in `bookbot.desktop` matches your actual installation directory.

## 🛡️ License
MIT License

## 📂 Includes

- `bookbot.py` – Main Reddit bot
- `send_csv_email.py` – Sends daily CSV email
- `storage_alert.py` – Disk usage alerts
- `cron_setup.sh` – Sets up daily/weekly tasks
- `install.sh` – Full install script
- `bookbot.desktop` – Desktop shortcut for Raspberry Pi

## 🧩 Modular Bot Handlers

The bot now uses a modular structure for handling different Reddit bots. Each bot handler is in its own file, making it easy to add, update, or test support for new bots.

### Adding a New Bot Handler

1. **Copy the template:**
   - Use `bot_handler_template.py` as a starting point for your new bot handler.
2. **Implement detection and handling:**
   - Implement `is_<yourbot>_bot(comment)` and `handle_<yourbot>_bot_comment(comment, seen)` in your new file.
3. **Register the handler in `bookbot.py`:**
   - Import your handler and add it to the `process_comments` logic, just like `romance_bot_handler`.

**Example:**
```python
from romance_bot_handler import is_romance_bot, handle_romance_bot_comment
from fantasy_bot_handler import is_fantasy_bot, handle_fantasy_bot_comment

for comment in comments:
    if is_romance_bot(comment):
        handle_romance_bot_comment(comment, seen)
        continue
    if is_fantasy_bot(comment):
        handle_fantasy_bot_comment(comment, seen)
        continue
    # ... generic extraction ...
```

### Existing Handlers
- `romance_bot_handler.py`: Handles comments from romance-bot, including both curly-brace and plain `Title by Author` formats.
- `bot_handler_template.py`: Template for creating new handlers.

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

- The GUI now includes a **Bluesky Dashboard** tab (on the left) for running and monitoring Bluesky scans.
- The dashboard shows:
  - Number of posts to process
  - Duplicates found
  - Books added to CSV
  - Books ignored (already in CSV)
- You can run or stop Bluesky scans independently of Reddit scans.

### Command Line Only Bluesky Scan

To run only the Bluesky scan from the command line:

```bash
python3 bookbot.py --bluesky-only
```

This will process Bluesky posts according to your config and update the CSV/logs.
