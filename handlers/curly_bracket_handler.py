import logging
from book_utils import extract_books, write_book_to_csv, activity_logger, extract_romance_io_link
from handlers.web_search.openlibrary_handler import enrich_with_openlibrary
from handlers.web_search.googlebooks_handler import enrich_with_googlebooks
from handlers.web_search.romanceio_handler import enrich_with_romanceio
import datetime
import os
from rich.console import Console
console = Console()

# Set up a dedicated logger for comment data (shared with romance-bot handler)
os.makedirs("logs", exist_ok=True)
comment_data_logger = logging.getLogger("comment_data")
comment_data_logger.setLevel(logging.INFO)
comment_data_handler = logging.FileHandler("logs/comment_data.log", encoding='utf-8')
comment_data_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not comment_data_logger.hasHandlers():
    comment_data_logger.addHandler(comment_data_handler)

def is_curly_bracket_comment(item):
    """Checks if a post or comment contains a curly bracket mention."""
    content = ""
    if hasattr(item, 'body'): # It's a comment
        content = item.body
    elif hasattr(item, 'selftext'): # It's a post
        content = item.selftext
    return extract_books(content)

def handle_curly_bracket_comment(item, seen, ignored_counter=None):
    """Handles posts or comments with curly bracket mentions."""
    content = ""
    if hasattr(item, 'body'): # It's a comment
        content = item.body
    elif hasattr(item, 'selftext'): # It's a post
        content = f"{item.title} {item.selftext}"

    mentions = extract_books(content)
    if not mentions:
        return

    subreddit_name = item.subreddit.display_name
    reddit_created_utc = getattr(item, 'created_utc', None)
    reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
    romance_link = extract_romance_io_link(content)
    reddit_url = f"https://reddit.com{getattr(item, 'permalink', '')}"
    
    # Log the raw data
    try:
        log_content = content.replace('\n', ' ').replace('\r', '')
        comment_data_logger.info(f"[RAW DATA] ID: {getattr(item, 'id', '')} | Subreddit: {subreddit_name} | Content: {log_content}")
    except Exception as e:
        comment_data_logger.warning(f"[RAW DATA LOGGING FAILED] Could not log full object: {e}")

    for title, author in mentions:
        key = (title.lower(), author.lower())
        if key in seen:
            if ignored_counter is not None:
                ignored_counter[0] += 1
            continue
        seen.add(key)

        book = {'title': title, 'author': author}
        
        # Enrich book data
        enriched_book = enrich_with_openlibrary(title, author)
        if not enriched_book:
            enriched_book = enrich_with_romanceio(title, author)
        if not enriched_book:
            enriched_book = enrich_with_googlebooks(title, author)

        if enriched_book:
            book.update(enriched_book)
        
        # Always add standard reddit data
        book['reddit_created_utc'] = reddit_created_utc
        book['reddit_created_date'] = reddit_created_date
        book['reddit_url'] = reddit_url
        book['subreddit'] = subreddit_name
        # Always overwrite with a direct romance.io link if one was in the comment
        if romance_link:
            book['romance_io_url'] = romance_link
        
        activity_logger.info(f"Found mention for '{title}' by '{author}' in r/{subreddit_name}. Writing to CSV.")
        added = write_book_to_csv(book)
        if ignored_counter is not None and not added:
            ignored_counter[0] += 1 