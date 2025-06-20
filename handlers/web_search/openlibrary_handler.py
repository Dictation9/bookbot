import requests
import time
from book_utils import activity_logger

def enrich_with_openlibrary(title, author, retries=3, delay=2):
    """
    Try to enrich book data using Open Library API.
    Returns a dict with book data or None if not found.
    """
    url = f"https://openlibrary.org/search.json?title={title}&author={author}"
    for attempt in range(retries):
        try:
            r = requests.get(url)
            if not r.ok:
                continue
            docs = r.json().get("docs", [])
            if not docs:
                continue
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
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                activity_logger.error(f"Open Library lookup failed for {title} by {author}: {e}")
    return None 