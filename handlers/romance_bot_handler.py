import re
import datetime
import logging
import os
from book_utils import extract_books, update_csv_with_romance_bot, write_book_to_csv, activity_logger
from rich.console import Console
console = Console()

# Set up a dedicated logger for comment data
os.makedirs("logs", exist_ok=True)
comment_data_logger = logging.getLogger("comment_data")
comment_data_logger.setLevel(logging.INFO)
comment_data_handler = logging.FileHandler("logs/comment_data.log")
comment_data_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not comment_data_logger.hasHandlers():
    comment_data_logger.addHandler(comment_data_handler)

STEAM_LABEL_TO_NUM = {
    "Glimpses and kisses": 1,
    "Behind closed doors": 2,
    "Open door": 3,
    "Explicit open door": 4,
    "Explicit and plentiful": 5,
    # Add common variants/typos as needed
}

def is_romance_bot(comment):
    return getattr(comment, 'author', None) and str(comment.author).lower() == 'romance-bot'

def extract_markdown_title_author(text):
    """
    Extracts '[Title](book_link) by [Author](author_link)' from the first line of a romance-bot comment.
    Returns a list of (title, author, book_link) tuples.
    """
    lines = text.strip().splitlines()
    if not lines:
        return []
    first_line = lines[0].strip()
    # Match [Title](book_link) by [Author](author_link)
    match = re.match(r"\[([^\]]+)\]\(([^\)]+)\)\s+by\s+\[([^\]]+)\]\([^\)]+\)", first_line, re.IGNORECASE)
    if match:
        title, book_link, author = match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
        return [(title, author, book_link)]
    # Fallback to plain 'Title by Author'
    match = re.match(r"(.+?)\s+by\s+(.+)", first_line, re.IGNORECASE)
    if match:
        title, author = match.group(1).strip(), match.group(2).strip()
        return [(title, author, '')]
    return []

def extract_romance_bot_data(text):
    # Extract romance.io link
    link_match = re.search(r'(https?://www\.romance\.io/[\w\-/\?=&#.]+)', text)
    romance_link = link_match.group(1) if link_match else ''
    # Extract topics (e.g. 'Topics: topic1, topic2, ...')
    topics_match = re.search(r'Topics?:\s*([^\n]+)', text, re.IGNORECASE)
    topics = [t.strip() for t in topics_match.group(1).split(',')] if topics_match else []
    # Extract steam level (markdown or plain, bolded or not)
    steam = ''
    steam_rating = ''
    # Match **Steam**: [level](link) or Steam: [level](link)
    steam_md = re.search(r'(?:\*\*|__)?Steam(?:\*\*|__)?\s*:\s*\[([^\]]+)\]\([^\)]+\)', text, re.IGNORECASE)
    if steam_md:
        steam = steam_md.group(1).strip()
    else:
        # Fallback: Steam: plain text
        steam_plain = re.search(r'(?:\*\*|__)?Steam(?:\*\*|__)?\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if steam_plain:
            steam = steam_plain.group(1).strip()
    # Map to numeric rating
    steam_rating = str(STEAM_LABEL_TO_NUM.get(steam, '')) if steam else ''
    return romance_link, topics, steam, steam_rating

def handle_romance_bot_comment(comment, seen, ignored_counter=None):
    subreddit_name = comment.subreddit.display_name
    reddit_created_utc = getattr(comment, 'created_utc', None)
    reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
    reddit_url = f"https://reddit.com{getattr(comment, 'permalink', '')}"
    console.print(f"[INFO] Processing romance-bot comment: {reddit_url}")
    # Log the full raw Reddit API data for the comment
    try:
        comment_data_logger.info(f"[RAW COMMENT DATA] {getattr(comment, 'id', '')}: {getattr(comment, 'body', '')}")
        comment_data_logger.info(f"[RAW COMMENT OBJECT] {getattr(comment, 'id', '')}: {vars(comment)}")
    except Exception as e:
        comment_data_logger.warning(f"[RAW COMMENT DATA] Could not log full comment object: {e}")
    # Try both curly-brace and markdown extraction
    comment_mentions = extract_books(comment.body)
    if not comment_mentions:
        comment_mentions = extract_markdown_title_author(comment.body)
    for mention in comment_mentions:
        # Support both (title, author) and (title, author, book_link)
        if len(mention) == 3:
            title, author, book_link = mention
        else:
            title, author = mention
            book_link = ''
        romance_bot_link, romance_bot_topics, romance_bot_steam, romance_bot_steam_rating = extract_romance_bot_data(comment.body)
        # Prefer the markdown book_link if present
        romance_io_url = book_link or romance_bot_link
        # Log comment data and missing fields
        missing = []
        if not title: missing.append('title')
        if not author: missing.append('author')
        if not romance_io_url: missing.append('romance_io_url')
        if not romance_bot_steam: missing.append('steam')
        if not romance_bot_topics: missing.append('tags')
        comment_data_logger.info(f"Pulled: title='{title}', author='{author}', romance_io_url='{romance_io_url}', steam='{romance_bot_steam}', tags='{romance_bot_topics}', steam_rating='{romance_bot_steam_rating}', reddit_url='{reddit_url}', subreddit='{subreddit_name}'" + (f" | MISSING: {', '.join(missing)}" if missing else ""))
        updated = update_csv_with_romance_bot(title, author, romance_io_url, romance_bot_topics, romance_bot_steam, romance_bot_steam_rating, reddit_url=reddit_url, subreddit=subreddit_name)
        if not updated:
            # If not already in CSV, add as new
            romance_book = {
                'title': title,
                'author': author,
                'isbn13': 'N/A',
                'tags': romance_bot_topics,
                'cover_url': 'N/A',
                'romance_io_url': romance_io_url,
                'google_books_url': '',
                'steam': romance_bot_steam,
                'steam_rating': romance_bot_steam_rating,
                'reddit_created_utc': reddit_created_utc,
                'reddit_created_date': reddit_created_date,
                'reddit_url': reddit_url,
                'subreddit': subreddit_name
            }
            added = write_book_to_csv(romance_book)
            if ignored_counter is not None and not added:
                ignored_counter[0] += 1
            activity_logger.info(f"Added romance-bot book: {title} by {author}")
            console.print("-" * 60)
            console.print(f"[ROMANCE-BOT] {title} by {author}")
            console.print(f"Tags: {', '.join(romance_bot_topics) if romance_bot_topics else 'None'}")
            console.print(f"Romance.io URL: {romance_io_url if romance_io_url else 'None'}")
            console.print(f"Steam: {romance_bot_steam if romance_bot_steam else 'None'} (Rating: {romance_bot_steam_rating if romance_bot_steam_rating else 'N/A'})")
            console.print("-" * 60) 