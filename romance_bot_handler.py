import re
import datetime
from book_utils import extract_books, extract_books_from_romance_bot, extract_romance_bot_data, update_csv_with_romance_bot, write_book_to_csv, activity_logger

def is_romance_bot(comment):
    return getattr(comment, 'author', None) and str(comment.author).lower() == 'romance-bot'

def handle_romance_bot_comment(comment, seen):
    reddit_created_utc = getattr(comment, 'created_utc', None)
    reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
    # Try both curly-brace and plain extraction
    comment_mentions = extract_books(comment.body)
    if not comment_mentions:
        comment_mentions = extract_books_from_romance_bot(comment.body)
    for title, author in comment_mentions:
        romance_bot_link, romance_bot_topics, romance_bot_steam = extract_romance_bot_data(comment.body)
        updated = update_csv_with_romance_bot(title, author, romance_bot_link, romance_bot_topics, romance_bot_steam)
        if not updated:
            # If not already in CSV, add as new
            romance_book = {
                'title': title,
                'author': author,
                'isbn13': 'N/A',
                'tags': romance_bot_topics,
                'cover_url': 'N/A',
                'romance_io_url': romance_bot_link,
                'google_books_url': '',
                'steam': romance_bot_steam,
                'reddit_created_utc': reddit_created_utc,
                'reddit_created_date': reddit_created_date
            }
            write_book_to_csv(romance_book)
            activity_logger.info(f"Added romance-bot book: {title} by {author}") 