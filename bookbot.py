import re
import configparser
import requests
import praw
import logging
import os
try:
    import setproctitle
    setproctitle.setproctitle("bookbot")
except ImportError:
    pass  # If not installed, just skip
from rich.console import Console
console = Console()
from rich.table import Table
import csv
import time
import prawcore
from bs4 import BeautifulSoup
import datetime
from handlers.romance_bot_handler import is_romance_bot, handle_romance_bot_comment
from book_utils import extract_books, update_csv_with_romance_bot, write_book_to_csv, activity_logger
from handlers.curly_bracket_handler import is_curly_bracket_comment, handle_curly_bracket_comment
from handlers.csv_double_check_handler import run_csv_double_check
# Add import for Bluesky scanning (to be implemented)
try:
    from bluesky_scan import run_bluesky_scan
except ImportError:
    run_bluesky_scan = None

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
    console.print("❌ config.ini is missing. Please create it from config.example.ini.")
    activity_logger.info("❌ config.ini is missing. Please create it from config.example.ini.")
    exit(1)
config.read("config.ini")

REDDIT_CLIENT_ID = config["reddit"]["client_id"]
REDDIT_SECRET = config["reddit"]["client_secret"]
REDDIT_USER_AGENT = config["reddit"]["user_agent"]
# Parse comma-separated subreddit list and join with "+" for PRAW
SUBREDDIT_NAMES_LIST = [name.strip() for name in config["reddit"].get("subreddit", "lgbtbooks").split(',')]
SUBREDDIT_NAME = "+".join(SUBREDDIT_NAMES_LIST)

limit_str = config["reddit"].get("limit", "").strip()
POST_LIMIT = None if not limit_str or limit_str.lower() == "none" else int(limit_str)

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
            console.print("🔄 Auto-update complete.")
            activity_logger.info("🔄 Auto-update complete.")
        except subprocess.CalledProcessError:
            console.print("⚠️ Auto-update failed. Please pull manually.")
            activity_logger.info("⚠️ Auto-update failed. Please pull manually.")


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
        console.print("📧 Test email sent.")
        activity_logger.info("📧 Test email sent.")
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

def process_comments(post, seen):
    # Process comments with retry logic for API errors
    try:
        # Replace MoreComments with a fresh fetch, which is more robust
        post.comments.replace_more(limit=None)
        comments = post.comments.list()
    except (prawcore.exceptions.RequestException, prawcore.exceptions.ServerError) as e:
        activity_logger.warning(f"Could not fetch comments for post {post.id} due to API error: {e}. Skipping post.")
        console.print(f"⚠️ Could not fetch comments for post {post.id}. Skipping.")
        return

    for comment in comments:
        # Each handler will now be responsible for calling write_book_to_csv with the correct data
        if is_romance_bot(comment):
            handle_romance_bot_comment(comment, seen)
            continue # Move to the next comment
            
        if is_curly_bracket_comment(comment):
            handle_curly_bracket_comment(comment, seen)
            continue

def send_csv_report():
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    import os
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "📚 Book Bot - CSV and Logs Report"
    attachments = []
    csv_path = "book_mentions.csv"
    botlog_path = os.path.join("logs", "bot.log")
    commentlog_path = os.path.join("logs", "comment_data.log")
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            part = MIMEApplication(f.read(), Name="book_mentions.csv")
            part["Content-Disposition"] = 'attachment; filename="book_mentions.csv"'
            msg.attach(part)
            attachments.append("book_mentions.csv")
    if os.path.exists(botlog_path):
        with open(botlog_path, "rb") as f:
            part = MIMEApplication(f.read(), Name="bot.log")
            part["Content-Disposition"] = 'attachment; filename="bot.log"'
            msg.attach(part)
            attachments.append("bot.log")
    if os.path.exists(commentlog_path):
        with open(commentlog_path, "rb") as f:
            part = MIMEApplication(f.read(), Name="comment_data.log")
            part["Content-Disposition"] = 'attachment; filename="comment_data.log"'
            msg.attach(part)
            attachments.append("comment_data.log")
    body = "Attached are your CSV export and logs: " + ", ".join(attachments) + "."
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        console.print("📧 CSV and logs email sent.")
        activity_logger.info("📧 CSV and logs email sent.")
    except Exception as e:
        print(f"❌ Failed to send CSV/logs email: {e}")

def get_next_run_time(check_times):
    now = datetime.datetime.now()
    today_run_times = []
    for t_str in check_times:
        h, m = map(int, t_str.split(':'))
        today_run_times.append(now.replace(hour=h, minute=m, second=0, microsecond=0))
    
    # Find the next run time today
    future_times_today = sorted([t for t in today_run_times if t > now])
    if future_times_today:
        return future_times_today[0]
    
    # If no more runs today, schedule for the first time tomorrow
    tomorrow = now + datetime.timedelta(days=1)
    first_run_tomorrow = sorted(today_run_times)[0]
    return tomorrow.replace(hour=first_run_tomorrow.hour, minute=first_run_tomorrow.minute, second=0, microsecond=0)

def run_scan_and_enrich(reddit):
    seen = set()
    csv_path = "book_mentions.csv"
    if os.path.exists(csv_path):
        try:
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header
                next(reader, None)
                for row in reader:
                    if row: 
                        title, author = row[0].strip().lower(), row[1].strip().lower()
                        seen.add((title, author))
        except (FileNotFoundError, StopIteration):
            pass # File is empty or doesn't exist
    
    console.print(f"🔎 Scanning subreddit(s): [bold cyan]{SUBREDDIT_NAME}[/bold cyan]...")
    activity_logger.info(f"Scanning subreddit(s): {SUBREDDIT_NAME}...")

    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    
    try:
        if POST_LIMIT:
            posts = subreddit.new(limit=POST_LIMIT)
        else:
            posts = subreddit.new(limit=None)
        for post in posts:
            # Pass the post object to process_comments
            process_comments(post, seen)
            
            # Also process the post body itself using the curly bracket handler
            handle_curly_bracket_comment(post, seen)

            content = f"{post.title} {post.selftext}"
            mentions = extract_books(content)
            reddit_created_utc = getattr(post, 'created_utc', None)
            reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
            romance_link = extract_romance_io_link(content)
            reddit_url = f"https://reddit.com{getattr(post, 'permalink', '')}"
            for title, author in mentions:
                key = (title, author)
                if key in seen:
                    continue
                seen.add(key)
                book = robust_lookup_open_library(title, author)
                if book:
                    book['reddit_created_utc'] = reddit_created_utc
                    book['reddit_created_date'] = reddit_created_date
                    book['romance_io_url'] = romance_link
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
                    activity_logger.info(f"No data found on Open Library, but found on romance.io: {title} by {author}")
                else:
                    google_book = lookup_google_books(title, author)
                    if google_book:
                        google_book['reddit_created_utc'] = reddit_created_utc
                        google_book['reddit_created_date'] = reddit_created_date
                        google_book['reddit_url'] = reddit_url
                        activity_logger.info(f"Found book mention on Google Books: {google_book['title']} by {google_book['author']}")
                        write_book_to_csv(google_book)
                        console.print(f"[yellow]No data found on Open Library or romance.io, but found on Google Books: {title} by {author}[/]")
                        activity_logger.info(f"No data found on Open Library or romance.io, but found on Google Books: {title} by {author}")
                    else:
                        no_data_book = {
                            'title': title, 'author': author, 'isbn13': 'N/A', 'tags': [], 'cover_url': 'N/A',
                            'romance_io_url': '', 'google_books_url': '', 'steam': '',
                            'reddit_created_utc': reddit_created_utc, 'reddit_created_date': reddit_created_date, 'reddit_url': reddit_url
                        }
                        activity_logger.info(f"No data found for: {title} by {author}, adding to CSV anyway.")
                        write_book_to_csv(no_data_book)
                        console.print(f"[yellow]No data found for: {title} by {author}[/]")
                        activity_logger.info(f"No data found for: {title} by {author}")

        activity_logger.info(f"✅ Book scan complete.")
        console.print(f"[cyan]✅ Book scan complete.[/]")
        activity_logger.info("✅ Book scan complete.")

        # Double-check CSV if enabled on run
        if DOUBLE_CHECK_ON_RUN:
            activity_logger.info(f"Running CSV double-check in mode: {DOUBLE_CHECK_MODE}")
            run_csv_double_check(mode=DOUBLE_CHECK_MODE, praw_reddit=reddit)
    except Exception as e:
        activity_logger.error(f"Error running scan and enrich: {e}")

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

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    run_scan_and_enrich(reddit)
    
    # Bluesky scan if enabled
    if config.has_section('bluesky') and config['bluesky'].get('scan_enabled', 'false').strip().lower() == 'true':
        if run_bluesky_scan:
            run_bluesky_scan(config)
        else:
            console.print("[yellow]Bluesky scanning is enabled in config, but bluesky_scan module is missing.[/]")
    
    # After the scan, send a final email if enabled.
    # For continuous, scheduled checks, run scheduled_check.py via cron.
    if SEND_CSV_EMAIL:
        send_csv_report()

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
    except KeyboardInterrupt:
        console.print("\nBot stopped by user.")
        activity_logger.info("Bot stopped by user.")
        exit(0)
    except Exception as e:
        activity_logger.error(f"An unexpected error occurred in main: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")
        exit(1)
