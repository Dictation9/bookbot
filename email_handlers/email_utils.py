import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import math

MAX_EMAIL_SIZE_MB = 20
MAX_ATTACHMENT_SIZE = MAX_EMAIL_SIZE_MB * 1024 * 1024

def send_email(subject, body, attachments=None, config=None):
    """
    Sends an email with optional attachments, handling large files by splitting them.
    - subject (str): The subject of the email.
    - body (str): The plain text body of the email.
    - attachments (list): A list of file paths to attach.
    - config (ConfigParser): A loaded configparser object. If None, it will be loaded.
    """
    if config is None:
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        if not os.path.exists(config_path):
            print(f"❌ Cannot find config file at {config_path}")
            return False
        config.read(config_path)

    EMAIL_FROM = config["email"]["from"]
    EMAIL_TO = config["email"]["to"]
    EMAIL_PASSWORD = config["email"]["password"]
    SMTP_SERVER = config["email"]["smtp_server"]
    SMTP_PORT = int(config["email"]["smtp_port"])

    attachments = attachments or []
    small_attachments_data = {}
    
    # Process attachments, splitting large ones
    for file_path in attachments:
        if not os.path.exists(file_path):
            print(f"⚠️ Attachment not found, skipping: {file_path}")
            continue

        file_size = os.path.getsize(file_path)
        file_basename = os.path.basename(file_path)

        if file_size > MAX_ATTACHMENT_SIZE:
            print(f"'{file_path}' is {file_size/1024/1024:.2f}MB. Splitting into multiple emails.")
            num_chunks = math.ceil(file_size / MAX_ATTACHMENT_SIZE)
            with open(file_path, "rb") as f:
                for i in range(num_chunks):
                    chunk_data = f.read(MAX_ATTACHMENT_SIZE)
                    chunk_filename = f"{file_basename}.part{i+1}"
                    chunk_subject = f"{subject} ({file_basename} Part {i+1}/{num_chunks})"
                    chunk_body = f"Attached is part {i+1} of {num_chunks} for {file_basename}."
                    
                    # Recursively call a helper to send the single chunk
                    _send_single_email(config, chunk_subject, chunk_body, {chunk_filename: chunk_data})
        else:
            with open(file_path, "rb") as f:
                small_attachments_data[file_basename] = f.read()

    # Send the main email with the body and any small attachments
    return _send_single_email(config, subject, body, small_attachments_data)


def _send_single_email(config, subject, body, attachments_data):
    """Internal helper to send one email message."""
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
        print(f"📧 Email sent: \"{subject}\"")
        return True
    except Exception as e:
        print(f"❌ Failed to send email \"{subject}\": {e}")
        return False 