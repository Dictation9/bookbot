#!/bin/bash

echo "[*] Installing cron jobs..."

# Edit user's crontab
(crontab -l 2>/dev/null; echo "0 8 * * * /home/pi/bookbot/venv/bin/python /home/pi/bookbot/send_csv_email.py") | crontab -
(crontab -l 2>/dev/null; echo "0 17 * * * /home/pi/bookbot/venv/bin/python /home/pi/bookbot/send_csv_email.py") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * /home/pi/bookbot/venv/bin/python /home/pi/bookbot/storage_alert.py") | crontab -

echo "[✓] Cron jobs installed."
