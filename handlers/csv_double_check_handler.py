import csv
import praw
import datetime
from book_utils import extract_books, update_csv_with_romance_bot, write_book_to_csv, activity_logger
from handlers.web_search.openlibrary_handler import enrich_with_openlibrary
from handlers.web_search.googlebooks_handler import enrich_with_googlebooks
from handlers.web_search.romanceio_handler import enrich_with_romanceio

def is_entry_missing_data(row):
    # Define what counts as missing: no ISBN, no tags, no cover, etc.
    return (
        row.get('isbn13', 'N/A') in ('', 'N/A') or
        not row.get('tags') or
        row.get('cover_url', 'N/A') in ('', 'N/A')
    )

def run_csv_double_check(mode='missing', csv_path='book_mentions.csv', praw_reddit=None):
    """
    mode: 'missing' (only incomplete entries) or 'all' (every entry)
    praw_reddit: a praw.Reddit instance
    """
    print(f"[INFO] Running CSV double-check (mode: {mode})...")
    if praw_reddit is None:
        raise ValueError("praw_reddit instance required")
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            rows = list(csv.DictReader(csvfile))
    except FileNotFoundError:
        activity_logger.warning("CSV file not found for double-check.")
        return
    updated = False
    for row in rows:
        if mode == 'missing' and not is_entry_missing_data(row):
            continue
        reddit_url = row.get('reddit_url', '')
        if not reddit_url:
            continue
        # Extract the Reddit ID from the URL
        if '/comments/' in reddit_url:
            # It's a comment
            try:
                comment_id = reddit_url.split('/comments/')[1].split('/')[2]
                comment = praw_reddit.comment(id=comment_id)
                body = comment.body
                # Try both curly and romance-bot extraction
                mentions = extract_books(body)
                for title, author in mentions:
                    # Try to enrich
                    book = enrich_with_openlibrary(title, author)
                    if not book:
                        book = enrich_with_romanceio(title, author)
                    if not book:
                        book = enrich_with_googlebooks(title, author)
                    if book:
                        book['reddit_created_utc'] = getattr(comment, 'created_utc', '')
                        book['reddit_created_date'] = datetime.datetime.utcfromtimestamp(getattr(comment, 'created_utc', 0)).isoformat() if getattr(comment, 'created_utc', None) else ''
                        book['reddit_url'] = reddit_url
                        write_book_to_csv(book)
                        activity_logger.info(f"Double-check updated: {title} by {author} from comment {reddit_url}")
                        updated = True
            except Exception as e:
                activity_logger.error(f"Failed to double-check comment {reddit_url}: {e}")
        else:
            # It's a post
            try:
                post_id = reddit_url.rstrip('/').split('/')[-1]
                post = praw_reddit.submission(id=post_id)
                content = f"{post.title} {post.selftext}"
                mentions = extract_books(content)
                for title, author in mentions:
                    book = enrich_with_openlibrary(title, author)
                    if not book:
                        book = enrich_with_romanceio(title, author)
                    if not book:
                        book = enrich_with_googlebooks(title, author)
                    if book:
                        book['reddit_created_utc'] = getattr(post, 'created_utc', '')
                        book['reddit_created_date'] = datetime.datetime.utcfromtimestamp(getattr(post, 'created_utc', 0)).isoformat() if getattr(post, 'created_utc', None) else ''
                        book['reddit_url'] = reddit_url
                        write_book_to_csv(book)
                        activity_logger.info(f"Double-check updated: {title} by {author} from post {reddit_url}")
                        updated = True
            except Exception as e:
                activity_logger.error(f"Failed to double-check post {reddit_url}: {e}")
    if updated:
        activity_logger.info("CSV double-check completed with updates.")
    else:
        activity_logger.info("CSV double-check completed. No updates made.") 