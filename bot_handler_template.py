"""
Template for a bot handler module. Copy and adapt for new bots.
"""

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
    # Example: extract book info from comment.body
    # title, author = ...
    # Update or add to CSV as needed
    pass 