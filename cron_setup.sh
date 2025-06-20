#!/bin/bash

# Get the absolute path to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
SCHEDULED_CHECK_SCRIPT="$SCRIPT_DIR/scheduled_check.py"
LOG_FILE="$SCRIPT_DIR/logs/cron.log"
CONFIG_FILE="$SCRIPT_DIR/config.ini"

# Read the cron schedule from config.ini
CRON_SCHEDULE=$(grep "double_check_times" "$CONFIG_FILE" | awk -F'=' '{print $2}' | xargs)

# The command to be run by cron
CRON_COMMAND="cd \"$SCRIPT_DIR\" && \"$VENV_PYTHON\" \"$SCHEDULED_CHECK_SCRIPT\" >> \"$LOG_FILE\" 2>&1"

# Always remove existing cron jobs for this script to ensure a clean update
echo "Removing existing cron jobs for scheduled_check.py to prevent duplicates..."
(crontab -l 2>/dev/null | grep -vF "$SCHEDULED_CHECK_SCRIPT") | crontab -

# If a schedule is defined in config.ini, proceed
if [ -n "$CRON_SCHEDULE" ]; then
    # Check if the schedule is in HH:MM format or a standard cron string
    if [[ "$CRON_SCHEDULE" == *":"* ]]; then
        echo "Detected HH:MM schedule format. Creating individual cron jobs."
        # Convert comma-separated list to space-separated for the loop
        TIMES=$(echo "$CRON_SCHEDULE" | tr ',' ' ')
        
        CRON_TMP_FILE=$(mktemp)
        crontab -l > "$CRON_TMP_FILE"

        for TIME in $TIMES; do
            HOUR=$(echo "$TIME" | cut -d: -f1)
            MINUTE=$(echo "$TIME" | cut -d: -f2)
            
            # Basic validation to ensure we have numbers
            if [[ "$HOUR" =~ ^[0-9]+$ ]] && [[ "$MINUTE" =~ ^[0-9]+$ ]]; then
                CRON_JOB="$MINUTE $HOUR * * * $CRON_COMMAND"
                echo "Adding job: $CRON_JOB"
                echo "$CRON_JOB" >> "$CRON_TMP_FILE"
            else
                echo "Skipping invalid time format: $TIME"
            fi
        done
        crontab "$CRON_TMP_FILE"
        rm "$CRON_TMP_FILE"
        echo "Cron jobs updated from HH:MM schedule."

    else
        echo "Detected standard cron schedule format."
        CRON_JOB="$CRON_SCHEDULE $CRON_COMMAND"
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo "Cron job updated from standard cron schedule."
    fi
else
    echo "No schedule found in config.ini (double_check_times is empty). Cron job(s) removed."
fi
