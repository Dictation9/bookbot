import re
import configparser
import requests
import praw
import logging
import os
from rich.console import Console
from rich.table import Table
import csv
import time
import prawcore
from bs4 import BeautifulSoup
import datetime
from handlers.romance_bot_handler import is_romance_bot, handle_romance_bot_comment
from book_utils import extract_books, extract_books_from_romance_bot, extract_romance_bot_data, update_csv_with_romance_bot, write_book_to_csv, activity_logger
from handlers.curly_bracket_handler import is_curly_bracket_comment, handle_curly_bracket_comment
from handlers.csv_double_check_handler import run_csv_double_check

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

limit_str = config["reddit"].get("limit", "10").strip()
POST_LIMIT = None if limit_str.lower() == "none" else int(limit_str)

console = Console()

EMAIL_FROM = config["email"]["from"]
EMAIL_TO = config["email"]["to"]
EMAIL_PASSWORD = config["email"]["password"]
SMTP_SERVER = config["email"]["smtp_server"]
SMTP_PORT = int(config["email"]["smtp_port"])

SEND_CSV_EMAIL = config["email"].get("send_csv_email", "true").strip().lower() == "true"

DELETE_CSV_ON_START = config.has_option('general', 'delete_csv_on_start') and config['general'].get('delete_csv_on_start', 'false').strip().lower() == 'true'

# Read double-check config
DOUBLE_CHECK_ON_RUN = config['general'].get('double_check_csv_on_run', 'false').strip().lower() == 'true'
DOUBLE_CHECK_MODE = config['general'].get('double_check_mode', 'missing').strip().lower()
DOUBLE_CHECK_TIMES = [t.strip() for t in config['general'].get('double_check_times', '').split(',') if t.strip()]

def extract_books(text):
    # Matches {Book Title by Author} with curly braces
    pattern = r"\{([^\{\}]+?)\s+by\s+([^\{\}]+?)\}"
    return [(t.strip(), a.strip()) for t, a in re.findall(pattern, text, re.IGNORECASE)]

def lookup_open_library(title, author):
    url = f"https://openlibrary.org/search.json?title={title}&author={author}"
    r = requests.get(url)
    if not r.ok:
        return None

    docs = r.json().get("docs", [])
    if not docs:
        return None

    # Try to find the best match for both title and author
    doc = None
    for d in docs:
        doc_title = d.get("title", "").lower()
        doc_authors = " ".join(d.get("author_name", [])).lower()
        if title.lower() in doc_title and author.lower() in doc_authors:
            doc = d
            break
    if not doc:
        doc = docs[0]  # fallback to first

    isbn_list = doc.get("isbn", [])
    isbn13 = next((i for i in isbn_list if len(i) == 13), None)
    isbn10 = next((i for i in isbn_list if len(i) == 10), None)
    isbn_value = isbn13 or isbn10 or (isbn_list[0] if isbn_list else "N/A")

    return {
        "title": doc.get("title", title),
        "author": ", ".join(doc.get("author_name", [author])),
        "tags": doc.get("subject", [])[:10],
        "cover_url": f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg" if doc.get("cover_i") else "N/A",
        "isbn13": isbn_value
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

def robust_lookup_open_library(title, author, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return lookup_open_library(title, author)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                activity_logger.error(f"Open Library lookup failed for {title} by {author}: {e}")
                return None

def lookup_romance_io(title, author):
    search_query = f"{title} {author}".replace(" ", "+")
    url = f"https://www.romance.io/books?search={search_query}"
    try:
        response = requests.get(url, timeout=10)
        if not response.ok:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        book_link = soup.find("a", class_="book-link")
        if book_link:
            book_url = "https://www.romance.io" + book_link.get("href")
            return {
                "title": title,
                "author": author,
                "isbn13": "N/A",
                "tags": [],
                "cover_url": "N/A",
                "romance_io_url": book_url
            }
    except Exception as e:
        activity_logger.error(f"Romance.io lookup failed for {title} by {author}: {e}")
    return None

def lookup_google_books(title, author):
    import requests
    params = {
        'q': f'intitle:{title} inauthor:{author}',
        'maxResults': 1
    }
    url = 'https://www.googleapis.com/books/v1/volumes'
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.ok:
            items = r.json().get('items', [])
            if items:
                volume = items[0]['volumeInfo']
                isbn13 = next((id['identifier'] for id in volume.get('industryIdentifiers', []) if id['type'] == 'ISBN_13'), 'N/A')
                return {
                    'title': volume.get('title', title),
                    'author': ', '.join(volume.get('authors', [author])),
                    'isbn13': isbn13,
                    'tags': volume.get('categories', []),
                    'cover_url': volume.get('imageLinks', {}).get('thumbnail', 'N/A'),
                    'romance_io_url': '',
                    'google_books_url': volume.get('infoLink', '')
                }
    except Exception as e:
        activity_logger.error(f"Google Books lookup failed for {title} by {author}: {e}")
    return None

def write_book_to_csv(book, csv_path="book_mentions.csv"):
    existing = set()
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = (row['title'].strip().lower(), row['author'].strip().lower())
                existing.add(key)
    except FileNotFoundError:
        pass
    key = (book['title'].strip().lower(), book['author'].strip().lower())
    if key in existing:
        return
    write_header = not os.path.exists(csv_path)
    fieldnames = ['title', 'author', 'isbn13', 'tags', 'cover_url', 'romance_io_url', 'google_books_url', 'steam', 'datetime_added', 'reddit_created_utc', 'reddit_created_date']
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            'title': book['title'],
            'author': book['author'],
            'isbn13': book.get('isbn13', 'N/A'),
            'tags': ', '.join(book.get('tags', [])) if book.get('tags') else '',
            'cover_url': book.get('cover_url', 'N/A'),
            'romance_io_url': book.get('romance_io_url', ''),
            'google_books_url': book.get('google_books_url', ''),
            'steam': book.get('steam', ''),
            'datetime_added': datetime.datetime.now().isoformat(),
            'reddit_created_utc': book.get('reddit_created_utc', ''),
            'reddit_created_date': book.get('reddit_created_date', '')
        })
        csvfile.flush()
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

def extract_romance_io_link(text):
    match = re.search(r'(https?://www\.romance\.io/[\w\-/\?=&#.]+)', text)
    return match.group(1) if match else ''

def extract_romance_bot_data(text):
    # Extract romance.io link
    link_match = re.search(r'(https?://www\.romance\.io/[\w\-/\?=&#.]+)', text)
    romance_link = link_match.group(1) if link_match else ''
    # Extract topics (e.g. 'Topics: topic1, topic2, ...')
    topics_match = re.search(r'Topics?:\s*([^\n]+)', text, re.IGNORECASE)
    topics = [t.strip() for t in topics_match.group(1).split(',')] if topics_match else []
    # Extract steam level (e.g. 'Steam: Open door')
    steam_match = re.search(r'Steam:\s*([^\n]+)', text, re.IGNORECASE)
    steam = steam_match.group(1).strip() if steam_match else ''
    return romance_link, topics, steam

def update_csv_with_romance_bot(title, author, romance_io_url, topics, steam, csv_path="book_mentions.csv"):
    key = (title.strip().lower(), author.strip().lower())
    updated = False
    rows = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row_key = (row['title'].strip().lower(), row['author'].strip().lower())
                if row_key == key:
                    if romance_io_url:
                        row['romance_io_url'] = romance_io_url
                    if topics:
                        row['tags'] = ', '.join(topics)
                    if steam:
                        row['steam'] = steam
                    updated = True
                rows.append(row)
    except FileNotFoundError:
        return False
    if updated:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return updated

def extract_books_from_romance_bot(text):
    """
    Extracts 'Title by Author' from the first line of a romance-bot comment.
    Returns a list of (title, author) tuples.
    """
    # Romance-bot usually puts the book mention on the first line
    lines = text.strip().splitlines()
    if not lines:
        return []
    first_line = lines[0].strip()
    # Match 'Title by Author' (not in curly brackets)
    match = re.match(r"(.+?)\s+by\s+(.+)", first_line, re.IGNORECASE)
    if match:
        title, author = match.group(1).strip(), match.group(2).strip()
        return [(title, author)]
    return []

def process_comments(post, seen):
    try:
        post.comments.replace_more(limit=None)
        for comment in post.comments.list():
            # Romance-bot handler
            if is_romance_bot(comment):
                handle_romance_bot_comment(comment, seen)
                continue  # Don't process further for romance-bot
            # Add more bot handlers here, e.g.:
            # from fantasy_bot_handler import is_fantasy_bot, handle_fantasy_bot_comment
            # if is_fantasy_bot(comment):
            #     handle_fantasy_bot_comment(comment, seen)
            #     continue
            # Curly-bracket handler as fallback
            if is_curly_bracket_comment(comment):
                handle_curly_bracket_comment(comment, seen)
    except praw.exceptions.APIException as e:
        if hasattr(e, 'error_type') and 'RATELIMIT' in str(e.error_type).upper():
            activity_logger.error(f"Rate limit exceeded while processing comments: {e}")
            time.sleep(60)  # Wait a minute before retrying
            process_comments(post, seen)
        else:
            activity_logger.error(f"APIException while processing comments: {e}")
    except Exception as e:
        activity_logger.error(f"Error scanning comments for post {post.id}: {e}")

def send_csv_report():
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    import os
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "📚 Book Bot - CSV Report"
    msg.attach(MIMEText("Attached is your CSV export.", "plain"))
    csv_path = "book_mentions.csv"
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            part = MIMEApplication(f.read(), Name="book_mentions.csv")
            part["Content-Disposition"] = 'attachment; filename="book_mentions.csv"'
            msg.attach(part)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 CSV email sent.")
    except Exception as e:
        print(f"❌ Failed to send CSV email: {e}")

def main():
    send_test_email()
    auto_update()
    if DELETE_CSV_ON_START:
        csv_path = "book_mentions.csv"
        if os.path.exists(csv_path):
            os.remove(csv_path)
            activity_logger.info("Deleted book_mentions.csv at start of run due to config setting.")
        else:
            activity_logger.info("CSV deletion requested but book_mentions.csv does not exist.")
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
        reddit_created_utc = getattr(post, 'created_utc', None)
        reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
        romance_link = extract_romance_io_link(content)
        reddit_url = f"https://reddit.com{getattr(post, 'permalink', '')}"
        for title, author in mentions:
            key = (title.lower(), author.lower())
            if key in seen:
                continue
            seen.add(key)
            book = robust_lookup_open_library(title, author)
            if book:
                book['reddit_created_utc'] = reddit_created_utc
                book['reddit_created_date'] = reddit_created_date
                book['romance_io_url'] = romance_link  # Always include romance.io link if present
                book['reddit_url'] = reddit_url
                activity_logger.info(f"Found book mention: {book['title']} by {book['author']}")
                write_book_to_csv(book)
                display_book(book)
                continue
            romance_book = lookup_romance_io(title, author)
            if romance_book:
                romance_book['reddit_created_utc'] = reddit_created_utc
                romance_book['reddit_created_date'] = reddit_created_date
                romance_book['reddit_url'] = reddit_url
                activity_logger.info(f"Found book mention on romance.io: {romance_book['title']} by {romance_book['author']}")
                write_book_to_csv(romance_book)
                console.print(f"[yellow]No data found on Open Library, but found on romance.io: {title} by {author}[/]")
            else:
                google_book = lookup_google_books(title, author)
                if google_book:
                    google_book['reddit_created_utc'] = reddit_created_utc
                    google_book['reddit_created_date'] = reddit_created_date
                    google_book['reddit_url'] = reddit_url
                    activity_logger.info(f"Found book mention on Google Books: {google_book['title']} by {google_book['author']}")
                    write_book_to_csv(google_book)
                    console.print(f"[yellow]No data found on Open Library or romance.io, but found on Google Books: {title} by {author}[/]")
                else:
                    no_data_book = {
                        'title': title,
                        'author': author,
                        'isbn13': 'N/A',
                        'tags': [],
                        'cover_url': 'N/A',
                        'romance_io_url': '',
                        'google_books_url': '',
                        'steam': '',
                        'reddit_created_utc': reddit_created_utc,
                        'reddit_created_date': reddit_created_date,
                        'reddit_url': reddit_url
                    }
                    activity_logger.info(f"No data found for: {title} by {author}, adding to CSV anyway.")
                    write_book_to_csv(no_data_book)
                    console.print(f"[yellow]No data found for: {title} by {author}[/]")
        process_comments(post, seen)
    activity_logger.info(f"✅ Book scan complete.")
    console.print(f"[cyan]✅ Book scan complete.[/]")
    if SEND_CSV_EMAIL:
        send_csv_report()
    # Double-check CSV if enabled
    if DOUBLE_CHECK_ON_RUN:
        activity_logger.info(f"Running CSV double-check in mode: {DOUBLE_CHECK_MODE}")
        run_csv_double_check(mode=DOUBLE_CHECK_MODE, praw_reddit=reddit)
    # Pseudo-code for scheduled double-checks (daemon mode):
    # while True:
    #     now = datetime.datetime.now().strftime('%H:%M')
    #     if now in DOUBLE_CHECK_TIMES:
    #         run_csv_double_check(mode=DOUBLE_CHECK_MODE, praw_reddit=reddit)
    #     time.sleep(60)

def livestream_subreddit():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    seen = set()
    activity_logger.info(f"Livestreaming r/{SUBREDDIT_NAME} for new posts and comments...")
    for post in subreddit.stream.submissions(skip_existing=True):
        content = f"{post.title} {post.selftext}"
        mentions = extract_books(content)
        for title, author in mentions:
            key = (title.lower(), author.lower())
            if key in seen:
                continue
            seen.add(key)
            book = robust_lookup_open_library(title, author)
            if book:
                activity_logger.info(f"[LIVE] Found book mention: {book['title']} by {book['author']}")
                write_book_to_csv(book)
                display_book(book)
        process_comments(post, seen)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Bot crashed:")
        print("❌ An error occurred. Check error.log for details.")
