import requests
from book_utils import activity_logger

def enrich_with_googlebooks(title, author):
    """
    Try to enrich book data using Google Books API.
    Returns a dict with book data or None if not found.
    """
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