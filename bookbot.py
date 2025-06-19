import re
import configparser
import requests
import praw
import logging
import os
from rich.console import Console
from rich.table import Table
import csv

# Set up error logging
logging.basicConfig(filename="error.log", level=logging.ERROR,
                    format="%(asctime)s [%(levelname)s] %(message)s")
# Set up activity logging
activity_logger = logging.getLogger("bot_activity")
activity_logger.setLevel(logging.INFO)
activity_handler = logging.FileHandler("bot.log")
activity_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
activity_logger.addHandler(activity_handler)

# Load config
config = configparser.ConfigParser()
if not os.path.exists("config.ini"):
    print("❌ config.ini is missing. Please create it from config.example.ini.")
    exit(1)
config.read("config.ini")

REDDIT_CLIENT_ID = config["reddit"]["client_id"]
REDDIT_SECRET = config["reddit"]["client_secret"]
REDDIT_USER_AGENT = config["reddit"]["user_agent"]
SUBREDDIT_NAME = config["reddit"].get("subreddit", "lgbtbooks")

POST_LIMIT = 10  # Set to None to fetch all posts

console = Console()

EMAIL_FROM = config["email"]["from"]
EMAIL_TO = config["email"]["to"]
EMAIL_PASSWORD = config["email"]["password"]
SMTP_SERVER = config["email"]["smtp_server"]
SMTP_PORT = int(config["email"]["smtp_port"])

def extract_books(text):
    pattern = r"\[(.*?)\s+by\s+(.*?)\]"
    return [(t.strip(), a.strip()) for t, a in re.findall(pattern, text, re.IGNORECASE)]

def lookup_open_library(title, author):
    url = f"https://openlibrary.org/search.json?title={title}&author={author}"
    r = requests.get(url)
    if not r.ok:
        return None

    docs = r.json().get("docs", [])
    if not docs:
        return None

    doc = docs[0]
    return {
        "title": doc.get("title", title),
        "author": ", ".join(doc.get("author_name", [author])),
        "tags": doc.get("subject", [])[:10],
        "cover_url": f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg" if doc.get("cover_i") else "N/A",
        "isbn13": next((i for i in doc.get("isbn", []) if len(i) == 13), "N/A")
    }

def display_book(book):
    table = Table(title=f"[bold magenta]{book['title']}[/] by {book['author']}")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Tags", ", ".join(book["tags"]) if book["tags"] else "None")
    table.add_row("Cover URL", book["cover_url"])
    table.add_row("ISBN-13", book["isbn13"])
    console.print(table)
    console.print("-" * 60)

def write_book_to_csv(book, csv_path="book_mentions.csv"):
    # Read existing entries to avoid duplicates
    existing = set()
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = (row['title'].strip().lower(), row['author'].strip().lower())
                existing.add(key)
    except FileNotFoundError:
        pass  # File will be created

    key = (book['title'].strip().lower(), book['author'].strip().lower())
    if key in existing:
        return  # Duplicate, do not write

    # Write new entry
    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'author', 'isbn13', 'tags', 'cover_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            'title': book['title'],
            'author': book['author'],
            'isbn13': book['isbn13'],
            'tags': ', '.join(book['tags']) if book['tags'] else '',
            'cover_url': book['cover_url']
        })
    activity_logger.info(f"Wrote book to CSV: {book['title']} by {book['author']}")

def auto_update():
    import subprocess
    import os
    repo_dir = os.path.expanduser("~/bookbot")
    if os.path.exists(repo_dir):
        try:
            subprocess.run(["git", "-C", repo_dir, "pull"], check=True)
            print("🔄 Auto-update complete.")
        except subprocess.CalledProcessError:
            print("⚠️ Auto-update failed. Please pull manually.")


def send_test_email():
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText("✅ Book Bot started successfully on your Raspberry Pi.")
    msg["Subject"] = "Book Bot Started"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Test email sent.")
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")

def main():
    send_test_email()

    auto_update()

    activity_logger.info(f"Scanning r/{SUBREDDIT_NAME} for book mentions...")

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    seen = set()

    console.print(f"[green]Scanning r/{SUBREDDIT_NAME} for book mentions...[/]\n")

    posts = subreddit.new(limit=POST_LIMIT) if POST_LIMIT else subreddit.new(limit=None)

    for post in posts:
        content = f"{post.title} {post.selftext}"
        mentions = extract_books(content)

        for title, author in mentions:
            key = (title.lower(), author.lower())
            if key in seen:
                continue
            seen.add(key)

            book = lookup_open_library(title, author)
            if book:
                activity_logger.info(f"Found book mention: {book['title']} by {book['author']}")
                write_book_to_csv(book)
                display_book(book)
            else:
                console.print(f"[yellow]No data found for: {title} by {author}[/]")

    activity_logger.info(f"✅ Book scan complete.")
    console.print(f"[cyan]✅ Book scan complete.[/]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Bot crashed:")
        print("❌ An error occurred. Check error.log for details.")
