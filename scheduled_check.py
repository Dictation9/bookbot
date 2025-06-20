import praw
import configparser
import os
import logging
from rich.console import Console

# Assuming this script is run from the root of the bookbot directory
from handlers.csv_double_check_handler import run_csv_double_check
from email_handlers.send_csv_email import send_csv_email
from email_handlers.storage_alert import run_storage_check
from bookbot import auto_update

# --- Setup Logging ---
console = Console()
activity_logger = logging.getLogger("scheduled_check_activity")
activity_logger.setLevel(logging.INFO)
# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)
activity_handler = logging.FileHandler("logs/bot.log", mode='a') # Append to the main bot log
activity_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] (Scheduled Check) %(message)s"))
activity_logger.addHandler(activity_handler)

def run_scheduled_tasks():
    # --- Load Config ---
    config = configparser.ConfigParser()
    config_path = "config.ini"
    if not os.path.exists(config_path):
        console.print(f"❌ {config_path} is missing.")
        activity_logger.error(f"config.ini missing, cannot run scheduled check.")
        exit(1)
    config.read(config_path)

    # --- Read Config Values ---
    REDDIT_CLIENT_ID = config["reddit"]["client_id"]
    REDDIT_SECRET = config["reddit"]["client_secret"]
    REDDIT_USER_AGENT = config["reddit"]["user_agent"]
    DOUBLE_CHECK_MODE = config['general'].get('double_check_mode', 'missing').strip().lower()
    SEND_CSV_EMAIL = config["email"].get("send_csv_email", "true").strip().lower() == "true"
    
    activity_logger.info("--- Starting Scheduled Tasks ---")
    console.print("--- Starting Scheduled Tasks ---")

    # --- Initialize PRAW ---
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    # --- Run Double-Check ---
    console.print("Running CSV double-check...")
    activity_logger.info("Running CSV double-check...")
    run_csv_double_check(mode=DOUBLE_CHECK_MODE, praw_reddit=reddit)
    
    # --- Send Report ---
    if SEND_CSV_EMAIL:
        console.print("Sending email report...")
        activity_logger.info("Sending email report...")
        send_csv_email()

    # --- Run Storage Alert Check ---
    console.print("Checking storage usage...")
    activity_logger.info("Checking storage usage...")
    run_storage_check()
    
    # --- Auto-Update ---
    console.print("Checking for updates...")
    activity_logger.info("Checking for updates...")
    auto_update()

    activity_logger.info("--- Scheduled Tasks Complete ---")
    console.print("--- Scheduled Tasks Complete ---")

if __name__ == "__main__":
    run_scheduled_tasks() 