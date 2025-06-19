# 📚 Book Bot

A Raspberry Pi–friendly Reddit bot that finds `[Book by Author]` mentions, enriches them using Open Library, and emails you daily updates.

## 🚀 Install

```bash
curl -sSL https://raw.githubusercontent.com/Dictation9/bookbot/main/install.sh | bash
```

Then edit `config.ini` to add your Reddit and email credentials.

## 📂 Includes

- `bookbot.py` – Main Reddit bot
- `send_csv_email.py` – Sends daily CSV email
- `storage_alert.py` – Disk usage alerts
- `cron_setup.sh` – Adds scheduled tasks
- `install.sh` – Full installer

---
[GitHub Repo](https://github.com/Dictation9/bookbot)
