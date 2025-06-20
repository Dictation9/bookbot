"""
Template for a bot handler module. Copy and adapt for new bots.
"""

import logging

# Set up a dedicated logger for comment data (shared with other handlers)
comment_data_logger = logging.getLogger("comment_data")
comment_data_logger.setLevel(logging.INFO)
comment_data_handler = logging.FileHandler("logs/comment_data.log")
comment_data_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not comment_data_logger.hasHandlers():
    comment_data_logger.addHandler(comment_data_handler)

def is_example_bot(comment):
    """
    Returns True if the comment is from the example bot.
    Replace 'example-bot' with the actual bot username.
    """
    return getattr(comment, 'author', None) and str(comment.author).lower() == 'example-bot'

def handle_example_bot_comment(comment, seen):
    """
    Handles extraction and CSV update for example-bot comments.
    Replace this logic with extraction and CSV update for your bot.
    """
    # Log the full raw Reddit API data for the comment before processing
    try:
        comment_data_logger.info(f"[RAW COMMENT DATA] {getattr(comment, 'id', '')}: {getattr(comment, 'body', '')}")
        comment_data_logger.info(f"[RAW COMMENT OBJECT] {getattr(comment, 'id', '')}: {vars(comment)}")
    except Exception as e:
        comment_data_logger.warning(f"[RAW COMMENT DATA] Could not log full comment object: {e}")
    # Example: extract book info from comment.body
    # title, author = ...
    # Update or add to CSV as needed
    pass 