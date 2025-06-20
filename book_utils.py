import re
import csv
import os
import datetime
import logging

def extract_books(text):
    # Matches {Book Title by Author} with curly braces
    pattern = r"\{([^\{\}]+?)\s+by\s+([^\{\}]+?)\}"
    return [(t.strip(), a.strip()) for t, a in re.findall(pattern, text, re.IGNORECASE)]

def extract_books_from_romance_bot(text):
    """
    Extracts 'Title by Author' from the first line of a romance-bot comment.
    Returns a list of (title, author) tuples.
    """
    lines = text.strip().splitlines()
    if not lines:
        return []
    first_line = lines[0].strip()
    match = re.match(r"(.+?)\s+by\s+(.+)", first_line, re.IGNORECASE)
    if match:
        title, author = match.group(1).strip(), match.group(2).strip()
        return [(title, author)]
    return []

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

def update_csv_with_romance_bot(title, author, romance_io_url, topics, steam, csv_path="book_mentions.csv", reddit_url=""):
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
                    if reddit_url:
                        row['reddit_url'] = reddit_url
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
    fieldnames = ['title', 'author', 'isbn13', 'tags', 'cover_url', 'romance_io_url', 'google_books_url', 'steam', 'datetime_added', 'reddit_created_utc', 'reddit_created_date', 'reddit_url']
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
            'reddit_created_date': book.get('reddit_created_date', ''),
            'reddit_url': book.get('reddit_url', '')
        })
        csvfile.flush()
    activity_logger.info(f"Wrote book to CSV: {book['title']} by {book['author']}")

def extract_romance_io_link(text):
    match = re.search(r'(https?://www\.romance\.io/[\w\-/\?=&#.]+)', text)
    return match.group(1) if match else ''

def lookup_open_library(title, author):
    import requests
    url = f"https://openlibrary.org/search.json?title={title}&author={author}"
    r = requests.get(url)
    if not r.ok:
        return None
    docs = r.json().get("docs", [])
    if not docs:
        return None
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

def robust_lookup_open_library(title, author, retries=3, delay=2):
    import time
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
    import requests
    from bs4 import BeautifulSoup
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

# Set up activity logging (for use in both main and handlers)
activity_logger = logging.getLogger("bot_activity")
activity_logger.setLevel(logging.INFO)
activity_handler = logging.FileHandler("bot.log")
activity_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not activity_logger.hasHandlers():
    activity_logger.addHandler(activity_handler) 