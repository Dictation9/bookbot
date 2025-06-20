import shutil
import configparser
import os
from .email_utils import send_email

def check_disk_usage(path="/"):
    total, used, free = shutil.disk_usage(path)
    percent = used / total * 100
    return percent, total, used, free

def send_alert_email(level, usage_percent, config):
    subject = f"⚠️ Book Bot Storage Alert: {level.upper()}"
    body = f"The disk usage has reached {usage_percent:.2f}%, which exceeds the {level} threshold."
    send_email(subject, body, config=config)

def run_storage_check():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.ini')
    state_file = os.path.join(project_root, ".disk_alert_state")
    
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        print(f"❌ Cannot find config file at {config_path}")
        return
    config.read(config_path)

    # Get thresholds from config, with defaults
    warn_threshold = config.getint("general", "storage_warn_percent", fallback=80)
    critical_threshold = config.getint("general", "storage_critical_percent", fallback=90)
    
    # Path to check can also be from config, defaults to root "/"
    path_to_check = config.get("general", "storage_path_to_check", fallback="/")

    usage_percent, _, _, _ = check_disk_usage(path_to_check)
    
    last_alert_level = "none"
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            last_alert_level = f.read().strip()

    alert_level_to_send = None
    new_alert_level = last_alert_level

    if usage_percent >= critical_threshold:
        if last_alert_level != "critical":
            alert_level_to_send = "critical"
        new_alert_level = "critical"
    elif usage_percent >= warn_threshold:
        if last_alert_level not in ["warn", "critical"]:
            alert_level_to_send = "warn"
        new_alert_level = "warn"
    else:
        new_alert_level = "none"

    if alert_level_to_send:
        print(f"Disk usage is at {usage_percent:.2f}%. Sending {alert_level_to_send} alert.")
        send_alert_email(alert_level_to_send, usage_percent, config)
        with open(state_file, "w") as f:
            f.write(new_alert_level)
    elif new_alert_level != last_alert_level:
        # If usage dropped below a threshold, just update the state without an alert
        print(f"Disk usage is now {usage_percent:.2f}%. Resetting alert state to '{new_alert_level}'.")
        with open(state_file, "w") as f:
            f.write(new_alert_level)

if __name__ == "__main__":
    run_storage_check()
