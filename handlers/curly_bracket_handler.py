from book_utils import extract_books, robust_lookup_open_library, lookup_romance_io, lookup_google_books, write_book_to_csv, activity_logger, extract_romance_io_link
import datetime

def is_curly_bracket_comment(comment):
    # This handler is the fallback for any comment
    return True

def handle_curly_bracket_comment(comment, seen):
    comment_mentions = extract_books(comment.body)
    reddit_created_utc = getattr(comment, 'created_utc', None)
    reddit_created_date = datetime.datetime.utcfromtimestamp(reddit_created_utc).isoformat() if reddit_created_utc else ''
    romance_link = extract_romance_io_link(comment.body)
    reddit_url = f"https://reddit.com{getattr(comment, 'permalink', '')}"
    for title, author in comment_mentions:
        key = (title.lower(), author.lower())
        if key in seen:
            continue
        seen.add(key)
        book = robust_lookup_open_library(title, author)
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
        romance_book = lookup_romance_io(title, author)
        if romance_book:
            romance_book['reddit_created_utc'] = reddit_created_utc
            romance_book['reddit_created_date'] = reddit_created_date
            romance_book['steam'] = ''
            romance_book['reddit_url'] = reddit_url
            activity_logger.info(f"Found book mention in comment on romance.io: {romance_book['title']} by {romance_book['author']}")
            write_book_to_csv(romance_book)
        else:
            google_book = lookup_google_books(title, author)
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