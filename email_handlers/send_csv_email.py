import configparser
import os
from .email_utils import send_email

def send_csv_email():
    """
    Sends the book_mentions.csv file via email.
    The send_email utility will handle splitting if the file is too large.
    """
    config = configparser.ConfigParser()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"❌ Cannot find config file at {config_path}")
        return
    config.read(config_path)

    # Check if sending CSV is enabled in the config
    if not config.getboolean("email", "send_csv_email", fallback=False):
        print("📧 CSV email sending is disabled in config.ini. Skipping.")
        return

    csv_path = os.path.join(project_root, "book_mentions.csv")

    if not os.path.exists(csv_path):
        print(f"⚠️ CSV file not found at {csv_path}. Cannot send report.")
        # Send an alert email instead
        subject = "📚 Book Bot - CSV Report Failed"
        body = "The scheduled CSV report failed because the file 'book_mentions.csv' could not be found."
        send_email(subject, body, config=config)
        return

    subject = "📚 Book Bot - Scheduled CSV Report"
    body = "Attached is your scheduled book mentions CSV report."
    
    print("Sending CSV report...")
    success = send_email(subject, body, attachments=[csv_path], config=config)

    if success:
        print("✅ CSV report email process completed.")
    else:
        print("❌ CSV report email process failed.")


if __name__ == "__main__":
    send_csv_email()
