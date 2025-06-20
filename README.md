# 📚 Book Bot

A Raspberry Pi–friendly Reddit bot that finds `{Book Title by Author}` mentions in posts and comments, enriches them using Open Library, romance.io, and Google Books, and emails you daily updates with a CSV export.

## 🚀 Features

- **Scans posts and comments** in a subreddit for `{Book Title by Author}` (curly braces format)
- **Extracts book data** from Open Library, then romance.io, then Google Books (in that order)
- **Captures romance.io links** if present in posts/comments, even if Open Library provides data
- **Exports all found books to a CSV** with the following columns:
  - title
  - author
  - isbn13
  - tags (from Open Library or Google Books)
  - cover_url
  - romance_io_url (from scraping or direct link in post/comment)
  - google_books_url
  - datetime_added (when the entry was added to the CSV)
  - reddit_created_utc (when the post/comment was uploaded to Reddit, UTC timestamp)
  - reddit_created_date (human-readable date)
- **Configurable post/comment limit** via `config.ini`
- **Option to email the CSV** after each run (configurable in `config.ini`)
- **Robust error handling and rate limit management**
- **Manual update script** to safely update the bot while preserving your config
- **Modular bot handler support** – easily add new bot handlers for different Reddit bots (see below)

## 🛠️ Install

```bash
curl -sSL https://raw.githubusercontent.com/Dictation9/bookbot/main/install.sh | bash
```

Then edit `config.ini` to add your Reddit and email credentials, and set your preferences.

## ⚙️ Configuration

Edit `config.ini`:

```ini
[reddit]
client_id = your_client_id
client_secret = your_client_secret
user_agent = bookbot
subreddit = your_subreddit
limit = 10  # Set to None to fetch all posts/comments

[email]
from = your_email@gmail.com
to = your_email@gmail.com
password = your_app_password
smtp_server = smtp.gmail.com
smtp_port = 587
send_csv_email = true  # Set to false to disable sending CSV via email
```

- **limit**: How many posts/comments to scan. Set to `None` for all.
- **send_csv_email**: Set to `true` to email the CSV after each run, or `false` to disable.

## 📝 Usage

1. Run the bot:
   ```bash
   ./run.sh
   ```
2. The bot will scan the configured subreddit for `{Book Title by Author}` in posts and comments.
3. For each match, it will:
   - Try to fetch book data from Open Library.
   - If not found, try romance.io (using direct links in comments if present).
   - If still not found, try Google Books.
   - If no data is found, add minimal info (title/author only).
   - Always include the romance.io link if present in the post/comment.
4. All results are saved to `book_mentions.csv`.
5. If enabled, the CSV will be emailed to you after the scan.

## 🔄 Manual Update

To safely update your bot to the latest version **without overwriting your config.ini**, use:

```bash
./manual_update.sh
```
This will pull the latest code and restore your config file automatically.

## 📄 CSV Columns
- `title`, `author`, `isbn13`, `tags`, `cover_url`, `romance_io_url`, `google_books_url`, `datetime_added`, `reddit_created_utc`, `reddit_created_date`

## 🧩 Dependencies
- Python 3.7+
- praw
- requests
- rich
- beautifulsoup4

All dependencies are installed automatically by `install.sh`.

## 🛠️ Troubleshooting

- **ModuleNotFoundError: No module named 'bs4'**
  - Run: `pip install beautifulsoup4`
- **ModuleNotFoundError: No module named 'praw' or 'rich'**
  - Run: `pip install praw rich prawcore`
- **ValueError: invalid literal for int() with base 10: '10  # Set to None...'**
  - Remove comments from the same line as values in `config.ini`. Place comments on their own line above the setting.
- **Authentication errors with Reddit or email**
  - Double-check your credentials in `config.ini`.
- **Bot not finding any books**
  - Make sure posts/comments use the `{Book Title by Author}` format with curly braces.
- **CSV not being created**
  - Ensure the bot has write permissions in the directory and that at least one book mention is found.

## 🛡️ License
MIT License

## 📂 Includes

- `bookbot.py` – Main Reddit bot
- `send_csv_email.py` – Sends daily CSV email
- `storage_alert.py` – Disk usage alerts
- `cron_setup.sh` – Sets up daily/weekly tasks
- `install.sh` – Full install script
- `bookbot.desktop` – Desktop shortcut for Raspberry Pi

## 🧩 Modular Bot Handlers

The bot now uses a modular structure for handling different Reddit bots. Each bot handler is in its own file, making it easy to add, update, or test support for new bots.

### Adding a New Bot Handler

1. **Copy the template:**
   - Use `bot_handler_template.py` as a starting point for your new bot handler.
2. **Implement detection and handling:**
   - Implement `is_<yourbot>_bot(comment)` and `handle_<yourbot>_bot_comment(comment, seen)` in your new file.
3. **Register the handler in `bookbot.py`:**
   - Import your handler and add it to the `process_comments` logic, just like `romance_bot_handler`.

**Example:**
```python
from romance_bot_handler import is_romance_bot, handle_romance_bot_comment
from fantasy_bot_handler import is_fantasy_bot, handle_fantasy_bot_comment

for comment in comments:
    if is_romance_bot(comment):
        handle_romance_bot_comment(comment, seen)
        continue
    if is_fantasy_bot(comment):
        handle_fantasy_bot_comment(comment, seen)
        continue
    # ... generic extraction ...
```

### Existing Handlers
- `romance_bot_handler.py`: Handles comments from romance-bot, including both curly-brace and plain `Title by Author` formats.
- `bot_handler_template.py`: Template for creating new handlers.
