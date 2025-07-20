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

console = Console()

def run_bluesky_scan(config):
    console.print("[cyan]🔎 Scanning Bluesky for book mentions...[/]")
    if not config.has_section('bluesky'):
        console.print("[yellow]No [bluesky] section in config. Skipping Bluesky scan.[/]")
        return
    username = config['bluesky'].get('username', '').strip()
    password = config['bluesky'].get('app_password', '').strip()
    feeds = [f.strip() for f in config['bluesky'].get('feeds', '').split(',') if f.strip()]
    hashtags = [h.strip().lstrip('#') for h in config['bluesky'].get('hashtags', '').split(',') if h.strip()]
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
    found_any = False
    # 1. Try feeds if specified
    if feeds:
        for feed in feeds:
            try:
                console.print(f"[blue]Scanning Bluesky feed: {feed}[/]")
                feed_result = client.get_feed(feed=feed)
                for feed_view in feed_result.feed:
                    post = feed_view.post.record
                    author = feed_view.post.author
                    content = getattr(post, 'text', '')
                    mentions = extract_books(content)
                    created_at = getattr(post, 'created_at', '')
                    bluesky_url = f"https://bsky.app/profile/{author.handle}/post/{feed_view.post.uri.split('/')[-1]}"
                    for title, author_name in mentions:
                        key = (title.lower(), author_name.lower())
                        if key in seen:
                            continue
                        seen.add(key)
                        book = robust_lookup_open_library(title, author_name)
                        if book:
                            book['bluesky_created_date'] = created_at
                            book['bluesky_url'] = bluesky_url
                            activity_logger.info(f"[Bluesky] Found book mention: {book['title']} by {book['author']}")
                            write_book_to_csv(book)
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
                # There is no official hashtag search, so we search the timeline and filter
                timeline = client.get_timeline(algorithm='reverse-chronological')
                for feed_view in timeline.feed:
                    post = feed_view.post.record
                    author = feed_view.post.author
                    content = getattr(post, 'text', '')
                    if f"#{hashtag}" not in content:
                        continue
                    mentions = extract_books(content)
                    created_at = getattr(post, 'created_at', '')
                    bluesky_url = f"https://bsky.app/profile/{author.handle}/post/{feed_view.post.uri.split('/')[-1]}"
                    for title, author_name in mentions:
                        key = (title.lower(), author_name.lower())
                        if key in seen:
                            continue
                        seen.add(key)
                        book = robust_lookup_open_library(title, author_name)
                        if book:
                            book['bluesky_created_date'] = created_at
                            book['bluesky_url'] = bluesky_url
                            activity_logger.info(f"[Bluesky] Found book mention: {book['title']} by {book['author']}")
                            write_book_to_csv(book)
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