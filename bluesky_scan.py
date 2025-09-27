# bluesky_scan.py
"""
Scan Bluesky for book mentions using the atproto library.
Supports scanning the home timeline, specific feeds, or hashtags as configured.
"""
import logging
from rich.console import Console
from atproto import Client
from book_utils import extract_books, write_book_to_csv, activity_logger
from bookbot import robust_lookup_open_library, lookup_romance_io, lookup_google_books
import datetime
import urllib.parse
import os

# Set up a separate logger for Bluesky post scans
os.makedirs("logs", exist_ok=True)
bluesky_post_logger = logging.getLogger("bluesky_post_scan")
bluesky_post_logger.setLevel(logging.INFO)
bluesky_log_handler = logging.FileHandler("logs/bluesky.log", encoding='utf-8')
bluesky_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not bluesky_post_logger.hasHandlers():
    bluesky_post_logger.addHandler(bluesky_log_handler)

console = Console()

def convert_bluesky_feed_url_to_aturi(feed_url, client):
    """
    Convert a Bluesky feed web URL to an AT-URI.
    feed_url: str, e.g. https://bsky.app/profile/biblioqueer.bsky.social/feed/aaafcf5orer4q
    client: atproto.Client instance (for handle resolution)
    Returns: str (AT-URI) or raises Exception
    """
    parsed = urllib.parse.urlparse(feed_url)
    path_parts = [p for p in parsed.path.split("/") if p]
    # Looking for .../profile/<handle_or_did>/feed/<feed_id>
    if "profile" in path_parts and "feed" in path_parts:
        profile_idx = path_parts.index("profile")
        handle_or_did = path_parts[profile_idx + 1]
        feed_idx = path_parts.index("feed")
        feed_id = path_parts[feed_idx + 1]
        # If it's a DID, use directly
        if handle_or_did.startswith("did:plc:"):
            did = handle_or_did
        else:
            # Resolve handle to DID
            resolved = client.resolve_handle(handle_or_did)
            did = resolved.did
        return f"at://{did}/app.bsky.feed.generator/{feed_id}"
    else:
        raise ValueError("URL does not contain expected /profile/<handle_or_did>/feed/<feed_id> structure")

def run_bluesky_scan(config, emit_post_count=False):
    console.print("[cyan]🔎 Scanning Bluesky for book mentions...[/]")
    if not config.has_section('bluesky'):
        console.print("[yellow]No [bluesky] section in config. Skipping Bluesky scan.[/]")
        return
    username = config['bluesky'].get('username', '').strip()
    password = config['bluesky'].get('app_password', '').strip()
    feeds = [f.strip() for f in config['bluesky'].get('feeds', '').split(',') if f.strip()]
    hashtags = [h.strip().lstrip('#') for h in config['bluesky'].get('hashtags', '').split(',') if h.strip()]
    # Get post limit from config
    post_limit_str = config['bluesky'].get('bluesky_post_limit', '').strip()
    try:
        post_limit = int(post_limit_str) if post_limit_str else 0
    except Exception:
        post_limit = 0
    if not username or not password:
        console.print("[yellow]Bluesky username or app_password not set. Skipping Bluesky scan.[/]")
        return
    try:
        client = Client()
        client.login(username, password)
    except Exception as e:
        console.print(f"[red]Failed to authenticate with Bluesky: {e}[/]")
        activity_logger.error(f"Failed to authenticate with Bluesky: {e}")
        return
    seen = set()
    duplicate_count = 0
    found_any = False
    books_added = 0
    books_ignored = 0
    # 1. Try feeds if specified
    if feeds:
        for feed in feeds:
            try:
                console.print(f"[blue]Scanning Bluesky feed: {feed}[/]")
                # If feed is a web URL, convert to AT-URI
                at_uri = feed
                if feed.startswith("https://bsky.app/profile/"):
                    try:
                        # Robustly parse the URL
                        parsed = urllib.parse.urlparse(feed)
                        path_parts = [p for p in parsed.path.split("/") if p]
                        # Looking for .../profile/<handle>/feed/<feed_id>
                        if "profile" in path_parts and "feed" in path_parts:
                            profile_idx = path_parts.index("profile")
                            handle = path_parts[profile_idx + 1]
                            feed_idx = path_parts.index("feed")
                            feed_id = path_parts[feed_idx + 1]
                        else:
                            raise ValueError("URL does not contain expected /profile/<handle>/feed/<feed_id> structure")
                        # Resolve handle to DID
                        resolved = client.resolve_handle(handle)
                        did = resolved.did
                        at_uri = f"at://{did}/app.bsky.feed.generator/{feed_id}"
                    except Exception as e:
                        console.print(f"[yellow]Failed to parse or resolve feed URL {feed}: {e}[/]")
                        activity_logger.warning(f"Failed to parse or resolve feed URL {feed}: {e}")
                        continue
                feed_result = client.app.bsky.feed.get_feed({'feed': at_uri})
                post_count = len(feed_result.feed)
                if emit_post_count:
                    print(f"[BLUESKY_POST_COUNT] {post_count}")
                processed = 0
                for feed_view in feed_result.feed:
                    if post_limit and processed >= post_limit:
                        break
                    processed += 1
                    post = feed_view.post.record
                    author = feed_view.post.author
                    content = getattr(post, 'text', '')
                    created_at = getattr(post, 'created_at', '')
                    bluesky_url = f"https://bsky.app/profile/{author.handle}/post/{feed_view.post.uri.split('/')[-1]}"
                    # Log every post scanned from feeds
                    bluesky_post_logger.info(f"[Bluesky][Scan][Feed] @{author.handle} | {created_at} | {bluesky_url} | {content[:200].replace(chr(10), ' ')}")
                    mentions = extract_books(content)
                    for title, author_name in mentions:
                        key = (title.lower(), author_name.lower())
                        if key in seen:
                            duplicate_count += 1
                            continue
                        seen.add(key)
                        # Check CSV before adding
                        book = robust_lookup_open_library(title, author_name)
                        if book:
                            book['bluesky_created_date'] = created_at
                            book['bluesky_url'] = bluesky_url
                            # Only add if not in CSV
                            before = books_added
                            write_book_to_csv(book)
                            # Check if added
                            with open('book_mentions.csv', newline='', encoding='utf-8') as csvfile:
                                import csv
                                reader = csv.DictReader(csvfile)
                                count = sum(1 for row in reader if row['title'].strip().lower() == title.lower() and row['author'].strip().lower() == author_name.lower())
                            if count == 1:
                                books_added += 1
                            else:
                                books_ignored += 1
                            activity_logger.info(f"[Bluesky] Found book mention: {book['title']} by {book['author']}")
                            found_any = True
                            continue
                        romance_book = lookup_romance_io(title, author_name)
                        if romance_book:
                            romance_book['bluesky_created_date'] = created_at
                            romance_book['bluesky_url'] = bluesky_url
                            activity_logger.info(f"[Bluesky] Found book mention on romance.io: {romance_book['title']} by {romance_book['author']}")
                            write_book_to_csv(romance_book)
                            found_any = True
                        else:
                            google_book = lookup_google_books(title, author_name)
                            if google_book:
                                google_book['bluesky_created_date'] = created_at
                                google_book['bluesky_url'] = bluesky_url
                                activity_logger.info(f"[Bluesky] Found book mention on Google Books: {google_book['title']} by {google_book['author']}")
                                write_book_to_csv(google_book)
                                found_any = True
                            else:
                                no_data_book = {
                                    'title': title, 'author': author_name, 'isbn13': 'N/A', 'tags': [], 'cover_url': 'N/A',
                                    'romance_io_url': '', 'google_books_url': '', 'steam': '',
                                    'bluesky_created_date': created_at, 'bluesky_url': bluesky_url
                                }
                                activity_logger.info(f"[Bluesky] No data found for: {title} by {author_name}, adding to CSV anyway.")
                                write_book_to_csv(no_data_book)
                                found_any = True
            except Exception as e:
                console.print(f"[yellow]Error scanning feed {feed}: {e}[/]")
                activity_logger.warning(f"Error scanning feed {feed}: {e}")
    # 2. If no feeds or none found, try hashtags
    if not feeds or not found_any:
        for hashtag in hashtags:
            try:
                console.print(f"[blue]Searching Bluesky for hashtag: #{hashtag}[/]")
                timeline = client.get_timeline(algorithm='reverse-chronological')
                # Count posts with the hashtag
                posts_with_hashtag = [feed_view for feed_view in timeline.feed if f"#{hashtag}" in getattr(feed_view.post.record, 'text', '')]
                if emit_post_count:
                    print(f"[BLUESKY_POST_COUNT] {len(posts_with_hashtag)}")
                for feed_view in posts_with_hashtag:
                    post = feed_view.post.record
                    author = feed_view.post.author
                    content = getattr(post, 'text', '')
                    if f"#{hashtag}" not in content:
                        continue
                    created_at = getattr(post, 'created_at', '')
                    bluesky_url = f"https://bsky.app/profile/{author.handle}/post/{feed_view.post.uri.split('/')[-1]}"
                    # Log every post scanned from hashtags
                    bluesky_post_logger.info(f"[Bluesky][Scan][Hashtag] @{author.handle} | {created_at} | {bluesky_url} | {content[:200].replace(chr(10), ' ')}")
                    mentions = extract_books(content)
                    for title, author_name in mentions:
                        key = (title.lower(), author_name.lower())
                        if key in seen:
                            duplicate_count += 1
                            continue
                        seen.add(key)
                        # Check CSV before adding
                        book = robust_lookup_open_library(title, author_name)
                        if book:
                            book['bluesky_created_date'] = created_at
                            book['bluesky_url'] = bluesky_url
                            before = books_added
                            write_book_to_csv(book)
                            with open('book_mentions.csv', newline='', encoding='utf-8') as csvfile:
                                import csv
                                reader = csv.DictReader(csvfile)
                                count = sum(1 for row in reader if row['title'].strip().lower() == title.lower() and row['author'].strip().lower() == author_name.lower())
                            if count == 1:
                                books_added += 1
                            else:
                                books_ignored += 1
                            activity_logger.info(f"[Bluesky] Found book mention: {book['title']} by {book['author']}")
                            found_any = True
                            continue
                        romance_book = lookup_romance_io(title, author_name)
                        if romance_book:
                            romance_book['bluesky_created_date'] = created_at
                            romance_book['bluesky_url'] = bluesky_url
                            activity_logger.info(f"[Bluesky] Found book mention on romance.io: {romance_book['title']} by {romance_book['author']}")
                            write_book_to_csv(romance_book)
                            found_any = True
                        else:
                            google_book = lookup_google_books(title, author_name)
                            if google_book:
                                google_book['bluesky_created_date'] = created_at
                                google_book['bluesky_url'] = bluesky_url
                                activity_logger.info(f"[Bluesky] Found book mention on Google Books: {google_book['title']} by {google_book['author']}")
                                write_book_to_csv(google_book)
                                found_any = True
                            else:
                                no_data_book = {
                                    'title': title, 'author': author_name, 'isbn13': 'N/A', 'tags': [], 'cover_url': 'N/A',
                                    'romance_io_url': '', 'google_books_url': '', 'steam': '',
                                    'bluesky_created_date': created_at, 'bluesky_url': bluesky_url
                                }
                                activity_logger.info(f"[Bluesky] No data found for: {title} by {author_name}, adding to CSV anyway.")
                                write_book_to_csv(no_data_book)
                                found_any = True
            except Exception as e:
                console.print(f"[yellow]Error searching for hashtag #{hashtag}: {e}[/]")
                activity_logger.warning(f"Error searching for hashtag #{hashtag}: {e}")
    if found_any:
        console.print("[cyan]✅ Bluesky book scan complete.[/]")
        activity_logger.info("✅ Bluesky book scan complete.")
    else:
        console.print("[yellow]No book mentions found on Bluesky.[/]")
        activity_logger.info("No book mentions found on Bluesky.")
    if emit_post_count:
        print(f"[BLUESKY_DUPLICATES] {duplicate_count}")
        print(f"[BLUESKY_ADDED] {books_added}")
        print(f"[BLUESKY_IGNORED] {books_ignored}")

if __name__ == "__main__":
    import sys
    from atproto import Client
    example_url = "https://bsky.app/profile/did:plc:6qswqt6prj5ch3jwjyqedexs/feed/aaafcf5orer4q"
    if len(sys.argv) == 2:
        feed_url = sys.argv[1]
    else:
        print("Usage: python bluesky_scan.py <bluesky_feed_url>")
        print(f"Example: python bluesky_scan.py {example_url}")
        feed_url = input(f"Enter a Bluesky feed URL to convert (or 'q' to quit): ").strip()
        if feed_url.lower() in ('q', 'quit'):
            sys.exit(0)
    username = input("Bluesky username (handle): ")
    password = input("Bluesky app password: ")
    client = Client()
    client.login(username, password)
    while True:
        try:
            at_uri = convert_bluesky_feed_url_to_aturi(feed_url, client)
            print(f"AT-URI: {at_uri}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        # Prompt for another
        feed_url = input("Enter another Bluesky feed URL to convert (or 'q' to quit): ").strip()
        if feed_url.lower() in ('q', 'quit'):
            break 