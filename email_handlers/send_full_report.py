import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import math

# Set a safe max size for attachments in a single email (in bytes)
# GMX/Gmail limit is 25MB, let's use 20MB to be safe.
MAX_EMAIL_SIZE_MB = 20
MAX_ATTACHMENT_SIZE = MAX_EMAIL_SIZE_MB * 1024 * 1024

def send_email(config, subject, body, attachments_data):
    """Helper function to send one email."""
    EMAIL_FROM = config["email"]["from"]
    EMAIL_TO = config["email"]["to"]
    EMAIL_PASSWORD = config["email"]["password"]
    SMTP_SERVER = config["email"]["smtp_server"]
    SMTP_PORT = int(config["email"]["smtp_port"])

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    for filename, data in attachments_data.items():
        part = MIMEApplication(data, Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📧 Email sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email '{subject}': {e}")
        return False

def send_full_report():
    # --- Load Config ---
    config = configparser.ConfigParser()
    config_path = "config.ini"
    if not os.path.exists(config_path):
        print(f"❌ {config_path} is missing. Please create it first.")
        exit(1)
    config.read(config_path)

    # --- File Paths ---
    files_to_send = [
        "book_mentions.csv",
        os.path.join("logs", "bot.log"),
        os.path.join("logs", "comment_data.log")
    ]

    small_attachments = {}
    
    for file_path in files_to_send:
        if not os.path.exists(file_path):
            continue

        file_size = os.path.getsize(file_path)
        file_basename = os.path.basename(file_path)

        if file_size > MAX_ATTACHMENT_SIZE:
            # File is too large, split it and send in multiple emails
            print(f"'{file_path}' is {file_size/1024/1024:.2f}MB, which is too large. Splitting into multiple emails.")
            num_chunks = math.ceil(file_size / MAX_ATTACHMENT_SIZE)
            with open(file_path, "rb") as f:
                for i in range(num_chunks):
                    chunk_data = f.read(MAX_ATTACHMENT_SIZE)
                    chunk_filename = f"{file_basename}.part{i+1}"
                    subject = f"📚 Book Bot - Manual Report ({file_basename} Part {i+1}/{num_chunks})"
                    body = f"Attached is part {i+1} of {num_chunks} for {file_basename}."
                    send_email(config, subject, body, {chunk_filename: chunk_data})
        else:
            # File is small enough, add to the combined email
            with open(file_path, "rb") as f:
                 small_attachments[file_basename] = f.read()

    # --- Send the combined report of small files ---
    if small_attachments:
        attachment_names = ", ".join(small_attachments.keys())
        subject = "📚 Book Bot - Manual Report"
        body = f"Attached are your requested files: {attachment_names}."
        send_email(config, subject, body, small_attachments)
    else:
        # This message shows only if no small files were found and all large files were handled above.
        print("All files were sent as chunks. No combined report needed.")


if __name__ == "__main__":
    send_full_report() 