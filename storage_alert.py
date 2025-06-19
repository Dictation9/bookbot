import shutil
import smtplib
import configparser
import os
from email.mime.text import MIMEText

# Load config
config = configparser.ConfigParser()
config.read("config.ini")

EMAIL_FROM = config["email"]["from"]
EMAIL_TO = config["email"]["to"]
EMAIL_PASSWORD = config["email"]["password"]
SMTP_SERVER = config["email"]["smtp_server"]
SMTP_PORT = int(config["email"]["smtp_port"])

WARN_THRESHOLD = 80
CRITICAL_THRESHOLD = 90
STATE_FILE = "/home/pi/bookbot/.disk_alert_state"

def check_disk_usage():
    total, used, free = shutil.disk_usage("/")
    percent = used / total * 100
    return percent, total, used, free

def send_storage_email(level, usage):
    level_label = "⚠️ WARNING" if level == "warn" else "❗ CRITICAL"
    percent, total, used, free = usage

    body = (
        f"{level_label} - Your Raspberry Pi is running low on storage.\n\n"
        f"Used: {used // (1024**3)} GB / {total // (1024**3)} GB "
        f"({percent:.2f}% used)\nFree: {free // (1024**3)} GB\n"
    )

    msg = MIMEText(body)
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = f"[{level_label}] Raspberry Pi Disk Usage Alert"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📧 {level_label} email sent.")
    except Exception as e:
        print(f"❌ Failed to send alert email: {e}")

def get_last_alert_level():
    if not os.path.exists(STATE_FILE):
        return "none"
    with open(STATE_FILE, "r") as f:
        return f.read().strip()

def set_last_alert_level(level):
    with open(STATE_FILE, "w") as f:
        f.write(level)

if __name__ == "__main__":
    percent, total, used, free = check_disk_usage()
    current_level = get_last_alert_level()

    if percent >= CRITICAL_THRESHOLD and current_level != "critical":
        send_storage_email("critical", (percent, total, used, free))
        set_last_alert_level("critical")
    elif percent >= WARN_THRESHOLD and current_level == "none":
        send_storage_email("warn", (percent, total, used, free))
        set_last_alert_level("warn")
    elif percent < WARN_THRESHOLD and current_level != "none":
        set_last_alert_level("none")
        print("✅ Storage back to normal. Alert state reset.")
    else:
        print(f"ℹ️ Disk usage: {percent:.2f}%. No alert triggered.")
