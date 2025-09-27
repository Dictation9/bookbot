import configparser
import os
import logging
from rich.console import Console
from handlers.csv_double_check_handler import run_csv_double_check
from bookbot import auto_update

# --- Setup Logging ---
console = Console()
activity_logger = logging.getLogger("manual_enrich_activity")
activity_logger.setLevel(logging.INFO)
# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)
activity_handler = logging.FileHandler("logs/manual_enrich.log", mode='a', encoding='utf-8') # Separate log for manual enrich
activity_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] (Manual Enrich) %(message)s"))
activity_logger.addHandler(activity_handler)

def run_manual_enrich():
    # --- Load Config ---
    config = configparser.ConfigParser()
    config_path = "config.ini"
    if not os.path.exists(config_path):
        console.print(f"❌ {config_path} is missing.")
        activity_logger.error(f"config.ini missing, cannot run manual enrich.")
        exit(1)
    config.read(config_path)

    # --- Read Config Values ---
    REDDIT_CLIENT_ID = config["reddit"]["client_id"]
    REDDIT_SECRET = config["reddit"]["client_secret"]
    REDDIT_USER_AGENT = config["reddit"]["user_agent"]
    DOUBLE_CHECK_MODE = config['general'].get('double_check_mode', 'missing').strip().lower()

    activity_logger.info("--- Starting Manual Enrich ---")
    console.print("--- Starting Manual Enrich ---")

    # --- Initialize PRAW ---
    import praw
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    # --- Run Double-Check/Enrichment ---
    console.print("Running CSV double-check/enrichment...")
    activity_logger.info("Running CSV double-check/enrichment...")
    run_csv_double_check(mode=DOUBLE_CHECK_MODE, praw_reddit=reddit)

    # --- Auto-Update ---
    console.print("Checking for updates...")
    activity_logger.info("Checking for updates...")
    auto_update()

    activity_logger.info("--- Manual Enrich Complete ---")
    console.print("--- Manual Enrich Complete ---")

if __name__ == "__main__":
    run_manual_enrich() 