#!/bin/bash
cd ~/bookbot
source venv/bin/activate

# Backup config.ini if it exists
if [ -f config.ini ]; then
    cp config.ini config.ini.bak
fi

python3 bookbot.py

# Restore config.ini if it was overwritten
if [ -f config.ini.bak ]; then
    mv config.ini.bak config.ini
fi

read -p "Press ENTER to close..."
