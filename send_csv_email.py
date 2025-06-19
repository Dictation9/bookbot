import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

# Load config
config = configparser.ConfigParser()
config.read("config.ini")

EMAIL_FROM = config["email"]["from"]
EMAIL_TO = config["email"]["to"]
EMAIL_PASSWORD = config["email"]["password"]
SMTP_SERVER = config["email"]["smtp_server"]
SMTP_PORT = int(config["email"]["smtp_port"])

CSV_PATH = "/home/pi/bookbot/book_mentions.csv"

def send_email_with_csv():
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "📚 Queernook BookBot - Daily CSV Report"

    body = "Attached is the latest Queernook BookBot CSV export from your Raspberry Pi."
    msg.attach(MIMEText(body, "plain"))

    # Attach CSV if it exists
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "rb") as f:
            part = MIMEApplication(f.read(), Name="book_mentions.csv")
            part["Content-Disposition"] = 'attachment; filename="book_mentions.csv"'
            msg.attach(part)
    else:
        msg.attach(MIMEText("book_mentions.csv not found on device.", "plain"))

    # Send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Email with CSV sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_email_with_csv()
