import re
import datetime
from book_utils import extract_books, extract_romance_bot_data, update_csv_with_romance_bot, write_book_to_csv, activity_logger

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

def handle_romance_bot_comment(comment, seen):
    reddit_created_utc = getattr(comment, 'created_utc', None)
    reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
    reddit_url = f"https://reddit.com{getattr(comment, 'permalink', '')}"
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
        romance_bot_link, romance_bot_topics, romance_bot_steam = extract_romance_bot_data(comment.body)
        # Prefer the markdown book_link if present
        romance_io_url = book_link or romance_bot_link
        updated = update_csv_with_romance_bot(title, author, romance_io_url, romance_bot_topics, romance_bot_steam, reddit_url=reddit_url)
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
                'reddit_created_utc': reddit_created_utc,
                'reddit_created_date': reddit_created_date,
                'reddit_url': reddit_url
            }
            write_book_to_csv(romance_book)
            activity_logger.info(f"Added romance-bot book: {title} by {author}") 