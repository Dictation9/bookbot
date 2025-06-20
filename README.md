# 📚 Book Bot

A modular and configurable Reddit bot that scans subreddits for book mentions, enriches the data using various web APIs, and provides robust logging and reporting. It's designed for long-term, autonomous operation.

## ✨ Core Concepts

This bot operates in two primary modes:

1.  **Manual Scan (`run.sh`):** When you execute `./run.sh`, the bot performs a single, immediate scan of the target subreddit based on your `config.ini` settings. This script will also set up or update the scheduled tasks, ensuring your cron job always matches your config.
2.  **Scheduled Tasks (`scheduled_check.py`):** This script is designed to be run automatically by a scheduler like `cron`. It handles all recurring maintenance tasks:
    *   **Data Enrichment:** Re-scans the CSV to find and fill in any missing book information.
    *   **Email Reporting:** Sends the CSV data and log files via email.
    *   **Storage Monitoring:** Checks disk space and sends an alert if it's running low.
    *   **Auto-Updating:** Pulls the latest version from Git to keep the bot current.

Running `run.sh` is the primary way to interact with the bot, as it handles both manual scans and the configuration of these automated background tasks.

## 🛠️ Installation

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
subreddit = your_subreddit
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
storage_path_to_check = /
```

#### `[reddit]`

*   `client_id`, `client_secret`: Your Reddit API credentials.
*   `user_agent`: A unique identifier for your bot (e.g., `bookbot-v1 by u/yourusername`).
*   `subreddit`: The subreddit to scan (e.g., `romancebooks`).
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

### Performing a One-Off Scan

This will run the bot once and update the cron schedule based on your `config.ini`.

```bash
./run.sh
```

### Automated Scheduling

The scheduled tasks (enrichment, reporting, etc.) are managed by `cron`. When you run `./run.sh`, the script `cron_setup.sh` reads the `double_check_times` from your `config.ini` and automatically creates the necessary cron jobs for you. You can change the schedule at any time by editing the config file and re-running `./run.sh`.

### Manually Sending a Full Report

If you want an immediate email report with the CSV and all log files, you can run:

```bash
./send_report.sh
```

This script is smart and will automatically split large log files into multiple emails to avoid attachment size limits.

## 🔄 Updating

To update the bot to the latest version from GitHub without losing your configuration:

```bash
./manual_update.sh
```

This script pulls the latest code, restores your `config.ini`, and runs `pip install` to ensure any new dependencies are added.

## 📂 File Structure

*   `bookbot.py`: The main application entry point for manual scans.
*   `scheduled_check.py`: The script executed by `cron` for all automated tasks.
*   `run.sh`: The recommended script for running the bot and setting up cron jobs.
*   `install.sh`: The initial installation script.
*   `config.ini`: Your private configuration and API keys.
*   `book_mentions.csv`: The master CSV where all collected data is stored.
*   `logs/`: Contains `bot.log` (activity log), `comment_data.log` (raw comment data for debugging), and `cron.log` (output from scheduled tasks).
*   `handlers/`: Contains the logic for parsing different comment formats (`curly_bracket_handler.py`, `romance_bot_handler.py`) and for fetching data from web sources (`web_search/`).
*   `email_handlers/`: Contains all scripts related to sending emails, including the utility for splitting large files.

## 🛠️ Troubleshooting

- **`ValueError: invalid literal for int()`:** You likely have an inline comment (`#`) in your `config.ini` on the same line as a value. All comments must be on their own line.
- **Authentication Errors:** Double-check all credentials in `config.ini`. Ensure you are using an "App Password" for your email if using Gmail.
- **Cron Job Not Running:**
    - Run `crontab -l` to see if the jobs were created.
    - Check `logs/cron.log` for any error messages from the scheduled runs.
    - Make sure your system's `cron` daemon is running.
- **Permission Denied:** Ensure all `.sh` scripts are executable by running `chmod +x *.sh`.

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
