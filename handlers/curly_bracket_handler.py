import logging
from book_utils import extract_books, write_book_to_csv, activity_logger, extract_romance_io_link
from handlers.web_search.openlibrary_handler import enrich_with_openlibrary
from handlers.web_search.googlebooks_handler import enrich_with_googlebooks
from handlers.web_search.romanceio_handler import enrich_with_romanceio
import datetime

# Set up a dedicated logger for comment data (shared with romance-bot handler)
comment_data_logger = logging.getLogger("comment_data")
comment_data_logger.setLevel(logging.INFO)
comment_data_handler = logging.FileHandler("logs/comment_data.log")
comment_data_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not comment_data_logger.hasHandlers():
    comment_data_logger.addHandler(comment_data_handler)

def is_curly_bracket_comment(comment):
    # This handler is the fallback for any comment
    return True

def handle_curly_bracket_comment(comment, seen):
    comment_mentions = extract_books(comment.body)
    reddit_created_utc = getattr(comment, 'created_utc', None)
    reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
    romance_link = extract_romance_io_link(comment.body)
    reddit_url = f"https://reddit.com{getattr(comment, 'permalink', '')}"
    # Log the full raw Reddit API data for the comment
    try:
        comment_data_logger.info(f"[RAW COMMENT DATA] {getattr(comment, 'id', '')}: {getattr(comment, 'body', '')}")
        comment_data_logger.info(f"[RAW COMMENT OBJECT] {getattr(comment, 'id', '')}: {vars(comment)}")
    except Exception as e:
        comment_data_logger.warning(f"[RAW COMMENT DATA] Could not log full comment object: {e}")
    for title, author in comment_mentions:
        key = (title.lower(), author.lower())
        if key in seen:
            continue
        seen.add(key)
        # Log comment data and missing fields
        missing = []
        if not title: missing.append('title')
        if not author: missing.append('author')
        if not romance_link: missing.append('romance_io_url')
        comment_data_logger.info(f"Pulled: title='{title}', author='{author}', romance_io_url='{romance_link}', reddit_url='{reddit_url}'" + (f" | MISSING: {', '.join(missing)}" if missing else ""))
        book = enrich_with_openlibrary(title, author)
        if book:
            book['reddit_created_utc'] = reddit_created_utc
            book['reddit_created_date'] = reddit_created_date
            book['romance_io_url'] = romance_link  # Always include romance.io link if present
            book['steam'] = ''
            book['reddit_url'] = reddit_url
            activity_logger.info(f"Found book mention in comment: {book['title']} by {book['author']}")
            write_book_to_csv(book)
            continue
        if romance_link:
            romance_book = {
                'title': title,
                'author': author,
                'isbn13': 'N/A',
                'tags': [],
                'cover_url': 'N/A',
                'romance_io_url': romance_link,
                'google_books_url': '',
                'steam': '',
                'reddit_created_utc': reddit_created_utc,
                'reddit_created_date': reddit_created_date,
                'reddit_url': reddit_url
            }
            activity_logger.info(f"Found romance.io link in comment for: {title} by {author}")
            write_book_to_csv(romance_book)
            continue  # Skip further lookups for this mention
        romance_book = enrich_with_romanceio(title, author)
        if romance_book:
            romance_book['reddit_created_utc'] = reddit_created_utc
            romance_book['reddit_created_date'] = reddit_created_date
            romance_book['steam'] = ''
            romance_book['reddit_url'] = reddit_url
            activity_logger.info(f"Found book mention in comment on romance.io: {romance_book['title']} by {romance_book['author']}")
            write_book_to_csv(romance_book)
        else:
            google_book = enrich_with_googlebooks(title, author)
            if google_book:
                google_book['reddit_created_utc'] = reddit_created_utc
                google_book['reddit_created_date'] = reddit_created_date
                google_book['steam'] = ''
                google_book['reddit_url'] = reddit_url
                activity_logger.info(f"Found book mention in comment on Google Books: {google_book['title']} by {google_book['author']}")
                write_book_to_csv(google_book)
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
                activity_logger.info(f"No data found for: {title} by {author} in comment, adding to CSV anyway.")
                write_book_to_csv(no_data_book) 