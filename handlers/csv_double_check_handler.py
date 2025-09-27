import logging
import csv
import praw
import datetime
import os
import re
from book_utils import extract_books, update_csv_with_romance_bot, write_book_to_csv, activity_logger
from handlers.web_search.openlibrary_handler import enrich_with_openlibrary
from handlers.web_search.googlebooks_handler import enrich_with_googlebooks
from handlers.web_search.romanceio_handler import enrich_with_romanceio
from rich.console import Console

# Set up a dedicated logger for comment data (shared with other handlers)
os.makedirs("logs", exist_ok=True)
comment_data_logger = logging.getLogger("comment_data")
comment_data_logger.setLevel(logging.INFO)
comment_data_handler = logging.FileHandler("logs/comment_data.log", encoding='utf-8')
comment_data_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not comment_data_logger.hasHandlers():
    comment_data_logger.addHandler(comment_data_handler)

console = Console()

def is_entry_missing_data(row):
    # Define what counts as missing: no ISBN, no tags, no cover, etc.
    return (
        row.get('isbn13', 'N/A') in ('', 'N/A') or
        not row.get('tags') or
        row.get('cover_url', 'N/A') in ('', 'N/A')
    )

def run_csv_double_check(mode='missing', csv_path='book_mentions.csv', praw_reddit=None):
    """
    Re-processes entries in the CSV to fill in missing data.
    mode: 'missing' (only incomplete entries) or 'all' (every entry).
    """
    console.print(f"🔄 Running CSV double-check (mode: {mode})...")
    activity_logger.info(f"Running CSV double-check (mode: {mode})...")
    
    if not os.path.exists(csv_path):
        activity_logger.warning("CSV file not found for double-check.")
        console.print("⚠️ CSV file not found, skipping double-check.")
        return

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            # Define fieldnames from the header of the existing CSV
            fieldnames = reader.fieldnames
            if 'subreddit' not in fieldnames:
                 fieldnames.append('subreddit') # Backwards compatibility
    except (FileNotFoundError, StopIteration):
        console.print("⚠️ CSV file is empty or missing, skipping double-check.")
        return

    updates_made = False
    for i, row in enumerate(rows):
        if mode == 'missing' and not is_entry_missing_data(row):
            continue

        title, author = row.get('title'), row.get('author')
        if not title or not author:
            continue

        # Try to enrich the book data
        enriched_book = enrich_with_openlibrary(title, author)
        if not enriched_book:
            enriched_book = enrich_with_romanceio(title, author)
        if not enriched_book:
            enriched_book = enrich_with_googlebooks(title, author)

        if enriched_book:
            # Merge enriched data into the existing row, preserving original data
            for key, value in enriched_book.items():
                if value and value != 'N/A': # Only update if new data is meaningful
                    row[key] = value
            
            # If subreddit is missing from the row, try to get it from the reddit_url
            if not row.get('subreddit') and row.get('reddit_url'):
                try:
                    match = re.search(r'/r/([^/]+)/', row['reddit_url'])
                    if match:
                        row['subreddit'] = match.group(1)
                except Exception:
                    pass # Ignore if regex fails

            rows[i] = row # Update the row in the list
            updates_made = True
            activity_logger.info(f"Double-check updated '{title}' by '{author}'.")

    # After checking all rows, write the updated data back to the file
    if updates_made:
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            activity_logger.info("CSV double-check completed with updates.")
            console.print("✅ CSV double-check finished. Data was updated.")
        except Exception as e:
            activity_logger.error(f"Failed to write updated CSV in double-check: {e}")
            console.print(f"❌ Failed to write updated CSV: {e}")
    else:
        activity_logger.info("CSV double-check completed. No updates were needed.")
        console.print("✅ CSV double-check finished. No updates needed.") 