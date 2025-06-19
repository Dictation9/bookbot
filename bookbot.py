import re
import configparser
import requests
import praw
from rich.console import Console
from rich.table import Table

# Load config
config = configparser.ConfigParser()
config.read("config.ini")

REDDIT_CLIENT_ID = config["reddit"]["client_id"]
REDDIT_SECRET = config["reddit"]["client_secret"]
REDDIT_USER_AGENT = config["reddit"]["user_agent"]

SUBREDDIT_NAME = "lgbtbooks"
POST_LIMIT = 10

console = Console()

# Regex: [Title by Author]
def extract_books(text):
    pattern = r"\[(.*?)\s+by\s+(.*?)\]"
    return [(t.strip(), a.strip()) for t, a in re.findall(pattern, text, re.IGNORECASE)]

# Open Library API lookup
def lookup_open_library(title, author):
    url = f"https://openlibrary.org/search.json?title={title}&author={author}"
    r = requests.get(url)
    if not r.ok:
        return None

    docs = r.json().get("docs", [])
    if not docs:
        return None

    doc = docs[0]
    return {
        "title": doc.get("title", title),
        "author": ", ".join(doc.get("author_name", [author])),
        "tags": doc.get("subject", [])[:10],
        "cover_url": f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg" if doc.get("cover_i") else "N/A",
        "isbn13": next((i for i in doc.get("isbn", []) if len(i) == 13), "N/A")
    }

# Print result using Rich
def display_book(book):
    table = Table(title=f"[bold magenta]{book['title']}[/] by {book['author']}")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Tags", ", ".join(book["tags"]) if book["tags"] else "None")
    table.add_row("Cover URL", book["cover_url"])
    table.add_row("ISBN-13", book["isbn13"])

    console.print(table)
    console.print("-" * 60)

# Main logic
def main():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    seen = set()

    console.print(f"[green]Searching r/{SUBREDDIT_NAME} for book mentions...[/]\n")

    for post in subreddit.new(limit=POST_LIMIT):
        content = f"{post.title} {post.selftext}"
        mentions = extract_books(content)

        for title, author in mentions:
            key = (title.lower(), author.lower())
            if key in seen:
                continue
            seen.add(key)

            book = lookup_open_library(title, author)
            if book:
                display_book(book)
            else:
                console.print(f"[yellow]No data found for: {title} by {author}[/]")

if __name__ == "__main__":
    main()
