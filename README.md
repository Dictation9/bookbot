# 📚 Book Bot

A Raspberry Pi–friendly Reddit bot that scans a subreddit for book mentions (e.g. `[Title by Author]`), enriches them using Open Library, and emails you daily CSV reports.

---

## 🚀 Features

- 🔍 Searches a subreddit for books in `[Title by Author]` format
- 📖 Looks up ISBNs, tags, and cover URLs via Open Library
- 📨 Sends you an email with the latest CSV report twice a day (8AM & 5PM)
- 🧼 Monitors your Raspberry Pi's disk usage and emails you warnings
- 🖱️ One-click desktop launcher to run the bot manually

---

## 💾 Requirements

- Raspberry Pi (Pi 3/4/5 recommended)
- Python 3 with `pip`
- A Gmail account (or SMTP credentials for email)
- A Reddit app (for API credentials)

---

## 🔧 Setup Instructions

### 1. Clone and install

Run this in the terminal:

```bash
curl -sSL https://raw.githubusercontent.com/YOURUSERNAME/bookbot/main/install.sh
```

Or clone manually:

```bash
git clone https://github.com/YOURUSERNAME/bookbot.git ~/bookbot
cd ~/bookbot
chmod +x install.sh
./install.sh
```

2. Configure credentials
Edit config.ini and add your Reddit and email credentials:

[reddit]
client_id = your_client_id
client_secret = your_client_secret
user_agent = queernook-bookbot

[email]
from = your_email@gmail.com
to = your_email@gmail.com
password = your_app_password
smtp_server = smtp.gmail.com
smtp_port = 587

📌 If using Gmail:

Enable 2FA
Generate an App Password
🖥️ How to Use

🟢 Run the bot manually
cd ~/bookbot
source venv/bin/activate
python3 bookbot.py
🖱️ Run from desktop
Find "Book Bot" on your desktop
Double-click to launch in terminal
🕒 Automated Tasks (Cron)

🕗 8:00 AM – sends the current CSV by email
🕔 5:00 PM – sends another daily CSV update
🔁 Hourly – checks for low disk space and emails if over 80% or 90%
These are auto-installed with cron_setup.sh.

📁 Files Included

File	Description
bookbot.py	Main Reddit book scraper
send_csv_email.py	Sends the CSV via email
storage_alert.py	Emails you when disk is low
config.ini	Your Reddit/email credentials
book_mentions.csv	Book database (auto-generated)
install.sh	Sets up virtual environment, deps, shortcuts
cron_setup.sh	Installs scheduled tasks
bookbot.desktop	Desktop launcher
run.sh	Script that runs bookbot.py via terminal

---

Let me know your GitHub username or repo name if you'd like me to personalize the URLs for your actual repo!
