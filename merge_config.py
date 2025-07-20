import configparser
import sys

if len(sys.argv) != 3:
    print("Usage: python3 merge_config.py <default_config> <user_config>")
    sys.exit(1)

default_config = sys.argv[1]
user_config = sys.argv[2]

config = configparser.ConfigParser()
config.read([default_config, user_config])  # default first, then user

with open(user_config, 'w') as f:
    config.write(f) 