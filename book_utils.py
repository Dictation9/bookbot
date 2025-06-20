import re
import csv
import os
import datetime
import logging

os.makedirs("logs", exist_ok=True)

def extract_books(text):
    # Matches {Book Title by Author} with curly braces
    pattern = r"\{([^\{\}]+?)\s+by\s+([^\{\}]+?)\}"
    return [(t.strip(), a.strip()) for t, a in re.findall(pattern, text, re.IGNORECASE)]

def update_csv_with_romance_bot(title, author, romance_io_url, topics, steam, steam_rating='', csv_path="book_mentions.csv", reddit_url="", subreddit=""):
    key = (title.strip().lower(), author.strip().lower())
    updated = False
    rows = []
    fieldnames = ['title', 'author', 'isbn13', 'tags', 'cover_url', 'romance_io_url', 'google_books_url', 'steam', 'steam_rating', 'datetime_added', 'reddit_created_utc', 'reddit_created_date', 'reddit_url', 'subreddit']
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
                    if steam_rating:
                        row['steam_rating'] = steam_rating
                    if reddit_url:
                        row['reddit_url'] = reddit_url
                    if subreddit:
                        row['subreddit'] = subreddit
                    updated = True
                # Filter row to only fieldnames and no None keys
                filtered_row = {k: v for k, v in row.items() if k in fieldnames and k is not None}
                rows.append(filtered_row)
    except FileNotFoundError:
        return False
    if updated:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                filtered_row = {k: v for k, v in row.items() if k in fieldnames and k is not None}
                writer.writerow(filtered_row)
    return updated

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
    fieldnames = ['title', 'author', 'isbn13', 'tags', 'cover_url', 'romance_io_url', 'google_books_url', 'steam', 'steam_rating', 'datetime_added', 'reddit_created_utc', 'reddit_created_date', 'reddit_url', 'subreddit']
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
            'steam_rating': book.get('steam_rating', ''),
            'datetime_added': datetime.datetime.now().isoformat(),
            'reddit_created_utc': book.get('reddit_created_utc', ''),
            'reddit_created_date': book.get('reddit_created_date', ''),
            'reddit_url': book.get('reddit_url', ''),
            'subreddit': book.get('subreddit', '')
        })
        csvfile.flush()
    activity_logger.info(f"Wrote book to CSV: {book['title']} by {book['author']}")

def extract_romance_io_link(text):
    match = re.search(r'(https?://www\.romance\.io/[\w\-/\?=&#.]+)', text)
    return match.group(1) if match else ''

# Set up activity logging (for use in both main and handlers)
activity_logger = logging.getLogger("bot_activity")
activity_logger.setLevel(logging.INFO)
activity_handler = logging.FileHandler("logs/bot.log")
activity_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not activity_logger.hasHandlers():
    activity_logger.addHandler(activity_handler) 