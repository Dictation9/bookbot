import configparser
import os
from .email_utils import send_email

def send_full_report():
    # --- Load Config ---
    config = configparser.ConfigParser()
    # Assuming the script is run from the project root
    config_path = "config.ini"
    if not os.path.exists(config_path):
        print(f"❌ {config_path} is missing. Please create it first.")
        # Try to find config relative to the script's location as a fallback
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        if not os.path.exists(config_path):
            exit(1)
    config.read(config_path)

    # --- Define File Paths ---
    # Construct absolute paths from the project root (assuming script is run from root)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    files_to_send = [
        os.path.join(project_root, "book_mentions.csv"),
        os.path.join(project_root, "logs", "bot.log"),
        os.path.join(project_root, "logs", "comment_data.log")
    ]
    
    # Filter out files that don't exist
    existing_files = [f for f in files_to_send if os.path.exists(f)]

    if not existing_files:
        print("No files found to send. Report cancelled.")
        return

    # --- Send the email ---
    subject = "📚 Book Bot - Full Manual Report"
    body = f"Attached are your requested log and data files."
    
    print("Sending full report...")
    success = send_email(subject, body, attachments=existing_files, config=config)

    if success:
        print("✅ Full report email process completed.")
    else:
        print("❌ Full report email process failed.")


if __name__ == "__main__":
    send_full_report() 