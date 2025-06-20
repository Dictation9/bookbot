import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

def send_full_report():
    # Load config
    config = configparser.ConfigParser()
    if not os.path.exists("config.ini"):
        print("❌ config.ini is missing. Please create it first.")
        exit(1)
    config.read("config.ini")

    EMAIL_FROM = config["email"]["from"]
    EMAIL_TO = config["email"]["to"]
    EMAIL_PASSWORD = config["email"]["password"]
    SMTP_SERVER = config["email"]["smtp_server"]
    SMTP_PORT = int(config["email"]["smtp_port"])

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "📚 Book Bot - Manual Report"

    attachments = []
    # Define paths (assuming script is run from root)
    csv_path = "book_mentions.csv"
    botlog_path = os.path.join("logs", "bot.log")
    commentlog_path = os.path.join("logs", "comment_data.log")

    # Attach CSV if it exists
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(csv_path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(csv_path)}"'
            msg.attach(part)
            attachments.append(os.path.basename(csv_path))

    # Attach logs if they exist
    if os.path.exists(botlog_path):
        with open(botlog_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(botlog_path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(botlog_path)}"'
            msg.attach(part)
            attachments.append(os.path.basename(botlog_path))

    if os.path.exists(commentlog_path):
        with open(commentlog_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(commentlog_path))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(commentlog_path)}"'
            msg.attach(part)
            attachments.append(os.path.basename(commentlog_path))

    if not attachments:
        print("No files to send. Aborting.")
        return

    body = "Attached are your requested files: " + ", ".join(attachments) + "."
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📧 Email sent with {', '.join(attachments)}.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_full_report() 