import requests
from bs4 import BeautifulSoup
from book_utils import activity_logger

def enrich_with_romanceio(title, author):
    """
    Try to enrich book data using romance.io.
    Returns a dict with book data or None if not found.
    """
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