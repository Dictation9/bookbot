import shutil
import smtplib
import configparser
import os
from email.mime.text import MIMEText

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

def send_alert(level, usage):
    percent, total, used, free = usage
    msg = MIMEText(f"{level.upper()} - Disk usage: {percent:.2f}%\nFree: {free // (1024**3)} GB")
    msg["Subject"] = f"Disk Usage Alert: {level.upper()}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def get_last_alert_level():
    return open(STATE_FILE).read().strip() if os.path.exists(STATE_FILE) else "none"

def set_last_alert_level(level):
    with open(STATE_FILE, "w") as f:
        f.write(level)

if __name__ == "__main__":
    percent, total, used, free = check_disk_usage()
    last = get_last_alert_level()

    if percent >= CRITICAL_THRESHOLD and last != "critical":
        send_alert("critical", (percent, total, used, free))
        set_last_alert_level("critical")
    elif percent >= WARN_THRESHOLD and last == "none":
        send_alert("warn", (percent, total, used, free))
        set_last_alert_level("warn")
    elif percent < WARN_THRESHOLD and last != "none":
        set_last_alert_level("none")
