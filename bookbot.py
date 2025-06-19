import re
import configparser
import requests
import praw
import logging
import os
from rich.console import Console
from rich.table import Table

# Set up error logging
logging.basicConfig(filename="error.log", level=logging.ERROR,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# Load config
config = configparser.ConfigParser()
if not os.path.exists("config.ini"):
    print("❌ config.ini is missing. Please create it from config.example.ini.")
    exit(1)
config.read("config.ini")

REDDIT_CLIENT_ID = config["reddit"]["client_id"]
REDDIT_SECRET = config["reddit"]["client_secret"]
REDDIT_USER_AGENT = config["reddit"]["user_agent"]
SUBREDDIT_NAME = config["reddit"].get("subreddit", "lgbtbooks")

POST_LIMIT = 10  # Set to None to fetch all posts

console = Console()

def extract_books(text):
    pattern = r"\[(.*?)\s+by\s+(.*?)\]"
    return [(t.strip(), a.strip()) for t, a in re.findall(pattern, text, re.IGNORECASE)]

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

def display_book(book):
    table = Table(title=f"[bold magenta]{book['title']}[/] by {book['author']}")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Tags", ", ".join(book["tags"]) if book["tags"] else "None")
    table.add_row("Cover URL", book["cover_url"])
    table.add_row("ISBN-13", book["isbn13"])
    console.print(table)
    console.print("-" * 60)


def auto_update():
    import subprocess
    import os
    repo_dir = os.path.expanduser("~/bookbot")
    if os.path.exists(repo_dir):
        try:
            subprocess.run(["git", "-C", repo_dir, "pull"], check=True)
            print("🔄 Auto-update complete.")
        except subprocess.CalledProcessError:
            print("⚠️ Auto-update failed. Please pull manually.")

def main():
    auto_update()

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    seen = set()

    console.print(f"[green]Scanning r/{SUBREDDIT_NAME} for book mentions...[/]\n")

    posts = subreddit.new(limit=POST_LIMIT) if POST_LIMIT else subreddit.new(limit=None)

    for post in posts:
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

    console.print(f"[cyan]✅ Book scan complete.[/]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Bot crashed:")
        print("❌ An error occurred. Check error.log for details.")
