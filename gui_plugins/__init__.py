import os
user_plugins_dir = os.path.join(os.path.dirname(__file__), 'user_plugins')
if not os.path.exists(user_plugins_dir):
    os.makedirs(user_plugins_dir)
    with open(os.path.join(user_plugins_dir, '__init__.py'), 'w'):
        pass
from . import bluesky_dashboard_tab 