#!/bin/bash

# Get the absolute path to the script's directory and cd into it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set up the cron job for scheduled tasks
if [ -f cron_setup.sh ]; then
    echo "Setting up cron job..."
    bash cron_setup.sh
    echo "Cron setup finished."
else
    echo "WARNING: cron_setup.sh not found. Skipping cron setup."
fi

echo # Add a blank line for readability

# --- Display Schedule and Wait for User Confirmation ---
CONFIG_FILE="config.ini"
CRON_SCHEDULE=$(grep "double_check_times" "$CONFIG_FILE" | awk -F'=' '{print $2}' | xargs)

if [ -n "$CRON_SCHEDULE" ]; then
    echo "🗓️  Automated tasks are scheduled to run at: $CRON_SCHEDULE"
else
    echo "🗓️  Automated tasks are currently disabled (double_check_times is empty in config.ini)."
fi

echo "-> The bot will now perform a one-time scan of the subreddit."
read -p "-> Type 'start' and press Enter to begin: " user_input

if [ "$user_input" != "start" ]; then
    echo "Aborted by user. Exiting."
    exit 0
fi
# --- End Confirmation ---

# Activate virtual environment
source venv/bin/activate

# Backup config.ini if it exists
if [ -f config.ini ]; then
    cp config.ini config.ini.bak
fi

# Run the main bot
echo "🚀 Starting bot..."
python3 bookbot.py

# Restore config.ini if it was overwritten
if [ -f config.ini.bak ]; then
    mv config.ini.bak config.ini
fi

echo "✅ Bot run finished."
read -p "Press ENTER to close..."
